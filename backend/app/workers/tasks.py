"""Dramatiq transport for persisted SpeechEval evaluation jobs.

The database job record is the idempotency source of truth. Redis only transports an
instruction to claim that record, so duplicate delivery cannot duplicate metric results.
"""
from __future__ import annotations

from uuid import UUID

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from app.artifacts.storage import LocalArtifactStorage
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.entities import JobStatus
from app.workers.executor import execute_evaluation_job

_settings = get_settings()
_broker = RedisBroker(url=_settings.redis_url)
dramatiq.set_broker(_broker)


@dramatiq.actor(max_retries=0, time_limit=1_300_000)
def execute_evaluation_job_task(job_id: str) -> None:
    """Claim and run one durable job; reschedule persisted retries with backoff."""
    status = execute_evaluation_job(
        UUID(job_id),
        _settings.worker_id,
        session_factory=SessionLocal,
        storage=LocalArtifactStorage(),
    )
    if status == JobStatus.RETRYING:
        # Executor advances retry_count atomically in the durable job record. The
        # rescheduled message is harmless if a duplicate is delivered first.
        delay_ms = 1_000 * 2
        execute_evaluation_job_task.send_with_options(args=(job_id,), delay=delay_ms)
