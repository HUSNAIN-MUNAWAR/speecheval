# CI integration

A reference workflow lives at `examples/github-actions/tts-regression.yml`. It is intentionally marked as a Phase 4 pattern because queue execution and regression gates are not implemented in Phase 1.

The finished workflow will:

1. generate or collect audio fixtures,
2. validate a manifest,
3. create an evaluation run,
4. wait for terminal state,
5. export Markdown results,
6. fail only when a real `fail` regression decision is returned.

Do not turn demo metrics into CI evidence. Use the demo flow only to verify service wiring and UI behavior.
