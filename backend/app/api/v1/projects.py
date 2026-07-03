from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, request_id
from app.models.entities import Project
from app.schemas.common import Page
from app.schemas.contracts import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.domain import create_project, list_projects, must_get, update_project
from app.services.errors import DomainNotFoundError

router = APIRouter()


def missing(e: Exception, req: Request):
    return HTTPException(
        404, {"code": "not_found", "message": str(e), "request_id": request_id(req)}
    )


@router.get("", response_model=Page[ProjectResponse])
def read(
    workspace_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total = list_projects(db, workspace_id, limit, offset)
    return Page(items=rows, total=total, limit=limit, offset=offset)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create(payload: ProjectCreate, req: Request, db: Session = Depends(get_db)):
    try:
        return create_project(db, payload)
    except DomainNotFoundError as e:
        raise missing(e, req) from e


@router.get("/{project_id}", response_model=ProjectResponse)
def get(project_id: str, req: Request, db: Session = Depends(get_db)):
    try:
        return must_get(db, Project, project_id, "Project")
    except DomainNotFoundError as e:
        raise missing(e, req) from e


@router.patch("/{project_id}", response_model=ProjectResponse)
def update(project_id: str, payload: ProjectUpdate, req: Request, db: Session = Depends(get_db)):
    try:
        return update_project(db, must_get(db, Project, project_id, "Project"), payload)
    except DomainNotFoundError as e:
        raise missing(e, req) from e
