from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    TARGET_RANGE = "TARGET_RANGE"
    INFORMATIONAL = "INFORMATIONAL"


class MetricStatus(StrEnum):
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    MOCK = "MOCK"
    ESTIMATED = "ESTIMATED"


@dataclass(frozen=True, slots=True)
class EvaluationItem:
    sample_key: str
    expected_text: str
    language: str
    audio_ref: str | None
    reference_audio_ref: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    profile_id: str
    storage_root: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetricResult:
    metric_id: str
    metric_version: str
    status: MetricStatus
    value: float | None
    unit: str | None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    confidence: float | None = None
    error_message: str | None = None


class MetricPlugin(Protocol):
    id: str
    version: str
    display_name: str
    description: str
    category: str
    direction: MetricDirection
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...]
    hardware_requirements: str
    dependency_requirements: tuple[str, ...]
    configuration_schema: dict[str, Any]
    result_schema: dict[str, Any]
    aggregation_strategy: str
    limitations: str
    citation: str | None

    def is_available(self, context: EvaluationContext) -> tuple[bool, str | None]: ...
    def evaluate(self, item: EvaluationItem, context: EvaluationContext) -> list[MetricResult]: ...
