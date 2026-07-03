from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.entities import EvaluationRun, RegressionPolicy
from app.schemas.contracts import RegressionPolicyCreate, RegressionPolicyResponse
from app.services.evidence import create_policy, evaluate_policy

router = APIRouter()


@router.get("", response_model=list[RegressionPolicyResponse])
def list_policies(project_id: str | None = None, db: Session = Depends(get_db)):
    query = select(RegressionPolicy).order_by(RegressionPolicy.created_at.desc())
    if project_id:
        try:
            query = query.where(RegressionPolicy.project_id == UUID(project_id))
        except ValueError as exc:
            raise HTTPException(422, "project_id must be a UUID") from exc
    return list(db.scalars(query))


@router.post("", response_model=RegressionPolicyResponse, status_code=201)
def create(payload: RegressionPolicyCreate, db: Session = Depends(get_db)):
    return create_policy(db, **payload.model_dump())


@router.post("/{policy_id}/test")
def test(policy_id: UUID, run_id: UUID, db: Session = Depends(get_db)):
    policy = db.get(RegressionPolicy, policy_id)
    run = db.get(EvaluationRun, run_id)
    if not policy or not run:
        raise HTTPException(404, "Policy or run not found")
    result = evaluate_policy(db, policy, run)
    db.add(result)
    db.commit()
    db.refresh(result)
    return {
        "id": str(result.id),
        "integrity_status": result.integrity_status,
        "decision": result.decision,
        "observed_value": result.observed_value,
        "baseline_value": result.baseline_value,
        "absolute_delta": result.absolute_delta,
        "relative_delta": result.relative_delta,
        "confidence_interval": result.confidence_interval_json,
        "sample_count": result.sample_count,
        "explanation": result.explanation,
    }
