# Compose infrastructure

The root `docker-compose.yml` is the supported local service topology. PostgreSQL and Redis exist to keep Phase 2 execution boundaries stable; a CPU-only SQLite local path remains the default for fast development.
