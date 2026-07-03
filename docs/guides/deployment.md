# Deployment

## Development deployment

```bash
cp .env.example .env
docker compose up --build
```

Services:

- `web`: Next.js UI on port 3000
- `api`: FastAPI/OpenAPI on port 8000
- `worker`: future queue worker boundary
- `postgres`: production-oriented database
- `redis`: queue/cache boundary for Phase 2
- `minio`: optional object-store profile

## Production considerations

Use a managed PostgreSQL database, encrypted object storage, TLS termination, secret injection, upload limits, structured logs, backups, and a reverse proxy. Keep raw audio private by default, avoid serving storage paths directly, and use signed URL abstractions once object-storage artifacts are added.

Kubernetes and Helm are intentionally not required for V1. The local Docker path is the source of truth first.
