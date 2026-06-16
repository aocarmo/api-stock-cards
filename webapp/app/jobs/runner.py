"""Coração da lição anti-429: split em lotes → upload → poll → espera → retry.

Reimplementa em Python (assíncrono) a lógica do shell `send_batches.sh`, mas
acompanha o status via DynamoDB (por s3_key) em vez de credenciais embutidas.
"""
from __future__ import annotations

import asyncio

from app.csv_utils import build_csv
from app.validation import norm_idioma, norm_tipo


def _key(d: dict) -> tuple:
    return (
        str(d.get("numero", "")).strip(),
        str(d.get("colecao", "")).strip().upper(),
        norm_tipo(d.get("tipo", "")),
        norm_idioma(d.get("idioma", "")),
    )


class JobRunner:
    def __init__(self, store, client, tracker, settings):
        self.store = store
        self.client = client
        self.tracker = tracker
        self.s = settings

    async def run(self, job_id: str):
        job = self.store.get_job(job_id)
        if not job:
            return
        op = job["operation"]
        round_no = job.get("round", 0)
        prev_errors = None
        try:
            while True:
                if self.store.is_cancelled(job_id):
                    self.store.update_job(job_id, status="CANCELLED", mensagem="Cancelado")
                    return
                pending = self.store.get_lines(job_id, status="pending")
                if not pending:
                    break
                round_no += 1
                chunks = [pending[i:i + self.s.batch_size]
                          for i in range(0, len(pending), self.s.batch_size)]
                self.store.update_job(job_id, status="RUNNING", round=round_no,
                                      total_batches=len(chunks), current_batch=0,
                                      mensagem=f"Rodada {round_no}")
                for idx, chunk in enumerate(chunks, 1):
                    if self.store.is_cancelled(job_id):
                        self.store.update_job(job_id, status="CANCELLED", mensagem="Cancelado")
                        return
                    self.store.update_job(job_id, status="RUNNING", current_batch=idx)
                    await self._process_chunk(job_id, op, chunk, idx, len(chunks))
                    self.store.recompute_counts(job_id)
                    if idx < len(chunks):
                        self.store.update_job(job_id, status="WAITING",
                                              mensagem=f"Aguardando {self.s.batch_interval_seconds}s (anti-429)")
                        await asyncio.sleep(self.s.batch_interval_seconds)

                errors = self.store.get_lines(job_id, status="erro")
                n_err = len(errors)
                if n_err == 0:
                    break
                if round_no >= self.s.max_retry_rounds:
                    break
                if prev_errors is not None and n_err >= prev_errors:
                    break  # rodada não reduziu falhas → provavelmente reais
                prev_errors = n_err
                self.store.reset_errors_to_pending(job_id)
                self.store.update_job(job_id, status="RETRYING",
                                      mensagem=f"Retry de {n_err} falhas")

            self.store.recompute_counts(job_id)
            job = self.store.get_job(job_id)
            final = "COMPLETED" if job["total_erro"] == 0 else "COMPLETED_WITH_ERRORS"
            msg = ("Concluído sem erros" if job["total_erro"] == 0
                   else f"Concluído com {job['total_erro']} falha(s)")
            self.store.update_job(job_id, status=final, mensagem=msg)
        except Exception as e:  # noqa: BLE001
            self.store.update_job(job_id, status="FAILED", mensagem=f"Erro: {e}")

    async def _process_chunk(self, job_id, op, chunk, idx, total):
        csv_bytes = build_csv(chunk, op)
        filename = f"job_{job_id[:8]}_b{idx}.csv"
        resp = await self.client.upload_mass(csv_bytes, filename, op)
        s3_key = resp.get("s3_key")
        record = await self._poll(s3_key)

        if not record or record.get("status") == "FAILED":
            for line in chunk:
                self.store.set_line_status(line["id"], "erro", "falha_processamento")
            return

        error_keys = {}
        for e in record.get("linhas_erro", []) or []:
            error_keys[_key(e)] = e.get("status", "erro")
        for line in chunk:
            k = _key(line)
            if k in error_keys:
                self.store.set_line_status(line["id"], "erro", error_keys[k])
            else:
                self.store.set_line_status(line["id"], "ok", "")

    async def _poll(self, s3_key: str) -> dict | None:
        elapsed = 0
        record = None
        while elapsed < self.s.poll_timeout_seconds:
            record = await asyncio.to_thread(self.tracker.get_by_s3_key, s3_key)
            if record and record.get("status") in ("COMPLETED", "FAILED"):
                return record
            await asyncio.sleep(self.s.poll_interval_seconds)
            elapsed += self.s.poll_interval_seconds
        return record
