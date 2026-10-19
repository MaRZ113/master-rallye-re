"""PS2 landscape mesh access shared by the collision (W1) and render (W2) builders.

Vertex record (52 bytes, at 32 + 52 * i in the landscape PSM): normal (+0, 3 f32), colour word (+16: bytes A, c1, c2, c3), UV (+20, 2 f32),
the noise UV (+28, 2 f32; see noise_uv), position (+36, 3 f32).
UV: the PC course uses the PS2 UV as is. On every PC/PS2 shared vertex of Turkey3 the PC UV equals the raw PS2 UV, not 1 - v; PC DXT rows are
bottom-up and the GXI rows top-down, so a converted PS2 texture is written with its rows flipped (convert_gxi_rows).
Corner order: PS2 draws without back-face culling, so its strip order does not tell the visible side. PC stores a single-sided triangle with its
face normal (b - a) x (c - a) against the vertex normals; this rule reproduces the PC order on 100 percent of the single-sided shared triangles of
every directive group on 36 courses (track-render1/orientation-map-36.json).
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from water_runtime import area_normal  # noqa: E402  (the same zero-area test as ps2_obj_to_dx.source_triangles_ext)


def vertex(payload, i):
    b = 32 + 52 * i
    pos = struct.unpack_from('<3f', payload, b + 36)
    nrm = struct.unpack_from('<3f', payload, b)
    col = bytes(payload[b + 17:b + 20]) + bytes([payload[b + 16]])
    uv = struct.unpack_from('<2f', payload, b + 20)
    return pos, nrm, col, uv


def noise_uv(payload, i):
    """PC noise UV (second UV set) of a PS2 vertex: the pair at +28 plus 0.5. On 36 courses every PC noise vertex of a triangle shared with
    PS2 (1,711,740 vertices, 570,580 triangles) equals this modulo 1, with one integer offset per triangle; the noise texture wraps, so the
    integer part does not change the image."""
    u, v = struct.unpack_from('<2f', payload, 32 + 52 * i + 28)
    return (u + 0.5, v + 0.5)


def mesh_triangles(scene, mesh):
    """Vertex index triples in strip order; strips skip vertices whose control bit 0 is set and zero-area triangles
    (same rule as ps2_obj_to_dx.source_triangles_ext)."""
    out = []
    for strip in mesh['strips']:
        for newest in range(strip['start'] + 2, strip['start'] + strip['count']):
            if scene.control(newest) & 1:
                continue
            idx = (newest - 2, newest - 1, newest)
            if area_normal(tuple(scene.position(i) for i in idx))[0] <= 1e-7:
                continue
            out.append(idx)
    return out


def pc_order(payload, idx):
    """The triple in PC corner order: face normal against the summed vertex normals."""
    vs = [vertex(payload, i) for i in idx]
    a, b, c = (v[0] for v in vs)
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
    s = tuple(sum(v[1][k] for v in vs) for k in range(3))
    if n[0] * s[0] + n[1] * s[1] + n[2] * s[2] > 0:
        return (idx[1], idx[0], idx[2])
    return idx


def convert_gxi_rows(rgba, w, h):
    """BGRA pixel rows bottom-up (PC DXT layout) from GXI RGBA rows top-down."""
    out = bytearray(len(rgba))
    row = w * 4
    for y in range(h):
        src = rgba[(h - 1 - y) * row:(h - y) * row]
        dst = bytearray(src)
        for i in range(0, row, 4):
            dst[i], dst[i + 2] = src[i + 2], src[i]
        out[y * row:(y + 1) * row] = dst
    return bytes(out)
