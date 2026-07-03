from __future__ import annotations

import time

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.entities import EvaluationJob, JobStatus
from app.workers.executor import execute_evaluation_job


def run_worker_forever() -> None:
    settings=get_settings()
    while True:
        with SessionLocal() as db:
            job=db.scalar(select(EvaluationJob).where(EvaluationJob.status.in_([JobStatus.QUEUED,JobStatus.RETRYING])).order_by(EvaluationJob.created_at))
            job_id=job.id if job else None
        if job_id:
            execute_evaluation_job(job_id,settings.worker_id,session_factory=SessionLocal)
        else:
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    run_worker_forever()
