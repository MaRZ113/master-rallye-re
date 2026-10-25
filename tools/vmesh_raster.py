"""Tiny software rasteriser for material previews (pure Python, no dependencies; private diagnostics only).

Renders (a) a Master Rallye vehicle family (``car.dx``/``complete.dx`` + its DXT files) and (b) the original GT OBJ with its PNG
textures, from the same camera, with texture sampling, per-draw alpha blending (draws with the alpha flag, drawn after the opaque
ones in draw order, depth-tested, no depth write), alpha-test masks using the native two-byte selector gate, and
vertex-colour modulation.  It does NOT simulate the engine's environment
mapping, lighting or mip-mapping - it exists to compare UV mapping, alpha cut-outs and colours, not to predict final shading.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gtmat  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import decode_rgba_pixels, parse_dxt  # noqa: E402


@dataclass
class DrawItem:
    name: str
    tris: list                      # [(p0, p1, p2, uv0, uv1, uv2, color0, color1, color2)]
    texture: tuple | None           # (w, h, rgba upright)
    blend: bool = False
    alpha_test: bool = False
    address_modes: tuple = (0,0)    # 0 repeat, 1/2 clamp to supplied raster
    alpha_ref: int = 128


@dataclass
class Camera:
    az: float                       # degrees, 90 = looking at the +X side
    el: float
    scale: float = 1.0              # pixels per metre
    centre: tuple = (0.0, 0.8, 0.0)
    distance: float | None = None    # optional offline perspective, metres
    offset: tuple = (0.0,0.0)        # image-plane framing, pixels


def _tex_from_dxt(path: Path):
    t = parse_dxt(path)
    return t.width, t.height, decode_rgba_pixels(t)


def load_dx_family(fam: Path, which: str = "complete.dx", skip_draws=(), extra_offset=(0.0, 0.0, 0.0)) -> list[DrawItem]:
    model = parse_dx_bytes((fam / which).read_bytes())
    pos, uvs = model.vertices.positions, model.uv_sets[0].values
    cols = model.vertices.colors
    items = []
    cache = {}
    for d in model.physical_draws:
        if d.draw_index in skip_draws:
            continue
        name = d.texture_slots[0].value
        if name not in cache:
            p = fam / (name + ".dxt")
            cache[name] = _tex_from_dxt(p) if p.exists() else None
        tris = []
        for t in range(d.triangle_count):
            ids = [model.global_index_table.indices[d.index_start + 3 * t + k] for k in range(3)]
            tris.append((*(tuple(pos[i][k] + extra_offset[k] for k in range(3)) for i in ids), *(uvs[i] for i in ids),
                         *(tuple(cols[4 * i:4 * i + 3]) for i in ids)))
        alpha_enabled, test_selected = (bool(x) for x in d.flags_0x20[:2])
        items.append(DrawItem(f"{which}:{d.draw_index}", tris, cache[name],
                              alpha_enabled and not test_selected, alpha_enabled and test_selected))
    return items


def load_gt_obj(obj: Path, tp, faces_filter=None) -> list[DrawItem]:
    """GT OBJ -> draw items (one per material), transformed into the target frame with ``tp``; alpha normalised."""
    import vmesh_geometry as geo
    gt = geo.parse_gt_full(obj)
    texs = {}
    by = {}
    for o, m, t in gt["faces"]:
        if faces_filter and not faces_filter(o, m):
            continue
        if any(c[3] is None for c in t):
            continue
        if m not in texs:
            tx = gtmat.GtTexture(gt["textures"][m].read_bytes()) if m in gt["textures"] else None
            texs[m] = None if tx is None else (tx.w, tx.h, bytes(tx.rgba))
        by.setdefault(m, []).append((*(tp(c[0]) for c in t), *(c[3] for c in t), (255, 255, 255), (255, 255, 255), (255, 255, 255)))
    items = []
    for m, tris in by.items():
        tx = texs[m]
        blend = tx is not None and any(tx[2][i] < 255 for i in range(3, len(tx[2]), 4))
        items.append(DrawItem(m, tris, tx, blend))
    return items


def _project(p, cam: Camera, W, H):
    az, el = math.radians(cam.az), math.radians(cam.el)
    # camera right/up/forward in world (Y up); az 90 looks along -X
    right = (-math.cos(az), 0.0, -math.sin(az))
    fwd = (-math.sin(az) * math.cos(el), -math.sin(el), math.cos(az) * math.cos(el))
    up = (right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0])
    x, y, z = (p[0] - cam.centre[0], p[1] - cam.centre[1], p[2] - cam.centre[2])
    sx = x * right[0] + y * right[1] + z * right[2]
    sy = x * up[0] + y * up[1] + z * up[2]
    depth = x * fwd[0] + y * fwd[1] + z * fwd[2]
    factor=1.0
    if cam.distance is not None:
        if cam.distance<=0 or cam.distance+depth<=.1:raise ValueError('preview camera intersects geometry')
        factor=cam.distance/(cam.distance+depth)
    return W / 2 + sx * cam.scale*factor+cam.offset[0], H / 2 - sy * cam.scale*factor+cam.offset[1], depth


def render(items: list[DrawItem], cam: Camera, W=640, H=300, bg=(196, 200, 204), cull=0, flip_v=False) -> bytes:
    """Returns RGB bytes (W*H*3).  ``cull``: 0 none, +1/-1 cull by screen-space winding."""
    color = bytearray(bytes(bg) * (W * H))
    zbuf = [1e30] * (W * H)
    ordered = [i for i in items if not i.blend] + [i for i in items if i.blend]
    for item in ordered:
        tex = item.texture
        for t in item.tris:
            a, b, c = (_project(t[k], cam, W, H) for k in range(3))
            area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
            if abs(area) < 1e-9 or (cull and area * cull < 0):
                continue
            y0, y1 = max(0, int(math.floor(min(a[1], b[1], c[1])))), min(H - 1, int(math.ceil(max(a[1], b[1], c[1]))))
            x_lo, x_hi = max(0, int(math.floor(min(a[0], b[0], c[0])))), min(W - 1, int(math.ceil(max(a[0], b[0], c[0]))))
            uv = (t[3], t[4], t[5])
            col = (t[6], t[7], t[8])
            inv = 1.0 / area
            for y in range(y0, y1 + 1):
                py = y + 0.5
                # x interval from edge crossings
                xs = []
                for p, q in ((a, b), (b, c), (c, a)):
                    if (p[1] <= py < q[1]) or (q[1] <= py < p[1]):
                        xs.append(p[0] + (py - p[1]) * (q[0] - p[0]) / (q[1] - p[1]))
                if len(xs) < 2:
                    continue
                xa, xb = max(x_lo, int(math.floor(min(xs) - 0.5))), min(x_hi, int(math.ceil(max(xs) + 0.5)))
                for x in range(xa, xb + 1):
                    px = x + 0.5
                    w0 = ((b[0] - px) * (c[1] - py) - (c[0] - px) * (b[1] - py)) * inv
                    w1 = ((c[0] - px) * (a[1] - py) - (a[0] - px) * (c[1] - py)) * inv
                    w2 = 1.0 - w0 - w1
                    if w0 < -1e-6 or w1 < -1e-6 or w2 < -1e-6:
                        continue
                    z = w0 * a[2] + w1 * b[2] + w2 * c[2]
                    idx = y * W + x
                    if z >= zbuf[idx]:
                        continue
                    if tex is None:
                        r, g, bl, al = 128, 128, 128, 255
                    else:
                        u = w0 * uv[0][0] + w1 * uv[1][0] + w2 * uv[2][0]
                        v = w0 * uv[0][1] + w1 * uv[1][1] + w2 * uv[2][1]
                        tw, th, px_ = tex
                        vv = v if flip_v else 1.0 - v
                        tx=int(math.floor(u*tw));ty=int(math.floor(vv*th))
                        tx=tx%tw if item.address_modes[0]==0 else max(0,min(tw-1,tx))
                        ty=ty%th if item.address_modes[1]==0 else max(0,min(th-1,ty))
                        i4 = (ty*tw+tx)*4
                        r, g, bl, al = px_[i4], px_[i4 + 1], px_[i4 + 2], px_[i4 + 3]
                        if item.alpha_test and al <= item.alpha_ref:
                            continue
                        if not item.blend:
                            al = 255
                    cr = (w0 * col[0][0] + w1 * col[1][0] + w2 * col[2][0]) / 255.0
                    cg = (w0 * col[0][1] + w1 * col[1][1] + w2 * col[2][1]) / 255.0
                    cb = (w0 * col[0][2] + w1 * col[1][2] + w2 * col[2][2]) / 255.0
                    r, g, bl = r * cr, g * cg, bl * cb
                    if item.blend:
                        if al < 4:
                            continue
                        k = al / 255.0
                        o = idx * 3
                        color[o] = int(r * k + color[o] * (1 - k))
                        color[o + 1] = int(g * k + color[o + 1] * (1 - k))
                        color[o + 2] = int(bl * k + color[o + 2] * (1 - k))
                    else:
                        zbuf[idx] = z
                        o = idx * 3
                        color[o], color[o + 1], color[o + 2] = int(r), int(g), int(bl)
    return bytes(color)


def png_rgb(W: int, H: int, rgb: bytes) -> bytes:
    rgba = bytearray(W * H * 4)
    rgba[0::4], rgba[1::4], rgba[2::4], rgba[3::4] = rgb[0::3], rgb[1::3], rgb[2::3], bytes([255]) * (W * H)
    return gtmat.png_from_rgba(W, H, bytes(rgba))
