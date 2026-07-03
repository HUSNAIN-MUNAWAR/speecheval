# Storage and Artifacts

Local development reserves `SPEECHEVAL_ARTIFACT_ROOT` for artifacts. Phase 2 will introduce local filesystem and S3-compatible storage adapters. Artifact references must be opaque, hashed, versioned, and never expose raw host paths directly.
