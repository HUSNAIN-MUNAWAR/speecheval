from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comparison.integrity import IntegrityStatus, assess_integrity
from app.comparison.statistics import paired_bootstrap
from app.models.entities import (
    Comparison,
    ComparisonMetricResult,
    EvaluationCase,
    EvaluationRun,
    SampleMetricResult,
)


def _metric_values(db:Session,run_id,metric_id:str,language:str|None=None,tag:str|None=None)->dict[str,float]:
    query=(select(EvaluationCase.sample_key,SampleMetricResult.value)
           .join(SampleMetricResult,SampleMetricResult.evaluation_case_id==EvaluationCase.id)
           .where(EvaluationCase.run_id==run_id,SampleMetricResult.metric_id==metric_id,SampleMetricResult.value.is_not(None)))
    if language: query=query.where(EvaluationCase.language==language)
    rows=db.execute(query).all()
    return {str(key):float(value) for key,value in rows}


def create_comparison(db:Session,candidate:EvaluationRun,baseline:EvaluationRun,*,language_filter:str|None=None,tag_filter:str|None=None)->Comparison:
    assessment=assess_integrity(candidate,baseline)
    existing=db.scalar(select(Comparison).where(Comparison.candidate_run_id==candidate.id,Comparison.baseline_run_id==baseline.id))
    if existing:return existing
    comparison=Comparison(candidate_run_id=candidate.id,baseline_run_id=baseline.id,integrity_status=assessment.status.value,integrity_reasons=assessment.reasons,verdict="NOT_COMPARABLE" if assessment.status==IntegrityStatus.NOT_COMPARABLE else "INSUFFICIENT_DATA",methodology_json={"method":"paired bootstrap, 95% CI","scope":{"language":language_filter,"tag":tag_filter}})
    db.add(comparison);db.flush()
    if assessment.status==IntegrityStatus.NOT_COMPARABLE:
        db.commit();return comparison
    verdicts=[]
    for metric_id in sorted(set(candidate.selected_metrics).intersection(baseline.selected_metrics)):
        before=_metric_values(db,baseline.id,metric_id,language_filter,tag_filter);after=_metric_values(db,candidate.id,metric_id,language_filter,tag_filter);keys=sorted(set(before).intersection(after))
        if len(keys)<2:continue
        estimate=paired_bootstrap([before[key] for key in keys],[after[key] for key in keys])
        direction="lower" if metric_id in {"wer","cer","clipping","silence_ratio","performance"} else "higher"
        regression=(estimate.ci_low>0 if direction=="lower" else estimate.ci_high<0)
        improvement=(estimate.ci_high<0 if direction=="lower" else estimate.ci_low>0)
        verdict="LIKELY_REGRESSION" if regression else "LIKELY_IMPROVEMENT" if improvement else "NO_MEANINGFUL_DIFFERENCE"
        verdicts.append(verdict)
        db.add(ComparisonMetricResult(comparison_id=comparison.id,metric_id=metric_id,baseline_value=estimate.baseline_mean,candidate_value=estimate.candidate_mean,absolute_delta=estimate.absolute_delta,relative_delta=estimate.relative_delta,confidence_interval_json={"level":.95,"low":estimate.ci_low,"high":estimate.ci_high},sample_count=estimate.sample_count,verdict=verdict))
    comparison.verdict="LIKELY_REGRESSION" if "LIKELY_REGRESSION" in verdicts else "LIKELY_IMPROVEMENT" if "LIKELY_IMPROVEMENT" in verdicts else "NO_MEANINGFUL_DIFFERENCE" if verdicts else "INSUFFICIENT_DATA"
    db.commit();db.refresh(comparison);return comparison


def comparison_payload(db: Session, comparison: Comparison) -> dict[str, object]:
    metric_results = list(
        db.scalars(
            select(ComparisonMetricResult)
            .where(ComparisonMetricResult.comparison_id == comparison.id)
            .order_by(ComparisonMetricResult.metric_id)
        )
    )
    return {
        "id": str(comparison.id),
        "candidate_run_id": str(comparison.candidate_run_id),
        "baseline_run_id": str(comparison.baseline_run_id),
        "integrity_status": comparison.integrity_status,
        "integrity_reasons": comparison.integrity_reasons,
        "verdict": comparison.verdict,
        "methodology": comparison.methodology_json,
        "metric_results": [
            {
                "metric_id": result.metric_id,
                "baseline_value": result.baseline_value,
                "candidate_value": result.candidate_value,
                "absolute_delta": result.absolute_delta,
                "relative_delta": result.relative_delta,
                "confidence_interval": result.confidence_interval_json,
                "sample_count": result.sample_count,
                "verdict": result.verdict,
            }
            for result in metric_results
        ],
        "created_at": comparison.created_at.isoformat(),
    }
