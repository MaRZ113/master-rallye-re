"""GT3/GT4 material and texture conversion primitives for Master Rallye DX/DXT (reusable, vehicle independent).

Master Rallye draws are bound to one fixed donor texture each (dimensions and alpha-blend flag are part of the
confirmed writer boundary).  Restoring a GT appearance therefore means packing the *used UV islands* of many GT
textures into the fixed-size donor textures, remapping the vertex UVs, and routing every triangle to a draw whose
blend state matches what its texels need.  This module contains the format-level pieces:

* ``GtTexture``: RGBA PNG input with the PS2 alpha encoding normalised (PS2 alpha 0x80 = opaque is exported as
  ``2 * a + 1``: 249 is ~0.97 and counts as opaque, 65 is 0.25), wrap-around sampling;
* ``triangle_alpha_stats`` / ``classify_alpha``: alpha over the *texel footprint of a UV triangle* (not the whole texture,
  most GT textures are mostly unused atlas space) -> opaque / clear / cutout / translucent / mixed;
* ``build_islands``: triangles of one (material, pass) grouped by overlapping UV bounding boxes;
* ``Pool`` / ``pack_pools``: adaptive-resolution shelf packing into fixed-size pools, ``render_pool`` and ``remap_uv``.

No GT data is stored here.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from master_rallye.texture_authoring import decode_rgba_png  # noqa: E402

OPAQUE_SNAP = 246          # PNG alpha >= this is PS2 alpha ~0.96+ -> treated as fully opaque (normalised to 255)
CLEAR_MAX = 8              # alpha below this is "nothing there"
OPAQUE_FRACTION = 0.98
GUTTER = 2                 # texels of edge replication around every packed island
MIN_RECT = 4
SAMPLES_CAP = 16           # raster samples per triangle axis for alpha statistics


class GtTexture:
    """Straight-alpha RGBA GT texture with normalised alpha and wrap-around nearest sampling."""

    def __init__(self, png: bytes):
        self.w, self.h, rgba = decode_rgba_png(png)
        self.rgba = bytearray(rgba)
        for i in range(3, len(self.rgba), 4):
            if self.rgba[i] >= OPAQUE_SNAP:
                self.rgba[i] = 255
        self.alpha = bytes(self.rgba[3::4])

    def texel(self, x: int, y: int):
        i = ((y % self.h) * self.w + (x % self.w)) * 4
        return self.rgba[i], self.rgba[i + 1], self.rgba[i + 2], self.rgba[i + 3]

    def at_uv(self, u: float, v: float):
        """Nearest texel at OBJ-style UV (v up, image rows top-down), wrap addressing."""
        return self.texel(int(math.floor(u * self.w)), int(math.floor((1.0 - v) * self.h)))

    def mean_color(self):
        n = self.w * self.h
        wsum = sum(self.alpha) or 1
        return tuple(sum(self.rgba[i + c] * self.rgba[i + 3] for i in range(0, len(self.rgba), 4)) / wsum for c in range(3)), sum(self.alpha) / (255 * n)


# --------------------------------------------------------------------------- alpha statistics
def _inside(p, a, b, c) -> bool:
    d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
    d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1])
    d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1])
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def triangle_alpha_stats(tex: GtTexture, uvs) -> dict:
    """Alpha over the texel footprint of a UV triangle: fractions of opaque / clear / intermediate texels and the mean."""
    pts = [(u * tex.w, (1.0 - v) * tex.h) for u, v in uvs]
    lo_x, hi_x = min(p[0] for p in pts), max(p[0] for p in pts)
    lo_y, hi_y = min(p[1] for p in pts), max(p[1] for p in pts)
    sx = max(0.5, (hi_x - lo_x) / SAMPLES_CAP)
    sy = max(0.5, (hi_y - lo_y) / SAMPLES_CAP)
    n = op = cl = mid = 0
    total = 0
    x = lo_x + sx / 2
    while x < hi_x:
        y = lo_y + sy / 2
        while y < hi_y:
            if _inside((x, y), *pts):
                a = tex.alpha[(int(math.floor(y)) % tex.h) * tex.w + (int(math.floor(x)) % tex.w)]
                n += 1
                total += a
                op += a == 255
                cl += a < CLEAR_MAX
                mid += CLEAR_MAX <= a < 255
            y += sy
        x += sx
    if n == 0:     # sub-texel triangle: centroid texel
        cx, cy = sum(p[0] for p in pts) / 3, sum(p[1] for p in pts) / 3
        a = tex.alpha[(int(math.floor(cy)) % tex.h) * tex.w + (int(math.floor(cx)) % tex.w)]
        n, total, op, cl, mid = 1, a, int(a == 255), int(a < CLEAR_MAX), int(CLEAR_MAX <= a < 255)
    return {"opaque": op / n, "clear": cl / n, "intermediate": mid / n, "mean": total / (255 * n), "samples": n}


def classify_alpha(stats: dict) -> str:
    """opaque (draw without blending) | clear (invisible) | cutout (0/1 mask) | translucent | mixed (holes + translucency)."""
    if stats["opaque"] >= OPAQUE_FRACTION:
        return "opaque"
    if stats["clear"] >= OPAQUE_FRACTION:
        return "clear"
    if stats["intermediate"] >= 0.9:
        return "translucent"
    if stats["intermediate"] < 0.1:
        return "cutout"
    return "mixed"


def pass_of(alpha_class: str) -> str | None:
    """Which DX draw state a triangle needs: opaque, cutout, blend, or None (invisible)."""
    if alpha_class == "clear":
        return None
    if alpha_class in ("opaque", "cutout"):
        return alpha_class
    return "blend"


# --------------------------------------------------------------------------- islands
@dataclass
class Island:
    key: tuple                  # (material, pass)
    tris: list = field(default_factory=list)       # opaque ids chosen by the caller (face numbers)
    bbox: list = field(default_factory=lambda: [1e18, -1e18, 1e18, -1e18])    # u0, u1, v0, v1
    area: float = 0.0           # surface area in m2 (target frame)
    flat: bool = False          # uniform colour: a minimal swatch is enough
    degraded: bool = False      # forced to a mean-colour swatch because no pool had room for its real resolution

    def add(self, tri_id, uvs, area):
        self.tris.append(tri_id)
        for u, v in uvs:
            self.bbox[0] = min(self.bbox[0], u)
            self.bbox[1] = max(self.bbox[1], u)
            self.bbox[2] = min(self.bbox[2], v)
            self.bbox[3] = max(self.bbox[3], v)
        self.area += area

    def overlaps(self, other: "Island") -> bool:
        a, b = self.bbox, other.bbox
        return not (a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2])


def build_islands(items) -> list[Island]:
    """``items``: iterable of (material, pass, tri_id, uvs, area).  Triangles of the same (material, pass) whose UV
    bounding boxes overlap (transitively) form one island."""
    groups: dict[tuple, list[Island]] = {}
    for material, pas, tri_id, uvs, area in items:
        tri_island = Island((material, pas))
        tri_island.add(tri_id, uvs, area)
        groups.setdefault((material, pas), []).append(tri_island)
    out = []
    for key, singles in groups.items():
        merged: list[Island] = []
        for s in singles:
            hit = [m for m in merged if m.overlaps(s)]
            base = Island(key)
            for part in hit + [s]:
                base.tris += part.tris
                base.area += part.area
                for i in (0, 2):
                    base.bbox[i] = min(base.bbox[i], part.bbox[i])
                for i in (1, 3):
                    base.bbox[i] = max(base.bbox[i], part.bbox[i])
            merged = [m for m in merged if m not in hit] + [base]
        out += merged
    return out


# --------------------------------------------------------------------------- pools and packing
@dataclass
class Pool:
    name: str                   # donor texture basename (e.g. "sidenav1-tga")
    width: int
    height: int
    pass_: str                  # 'opaque' | 'cutout' | 'blend' | 'special'
    draws: dict = field(default_factory=dict)      # {"car.dx": draw index, "complete.dx": draw index}
    placements: list = field(default_factory=list)  # (island, x, y, w, h)
    alpha_scale: float = 1.0


def _shelf_pack(sizes, width, height):
    """sizes: list of (w, h) -> list of (x, y) or None when they do not fit (tallest-first shelves)."""
    order = sorted(range(len(sizes)), key=lambda i: (-sizes[i][1], -sizes[i][0]))
    pos = [None] * len(sizes)
    x = y = shelf_h = 0
    for i in order:
        w, h = sizes[i]
        if w > width or h > height:
            return None
        if x + w > width:
            x, y, shelf_h = 0, y + shelf_h, 0
        if y + h > height:
            return None
        pos[i] = (x, y)
        x += w
        shelf_h = max(shelf_h, h)
    return pos


def island_source_size(island: Island, tex_w: int, tex_h: int):
    u0, u1, v0, v1 = island.bbox
    return max(1.0, (u1 - u0) * tex_w), max(1.0, (v1 - v0) * tex_h)


def _maxrect_pack(sizes,width,height):
    """Deterministic optional best-short-side placement with free-rectangle splits.

    Free rectangles may overlap one another; every placed rectangle is removed
    from all of them. This reuses short spaces beside tall islands that a shelf
    allocator leaves empty. Pixel buffers and native texture sizes do not grow.
    """
    free=[(0,0,width,height)];positions=[None]*len(sizes)
    for i in sorted(range(len(sizes)),key=lambda k:(-max(sizes[k]),-min(sizes[k]),k)):
        w,h=sizes[i]
        candidates=[(min(fw-w,fh-h),max(fw-w,fh-h),y,x,j)
                    for j,(x,y,fw,fh) in enumerate(free) if w<=fw and h<=fh]
        if not candidates:return None
        _,_,y,x,_=min(candidates);positions[i]=(x,y);next_free=[]
        for fx,fy,fw,fh in free:
            if x>=fx+fw or x+w<=fx or y>=fy+fh or y+h<=fy:
                next_free.append((fx,fy,fw,fh));continue
            if fx<x:next_free.append((fx,fy,x-fx,fh))
            if x+w<fx+fw:next_free.append((x+w,fy,fx+fw-x-w,fh))
            if fy<y:next_free.append((fx,fy,fw,y-fy))
            if y+h<fy+fh:next_free.append((fx,y+h,fw,fy+fh-y-h))
        unique=sorted(set(next_free))
        free=[r for r in unique if not any(r!=q and q[0]<=r[0] and q[1]<=r[1] and
              r[0]+r[2]<=q[0]+q[2] and r[1]+r[3]<=q[1]+q[3] for q in unique)]
    return positions


def pack_pool(pool: Pool, islands: list[Island], tex_dims: dict, min_density: float = 0.0):
    """Pack ``islands`` into ``pool`` with the largest uniform density (texels per m2) that fits.

    Island rectangles never exceed their source texel size (no upscaling).  Returns (density, packed, rejected)."""
    def sizes_for(density):
        out = []
        for isl in islands:
            sw, sh = island_source_size(isl, *tex_dims[isl.key[0]])
            want = MIN_RECT * MIN_RECT if isl.flat else min(sw * sh, max(MIN_RECT * MIN_RECT, isl.area * density * getattr(isl,'density_weight',1.0)))
            # rectangle aspect is the geometric mean of the source aspect and 1 (very wide/tall atlases keep texels usable in a
            # square pool); never more texels than the source along either axis
            ar = math.sqrt(sw / sh)
            w = min(sw, max(MIN_RECT, math.sqrt(want * ar)))
            h = min(sh, max(MIN_RECT, want / w))
            w = min(sw, max(MIN_RECT, want / h))
            out.append((int(round(w)) + 2 * GUTTER, int(round(h)) + 2 * GUTTER))
        return out
    if not islands:
        return 0.0, [], []
    lo, hi = 1.0, 1e7
    best = None
    for _ in range(40):
        mid = math.sqrt(lo * hi)
        packer=_maxrect_pack if getattr(pool,'packing','shelf')=='maxrects' else _shelf_pack
        pos = packer(sizes_for(mid), pool.width, pool.height)
        if pos is None:
            hi = mid
        else:
            best, lo = (mid, pos), mid
        if hi / lo < 1.01:
            break
    if best is None:
        return 0.0, [], list(islands)
    density, pos = best
    sizes = sizes_for(density)
    pool.placements = [(isl, p[0] + GUTTER, p[1] + GUTTER, s[0] - 2 * GUTTER, s[1] - 2 * GUTTER)
                       for isl, p, s in zip(islands, pos, sizes)]
    return density, list(islands), []


def assign_to_pools(islands: list[Island], pools: list[Pool], tex_dims: dict, target_density: float = 5000.0):
    """Distribute islands over pools so that every pool ends up equally loaded; returns (rejected islands, per-pool report).

    Islands (descending area) go to the pool with the lowest ``load / capacity`` after adding the pixels the island would need at
    ``target_density`` (texels per m2, capped by its source size); each pool is then packed at the largest uniform density that
    fits, so crowding lowers resolution instead of rejecting islands.  An island that cannot fit even at the minimum density
    is returned as rejected."""
    order = sorted(islands, key=lambda i: -i.area)
    loads = [0.0] * len(pools)
    chosen = [[] for _ in pools]
    for isl in order:
        sw, sh = island_source_size(isl, *tex_dims[isl.key[0]])
        need = MIN_RECT * MIN_RECT if isl.flat else min(sw * sh, max(MIN_RECT * MIN_RECT, isl.area * target_density))
        j = min(range(len(pools)), key=lambda k: (loads[k] + need) / (pools[k].width * pools[k].height))
        chosen[j].append(isl)
        loads[j] += need
    rejected, report = [], []
    for pool, group in zip(pools, chosen):
        group = sorted(group, key=lambda i: -i.area)
        while group:
            density, packed, rej = pack_pool(pool, group, tex_dims)
            if packed:
                break
            rejected.append(group.pop())
        else:
            pool.placements = []
        chosen[pools.index(pool)] = group
    # second chance: islands that did not fit their pool try every other pool (then as a minimal swatch of their mean colour)
    for isl in sorted(rejected, key=lambda i: -i.area):
        placed = False
        was_flat = isl.flat
        for flat in (isl.flat, True):
            isl.flat = flat
            isl.degraded = flat and not was_flat
            for j in sorted(range(len(pools)), key=lambda k: len(chosen[k])):
                trial = sorted(chosen[j] + [isl], key=lambda i: -i.area)
                saved = list(pools[j].placements)
                density, packed, rej = pack_pool(pools[j], trial, tex_dims)
                if packed:
                    chosen[j] = trial
                    placed = True
                    break
                pools[j].placements = saved
            if placed:
                break
        if placed:
            rejected = [r for r in rejected if r is not isl]
    for pool, group in zip(pools, chosen):
        if group:
            density, _, _ = pack_pool(pool, group, tex_dims)
            report.append({"pool": pool.name, "density_texels_per_m2": round(density, 1), "islands": len(group)})
    return sorted(rejected, key=lambda i: -i.area), report


def remap_uv(pool: Pool, island: Island, rect, uv):
    """Source UV -> pool UV for an island placed at ``rect`` = (x, y, w, h) (pixels, image rows top-down)."""
    x, y, w, h = rect
    u0, u1, v0, v1 = island.bbox
    fu = 0.5 if u1 - u0 < 1e-9 else (uv[0] - u0) / (u1 - u0)
    fv = 0.5 if v1 - v0 < 1e-9 else (v1 - uv[1]) / (v1 - v0)         # image row grows downward, v upward
    return ((x + fu * w) / pool.width, 1.0 - (y + fv * h) / pool.height)


def render_pool(pool: Pool, textures: dict, background=(0, 0, 0, 0)) -> bytes:
    """RGBA (PNG row order) pixels of a pool: every island is area-averaged into its rectangle, gutters replicate edges.

    Colour is averaged alpha-weighted (no dark halos on cut-out edges); alpha is the plain average, scaled by pool.alpha_scale.
    """
    w, h = pool.width, pool.height
    out = bytearray(bytes(background) * (w * h))
    for island, rx, ry, rw, rh in pool.placements:
        tex = textures[island.key[0]]
        u0, u1, v0, v1 = island.bbox
        sx0, sx1 = u0 * tex.w, max(u1 * tex.w, u0 * tex.w + 1)
        sy0, sy1 = (1.0 - v1) * tex.h, max((1.0 - v0) * tex.h, (1.0 - v1) * tex.h + 1)
        for oy in range(-GUTTER, rh + GUTTER):
            for ox in range(-GUTTER, rw + GUTTER):
                px, py = rx + ox, ry + oy
                if not (0 <= px < w and 0 <= py < h):
                    continue
                cx = min(max(ox, 0), rw - 1)
                cy = min(max(oy, 0), rh - 1)
                x_a, x_b = sx0 + (sx1 - sx0) * cx / rw, sx0 + (sx1 - sx0) * (cx + 1) / rw
                y_a, y_b = sy0 + (sy1 - sy0) * cy / rh, sy0 + (sy1 - sy0) * (cy + 1) / rh
                nx = max(1, min(4, int(math.ceil(x_b - x_a))))
                ny = max(1, min(4, int(math.ceil(y_b - y_a))))
                rs = gs = bs = asum = wsum = 0.0
                for iy in range(ny):
                    for ix in range(nx):
                        t = tex.texel(int(math.floor(x_a + (x_b - x_a) * (ix + 0.5) / nx)), int(math.floor(y_a + (y_b - y_a) * (iy + 0.5) / ny)))
                        rs += t[0] * t[3]
                        gs += t[1] * t[3]
                        bs += t[2] * t[3]
                        asum += t[3]
                        wsum += 1
                a_mean = asum / wsum
                if asum > 0:
                    rgb = (rs / asum, gs / asum, bs / asum)
                else:
                    rgb = (0, 0, 0)
                i = (py * w + px) * 4
                out[i:i + 4] = bytes((int(rgb[0] + 0.5), int(rgb[1] + 0.5), int(rgb[2] + 0.5),
                                      max(0, min(255, int(a_mean * pool.alpha_scale + 0.5)))))
    return bytes(out)


def flat_color_pool(width: int, height: int, rgba) -> bytes:
    return bytes(rgba) * (width * height)


def dilate_color(px: bytearray, w: int, h: int, passes: int = 3) -> None:
    """Fill the colour of fully transparent texels from visible neighbours (no dark fringes under bilinear filtering)."""
    for _ in range(passes):
        src = bytes(px)
        changed = False
        for y in range(h):
            for x in range(w):
                i = (y * w + x) * 4
                if src[i + 3] != 0 or (src[i] or src[i + 1] or src[i + 2]):
                    continue
                r = g = b = n = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < w and 0 <= yy < h:
                            j = (yy * w + xx) * 4
                            if src[j + 3] > 0 or src[j] or src[j + 1] or src[j + 2]:
                                r += src[j]
                                g += src[j + 1]
                                b += src[j + 2]
                                n += 1
                if n:
                    px[i], px[i + 1], px[i + 2] = r // n, g // n, b // n
                    changed = True
        if not changed:
            break


def png_from_rgba(width: int, height: int, rgba: bytes) -> bytes:
    """Minimal RGBA8 PNG writer (rows top-down, as consumed by ``vehicle_project`` texture edits)."""
    import struct
    import zlib
    raw = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    return (bytes([0x89]) + b"PNG" + bytes([13, 10, 26, 10]) + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def footprint_mean(rgba, width: int, height: int, uvs) -> tuple:
    """Alpha-weighted mean colour and mean alpha over the texel footprint of a UV triangle (PNG row order, wrap)."""
    pts = [(u * width, (1.0 - v) * height) for u, v in uvs]
    lo_x, hi_x = min(p[0] for p in pts), max(p[0] for p in pts)
    lo_y, hi_y = min(p[1] for p in pts), max(p[1] for p in pts)
    sx, sy = max(0.5, (hi_x - lo_x) / SAMPLES_CAP), max(0.5, (hi_y - lo_y) / SAMPLES_CAP)
    r = g = b = a = wsum = n = 0.0
    x = lo_x + sx / 2
    while x < hi_x:
        y = lo_y + sy / 2
        while y < hi_y:
            if _inside((x, y), *pts):
                i = ((int(math.floor(y)) % height) * width + (int(math.floor(x)) % width)) * 4
                al = rgba[i + 3]
                r += rgba[i] * al
                g += rgba[i + 1] * al
                b += rgba[i + 2] * al
                wsum += al
                a += al
                n += 1
            y += sy
        x += sx
    if n == 0:
        cx, cy = sum(p[0] for p in pts) / 3, sum(p[1] for p in pts) / 3
        i = ((int(math.floor(cy)) % height) * width + (int(math.floor(cx)) % width)) * 4
        return (rgba[i], rgba[i + 1], rgba[i + 2]), rgba[i + 3]
    if wsum == 0:
        return (0.0, 0.0, 0.0), 0.0
    return (r / wsum, g / wsum, b / wsum), a / n
