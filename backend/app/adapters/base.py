from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    id: str
    version: str
    display_name: str
    mode: str
    enabled_by_default: bool
    limitations: str

class ModelAdapter(Protocol):
    descriptor: AdapterDescriptor
    def validate(self, configuration: dict[str, object]) -> list[str]: ...
