# Adding a Model Adapter

`ArtifactOnlyAdapter` is the default. New HTTP and controlled-container adapters must validate configuration server-side, redact secrets, record model image/Git provenance, use isolated artifact output, and never expose arbitrary shell command execution to public API callers.
