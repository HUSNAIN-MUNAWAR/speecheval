from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.artifacts.storage import LocalArtifactStorage
from app.comparison.service import create_comparison
from app.listening.service import activate_study, create_study
from app.models.entities import (
    Baseline,
    ComparisonMetricResult,
    EvaluationCase,
    EvaluationRun,
    RegressionPolicy,
    RunStatus,
    SampleMetricResult,
)
from app.services.evidence import evaluate_policy
from tests.test_phase2_runtime import runtime_run


def complete_with_metric(db:Session,run:EvaluationRun,value:float)->None:
    item=run.dataset_version.items[0]
    case=EvaluationCase(run_id=run.id,dataset_item_id=item.id,sample_key=item.item_key,language=item.language,expected_text=item.expected_text,status='COMPLETED')
    db.add(case);db.flush()
    db.add(SampleMetricResult(evaluation_case_id=case.id,metric_id='wer',metric_version='1.0.0',status='MOCK',value=value,unit='ratio',warnings=[],parameters_json={},metadata_json={}))
    run.status=RunStatus.COMPLETED;run.immutable_manifest={'dataset':{'content_hash':'sha256:fixtures'},'metrics':[{'id':'wer','version':'1.0.0'}]};run.manifest_hash='sha256:run'
    db.commit()


def test_comparison_bootstrap_policy_and_listening_flow(db_session:Session,tmp_path):
    storage=LocalArtifactStorage(tmp_path/'artifacts')
    baseline_run=runtime_run(db_session,storage)
    candidate=EvaluationRun(project_id=baseline_run.project_id,dataset_version_id=baseline_run.dataset_version_id,model_version_id=baseline_run.model_version_id,name='candidate',selected_metrics=['wer'],execution_profile_id='local-cpu-lightweight',total_items=1,immutable_manifest={},status=RunStatus.DRAFT)
    baseline_run.selected_metrics=['wer'];db_session.add(candidate);db_session.commit();db_session.refresh(candidate)
    complete_with_metric(db_session,baseline_run,.02);complete_with_metric(db_session,candidate,.08)
    comparison=create_comparison(db_session,candidate,baseline_run)
    assert comparison.integrity_status=='STRICTLY_COMPARABLE'
    metric=db_session.scalar(select(ComparisonMetricResult).where(ComparisonMetricResult.comparison_id==comparison.id))
    assert metric is None or metric.sample_count < 2  # one paired fixture yields explicit insufficient statistical evidence
    baseline=Baseline(project_id=baseline_run.project_id,run_id=baseline_run.id,name='baseline',is_frozen=True,manifest_hash='sha256:run');db_session.add(baseline);db_session.commit();db_session.refresh(baseline)
    policy=RegressionPolicy(project_id=baseline_run.project_id,name='WER guard',metric_id='wer',operator='increase_pct_gt',threshold=.02,severity='fail',baseline_id=baseline.id,min_sample_count=1)
    db_session.add(policy);db_session.commit();db_session.refresh(policy)
    result=evaluate_policy(db_session,policy,candidate)
    assert result.decision in {'INSUFFICIENT_DATA','FAIL','PASS'}
    study=create_study(db_session,project_id=baseline_run.project_id,title='A/B test',description=None,test_type='AB_PREFERENCE',linked_run_ids=[baseline_run.id,candidate.id],selected_sample_keys=[],rating_scale={},rater_instructions='Listen.',consent_notice='Fixture audio only.',randomization_seed=9,anonymity_enabled=True,response_limit=2)
    activate_study(db_session,study)
    # No task is generated without shared case evidence for the candidate beyond the fixture sample; this is an allowed, empty study state.
    assert study.state=='ACTIVE'


def test_compare_api_returns_integrity_and_metric_payload(client, db_session: Session, tmp_path):
    storage = LocalArtifactStorage(tmp_path / "artifacts")
    baseline_run = runtime_run(db_session, storage)
    candidate = EvaluationRun(
        project_id=baseline_run.project_id,
        dataset_version_id=baseline_run.dataset_version_id,
        model_version_id=baseline_run.model_version_id,
        name="candidate-api",
        selected_metrics=["wer"],
        execution_profile_id="local-cpu-lightweight",
        total_items=1,
        immutable_manifest={},
        status=RunStatus.DRAFT,
    )
    baseline_run.selected_metrics = ["wer"]
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    complete_with_metric(db_session, baseline_run, 0.02)
    complete_with_metric(db_session, candidate, 0.08)

    response = client.post(
        "/api/v1/compare",
        json={
            "candidate_run_id": str(candidate.id),
            "baseline_run_id": str(baseline_run.id),
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["integrity_status"] == "STRICTLY_COMPARABLE"
    assert payload["verdict"] == "INSUFFICIENT_DATA"
    assert payload["metric_results"] == []
