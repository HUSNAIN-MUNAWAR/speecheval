from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.models.entities import RunStatus
from app.schemas.common import TimestampedResponse


class ProjectCreate(BaseModel):
    workspace_id: UUID
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=20)


class ProjectResponse(TimestampedResponse):
    workspace_id: UUID
    name: str
    slug: str
    description: str | None
    tags: list[str]
    is_demo: bool


class DatasetCreate(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    source: str | None = None
    language_coverage: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class DatasetResponse(TimestampedResponse):
    project_id: UUID
    name: str
    description: str | None
    source: str | None
    content_hash: str | None
    language_coverage: list[str]
    tags: list[str]
    is_demo: bool


class DatasetItemCreate(BaseModel):
    id: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=16)
    generated_audio: str | None = None
    reference_audio: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetVersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=64)
    manifest_format: str = Field(default="yaml", pattern="^(yaml|json)$")
    manifest: dict[str, Any] = Field(default_factory=dict)
    items: list[DatasetItemCreate] = Field(default_factory=list)


class DatasetVersionResponse(TimestampedResponse):
    dataset_id: UUID
    version: str
    manifest_format: str
    manifest_hash: str | None
    item_count: int
    is_active: bool
    manifest_json: dict[str, Any]


class DatasetItemResponse(TimestampedResponse):
    dataset_version_id: UUID
    item_key: str
    expected_text: str
    normalized_expected_text: str | None
    language: str
    generated_audio_ref: str | None
    reference_audio_ref: str | None
    tags: list[str]
    metadata_json: dict[str, Any]


class ModelCreate(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    provider: str | None = None
    model_family: str | None = None
    model_card_url: HttpUrl | None = None
    license: str | None = None
    supported_languages: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ModelResponse(TimestampedResponse):
    project_id: UUID
    name: str
    provider: str | None
    model_family: str | None
    model_card_url: str | None
    license: str | None
    supported_languages: list[str]
    tags: list[str]
    is_demo: bool


class ModelVersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=80)
    git_sha: str | None = None
    docker_image_tag: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"


class ModelVersionResponse(TimestampedResponse):
    model_id: UUID
    version: str
    git_sha: str | None
    docker_image_tag: str | None
    configuration_json: dict[str, Any]
    status: str


class RunCreate(BaseModel):
    project_id: UUID
    dataset_version_id: UUID
    model_version_id: UUID
    name: str = Field(min_length=2, max_length=200)
    selected_metrics: list[str] = Field(min_length=1, max_length=30)
    execution_environment: dict[str, Any] = Field(default_factory=dict)
    execution_profile_id: str = "local-cpu-lightweight"


class RunResponse(TimestampedResponse):
    project_id: UUID
    dataset_version_id: UUID
    model_version_id: UUID
    name: str
    status: RunStatus
    regression_decision: str | None
    selected_metrics: list[str]
    aggregate_metrics: dict[str, Any]
    immutable_manifest: dict[str, Any]
    execution_environment: dict[str, Any]
    execution_profile_id: str
    manifest_hash: str | None = None
    current_stage: str | None = None
    cancellation_requested: bool = False
    total_items: int
    processed_items: int
    is_demo: bool

# Phase 2 runtime contracts
class RunEnqueueResponse(BaseModel):
    run_id: UUID
    job_id: UUID
    status: RunStatus
    manifest_hash: str | None


class RunEventResponse(BaseModel):
    id: UUID
    sequence: int
    event_type: str
    stage: str | None
    level: str
    message: str
    payload_json: dict[str, Any]
    created_at: str


class ExecutionProfileResponse(BaseModel):
    id: str
    display_name: str
    capabilities: list[str]
    max_concurrency: int
    timeout_seconds: int
    min_ram_gb: int
    gpu_required: bool
    max_audio_duration_seconds: int
    max_upload_size_mb: int


class BaselineCreate(BaseModel):
    project_id: UUID
    run_id: UUID
    name: str = Field(min_length=2, max_length=160)


class BaselineResponse(TimestampedResponse):
    project_id: UUID
    run_id: UUID
    name: str
    is_frozen: bool
    manifest_hash: str | None


class RegressionPolicyCreate(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    metric_id: str
    operator: str = Field(pattern="^(increase_pct_gt|decrease_pct_gt|absolute_gt|absolute_lt)$")
    threshold: float
    severity: str = Field(pattern="^(info|warning|fail)$")
    baseline_id: UUID | None = None
    language_filter: str | None = None
    tag_filter: str | None = None
    min_sample_count: int = Field(default=1, ge=1)
    confidence_required: float | None = Field(default=None, gt=0, le=0.99)
    remediation_guidance: str | None = None


class RegressionPolicyResponse(TimestampedResponse):
    project_id: UUID
    name: str
    metric_id: str
    metric_version: str | None
    operator: str
    threshold: float
    severity: str
    baseline_id: UUID | None
    language_filter: str | None
    tag_filter: str | None
    min_sample_count: int
    confidence_required: float | None
    enabled: bool


class ComparisonCreate(BaseModel):
    candidate_run_id: UUID
    baseline_run_id: UUID
    language_filter: str | None = None
    tag_filter: str | None = None


class ListeningStudyCreate(BaseModel):
    project_id: UUID
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    test_type: str = Field(pattern="^(AB_PREFERENCE|ABX|MOS|NATURALNESS|INTELLIGIBILITY|SIMILARITY)$")
    linked_run_ids: list[UUID] = Field(min_length=1, max_length=2)
    selected_sample_keys: list[str] = Field(default_factory=list)
    rating_scale: dict[str, Any] = Field(default_factory=dict)
    rater_instructions: str | None = None
    consent_notice: str | None = None
    randomization_seed: int = 42
    anonymity_enabled: bool = True
    response_limit: int | None = Field(default=None, ge=1)


class ListeningResponseCreate(BaseModel):
    task_id: UUID
    rater_key: str = Field(min_length=1, max_length=160)
    preference: str | None = Field(default=None, pattern="^(A|B|X|NO_PREFERENCE)$")
    rating: float | None = Field(default=None, ge=1, le=5)
    confidence: int | None = Field(default=None, ge=1, le=5)
    note: str | None = Field(default=None, max_length=2000)
    duration_ms: int | None = Field(default=None, ge=0)
