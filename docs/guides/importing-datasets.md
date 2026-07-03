# Importing datasets

A dataset is a durable registry record. A dataset version contains immutable item metadata and an input manifest hash.

## Validate a manifest

```bash
cd backend
speecheval dataset validate ../examples/manifests/demo.yaml
```

The validator rejects missing IDs and duplicate item IDs. The same validation is used by the API import flow; CLI validation is not a weaker parallel implementation.

## Supported manifest shape

```yaml
version: "1.0"
dataset:
  name: "Urdu Narration Mini"
  description: "Consent-cleared regression fixture"
items:
  - id: ur_001
    text: "یہ ایک قابلِ تکرار جانچ کا نمونہ ہے۔"
    language: ur
    generated_audio: audio/ur_001.wav
    reference_audio: references/speaker_a.wav
    tags: [narration, short-form]
    metadata:
      source: fixture
```

## API validation

```bash
curl -X POST http://localhost:8000/api/v1/datasets/validate \
  -H 'content-type: application/json' \
  --data @examples/manifests/demo.yaml
```

For the final import endpoint, send structured JSON after the manifest parser is introduced in Phase 2. Audio artifact ingestion is intentionally deferred: Phase 1 stores no raw audio and does not expose arbitrary local paths.
