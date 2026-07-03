from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.models.entities import EvaluationRun, RunStatus


class IntegrityStatus(StrEnum):
    STRICTLY_COMPARABLE = "STRICTLY_COMPARABLE"
    COMPARABLE_WITH_WARNINGS = "COMPARABLE_WITH_WARNINGS"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True, slots=True)
class IntegrityAssessment:
    status: IntegrityStatus
    reasons: list[str]


def assess_integrity(candidate: EvaluationRun, baseline: EvaluationRun) -> IntegrityAssessment:
    reasons: list[str] = []
    if candidate.status not in {RunStatus.COMPLETED, RunStatus.PARTIAL} or baseline.status not in {RunStatus.COMPLETED, RunStatus.PARTIAL}:
        return IntegrityAssessment(IntegrityStatus.NOT_COMPARABLE, ["Both runs must be completed or partial terminal runs."])
    if candidate.project_id != baseline.project_id:
        return IntegrityAssessment(IntegrityStatus.NOT_COMPARABLE, ["Runs belong to different projects."])
    if candidate.dataset_version_id != baseline.dataset_version_id:
        return IntegrityAssessment(IntegrityStatus.NOT_COMPARABLE, ["Dataset versions differ."])
    candidate_metrics = set(candidate.selected_metrics)
    baseline_metrics = set(baseline.selected_metrics)
    if not candidate_metrics.intersection(baseline_metrics):
        return IntegrityAssessment(IntegrityStatus.NOT_COMPARABLE, ["Runs share no selected metrics."])
    candidate_manifest=candidate.immutable_manifest or {}; baseline_manifest=baseline.immutable_manifest or {}
    if candidate_manifest.get("dataset",{}).get("content_hash") and baseline_manifest.get("dataset",{}).get("content_hash") and candidate_manifest["dataset"]["content_hash"] != baseline_manifest["dataset"]["content_hash"]:
        return IntegrityAssessment(IntegrityStatus.NOT_COMPARABLE,["Dataset content hashes differ."])
    if candidate.execution_profile_id != baseline.execution_profile_id:
        reasons.append("Execution profiles differ; timing metrics may not be directly comparable.")
    if candidate_manifest.get("metrics") != baseline_manifest.get("metrics"):
        reasons.append("Metric configuration or normalization settings differ.")
    return IntegrityAssessment(IntegrityStatus.COMPARABLE_WITH_WARNINGS if reasons else IntegrityStatus.STRICTLY_COMPARABLE,reasons or ["Same dataset version, overlapping metrics, and compatible profile."])
