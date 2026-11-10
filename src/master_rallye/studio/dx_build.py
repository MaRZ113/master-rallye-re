"""Offline course DX writer (render records, tag100, tag1339, tag1400) for any topology.

The layout and every per-record field reproduce the Retail cooker contract
measured on ``invspaingx.dx`` (cooked by Retail ``MRallye.exe`` from a GXM we
wrote) and on Retail course records:

* header ``0xD00D, 135, 1337, vertex count``; positions, normals, BGRA colours,
  two UV sets (base, noise), u16 local indices; draw envelope ``(1, n)`` of
  tag-2 records, one per material (split at 65 536 vertices);
* render winding = authoring ``(b, a, c)``; noise UV = ``(x, z)/37 + 0.5`` with
  integer shifts per triangle; vertex colours are prelit (baked) lighting;
* tag100 = solid-leaf collision BSP (:mod:`master_rallye.course_bsp`) from
  terrain + collision meshes (+ an optional map-edge skirt), plane code =
  land-database record index for terrain, unique indices after it otherwise;
* tag1339 = render AABB centre + farthest-vertex radius + AABB;
* tag1400 = land surface database: terrain and water triangles in authoring
  order wound ``(c, b, a)``, plane ``n,d`` of that winding, material-name string
  table (the physics reads ``$surfacetype``), 20-unit grid of record lists in
  z-major order, membership by triangle AABB.
"""
from __future__ import annotations

import math
import struct
import time
from dataclasses import dataclass, field

from ..course_bsp import Leaf, Node, build_solid_bsp, close_land, encode_tag100, polygon
from ..course_gxm_writer import GxmGroup, GxmMaterial, GxmMesh, GxmTextureSlot, encode_txt
from .materials import NOISE_UV_SCALE, encode_record_fields
from .model import LAND_ROLES, ROLE_COLLISION, ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER, CourseProject, Mesh

DX_MAGIC = 0xD00D
DX_REVISION = 135
DX_WORD8 = 1337
MAX_LOCAL_VERTICES = 65536
LAND_CELL = 20.0
TAG1339 = 1339
TAG1400 = 1400
DEGENERATE_AREA = 1e-7


class BuildError(ValueError):
    pass


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _norm(v):
    length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / length, v[1] / length, v[2] / length) if length > 1e-12 else (0.0, 1.0, 0.0)


def triangle_normal(a, b, c):
    return _cross(_sub(b, a), _sub(c, a))


def triangle_area(a, b, c) -> float:
    n = triangle_normal(a, b, c)
    return 0.5 * math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])


@dataclass
class SourceTriangle:
    mesh: Mesh
    index: int
    points: tuple
    material: str


@dataclass
class CourseDxBuild:
    dx: bytes
    txt: str
    report: dict
    land_sources: list = field(default_factory=list)     # (mesh id, triangle index) per land record
    bsp_tree: object = None
    texture_keys: list = field(default_factory=list)


def _smooth_normals(mesh: Mesh) -> list:
    """Per-vertex area-weighted normals (game space) for meshes authored without corner normals."""
    acc = [[0.0, 0.0, 0.0] for _ in range(mesh.vertex_count)]
    for t in range(mesh.triangle_count):
        a, b, c = mesh.triangle(t)
        n = triangle_normal(mesh.vertex(a), mesh.vertex(b), mesh.vertex(c))
        for i in (a, b, c):
            acc[i][0] += n[0]; acc[i][1] += n[1]; acc[i][2] += n[2]
    return [_norm(v) for v in acc]


def _bake(normal, light, base=(255, 255, 255, 255)):
    lx, ly, lz = _norm(light)
    shade = 0.55 + 0.45 * max(0.0, normal[0] * lx + normal[1] * ly + normal[2] * lz)
    return (min(255, int(base[0] * shade)), min(255, int(base[1] * shade)), min(255, int(base[2] * shade)), base[3])


class _RenderBank:
    def __init__(self):
        self.positions, self.normals, self.colors, self.uv0, self.uv1, self.indices = [], [], [], [], [], []
        self.records = []

    def add_record(self, material, fields, slots, corners):
        """``corners``: list of (pos, normal, color, uv0, uv1) in render winding, 3 per triangle."""
        start = 0
        while start < len(corners):
            lookup, local = {}, []
            base = len(self.positions)
            index_start = len(self.indices)
            pos = start
            while pos < len(corners):
                tri = corners[pos:pos + 3]
                new = sum(1 for c in tri if self._key(c) not in lookup)
                if len(lookup) + new > MAX_LOCAL_VERTICES:
                    break
                for c in tri:
                    key = self._key(c)
                    slot = lookup.get(key)
                    if slot is None:
                        slot = len(lookup)
                        lookup[key] = slot
                        p, n, col, t0, t1 = c
                        self.positions.append(p); self.normals.append(n); self.colors.append(col)
                        self.uv0.append(t0); self.uv1.append(t1)
                    local.append(slot)
                pos += 3
            if pos == start:
                raise BuildError("a single triangle exceeds the local vertex limit")
            self.indices.extend(local)
            self.records.append({"material": material, "fields": fields, "slots": slots, "vertex_base": base,
                                 "local_vertex_max": len(lookup) - 1, "index_start": index_start,
                                 "index_count": len(local)})
            start = pos

    @staticmethod
    def _key(c):
        p, n, col, t0, t1 = c
        return (round(p[0], 5), round(p[1], 5), round(p[2], 5), round(n[0], 4), round(n[1], 4), round(n[2], 4),
                col, round(t0[0], 6), round(t0[1], 6), round(t1[0], 5), round(t1[1], 5))


def _encode_record(rec) -> bytes:
    f = rec["fields"]
    core = struct.pack("<5I2If4sI", 2, rec["vertex_base"], rec["local_vertex_max"], rec["index_start"],
                       rec["index_count"], f.address, f.effect, f.mip, f.flags, f.slot_mask)
    out = bytearray(core)
    out += struct.pack("<I", 3)
    for name in rec["slots"]:
        text = (name or "Null").encode("ascii")
        out += struct.pack("<I", len(text)) + text
    out += struct.pack("<I", 0)
    return bytes(out)


def _land_database(records, strings):
    """``records``: list of (v0, v1, v2, string index) in stored (c, b, a) winding."""
    if not records:
        raise BuildError("the course has no terrain: the land surface database would be empty")
    xs = [p[0] for r in records for p in r[:3]]
    ys = [p[1] for r in records for p in r[:3]]
    zs = [p[2] for r in records for p in r[:3]]
    lo, hi = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
    d0 = int(math.floor((hi[0] - lo[0]) / LAND_CELL)) + 1
    d1 = int(math.floor((hi[2] - lo[2]) / LAND_CELL)) + 1
    cells = [[] for _ in range(d0 * d1)]
    body = bytearray()
    for index, (v0, v1, v2, sref) in enumerate(records):
        i0 = int((min(v0[0], v1[0], v2[0]) - lo[0]) // LAND_CELL)
        i1 = int((max(v0[0], v1[0], v2[0]) - lo[0]) // LAND_CELL)
        j0 = int((min(v0[2], v1[2], v2[2]) - lo[2]) // LAND_CELL)
        j1 = int((max(v0[2], v1[2], v2[2]) - lo[2]) // LAND_CELL)
        for j in range(max(j0, 0), min(j1, d1 - 1) + 1):
            row = j * d0
            for i in range(max(i0, 0), min(i1, d0 - 1) + 1):
                cells[row + i].append(index)
        n = _norm(triangle_normal(v0, v1, v2))
        d = -(n[0] * v0[0] + n[1] * v0[1] + n[2] * v0[2])
        body += struct.pack("<9fI4f", *v0, *v1, *v2, sref, *n, d)
    out = bytearray(struct.pack("<IfII3f3f", TAG1400, LAND_CELL, d0, d1, *lo, *hi))
    for cell in cells:
        out += struct.pack(f"<I{len(cell)}I", len(cell), *cell)
    out += struct.pack("<I", len(strings))
    for text in strings:
        raw = text.encode("latin-1")
        out += struct.pack("<I", len(raw)) + raw
    out += struct.pack("<I", len(records)) + body
    stats = {"records": len(records), "grid": [d0, d1], "cell_entries": sum(len(c) for c in cells),
             "max_cell_entries": max((len(c) for c in cells), default=0), "strings": len(strings),
             "min": [round(v, 3) for v in lo], "max": [round(v, 3) for v in hi]}
    return bytes(out), stats


def _bounds1339(positions):
    xs, ys, zs = [p[0] for p in positions], [p[1] for p in positions], [p[2] for p in positions]
    lo, hi = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
    centre = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
    radius = max(math.dist(centre, p) for p in positions)
    return struct.pack("<I3ff3f3f", TAG1339, *centre, radius, *lo, *hi), {"centre": centre, "radius": radius}


def collision_polygons(project: CourseProject, *, skirt: bool = True, exclude=(), extra_objects=()):
    """Polygons for the collision BSP and their provenance (mesh id, triangle) per plane code.

    Land faces keep code = land-database record index. Collision objects are
    united with the terrain first (:mod:`.bsp_union`): buried parts of objects
    and terrain inside closed objects are clipped away, so a building sunk
    into the ground is solid inside.
    """
    from .bsp_union import union_polygons
    provenance = []
    land_polys, land_tris = [], []
    code = 0
    for mesh in project.meshes_with(*LAND_ROLES):
        for t in range(mesh.triangle_count):
            a, b, c = mesh.triangle_points(t)
            if triangle_area(a, b, c) < DEGENERATE_AREA:
                continue
            poly = polygon([a, b, c], triangle_normal(a, b, c), code)
            if poly is not None:
                land_polys.append(poly)
            land_tris.append(([a, b, c], code))
            provenance.append((mesh.id, t))
            code += 1
    land_count = code
    objects = []          # (polygons, closed) per connected piece of every collision mesh
    for mesh in project.meshes_with(ROLE_COLLISION):
        if mesh.id in exclude:
            continue
        parent = list(range(mesh.vertex_count))

        def find(v):
            while parent[v] != v:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v
        for t in range(mesh.triangle_count):
            i0, i1, i2 = mesh.triangle(t)
            r0 = find(i0)
            parent[find(i1)] = r0
            parent[find(i2)] = r0
        pieces: dict = {}
        for t in range(mesh.triangle_count):
            ids = mesh.triangle(t)
            a, b, c = mesh.triangle_points(t)
            if triangle_area(a, b, c) < DEGENERATE_AREA:
                continue
            poly = polygon([a, b, c], triangle_normal(a, b, c), code)
            if poly is None:
                continue
            group = pieces.setdefault(find(ids[0]), ([], {}))
            group[0].append(poly)
            for e in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
                k = (min(e), max(e))
                group[1][k] = group[1].get(k, 0) + 1
            provenance.append((mesh.id, t))
            code += 1
        native = mesh.source.startswith("retail-bsp")
        for polys, edges in pieces.values():
            objects.append((polys, bool(edges) and all(n == 2 for n in edges.values()), not native))
    for tris in extra_objects:      # closed islands given as point triples (moved native cells)
        polys, edges = [], {}
        keyed = {}
        for tri in tris:
            poly = polygon(list(tri), triangle_normal(*tri), code)
            if poly is None or triangle_area(*tri) < DEGENERATE_AREA:
                continue
            polys.append(poly)
            code += 1
            ks = [keyed.setdefault((round(p[0], 4), round(p[1], 4), round(p[2], 4)), len(keyed)) for p in tri]
            for e in ((ks[0], ks[1]), (ks[1], ks[2]), (ks[2], ks[0])):
                k = (min(e), max(e))
                edges[k] = edges.get(k, 0) + 1
        if polys:
            objects.append((polys, all(n == 2 for n in edges.values()), True))
    stats = {"terrain_polygons": land_count, "collision_polygons": code - land_count, "skirt": None}
    walls_polys = []
    if skirt and land_tris:
        walls, info = close_land([pts for pts, _ in land_tris])
        for points, normal, local in walls:
            poly = polygon(points, normal, land_tris[local][1])
            if poly is not None:
                walls_polys.append(poly)
        info = {k: v for k, v in info.items() if k != "detail"}
        info["polygons"] = len(walls_polys)
        stats["skirt"] = info
    heights = None
    if objects and land_tris:
        from .collision import HeightField
        hf = HeightField([pts for pts, _ in land_tris])
        heights = lambda x, z: hf.ground(x, z)
    polys, ustats = union_polygons(land_polys, walls_polys, objects, heights=heights)
    stats["union"] = ustats
    return polys, provenance, stats


def tree_stats(root) -> dict:
    nodes = leaves = solid = depth_max = 0
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        depth_max = max(depth_max, depth)
        if isinstance(node, Leaf):
            leaves += 1
            solid += node.solid
        else:
            nodes += 1
            stack.append((node.back, depth + 1))
            stack.append((node.front, depth + 1))
    return {"planes": nodes, "leaves": leaves, "solid_leaves": solid, "max_depth": depth_max}


def build_course_dx(project: CourseProject, *, progress=None, bsp_tree=None) -> CourseDxBuild:
    """Return the complete DX + TXT for ``project`` (``bsp_tree`` reuses a previous collision build)."""
    began = time.time()
    say = progress or (lambda *_: None)
    light = project.environment.vertex_light
    report = {"dropped_degenerate": 0, "meshes": {}}
    materials = project.materials
    for key, mat in materials.items():
        problems = mat.validate()
        if problems:
            raise BuildError(f"material {key}: {'; '.join(problems)}")

    # ------------------------------------------------------------ render corners per material
    say("render", 0.0)
    per_material: dict[str, list] = {}
    order: list[str] = []
    for mesh in project.meshes_with(ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER):
        problems = mesh.validate_arrays()
        if problems:
            raise BuildError(f"mesh {mesh.name}: {'; '.join(problems)}")
        vertex_normals = None if mesh.normals is not None else _smooth_normals(mesh)
        drawn = 0
        for t in range(mesh.triangle_count):
            key = mesh.material_of(t)
            if key not in materials:
                raise BuildError(f"mesh {mesh.name} uses undefined material {key!r}")
            mat = materials[key]
            ids = mesh.triangle(t)
            pts = [mesh.vertex(i) for i in ids]
            if triangle_area(*pts) < DEGENERATE_AREA:
                report["dropped_degenerate"] += 1
                continue
            noise = mat.has_noise()
            if noise:
                cx = (pts[0][0] + pts[1][0] + pts[2][0]) / 3 * NOISE_UV_SCALE
                cz = (pts[0][2] + pts[1][2] + pts[2][2]) / 3 * NOISE_UV_SCALE
                sx, sz = 5.0 * math.floor(cx / 5.0), 5.0 * math.floor(cz / 5.0)
            corners = []
            for k in range(3):
                p = pts[k]
                if mesh.normals is not None:
                    n = _norm(tuple(mesh.normals[9 * t + 3 * k:9 * t + 3 * k + 3]))
                else:
                    n = vertex_normals[ids[k]]
                if mesh.colors is not None:
                    col = tuple(mesh.colors[12 * t + 4 * k:12 * t + 4 * k + 4])
                else:
                    col = _bake(n, light)
                uv = (mesh.uv[6 * t + 2 * k], mesh.uv[6 * t + 2 * k + 1]) if mesh.uv is not None else (0.0, 0.0)
                uv1 = (p[0] * NOISE_UV_SCALE + 0.5 - sx, p[2] * NOISE_UV_SCALE + 0.5 - sz) if noise else (0.0, 0.0)
                corners.append((p, n, col, uv, uv1))
            if key not in per_material:
                per_material[key] = []
                order.append(key)
            a, b, c = corners
            per_material[key].extend((b, a, c))   # Retail render winding
            drawn += 1
        report["meshes"][mesh.name] = {"role": mesh.role, "drawn_triangles": drawn}

    bank = _RenderBank()
    texture_keys: list[str] = []
    sortable = []
    for key in order:
        mat = materials[key]
        slots = mat.texture_slots()
        fields = encode_record_fields(shader=mat.shader, alpha=mat.alpha, clamp=mat.clamp, mip=mat.mip,
                                      has_secondary=slots[1] is not None, has_noise=slots[2] is not None,
                                      has_base=slots[0] is not None, scroll=bool(mat.scroll))
        sortable.append((fields.sort_class, order.index(key), key, fields, slots))
        for name in slots:
            if name and name not in texture_keys:
                texture_keys.append(name)
    for _, _, key, fields, slots in sorted(sortable):
        bank.add_record(key, fields, slots, per_material[key])
    if not bank.positions:
        raise BuildError("nothing to draw: add a terrain or visual mesh")
    say("render", 1.0)

    # ------------------------------------------------------------ land surface database
    strings: list[str] = []
    land_records, land_sources = [], []
    for mesh in project.meshes_with(*LAND_ROLES) + project.meshes_with(ROLE_WATER):
        for t in range(mesh.triangle_count):
            a, b, c = mesh.triangle_points(t)
            if triangle_area(a, b, c) < DEGENERATE_AREA:
                continue
            name = materials[mesh.material_of(t)].native_name()
            if name not in strings:
                strings.append(name)
            land_records.append((c, b, a, strings.index(name)))
            land_sources.append((mesh.id, t))
    # land (terrain + invisible ground) records first, in the same order as the BSP land codes
    tag1400, land_stats = _land_database(land_records, strings)
    say("surfaces", 1.0)

    # ------------------------------------------------------------ collision tree
    if bsp_tree is None:
        say("collision", 0.0)
        from .collision import build_tree
        bsp_tree, provenance, cstats = build_tree(project)
    else:
        cstats = tree_stats(bsp_tree)
    tag100 = encode_tag100(bsp_tree)
    cstats["tag100_bytes"] = len(tag100)
    say("collision", 1.0)

    # ------------------------------------------------------------ assemble
    tag1339, bounds = _bounds1339(bank.positions)
    n = len(bank.positions)
    out = bytearray(struct.pack("<4I", DX_MAGIC, DX_REVISION, DX_WORD8, n))
    out += b"".join(struct.pack("<3f", *p) for p in bank.positions)
    out += b"".join(struct.pack("<3f", *v) for v in bank.normals)
    out += b"".join(bytes((c[2], c[1], c[0], c[3])) for c in bank.colors)
    out += struct.pack("<I", 2)
    out += b"".join(struct.pack("<2f", *t) for t in bank.uv0)
    out += b"".join(struct.pack("<2f", *t) for t in bank.uv1)
    out += struct.pack("<I", len(bank.indices)) + struct.pack(f"<{len(bank.indices)}H", *bank.indices)
    out += struct.pack("<2I", 1, len(bank.records))
    for rec in bank.records:
        out += _encode_record(rec)
    out += tag100 + tag1339 + tag1400

    # ------------------------------------------------------------ TXT sidecar (Retail ships one per DX)
    gxm_materials = []
    names = []          # first use by the course geometry (independent of optional-module materials)
    for m in project.meshes:
        if m.role in (ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER, ROLE_COLLISION) or m.role in LAND_ROLES:
            for k in m.materials:
                if k not in names and k in materials:
                    names.append(k)
    for key in names:
        mat = materials[key]
        slots = mat.texture_slots()
        gxm_materials.append(GxmMaterial(mat.native_name(), [
            GxmTextureSlot(f"{s}.tga" if s else "Null", has_alpha=mat.alpha != "opaque",
                           uses_alpha=mat.alpha != "opaque") if s else GxmTextureSlot() for s in slots]))
    first = 0
    def group(role):
        nonlocal first
        nodes = []
        for mesh in project.meshes_with(role):
            nodes.append(GxmMesh(mesh.name.replace("[", "(").replace("]", ")"), first, mesh.triangle_count))
            first += mesh.triangle_count
        return nodes
    land = group(ROLE_TERRAIN)
    coll = group(ROLE_COLLISION)
    objects = group(ROLE_VISUAL)
    water = [GxmMesh(f"{m.name} $water $landdb", m.first, m.count) for m in group(ROLE_WATER)]
    tree = [GxmGroup("$autovsphere_300", [
        GxmGroup("$bsp", [GxmGroup("$draw $landdb", land), GxmGroup("$nodraw", coll)]),
        GxmGroup("$objects", objects), *water])]
    txt = encode_txt("Model", gxm_materials, tree)

    report.update({
        "vertices": n, "indices": len(bank.indices), "draw_records": len(bank.records),
        "records": [{"material": r["material"], "vertices": r["local_vertex_max"] + 1,
                     "triangles": r["index_count"] // 3, "textures": r["slots"]} for r in bank.records],
        "land_database": land_stats, "collision": cstats, "bounds": {"centre": [round(v, 3) for v in bounds["centre"]],
                                                                     "radius": round(bounds["radius"], 3)},
        "textures": texture_keys, "dx_bytes": len(out), "seconds": round(time.time() - began, 2),
    })
    return CourseDxBuild(bytes(out), txt, report, land_sources, bsp_tree, texture_keys)


def verify_course_dx(data: bytes, expected: CourseDxBuild | None = None) -> dict:
    """Re-read a written DX with the independent Retail-format parsers and check structural invariants."""
    from ..course_tag100 import parse_course_tag100_bytes
    from ..course_tag1400 import parse_course_tag1400_bytes
    from ..dx_course import parse_course_dx_bytes

    model = parse_course_dx_bytes(data, "<studio>")
    problems = list(model.diagnostics.errors)
    if not model.course_render_validated:
        problems.append(f"render index coverage {model.diagnostics.index_coverage}")
    bsp = model.collision.bsp
    if bsp is None:
        problems.append("no tag100 collision tree")
        return {"ok": False, "problems": problems}
    tree = parse_course_tag100_bytes(bsp.raw, "<studio>", allow_trailing=True)
    rest = bsp.raw[tree.consumed_size:]
    if struct.unpack_from("<I", rest)[0] != TAG1339:
        problems.append("tag1339 bounds do not follow the collision tree")
    land = parse_course_tag1400_bytes(rest[44:], "<studio>")
    nan_planes = sum(1 for r in land.records if any(math.isnan(v) for v in r.float_suffix))
    if nan_planes:
        problems.append(f"{nan_planes} land records with undefined planes")
    result = {"ok": not problems, "problems": problems, "vertices": len(model.vertices.positions),
              "draw_records": len(model.course_root_records), "tag100_nodes": len(tree.nodes),
              "land_records": len(land.records), "land_grid": [land.dimension_0, land.dimension_1]}
    if expected is not None:
        result["matches_build"] = (result["land_records"] == expected.report["land_database"]["records"]
                                   and result["draw_records"] == expected.report["draw_records"])
        if not result["matches_build"]:
            result["ok"] = False
            problems.append("re-read structure differs from the build report")
    return result
