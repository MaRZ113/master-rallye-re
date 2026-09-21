"""Case-insensitive resource lookup helpers."""
from __future__ import annotations

from pathlib import Path

from .sidecar import normalize_texture_value


class AssetResolver:
    def __init__(self, directory: Path):
        self.directory = directory
        self._files = {path.name.lower(): path for path in directory.iterdir() if path.is_file()}

    def resolve_texture(self, value: str) -> Path | None:
        if value.strip().lower() == "null":
            return None
        stem = normalize_texture_value(value)
        return self._files.get(f"{stem}.dxt".lower())
