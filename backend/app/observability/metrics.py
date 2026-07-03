from __future__ import annotations

from collections.abc import Callable
from typing import Any

CounterFactory = Callable[[str, str], Any]
GaugeFactory = Callable[[str, str], Any]
GenerateLatest = Callable[[], bytes]
_counter_factory: CounterFactory | None
_gauge_factory: GaugeFactory | None
_generate_latest: GenerateLatest | None

try:
    from prometheus_client import Counter as _prometheus_counter
    from prometheus_client import Gauge as _prometheus_gauge
    from prometheus_client import generate_latest as _prometheus_generate_latest
except ImportError:  # pragma: no cover - dependency is optional in minimal installs
    _counter_factory = None
    _gauge_factory = None
    _generate_latest = None
else:
    _counter_factory = _prometheus_counter
    _gauge_factory = _prometheus_gauge
    _generate_latest = _prometheus_generate_latest


def _counter(name: str, documentation: str):
    factory: CounterFactory | None = _counter_factory
    return factory(name, documentation) if factory is not None else None


def _gauge(name: str, documentation: str):
    factory: GaugeFactory | None = _gauge_factory
    return factory(name, documentation) if factory is not None else None


runs_total = _counter("speecheval_runs_total", "Evaluation runs created")
runs_failed_total = _counter("speecheval_runs_failed_total", "Evaluation runs failed")
metric_duration_seconds = _counter("speecheval_metric_duration_seconds_total", "Metric execution duration seconds")
audio_validation_failures_total = _counter("speecheval_audio_validation_failures_total", "Audio validation failures")
queue_depth = _gauge("speecheval_queue_depth", "Queued evaluation jobs")
artifact_storage_bytes = _gauge("speecheval_artifact_storage_bytes", "Local artifact storage bytes")


def render_prometheus() -> bytes:
    generate_latest: GenerateLatest | None = _generate_latest
    if generate_latest is None:
        return b"# Prometheus support is unavailable\n"
    return generate_latest()
