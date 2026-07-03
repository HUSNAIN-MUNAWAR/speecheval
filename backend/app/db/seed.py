from __future__ import annotations

import math
import wave
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.artifacts.storage import LocalArtifactStorage
from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.models.entities import (
    Baseline,
    BenchmarkCard,
    Dataset,
    DatasetItem,
    DatasetVersion,
    EvaluationRun,
    ListeningResponse,
    ListeningStudy,
    ListeningTask,
    ModelVersion,
    Project,
    RegressionPolicy,
    RunStatus,
    TTSModel,
    Workspace,
)


def _write_wav(storage: LocalArtifactStorage, key: str, frequency: float, *, clipped: bool = False) -> str:
    path=storage.resolve(key);path.parent.mkdir(parents=True,exist_ok=True)
    sample_rate=16000; silence=int(.08*sample_rate); voice=int(.48*sample_rate)
    samples=[0.0]*silence+[.28*math.sin(2*math.pi*frequency*(i/sample_rate)) for i in range(voice)]+[0.0]*silence
    if clipped:
        for index in range(silence+160,silence+175):samples[index]=1.0
    raw=b"".join(int(max(-1,min(1,value))*32767).to_bytes(2,"little",signed=True) for value in samples)
    with wave.open(str(path),"wb") as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(sample_rate);out.writeframes(raw)
    return key


def seed_demo_data(db: Session) -> bool:
    existing=db.scalar(select(Workspace).where(Workspace.slug=="demo-lab"))
    if existing:return False
    storage=LocalArtifactStorage()
    workspace=Workspace(name="Demo Speech Lab",slug="demo-lab",is_demo=True)
    project=Project(workspace=workspace,name="Multilingual Narration Regression",slug="multilingual-narration",description="Synthetic fixture workspace. Audio metrics are real PCM calculations; transcript-derived metrics are explicitly mock/manual.",tags=["Demo Data","Regression","Multilingual"],is_demo=True)
    audit_project=Project(workspace=workspace,name="Voice Clone QA Sandbox",slug="voice-clone-qa",description="Synthetic governance and listening-study demo.",tags=["Demo Data","Listening Lab"],is_demo=True)
    dataset=Dataset(project=project,name="Narration Fixture Set",description="Deterministic local WAV fixtures; not a public benchmark.",source="speecheval-demo",content_hash="sha256:demo-fixtures-v2",language_coverage=["en","ur","ar","es","zh"],tags=["Synthetic Fixture","Demo Data"],is_demo=True)
    extended=Dataset(project=project,name="Long-form Stress Fixture",description="Synthetic long-form benchmark metadata.",source="speecheval-demo",content_hash="sha256:stress-fixtures-v1",language_coverage=["en","ur"],tags=["Synthetic Fixture","Long-form"],is_demo=True)
    clone_dataset=Dataset(project=audit_project,name="Clone Consent Fixture",description="Synthetic reference-audio metadata with no identity claims.",source="speecheval-demo",content_hash="sha256:clone-fixtures-v1",language_coverage=["en"],tags=["Synthetic Fixture","Consent Example"],is_demo=True)
    version=DatasetVersion(dataset=dataset,version="1.0.0",manifest_format="yaml",manifest_hash="sha256:demo-manifest-v2",manifest_json={"version":"1.0","label":"Synthetic Fixture"},item_count=5)
    extended_version=DatasetVersion(dataset=extended,version="1.0.0",manifest_format="yaml",manifest_hash="sha256:stress-manifest-v1",manifest_json={"version":"1.0"},item_count=1)
    clone_version=DatasetVersion(dataset=clone_dataset,version="1.0.0",manifest_format="yaml",manifest_hash="sha256:clone-manifest-v1",manifest_json={"version":"1.0"},item_count=1)
    fixture_rows=[
        ("en_001","Speech evaluation should be reproducible and transparent.","en",180),
        ("ur_001","آواز کے معیار کی جانچ قابلِ تکرار ہونی چاہیے۔","ur",196),
        ("ar_001","يجب أن يكون تقييم الصوت قابلاً لإعادة الإنتاج.","ar",210),
        ("es_001","La evaluación de voz debe ser transparente.","es",175),
        ("zh_001","语音评估应当可复现且透明。","zh",225),
    ]
    for index,(key,text,language,frequency) in enumerate(fixture_rows):
        audio=_write_wav(storage,f"demo-fixtures/{key}.wav",frequency,clipped=key=="ur_001")
        db.add(DatasetItem(dataset_version=version,item_key=key,expected_text=text,normalized_expected_text=text,language=language,generated_audio_ref=audio,tags=["narration","Synthetic Fixture"],metadata_json={"fixture":True,"sequence":index,"mock_transcript":text}))
    db.add(DatasetItem(dataset_version=extended_version,item_key="en_long_001",expected_text="A longer synthetic narration sample used only to demonstrate duration and clipping triage.",normalized_expected_text="A longer synthetic narration sample used only to demonstrate duration and clipping triage.",language="en",generated_audio_ref=_write_wav(storage,"demo-fixtures/en_long_001.wav",145,clipped=True),tags=["long-form","Synthetic Fixture"],metadata_json={"mock_transcript":"A longer synthetic narration sample used only to demonstrate duration and clipping triage."}))
    db.add(DatasetItem(dataset_version=clone_version,item_key="clone_001",expected_text="This is a synthetic consent-aware fixture.",normalized_expected_text="This is a synthetic consent-aware fixture.",language="en",generated_audio_ref=_write_wav(storage,"demo-fixtures/clone_001.wav",165),reference_audio_ref="demo-fixtures/clone_001.wav",tags=["voice_clone","Synthetic Fixture"],metadata_json={"mock_transcript":"This is a synthetic consent-aware fixture.","consent":"fixture-only"}))
    model=TTSModel(project=project,name="FixtureVoice",provider="SpeechEval",model_family="mock-tts",supported_languages=["en","ur","ar","es","zh"],tags=["Demo Data","Mock Model"],is_demo=True)
    alt=TTSModel(project=project,name="FixtureVoice Alt",provider="SpeechEval",model_family="mock-tts",supported_languages=["en","ur"],tags=["Demo Data","Mock Model"],is_demo=True)
    clone_model=TTSModel(project=audit_project,name="CloneFixture",provider="SpeechEval",model_family="mock-tts",supported_languages=["en"],tags=["Demo Data"],is_demo=True)
    baseline_model=ModelVersion(model=model,version="0.9.0-fixture",git_sha="fixturebaseline",configuration_json={"label":"Mock Metric"})
    candidate_model=ModelVersion(model=model,version="1.0.0-fixture",git_sha="fixturecandidate",configuration_json={"label":"Mock Metric"})
    regression_model=ModelVersion(model=model,version="1.1.0-fixture",git_sha="fixtureregression",configuration_json={"label":"Mock Metric"})
    alt_model=ModelVersion(model=alt,version="0.1.0-fixture",git_sha="fixturealt",configuration_json={"label":"Mock Metric"})
    clone_model_version=ModelVersion(model=clone_model,version="0.1.0-fixture",git_sha="fixtureclone",configuration_json={"label":"Mock Metric"})
    now=datetime.now(UTC)
    selected=["audio_validation","duration","silence_ratio","clipping","loudness","pitch_prosody","speech_rate","text_normalization","wer","cer","performance"]
    runs=[]
    for days,name,status,model_version,decision,aggregate in [
        (6,"Baseline fixture run",RunStatus.COMPLETED,baseline_model,"pass",{"wer":{"median":0.04,"sample_count":5},"clipping":{"median":0.0,"sample_count":5}}),
        (5,"Candidate fixture warning",RunStatus.PARTIAL,candidate_model,"warning",{"wer":{"median":0.05,"sample_count":5},"clipping":{"median":0.0,"sample_count":5}}),
        (4,"Candidate fixture failure",RunStatus.COMPLETED,regression_model,"fail",{"wer":{"median":0.12,"sample_count":5},"clipping":{"median":0.02,"sample_count":5}}),
        (3,"Partial signal audit",RunStatus.PARTIAL,candidate_model,None,{"audio_validation":{"median":1.0,"sample_count":4}}),
        (2,"Cancelled fixture run",RunStatus.CANCELLED,candidate_model,None,{}),
        (1,"Queued demo run",RunStatus.QUEUED,candidate_model,None,{}),
        (0,"Runnable CPU fixture run",RunStatus.DRAFT,candidate_model,None,{}),
    ]:
        run=EvaluationRun(project=project,dataset_version=version,model_version=model_version,name=name,status=status,regression_decision=decision,selected_metrics=selected,aggregate_metrics=aggregate,immutable_manifest={"label":"Demo Data","metric_provenance":"Synthetic Fixture / Mock Metric"},execution_environment={"label":"Demo Data"},execution_profile_id="local-cpu-lightweight",total_items=5,processed_items=5 if status in {RunStatus.COMPLETED,RunStatus.PARTIAL} else 0,is_demo=True,created_at=now-timedelta(days=days),updated_at=now-timedelta(days=days))
        db.add(run);runs.append(run)
    db.add(EvaluationRun(project=project,dataset_version=extended_version,model_version=alt_model,name="Long-form fixture comparison",status=RunStatus.COMPLETED,regression_decision="warning",selected_metrics=selected,aggregate_metrics={"clipping":{"median":.01,"sample_count":1}},immutable_manifest={"label":"Demo Data"},execution_environment={"label":"Demo Data"},execution_profile_id="local-cpu-lightweight",total_items=1,processed_items=1,is_demo=True))
    clone_run=EvaluationRun(project=audit_project,dataset_version=clone_version,model_version=clone_model_version,name="Clone consent fixture",status=RunStatus.COMPLETED,regression_decision="pass",selected_metrics=selected,aggregate_metrics={"wer":{"median":0,"sample_count":1}},immutable_manifest={"label":"Demo Data"},execution_environment={"label":"Demo Data"},execution_profile_id="local-cpu-lightweight",total_items=1,processed_items=1,is_demo=True)
    db.add(clone_run)
    db.add_all([workspace,project,audit_project,dataset,extended,clone_dataset,version,extended_version,clone_version,model,alt,clone_model,baseline_model,candidate_model,regression_model,alt_model,clone_model_version])
    db.flush()
    baseline=Baseline(project_id=project.id,run_id=runs[0].id,name="Fixture baseline",is_frozen=True,manifest_hash="sha256:fixture-baseline")
    db.add(baseline);db.flush()
    db.add_all([
        RegressionPolicy(project_id=project.id,name="WER release guard",metric_id="wer",operator="increase_pct_gt",threshold=.03,severity="fail",baseline_id=baseline.id,min_sample_count=3,remediation_guidance="Inspect language-specific transcript alignments."),
        RegressionPolicy(project_id=project.id,name="Clipping warning",metric_id="clipping",operator="absolute_gt",threshold=.005,severity="warning",baseline_id=baseline.id,min_sample_count=3,remediation_guidance="Inspect long-form waveform regions."),
        RegressionPolicy(project_id=project.id,name="Urdu WER watch",metric_id="wer",operator="increase_pct_gt",threshold=.02,severity="warning",baseline_id=baseline.id,language_filter="ur",min_sample_count=1),
    ])
    card=BenchmarkCard(run_id=runs[0].id,integrity_status="STRICTLY_COMPARABLE",manifest_hash="sha256:fixture-baseline",content_json={"label":"Demo Data"},markdown="# Demo benchmark card\n\nSynthetic fixture only.",html="<p>Synthetic fixture only.</p>")
    db.add(card)
    study=ListeningStudy(project_id=project.id,title="Fixture A/B Listening Lab",description="Synthetic audio study. Internal exploratory feedback only.",state="ACTIVE",test_type="AB_PREFERENCE",linked_run_ids=[str(runs[0].id),str(runs[1].id)],selected_sample_keys=["en_001"],rating_scale={},rater_instructions="Listen without autoplay and choose a preference.",consent_notice="Synthetic fixture audio only.",randomization_seed=42,anonymity_enabled=True,response_limit=5)
    db.add(study);db.flush()
    task=ListeningTask(study_id=study.id,task_order=1,sample_key="en_001",expected_text=fixture_rows[0][1],option_a_json={"label":"A"},option_b_json={"label":"B"},option_x_json={},randomization_token="fixture-task-1")
    db.add(task);db.flush()
    db.add_all([ListeningResponse(study_id=study.id,task_id=task.id,rater_key="demo-rater-a",preference="A",confidence=3),ListeningResponse(study_id=study.id,task_id=task.id,rater_key="demo-rater-b",preference="NO_PREFERENCE",confidence=2)])
    db.commit();return True


def main()->None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:created=seed_demo_data(db)
    print("Seeded SpeechEval demo data." if created else "SpeechEval demo data already exists.")

if __name__=='__main__':main()
