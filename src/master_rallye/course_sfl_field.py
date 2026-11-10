"""Course SFL heading-field geometry and an experimental route-derived synthesizer.

The structural reader in :mod:`master_rallye.sfl` keeps neutral names. This
module adds the geometric interpretation measured on the Retail corpus:

* header ``<fIIff>`` = cell size, width (X cells), height (Z cells), origin X,
  origin Z; every Retail file uses cell size 3.0 and its grid encloses the
  course RaceLine X/Z bounds;
* the payload is **column-major**: ``payload[x_index * height + z_index]``;
* each byte is a quantized heading ``round(256 * atan2(-dx, dz) / 2pi) mod 256``.
  Far from the route it points at the nearest RaceLine sample; on the route it
  follows the local RaceLine travel direction.

The owning component is ``gaIContAIManager`` (``AI DataSet Name`` =
``ICont/<name>``). That executable consumer and the heading interpretation are
corpus/geometry correlations, not a runtime proof of how AI steering uses the
field. :func:`synthesize_heading_field` is an approximation intended for new
course experiments; it is validated by agreement statistics, not byte equality.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Sequence

from .errors import FormatError
from .sfl import HEADER_SIZE, SflField

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class SflGrid:
    cell_size: float
    width: int
    height: int
    origin_x: float
    origin_z: float

    @property
    def max_x(self) -> float:
        return self.origin_x + self.width * self.cell_size

    @property
    def max_z(self) -> float:
        return self.origin_z + self.height * self.cell_size

    def cell_center(self, x_index: int, z_index: int) -> tuple[float, float]:
        return (
            self.origin_x + (x_index + 0.5) * self.cell_size,
            self.origin_z + (z_index + 0.5) * self.cell_size,
        )

    def cell_of(self, x: float, z: float) -> tuple[int, int] | None:
        i = math.floor((x - self.origin_x) / self.cell_size)
        j = math.floor((z - self.origin_z) / self.cell_size)
        if 0 <= i < self.width and 0 <= j < self.height:
            return i, j
        return None

    def pack_header(self) -> bytes:
        return struct.pack("<fIIff", self.cell_size, self.width, self.height, self.origin_x, self.origin_z)


def sfl_grid(field: SflField) -> SflGrid:
    header = field.header
    if header.first_float <= 0.0:
        raise FormatError(f"SFL cell size must be positive in {field.source}")
    return SflGrid(header.first_float, header.width, header.height,
                   header.unknown_float_0x0c, header.unknown_float_0x10)


def sample(field: SflField, x: float, z: float) -> int | None:
    """Return the stored byte for world X/Z using the column-major layout."""
    grid = sfl_grid(field)
    cell = grid.cell_of(x, z)
    if cell is None:
        return None
    return field.payload[cell[0] * grid.height + cell[1]]


def heading_byte(dx: float, dz: float) -> int:
    return int(round(math.atan2(-dx, dz) / (2.0 * math.pi) * 256.0)) % 256


def heading_error(a: int, b: int) -> int:
    """Smallest wrapped distance between two heading bytes (0..128)."""
    return abs((int(a) - int(b) + 128) % 256 - 128)


def grid_for_route(route: Sequence[Vec3], *, cell_size: float = 3.0, margin: float = 60.0) -> SflGrid:
    """Choose a Retail-like grid enclosing the route X/Z bounds plus a margin."""
    if len(route) < 2:
        raise ValueError("a route needs at least two samples")
    xs = [p[0] for p in route]
    zs = [p[2] for p in route]
    origin_x = min(xs) - margin
    origin_z = min(zs) - margin
    width = int(math.ceil((max(xs) + margin - origin_x) / cell_size))
    height = int(math.ceil((max(zs) + margin - origin_z) / cell_size))
    return SflGrid(cell_size, width, height, origin_x, origin_z)


def synthesize_heading_field(
    route: Sequence[Vec3],
    grid: SflGrid | None = None,
    *,
    near_radius: float = 8.0,
    far_radius: float = 40.0,
    lookahead: int = 1,
    chunk: int = 65536,
) -> bytes:
    """Build a complete SFL file from an ordered RaceLine.

    Cells within ``near_radius`` of the nearest sample use the travel heading
    from that sample to ``sample + lookahead``; cells beyond ``far_radius`` aim
    at the nearest sample; the band between them blends the two unit vectors.
    Requires numpy (an optional dependency used only by this experiment).
    """
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("SFL synthesis requires numpy") from exc
    if len(route) < 2:
        raise ValueError("a route needs at least two samples")
    if not 0.0 <= near_radius < far_radius:
        raise ValueError("expected 0 <= near_radius < far_radius")
    grid = grid or grid_for_route(route)
    pts = np.asarray([(p[0], p[2]) for p in route], dtype=np.float64)
    ahead = np.minimum(np.arange(len(pts)) + lookahead, len(pts) - 1)
    travel = pts[ahead] - pts
    travel[-1] = pts[-1] - pts[-2]
    travel /= np.maximum(np.linalg.norm(travel, axis=1, keepdims=True), 1e-9)

    ii, jj = np.meshgrid(np.arange(grid.width), np.arange(grid.height), indexing="ij")
    cx = (grid.origin_x + (ii.ravel() + 0.5) * grid.cell_size)
    cz = (grid.origin_z + (jj.ravel() + 0.5) * grid.cell_size)
    out = np.empty(cx.size, dtype=np.uint8)
    for start in range(0, cx.size, chunk):
        x = cx[start:start + chunk, None]
        z = cz[start:start + chunk, None]
        d2 = (pts[None, :, 0] - x) ** 2 + (pts[None, :, 1] - z) ** 2
        nearest = np.argmin(d2, axis=1)
        dist = np.sqrt(d2[np.arange(nearest.size), nearest])
        to = pts[nearest] - np.stack((x[:, 0], z[:, 0]), axis=1)
        to /= np.maximum(np.linalg.norm(to, axis=1, keepdims=True), 1e-9)
        weight = np.clip((dist - near_radius) / (far_radius - near_radius), 0.0, 1.0)[:, None]
        direction = travel[nearest] * (1.0 - weight) + to * weight
        angle = np.arctan2(-direction[:, 0], direction[:, 1])
        out[start:start + chunk] = (np.rint(angle / (2 * np.pi) * 256.0).astype(np.int64) % 256).astype(np.uint8)
    # meshgrid(indexing="ij").ravel() is already x-major / column-major.
    data = grid.pack_header() + out.tobytes()
    assert len(data) == HEADER_SIZE + grid.width * grid.height
    return data


def synthesize_pursuit_field(
    route: Sequence[Vec3],
    grid: SflGrid | None = None,
    *,
    lookahead: float = 10.0,
    spacing: float = 2.0,
    chunk: int = 4096,
) -> bytes:
    """SFL in the Retail style: every cell aims at the route point ``lookahead``
    units of arc length past its nearest route point (pure pursuit).

    Retail fields steer a car that is off the line back to it: measured on
    SpainW/France1/Italy1 the heading deviates from the road direction by about
    10-15 degrees 3 units off the line, 30 at 6 and 45-60 at 10, always towards
    the line. The older ``synthesize_heading_field`` is parallel to the road up
    to 8 units off it, so AI cars drifting wide never came back (walls).
    """
    import numpy as np
    from .course_atlas import resample_route

    if len(route) < 2:
        raise ValueError("a route needs at least two samples")
    grid = grid or grid_for_route(route)
    dense = resample_route(route, spacing)
    pts = np.asarray([(p[0], p[2]) for p in dense], dtype=np.float64)
    step = max(1, int(round(lookahead / spacing)))
    last = len(pts) - 1
    tail = pts[-1] - pts[-2]
    tail /= max(float(np.linalg.norm(tail)), 1e-9)
    ii, jj = np.meshgrid(np.arange(grid.width), np.arange(grid.height), indexing="ij")
    cx = (grid.origin_x + (ii.ravel() + 0.5) * grid.cell_size)
    cz = (grid.origin_z + (jj.ravel() + 0.5) * grid.cell_size)
    out = np.empty(cx.size, dtype=np.uint8)
    for start in range(0, cx.size, chunk):
        x = cx[start:start + chunk, None]
        z = cz[start:start + chunk, None]
        d2 = (pts[None, :, 0] - x) ** 2 + (pts[None, :, 1] - z) ** 2
        nearest = np.argmin(d2, axis=1)
        target_index = np.minimum(nearest + step, last)
        target = pts[target_index]
        # past the end keep pursuing along the final direction
        over = nearest + step - last
        target = target + np.where(over[:, None] > 0, tail[None, :] * (over[:, None] * spacing), 0.0)
        direction = target - np.stack((x[:, 0], z[:, 0]), axis=1)
        angle = np.arctan2(-direction[:, 0], direction[:, 1])
        out[start:start + chunk] = (np.rint(angle / (2 * np.pi) * 256.0).astype(np.int64) % 256).astype(np.uint8)
    data = grid.pack_header() + out.tobytes()
    assert len(data) == HEADER_SIZE + grid.width * grid.height
    return data


def compare_heading_fields(reference: SflField, candidate: SflField, *, stride: int = 7) -> dict[str, float]:
    """Wrapped-heading agreement statistics over a regular subsample."""
    ref_grid, cand_grid = sfl_grid(reference), sfl_grid(candidate)
    errors: list[int] = []
    for i in range(0, ref_grid.width, stride):
        for j in range(0, ref_grid.height, stride):
            x, z = ref_grid.cell_center(i, j)
            other = cand_grid.cell_of(x, z)
            if other is None:
                continue
            errors.append(heading_error(
                reference.payload[i * ref_grid.height + j],
                candidate.payload[other[0] * cand_grid.height + other[1]],
            ))
    if not errors:
        return {"samples": 0}
    errors.sort()
    n = len(errors)
    return {
        "samples": n,
        "median_byte_error": float(errors[n // 2]),
        "p90_byte_error": float(errors[int(n * 0.9)]),
        "within_8_bytes": sum(e <= 8 for e in errors) / n,
        "median_degrees": errors[n // 2] * 360.0 / 256.0,
    }
