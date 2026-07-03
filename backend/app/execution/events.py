from __future__ import annotations

import json
from datetime import UTC
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import EvaluationEvent


def emit_event(
    db: Session,
    run_id: UUID,
    event_type: str,
    message: str,
    *,
    job_id: UUID | None = None,
    stage: str | None = None,
    level: str = "info",
    payload: dict[str, object] | None = None,
) -> EvaluationEvent:
    sequence = (db.scalar(select(func.max(EvaluationEvent.sequence)).where(EvaluationEvent.run_id == run_id)) or 0) + 1
    event = EvaluationEvent(
        run_id=run_id,
        job_id=job_id,
        sequence=sequence,
        event_type=event_type,
        stage=stage,
        level=level,
        message=message,
        payload_json=payload or {},
    )
    db.add(event)
    db.flush()
    return event


def event_payload(event: EvaluationEvent) -> dict[str, object]:
    created_at = event.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return {
        "id": str(event.id),
        "sequence": event.sequence,
        "type": event.event_type,
        "stage": event.stage,
        "level": event.level,
        "message": event.message,
        "payload": event.payload_json,
        "created_at": created_at.isoformat(),
    }


def sse_event(event: EvaluationEvent) -> str:
    return f"id: {event.sequence}\nevent: {event.event_type}\ndata: {json.dumps(event_payload(event), ensure_ascii=False)}\n\n"
