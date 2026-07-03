from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "speecheval-api"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "reachable"}


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": "0.1.0", "environment": get_settings().environment}
