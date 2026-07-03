# Quickstart

SpeechEval Phase 1 is a CPU-first provenance foundation. It records projects, versioned datasets, versioned models, and immutable evaluation manifests. It does **not** execute audio metrics yet.

## Local prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- npm 10 or newer

## Start locally

```bash
cp .env.example .env
make bootstrap
make seed
```

Start the API and web app in two terminals:

```bash
make api
make web
```

Open the dashboard at `http://localhost:3000`; inspect API contracts at `http://localhost:8000/docs`.

## Verify the foundation

```bash
make test
```

Expected backend result:

```text
3 passed
```

The database is SQLite by default and is created at `backend/.data/speecheval.db`. Delete it with `make db-reset` when you need a clean demo workspace.

## Demo boundary

The seed data is clearly labeled as `Demo Data`, `Synthetic Fixture`, and `Mock Metric`. It demonstrates record shape and UI hierarchy; it is not a quality benchmark.
