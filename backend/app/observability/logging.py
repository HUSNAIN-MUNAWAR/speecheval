from __future__ import annotations

import json
import logging
import sys
from typing import Any

_SECRET_MARKERS = ("token", "secret", "password", "authorization", "api_key")


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if any(mark in key.lower() for mark in _SECRET_MARKERS) else _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname.lower(), "message": record.getMessage(), "logger": record.name}
        context = getattr(record, "context", None)
        if isinstance(context, dict):
            payload.update(_safe(context))
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)
