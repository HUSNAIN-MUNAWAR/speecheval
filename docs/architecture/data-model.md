# Data Model

The foundation persists `Workspace`, `Project`, `Dataset`, `DatasetVersion`, `DatasetItem`, `TTSModel`, `ModelVersion`, and `EvaluationRun`. A run references immutable version records rather than mutable “latest” aliases.

Phase 2–4 introduce metric results, aggregates, artifacts, baselines, policies, regression results, worker executions, and audit events.
