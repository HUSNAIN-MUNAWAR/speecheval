# Execution Engine

SpeechEval persists an `EvaluationJob` before work begins. The durable job record, not the transport, is authoritative. Local `inline` dispatch runs a CPU worker in a background thread; the Compose worker polls durable queued jobs. Both use the same executor, lifecycle validation, artifact workspace, cancellation checkpoints, events, and idempotent terminal-job guard.

A run progresses through `DRAFT → VALIDATING → QUEUED → PREPARING → RUNNING → AGGREGATING → COMPARING → REPORTING → COMPLETED|PARTIAL`. Terminal runs can only be re-executed through the rerun operation.

## Queue transport

`SPEECHEVAL_QUEUE_MODE=inline` is the default for local SQLite development. The API
runs the durable job on a CPU-safe local executor, and the CLI waits for it so that a
one-shot command cannot exit before work completes.

`SPEECHEVAL_QUEUE_MODE=dramatiq` sends the durable job UUID through Redis. Compose uses
this mode and starts `dramatiq app.workers.tasks`. Redis is a delivery mechanism, not
the system of record: `evaluation_jobs` owns idempotency keys, attempts, cancellation,
and terminal state. A duplicate message only observes a completed job and returns.
