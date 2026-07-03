from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.execution.events import emit_event
from app.execution.lifecycle import transition_run
from app.execution.profiles import get_profile
from app.models.entities import EvaluationJob, EvaluationRun, JobStatus, RunStatus
from app.services.errors import DomainValidationError


def stable_hash(payload: object) -> str:
    body=json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",",":"))
    return "sha256:"+hashlib.sha256(body.encode()).hexdigest()


def frozen_manifest(run: EvaluationRun) -> dict[str, object]:
    dataset=run.dataset_version; model_version=run.model_version; model=model_version.model
    return {
        "speecheval_manifest_version":"2.0",
        "run_id":str(run.id),
        "project":{"id":str(run.project_id),"name":run.project.name},
        "dataset":{"id":str(dataset.dataset_id),"version":dataset.version,"content_hash":dataset.manifest_hash,"item_count":dataset.item_count},
        "model":{"id":str(model.id),"name":model.name,"version":model_version.version,"git_sha":model_version.git_sha,"image_digest":model_version.docker_image_tag},
        "adapter":{"id":"artifact-only","version":"1.0.0"},
        "execution":{"profile":run.execution_profile_id,"python":sys.version.split()[0],"os":platform.platform(),"cpu":platform.processor() or "unknown","timestamp":datetime.now(UTC).isoformat()},
        "metrics":[{"id":metric,"version":"1.0.0","parameters":{}} for metric in run.selected_metrics],
        "source":{"app_version":"0.2.0","timestamp":datetime.now(UTC).isoformat()},
        "artifacts":{"storage_backend":"local","hash_algorithm":"sha256"},
    }


def validate_run_for_enqueue(run: EvaluationRun) -> None:
    if run.status != RunStatus.DRAFT:
        raise DomainValidationError(f"Only DRAFT runs can be enqueued; run is {run.status}.")
    profile=get_profile(run.execution_profile_id)
    unavailable=sorted(set(run.selected_metrics)-set(profile.capabilities))
    if unavailable:
        raise DomainValidationError(f"Profile '{profile.id}' cannot run requested metrics: {', '.join(unavailable)}.")
    if run.total_items <= 0:
        raise DomainValidationError("Evaluation run has no dataset items.")


def create_evaluation_job(db: Session, run: EvaluationRun) -> EvaluationJob:
    validate_run_for_enqueue(run)
    transition_run(run, RunStatus.VALIDATING)
    manifest=frozen_manifest(run)
    run.immutable_manifest=manifest
    run.manifest_hash=stable_hash(manifest)
    transition_run(run, RunStatus.QUEUED)
    existing=db.scalar(select(EvaluationJob).where(EvaluationJob.run_id==run.id, EvaluationJob.status.in_([JobStatus.QUEUED,JobStatus.CLAIMED,JobStatus.RUNNING,JobStatus.RETRYING])))
    if existing:
        return existing
    job=EvaluationJob(run_id=run.id,idempotency_key=f"run:{run.id}:attempt:1",attempt=1,status=JobStatus.QUEUED)
    db.add(job); db.flush()
    emit_event(db,run.id,"run.queued","Evaluation job queued.",job_id=job.id,stage="QUEUED",payload={"profile":run.execution_profile_id,"manifest_hash":run.manifest_hash})
    db.commit(); db.refresh(job); return job


def request_cancel(db:Session,run:EvaluationRun)->EvaluationRun:
    if run.status in {RunStatus.COMPLETED,RunStatus.PARTIAL,RunStatus.FAILED,RunStatus.CANCELLED}:
        raise DomainValidationError(f"Run in state {run.status} cannot be cancelled.")
    run.cancellation_requested=True
    for job in db.scalars(select(EvaluationJob).where(EvaluationJob.run_id==run.id,EvaluationJob.status.in_([JobStatus.QUEUED,JobStatus.CLAIMED,JobStatus.RUNNING,JobStatus.RETRYING]))):
        job.cancel_requested=True
    emit_event(db,run.id,"run.cancel_requested","Cancellation will be checked between samples.",stage=run.current_stage)
    db.commit(); db.refresh(run); return run


def rerun_clone(db:Session,run:EvaluationRun)->EvaluationRun:
    if run.status not in {RunStatus.COMPLETED,RunStatus.PARTIAL,RunStatus.FAILED,RunStatus.CANCELLED}:
        raise DomainValidationError("Only terminal runs can be rerun.")
    clone=EvaluationRun(project_id=run.project_id,dataset_version_id=run.dataset_version_id,model_version_id=run.model_version_id,rerun_of_id=run.id,name=f"{run.name} · rerun",selected_metrics=list(run.selected_metrics),execution_environment=dict(run.execution_environment),execution_profile_id=run.execution_profile_id,total_items=run.total_items,immutable_manifest={"rerun_of":str(run.id),"schema_version":"2.0"})
    db.add(clone);db.commit();db.refresh(clone);return clone
