from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    Dataset,
    DatasetItem,
    DatasetVersion,
    EvaluationRun,
    ModelVersion,
    Project,
    RunStatus,
    TTSModel,
    Workspace,
)
from app.schemas.contracts import (
    DatasetCreate,
    DatasetVersionCreate,
    ModelCreate,
    ModelVersionCreate,
    ProjectCreate,
    ProjectUpdate,
    RunCreate,
)
from app.services.errors import DomainConflictError, DomainNotFoundError, DomainValidationError


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "untitled"


def stable_hash(value: object) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(body.encode()).hexdigest()


def page(query, db: Session, limit: int, offset: int):
    return list(db.scalars(query.limit(limit).offset(offset))), db.scalar(
        select(func.count()).select_from(query.subquery())
    ) or 0


def as_uuid(value):
    return value if isinstance(value, UUID) else UUID(str(value))


def must_get(db: Session, model, entity_id: str, label: str):
    item = db.get(model, as_uuid(entity_id))
    if item is None:
        raise DomainNotFoundError(label, entity_id)
    return item


def create_project(db: Session, payload: ProjectCreate) -> Project:
    workspace = must_get(db, Workspace, str(payload.workspace_id), "Workspace")
    obj = Project(
        workspace_id=workspace.id,
        name=payload.name,
        slug=slugify(payload.name),
        description=payload.description,
        tags=payload.tags,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_projects(db: Session, workspace_id: str | None, limit: int, offset: int):
    q = select(Project).order_by(Project.updated_at.desc())
    if workspace_id:
        q = q.where(Project.workspace_id == as_uuid(workspace_id))
    return page(q, db, limit, offset)


def update_project(db: Session, project: Project, payload: ProjectUpdate) -> Project:
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(project, key, value)
    if payload.name is not None:
        project.slug = slugify(payload.name)
    db.commit()
    db.refresh(project)
    return project


def create_dataset(db: Session, payload: DatasetCreate) -> Dataset:
    must_get(db, Project, str(payload.project_id), "Project")
    obj = Dataset(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_datasets(db: Session, project_id: str | None, limit: int, offset: int):
    q = select(Dataset).order_by(Dataset.updated_at.desc())
    if project_id:
        q = q.where(Dataset.project_id == as_uuid(project_id))
    return page(q, db, limit, offset)


def create_dataset_version(
    db: Session, dataset: Dataset, payload: DatasetVersionCreate
) -> DatasetVersion:
    duplicate = db.scalar(
        select(DatasetVersion).where(
            DatasetVersion.dataset_id == dataset.id, DatasetVersion.version == payload.version
        )
    )
    if duplicate:
        raise DomainConflictError(f"Dataset version '{payload.version}' already exists.")
    manifest = payload.manifest or {
        "version": payload.version,
        "items": [x.model_dump() for x in payload.items],
    }
    version = DatasetVersion(
        dataset_id=dataset.id,
        version=payload.version,
        manifest_format=payload.manifest_format,
        manifest_json=manifest,
        manifest_hash=stable_hash(manifest),
        item_count=len(payload.items),
    )
    db.add(version)
    db.flush()
    for item in payload.items:
        db.add(
            DatasetItem(
                dataset_version_id=version.id,
                item_key=item.id,
                expected_text=item.text,
                normalized_expected_text=item.text,
                language=item.language,
                generated_audio_ref=item.generated_audio,
                reference_audio_ref=item.reference_audio,
                tags=item.tags,
                metadata_json=item.metadata,
            )
        )
    dataset.content_hash = stable_hash({"dataset": str(dataset.id), "manifest": manifest})
    db.commit()
    db.refresh(version)
    return version


def list_dataset_items(db: Session, dataset_id: str, limit: int, offset: int):
    must_get(db, Dataset, dataset_id, "Dataset")
    q = (
        select(DatasetItem)
        .join(DatasetVersion)
        .where(DatasetVersion.dataset_id == as_uuid(dataset_id))
        .order_by(DatasetItem.item_key)
    )
    return page(q, db, limit, offset)


def validate_manifest_items(items: Iterable[dict[str, object]]) -> list[str]:
    errors, ids = [], set()
    for i, item in enumerate(items):
        item_id = str(item.get("id", ""))
        if not item_id:
            errors.append(f"items[{i}].id is required")
        elif item_id in ids:
            errors.append(f"items[{i}].id duplicates '{item_id}'")
        ids.add(item_id)
        if not str(item.get("text", "")).strip():
            errors.append(f"items[{i}].text is required")
        if not str(item.get("language", "")).strip():
            errors.append(f"items[{i}].language is required")
    return errors


def create_model(db: Session, payload: ModelCreate) -> TTSModel:
    must_get(db, Project, str(payload.project_id), "Project")
    data = payload.model_dump()
    data["model_card_url"] = str(data["model_card_url"]) if data.get("model_card_url") else None
    obj = TTSModel(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_models(db: Session, project_id: str | None, limit: int, offset: int):
    q = select(TTSModel).order_by(TTSModel.updated_at.desc())
    if project_id:
        q = q.where(TTSModel.project_id == as_uuid(project_id))
    return page(q, db, limit, offset)


def create_model_version(db: Session, model: TTSModel, payload: ModelVersionCreate) -> ModelVersion:
    duplicate = db.scalar(
        select(ModelVersion).where(
            ModelVersion.model_id == model.id, ModelVersion.version == payload.version
        )
    )
    if duplicate:
        raise DomainConflictError(f"Model version '{payload.version}' already exists.")
    obj = ModelVersion(
        model_id=model.id,
        version=payload.version,
        git_sha=payload.git_sha,
        docker_image_tag=payload.docker_image_tag,
        configuration_json=payload.configuration,
        status=payload.status,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_run(db: Session, payload: RunCreate) -> EvaluationRun:
    project = must_get(db, Project, str(payload.project_id), "Project")
    dataset_version = must_get(
        db, DatasetVersion, str(payload.dataset_version_id), "DatasetVersion"
    )
    model_version = must_get(db, ModelVersion, str(payload.model_version_id), "ModelVersion")
    if dataset_version.dataset.project_id != project.id:
        raise DomainValidationError("Dataset version does not belong to the selected project.")
    if model_version.model.project_id != project.id:
        raise DomainValidationError("Model version does not belong to the selected project.")
    manifest = {
        "schema_version": "2.0",
        "dataset_version_id": str(dataset_version.id),
        "dataset_manifest_hash": dataset_version.manifest_hash,
        "model_version_id": str(model_version.id),
        "model_version": model_version.version,
        "selected_metrics": payload.selected_metrics,
        "status": "draft",
        "execution_profile": payload.execution_profile_id,
    }
    obj = EvaluationRun(
        project_id=project.id,
        dataset_version_id=dataset_version.id,
        model_version_id=model_version.id,
        name=payload.name,
        selected_metrics=payload.selected_metrics,
        execution_environment=payload.execution_environment,
        execution_profile_id=payload.execution_profile_id,
        total_items=dataset_version.item_count,
        immutable_manifest=manifest,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_runs(
    db: Session, project_id: str | None, status: RunStatus | None, limit: int, offset: int
):
    q = select(EvaluationRun).order_by(EvaluationRun.created_at.desc())
    if project_id:
        q = q.where(EvaluationRun.project_id == as_uuid(project_id))
    if status:
        q = q.where(EvaluationRun.status == status)
    return page(q, db, limit, offset)


def cancel_run(db: Session, run: EvaluationRun) -> EvaluationRun:
    if run.status not in {
        RunStatus.DRAFT,
        RunStatus.QUEUED,
        RunStatus.PREPARING,
        RunStatus.RUNNING,
    }:
        raise DomainValidationError(f"Run in state {run.status} cannot be cancelled.")
    run.status = RunStatus.CANCELLED
    db.commit()
    db.refresh(run)
    return run
