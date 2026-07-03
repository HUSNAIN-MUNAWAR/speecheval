from __future__ import annotations

import math
import statistics
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.artifacts.storage import LocalArtifactStorage
from app.execution.events import emit_event
from app.execution.lifecycle import transition_run
from app.execution.runtime import frozen_manifest
from app.metrics import registry
from app.metrics.base import EvaluationContext, EvaluationItem, MetricStatus
from app.models.entities import (
    Artifact,
    ArtifactKind,
    DatasetItem,
    EvaluationCase,
    EvaluationCaseStatus,
    EvaluationJob,
    EvaluationRun,
    JobStatus,
    MetricResultStatus,
    RunAggregateMetric,
    RunStatus,
    SampleMetricResult,
    Worker,
    WorkerStatus,
)
from app.observability.metrics import (
    audio_validation_failures_total,
    metric_duration_seconds,
    runs_failed_total,
)

_STATUS_MAP={MetricStatus.SUCCESS:MetricResultStatus.SUCCESS,MetricStatus.SKIPPED:MetricResultStatus.SKIPPED,MetricStatus.UNAVAILABLE:MetricResultStatus.UNAVAILABLE,MetricStatus.FAILED:MetricResultStatus.FAILED,MetricStatus.MOCK:MetricResultStatus.MOCK,MetricStatus.ESTIMATED:MetricResultStatus.ESTIMATED}


def _worker(db:Session, worker_key:str, profile_id:str)->Worker:
    worker=db.scalar(select(Worker).where(Worker.worker_key==worker_key))
    if worker is None:
        worker=Worker(worker_key=worker_key,profile_id=profile_id,status=WorkerStatus.ONLINE,capabilities_json={"profile":profile_id})
        db.add(worker);db.flush()
    worker.status=WorkerStatus.BUSY;worker.profile_id=profile_id;worker.last_heartbeat_at=datetime.now(UTC);return worker


def _aggregate(db:Session,run:EvaluationRun)->None:
    rows=list(db.scalars(select(SampleMetricResult).join(EvaluationCase).where(EvaluationCase.run_id==run.id)))
    grouped:dict[str,list[float]]={}
    statuses:dict[str,list[MetricResultStatus]]={}
    for row in rows:
        statuses.setdefault(row.metric_id,[]).append(row.status)
        if row.value is not None and row.status in {MetricResultStatus.SUCCESS,MetricResultStatus.MOCK,MetricResultStatus.ESTIMATED}:
            grouped.setdefault(row.metric_id,[]).append(float(row.value))
    summary:dict[str,dict[str,float|int|str|None]]={}
    for metric_id, values in grouped.items():
        ordered=sorted(values); p95=ordered[min(len(ordered)-1,max(0,math.ceil(len(ordered)*.95)-1))]
        record=RunAggregateMetric(run_id=run.id,metric_id=metric_id,metric_version="1.0.0",status=MetricResultStatus.SUCCESS,sample_count=len(values),excluded_sample_count=len(statuses.get(metric_id,[]))-len(values),mean=statistics.fmean(values),median=statistics.median(values),p95=p95,details_json={})
        db.add(record);summary[metric_id]={"mean":record.mean,"median":record.median,"p95":record.p95,"sample_count":record.sample_count}
    for metric_id, metric_statuses in statuses.items():
        if metric_id not in summary:
            summary[metric_id]={"status":metric_statuses[0].value,"sample_count":0}
    run.aggregate_metrics=summary


def execute_evaluation_job(job_id:UUID,worker_key:str,*,session_factory:sessionmaker[Session],storage:LocalArtifactStorage|None=None)->JobStatus:
    storage=storage or LocalArtifactStorage()
    with session_factory() as db:
        job=db.get(EvaluationJob,job_id)
        if job is None: raise ValueError(f"Job {job_id} does not exist.")
        run=db.get(EvaluationRun,job.run_id)
        if run is None: raise ValueError("Run does not exist.")
        if job.status==JobStatus.SUCCEEDED:return job.status
        if job.cancel_requested or run.cancellation_requested:
            job.status=JobStatus.CANCELLED;transition_run(run,RunStatus.CANCELLED);db.commit();return job.status
        worker=_worker(db,worker_key,run.execution_profile_id);job.worker_id=worker.id;job.status=JobStatus.RUNNING;job.claimed_at=job.claimed_at or datetime.now(UTC);job.started_at=datetime.now(UTC)
        transition_run(run,RunStatus.PREPARING);emit_event(db,run.id,"worker.claimed","Worker claimed evaluation job.",job_id=job.id,stage="PREPARING",payload={"worker_id":worker_key});transition_run(run,RunStatus.RUNNING);db.commit()
        try:
            items=list(db.scalars(select(DatasetItem).where(DatasetItem.dataset_version_id==run.dataset_version_id).order_by(DatasetItem.item_key)))
            context=EvaluationContext(profile_id=run.execution_profile_id,storage_root=str(storage.root))
            for position,item in enumerate(items,1):
                db.refresh(job);db.refresh(run)
                if job.cancel_requested or run.cancellation_requested:
                    job.status=JobStatus.CANCELLED;transition_run(run,RunStatus.CANCELLED);emit_event(db,run.id,"run.cancelled","Run cancelled at sample checkpoint.",job_id=job.id,stage="RUNNING");db.commit();return job.status
                case=db.scalar(select(EvaluationCase).where(EvaluationCase.run_id==run.id,EvaluationCase.dataset_item_id==item.id))
                if case is None:
                    case=EvaluationCase(run_id=run.id,dataset_item_id=item.id,sample_key=item.item_key,language=item.language,expected_text=item.expected_text,status=EvaluationCaseStatus.RUNNING)
                    db.add(case);db.flush()
                elif case.status==EvaluationCaseStatus.COMPLETED:
                    continue
                started=time.perf_counter(); evaluation_item=EvaluationItem(item.item_key,item.expected_text,item.language,item.generated_audio_ref,item.reference_audio_ref,dict(item.metadata_json))
                values:dict[str,float|None]={}; failed=False
                for metric_id in run.selected_metrics:
                    plugin=registry.get(metric_id)
                    if plugin is None:
                        result_rows=[]
                        from app.metrics.base import MetricResult
                        result_rows=[MetricResult(metric_id,"0",MetricStatus.UNAVAILABLE,None,None,warnings=["Metric plugin is not registered."])]
                    else:
                        available, reason=plugin.is_available(context)
                        if not available:
                            from app.metrics.base import MetricResult
                            result_rows=[MetricResult(metric_id,plugin.version,MetricStatus.UNAVAILABLE,None,None,warnings=[reason or "Unavailable."])]
                        else:
                            metric_start=time.perf_counter()
                            try: result_rows=plugin.evaluate(evaluation_item,context)
                            except Exception as exc:
                                from app.metrics.base import MetricResult
                                result_rows=[MetricResult(metric_id,plugin.version,MetricStatus.FAILED,None,None,error_message=str(exc))]
                            if metric_duration_seconds: metric_duration_seconds.inc(time.perf_counter()-metric_start)
                    for result in result_rows:
                        row=SampleMetricResult(evaluation_case_id=case.id,metric_id=result.metric_id,metric_version=result.metric_version,status=_STATUS_MAP[result.status],value=result.value,unit=result.unit,confidence=result.confidence,warnings=result.warnings,parameters_json={},metadata_json=result.metadata,execution_duration_ms=int((time.perf_counter()-started)*1000),error_message=result.error_message)
                        db.add(row);values[result.metric_id]=result.value
                        if result.status==MetricStatus.FAILED: failed=True
                        if result.metric_id=="audio_validation" and result.status==MetricStatus.FAILED and audio_validation_failures_total: audio_validation_failures_total.inc()
                case.transcript=str(item.metadata_json.get("manual_transcript") or item.metadata_json.get("mock_transcript") or item.expected_text)
                case.metric_summary_json=values;case.status=EvaluationCaseStatus.PARTIAL if failed else EvaluationCaseStatus.COMPLETED;run.processed_items=position;worker.last_heartbeat_at=datetime.now(UTC)
                emit_event(db,run.id,"sample.completed",f"Processed {item.item_key}.",job_id=job.id,stage="RUNNING",payload={"sample_id":item.item_key,"processed":position,"total":len(items),"status":case.status.value})
                db.commit()
            transition_run(run,RunStatus.AGGREGATING);emit_event(db,run.id,"run.aggregating","Aggregating sample metrics.",job_id=job.id,stage="AGGREGATING");_aggregate(db,run);transition_run(run,RunStatus.COMPARING);transition_run(run,RunStatus.REPORTING)
            manifest=frozen_manifest(run);run.immutable_manifest=manifest
            stored=storage.write_text(f"runs/{run.id}/manifest.json",__import__('json').dumps(manifest,ensure_ascii=False,indent=2))
            db.add(Artifact(run_id=run.id,kind=ArtifactKind.MANIFEST,storage_key=stored.storage_key,content_hash=stored.content_hash,content_type=stored.content_type,size_bytes=stored.size_bytes,origin="runtime"))
            partial=bool(db.scalar(select(EvaluationCase).where(EvaluationCase.run_id==run.id,EvaluationCase.status==EvaluationCaseStatus.PARTIAL)))
            transition_run(run,RunStatus.PARTIAL if partial else RunStatus.COMPLETED);run.completed_at=datetime.now(UTC);job.status=JobStatus.SUCCEEDED;job.finished_at=datetime.now(UTC);worker.status=WorkerStatus.ONLINE;worker.last_heartbeat_at=datetime.now(UTC)
            # Policies are applied only after terminal sample evidence and manifest artifacts exist.
            from app.services.evidence import evaluate_active_policies
            policy_results=evaluate_active_policies(db,run)
            emit_event(db,run.id,"run.completed","Evaluation execution completed.",job_id=job.id,stage=run.status.value,payload={"processed":run.processed_items,"total":run.total_items,"manifest_hash":stored.content_hash,"policy_result_count":len(policy_results)})
            db.commit();return job.status
        except Exception as exc:
            job.retry_count+=1;job.error_message=str(exc);job.status=JobStatus.RETRYING if job.retry_count<3 else JobStatus.FAILED
            run.failure_reason=str(exc);worker.status=WorkerStatus.ONLINE;worker.last_heartbeat_at=datetime.now(UTC)
            if job.status==JobStatus.FAILED:
                transition_run(run,RunStatus.FAILED)
                if runs_failed_total:runs_failed_total.inc()
            emit_event(db,run.id,"job.retry_scheduled" if job.status==JobStatus.RETRYING else "run.failed",str(exc),job_id=job.id,stage=run.current_stage,level="error")
            db.commit();return job.status
