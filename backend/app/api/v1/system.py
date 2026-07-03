from __future__ import annotations

import socket
from datetime import UTC, datetime
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.artifacts.storage import LocalArtifactStorage
from app.core.config import get_settings
from app.execution.profiles import PROFILES, serialize_profile
from app.metrics import registry
from app.models.entities import EvaluationJob, JobStatus, Worker
from app.observability.metrics import artifact_storage_bytes, queue_depth, render_prometheus

router=APIRouter()


def _utc(value:datetime)->datetime:return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


@router.get("/worker-status")
def worker_status(db:Session=Depends(get_db)):
    workers=list(db.scalars(select(Worker).order_by(Worker.last_heartbeat_at.desc())))
    queued=db.scalar(select(func.count()).select_from(EvaluationJob).where(EvaluationJob.status.in_([JobStatus.QUEUED,JobStatus.RETRYING]))) or 0
    if queue_depth:queue_depth.set(queued)
    return {"queue_mode":get_settings().queue_mode,"queued_jobs":queued,"worker_count":len(workers),"workers":[{"worker_id":w.worker_key,"profile":w.profile_id,"status":w.status.value,"last_heartbeat_at":_utc(w.last_heartbeat_at).isoformat() if w.last_heartbeat_at else None,"capabilities":w.capabilities_json} for w in workers]}


@router.get("/workers")
def workers(db:Session=Depends(get_db)):
    return worker_status(db)


@router.get("/execution-profiles")
def execution_profiles():return {"profiles":[serialize_profile(profile) for profile in PROFILES.values()]}


@router.get("/plugins")
def plugins():return {"plugins":registry.describe_all()}


@router.get("/metrics")
def metrics():
    if not get_settings().enable_prometheus:return Response(status_code=404)
    return Response(render_prometheus(),media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get("/storage-status")
def storage_status():
    storage=LocalArtifactStorage();total=sum(path.stat().st_size for path in storage.root.rglob('*') if path.is_file())
    if artifact_storage_bytes:artifact_storage_bytes.set(total)
    return {"backend":"local_filesystem","writable":storage.root.is_dir(),"bytes_used":total}


def _redis_health() -> str:
    settings = get_settings()
    if settings.queue_mode == "inline":
        return "not_required"
    parsed = urlparse(settings.redis_url)
    host = parsed.hostname
    port = parsed.port or 6379
    if not host:
        return "misconfigured"
    try:
        with socket.create_connection((host, port), timeout=0.5) as connection:
            connection.sendall(b"*1\r\n$4\r\nPING\r\n")
            response = connection.recv(32)
        return "healthy" if response.startswith(b"+PONG") else "reachable"
    except OSError:
        return "unavailable"


@router.get("/health")
def health(db:Session=Depends(get_db)):
    try:db.execute(text('SELECT 1'));database='healthy'
    except Exception:database='unavailable'
    return {"api":"healthy","database":database,"redis":_redis_health(),"workers":worker_status(db),"storage":storage_status(),"metric_plugin_count":len(registry.plugins)}
