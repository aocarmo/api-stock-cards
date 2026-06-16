"""Persistência de jobs em SQLite (sobrevive a reload do servidor)."""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

ACTIVE_STATES = ("PENDING", "RUNNING", "WAITING", "RETRYING")

_JOB_COLS = [
    "id", "operation", "status", "total_linhas", "total_sucesso", "total_erro",
    "round", "current_batch", "total_batches", "cancel_requested", "mensagem",
    "created_at", "updated_at",
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class JobStore:
    def __init__(self, db_file: Path):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_file), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def init(self):
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_linhas INTEGER DEFAULT 0,
                    total_sucesso INTEGER DEFAULT 0,
                    total_erro INTEGER DEFAULT 0,
                    round INTEGER DEFAULT 0,
                    current_batch INTEGER DEFAULT 0,
                    total_batches INTEGER DEFAULT 0,
                    cancel_requested INTEGER DEFAULT 0,
                    mensagem TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS job_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    numero TEXT, colecao TEXT, tipo TEXT, idioma TEXT,
                    preco TEXT, quantidade TEXT,
                    linha_status TEXT DEFAULT 'pending',
                    ultimo_erro_status TEXT DEFAULT '',
                    tentativas INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_lines_job ON job_lines(job_id);
                """
            )
            self._conn.commit()

    # ---- jobs ----
    def create_job(self, job_id: str, operation: str, cards: list[dict]):
        with self._lock:
            self._conn.execute(
                "INSERT INTO jobs (id, operation, status, total_linhas, created_at, updated_at)"
                " VALUES (?,?,?,?,?,?)",
                (job_id, operation, "PENDING", len(cards), _now(), _now()),
            )
            self._conn.executemany(
                "INSERT INTO job_lines (job_id, numero, colecao, tipo, idioma, preco, quantidade)"
                " VALUES (?,?,?,?,?,?,?)",
                [
                    (job_id, c.get("numero"), c.get("colecao"), c.get("tipo"),
                     c.get("idioma"), c.get("preco"), c.get("quantidade"))
                    for c in cards
                ],
            )
            self._conn.commit()

    def update_job(self, job_id: str, **fields):
        fields["updated_at"] = _now()
        cols = ", ".join(f"{k}=?" for k in fields)
        with self._lock:
            self._conn.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*fields.values(), job_id))
            self._conn.commit()

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def list_jobs(self, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def active_job_ids(self) -> list[str]:
        q = "SELECT id FROM jobs WHERE status IN (%s)" % ",".join("?" * len(ACTIVE_STATES))
        with self._lock:
            rows = self._conn.execute(q, ACTIVE_STATES).fetchall()
        return [r["id"] for r in rows]

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT cancel_requested FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
        return bool(row and row["cancel_requested"])

    def request_cancel(self, job_id: str):
        self.update_job(job_id, cancel_requested=1)

    # ---- lines ----
    def get_lines(self, job_id: str, status: str | None = None) -> list[dict]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM job_lines WHERE job_id=? AND linha_status=? ORDER BY id",
                    (job_id, status),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM job_lines WHERE job_id=? ORDER BY id", (job_id,)
                ).fetchall()
        return [dict(r) for r in rows]

    def set_line_status(self, line_id: int, status: str, err_status: str = ""):
        with self._lock:
            self._conn.execute(
                "UPDATE job_lines SET linha_status=?, ultimo_erro_status=?,"
                " tentativas=tentativas+1 WHERE id=?",
                (status, err_status, line_id),
            )
            self._conn.commit()

    def reset_errors_to_pending(self, job_id: str):
        with self._lock:
            self._conn.execute(
                "UPDATE job_lines SET linha_status='pending' WHERE job_id=? AND linha_status='erro'",
                (job_id,),
            )
            self._conn.commit()

    def recompute_counts(self, job_id: str):
        with self._lock:
            rows = self._conn.execute(
                "SELECT linha_status, COUNT(*) c FROM job_lines WHERE job_id=? GROUP BY linha_status",
                (job_id,),
            ).fetchall()
        counts = {r["linha_status"]: r["c"] for r in rows}
        self.update_job(
            job_id,
            total_sucesso=counts.get("ok", 0),
            total_erro=counts.get("erro", 0),
        )
