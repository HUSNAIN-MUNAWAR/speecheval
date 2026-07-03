from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.entities import Baseline, EvaluationRun
from app.schemas.contracts import BaselineCreate, BaselineResponse
from app.services.errors import DomainValidationError
from app.services.evidence import create_baseline, freeze_baseline

router = APIRouter()


@router.get("", response_model=list[BaselineResponse])
def list_baselines(project_id: str | None = None, db: Session = Depends(get_db)):
    query = select(Baseline).order_by(Baseline.created_at.desc())
    if project_id:
        try:
            query = query.where(Baseline.project_id == UUID(project_id))
        except ValueError as exc:
            raise HTTPException(422, "project_id must be a UUID") from exc
    return list(db.scalars(query))


@router.post("", response_model=BaselineResponse, status_code=201)
def create(payload: BaselineCreate, db: Session = Depends(get_db)):
    run = db.get(EvaluationRun, payload.run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    try:
        return create_baseline(db, payload.project_id, run, payload.name)
    except DomainValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/{baseline_id}/freeze", response_model=BaselineResponse)
def freeze(baseline_id: UUID, db: Session = Depends(get_db)):
    baseline = db.get(Baseline, baseline_id)
    if not baseline:
        raise HTTPException(404, "Baseline not found")
    return freeze_baseline(db, baseline)
