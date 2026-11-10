"""PS2 physical objects (hay bales, tumbleweeds, checkpoint barrels) for the optional Renderer module.

These objects exist only through the Renderer's RigidProps mechanism (owner,
2026-11-10: they do not run natively in the PC game). The asset format is
PS2RGD02 (``master_rallye.course_rigid`` reader, written by
``pc-port/tools/prepare_rigid_props.py``). :func:`write_rigid_asset` is the
exact inverse of the reader; :func:`with_course` appends a Studio course and
its placed props to an existing asset while keeping every other byte meaning.

Packaging rule: a course never depends on this module. The build writes the
asset to ``optional/`` with a manifest. The accepted Renderer loads only the
asset whose SHA-256 is compiled in (``rigid_props.cpp``: ``digest ==
kRigidPropsArtifactSha``), so a Studio asset is used by a Renderer build that
accepts it; without that the course runs normally without these props.
"""
from __future__ import annotations

import hashlib
import math
import struct
from pathlib import Path

from ..course_rigid import COURSE, MODEL, PROP, read_rigid_asset, text

HEADER = struct.Struct("<8s9I")
FLAG_SHADOW = 1
FLAG_CHECKPOINT = 2


def _fixed(value: str, size: int) -> bytes:
    raw = value.encode("ascii")
    if len(raw) >= size:
        raise ValueError(f"{value!r} does not fit {size} bytes")
    return raw + b"\0" * (size - len(raw))


def write_rigid_asset(asset: dict) -> bytes:
    shadow = asset.get("shadow_texture", 0)
    out = bytearray(HEADER.pack(b"PS2RGD02", 2, len(asset["textures"]), len(asset["models"]), len(asset["vertices"]),
                                len(asset["points"]), len(asset["planes"]), len(asset["courses"]), len(asset["props"]),
                                shadow))
    for w, h, data in asset["textures"]:
        out += struct.pack("<2I", w, h) + data
    for m in asset["models"]:
        out += MODEL.pack(*m)
    for v in asset["vertices"]:
        out += struct.pack("<3fI2f", *v)
    for n in asset["normals"]:
        out += struct.pack("<3f", *n)
    for p in asset["points"]:
        out += struct.pack("<3f", *p)
    for q in asset["planes"]:
        out += struct.pack("<4f", *q)
    for c in asset["courses"]:
        out += COURSE.pack(*c)
    for p in asset["props"]:
        out += PROP.pack(*p)
    return bytes(out)


def read_asset_with_shadow(path: Path) -> dict:
    asset = read_rigid_asset(path)
    asset["shadow_texture"] = struct.unpack_from("<I", Path(path).read_bytes(), 40)[0]
    return asset


def model_names(asset: dict) -> list[str]:
    return [text(m[0]) for m in asset["models"]]


def prop_record(name: str, model: int, position, heading_deg: float, *, mass: float, moi, trigger: float,
                shadow: bool = True, checkpoint: bool = False):
    h = math.radians(heading_deg)
    fx, fz = math.sin(h), math.cos(h)
    rows = ((fz, 0.0, -fx), (0.0, 1.0, 0.0), (fx, 0.0, fz), tuple(position))
    flags = (FLAG_SHADOW if shadow else 0) | (FLAG_CHECKPOINT if checkpoint else 0)
    return (_fixed(name, 32), model, flags, float(mass), *map(float, moi), float(trigger),
            *(v for row in rows for v in row))


def with_course(asset: dict, *, course_id: str, dx_path: str, dx_bytes: bytes, props: list) -> dict:
    """``course_id`` is the Renderer course id ``RaceTest/<scene>``."""
    """Copy of ``asset`` with one more course (replacing a previous entry of the same id)."""
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in asset.items()}
    courses, all_props = [], []
    for c in asset["courses"]:
        first, count = c[3], c[4]
        if text(c[0]) == course_id:
            continue
        courses.append((c[0], c[1], c[2], len(all_props), count))
        all_props.extend(asset["props"][first:first + count])
    if props:
        if len(props) > 32:
            raise ValueError("the Renderer simulates at most 32 physical objects per course "
                             "(rigid_props.hpp kRigidMaximumPropsPerCourse)")
        # Retail DX field: a Studio course has no Retail counterpart. The Renderer admits a course whose loose
        # DX differs from this digest ("ps2_course_package"), so an all-zero digest always admits it.
        courses.append((_fixed(course_id, 48), _fixed(dx_path, 64), bytes(32), len(all_props), len(props)))
        all_props.extend(props)
    if len(courses) > 64:
        raise ValueError("the PS2RGD02 asset holds at most 64 courses")
    out["courses"], out["props"] = courses, all_props
    return out


def build_optional_asset(project, base_asset: Path, dx_rel_path: str, dx_bytes: bytes, texture_payloads: dict | None = None):
    """(asset bytes, manifest) for ``project.extras['ps2_props']`` / ``['ps2_models']``, or None.

    A prop names a model: a family of the base asset (``haybale``, ``tumblweed``, ``checkpoint``) or a new
    Studio model from ``ps2_models`` (vertices, normals, texture key, material) appended to the asset.
    """
    items = project.extras.get("ps2_props") or []
    if not items:
        return None
    asset = read_asset_with_shadow(base_asset)
    added = []
    for key, model in (project.extras.get("ps2_models") or {}).items():
        feed = (texture_payloads or {}).get(model.get("texture"))
        if feed is None:
            from .textures import solid_texture
            feed = solid_texture((180, 180, 180, 255))
        add_model(asset, name=key[:15], vertices=[tuple(v) for v in model["vertices"]],
                  normals=[tuple(n) for n in model["normals"]], texture_feed=feed,
                  material=model.get("material", "object"))
        added.append(key[:15])
    names = model_names(asset)
    props = []
    for i, item in enumerate(items):
        model = item["model"][:15]
        if model not in names:
            raise ValueError(f"physical object {i}: unknown model {model!r} (available: {names})")
        props.append(prop_record(f"Studio{i}", names.index(model), item["position"], item.get("heading", 0.0),
                                 mass=item.get("mass", 300.0), moi=item.get("moi", (150.0, 150.0, 150.0)),
                                 trigger=item.get("trigger", 5.0), shadow=item.get("shadow", True),
                                 checkpoint=model == "checkpoint"))
    new = with_course(asset, course_id=f"RaceTest/{project.course_key()}", dx_path=dx_rel_path, dx_bytes=dx_bytes,
                      props=props)
    data = write_rigid_asset(new)
    read_back = read_rigid_asset_bytes(data)
    manifest = {"module": "Renderer RigidProps (optional)", "asset_sha256": hashlib.sha256(data).hexdigest(),
                "base_asset_sha256": hashlib.sha256(Path(base_asset).read_bytes()).hexdigest(),
                "course": project.course_key(), "props": len(props), "models": names, "new_models": added,
                "reread": {"courses": len(read_back["courses"]), "props": len(read_back["props"])}}
    return data, manifest


def read_rigid_asset_bytes(data: bytes) -> dict:
    import os
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".ps2rgd")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return read_rigid_asset(path)
    finally:
        os.unlink(path)


MATERIALS = {"object": 0, "treeblend": 1, "metal": 2}   # renderer restitution/friction/rolling per material
MAX_MODELS, MAX_TEXTURES = 16, 16


def hull_of(points):
    """Convex hull points + outward planes (n.p + d <= 0 inside) of model-space points."""
    from .collision import convex_hull
    tris = convex_hull(points)
    if not tris:
        raise ValueError("a physical object needs a 3-D volume (at least 4 non-coplanar points)")
    pts, planes = [], []
    for tri in tris:
        for p in tri:
            if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > 1e-5 for q in pts):
                pts.append(tuple(p))
        a, b, c = tri
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        length = math.sqrt(sum(x * x for x in n))
        n = tuple(x / length for x in n)
        d = -(n[0] * a[0] + n[1] * a[1] + n[2] * a[2])
        if all(abs(n[0] - q[0]) + abs(n[1] - q[1]) + abs(n[2] - q[2]) + abs(d - q[3]) > 1e-4 for q in planes):
            planes.append((*n, d))
    return pts[:4096], planes[:4096]


def add_model(asset: dict, *, name: str, vertices, normals, texture_feed: bytes, material: str = "object") -> int:
    """Append a new physical-object model; returns its model index.

    ``vertices``: model-space triangle list ``(x, y, z, rgba_u32, u, v)`` (3 per triangle, Y up, origin = pivot);
    ``texture_feed``: a FEED texture (its BGRA payload is what the Renderer uploads).
    """
    names = model_names(asset)
    if name in names:
        return names.index(name)
    if len(asset["models"]) >= MAX_MODELS:
        raise ValueError(f"the asset already holds {MAX_MODELS} models")
    if not vertices or len(vertices) % 3:
        raise ValueError("a model needs a triangle list")
    if len(asset["vertices"]) + len(vertices) > 65536:
        raise ValueError("the asset vertex budget (65536) is exceeded")
    w, h = struct.unpack_from("<2I", texture_feed, 12)
    payload = texture_feed[20:]
    texture = next((i for i, t in enumerate(asset["textures"]) if t[2] == payload), None)
    if texture is None:
        if len(asset["textures"]) >= MAX_TEXTURES:
            raise ValueError(f"the asset already holds {MAX_TEXTURES} textures")
        if w > 1024 or h > 1024:
            raise ValueError("physical-object textures are at most 1024 x 1024")
        asset["textures"].append((w, h, payload))
        texture = len(asset["textures"]) - 1
    pts = [v[:3] for v in vertices]
    hull_points, hull_planes = hull_of(pts)
    first_vertex = len(asset["vertices"])
    asset["vertices"].extend(tuple(v) for v in vertices)
    asset["normals"].extend(tuple(n) for n in normals)
    first_point, first_plane = len(asset["points"]), len(asset["planes"])
    asset["points"].extend(hull_points)
    asset["planes"].extend(hull_planes)
    radius = max(math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) for p in pts)
    hull_radius = max(math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) for p in hull_points)
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]
    asset["models"].append((_fixed(name, 16), MATERIALS[material], 1, texture, first_vertex, len(vertices), 0, 0, 0,
                            float(radius), first_point, len(hull_points), first_plane, len(hull_planes),
                            float(hull_radius), -1, *lo, *hi))
    return len(asset["models"]) - 1


def box_inertia(mass: float, size) -> tuple[float, float, float]:
    """Solid-box moments of inertia about the model axes (x, y, z)."""
    x, y, z = size
    return (mass * (y * y + z * z) / 12.0, mass * (x * x + z * z) / 12.0, mass * (x * x + y * y) / 12.0)
