# Creating evaluations

In Phase 1, creating a run validates provenance and freezes a reproducibility manifest. Evaluation work is not enqueued yet.

## Required records

1. A project.
2. A dataset version owned by the project.
3. A model version owned by the project.
4. A selected metric list and optional baseline reference.

## API request

```bash
curl -X POST http://localhost:8000/api/v1/evaluation-runs \
  -H 'content-type: application/json' \
  --data '{
    "project_id": "<project-uuid>",
    "dataset_version_id": "<dataset-version-uuid>",
    "model_version_id": "<model-version-uuid>",
    "name": "release-0.1-candidate",
    "metric_ids": ["audio_validation", "duration"],
    "metadata": {"trigger": "manual"}
  }'
```

The API rejects version IDs from a different project. This prevents baseline comparisons and reports from silently mixing provenance.

## Immutable manifest

Each run response exposes an `immutable_manifest` containing the dataset version, model version, selected metrics, and metadata. Phase 2 will add artifact hashes, dependency versions, worker profile, and code revision to the same record.
