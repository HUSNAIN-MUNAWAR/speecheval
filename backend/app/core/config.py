from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    api_prefix: str
    database_url: str
    redis_url: str
    queue_mode: str
    cors_origins: tuple[str, ...]
    artifact_root: Path
    demo_mode: bool
    worker_id: str
    worker_poll_seconds: float
    max_upload_size_mb: int
    max_audio_duration_seconds: int
    enable_prometheus: bool

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in {"development", "test"}

    @property
    def uses_redis_queue(self) -> bool:
        return self.queue_mode == "dramatiq"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    root = Path(__file__).resolve().parents[3]
    artifact_root = Path(os.getenv("SPEECHEVAL_ARTIFACT_ROOT", "./.artifacts"))
    if not artifact_root.is_absolute():
        artifact_root = (root / artifact_root).resolve()
    queue_mode = os.getenv("SPEECHEVAL_QUEUE_MODE", "inline").strip().lower()
    if queue_mode not in {"inline", "dramatiq"}:
        raise ValueError("SPEECHEVAL_QUEUE_MODE must be either 'inline' or 'dramatiq'.")
    origins = tuple(
        value.strip()
        for value in os.getenv("SPEECHEVAL_CORS_ORIGINS", "http://localhost:3000").split(",")
        if value.strip()
    )
    return Settings(
        environment=os.getenv("SPEECHEVAL_ENV", "development"),
        api_prefix=os.getenv("SPEECHEVAL_API_PREFIX", "/api/v1"),
        database_url=os.getenv("SPEECHEVAL_DATABASE_URL", "sqlite:///./.data/speecheval.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        queue_mode=queue_mode,
        cors_origins=origins,
        artifact_root=artifact_root,
        demo_mode=os.getenv("SPEECHEVAL_DEMO_MODE", "true").lower() == "true",
        worker_id=os.getenv("SPEECHEVAL_WORKER_ID", "local-worker"),
        worker_poll_seconds=float(os.getenv("SPEECHEVAL_WORKER_POLL_SECONDS", "0.6")),
        max_upload_size_mb=int(os.getenv("SPEECHEVAL_MAX_UPLOAD_SIZE_MB", "100")),
        max_audio_duration_seconds=int(os.getenv("SPEECHEVAL_MAX_AUDIO_DURATION_SECONDS", "300")),
        enable_prometheus=os.getenv("SPEECHEVAL_ENABLE_PROMETHEUS", "true").lower() == "true",
    )
