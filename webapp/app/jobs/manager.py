"""Gerencia ciclo de vida dos jobs em massa. Serializa execução (1 por vez)."""
import asyncio
import uuid
from datetime import datetime


class JobManager:
    def __init__(self, store, runner):
        self.store = store
        self.runner = runner
        self._lock = asyncio.Lock()  # garante 1 job em massa por vez (evita 429)
        self._tasks: dict[str, asyncio.Task] = {}

    def _new_id(self) -> str:
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    def create_and_start(self, operation: str, cards: list[dict]) -> str:
        job_id = self._new_id()
        self.store.create_job(job_id, operation, cards)
        self._schedule(job_id)
        return job_id

    def _schedule(self, job_id: str):
        task = asyncio.create_task(self._run_guarded(job_id))
        self._tasks[job_id] = task
        task.add_done_callback(lambda t: self._tasks.pop(job_id, None))

    async def _run_guarded(self, job_id: str):
        async with self._lock:
            if self.store.is_cancelled(job_id):
                return
            await self.runner.run(job_id)

    def retry(self, job_id: str) -> bool:
        job = self.store.get_job(job_id)
        if not job or job["status"] in ("RUNNING", "WAITING", "RETRYING", "PENDING"):
            return False
        self.store.reset_errors_to_pending(job_id)
        self.store.update_job(job_id, status="PENDING", cancel_requested=0,
                              mensagem="Reenfileirado para retry")
        self._schedule(job_id)
        return True

    def cancel(self, job_id: str) -> bool:
        job = self.store.get_job(job_id)
        if not job:
            return False
        self.store.request_cancel(job_id)
        return True

    async def resume_active(self):
        """No startup, retoma jobs que ficaram ativos após um reload."""
        for job_id in self.store.active_job_ids():
            self.store.update_job(job_id, status="PENDING", mensagem="Retomado após reinício")
            self._schedule(job_id)
