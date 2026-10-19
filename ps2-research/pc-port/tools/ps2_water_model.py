"""COURSE-WATER1 reference model of the PS2 water shaders (modes 9 puddle, 10 water, 19 waterfall/waterall).

Pure functions in float32, operation by operation as the EE code (SLES_509.06, decompiled with Ghidra EER; see
docs/course-water1/README.md for the addresses). The C++ renderer (renderer/ps2_water.hpp) follows this module and the tests
compare both bit for bit.

- 328c90  sine table: L[i] = sinf(float(i) * C * 2^-12), i < 4096, C = 15acc8() = 0x40c90fdb (2 pi in float32).
- 316808  phase T = float(counter) / 150 (unchanged while Game/PauseMenuEnabled is true).
- 320938  puddle load: vertex RGBA from the gap to the lowest non-water ground hit below the vertex (2d4618 query).
- 320c78  puddle frame update: primary and secondary UV from position, normal, T and the camera rows 42dc00.
- 320f90 -> 321098  water load: RGBA 254, primary and secondary UV once (load-time T), integer mean rebase.
- 321838  waterfall frame update: V from world Y and frac(2T) / frac(4T); secondary U = primary U.
"""
from __future__ import annotations

import math
import struct

F32 = struct.Struct('<f')
I32 = struct.Struct('<I')


def f32(x: float) -> float:
    return F32.unpack(F32.pack(x))[0]


def bits(x: float) -> int:
    return I32.unpack(F32.pack(x))[0]


C = F32.unpack(bytes.fromhex('db0fc940'))[0]          # 0x40c90fdb
INDEX_SCALE = f32(4096.0 / C)                          # 4096.0 / fVar9, evaluated in float32
TABLE = tuple(f32(math.sin(f32(f32(f32(i) * C) * 0.000244140625))) for i in range(4096))


def trunc_index(x: float) -> int:
    """EE cvt.w.s (round toward zero), two's complement, then `& 0xfff` by the caller."""
    x = f32(x)
    if not math.isfinite(x) or abs(x) >= 2.0 ** 31:
        raise ValueError('index conversion out of range')
    return int(x) & 0xffffffff


def inline_int(x: float) -> int:
    """The inline float -> int sequence of 321098/321838/2d4618 (detail_runtime.ee_floor): floor for every input except
    normalized negative values in (-1, 0), which give 0."""
    x = f32(x)
    if not math.isfinite(x) or abs(x) >= 2.0 ** 31:
        raise ValueError('inline conversion out of range')
    b = bits(x)
    exponent = ((b & 0x7fffffff) >> 23) - 127
    sign = -1 if b >> 31 else 0
    mantissa = b & 0x7fffff
    magnitude = (((mantissa | 0x800000) << 8) & 0xffffffff) >> ((31 - exponent) & 31)
    value = (magnitude if exponent >= 0 else 0) ^ sign
    if ((mantissa << 8) & ((1 << ((31 - max(exponent, 0)) & 31)) - 1)) == 0:
        value -= sign
    return value


# The EE literals are float32 (lui/ori or .rodata words): every constant is rounded before use.
K = {name: f32(value) for name, value in dict(
    f01=0.1, f005=0.05, f001=0.01, f002=0.02, f06=0.6, f05=0.5, speed=1.61368, a1=1.13, b1=1.78, a2=2.19, b2=2.93,
    four=4.0, six=6.0).items()}


def L(index: int) -> float:
    return TABLE[index & 0xfff]


def phase(counter: int) -> float:
    return f32(f32(float(counter & 0xffffffff)) / 150.0)


def waves(x: float, z: float, t: float, frequency: float):
    """The shared A/B perturbation of 320c78 (frequency 0.1) and 321098 (frequency 0.05)."""
    frequency = f32(frequency)
    a = f32(f32(f32(x) * frequency) + f32(t * K['speed']))
    b = f32(f32(f32(z) * frequency) + f32(t))
    b178 = f32(b * K['b1'])
    A = f32(L(trunc_index(f32(f32(a * K['a1']) * INDEX_SCALE))) - L(trunc_index(f32(b178 * INDEX_SCALE)) + 0x400))
    B1 = L(trunc_index(f32(f32(a * K['a2']) * INDEX_SCALE)) + 0x400)
    B2 = L(trunc_index(f32(f32(b * K['b2']) * INDEX_SCALE)))
    return A, f32(B1 + B2)


# Camera rows of 42dc00 as 320c78 reads them: (dc00, dc04), (dc10, dc14), (dc20, dc24). Water (321098) uses the fixed
# rows (1, 0), (0, 1), (0, 0) instead.
WATER_BASIS = ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))


def puddle_uv(position, normal, t, basis):
    """320c78: (primary u, v, secondary u, v) of one puddle vertex. basis = PS2 camera rows (x right, y down)."""
    x, y, z = (f32(v) for v in position)
    nx, ny, nz = (f32(v) for v in normal)
    A, B = waves(x, z, t, K['f01'])
    u0 = f32(f32(x * K['f005']) + f32(A * K['f005']))
    v0 = f32(f32(z * K['f005']) + f32(B * K['f005']))
    px = f32(nx + f32(A * K['f06']))
    pz = f32(nz + f32(B * K['f06']))
    (m00, m01), (m10, m11), (m20, m21) = ((f32(a), f32(b)) for a, b in basis)
    v1 = f32(f32(f32(f32(f32(px * m01) + f32(ny * m11)) + f32(pz * m21)) * -K['f05']) + K['f05'])
    v1 = f32(v1 + f32(z * K['f002']))
    u1 = f32(f32(f32(f32(f32(px * m00) + f32(ny * m10)) + f32(pz * m20)) * K['f05']) + K['f05'])
    u1 = f32(u1 + f32(x * K['f002']))
    return u0, v0, u1, v1


def water_uv(position, normal, t):
    """321098 before the rebase: (primary u, v, secondary u, v)."""
    x, y, z = (f32(v) for v in position)
    nx, ny, nz = (f32(v) for v in normal)
    A, B = waves(x, z, t, K['f005'])
    u0 = f32(f32(x * K['f001']) + f32(A * K['f005']))
    v0 = f32(f32(z * K['f001']) + f32(B * K['f005']))
    px = f32(nx + f32(A * K['f06']))
    pz = f32(nz + f32(B * K['f06']))
    v1 = f32(f32(f32(f32(f32(f32(px * 0.0) + f32(ny * 1.0)) + f32(pz * 0.0)) * -K['f05']) + K['f05']) + f32(z * K['f002']))
    u1 = f32(f32(f32(f32(f32(f32(px * 1.0) + f32(ny * 0.0)) + f32(pz * 0.0)) * K['f05']) + K['f05']) + f32(x * K['f002']))
    return u0, v0, u1, v1


def water_mesh_uv(vertices, t):
    """321098 over one mesh: per-vertex UV, then each component minus the inline-int of its mean (float32 running sum in
    vertex order, divided by the vertex count)."""
    uvs = [water_uv(p, n, t) for p, n in vertices]
    if not uvs:
        return []
    sums = [0.0, 0.0, 0.0, 0.0]
    for uv in uvs:
        sums = [f32(s + c) for s, c in zip(sums, uv)]
    count = f32(float(len(uvs)))
    shift = [f32(float(inline_int(f32(s / count)))) for s in sums]
    return [tuple(f32(c - s) for c, s in zip(uv, shift)) for uv in uvs]


def waterfall_v(source_y, first_y, t):
    """321838: (primary V, secondary V); U of both layers = the cached primary U (the authored UV)."""
    doubled = f32(t + t)
    quadrupled = f32(t * K['four'])
    base = f32(float(inline_int(f32(f32(f32(first_y) * K['f005']) + K['six']))))
    y = f32(f32(source_y) * K['f005'])
    primary = f32(f32(y + f32(doubled - f32(float(inline_int(doubled))))) - base)
    secondary = f32(f32(y + f32(quadrupled - f32(float(inline_int(quadrupled))))) - base)
    return primary, secondary


# ---- 320938: puddle vertex RGBA from the 2d4618 spatial ground query ------------------------------------------------

def weight_byte(gap: float) -> int:
    """clamp(int((1 - 1/(2*gap + 1)) * 255), 2, 254); all four channels get the same value (320938)."""
    g = f32(abs(f32(gap)))
    v = int(f32(f32(1.0 - f32(1.0 / f32(f32(g + g) + 1.0))) * 255.0))
    return max(2, min(254, v))


def ground_hits(landscape, x, z):
    """2d4618: the triangles of the grid cell under (x, z) whose XZ projection contains the point (the original edge tests),
    intersected with the vertical line; (tri, material, y), sorted by t = -y ascending (insertion sort on +0x1c)."""
    pitch, _, _, minx, _, minz = landscape.parameters[:6]
    ix = max(0, min(inline_int(f32(f32(f32(x) - minx) / pitch)), landscape.nx - 1))
    iz = max(0, min(inline_int(f32(f32(f32(z) - minz) / pitch)), landscape.nz - 1))
    hits = []
    x, z = f32(x), f32(z)
    for ref in landscape.cells[iz * landscape.nx + ix]:
        tri, material = ref & 0xffff, ref >> 16
        a, b, c = (landscape.position(i) for i in landscape.triangles[tri * 3:tri * 3 + 3])
        ax, az, bx, bz, cx, cz = (f32(v) for v in (a[0], a[2], b[0], b[2], c[0], c[2]))
        if not f32(f32(bz - az) * f32(ax - x)) <= f32(f32(bx - ax) * f32(az - z)):
            continue
        if not f32(f32(cz - bz) * f32(bx - x)) <= f32(f32(cx - bx) * f32(bz - z)):
            continue
        if not f32(f32(az - cz) * f32(cx - x)) <= f32(f32(ax - cx) * f32(cz - z)):
            continue
        e1 = [f32(f32(b[i]) - f32(a[i])) for i in range(3)]
        e2 = [f32(f32(c[i]) - f32(a[i])) for i in range(3)]
        n = [f32(f32(e1[1] * e2[2]) - f32(e1[2] * e2[1])), f32(f32(e1[2] * e2[0]) - f32(e1[0] * e2[2])),
             f32(f32(e1[0] * e2[1]) - f32(e1[1] * e2[0]))]
        length = f32(math.sqrt(f32(f32(f32(n[0] * n[0]) + f32(n[1] * n[1])) + f32(n[2] * n[2]))))
        if not length:
            continue
        n = [f32(v / length) for v in n]
        d = f32(-f32(f32(f32(n[0] * f32(a[0])) + f32(n[1] * f32(a[1]))) + f32(n[2] * f32(a[2]))))
        down = f32(-n[1])
        if -1.1920929e-06 <= down <= 1.1920929e-06:
            continue                                    # vertical triangle: no hit record
        t = f32(-f32(f32(f32(x * n[0]) + f32(z * n[2])) + d) / down)
        hits.append((tri, material, f32(-t), t))
    hits.sort(key=lambda h: h[3])                       # stable, ascending t (the insertion sort keeps equal keys in order)
    return [(tri, material, y) for tri, material, y, _ in hits]


def puddle_rgba(landscape, position):
    """320938 for one vertex: 254 unless there are at least two hits; then the gap to the last hit whose material has no
    "water" substring (or the first hit if every hit is water)."""
    hits = ground_hits(landscape, position[0], position[2])
    if len(hits) < 2:
        return 254
    chosen = hits[0]
    for hit in hits:
        if 'water' not in landscape.materials[hit[1]]:
            chosen = hit
    return weight_byte(f32(f32(position[1]) - chosen[2]))
