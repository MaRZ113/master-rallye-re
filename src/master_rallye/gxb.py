"""Strict structural reader for observed GXB image files."""
from __future__ import annotations

from pathlib import Path
from .gx_image import GxImage, parse_gx_image, parse_gx_image_bytes


def parse_gxb_bytes(data: bytes, source: str = "<bytes>") -> GxImage:
    return parse_gx_image_bytes(data, source=source, kind="GXB")


def parse_gxb(path: Path) -> GxImage:
    return parse_gx_image(path, kind="GXB")
