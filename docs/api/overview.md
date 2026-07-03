# API overview

All endpoints use the `/api/v1` prefix and return JSON. FastAPI serves an interactive OpenAPI UI at `/docs`.

## Error contract

Errors include a human-readable `detail` and an `x-request-id` header. Use the request ID when sharing logs or an issue report.

## Foundation resources

| Resource | Phase 1 capability |
| --- | --- |
| Projects | create, list, read, patch |
| Datasets | create, list, read, version, inspect items |
| Models | create, list, read, version |
| Evaluation runs | create provenance manifest, list, read, cancel draft/queued record |
| System | health, readiness, version, storage/worker boundary status |

Execution, events, reports, compare, policy APIs, and artifact downloads are explicitly reserved for later phases.
