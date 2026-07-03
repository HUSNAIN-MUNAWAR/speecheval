from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, request_id
from app.models.entities import TTSModel
from app.schemas.common import Page
from app.schemas.contracts import (
    ModelCreate,
    ModelResponse,
    ModelVersionCreate,
    ModelVersionResponse,
)
from app.services.domain import create_model, create_model_version, list_models, must_get
from app.services.errors import DomainConflictError, DomainNotFoundError

router = APIRouter()


def err(e: Exception, req: Request):
    code = "not_found" if isinstance(e, DomainNotFoundError) else "conflict"
    return HTTPException(
        404 if code == "not_found" else 409,
        {"code": code, "message": str(e), "request_id": request_id(req)},
    )


@router.get("", response_model=Page[ModelResponse])
def read(
    project_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total = list_models(db, project_id, limit, offset)
    return Page(items=rows, total=total, limit=limit, offset=offset)


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def create(payload: ModelCreate, req: Request, db: Session = Depends(get_db)):
    try:
        return create_model(db, payload)
    except DomainNotFoundError as e:
        raise err(e, req) from e


@router.get("/{model_id}", response_model=ModelResponse)
def get(model_id: str, req: Request, db: Session = Depends(get_db)):
    try:
        return must_get(db, TTSModel, model_id, "Model")
    except DomainNotFoundError as e:
        raise err(e, req) from e


@router.post(
    "/{model_id}/versions", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED
)
def version(
    model_id: str, payload: ModelVersionCreate, req: Request, db: Session = Depends(get_db)
):
    try:
        return create_model_version(db, must_get(db, TTSModel, model_id, "Model"), payload)
    except (DomainNotFoundError, DomainConflictError) as e:
        raise err(e, req) from e
