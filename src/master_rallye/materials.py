"""Material binding helpers kept separate from binary parsing."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .assets import AssetResolver
from .model import DrawRecord


@dataclass(frozen=True)
class PreviewBinding:
    draw_index: int
    primary_slot: str | None
    texture_path: Path | None
    missing_texture: bool


def select_preview_binding(draw: DrawRecord, resolver: AssetResolver) -> PreviewBinding:
    primary = next((slot.value for slot in draw.texture_slots if slot.value.lower() != "null"), None)
    texture_path = resolver.resolve_texture(primary) if primary else None
    return PreviewBinding(
        draw_index=draw.draw_index if draw.draw_index is not None else -1,
        primary_slot=primary,
        texture_path=texture_path,
        missing_texture=primary is not None and texture_path is None,
    )
