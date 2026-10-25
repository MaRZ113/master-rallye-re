"""Vehicle-level validation and safe staged build using existing donor identities."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import json
from pathlib import Path
import shutil
import struct
import zlib

from .bounds import bound_points, compute_bounds1339, replace_bounds1339
from .collision_writer import patch_dx_collision_translation
from .collision_scale import scale_dx_collision
from .dx import parse_dx_bytes
from .errors import DxWriteError
from .dxt import parse_dxt, parse_dxt_bytes, encode_dxt_pixels, PNG_ROWS_FLIP_VERTICAL
from .r4e_writer import patch_dx_attributes
from .texture_authoring import decode_rgba_png
from .vehicle_packaging import RESOURCE_NAMES, pack_sma, vehicle_dependencies


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class VehicleProject:
    path: Path
    vehicle_name: str
    source_vehicle_dir: Path
    resources: dict
    texture_edits: dict
    texture_replacements: dict

    @classmethod
    def load(cls, path: Path) -> "VehicleProject":
        path = Path(path).resolve()
        spec = json.loads(path.read_text(encoding="utf-8"))
        allowed_top = {"vehicle_name", "source_vehicle_dir", "resources",
                       "texture_edits", "texture_replacements"}
        if set(spec) - allowed_top:
            raise ValueError(f"unsupported VehicleProject keys: {sorted(set(spec) - allowed_top)}")
        source = Path(spec["source_vehicle_dir"])
        if not source.is_absolute():
            source = path.parent / source
        resources = spec.get("resources", {})
        texture_names = list(spec.get("texture_edits", {})) + list(spec.get("texture_replacements", {}))
        if len({name.casefold() for name in texture_names}) != len(texture_names):
            raise ValueError("duplicate texture edit/replacement names")
        allowed_resource = {"source_sha256", "candidate", "topology_candidate", "scene_candidate", "native_brake_scene_candidate",
                            "attributes", "surface_edits", "surface_source_sha256", "surface_layers", "collision_scale", "collision_center",
                            "collision_translation", "crew_layer"}
        for role, edit in resources.items():
            if set(edit) - allowed_resource:
                raise ValueError(f"{role}: unsupported edit keys {sorted(set(edit) - allowed_resource)}")
        if any(name not in RESOURCE_NAMES for name in resources):
            raise ValueError("project resources must be car.dx, complete.dx or wheel.dx")
        if spec.get("vehicle_name", source.name).casefold() != source.name.casefold():
            raise ValueError("project vehicle name differs from source folder")
        return cls(path, source.name, source.resolve(), resources, spec.get("texture_edits", {}),
                   spec.get("texture_replacements", {}))

    def resolve(self, value: str) -> Path:
        path = Path(value)
        return (path if path.is_absolute() else self.path.parent / path).resolve()


def _topology_candidate(source: bytes, candidate: bytes, role: str) -> dict:
    original = parse_dx_bytes(source)
    edited = parse_dx_bytes(candidate)
    if not edited.diagnostics.validated or edited.diagnostics.warnings != original.diagnostics.warnings:
        raise ValueError(f"{role}: candidate DX failed structural validation")
    if source[:12] != candidate[:12] or len(original.physical_draws) != len(edited.physical_draws):
        raise ValueError(f"{role}: source header or draw count changed")
    alpha_toggles = []
    for old, new in zip(original.physical_draws, edited.physical_draws):
        if (old.tag, old.texture_tuple, old.group_label, old.control_words,
                old.flags_0x20[2:], old.unknown_0x24) != (
                new.tag, new.texture_tuple, new.group_label, new.control_words,
                new.flags_0x20[2:], new.unknown_0x24):
            raise ValueError(f"{role}: existing draw/material identity changed")
        alpha_edit = old.flags_0x20[0] != new.flags_0x20[0]
        alpha_test_edit = old.flags_0x20[1] != new.flags_0x20[1]
        if alpha_edit or alpha_test_edit:
            if old.tag not in (2, 7, 8) or tuple(new.flags_0x20[:2]) not in ((0, 0), (1, 0), (1, 1)):
                raise ValueError(f"{role}: unauthorized or conflicting material pass change on draw {old.draw_index}")
            alpha_toggles.append({"draw": old.draw_index, "alpha": bool(new.flags_0x20[0]),
                                  "alpha_test": bool(new.flags_0x20[1])})
        a = bytearray(source[old.offset:old.offset + old.own_size])
        b = bytearray(candidate[new.offset:new.offset + new.own_size])
        for relative in (4, 8, 12, 16):
            offset_a = old.core_offset - old.offset + relative
            offset_b = new.core_offset - new.offset + relative
            a[offset_a:offset_a + 4] = b"\0" * 4
            b[offset_b:offset_b + 4] = b"\0" * 4
        if alpha_edit or alpha_test_edit:
            for relative in (0x20, 0x21):
                a[old.core_offset - old.offset + relative] = 0
                b[new.core_offset - new.offset + relative] = 0
        if a != b:
            raise ValueError(f"{role}: unexpected draw-record bytes")
    if source[original.collision.offset:original.collision.unparsed_offset] != candidate[edited.collision.offset:edited.collision.unparsed_offset]:
        raise ValueError(f"{role}: collision bytes changed in topology candidate")
    bounds = edited.collision.spatial_bounds_1339
    if bounds is None:
        raise ValueError(f"{role}: marker-1339 bounds absent")
    points = bound_points(edited.vertices.positions, edited.collision.convex_hull)
    if any(any(not bounds.minimum[i] - 1e-5 <= p[i] <= bounds.maximum[i] + 1e-5 for i in range(3)) for p in points):
        raise ValueError(f"{role}: spatial bounds do not cover geometry")
    if max(math.dist(p, bounds.center) for p in points) > bounds.radius + 1e-5:
        raise ValueError(f"{role}: spatial radius does not cover geometry")
    expected = compute_bounds1339(edited.vertices.positions, edited.collision.convex_hull)
    if max(abs(a - b) for a, b in zip(bounds.minimum + bounds.maximum, expected.minimum + expected.maximum)) > 1e-5:
        raise ValueError(f"{role}: bounds extrema are stale")
    if edited.collision.unparsed_offset + 44 != len(candidate):
        raise ValueError(f"{role}: unrecognized bytes after bounds")
    return {"source_vertices": original.vertex_count, "output_vertices": edited.vertex_count,
            "source_triangles": original.triangle_count, "output_triangles": edited.triangle_count,
            "alpha_toggles": alpha_toggles, "bounds": bounds.to_dict(), "status": "PASS"}


def _attribute_candidate(source: bytes, candidate: bytes, role: str) -> dict:
    old = parse_dx_bytes(source)
    new = parse_dx_bytes(candidate)
    if old.vertex_count != new.vertex_count or old.local_indices != new.local_indices:
        raise ValueError(f"{role}: candidate is not same-topology")
    alpha = {}
    alpha_test = {}
    env = {}
    for index, (before, after) in enumerate(zip(old.physical_draws, new.physical_draws)):
        if before.flags_0x20[0] != after.flags_0x20[0]:
            alpha[index] = bool(after.flags_0x20[0])
        if before.flags_0x20[1] != after.flags_0x20[1]:
            alpha_test[index] = bool(after.flags_0x20[1])
        if bool(before.unknown_0x24 & 4) != bool(after.unknown_0x24 & 4):
            env[index] = bool(after.unknown_0x24 & 4)
    expected = patch_dx_attributes(
        source, positions=new.vertices.positions,
        normals=[v if all(math.isfinite(x) for x in v) else None for v in new.vertices.normals],
        uv_sets=[layer.values for layer in new.uv_sets],
        colors=new.vertices.colors, material_alpha=alpha, material_alpha_test=alpha_test, material_env=env)
    if expected.data != candidate:
        raise ValueError(f"{role}: same-topology candidate contains unauthorized bytes")
    return {"status": "PASS", "classification": expected.classification}


def _compile_resource(project: VehicleProject, role: str, spec: dict) -> tuple[bytes, dict]:
    def binding_texture(stem):
        from .assets import AssetResolver
        path=AssetResolver(project.source_vehicle_dir).resolve_texture(stem)
        if path is None:raise ValueError('Unresolved binding texture: '+stem)
        if path.name in project.texture_edits:return _compile_texture(project,path.name,project.texture_edits[path.name])[0]
        if path.name in project.texture_replacements:
            entry=project.texture_replacements[path.name]
            entry=project.texture_replacements[path.name]
            if _sha(path.read_bytes())!=entry['source_sha256']:raise ValueError('Binding texture source changed')
            return project.resolve(entry['candidate']).read_bytes()
        return path.read_bytes()
    path = project.source_vehicle_dir / role
    source = path.read_bytes()
    expected = spec.get("source_sha256")
    if expected != _sha(source):
        raise ValueError(f"{role}: source SHA-256 mismatch")
    operations = [key for key in ("candidate", "topology_candidate", "scene_candidate", "native_brake_scene_candidate", "attributes") if key in spec]
    if len(operations) > 1:
        raise ValueError(f"{role}: candidate operations cannot be combined")
    data = source
    detail = {"resource": role, "source_sha256": _sha(source)}
    if 'native_brake_scene_candidate' in spec:
        from .addon_sdk.native_brakes import validate_brake_scene
        candidate=project.resolve(spec['native_brake_scene_candidate'])
        if candidate==path.resolve() or role!='car.dx':raise ValueError('native brake scene requires a separate race resource')
        if any(key.startswith('collision_') for key in spec):raise ValueError('native brake scene preserves donor collision')
        data=candidate.read_bytes();detail['imported_scene']=validate_brake_scene(source,data)
    elif 'scene_candidate' in spec:
        from .scene_dx_writer import validate_scene_dx
        candidate=project.resolve(spec['scene_candidate'])
        if candidate==path.resolve():raise ValueError(f'{role}: candidate is original source')
        if any(key.startswith('collision_') for key in spec):raise ValueError('imported scenes preserve donor collision; collision edits require a separate stage')
        data=candidate.read_bytes();detail['imported_scene']=validate_scene_dx(source,data)
    elif "candidate" in spec or "topology_candidate" in spec:
        candidate = project.resolve(spec.get("candidate", spec.get("topology_candidate")))
        if candidate.resolve() == path.resolve():
            raise ValueError(f"{role}: candidate is original source")
        data = candidate.read_bytes()
        source_model = parse_dx_bytes(source)
        candidate_model = parse_dx_bytes(data)
        if (source_model.vertex_count == candidate_model.vertex_count
                and source_model.local_indices == candidate_model.local_indices):
            try:
                detail["attributes"] = _attribute_candidate(source, data, role)
            except (ValueError, DxWriteError):
                # An explicit topology_candidate may rewrite the bounds footer (e.g. a uniformly scaled
                # wheel.dx); the topology validator checks the fixed draw records, collision and suffix.
                if "topology_candidate" not in spec:
                    raise
                detail["topology"] = _topology_candidate(source, data, role)
        else:
            detail["topology"] = _topology_candidate(source, data, role)
    elif "attributes" in spec:
        edit = spec["attributes"]
        patch = patch_dx_attributes(data,
            positions=edit.get("positions"), normals=edit.get("normals"),
            uv_sets=edit.get("uv_sets"), colors=edit.get("colors"),
            material_alpha={int(k):v for k,v in edit.get("material_alpha",{}).items()},
            material_alpha_test={int(k):v for k,v in edit.get("material_alpha_test",{}).items()},
            material_env={int(k):v for k,v in edit.get("material_env",{}).items()})
        data = patch.data
        detail["attributes"] = patch.classification
    if "collision_scale" in spec:
        if role != "car.dx":
            raise ValueError("collision scale authoring is limited to car.dx")
        scaled = scale_dx_collision(data, spec["collision_scale"],
                                    spec.get("collision_center"))
        data = scaled["data"]
        detail["collision_scale"] = {k:v for k,v in scaled.items() if k != "data"}
    if "collision_translation" in spec:
        if role != "car.dx":
            raise ValueError("collision translation authoring is limited to car.dx")
        translated = patch_dx_collision_translation(data, spec["collision_translation"])
        data = translated.data
        parsed = parse_dx_bytes(data)
        bounds = compute_bounds1339(parsed.vertices.positions, parsed.collision.convex_hull,
                                    offset=parsed.collision.unparsed_offset)
        data = replace_bounds1339(data, bounds, footer_offset=parsed.collision.unparsed_offset)
        detail["collision_translation"] = {
            "delta": list(spec["collision_translation"]),
            "changed_byte_count": translated.diff.changed_byte_count,
            "unexpected_diff_count": 0, "bounds": bounds.to_dict()}
    if "surface_edits" in spec:
        from .surface_authoring import apply_surface_edits
        surface=apply_surface_edits(data,spec['surface_edits'],source_sha256=spec.get('surface_source_sha256'),texture_provider=binding_texture)
        data=surface.data;detail['surface_authoring']=surface.to_dict()
    if 'surface_layers' in spec:
        from .surface_authoring import apply_surface_edits
        if not isinstance(spec['surface_layers'],list) or len(spec['surface_layers'])>30:raise ValueError('Invalid surface layer stack')
        detail['surface_layers']=[]
        for layer in spec['surface_layers']:
            if not isinstance(layer,dict) or set(layer)!={'source_sha256','edits'}:raise ValueError('Invalid surface layer')
            surface=apply_surface_edits(data,layer['edits'],source_sha256=layer['source_sha256'],texture_provider=binding_texture)
            data=surface.data;detail['surface_layers'].append(surface.to_dict())
    if 'crew_layer' in spec:
        from .crew_authoring import apply_crew_fit
        layer=spec['crew_layer']
        if set(layer)!={'source_sha256','definition','placements'}:raise ValueError('Invalid crew layer')
        data,detail['crew_fit']=apply_crew_fit(data,layer['definition'],layer['placements'],source_sha256=layer['source_sha256'])
    final = parse_dx_bytes(data)
    if not final.diagnostics.validated or final.collision.spatial_bounds_1339 is None:
        raise ValueError(f"{role}: compiled DX failed final validation")
    detail["output_sha256"] = _sha(data)
    detail["status"] = "PASS"
    return data, detail


def _compile_texture(project: VehicleProject, name: str, spec: dict) -> tuple[bytes, dict]:
    path = project.source_vehicle_dir / name
    if not path.is_file() or path.suffix.casefold() != ".dxt":
        raise ValueError(f"{name}: texture is not an existing DXT")
    source = path.read_bytes()
    if spec.get("source_sha256") != _sha(source):
        raise ValueError(f"{name}: DXT source SHA-256 mismatch")
    template = parse_dxt(path)
    png = project.resolve(spec["png"])
    width, height, rgba = decode_rgba_png(png.read_bytes())
    data = encode_dxt_pixels(template, rgba, width, height, row_policy=PNG_ROWS_FLIP_VERTICAL)
    refresh_crc=spec.get('refresh_crc32',False)
    if type(refresh_crc) is not bool:raise ValueError(f'{name}: refresh_crc32 must be boolean')
    if refresh_crc:data=data[:8]+struct.pack('<I',zlib.crc32(data[20:])&0xffffffff)+data[12:]
    after = parse_dxt_bytes(data)
    old_header=template.header[:8]+template.header[12:] if refresh_crc else template.header
    new_header=after.header[:8]+after.header[12:] if refresh_crc else after.header
    if old_header != new_header or len(data) != len(source):
        raise ValueError(f"{name}: DXT header/size changed")
    return data, {"resource": name, "source_sha256": _sha(source),
                  "output_sha256": _sha(data), "dimensions": [width, height], "status": "PASS"}


def validate_vehicle(project: VehicleProject) -> dict:
    diagnostics = []
    resources = {}
    compiled = {}
    source = project.source_vehicle_dir
    if not source.is_dir():
        return {"status": "FAIL", "diagnostics": [{"level": "FAIL", "message": "source vehicle folder is absent"}]}
    for role in ("car.dx", "complete.dx"):
        if not (source / role).is_file():
            diagnostics.append({"level": "FAIL", "message": f"required {role} is absent"})
    if not (source / "wheel.dx").is_file():
        diagnostics.append({"level": "WARN", "message": "wheel.dx is absent; this vehicle has no wheel template"})
    try:
        deps = vehicle_dependencies(source)
        if deps["unresolved_count"]:
            diagnostics.append({"level": "FAIL", "message": f"{deps['unresolved_count']} texture references unresolved"})
    except Exception as error:
        deps = None
        diagnostics.append({"level": "FAIL", "message": f"dependency scan: {error}"})
    for role in RESOURCE_NAMES:
        path = source / role
        if not path.is_file():
            continue
        try:
            model = parse_dx_bytes(path.read_bytes())
            if not model.diagnostics.validated or model.collision.spatial_bounds_1339 is None:
                raise ValueError(f"{role}: source DX grammar or marker-1339 bounds invalid")
            bounds = model.collision.spatial_bounds_1339
            expected = compute_bounds1339(model.vertices.positions, model.collision.convex_hull)
            if max(abs(a - b) for a, b in zip(
                    bounds.minimum + bounds.maximum,
                    expected.minimum + expected.maximum)) > 1e-5:
                raise ValueError(f"{role}: source bounds extrema do not match geometry")
            if model.collision.errors:
                diagnostics.append({"level": "WARN", "message": f"{role}: source collision has known parser diagnostics"})
        except Exception as error:
            diagnostics.append({"level": "FAIL", "message": str(error)})
    if deps is not None:
        seen = set()
        for binding in deps["bindings"]:
            path = binding["source_path"]
            if not path or path in seen:
                continue
            seen.add(path)
            try:
                parse_dxt(Path(path))
            except Exception as error:
                diagnostics.append({"level": "FAIL", "message": f"DXT {Path(path).name}: {error}"})
    for role, spec in project.resources.items():
        try:
            if not (source / role).is_file():
                raise ValueError(f"{role}: source resource absent")
            data, detail = _compile_resource(project, role, spec)
            if data != (source / role).read_bytes():
                compiled[role] = data
            resources[role] = detail
        except Exception as error:
            diagnostics.append({"level": "FAIL", "message": str(error)})
    for name, spec in project.texture_replacements.items():
        try:
            if Path(name).name != name or not name.casefold().endswith(".dxt"):
                raise ValueError(f"{name}: texture replacement key must be a DXT basename")
            source_path = source / name
            original = source_path.read_bytes()
            if _sha(original) != spec.get("source_sha256"):
                raise ValueError(f"{name}: DXT source SHA-256 mismatch")
            replacement = project.resolve(spec["candidate"]).read_bytes()
            before, after = parse_dxt_bytes(original), parse_dxt_bytes(replacement)
            if before.header != after.header or len(original) != len(replacement):
                raise ValueError(f"{name}: replacement DXT header/size changed")
            compiled[name] = replacement
            resources[name] = {"resource": name, "source_sha256": _sha(original),
                               "output_sha256": _sha(replacement), "status": "PASS"}
        except Exception as error:
            diagnostics.append({"level": "FAIL", "message": str(error)})
    for name, spec in project.texture_edits.items():
        try:
            if name in project.texture_replacements or Path(name).name != name:
                raise ValueError(f"{name}: duplicate or non-basename texture edit")
            data, detail = _compile_texture(project, name, spec)
            compiled[name] = data
            resources[name] = detail
        except Exception as error:
            diagnostics.append({"level": "FAIL", "message": str(error)})
    status = "FAIL" if any(d["level"] == "FAIL" for d in diagnostics) else (
        "WARN" if diagnostics else "PASS")
    return {"status": status, "vehicle": project.vehicle_name, "source_vehicle_dir": str(source),
            "resources": resources, "diagnostics": diagnostics,
            "dependency_manifest": deps, "compiled": compiled}


def build_vehicle_mod(project: VehicleProject, output: Path, *,
                      sma: Path | None = None, sma_root: Path | None = None) -> dict:
    validation = validate_vehicle(project)
    if validation["status"] == "FAIL":
        raise ValueError("vehicle validation failed: " + "; ".join(d["message"] for d in validation["diagnostics"]))
    output = Path(output).resolve()
    source = project.source_vehicle_dir
    if (output == source or source in output.parents or output == project.path
            or (source.parent.name.casefold() == "vehicles" and
                (output == source.parent or source.parent in output.parents))):
        raise ValueError("build output must be outside the source vehicle folder/project")
    if output.exists() and any(output.iterdir()):
        raise ValueError("build output must be empty")
    if sma is not None and (sma_root is None or Path(sma).resolve().exists()):
        raise ValueError("SMA requires a full original tree and a fresh destination")
    stage = output / "staging"
    vehicle_stage = stage / "DataGx" / "Vehicles" / project.vehicle_name
    vehicle_stage.mkdir(parents=True)
    files = []
    for name, data in sorted(validation["compiled"].items()):
        dest = vehicle_stage / name
        dest.write_bytes(data)
        files.append({"resource": name, "archive_path": dest.relative_to(stage).as_posix(),
                      "sha256": _sha(data)})
    report = {k:v for k,v in validation.items() if k != "compiled"}
    report.update(staging_root=str(stage), files=files)
    if sma is not None:
        overrides = {item["archive_path"]: vehicle_stage / item["resource"] for item in files}
        report["sma"] = pack_sma(Path(sma_root), Path(sma), overrides)
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
