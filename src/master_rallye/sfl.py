"""Read-only structural parser for retail `.sfl` course fields."""
from __future__ import annotations

import math
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .errors import BoundsError, FormatError


HEADER_SIZE = 20
MAX_AXIS_CELLS = 16_777_216


@dataclass(frozen=True)
class SflHeader:
    first_float: float
    width: int
    height: int
    unknown_float_0x0c: float
    unknown_float_0x10: float
    raw: bytes


@dataclass(frozen=True)
class SflField:
    source: str
    byte_size: int
    header: SflHeader
    payload_offset: int
    payload: bytes
    value_counts: tuple[tuple[int, int], ...]

    @property
    def cell_count(self) -> int:
        return self.header.width * self.header.height

    @property
    def value_min(self) -> int | None:
        return min(self.payload) if self.payload else None

    @property
    def value_max(self) -> int | None:
        return max(self.payload) if self.payload else None

    @property
    def distinct_value_count(self) -> int:
        return len(self.value_counts)


def parse_sfl_bytes(data: bytes, source: str = "<bytes>") -> SflField:
    if len(data) < HEADER_SIZE:
        raise BoundsError(f"SFL header in {source}: need {HEADER_SIZE} bytes, have {len(data)}")
    first_float, width, height, unknown_0x0c, unknown_0x10 = struct.unpack_from("<fIIff", data, 0)
    if not math.isfinite(first_float) or not math.isfinite(unknown_0x0c) or not math.isfinite(unknown_0x10):
        raise FormatError(f"non-finite SFL header float in {source}")
    if width <= 0 or height <= 0 or width > MAX_AXIS_CELLS or height > MAX_AXIS_CELLS:
        raise FormatError(f"unreasonable SFL dimensions {width}x{height} in {source}")
    payload_size = width * height
    expected_size = HEADER_SIZE + payload_size
    if len(data) < expected_size:
        raise BoundsError(
            f"SFL payload in {source}: dimensions require {payload_size} bytes, "
            f"have {max(0, len(data) - HEADER_SIZE)}"
        )
    if len(data) > expected_size:
        raise FormatError(
            f"SFL in {source}: dimensions account for {expected_size} bytes, "
            f"file has {len(data)}"
        )
    payload = data[HEADER_SIZE:]
    counts = tuple(sorted(Counter(payload).items()))
    return SflField(
        source=source,
        byte_size=len(data),
        header=SflHeader(
            first_float,
            width,
            height,
            unknown_0x0c,
            unknown_0x10,
            data[:HEADER_SIZE],
        ),
        payload_offset=HEADER_SIZE,
        payload=payload,
        value_counts=counts,
    )


def parse_sfl(path: Path) -> SflField:
    resolved = path.resolve()
    return parse_sfl_bytes(resolved.read_bytes(), resolved.name)
