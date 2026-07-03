# Contributing to SpeechEval

- Preserve CPU-first operation.
- Never turn unavailable inputs into invented metric scores.
- Include tests with behavior changes.
- Keep model, dataset, metric, and environment provenance explicit.

```bash
cp .env.example .env
make bootstrap
make seed
make test
```
