# CI Regression Testing

Use `speecheval ci evaluate --candidate-run <id> --baseline-run <id>`. It emits a Markdown summary and exits with code 2 for `LIKELY_REGRESSION` or `NOT_COMPARABLE`. Persist the generated audio and manifest before invoking evaluation.
