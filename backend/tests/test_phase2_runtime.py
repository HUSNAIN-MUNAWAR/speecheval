from __future__ import annotations

import math
import wave
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.artifacts.storage import ArtifactPathError, LocalArtifactStorage
from app.comparison.integrity import IntegrityStatus, assess_integrity
from app.execution.runtime import create_evaluation_job
from app.models.entities import (
    Artifact,
    Dataset,
    DatasetItem,
    DatasetVersion,
    EvaluationCase,
    EvaluationRun,
    JobStatus,
    ModelVersion,
    Project,
    RunStatus,
    SampleMetricResult,
    TTSModel,
    Workspace,
)
from app.workers.executor import execute_evaluation_job


def write_wav(storage: LocalArtifactStorage, key: str) -> str:
    path=storage.resolve(key);path.parent.mkdir(parents=True,exist_ok=True)
    rate=16000;samples=[0.0]*800+[.3*math.sin(2*math.pi*180*i/rate) for i in range(7200)]+[0.0]*800
    samples[1000:1010]=[1.0]*10
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate)
        out.writeframes(b''.join(int(sample*32767).to_bytes(2,'little',signed=True) for sample in samples))
    return key


def runtime_run(db:Session,storage:LocalArtifactStorage)->EvaluationRun:
    workspace=Workspace(name='Runtime Lab',slug='runtime-lab')
    project=Project(workspace=workspace,name='CPU Runtime',slug='cpu-runtime')
    dataset=Dataset(project=project,name='Fixtures',language_coverage=['en'])
    version=DatasetVersion(dataset=dataset,version='1.0',manifest_hash='sha256:fixtures',manifest_json={},item_count=1)
    item=DatasetItem(dataset_version=version,item_key='sample_001',expected_text='Speech evaluation should be reproducible.',normalized_expected_text='Speech evaluation should be reproducible.',language='en',generated_audio_ref=write_wav(storage,'samples/sample_001.wav'),metadata_json={'mock_transcript':'Speech evaluation should be reproducible.'})
    model=TTSModel(project=project,name='Fixture TTS')
    model_version=ModelVersion(model=model,version='1.0')
    run=EvaluationRun(project=project,dataset_version=version,model_version=model_version,name='Runtime run',selected_metrics=['audio_validation','duration','silence_ratio','clipping','loudness','pitch_prosody','speech_rate','text_normalization','wer','cer','performance'],execution_profile_id='local-cpu-lightweight',total_items=1,immutable_manifest={})
    db.add_all([workspace,project,dataset,version,item,model,model_version,run]);db.commit();db.refresh(run);return run


def test_cpu_runtime_persists_signal_metrics_events_and_artifact(db_session:Session,tmp_path:Path):
    storage=LocalArtifactStorage(tmp_path/'artifacts');run=runtime_run(db_session,storage);job=create_evaluation_job(db_session,run)
    factory=sessionmaker(bind=db_session.get_bind(),autoflush=False,expire_on_commit=False)
    assert execute_evaluation_job(job.id,'test-worker',session_factory=factory,storage=storage)==JobStatus.SUCCEEDED
    db_session.expire_all();completed=db_session.get(EvaluationRun,run.id)
    assert completed and completed.status==RunStatus.COMPLETED and completed.manifest_hash
    assert db_session.scalar(select(func.count()).select_from(EvaluationCase).where(EvaluationCase.run_id==run.id))==1
    assert db_session.scalar(select(func.count()).select_from(SampleMetricResult).join(EvaluationCase).where(EvaluationCase.run_id==run.id))>=11
    loudness = db_session.scalar(
        select(SampleMetricResult)
        .join(EvaluationCase)
        .where(EvaluationCase.run_id == run.id, SampleMetricResult.metric_id == "loudness")
    )
    assert loudness is not None
    assert loudness.status.value in {"SUCCESS", "ESTIMATED"}
    assert loudness.metadata_json.get("method") in {"pyloudnorm", "rms_fallback"}
    assert db_session.scalar(select(func.count()).select_from(Artifact).where(Artifact.run_id==run.id))==1
    duplicate=execute_evaluation_job(job.id,'test-worker',session_factory=factory,storage=storage)
    assert duplicate==JobStatus.SUCCEEDED


def test_integrity_guard_rejects_dataset_mismatch(db_session:Session,tmp_path:Path):
    storage=LocalArtifactStorage(tmp_path/'artifacts')
    left=runtime_run(db_session,storage)
    left.status=RunStatus.COMPLETED
    db_session.commit()
    right=EvaluationRun(project_id=left.project_id,dataset_version_id=left.dataset_version_id,model_version_id=left.model_version_id,name='different dataset reference',selected_metrics=['duration'],execution_profile_id='local-cpu-lightweight',total_items=1,immutable_manifest={},status=RunStatus.COMPLETED)
    db_session.add(right);db_session.commit();db_session.refresh(right)
    # Same dataset, but different metric profile causes a warning rather than invalid evidence.
    assert assess_integrity(right,left).status==IntegrityStatus.STRICTLY_COMPARABLE
    right.dataset_version_id=__import__('uuid').uuid4()
    assert assess_integrity(right,left).status==IntegrityStatus.NOT_COMPARABLE


def test_artifact_storage_blocks_path_traversal(tmp_path:Path):
    storage=LocalArtifactStorage(tmp_path/'artifacts')
    try:storage.resolve('../outside.wav')
    except ArtifactPathError:pass
    else:raise AssertionError('unsafe artifact path was accepted')
