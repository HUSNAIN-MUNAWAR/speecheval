from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def build_engine(url: str | None = None) -> Engine:
    database_url = url or get_settings().database_url
    if database_url.startswith("sqlite:///"):
        location = database_url.removeprefix("sqlite:///")
        if location and location != ":memory:":
            Path(location).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        pool_pre_ping=True,
    )


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
