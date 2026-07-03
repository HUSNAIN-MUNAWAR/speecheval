from __future__ import annotations

import threading
from uuid import UUID

from app.artifacts.storage import LocalArtifactStorage
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.workers.executor import execute_evaluation_job


def dispatch_evaluation_job(job_id: UUID, *, wait_for_inline: bool = False) -> None:
    """Dispatch a durable job through Dramatiq or the local CPU-safe inline transport.

    Both paths call the same executor. A persisted `EvaluationJob` record guards
    idempotency, retries, cancellation, and auditability independently of the transport.
    """
    settings = get_settings()
    if settings.uses_redis_queue:
        from app.workers.tasks import execute_evaluation_job_task

        execute_evaluation_job_task.send(str(job_id))
        return

    def work() -> None:
        execute_evaluation_job(
            job_id,
            settings.worker_id,
            session_factory=SessionLocal,
            storage=LocalArtifactStorage(),
        )

    if wait_for_inline:
        work()
        return
    thread = threading.Thread(target=work, daemon=True, name=f"speecheval-job-{job_id}")
    thread.start()
