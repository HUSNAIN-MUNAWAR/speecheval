# Writing metric plugins

Metric implementations are intentionally separated from the API. A plugin reports whether it is available before it can emit values.

## Contract

A plugin declares an ID, semantic version, category, input requirements, CPU compatibility, optional dependencies, availability, per-item evaluation, and aggregation behavior. See `backend/app/metrics/base.py`.

## Rules

- Return **unavailable** or **skipped** when requirements are absent.
- Never substitute a mock value unless the run is explicitly demo-mode and marks it as a mock metric.
- Preserve plugin version and options in each result.
- Make directionality explicit: lower is better for WER/CER/latency; higher is better for a similarity score.
- Keep CPU-capable paths lightweight; heavyweight ASR or embedding packages are optional extras.

## Phase 2 plugin sequence

1. Audio validation.
2. Duration, silence ratio, clipping, and loudness.
3. Artifact waveform generation.
4. Aggregate-statistic and availability reporting.

The registry is present now so that metric execution can arrive without changing run or report contracts.
