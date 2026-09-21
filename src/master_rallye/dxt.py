"""Reader and PNG encoder for the observed Master Rallye DXT wrapper."""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

from .errors import BoundsError, FormatError

MAGIC = 0x0000FEED
MAX_DIMENSION = 16384
PNG_ROWS_PRESERVE_STORED = "preserve-stored"
PNG_ROWS_FLIP_VERTICAL = "flip-vertical"
PNG_ROW_POLICIES = {PNG_ROWS_PRESERVE_STORED, PNG_ROWS_FLIP_VERTICAL}


@dataclass(frozen=True)
class DxtTexture:
    """DXT header plus the untouched BGRA payload in stored row order."""

    source: str
    word_0x04: int
    word_0x08: int
    width: int
    height: int
    bgra: bytes


def parse_dxt_bytes(data: bytes, source: str = "<bytes>") -> DxtTexture:
    if len(data) < 20:
        raise BoundsError(f"DXT header in {source}: need 20 bytes, have {len(data)}")
    magic, word_0x04, word_0x08, width, height = struct.unpack_from("<5I", data)
    if magic != MAGIC:
        raise FormatError(f"bad DXT magic 0x{magic:08X} in {source}")
    if not 0 < width <= MAX_DIMENSION or not 0 < height <= MAX_DIMENSION:
        raise FormatError(f"unreasonable DXT dimensions {width}x{height} in {source}")
    expected = 20 + width * height * 4
    if len(data) != expected:
        raise BoundsError(f"DXT size mismatch in {source}: expected {expected}, got {len(data)}")
    return DxtTexture(source, word_0x04, word_0x08, width, height, data[20:])


def parse_dxt(path: Path) -> DxtTexture:
    return parse_dxt_bytes(path.read_bytes(), path.name)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def encode_png(texture: DxtTexture, row_policy: str = PNG_ROWS_FLIP_VERTICAL) -> bytes:
    """Encode PNG while explicitly selecting how stored DXT rows are presented."""
    if row_policy not in PNG_ROW_POLICIES:
        raise ValueError(f"unknown PNG row policy {row_policy!r}")
    rows = []
    row_indices = range(texture.height)
    if row_policy == PNG_ROWS_FLIP_VERTICAL:
        row_indices = reversed(range(texture.height))
    for y in row_indices:
        row = bytearray([0])
        source = texture.bgra[y * texture.width * 4:(y + 1) * texture.width * 4]
        for index in range(0, len(source), 4):
            blue, green, red, alpha = source[index:index + 4]
            row.extend((red, green, blue, alpha))
        rows.append(bytes(row))
    ihdr = struct.pack(">IIBBBBB", texture.width, texture.height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + png_chunk(b"IEND", b"")
    )


def write_png(
    texture: DxtTexture,
    path: Path,
    row_policy: str = PNG_ROWS_FLIP_VERTICAL,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_png(texture, row_policy=row_policy))


def has_transparency(texture: DxtTexture) -> bool:
    return any(alpha != 255 for alpha in texture.bgra[3::4])
