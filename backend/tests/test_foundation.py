from uuid import uuid4

from app.models.entities import Workspace


def test_health_and_readiness(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"
    ready = client.get("/api/v1/ready")
    assert ready.status_code == 200 and ready.headers["x-request-id"]


def test_project_dataset_model_run_flow(client, db_session):
    workspace = Workspace(name="Test Lab", slug=f"test-{uuid4().hex[:8]}")
    db_session.add(workspace)
    db_session.commit()
    project = client.post(
        "/api/v1/projects",
        json={"workspace_id": str(workspace.id), "name": "English benchmark", "tags": ["ci"]},
    )
    assert project.status_code == 201
    dataset = client.post(
        "/api/v1/datasets",
        json={
            "project_id": project.json()["id"],
            "name": "Fixture set",
            "language_coverage": ["en"],
        },
    )
    assert dataset.status_code == 201
    dataset_version = client.post(
        f"/api/v1/datasets/{dataset.json()['id']}/versions",
        json={
            "version": "1.0.0",
            "items": [{"id": "s1", "text": "A reproducible test.", "language": "en"}],
        },
    )
    assert dataset_version.status_code == 201 and dataset_version.json()["item_count"] == 1
    model = client.post(
        "/api/v1/models",
        json={"project_id": project.json()["id"], "name": "Local TTS", "provider": "internal"},
    )
    assert model.status_code == 201
    model_version = client.post(
        f"/api/v1/models/{model.json()['id']}/versions",
        json={"version": "0.1.0", "configuration": {"seed": 42}},
    )
    assert model_version.status_code == 201
    run = client.post(
        "/api/v1/evaluation-runs",
        json={
            "project_id": project.json()["id"],
            "dataset_version_id": dataset_version.json()["id"],
            "model_version_id": model_version.json()["id"],
            "name": "Draft evaluation",
            "selected_metrics": ["audio_validation", "duration"],
        },
    )
    assert run.status_code == 201
    assert run.json()["status"] == "DRAFT"
    assert run.json()["immutable_manifest"]["schema_version"] == "2.0"


def test_manifest_duplicate_id_error(client):
    response = client.post(
        "/api/v1/datasets/validate",
        json={
            "version": "1.0",
            "items": [
                {"id": "same", "text": "one", "language": "en"},
                {"id": "same", "text": "two", "language": "en"},
            ],
        },
    )
    assert not response.json()["valid"]
    assert "duplicates" in response.json()["errors"][0]
