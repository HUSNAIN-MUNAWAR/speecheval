# Local development

## Commands

```bash
make bootstrap  # create Python venv and install both apps
make api        # FastAPI with hot reload on :8000
make web        # Next.js dev server on :3000
make worker     # Phase 1 worker boundary; no queue execution yet
make test       # backend + frontend tests
make lint       # Ruff, mypy, frontend type check
make format     # Ruff format and Prettier
make seed       # idempotent demo seed
```

## Local service mode

The default configuration intentionally needs neither Docker, Redis, PostgreSQL, an API key, a GPU, nor a cloud account. The API uses SQLite and local filesystem paths.

## Docker mode

```bash
cp .env.example .env
docker compose up --build
```

Docker starts PostgreSQL and Redis so Phase 2 queue work can be added without changing the service boundary. The default local mode remains the recommended path for feature development.

## Common errors

| Symptom | Cause | Resolution |
| --- | --- | --- |
| `address already in use` | Another API/web process is running | Stop the existing process or change the port. |
| `ModuleNotFoundError: app` | Backend command was run from repository root | Run through `make api`, or `cd backend`. |
| Browser cannot reach API | CORS/API base URL mismatch | Check `NEXT_PUBLIC_API_BASE_URL` and `SPEECHEVAL_CORS_ORIGINS` in `.env`. |
| Worker reports `not_configured` | Expected in Phase 1 | Queue execution begins in Phase 2; no metric result is fabricated. |
