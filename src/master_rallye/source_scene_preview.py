"""Universal Vehicle Scene -> neutral MRPV preview, never MR DX authoring.

The shared D3D9 viewport consumes this disposable scene. Original geometry,
texture channels and source metadata stay in the source project. Native game
lighting, material shaders and dynamic equipment behavior are not simulated.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path

IDENTITY = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
VIEWS = ("front", "rear", "left", "right", "top", "isometric")
MAX_SCENE = 256 * 1024 * 1024


def capture_startup_info():
    if not hasattr(subprocess, "STARTUPINFO"):
        return None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = 0
    return info


def _finite(values, count, label):
    if not isinstance(values, (list, tuple)) or len(values) != count or any(
        type(v) not in (int, float) or not math.isfinite(v) for v in values
    ):
        raise ValueError(f"Invalid finite {label}")
    return list(values)


def _matrix(values, label):
    values = _finite(values, 16, label)
    if values[12:16] != [0, 0, 0, 1]:
        raise ValueError(f"{label} must be affine row-major")
    if abs(_det(values)) < 1e-12:
        raise ValueError(f"Singular {label}")
    return values


def _mul(a, b):
    return [sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4)) for r in range(4) for c in range(4)]


def _det(a):
    return (a[0] * (a[5] * a[10] - a[6] * a[9])
            - a[1] * (a[4] * a[10] - a[6] * a[8])
            + a[2] * (a[4] * a[9] - a[5] * a[8]))


def _point(a, p):
    return tuple(sum(a[r * 4 + k] * p[k] for k in range(3)) + a[r * 4 + 3] for r in range(3))


def _normal(a, p):
    # Cofactor matrix / determinant is the inverse-transpose normal transform.
    cof = [a[5]*a[10]-a[6]*a[9], a[6]*a[8]-a[4]*a[10], a[4]*a[9]-a[5]*a[8],
           a[2]*a[9]-a[1]*a[10], a[0]*a[10]-a[2]*a[8], a[1]*a[8]-a[0]*a[9],
           a[1]*a[6]-a[2]*a[5], a[2]*a[4]-a[0]*a[6], a[0]*a[5]-a[1]*a[4]]
    d = _det(a)
    n = [sum(cof[r * 3 + k] * p[k] for k in range(3)) / d for r in range(3)]
    length = math.sqrt(sum(v * v for v in n))
    if length < 1e-12:
        raise ValueError("Zero-length source normal")
    return tuple(v / length for v in n)


def _unlinked(path):
    for part in [path.absolute(), *path.absolute().parents]:
        if part.is_symlink() or (part.exists() and getattr(part.stat(), "st_file_attributes", 0) & 0x400):
            raise ValueError(f"Linked/reparse preview path: {part}")


def _asset(root, relative, size, digest):
    if not isinstance(relative, str) or "\\" in relative or ":" in relative:
        raise ValueError("Texture path must be a safe relative source-project path")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("Texture path escapes source project")
    path = root / rel
    _unlinked(path)
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Missing or escaped source-project texture")
    before = path.stat()
    if before.st_size != size:
        raise ValueError("Texture sidecar size does not match dimensions")
    data = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Texture sidecar changed during read")
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("Texture sidecar SHA-256 mismatch")
    return data


def _index(items, label, limit):
    if not isinstance(items, list) or len(items) > limit:
        raise ValueError(f"{label} count exceeds preview bounds")
    result = {}
    for item in items:
        key = item.get("id")
        if not isinstance(key, str) or not key or len(key) > 1024 or key in result:
            raise ValueError(f"Invalid/duplicate {label} ID")
        result[key] = item
    return result


def stage_source_scene(scene: dict, output: Path, *, scene_root: Path,
                       basis="normalized", material_mode="original", visibility="selected") -> dict:
    """Write a disposable neutral preview without changing the source scene."""
    if scene.get("schema") != "universal-vehicle-scene/1":
        raise ValueError("Universal Vehicle Scene v1 required")
    from .universal_vehicle_scene import validate_scene
    validate_scene(scene)
    if basis not in ("source", "normalized") or material_mode not in ("original", "interpreted", "material_ids"):
        raise ValueError("Unknown source preview coordinate/material mode")
    if visibility not in ("selected", "source", "all"):
        raise ValueError("Unknown source visibility selection")
    root, output = Path(scene_root), Path(output)
    _unlinked(root); _unlinked(output)
    if output.suffix.lower() != ".mrpv" or output.exists() or output.with_suffix(".json").exists():
        raise ValueError("A fresh .mrpv preview/output report pair is required")
    extra_protected = scene["source"].get("protected_roots", [])
    if not isinstance(extra_protected, list) or len(extra_protected) > 128 or any(not isinstance(p, str) for p in extra_protected):
        raise ValueError("Invalid protected source-root metadata")
    protected = [Path(scene["source"]["root"]), *map(Path, extra_protected)]
    for path in protected:
        _unlinked(path)
    for target in (output.resolve(), output.with_suffix(".json").resolve()):
        if any(target == path.resolve() or target.is_relative_to(path.resolve()) for path in protected):
            raise ValueError("Preview output overlaps original read-only source/tool root")
    textures = _index(scene.get("textures"), "texture", 1024)
    materials = _index(scene.get("materials"), "material", 4096)
    meshes = _index(scene.get("meshes"), "mesh", 8192)
    nodes = _index(scene.get("nodes"), "node", 8192)
    basis_matrix = (_matrix(scene["coordinate_system"]["source_to_normalized"], "source-to-normalized matrix")
                    if basis == "normalized" else IDENTITY)
    texture_rows, texture_ids = [], {}
    total_texture_bytes = 0
    for key, tex in textures.items():
        w, h = tex.get("width"), tex.get("height")
        if type(w) is not int or type(h) is not int or min(w, h) < 1 or max(w, h) > 4096:
            raise ValueError("Source texture dimensions outside preview bound")
        total_texture_bytes += w * h * 4
        if total_texture_bytes > MAX_SCENE // 2:
            raise ValueError("Source texture aggregate preview budget exceeded")
        raw = bytearray(_asset(root, tex["rgba_path"], w * h * 4, tex["rgba_sha256"]))
        raw[0::4], raw[2::4] = raw[2::4], raw[0::4]
        texture_ids[key] = len(texture_rows)
        texture_rows.append((key, w, h, bytes(raw)))
    world, inherited_visible, visiting = {}, {}, set()

    def node_world(key):
        if key in world:
            return world[key]
        if key in visiting:
            raise ValueError("Cyclic source scene hierarchy")
        visiting.add(key)
        node = nodes[key]
        parent = node.get("parent_id")
        if parent is not None and parent not in nodes:
            raise ValueError("Source node references missing parent")
        matrix = _matrix(node["local_transform"], "source node transform")
        if parent is not None:
            matrix = _mul(node_world(parent), matrix)
        flag = node.get("source_visible", node.get("visible")) if visibility == "source" else node.get("visible")
        if type(flag) is not bool:
            raise ValueError("Source node visibility must be explicit boolean")
        inherited_visible[key] = visibility == "all" or (flag and (parent is None or inherited_visible[parent]))
        visiting.remove(key)
        world[key] = matrix
        return matrix

    draws, points, diagnostics = [], [], []
    total_vertices, total_indices = 0, 0
    for node_id, node in nodes.items():
        matrix = _mul(basis_matrix, node_world(node_id))
        mesh_ids = node.get("mesh_ids")
        if not isinstance(mesh_ids, list) or len(mesh_ids) > 8192 or len(set(mesh_ids)) != len(mesh_ids):
            raise ValueError("Invalid source node mesh list")
        if not inherited_visible[node_id]:
            continue
        for mesh_id in mesh_ids:
            if mesh_id not in meshes:
                raise ValueError("Source node references missing mesh")
            mesh = meshes[mesh_id]
            positions, normals, uvs, triangles = (mesh.get(k) for k in ("positions", "normals", "uvs", "triangles"))
            if not isinstance(positions, list) or not positions or len(positions) > 1_000_000:
                raise ValueError("Invalid source mesh position count")
            if not isinstance(normals, list) or not isinstance(uvs, list) or len(normals) != len(positions) or len(uvs) != len(positions):
                raise ValueError("Source position/normal/UV counts differ")
            if not isinstance(triangles, list) or len(triangles) > 2_000_000:
                raise ValueError("Source triangle count outside preview bound")
            total_vertices += len(positions); total_indices += len(triangles) * 3
            if total_vertices > 1_000_000 or total_indices > 6_000_000:
                raise ValueError("Assembled source geometry exceeds preview aggregate bound")
            material = materials.get(mesh.get("material_id"))
            if material is None:
                raise ValueError("Source mesh references missing material")
            texture_id = material.get("diffuse_texture_id")
            if texture_id is not None and texture_id not in texture_ids:
                raise ValueError("Source material references missing texture")
            transparent = material.get("flags", {}).get("transparent_raw")
            if transparent not in ("0", "1"):
                raise ValueError("Unknown source transparency remains unsupported")
            opacity = 1.
            if material_mode == "interpreted":
                opacity = material.get("preview", {}).get("opacity", 1.)
                if type(opacity) not in (float, int) or not math.isfinite(opacity) or not 0 <= opacity <= 1:
                    raise ValueError("Explicit interpreted opacity must be 0..1")
            color = [255, 255, 255, round(opacity * 255)]
            if material_mode == "material_ids":
                token = hashlib.sha256(material["id"].encode()).digest()
                color[:3] = [80 + c % 176 for c in token[:3]]
            colors = mesh.get('preview_colors_bgra')
            if colors is not None and (not isinstance(colors,list) or len(colors)!=len(positions) or
                any(not isinstance(c,list) or len(c)!=4 or any(type(v)is not int or not 0<=v<=255 for v in c) for c in colors)):
                raise ValueError('Invalid explicit source vertex colors')
            vertices, transformed = bytearray(), []
            for ordinal, (p, n, uv) in enumerate(zip(positions, normals, uvs)):
                p = _point(matrix, _finite(p, 3, "source position"))
                n = _normal(matrix, _finite(n, 3, "source normal"))
                uv = _finite(uv, 2, "source UV")
                transformed.append(p); points.append(p)
                bgra = colors[ordinal][:] if colors is not None and material_mode!='material_ids' else [color[2],color[1],color[0],color[3]]
                if colors is not None and material_mode!='material_ids': bgra[3] = round(bgra[3]*opacity)
                vertices.extend(struct.pack("<6f4B2f", *p, *n, *bgra, *uv))
            indices = []
            mirrored = _det(matrix) < 0
            for tri in triangles:
                if not isinstance(tri, (list, tuple)) or len(tri) != 3 or any(type(i) is not int or not 0 <= i < len(positions) for i in tri):
                    raise ValueError("Source triangle index outside positions")
                indices.extend((tri[0], tri[2], tri[1]) if mirrored else tri)
            centre = [sum(p[k] for p in transformed) / len(transformed) for k in range(3)]
            base = texture_ids[texture_id] if texture_id is not None and material_mode != "material_ids" else -1
            alpha = int(transparent == "1" or opacity < 1)
            name = f"source:{node_id}:{mesh_id}:{mesh.get('name', mesh_id)}"
            state = material.get('source_render_state')
            if state is not None:
                if (state.get('schema')!='dakar2-render-research/1' or state.get('cull') not in ('none','cw','ccw') or
                    type(state.get('depth_write'))is not bool or type(state.get('blend'))is not bool or
                    state.get('draw_pass') not in (0,1) or type(state.get('draw_order'))is not int):
                    raise ValueError('Invalid explicit source draw state')
            draws.append((name, base, alpha, centre, bytes(vertices), indices, state))
            diagnostics.append({"node": node_id, "mesh": mesh_id, "material": material["id"], "role": node.get("role"),
                                "source_member": mesh.get("source"), "source_material": material,
                                "transform_determinant": _det(matrix), "winding_reversed": mirrored,
                                "preview_opacity": opacity, "vertices": len(positions), "triangles": len(triangles)})
            diagnostics[-1]['source_render_state'] = state
    if not points or not draws:
        raise ValueError("No visible source geometry for this selection")
    lo = [min(p[k] for p in points) for k in range(3)]
    hi = [max(p[k] for p in points) for k in range(3)]
    extended = any(d[-1] is not None for d in draws)
    if extended:
        if any(d[-1]is None for d in draws): raise ValueError('Partial source state scene unsupported')
        draws.sort(key=lambda d:(d[-1]['draw_pass'],d[-1]['draw_order']))
    data = bytearray(struct.pack("<4sIII6f", b"MRPV", 2 if extended else 1, len(texture_rows), len(draws), *lo, *hi))

    def string(value):
        raw = value.encode("utf-8")
        if len(raw) > 4096:
            raise ValueError("Source preview string exceeds bound")
        return struct.pack("<I", len(raw)) + raw

    for name, w, h, pixels in texture_rows:
        data.extend(string(name) + struct.pack("<II", w, h) + pixels)
    for name, base, alpha, centre, vertices, indices, state in draws:
        data.extend(string(name) + struct.pack("<Iii4I3fII", 0, base, -1, alpha, 0, 0, 0, *centre, len(vertices) // 36, len(indices)))
        if extended:
            data.extend(struct.pack('<III', {'none':1,'cw':2,'ccw':3}[state['cull']],int(state['depth_write']),int(state['blend'])))
        data.extend(vertices + struct.pack(f"<{len(indices)}I", *indices))
        if len(data) > MAX_SCENE:
            raise ValueError("Neutral source preview exceeds byte budget")
    protected_files = [root / "scene.json", root / "manifest.json", *[root / t["rgba_path"] for t in textures.values()]]
    if any(target.resolve() == source.resolve() for target in (output, output.with_suffix(".json")) for source in protected_files):
        raise ValueError("Preview cannot overwrite source scene or texture sidecars")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    report = {"schema": "universal-vehicle-scene-preview/1", "status": "NEUTRAL_SOURCE_D3D9_APPROXIMATION",
              "basis": basis, "material_mode": material_mode, "visibility": visibility,
              "display_name": scene.get("metadata", {}).get("display_name", "Source vehicle"),
              "scene_sha256": hashlib.sha256(data).hexdigest(), "bounds": [lo, hi], "textures": len(texture_rows),
              "draws": diagnostics, "unknown_semantics": scene.get("unknown_semantics", []),
              "boundaries": ["No MR-native geometry/compiler or CarID", "No source-game runtime parity",
                             "Texture row order and UV values preserved", "Reflectivity and unsupported shaders not invented",
                             "RGBA sidecars are neutral decoded representations; original extra channels may remain unqualified",
                             "Transparency uses explicit source flag; optional preview opacity is an approximation"]}
    output.with_suffix(".json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def preview_cull(scene: dict) -> str:
    value = scene.get("metadata", {}).get("neutral_preview", {}).get("cull", "none")
    if value not in ("none", "cw", "ccw", "source"):
        raise ValueError("Unknown neutral culling interpretation")
    return value


def viewer_command(viewer: Path, scene_path: Path, *, view="isometric", capture: Path | None = None, provenance="", basis="normalized", cull="none") -> list[str]:
    if view not in VIEWS:
        raise ValueError("Unknown neutral fixed view")
    if basis not in ("source", "normalized"):
        raise ValueError("Unknown source coordinate basis")
    if cull not in ("none", "cw", "ccw", "source"):
        raise ValueError("Unknown neutral culling interpretation")
    command = [str(viewer), "--scene", str(scene_path), "--neutral-source", "--workshop", "--cull", 'cw' if cull=='source' else cull,
               "--depth-write", "shader", "--orthographic", "--fixed-view", view, "--source-front",
               "positive-z" if basis == "source" else "negative-z", "--provenance", provenance]
    if cull=='source': command.append('--source-states')
    if capture is not None:
        command.extend(("--capture", str(capture)))
    return command


def capture_views(viewer: Path, scene_path: Path, output: Path, *, provenance="", basis="normalized", cull="none", model=None) -> dict:
    """Capture six actual D3D9 views; this is a preview qualification only."""
    output = Path(output)
    if model not in (None,'race','frontend','wheel'):raise ValueError('Unknown capture model')
    _unlinked(output)
    output.mkdir(parents=True, exist_ok=False)
    paths = {}
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for view in VIEWS:
        path = output / (view + ".bmp")
        command=viewer_command(viewer, scene_path, view=view, capture=path, provenance=provenance, basis=basis, cull=cull)
        if model is not None:command+=['--model',model]
        subprocess.run(command,
                       check=True, timeout=45, creationflags=flags, startupinfo=capture_startup_info())
        if not path.is_file() or path.stat().st_size < 54:
            raise ValueError("D3D9 capture did not produce a valid-sized BMP")
        from PIL import Image
        with Image.open(path) as image:
            image.convert("RGB").save(path.with_suffix(".png"))
        paths[view] = str(path.with_suffix(".png"))
    report = {"schema": "source-scene-captures/1", "renderer": "D3D9 neutral orthographic approximation",
              "views": paths, "cull": cull, "scene_sha256": hashlib.sha256(Path(scene_path).read_bytes()).hexdigest(),
              "model":model,"qualification": "Captures require visual inspection; no source-game parity or MR gameplay claim"}
    (output / "captures.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
