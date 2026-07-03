from fastapi import Request

from app.db.session import get_db


def request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))


__all__ = ["get_db", "request_id"]
