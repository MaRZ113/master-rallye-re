"""Marker-1339 vehicle spatial bounds; conservative edited-resource writer."""
from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Iterable, Sequence

from .errors import DxWriteError


def f32(value: float) -> float:
    if not math.isfinite(value):
        raise DxWriteError("non-finite spatial bound")
    try:
        return struct.unpack("<f", struct.pack("<f", value))[0]
    except (OverflowError, struct.error) as error:
        raise DxWriteError("spatial bound exceeds float32 range") from error


@dataclass(frozen=True)
class DxSpatialBounds1339:
    offset: int
    center: tuple[float, float, float]
    radius: float
    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]
    raw: bytes

    def to_dict(self) -> dict:
        return {"offset": self.offset, "marker": 1339, "center": list(self.center),
                "radius": self.radius, "minimum": list(self.minimum),
                "maximum": list(self.maximum)}


def parse_bounds1339(data: bytes, offset: int = 0) -> DxSpatialBounds1339 | None:
    if len(data) != 44 or struct.unpack_from("<I", data)[0] != 1339:
        return None
    center = struct.unpack_from("<3f", data, 4)
    radius = struct.unpack_from("<f", data, 16)[0]
    minimum = struct.unpack_from("<3f", data, 20)
    maximum = struct.unpack_from("<3f", data, 32)
    if not all(math.isfinite(v) for v in center + (radius,) + minimum + maximum):
        raise DxWriteError("marker-1339 contains non-finite bounds")
    if radius < 0 or any(minimum[i] > maximum[i] for i in range(3)):
        raise DxWriteError("marker-1339 has inverted bounds or negative radius")
    return DxSpatialBounds1339(offset, center, radius, minimum, maximum, data)


def bound_points(render_positions: Iterable[Sequence[float]], hull=None) -> tuple[tuple[float, float, float], ...]:
    """The corpus-supported extrema/radius point set: render plus detailed tag101 B."""
    points = [tuple(p) for p in render_positions]
    if hull is not None:
        points.extend(tuple(p) for p in hull.representation_b.geometry_a.vertices)
    if not points:
        raise DxWriteError("no points for vehicle bounds")
    if any(len(p) != 3 or not all(math.isfinite(v) and abs(v) <= 10000 for v in p) for p in points):
        raise DxWriteError("vehicle bounds require finite, sane-size XYZ points")
    return tuple(points)


def compute_bounds1339(render_positions: Iterable[Sequence[float]], hull=None, *, offset: int = 0) -> DxSpatialBounds1339:
    points = bound_points(render_positions, hull)
    minimum = tuple(min(p[i] for p in points) for i in range(3))
    maximum = tuple(max(p[i] for p in points) for i in range(3))
    center = tuple(f32((minimum[i] + maximum[i]) / 2) for i in range(3))
    distance = max(math.dist(p, center) for p in points)
    radius = f32(distance)
    if radius < distance:
        radius = math.nextafter(radius, math.inf)
        radius = f32(radius)
        if radius < distance:
            radius = struct.unpack("<f", struct.pack("<I", struct.unpack("<I", struct.pack("<f", radius))[0] + 1))[0]
    raw = struct.pack("<I3ff3f3f", 1339, *center, radius, *minimum, *maximum)
    return DxSpatialBounds1339(offset, center, radius, minimum, maximum, raw)


def replace_bounds1339(data: bytes, bounds: DxSpatialBounds1339, *, footer_offset: int) -> bytes:
    if footer_offset < 0 or len(data) != footer_offset + 44 or parse_bounds1339(data[footer_offset:], footer_offset) is None:
        raise DxWriteError("marker-1339 source footer mismatch")
    return data[:footer_offset] + bounds.raw + data[footer_offset + 44:]
