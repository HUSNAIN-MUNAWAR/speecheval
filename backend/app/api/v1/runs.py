from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, request_id
from app.artifacts.storage import ArtifactPathError, LocalArtifactStorage
from app.comparison.integrity import assess_integrity
from app.execution.events import event_payload, sse_event
from app.execution.runtime import create_evaluation_job, request_cancel, rerun_clone
from app.models.entities import (
    Artifact,
    EvaluationCase,
    EvaluationEvent,
    EvaluationRun,
    RunStatus,
    SampleMetricResult,
)
from app.reporting.cards import create_benchmark_card
from app.schemas.common import Page
from app.schemas.contracts import RunCreate, RunEnqueueResponse, RunResponse
from app.services.domain import create_run, list_runs, must_get
from app.services.errors import DomainNotFoundError, DomainValidationError
from app.workers.queue import dispatch_evaluation_job

router = APIRouter()


def err(error: Exception, req: Request) -> HTTPException:
    code = "not_found" if isinstance(error, DomainNotFoundError) else "validation_error"
    return HTTPException(404 if code == "not_found" else 422, {"code": code, "message": str(error), "request_id": request_id(req)})


@router.get("", response_model=Page[RunResponse])
def read(project_id: str | None = None, status_filter: RunStatus | None = Query(None, alias="status"), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    rows,total=list_runs(db,project_id,status_filter,limit,offset);return Page(items=rows,total=total,limit=limit,offset=offset)


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def create(payload:RunCreate,req:Request,db:Session=Depends(get_db)):
    try:return create_run(db,payload)
    except (DomainNotFoundError,DomainValidationError) as exc:raise err(exc,req) from exc


@router.get("/{run_id}",response_model=RunResponse)
def get(run_id:str,req:Request,db:Session=Depends(get_db)):
    try:return must_get(db,EvaluationRun,run_id,"EvaluationRun")
    except DomainNotFoundError as exc:raise err(exc,req) from exc


@router.post("/{run_id}/enqueue",response_model=RunEnqueueResponse)
def enqueue(run_id:str,req:Request,db:Session=Depends(get_db)):
    try:
        run=must_get(db,EvaluationRun,run_id,"EvaluationRun");job=create_evaluation_job(db,run)
        dispatch_evaluation_job(job.id)
        return RunEnqueueResponse(run_id=run.id,job_id=job.id,status=run.status,manifest_hash=run.manifest_hash)
    except (DomainNotFoundError,DomainValidationError,ValueError) as exc:raise err(exc,req) from exc


@router.post("/{run_id}/cancel",response_model=RunResponse)
def cancel(run_id:str,req:Request,db:Session=Depends(get_db)):
    try:return request_cancel(db,must_get(db,EvaluationRun,run_id,"EvaluationRun"))
    except (DomainNotFoundError,DomainValidationError) as exc:raise err(exc,req) from exc


@router.post("/{run_id}/rerun",response_model=RunResponse,status_code=status.HTTP_201_CREATED)
def rerun(run_id:str,req:Request,db:Session=Depends(get_db)):
    try:return rerun_clone(db,must_get(db,EvaluationRun,run_id,"EvaluationRun"))
    except (DomainNotFoundError,DomainValidationError) as exc:raise err(exc,req) from exc


@router.get("/{run_id}/events")
async def events(run_id:str,after:int=0,db:Session=Depends(get_db)):
    must_get(db,EvaluationRun,run_id,"EvaluationRun")
    run_uuid=UUID(run_id)
    async def stream():
        cursor=after
        for _ in range(60):
            rows=list(db.scalars(select(EvaluationEvent).where(EvaluationEvent.run_id==run_uuid,EvaluationEvent.sequence>cursor).order_by(EvaluationEvent.sequence)))
            for event in rows:
                cursor=event.sequence;yield sse_event(event)
            if not rows:yield ": heartbeat\n\n"
            await asyncio.sleep(.5)
    return StreamingResponse(stream(),media_type="text/event-stream",headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})


@router.get("/{run_id}/events/history")
def event_history(run_id:str,after:int=0,db:Session=Depends(get_db)):
    run=must_get(db,EvaluationRun,run_id,"EvaluationRun")
    return {"items":[event_payload(event) for event in db.scalars(select(EvaluationEvent).where(EvaluationEvent.run_id==run.id,EvaluationEvent.sequence>after).order_by(EvaluationEvent.sequence))]}


@router.get("/{run_id}/samples")
def samples(run_id:str,language:str|None=None,failed_only:bool=False,db:Session=Depends(get_db)):
    run=must_get(db,EvaluationRun,run_id,"EvaluationRun")
    query=select(EvaluationCase).where(EvaluationCase.run_id==run.id).order_by(EvaluationCase.sample_key)
    if language:query=query.where(EvaluationCase.language==language)
    cases=list(db.scalars(query))
    items=[]
    for case in cases:
        metrics=list(db.scalars(select(SampleMetricResult).where(SampleMetricResult.evaluation_case_id==case.id)))
        failed=case.status.value in {"FAILED","PARTIAL"} or any(metric.status.value=="FAILED" for metric in metrics)
        if failed_only and not failed:continue
        items.append({"id":str(case.id),"sample_key":case.sample_key,"language":case.language,"expected_text":case.expected_text,"transcript":case.transcript,"status":case.status.value,"reviewed":case.reviewed_at is not None,"metrics":[{"id":m.metric_id,"value":m.value,"unit":m.unit,"status":m.status.value,"metadata":m.metadata_json,"warnings":m.warnings,"error":m.error_message} for m in metrics]})
    return {"items":items,"total":len(items)}


@router.post("/{run_id}/samples/{sample_id}/review")
def review_sample(run_id:str,sample_id:str,payload:dict[str,str]|None=None,db:Session=Depends(get_db)):
    run=must_get(db,EvaluationRun,run_id,"EvaluationRun");case=must_get(db,EvaluationCase,sample_id,"EvaluationCase")
    if case.run_id!=run.id:raise HTTPException(404,{"code":"not_found","message":"Sample is not part of run."})
    case.reviewed_at=datetime.now(UTC);case.review_note=(payload or {}).get("note");db.commit();return {"id":str(case.id),"reviewed":True}


@router.get("/{run_id}/artifacts")
def artifacts(run_id:str,db:Session=Depends(get_db)):
    run=must_get(db,EvaluationRun,run_id,"EvaluationRun")
    return {"items":[{"id":str(item.id),"kind":item.kind.value,"storage_key":item.storage_key,"content_hash":item.content_hash,"content_type":item.content_type,"size_bytes":item.size_bytes,"created_at":item.created_at.isoformat()} for item in db.scalars(select(Artifact).where(Artifact.run_id==run.id))]}


@router.get("/{run_id}/manifest")
def manifest(run_id:str,db:Session=Depends(get_db)):
    run=must_get(db,EvaluationRun,run_id,"EvaluationRun");return {"manifest":run.immutable_manifest,"hash":run.manifest_hash}


@router.get("/{run_id}/integrity")
def integrity(run_id:str,baseline_run_id:str|None=None,db:Session=Depends(get_db)):
    run=must_get(db,EvaluationRun,run_id,"EvaluationRun")
    if not baseline_run_id:return {"status":"SELF_DESCRIBED","reasons":["Select a baseline run for comparative integrity checks."]}
    baseline=must_get(db,EvaluationRun,baseline_run_id,"EvaluationRun");assessment=assess_integrity(run,baseline);return {"status":assessment.status.value,"reasons":assessment.reasons}


@router.get("/{run_id}/benchmark-card")
def benchmark_card(run_id:str,baseline_run_id:str|None=None,db:Session=Depends(get_db)):
    run=must_get(db,EvaluationRun,run_id,"EvaluationRun");baseline=must_get(db,EvaluationRun,baseline_run_id,"EvaluationRun") if baseline_run_id else None
    card=create_benchmark_card(db,run,baseline);return {"id":str(card.id),"integrity_status":card.integrity_status,"content":card.content_json,"markdown":card.markdown,"html":card.html}


@router.get("/{run_id}/audio/{storage_key:path}")
def audio(run_id:str,storage_key:str,db:Session=Depends(get_db)):
    must_get(db,EvaluationRun,run_id,"EvaluationRun")
    try:path=LocalArtifactStorage().resolve(storage_key)
    except ArtifactPathError as exc:raise HTTPException(400,{"code":"unsafe_storage_key","message":str(exc)}) from exc
    if not path.is_file():raise HTTPException(404,{"code":"not_found","message":"Audio artifact not found."})
    return FileResponse(path,media_type="audio/wav",filename=path.name)


@router.get("/{run_id}/logs",response_class=PlainTextResponse)
def logs(run_id:str,db:Session=Depends(get_db)):
    run=must_get(db,EvaluationRun,run_id,"EvaluationRun");lines=[]
    for event in db.scalars(select(EvaluationEvent).where(EvaluationEvent.run_id==run.id).order_by(EvaluationEvent.sequence)):
        lines.append(f"{event.created_at.isoformat()} [{event.level}] {event.stage or '-'} {event.message}")
    return "\n".join(lines)
