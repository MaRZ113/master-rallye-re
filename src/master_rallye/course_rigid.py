"""Strict inspect-only PS2RGD02 reader shared with Course Studio.

Layout: pc-port/tools/prepare_rigid_props.py and renderer/rigid_props.cpp.
No renderer dependency and no asset hash whitelist.
"""
from __future__ import annotations
import math
import struct
from pathlib import Path

MODEL = struct.Struct('<16s2I6If4Ifi6f')
PROP = struct.Struct('<32s2I5f12f')
COURSE = struct.Struct('<48s64s32s2I')


def read_rigid_asset(path):
    raw = Path(path).read_bytes()
    offset = 0
    def read(fmt):
        nonlocal offset
        codec = fmt if isinstance(fmt, struct.Struct) else struct.Struct(fmt)
        if offset + codec.size > len(raw): raise ValueError('Truncated PS2RGD02 asset')
        result = codec.unpack_from(raw, offset); offset += codec.size
        if any(isinstance(x, float) and not math.isfinite(x) for x in result):
            raise ValueError('Non-finite PS2RGD02 data')
        return result
    magic, version, nt, nm, nv, nh, np, nc, no, shadow = read('<8s9I')
    if magic != b'PS2RGD02' or version != 2 or not (0 < nt <= 16 and 0 < nm <= 16 and 0 < nv <= 65536 and 0 < nh <= 4096 and 0 < np <= 4096 and 0 < nc <= 64 and 0 < no <= 1024 and shadow < nt):
        raise ValueError('Unsupported PS2RGD02 header')
    textures = []
    for _ in range(nt):
        w, h = read('<2I')
        if not 0 < w <= 1024 or not 0 < h <= 1024 or w & (w-1) or h & (h-1) or offset + w*h*4 > len(raw):
            raise ValueError('Invalid rigid texture')
        textures.append((w, h, raw[offset:offset+w*h*4])); offset += w*h*4
    models = [read(MODEL) for _ in range(nm)]
    vertices = [read('<3fI2f') for _ in range(nv)]
    normals = [read('<3f') for _ in range(nv)]
    points = [read('<3f') for _ in range(nh)]
    planes = [read('<4f') for _ in range(np)]
    courses = [read(COURSE) for _ in range(nc)]
    props = [read(PROP) for _ in range(no)]
    if offset != len(raw): raise ValueError('Trailing PS2RGD02 bytes')
    for model in models:
        if model[1] > 2 or not 1 <= model[2] <= 2: raise ValueError('Unsupported rigid material/draws')
        for draw in range(model[2]):
            texture, first, count = model[3+draw*3:6+draw*3]
            if texture >= nt or not count or count % 3 or first + count > nv:
                raise ValueError('Invalid rigid visual span')
        first, count, first_plane, count_plane = model[10:14]
        if count < 4 or count_plane < 4 or first + count > nh or first_plane + count_plane > np:
            raise ValueError('Invalid rigid hull span')
        for plane in planes[first_plane:first_plane+count_plane]:
            if abs(math.sqrt(sum(x*x for x in plane[:3])) - 1) > 1e-3:
                raise ValueError('Invalid rigid hull normal')
            if any(sum(plane[k]*p[k] for k in range(3))+plane[3] > 1e-3 for p in points[first:first+count]):
                raise ValueError('Non-convex rigid hull')
    first = 0
    for course in courses:
        if course[3] != first or not course[4] or first + course[4] > no:
            raise ValueError('Invalid rigid course span')
        first += course[4]
    if first != no: raise ValueError('Unowned rigid props')
    for prop in props:
        if prop[1] >= nm or prop[2] > 3 or prop[3] <= 0 or any(x <= 0 for x in prop[4:7]):
            raise ValueError('Invalid rigid body')
    return dict(models=models, vertices=vertices, normals=normals, points=points, planes=planes,
                courses=courses, props=props, textures=textures, source=str(Path(path).resolve()))


def text(raw):
    return raw.split(b'\0', 1)[0].decode('ascii')
