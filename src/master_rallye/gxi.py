"""Strict structural reader for observed GXI image files."""
from __future__ import annotations

from pathlib import Path
import struct
import zlib
from .gx_image import GxImage, image_to_bgra_bottom_up, parse_gx_image, parse_gx_image_bytes


def parse_gxi_bytes(data: bytes, source: str = "<bytes>") -> GxImage:
    return parse_gx_image_bytes(data, source=source, kind="GXI")


def parse_gxi(path: Path) -> GxImage:
    return parse_gx_image(path, kind="GXI")


def encode_gxi_as_observed_dxt(image: GxImage) -> bytes:
    """Recreate the DXT bytes observed for matching same-build GXI pairs.

    This is an offline byte mapping. It does not assert a runtime cache action.
    """
    if image.kind != "GXI":
        raise ValueError("DXT source must be GXI")
    payload = image_to_bgra_bottom_up(image)
    header = struct.pack("<5I", 0x0000FEED, 1, zlib.crc32(payload) & 0xFFFFFFFF,
                         image.width, image.height)
    return header + payload
