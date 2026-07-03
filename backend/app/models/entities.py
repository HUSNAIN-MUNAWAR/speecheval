from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, UUIDTimestampMixin


class RunStatus(StrEnum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    AGGREGATING = "AGGREGATING"
    COMPARING = "COMPARING"
    REPORTING = "REPORTING"
    FINALIZING = "FINALIZING"  # backward-compatible Phase 1 state
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkerStatus(StrEnum):
    ONLINE = "ONLINE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"


class EvaluationCaseStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class MetricResultStatus(StrEnum):
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    MOCK = "MOCK"
    ESTIMATED = "ESTIMATED"


class ArtifactKind(StrEnum):
    MANIFEST = "MANIFEST"
    AUDIO = "AUDIO"
    WAVEFORM = "WAVEFORM"
    METRIC_DETAIL = "METRIC_DETAIL"
    LOG = "LOG"
    REPORT = "REPORT"
    EXPORT = "EXPORT"


class Workspace(UUIDTimestampMixin, Base):
    __tablename__ = "workspaces"
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    projects: Mapped[list[Project]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class Project(UUIDTimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_workspace_created", "workspace_id", "created_at"),)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), default=list, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    workspace: Mapped[Workspace] = relationship(back_populates="projects")
    datasets: Mapped[list[Dataset]] = relationship(back_populates="project", cascade="all, delete-orphan")
    models: Mapped[list[TTSModel]] = relationship(back_populates="project", cascade="all, delete-orphan")
    runs: Mapped[list[EvaluationRun]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Dataset(UUIDTimestampMixin, Base):
    __tablename__ = "datasets"
    __table_args__ = (Index("ix_datasets_project_created", "project_id", "created_at"),)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(256))
    content_hash: Mapped[str | None] = mapped_column(String(128))
    language_coverage: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), default=list, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    project: Mapped[Project] = relationship(back_populates="datasets")
    versions: Mapped[list[DatasetVersion]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(UUIDTimestampMixin, Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (Index("ix_dataset_versions_dataset_version", "dataset_id", "version", unique=True),)
    dataset_id: Mapped[UUID] = mapped_column(ForeignKey("datasets.id"), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_format: Mapped[str] = mapped_column(String(16), default="yaml", nullable=False)
    manifest_hash: Mapped[str | None] = mapped_column(String(128))
    manifest_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dataset: Mapped[Dataset] = relationship(back_populates="versions")
    items: Mapped[list[DatasetItem]] = relationship(back_populates="dataset_version", cascade="all, delete-orphan")
    runs: Mapped[list[EvaluationRun]] = relationship(back_populates="dataset_version")


class DatasetItem(UUIDTimestampMixin, Base):
    __tablename__ = "dataset_items"
    __table_args__ = (
        Index("ix_dataset_items_version_item", "dataset_version_id", "item_key", unique=True),
        Index("ix_dataset_items_language", "language"),
    )
    dataset_version_id: Mapped[UUID] = mapped_column(ForeignKey("dataset_versions.id"), index=True, nullable=False)
    item_key: Mapped[str] = mapped_column(String(160), nullable=False)
    expected_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_expected_text: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    generated_audio_ref: Mapped[str | None] = mapped_column(String(512))
    reference_audio_ref: Mapped[str | None] = mapped_column(String(512))
    tags: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), default=list, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    dataset_version: Mapped[DatasetVersion] = relationship(back_populates="items")


class TTSModel(UUIDTimestampMixin, Base):
    __tablename__ = "tts_models"
    __table_args__ = (Index("ix_tts_models_project_created", "project_id", "created_at"),)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(160))
    model_family: Mapped[str | None] = mapped_column(String(160))
    model_card_url: Mapped[str | None] = mapped_column(String(512))
    license: Mapped[str | None] = mapped_column(String(160))
    supported_languages: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), default=list, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    project: Mapped[Project] = relationship(back_populates="models")
    versions: Mapped[list[ModelVersion]] = relationship(back_populates="model", cascade="all, delete-orphan")


class ModelVersion(UUIDTimestampMixin, Base):
    __tablename__ = "model_versions"
    __table_args__ = (Index("ix_model_versions_model_version", "model_id", "version", unique=True),)
    model_id: Mapped[UUID] = mapped_column(ForeignKey("tts_models.id"), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    git_sha: Mapped[str | None] = mapped_column(String(64))
    docker_image_tag: Mapped[str | None] = mapped_column(String(256))
    configuration_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    model: Mapped[TTSModel] = relationship(back_populates="versions")
    runs: Mapped[list[EvaluationRun]] = relationship(back_populates="model_version")


class EvaluationRun(UUIDTimestampMixin, Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("ix_runs_project_status", "project_id", "status"),
        Index("ix_runs_created", "created_at"),
        Index("ix_runs_decision", "regression_decision"),
    )
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    dataset_version_id: Mapped[UUID] = mapped_column(ForeignKey("dataset_versions.id"), index=True, nullable=False)
    model_version_id: Mapped[UUID] = mapped_column(ForeignKey("model_versions.id"), index=True, nullable=False)
    rerun_of_id: Mapped[UUID | None] = mapped_column(ForeignKey("evaluation_runs.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.DRAFT, nullable=False)
    regression_decision: Mapped[str | None] = mapped_column(String(24), index=True)
    selected_metrics: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), default=list, nullable=False)
    aggregate_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    immutable_manifest: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    manifest_hash: Mapped[str | None] = mapped_column(String(128))
    execution_environment: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    execution_profile_id: Mapped[str] = mapped_column(String(80), default="local-cpu-lightweight", nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancellation_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(64))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    project: Mapped[Project] = relationship(back_populates="runs")
    dataset_version: Mapped[DatasetVersion] = relationship(back_populates="runs")
    model_version: Mapped[ModelVersion] = relationship(back_populates="runs")
    jobs: Mapped[list[EvaluationJob]] = relationship(back_populates="run", cascade="all, delete-orphan")
    events: Mapped[list[EvaluationEvent]] = relationship(back_populates="run", cascade="all, delete-orphan")
    cases: Mapped[list[EvaluationCase]] = relationship(back_populates="run", cascade="all, delete-orphan")
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="run", cascade="all, delete-orphan")


class Worker(UUIDTimestampMixin, Base):
    __tablename__ = "workers"
    __table_args__ = (Index("ix_workers_status_heartbeat", "status", "last_heartbeat_at"),)
    worker_key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[WorkerStatus] = mapped_column(Enum(WorkerStatus), default=WorkerStatus.ONLINE, nullable=False)
    capabilities_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    environment_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class EvaluationJob(UUIDTimestampMixin, Base):
    __tablename__ = "evaluation_jobs"
    __table_args__ = (
        Index("ix_jobs_status_created", "status", "created_at"),
        Index("ix_jobs_run_attempt", "run_id", "attempt", unique=True),
    )
    run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), index=True, nullable=False)
    worker_id: Mapped[UUID | None] = mapped_column(ForeignKey("workers.id"))
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    run: Mapped[EvaluationRun] = relationship(back_populates="jobs")


class EvaluationEvent(UUIDTimestampMixin, Base):
    __tablename__ = "evaluation_events"
    __table_args__ = (Index("ix_events_run_sequence", "run_id", "sequence", unique=True),)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), index=True, nullable=False)
    job_id: Mapped[UUID | None] = mapped_column(ForeignKey("evaluation_jobs.id"))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(64))
    level: Mapped[str] = mapped_column(String(16), default="info", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    run: Mapped[EvaluationRun] = relationship(back_populates="events")


class EvaluationCase(UUIDTimestampMixin, Base):
    __tablename__ = "evaluation_cases"
    __table_args__ = (
        Index("ix_cases_run_item", "run_id", "dataset_item_id", unique=True),
        Index("ix_cases_run_status", "run_id", "status"),
        Index("ix_cases_language", "language"),
    )
    run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), index=True, nullable=False)
    dataset_item_id: Mapped[UUID] = mapped_column(ForeignKey("dataset_items.id"), index=True, nullable=False)
    sample_key: Mapped[str] = mapped_column(String(160), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    expected_text: Mapped[str] = mapped_column(Text, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EvaluationCaseStatus] = mapped_column(Enum(EvaluationCaseStatus), default=EvaluationCaseStatus.PENDING, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
    metric_summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    run: Mapped[EvaluationRun] = relationship(back_populates="cases")
    results: Mapped[list[SampleMetricResult]] = relationship(back_populates="evaluation_case", cascade="all, delete-orphan")


class SampleMetricResult(UUIDTimestampMixin, Base):
    __tablename__ = "sample_metric_results"
    __table_args__ = (
        Index("ix_metric_results_case_metric", "evaluation_case_id", "metric_id"),
        Index("ix_metric_results_metric_status", "metric_id", "status"),
    )
    evaluation_case_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_cases.id"), index=True, nullable=False)
    metric_id: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[MetricResultStatus] = mapped_column(Enum(MetricResultStatus), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    execution_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    evaluation_case: Mapped[EvaluationCase] = relationship(back_populates="results")


class RunAggregateMetric(UUIDTimestampMixin, Base):
    __tablename__ = "run_aggregate_metrics"
    __table_args__ = (Index("ix_run_aggregate_metric", "run_id", "metric_id", unique=True),)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), index=True, nullable=False)
    metric_id: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[MetricResultStatus] = mapped_column(Enum(MetricResultStatus), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excluded_sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mean: Mapped[float | None] = mapped_column(Float)
    median: Mapped[float | None] = mapped_column(Float)
    p95: Mapped[float | None] = mapped_column(Float)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Artifact(UUIDTimestampMixin, Base):
    __tablename__ = "artifacts"
    __table_args__ = (Index("ix_artifact_hash", "content_hash"), Index("ix_artifact_run_kind", "run_id", "kind"))
    run_id: Mapped[UUID | None] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    evaluation_case_id: Mapped[UUID | None] = mapped_column(ForeignKey("evaluation_cases.id"), index=True)
    kind: Mapped[ArtifactKind] = mapped_column(Enum(ArtifactKind), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(768), unique=True, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    origin: Mapped[str] = mapped_column(String(80), default="generated", nullable=False)
    retention_policy: Mapped[str] = mapped_column(String(80), default="workspace-default", nullable=False)
    run: Mapped[EvaluationRun | None] = relationship(back_populates="artifacts")


class Baseline(UUIDTimestampMixin, Base):
    __tablename__ = "baselines"
    __table_args__ = (Index("ix_baselines_project_active", "project_id", "is_frozen"),)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manifest_hash: Mapped[str | None] = mapped_column(String(128))


class RegressionPolicy(UUIDTimestampMixin, Base):
    __tablename__ = "regression_policies"
    __table_args__ = (Index("ix_policies_project_enabled", "project_id", "enabled"),)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    metric_id: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_version: Mapped[str | None] = mapped_column(String(32))
    operator: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    baseline_id: Mapped[UUID | None] = mapped_column(ForeignKey("baselines.id"))
    language_filter: Mapped[str | None] = mapped_column(String(16))
    tag_filter: Mapped[str | None] = mapped_column(String(100))
    model_filter: Mapped[str | None] = mapped_column(String(160))
    execution_profile_filter: Mapped[str | None] = mapped_column(String(80))
    min_sample_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confidence_required: Mapped[float | None] = mapped_column(Float)
    remediation_guidance: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    author: Mapped[str] = mapped_column(String(160), default="local-admin", nullable=False)


class RegressionResult(UUIDTimestampMixin, Base):
    __tablename__ = "regression_results"
    __table_args__ = (Index("ix_regression_results_run_decision", "run_id", "decision"),)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), index=True, nullable=False)
    policy_id: Mapped[UUID] = mapped_column(ForeignKey("regression_policies.id"), index=True, nullable=False)
    integrity_status: Mapped[str] = mapped_column(String(40), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    observed_value: Mapped[float | None] = mapped_column(Float)
    baseline_value: Mapped[float | None] = mapped_column(Float)
    absolute_delta: Mapped[float | None] = mapped_column(Float)
    relative_delta: Mapped[float | None] = mapped_column(Float)
    confidence_interval_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excluded_sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    affected_samples_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class Comparison(UUIDTimestampMixin, Base):
    __tablename__ = "comparisons"
    __table_args__ = (Index("ix_comparisons_runs", "candidate_run_id", "baseline_run_id", unique=True),)
    candidate_run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), nullable=False)
    baseline_run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), nullable=False)
    integrity_status: Mapped[str] = mapped_column(String(40), nullable=False)
    integrity_reasons: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    verdict: Mapped[str] = mapped_column(String(48), nullable=False)
    methodology_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ComparisonMetricResult(UUIDTimestampMixin, Base):
    __tablename__ = "comparison_metric_results"
    __table_args__ = (Index("ix_compare_metric", "comparison_id", "metric_id", unique=True),)
    comparison_id: Mapped[UUID] = mapped_column(ForeignKey("comparisons.id"), index=True, nullable=False)
    metric_id: Mapped[str] = mapped_column(String(100), nullable=False)
    baseline_value: Mapped[float | None] = mapped_column(Float)
    candidate_value: Mapped[float | None] = mapped_column(Float)
    absolute_delta: Mapped[float | None] = mapped_column(Float)
    relative_delta: Mapped[float | None] = mapped_column(Float)
    confidence_interval_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verdict: Mapped[str] = mapped_column(String(48), nullable=False)


class BenchmarkCard(UUIDTimestampMixin, Base):
    __tablename__ = "benchmark_cards"
    __table_args__ = (Index("ix_benchmark_cards_run", "run_id", unique=True),)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_runs.id"), nullable=False)
    integrity_status: Mapped[str] = mapped_column(String(40), nullable=False)
    manifest_hash: Mapped[str | None] = mapped_column(String(128))
    content_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    html: Mapped[str] = mapped_column(Text, nullable=False)


class ListeningStudy(UUIDTimestampMixin, Base):
    __tablename__ = "listening_studies"
    __table_args__ = (Index("ix_listening_studies_project_state", "project_id", "state"),)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(24), default="DRAFT", nullable=False)
    test_type: Mapped[str] = mapped_column(String(24), nullable=False)
    linked_run_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    selected_sample_keys: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    rating_scale: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    rater_instructions: Mapped[str | None] = mapped_column(Text)
    consent_notice: Mapped[str | None] = mapped_column(Text)
    randomization_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    anonymity_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    response_limit: Mapped[int | None] = mapped_column(Integer)
    data_retention: Mapped[str] = mapped_column(String(80), default="workspace-default", nullable=False)
    created_by: Mapped[str] = mapped_column(String(160), default="local-admin", nullable=False)


class ListeningTask(UUIDTimestampMixin, Base):
    __tablename__ = "listening_tasks"
    __table_args__ = (Index("ix_listening_tasks_study_order", "study_id", "task_order", unique=True),)
    study_id: Mapped[UUID] = mapped_column(ForeignKey("listening_studies.id"), index=True, nullable=False)
    task_order: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_key: Mapped[str] = mapped_column(String(160), nullable=False)
    expected_text: Mapped[str | None] = mapped_column(Text)
    option_a_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    option_b_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    option_x_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    randomization_token: Mapped[str] = mapped_column(String(128), nullable=False)


class ListeningResponse(UUIDTimestampMixin, Base):
    __tablename__ = "listening_responses"
    __table_args__ = (
        Index("ix_listening_responses_study", "study_id"),
        Index("ix_listening_response_unique", "study_id", "task_id", "rater_key", unique=True),
    )
    study_id: Mapped[UUID] = mapped_column(ForeignKey("listening_studies.id"), index=True, nullable=False)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("listening_tasks.id"), index=True, nullable=False)
    rater_key: Mapped[str] = mapped_column(String(160), nullable=False)
    preference: Mapped[str | None] = mapped_column(String(24))
    rating: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
