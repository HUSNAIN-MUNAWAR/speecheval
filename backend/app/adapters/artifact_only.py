from __future__ import annotations

from app.adapters.base import AdapterDescriptor


class ArtifactOnlyAdapter:
    descriptor=AdapterDescriptor("artifact-only","1.0.0","Artifact-only","artifact",True,"Evaluates generated audio already registered in a manifest; it does not generate speech.")
    def validate(self, configuration: dict[str, object]) -> list[str]:
        return []
