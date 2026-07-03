from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, request_id
from app.models.entities import Dataset
from app.schemas.common import Page
from app.schemas.contracts import (
    DatasetCreate,
    DatasetItemResponse,
    DatasetResponse,
    DatasetVersionCreate,
    DatasetVersionResponse,
)
from app.services.domain import (
    create_dataset,
    create_dataset_version,
    list_dataset_items,
    list_datasets,
    must_get,
    validate_manifest_items,
)
from app.services.errors import DomainConflictError, DomainNotFoundError

router = APIRouter()


def err(e: Exception, req: Request):
    code = "not_found" if isinstance(e, DomainNotFoundError) else "conflict"
    return HTTPException(
        404 if code == "not_found" else 409,
        {"code": code, "message": str(e), "request_id": request_id(req)},
    )


@router.get("", response_model=Page[DatasetResponse])
def read(
    project_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total = list_datasets(db, project_id, limit, offset)
    return Page(items=rows, total=total, limit=limit, offset=offset)


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create(payload: DatasetCreate, req: Request, db: Session = Depends(get_db)):
    try:
        return create_dataset(db, payload)
    except DomainNotFoundError as e:
        raise err(e, req) from e


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get(dataset_id: str, req: Request, db: Session = Depends(get_db)):
    try:
        return must_get(db, Dataset, dataset_id, "Dataset")
    except DomainNotFoundError as e:
        raise err(e, req) from e


@router.post(
    "/{dataset_id}/versions",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def version(
    dataset_id: str, payload: DatasetVersionCreate, req: Request, db: Session = Depends(get_db)
):
    try:
        return create_dataset_version(db, must_get(db, Dataset, dataset_id, "Dataset"), payload)
    except (DomainNotFoundError, DomainConflictError) as e:
        raise err(e, req) from e


@router.get("/{dataset_id}/items", response_model=Page[DatasetItemResponse])
def items(
    dataset_id: str,
    req: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        rows, total = list_dataset_items(db, dataset_id, limit, offset)
    except DomainNotFoundError as e:
        raise err(e, req) from e
    return Page(items=rows, total=total, limit=limit, offset=offset)


@router.post("/validate")
def validate(payload: DatasetVersionCreate):
    errors = validate_manifest_items([item.model_dump() for item in payload.items])
    return {"valid": not errors, "errors": errors, "item_count": len(payload.items)}
