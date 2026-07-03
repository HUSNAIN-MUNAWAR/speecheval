# Metric Plugin System

`backend/app/metrics/base.py` establishes the plugin protocol. A plugin owns a stable ID, version, display metadata, CPU compatibility signal, availability check, and typed result.

Every result must include a status and provenance such as `measured`, `mock`, `estimated`, or `external`. Do not bundle heavyweight ASR or speaker embeddings into the base package; expose them as optional dependencies in Phase 3.
