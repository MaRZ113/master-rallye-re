"""Import sources into a Course Studio project.

* :func:`import_gxm` - a course GXM v7 source (Retail/Demo exporter output or a
  Studio-written source) with exact roles from its node tree;
* :func:`import_retail_course` - a Retail course (RaceTest XML + DX): terrain
  and water from the tag-1400 land database joined with the render records
  (UVs, materials, colours), visual objects from the remaining render
  triangles, collision-only geometry recovered exactly from the native BSP
  (:func:`master_rallye.studio.collision.extract_native_collision`), markers,
  checkpoints, route, limits and pace notes from the scene;
* :func:`import_obj` - Wavefront OBJ for command-line workflows (Blender users
  import OBJ/FBX/glTF with Blender's own importers and assign a role).
"""
from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path

from ..course_gxm import _float3_at, parse_course_gxm_model_v7
from ..course_gxm_writer import decode_materials
from .materials import parse_native_name
from .model import (ROLE_COLLISION, ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER, Area, Checkpoint, CourseProject,
                    Material, Mesh, PaceNote, Provenance, SoundAnchor, Texture, new_uid, safe_key)


def _texture_key(reference: str) -> str | None:
    if not reference or reference == "Null":
        return None
    base = os.path.basename(reference.replace("\\", "/"))
    stem, ext = os.path.splitext(base)
    if ext.lower() in (".gxi", ".dxt") and stem.lower().endswith("-tga"):
        return stem.lower()
    if ext.lower() == ".tga":
        return f"{stem.lower()}-tga"
    return stem.lower()


def material_from_native(key: str, name: str, textures: list, *, uses_alpha: bool = False) -> Material:
    info = parse_native_name(name)
    alpha = info["alpha"]
    if alpha == "opaque" and uses_alpha:
        alpha = "blend"      # cooker: blend flag = UsesAlpha of texture slot 0
    return Material(key=key, label=info["label"], shader=info["shader"], surface=info["surface"],
                    textures=list(textures) + [None] * (3 - len(textures)), noise=info["noise"],
                    alpha=alpha, clamp=info["clamp"], mip=info["mip"], scroll=info["scroll"], native=name)


def gxm_role(path: list[str]) -> str:
    joined = " ".join(path).lower()
    if "$nodraw" in joined:
        return ROLE_COLLISION
    if "$water" in joined:
        return ROLE_WATER
    if "$bsp" in joined and ("$landdb" in joined or "$draw" in joined):
        return ROLE_TERRAIN
    return ROLE_VISUAL


def import_gxm(path: Path, project: CourseProject | None = None) -> CourseProject:
    path = Path(path)
    model = parse_course_gxm_model_v7(path)
    gmats = decode_materials(model.materials.raw, model.materials.count)
    project = project or CourseProject(name=safe_key(path.stem))
    keys = []
    for index, gm in enumerate(gmats):
        texs = [_texture_key(s.reference) for s in gm.slots]
        key = f"m{index:03d}"
        project.materials[key] = material_from_native(
            key, gm.name, [texs[0], texs[1] if len(texs) > 1 else None, None],
            uses_alpha=bool(gm.slots and gm.slots[0].present and gm.slots[0].uses_alpha))
        for tk, slot in zip(texs, gm.slots):
            if tk and tk not in project.textures:
                project.textures[tk] = Texture(key=tk, has_alpha=slot.has_alpha)
        keys.append(key)

    nodes = model.object_table.nodes
    paths = _node_paths(path, nodes)
    for node, node_path in paths:
        if node.mesh_index is None or not node.mesh_size:
            continue
        role = gxm_role(node_path)
        mesh = Mesh(id=new_uid("mesh_"), name=node.name, role=role, source=f"gxm:{path.name}:{node.name}",
                    group="/".join(node_path[:-1]))
        lookup: dict = {}
        mat_slots: dict = {}
        uv, normals, colors = [], [], []
        for ti in range(node.mesh_index, node.mesh_index + node.mesh_size):
            tri = model.triangle(ti)
            ids = []
            for k in range(3):
                pi = tri.position_indices[k]
                if pi not in lookup:
                    p = _float3_at(model.positions, pi)
                    lookup[pi] = len(mesh.positions) // 3
                    mesh.positions.extend((p[0], p[2], -p[1]))
                ids.append(lookup[pi])
                ni = tri.normal_indices[k]
                n = _float3_at(model.normals, ni) if ni != 0xFFFFFFFF else (0.0, 0.0, 1.0)
                normals.extend((n[0], n[2], -n[1]))
                tci = tri.texcoord_indices[k]
                t = _float3_at(model.texcoords, tci) if tci != 0xFFFFFFFF else (0.0, 0.0, 0.0)
                uv.extend((t[0], t[1]))
                ci = tri.color_indices[k]
                c = model.color(ci) if ci != 0xFFFFFFFF else (1.0, 1.0, 1.0, 1.0)
                colors.extend(max(0, min(255, int(round(v * 255)))) for v in c)
            mesh.triangles.extend(ids)
            key = keys[tri.material_index]
            if key not in mat_slots:
                mat_slots[key] = len(mesh.materials)
                mesh.materials.append(key)
            mesh.tri_material.append(mat_slots[key])
        mesh.uv, mesh.normals, mesh.colors = uv, normals, colors
        project.meshes.append(mesh)
    project.provenance.notes.append(f"imported GXM {path.name} sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}")
    project.log("import_gxm", source=path.name, meshes=len(project.meshes))
    return project


def _node_paths(path: Path, nodes):
    """(node, [ancestor names..., own name]) from the GXM table's parent links."""
    by_id = {n.ordinal: n for n in nodes}
    out = []
    for node in nodes:
        chain, cur, guard = [], node, 0
        while cur is not None and guard < 256:
            chain.append(cur.name)
            cur = by_id.get(cur.parent_id) if cur.parent_id is not None else None
            guard += 1
        out.append((node, list(reversed(chain))))
    return out


# ---------------------------------------------------------------------- OBJ
def import_obj(path: Path, project: CourseProject, *, role: str = ROLE_TERRAIN, material: str = "imported",
               scale: float = 1.0, y_up: bool = True) -> Mesh:
    """Minimal Wavefront OBJ importer (v/vt/vn/f, usemtl). Game space = OBJ space when ``y_up``."""
    positions, texcoords, normals = [], [], []
    mesh = Mesh(id=new_uid("mesh_"), name=Path(path).stem, role=role, source=f"obj:{Path(path).name}")
    mesh.uv, mesh.normals = [], []
    current = material
    lookup = {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            x, y, z = (float(v) * scale for v in parts[1:4])
            positions.append((x, y, z) if y_up else (x, z, -y))
        elif parts[0] == "vt":
            texcoords.append((float(parts[1]), float(parts[2]) if len(parts) > 2 else 0.0))
        elif parts[0] == "vn":
            x, y, z = (float(v) for v in parts[1:4])
            normals.append((x, y, z) if y_up else (x, z, -y))
        elif parts[0] == "usemtl":
            current = safe_key(" ".join(parts[1:])).lower()
        elif parts[0] == "f":
            corners = []
            for token in parts[1:]:
                fields = (token.split("/") + ["", ""])[:3]
                vi = int(fields[0]); vi = vi - 1 if vi > 0 else len(positions) + vi
                ti = int(fields[1]) - 1 if fields[1] else None
                ni = int(fields[2]) - 1 if fields[2] else None
                corners.append((vi, ti, ni))
            for k in range(1, len(corners) - 1):
                for vi, ti, ni in (corners[0], corners[k], corners[k + 1]):
                    if vi not in lookup:
                        lookup[vi] = len(mesh.positions) // 3
                        mesh.positions.extend(positions[vi])
                    mesh.triangles.append(lookup[vi])
                    mesh.uv.extend(texcoords[ti] if ti is not None else (0.0, 0.0))
                    mesh.normals.extend(normals[ni] if ni is not None else (0.0, 1.0, 0.0))
                if current not in mesh.materials:
                    mesh.materials.append(current)
                    project.ensure_material(current, label=current)
                mesh.tri_material.append(mesh.materials.index(current))
    if not any(normals):
        mesh.normals = None
    project.meshes.append(mesh)
    project.log("import_obj", source=Path(path).name, triangles=mesh.triangle_count, role=role)
    return mesh


# ---------------------------------------------------------------------- Retail course
def _resolve(root: Path, relative: str) -> Path | None:
    from .validate import ci_path
    return ci_path(root, relative)


def _shader_from_fields(record) -> tuple[str, str, str]:
    """(shader, alpha, clamp) from native record fields when no TXT name is available."""
    flags = record.flags_0x20
    alpha = "cutout" if flags[1] else "blend" if flags[0] else "opaque"
    clamp = {1: "", 2: "u", 4: "v", 0: "uv"}.get(record.unknown_0x14, "")
    mask = record.unknown_0x24
    if record.unknown_0x18 == 1 or mask & 16:
        shader = "water"
    elif record.unknown_0x18 == 2:
        shader = "waterall"
    elif mask & 4:
        shader = "metal"
    elif mask & 8:
        shader = "ground"
    elif alpha == "cutout":
        shader = "tree"
    else:
        shader = "object"
    return shader, alpha, clamp


def import_retail_course(resource_root: Path, race: str, *, extract_collision: bool = True,
                         progress=None) -> CourseProject:
    """Retail RaceTest ``race`` (scene stem, e.g. ``France1``) -> editable project."""
    import struct as _struct
    from ..course_bsp import tree_from_parsed
    from ..course_tag100 import parse_course_tag100_bytes
    from ..course_tag1400 import parse_course_tag1400_bytes
    from ..dx_course import parse_course_dx_bytes
    from .ai import LIMIT_NAMES
    from .race import read_scene

    say = progress or (lambda *a: None)
    resource_root = Path(resource_root)
    scene_path = _resolve(resource_root, f"DataScene/RaceTest/{race}.xml")
    if scene_path is None:
        raise FileNotFoundError(f"RaceTest {race}.xml not found under {resource_root}")
    scene = read_scene(scene_path)
    if len(scene["landscape"]) != 1:
        raise ValueError(f"{race} has {len(scene['landscape'])} landscape models; import one stage at a time")
    model_rel = "DataGx/" + scene["landscape"][0].replace("\\", "/")
    folder = model_rel.rsplit("/", 1)[0]
    dx_path = _resolve(resource_root, model_rel + ".dx")
    if dx_path is None:
        raise FileNotFoundError(f"course model {model_rel}.dx not found")
    data = dx_path.read_bytes()
    say("read", 0.05)
    model = parse_course_dx_bytes(data, dx_path.name)
    tree_raw = model.collision.bsp.raw
    parsed_tree = parse_course_tag100_bytes(tree_raw, dx_path.name, allow_trailing=True)
    rest = tree_raw[parsed_tree.consumed_size:]
    land = parse_course_tag1400_bytes(rest[44:], dx_path.name, allow_trailing=True)
    trailing = rest[44 + land.consumed_size:]

    project = CourseProject(name=safe_key(f"{race}Edit"))
    project.build.course_key = safe_key(f"{race}Edit")
    project.build.title = f"{race} (edited)"
    project.environment.template = Path(scene_path).stem
    project.provenance = Provenance(kind="retail", race=race, scene=scene_path.relative_to(resource_root).as_posix(),
                                    model=dx_path.relative_to(resource_root).as_posix(),
                                    hashes={"dx": hashlib.sha256(data).hexdigest(),
                                            "scene": hashlib.sha256(scene_path.read_bytes()).hexdigest()})
    if trailing:
        project.provenance.notes.append(
            f"tag{_struct.unpack_from('<I', trailing)[0]} ({len(trailing)} bytes): sector visibility graph of the Retail "
            "hierarchical render batches; Studio writes the Retail cooker's flat layout, which has none")

    # TXT names per texture (unique matches only)
    txt_names: dict = {}
    txt = next((p for p in dx_path.parent.iterdir() if p.suffix.lower() == ".txt"), None)
    if txt is not None:
        text = txt.read_text(encoding="latin-1")
        for name, block in re.findall(r"has name \[(.*?)\]\r?\n((?:\s+Texture.*\r?\n)*)", text):
            m0 = re.search(r"Texture \[ ?0\].*Name\[(.*)\]", block)
            if m0:
                txt_names.setdefault(_texture_key(m0.group(1)), set()).add(name)

    P = model.vertices.positions
    N = model.vertices.normals
    C = model.vertices.colors
    U0 = model.uv_sets[0].values if model.uv_sets else None
    I = model.local_indices
    materials_by_sig: dict = {}
    render_tris = {}           # sorted position key -> (record material key, authoring-order vertex ids)
    for record in model.physical_draws:
        slots = [s.value for s in record.texture_slots]
        sig = (tuple(slots), record.unknown_0x14, record.unknown_0x18, round(record.unknown_0x1c_float, 3),
               bytes(record.flags_0x20), record.unknown_0x24)
        if sig not in materials_by_sig:
            key = f"m{len(materials_by_sig):03d}"
            shader, alpha, clamp = _shader_from_fields(record)
            base = slots[0] if slots and slots[0] != "Null" else None
            second = slots[1] if len(slots) > 1 and slots[1] != "Null" else None
            names = txt_names.get(base.lower() if base else None, set())
            native = next(iter(names)) if len(names) == 1 else None
            if native:
                mat = material_from_native(key, native, [base, second, None], uses_alpha=alpha == "blend")
                mat.alpha, mat.clamp = alpha, clamp
            else:
                mat = Material(key=key, label=base or "untextured", shader=shader, surface=None,
                               textures=[base, second, None], noise=bool(record.unknown_0x24 & 8), alpha=alpha,
                               clamp=clamp, mip=record.unknown_0x1c_float or 1.0)
            project.materials[key] = mat
            for s in slots:
                if s and s != "Null" and s not in project.textures:
                    project.textures[s] = Texture(key=s, native=f"{folder}/{s}.dxt")
            materials_by_sig[sig] = key
        key = materials_by_sig[sig]
        for k in range(record.index_count // 3):
            ids = tuple(record.vertex_base + I[record.index_start + 3 * k + j] for j in range(3))
            pk = tuple(sorted((round(P[i][0], 2), round(P[i][1], 2), round(P[i][2], 2)) for i in ids))
            render_tris.setdefault(pk, (key, (ids[1], ids[0], ids[2])))   # render (b, a, c) -> authoring
    say("render", 0.3)

    def new_mesh(name, role, group):
        mesh = Mesh(id=new_uid("mesh_"), name=name, role=role, source=f"retail:{race}", group=group)
        mesh.uv, mesh.normals, mesh.colors = [], [], []
        return mesh
    terrain = new_mesh("Terrain", ROLE_TERRAIN, "Terrain")
    hidden = new_mesh("Invisible ground", "terrain_hidden", "Terrain")
    water = new_mesh("Water", ROLE_WATER, "Water")
    strings = [s.raw_bytes.decode("latin-1") for s in land.strings]
    land_material: dict = {}
    used = set()
    for record in land.records:
        fp = record.float_prefix
        if any(math.isnan(v) for v in record.float_suffix):
            continue
        a, b, c = (fp[6], fp[7], fp[8]), (fp[3], fp[4], fp[5]), (fp[0], fp[1], fp[2])   # stored (c, b, a)
        name = strings[record.string_ref_index]
        is_water = "$surfacetype(water)" in name or "$shader(water)" in name or "$shader(puddle)" in name
        pk = tuple(sorted((round(p[0], 2), round(p[1], 2), round(p[2], 2)) for p in (a, b, c)))
        hit = render_tris.get(pk)
        target = water if is_water else terrain if hit else hidden
        if hit:
            used.add(pk)
            rkey, ids = hit
            mkey = f"{rkey}:{record.string_ref_index}"
            if mkey not in project.materials:
                base = project.materials[rkey]
                mat = material_from_native(mkey, name, list(base.textures), uses_alpha=base.alpha == "blend")
                mat.alpha, mat.clamp, mat.mip = base.alpha, base.clamp, base.mip
                project.materials[mkey] = mat
            for i in ids:
                target.positions.extend(P[i])
                target.normals.extend(N[i])
                target.colors.extend((C[4 * i + 2], C[4 * i + 1], C[4 * i], C[4 * i + 3]))
                target.uv.extend(U0[i] if U0 else (0.0, 0.0))
        else:
            mkey = land_material.get(record.string_ref_index)
            if mkey is None:
                mkey = f"land{record.string_ref_index:02d}"
                project.materials[mkey] = material_from_native(mkey, name, [None, None, None])
                land_material[record.string_ref_index] = mkey
            n = record.float_suffix[:3]
            for p in (a, b, c):
                target.positions.extend(p)
                target.normals.extend((-n[0], -n[1], -n[2]))
                target.colors.extend((255, 255, 255, 255))
                target.uv.extend((0.0, 0.0))
        base_index = target.vertex_count - 3
        target.triangles.extend((base_index, base_index + 1, base_index + 2))
        if mkey not in target.materials:
            target.materials.append(mkey)
        target.tri_material.append(target.materials.index(mkey))
    say("land", 0.5)

    objects = new_mesh("Objects", ROLE_VISUAL, "Objects")
    for pk, (rkey, ids) in render_tris.items():
        if pk in used:
            continue
        base_index = objects.vertex_count
        for i in ids:
            objects.positions.extend(P[i])
            objects.normals.extend(N[i])
            objects.colors.extend((C[4 * i + 2], C[4 * i + 1], C[4 * i], C[4 * i + 3]))
            objects.uv.extend(U0[i] if U0 else (0.0, 0.0))
        objects.triangles.extend((base_index, base_index + 1, base_index + 2))
        if rkey not in objects.materials:
            objects.materials.append(rkey)
        objects.tri_material.append(objects.materials.index(rkey))
    for mesh in (terrain, hidden, water, objects):
        if mesh.triangle_count:
            _weld(mesh)
            project.meshes.append(mesh)
    say("objects", 0.6)

    if extract_collision:
        from .collision import HeightField, extract_native_solids, solids_to_mesh
        root = tree_from_parsed(parsed_tree)
        lo, hi = land.vector_a, land.vector_b
        top = max(p[1] for p in P) + 10.0
        land_tris = []
        for record in land.records:
            fp = record.float_prefix
            if not any(math.isnan(v) for v in record.float_suffix):
                land_tris.append(((fp[6], fp[7], fp[8]), (fp[3], fp[4], fp[5]), (fp[0], fp[1], fp[2])))
        hf = HeightField(land_tris)
        solids, stats = extract_native_solids(
            root, lo, (hi[0], top, hi[2]), heights=lambda x, z: hf.ground(x, z),
            ground_planes=[r.float_suffix for r in land.records],
            progress=lambda s, n: say("collision", 0.6 + 0.3 * min(1.0, n / 400000)))
        project.materials.setdefault("collision", Material("collision", "Collision", shader="object", surface="rock",
                                                           noise=False, textures=[None, None, None]))
        mesh = solids_to_mesh(solids, name="Native collision", material="collision", source=f"retail-bsp:{race}")
        mesh.group = "Collision"
        project.meshes.append(mesh)
        from ..course_bsp import encode_tag100
        from .native_graft import fix_slots, mesh_digest, object_leaves, object_tree
        keep = object_leaves(root, lo, (hi[0], top, hi[2]), heights=lambda x, z: hf.ground(x, z),
                             ground_planes=[r.float_suffix for r in land.records])
        project.blobs["native_objects"] = encode_tag100(fix_slots(object_tree(root, keep)))
        project.extras["native_collision"] = {"digest": mesh_digest(mesh), "cells": len(keep),
                                              "lo": list(lo), "hi": [hi[0], top, hi[2]]}
        project.provenance.notes.append(f"native collision: {stats['object_cells']} closed convex solid cells of the "
                                        f"tag100 tree above the ground ({stats})")

    q = scene["start"]
    if len(q) == 4:
        project.start = Area(center=tuple(sum(p[k] for p in q) / 4 for k in range(3)), corners=[list(p) for p in q])
    q = scene["finish"]
    if len(q) == 4:
        project.finish = Area(center=tuple(sum(p[k] for p in q) / 4 for k in range(3)), corners=[list(p) for p in q])
    project.route.points = [tuple(p) for p in scene["raceline"]]
    if len(project.route.points) > 1:
        gaps = sorted(math.dist(a, b) for a, b in zip(project.route.points, project.route.points[1:]))
        project.route.spacing = gaps[len(gaps) // 2]
    project.limits.mode = "manual"
    project.limits.lists = {n: [tuple(p) for p in scene["limits"].get(n, [])] for n in LIMIT_NAMES}
    for cp in sorted(scene["checkpoints"], key=lambda c: c["id"]):
        project.checkpoints.append(Checkpoint(uid=new_uid("cp_"), center=cp["center"], radius=cp["radius"],
                                              extra_time=cp["extra_time"], boards=cp["boards"], name=cp["name"]))
    project.build.pacenotes = "manual"
    for note in scene["pacenotes"]:
        project.pacenotes.append(PaceNote(uid=new_uid("pn_"), position=note["position"], heading=note["heading"],
                                          note_id=note["id"], distance=note["distance"]))
    for snd in scene["sounds"]:
        project.sounds.append(SoundAnchor(uid=new_uid("snd_"), position=snd["position"], template=snd["name"],
                                          name=snd["name"]))
    project.environment.replay_cameras = [tuple(p) for p in scene["cameras"]]
    if "first_time" in scene:
        project.environment.time_to_first_checkpoint = scene["first_time"]
        project.environment.percentage_time_change = scene["percentage"]
    _orient_checkpoints(project)
    project.log("import_retail", race=race, meshes=[(m.name, m.triangle_count) for m in project.meshes])
    say("done", 1.0)
    return project


def _weld(mesh: Mesh) -> None:
    """Share vertices with identical positions (corner attributes stay per corner)."""
    lookup, positions, remap = {}, [], []
    for i in range(mesh.vertex_count):
        p = mesh.vertex(i)
        key = (round(p[0], 4), round(p[1], 4), round(p[2], 4))
        if key not in lookup:
            lookup[key] = len(positions) // 3
            positions.extend(p)
        remap.append(lookup[key])
    mesh.positions = positions
    mesh.triangles = [remap[i] for i in mesh.triangles]


def _orient_checkpoints(project: CourseProject) -> None:
    from ..course_entry import RouteFrame
    if len(project.route.points) < 2:
        return
    frame = RouteFrame(project.route.points)
    for cp in project.checkpoints:
        yaw = frame.local(cp.center)[3]
        cp.heading = math.degrees(math.atan2(math.cos(yaw), math.sin(yaw)))
