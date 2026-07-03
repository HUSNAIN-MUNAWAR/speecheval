from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.listening.service import (
    activate_study,
    create_study,
    public_tasks,
    results,
    submit_response,
)
from app.models.entities import ListeningStudy
from app.schemas.contracts import ListeningResponseCreate, ListeningStudyCreate
from app.services.errors import DomainValidationError

router = APIRouter()


@router.get("")
def list_studies(project_id: str | None = None, db: Session = Depends(get_db)):
    query = select(ListeningStudy).order_by(ListeningStudy.created_at.desc())
    if project_id:
        try:
            query = query.where(ListeningStudy.project_id == UUID(project_id))
        except ValueError as exc:
            raise HTTPException(422, "project_id must be a UUID") from exc
    return {
        "items": [
            {
                "id": str(study.id),
                "project_id": str(study.project_id),
                "title": study.title,
                "state": study.state,
                "test_type": study.test_type,
                "anonymity_enabled": study.anonymity_enabled,
                "created_at": study.created_at.isoformat(),
            }
            for study in db.scalars(query)
        ]
    }


@router.post("", status_code=201)
def create(payload: ListeningStudyCreate, db: Session = Depends(get_db)):
    try:
        study = create_study(
            db,
            project_id=payload.project_id,
            title=payload.title,
            description=payload.description,
            test_type=payload.test_type,
            linked_run_ids=payload.linked_run_ids,
            selected_sample_keys=payload.selected_sample_keys,
            rating_scale=payload.rating_scale,
            rater_instructions=payload.rater_instructions,
            consent_notice=payload.consent_notice,
            randomization_seed=payload.randomization_seed,
            anonymity_enabled=payload.anonymity_enabled,
            response_limit=payload.response_limit,
        )
        return {"id": str(study.id), "state": study.state}
    except DomainValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/{study_id}/activate")
def activate(study_id: UUID, db: Session = Depends(get_db)):
    study = db.get(ListeningStudy, study_id)
    if not study:
        raise HTTPException(404, "Study not found")
    try:
        study = activate_study(db, study)
        return {"id": str(study.id), "state": study.state}
    except DomainValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/{study_id}/tasks")
def tasks(study_id: UUID, db: Session = Depends(get_db)):
    study = db.get(ListeningStudy, study_id)
    if not study:
        raise HTTPException(404, "Study not found")
    return {
        "study": {
            "id": str(study.id),
            "title": study.title,
            "state": study.state,
            "test_type": study.test_type,
            "instructions": study.rater_instructions,
            "consent_notice": study.consent_notice,
            "anonymity_enabled": study.anonymity_enabled,
        },
        "tasks": public_tasks(db, study),
    }


@router.post("/{study_id}/responses", status_code=201)
def respond(study_id: UUID, payload: ListeningResponseCreate, db: Session = Depends(get_db)):
    study = db.get(ListeningStudy, study_id)
    if not study:
        raise HTTPException(404, "Study not found")
    try:
        response = submit_response(
            db,
            study,
            task_id=payload.task_id,
            rater_key=payload.rater_key,
            preference=payload.preference,
            rating=payload.rating,
            confidence=payload.confidence,
            note=payload.note,
            duration_ms=payload.duration_ms,
        )
        return {"id": str(response.id), "created_at": response.created_at.isoformat()}
    except DomainValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/{study_id}/results")
def study_results(study_id: UUID, db: Session = Depends(get_db)):
    study = db.get(ListeningStudy, study_id)
    if not study:
        raise HTTPException(404, "Study not found")
    return results(db, study)
