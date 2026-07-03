from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.comparison.service import comparison_payload, create_comparison
from app.models.entities import Comparison, EvaluationRun
from app.schemas.contracts import ComparisonCreate
from app.services.errors import DomainValidationError

router = APIRouter()


@router.post("", status_code=201)
def create(payload: ComparisonCreate, db: Session = Depends(get_db)):
    candidate = db.get(EvaluationRun, payload.candidate_run_id)
    baseline = db.get(EvaluationRun, payload.baseline_run_id)
    if not candidate or not baseline:
        raise HTTPException(404, "Candidate or baseline run not found")
    try:
        comparison = create_comparison(
            db,
            candidate,
            baseline,
            language_filter=payload.language_filter,
            tag_filter=payload.tag_filter,
        )
    except DomainValidationError as exc:
        raise HTTPException(422, str(exc)) from exc
    return comparison_payload(db, comparison)


@router.get("/{comparison_id}")
def get(comparison_id: UUID, db: Session = Depends(get_db)):
    comparison = db.get(Comparison, comparison_id)
    if not comparison:
        raise HTTPException(404, "Comparison not found")
    return comparison_payload(db, comparison)


@router.get("/{comparison_id}/integrity")
def integrity(comparison_id: UUID, db: Session = Depends(get_db)):
    comparison = db.get(Comparison, comparison_id)
    if not comparison:
        raise HTTPException(404, "Comparison not found")
    return {
        "status": comparison.integrity_status,
        "reasons": comparison.integrity_reasons,
    }
