# Writing a Metric Plugin

Implement `MetricPlugin`, declare availability and limitations, return explicit statuses for every error or unsupported input, write unit tests with deterministic fixtures, and never return a fabricated score when an optional dependency is absent.
