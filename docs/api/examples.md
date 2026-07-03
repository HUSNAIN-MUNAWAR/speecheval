# API examples

## Create a project

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H 'content-type: application/json' \
  --data '{"name":"Urdu Release Gate","description":"Narration evaluation"}'
```

## Register a model

```bash
curl -X POST http://localhost:8000/api/v1/models \
  -H 'content-type: application/json' \
  --data '{"project_id":"<project-uuid>","name":"Local TTS","provider":"internal","family":"custom"}'
```

## Check the system

```bash
curl -i http://localhost:8000/api/v1/health
```

Expected fields include `status`, `service`, `version`, and `request_id`.
