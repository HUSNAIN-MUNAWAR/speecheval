from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comparison.integrity import IntegrityStatus
from app.comparison.service import create_comparison
from app.models.entities import Baseline, EvaluationRun, RegressionPolicy, RegressionResult
from app.services.errors import DomainValidationError


def create_baseline(db:Session,project_id,run:EvaluationRun,name:str)->Baseline:
    if run.project_id != project_id: raise DomainValidationError("Baseline run must belong to the selected project.")
    if run.status.value not in {"COMPLETED","PARTIAL"}: raise DomainValidationError("Only completed or partial runs can become baselines.")
    baseline=Baseline(project_id=project_id,run_id=run.id,name=name,manifest_hash=run.manifest_hash)
    db.add(baseline);db.commit();db.refresh(baseline);return baseline


def freeze_baseline(db:Session,baseline:Baseline)->Baseline:
    baseline.is_frozen=True;db.commit();db.refresh(baseline);return baseline


def create_policy(db:Session,**kwargs)->RegressionPolicy:
    policy=RegressionPolicy(**kwargs);db.add(policy);db.commit();db.refresh(policy);return policy


def evaluate_policy(db:Session,policy:RegressionPolicy,candidate:EvaluationRun)->RegressionResult:
    if not policy.enabled:
        return RegressionResult(run_id=candidate.id,policy_id=policy.id,integrity_status="DISABLED",decision="NOT_APPLICABLE",explanation="Policy is disabled.")
    if candidate.project_id != policy.project_id:
        return RegressionResult(run_id=candidate.id,policy_id=policy.id,integrity_status="PROJECT_MISMATCH",decision="NOT_APPLICABLE",explanation="Policy project does not match run project.")
    baseline = db.get(Baseline,policy.baseline_id) if policy.baseline_id else db.scalar(select(Baseline).where(Baseline.project_id==policy.project_id).order_by(Baseline.created_at.desc()))
    if baseline is None:
        return RegressionResult(run_id=candidate.id,policy_id=policy.id,integrity_status="NO_BASELINE",decision="BLOCKED",explanation="No baseline is configured.")
    base_run=db.get(EvaluationRun,baseline.run_id)
    if base_run is None: return RegressionResult(run_id=candidate.id,policy_id=policy.id,integrity_status="NO_BASELINE_RUN",decision="BLOCKED",explanation="Baseline run no longer exists.")
    comparison=create_comparison(db,candidate,base_run,language_filter=policy.language_filter,tag_filter=policy.tag_filter)
    if comparison.integrity_status==IntegrityStatus.NOT_COMPARABLE.value:
        return RegressionResult(run_id=candidate.id,policy_id=policy.id,integrity_status=comparison.integrity_status,decision="BLOCKED",explanation="Benchmark Integrity Guard rejected this comparison.")
    metric=db.scalar(select(__import__('app.models.entities',fromlist=['ComparisonMetricResult']).ComparisonMetricResult).where(__import__('app.models.entities',fromlist=['ComparisonMetricResult']).ComparisonMetricResult.comparison_id==comparison.id,__import__('app.models.entities',fromlist=['ComparisonMetricResult']).ComparisonMetricResult.metric_id==policy.metric_id))
    if metric is None or metric.sample_count < policy.min_sample_count:
        return RegressionResult(run_id=candidate.id,policy_id=policy.id,integrity_status=comparison.integrity_status,decision="INSUFFICIENT_DATA",sample_count=metric.sample_count if metric else 0,explanation="Insufficient matched valid samples for this policy.")
    observed=metric.candidate_value;baseline_value=metric.baseline_value;delta=metric.absolute_delta;relative=metric.relative_delta
    if policy.operator=="increase_pct_gt": triggered=(relative or 0)>policy.threshold
    elif policy.operator=="decrease_pct_gt": triggered=-(relative or 0)>policy.threshold
    elif policy.operator=="absolute_gt": triggered=(observed or 0)>policy.threshold
    else: triggered=(observed or 0)<policy.threshold
    decision=policy.severity.upper() if triggered else "PASS"
    return RegressionResult(run_id=candidate.id,policy_id=policy.id,integrity_status=comparison.integrity_status,decision=decision,observed_value=observed,baseline_value=baseline_value,absolute_delta=delta,relative_delta=relative,confidence_interval_json=metric.confidence_interval_json,sample_count=metric.sample_count,excluded_sample_count=0,explanation=(f"Policy {policy.name} {'triggered' if triggered else 'passed'} using {metric.sample_count} paired samples."),affected_samples_json=[])


def evaluate_active_policies(db:Session,candidate:EvaluationRun)->list[RegressionResult]:
    results=[]
    for policy in db.scalars(select(RegressionPolicy).where(RegressionPolicy.project_id==candidate.project_id,RegressionPolicy.enabled.is_(True))):
        result=evaluate_policy(db,policy,candidate);db.add(result);results.append(result)
    if results:
        decisions={result.decision for result in results}
        candidate.regression_decision="fail" if "FAIL" in decisions else "warning" if "WARNING" in decisions else "blocked" if "BLOCKED" in decisions else "pass"
    db.commit();return results
