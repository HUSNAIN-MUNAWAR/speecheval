# Architecture Overview

SpeechEval is a modular monolith. One FastAPI service owns HTTP contracts, application services, persistence, artifact references, metric registration, and orchestration boundaries. It avoids premature microservices while retaining clean seams for workers, storage adapters, and metric plugins.

## Phase 1 decisions

- **SQLite first:** a laptop can run the platform without a database service. PostgreSQL is supported through the database URL.
- **Typed contracts:** API requests and responses are Pydantic models, not unstructured dictionaries.
- **Immutable run metadata:** a draft run freezes dataset/model/metric provenance before a worker is introduced.
- **No invented scores:** the worker endpoint says it is not configured rather than pretending to execute metrics.
