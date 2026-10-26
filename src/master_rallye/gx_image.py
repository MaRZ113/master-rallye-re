"""Strict reader for the observed eight-byte GX image container.

The two filename extensions are kept distinct at the API boundary. This module
only expresses their proven shared byte layout, not a common runtime role.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .errors import BoundsError, FormatError

MAGIC = 0x00013039
MAX_DIMENSION = 16384


@dataclass(frozen=True)
class GxImage:
    source: str
    kind: str
    width: int
    height: int
    rgba: bytes
    header: bytes


def parse_gx_image_bytes(data: bytes, *, source: str = "<bytes>", kind: str) -> GxImage:
    if len(data) < 8:
        raise BoundsError(f"{kind} header in {source}: need 8 bytes, have {len(data)}")
    magic, width, height = struct.unpack_from("<IHH", data)
    if magic != MAGIC:
        raise FormatError(f"bad {kind} magic 0x{magic:08X} in {source}")
    if not (0 < width <= MAX_DIMENSION and 0 < height <= MAX_DIMENSION):
        raise FormatError(f"unreasonable {kind} dimensions {width}x{height} in {source}")
    expected = 8 + width * height * 4
    if len(data) != expected:
        raise BoundsError(f"{kind} size mismatch in {source}: expected {expected}, got {len(data)}")
    return GxImage(source, kind, width, height, data[8:], data[:8])


def parse_gx_image(path: Path, *, kind: str) -> GxImage:
    return parse_gx_image_bytes(path.read_bytes(), source=str(path), kind=kind)


def image_to_bgra_bottom_up(image: GxImage) -> bytes:
    """Observed same-build GX image to DXT/TGA pixel correspondence."""
    stride = image.width * 4
    result = bytearray(len(image.rgba))
    for out_y, in_y in enumerate(reversed(range(image.height))):
        src = image.rgba[in_y * stride:(in_y + 1) * stride]
        dst_start = out_y * stride
        for i in range(0, stride, 4):
            result[dst_start + i:dst_start + i + 4] = bytes((src[i + 2], src[i + 1], src[i], src[i + 3]))
    return bytes(result)
