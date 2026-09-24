"""Strict structural reader for observed GXP image files (demo 9.3.1)."""
from __future__ import annotations

from pathlib import Path

from .gx_image import GxImage, parse_gx_image, parse_gx_image_bytes


def parse_gxp_bytes(data: bytes, source: str = "<bytes>") -> GxImage:
    return parse_gx_image_bytes(data, source=source, kind="GXP")


def parse_gxp(path: Path) -> GxImage:
    return parse_gx_image(path, kind="GXP")


def gxp_tile_bgra(image: GxImage, x: int, y: int, width: int, height: int) -> bytes:
    """Reproduce an observed DXT tile payload, including zero-filled padding.

    Coordinates address top-down source RGBA pixels. DXT stores the selected
    source rows bottom-up in BGRA order; any remaining right/top tile area is
    zero. This is a byte mapping, not a claim that the game performs it live.
    """
    if image.kind != "GXP":
        raise ValueError("tile source must be GXP")
    if not (0 <= x < image.width and 0 <= y < image.height):
        raise ValueError("tile origin must be inside the GXP image")
    if width <= 0 or height <= 0:
        raise ValueError("tile dimensions must be positive")
    take_width = min(width, image.width - x)
    take_height = min(height, image.height - y)
    result = bytearray(width * height * 4)
    for output_y in range(take_height):
        source_y = y + take_height - 1 - output_y
        source_start = (source_y * image.width + x) * 4
        dest_start = output_y * width * 4
        for column in range(take_width):
            source_offset = source_start + column * 4
            dest_offset = dest_start + column * 4
            red, green, blue, alpha = image.rgba[source_offset:source_offset + 4]
            result[dest_offset:dest_offset + 4] = bytes((blue, green, red, alpha))
    return bytes(result)
