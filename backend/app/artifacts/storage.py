from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.core.config import get_settings


class ArtifactPathError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    storage_key: str
    content_hash: str
    content_type: str
    size_bytes: int


class LocalArtifactStorage:
    """Local content-addressable artifact backend with safe relative storage keys."""

    def __init__(self, root: Path | None = None):
        self.root = (root or get_settings().artifact_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, storage_key: str) -> Path:
        key = PurePosixPath(storage_key)
        if key.is_absolute() or ".." in key.parts:
            raise ArtifactPathError("Artifact storage key must be a safe relative path.")
        path = (self.root / Path(*key.parts)).resolve()
        if self.root != path and self.root not in path.parents:
            raise ArtifactPathError("Artifact storage path escapes the configured root.")
        return path

    @staticmethod
    def fingerprint(content: bytes) -> str:
        return "sha256:" + hashlib.sha256(content).hexdigest()

    def write_bytes(self, storage_key: str, content: bytes, content_type: str | None = None) -> StoredArtifact:
        path = self.resolve(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredArtifact(
            storage_key=storage_key,
            content_hash=self.fingerprint(content),
            content_type=content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            size_bytes=len(content),
        )

    def write_text(self, storage_key: str, content: str) -> StoredArtifact:
        return self.write_bytes(storage_key, content.encode("utf-8"), "text/plain; charset=utf-8")

    def read_bytes(self, storage_key: str) -> bytes:
        return self.resolve(storage_key).read_bytes()

    def exists(self, storage_key: str) -> bool:
        return self.resolve(storage_key).is_file()
