"""Loaded-texture vehicle material audit; no game source is written.

Blender --background --factory-startup --python this.py -- <vehicle-root> <output>
All decoded images, copies, and saved Blender data go under output.
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root / "src"), str(root / "blender")]
from master_rallye.material_semantics import MaterialSemantics
from master_rallye_io.blender_export import export_dx_attributes
from master_rallye_io.blender_materials import PreviewMaterialCache
from master_rallye_io.blender_mesh import create_collection, import_dx_resource


def require(condition, message):
    if not condition:
        raise AssertionError(message)


vehicle_root, output = map(lambda value: Path(value).resolve(), sys.argv[sys.argv.index("--") + 1:])
output.mkdir(parents=True, exist_ok=True)
collection = create_collection("R-MAT1 vehicle validation")
caches = {}
counts = Counter()
helpers = Counter()
resources = []
retained = {}
keep = {"Astero/car.dx", "KiaSportage/car.dx", "Pajero/complete.dx",
        "IceCream/car.dx", "Bruno/car.dx", "ChevyBlazer/car.dx"}

for source in sorted(vehicle_root.rglob("*.dx")):
    relative = source.relative_to(vehicle_root).as_posix()
    cache = caches.setdefault(source.parent.name, PreviewMaterialCache(
        source.parent, cache_directory=output / "textures" / source.parent.name))
    object_count = len(bpy.data.objects)
    imported = import_dx_resource(source, collection, load_textures=True,
                                  show_collision=False, material_cache=cache)
    obj, model = imported.object, imported.model
    require(len(bpy.data.objects) == object_count + 1 and obj.type == "MESH", relative + ": one mesh per DX")
    require(len(obj.data.materials) == len({obj[f"mr_draw_material_slot_{draw.draw_index}"]
                                         for draw in model.physical_draws}), relative + ": material count")
    metadata = json.loads(obj["mr_metadata_json"])
    require(metadata["vehicle_material_semantics_version"] == "R_MAT1_V3", relative)
    for raw, draw in zip(metadata["draws"], model.physical_draws):
        prefix = f"{relative} draw {draw.draw_index}"
        sem = MaterialSemantics.from_draw(draw)
        require(sem.classification == "CLASSIFIED", prefix + ": unclassified")
        require(raw["flags_0x20_hex"] == draw.flags_0x20.hex(), prefix + ": raw flags")
        require(raw["texture_slots"] == list(draw.texture_tuple), prefix + ": raw slots")
        require(raw["unknown_0x24"] == draw.unknown_0x24, prefix + ": raw mask")
        require(raw["control_words"] == list(draw.control_words), prefix + ": raw controls")
        require(raw["runtime_material_semantics"] == sem.to_dict(), prefix + ": semantics")
        mat = obj.data.materials[obj[f"mr_draw_material_slot_{draw.draw_index}"]]
        nodes = mat.node_tree.nodes
        require(mat["mr_preview_source_slot"] == (0 if sem.texture_stage_mapping["slot0"].bound else -1), prefix + ": base identity")
        require(mat["mr_primary_texture_slot"] == sem.texture_slots[0], prefix + ": primary identity")
        require(json.loads(mat["mr_texture_slots_json"]) == list(draw.texture_tuple), prefix + ": material raw slots")
        require(json.loads(mat["mr_material_semantics_json"]) == sem.to_dict(), prefix + ": material semantics")
        require(("MR Source Vertex Diffuse" in nodes) == sem.vertex_diffuse_enabled, prefix + ": diffuse gate")
        require(("MR Slot 0 Base" in nodes) == sem.texture_stage_mapping["slot0"].bound, prefix + ": base node")
        require(("MR Slot 1 Environment" in nodes) == sem.null_slot_behavior["stage1_effective"], prefix + ": env node")
        shader = nodes["MR Preview Surface"]
        require(shader.inputs["Alpha"].is_linked == sem.alpha_enabled, prefix + ": raw alpha gate")
        require(mat["mr_preview_confidence"] == "APPROXIMATE", prefix + ": confidence")
        if "MR Slot 0 Base" in nodes:
            image = nodes["MR Slot 0 Base"].image
            require(Path(image["mr_dxt_source"]).stem.casefold() == sem.texture_slots[0].casefold(), prefix + ": base image identity")
            require("MR Source UV 0" in nodes, prefix + ": source UV gate")
        if "MR Slot 1 Environment" in nodes:
            image = nodes["MR Slot 1 Environment"].image
            require(Path(image["mr_dxt_source"]).stem.casefold() == sem.texture_slots[1].casefold(), prefix + ": env image identity")
            require(nodes["MR Env Normal Scale"].inputs["Scale"].default_value == 0.5, prefix + ": normal scale")
            require(tuple(nodes["MR Env Coordinate Bias"].inputs[1].default_value) == (0.5, 0.5, 0.0), prefix + ": normal bias")
            require(nodes["MR Stage 1 Alpha"].operation == "MULTIPLY", prefix + ": stage1 alpha")
            helpers[sem.texture_slots[1]] += 1
        counts["draws"] += 1
        counts[sem.alpha_mode] += 1
        counts["base_bound"] += sem.texture_stage_mapping["slot0"].bound
        counts["environment_bound"] += sem.texture_stage_mapping["slot1"].bound
        counts["environment_preview"] += sem.null_slot_behavior["stage1_effective"]
        counts["null_base"] += not sem.texture_stage_mapping["slot0"].bound
    dest = output / "zero" / source.parent.name / source.name
    exported = export_dx_attributes(obj, dest)
    require(exported.patch.data == source.read_bytes() and dest.read_bytes() == source.read_bytes(), relative + ": zero-edit identity")
    resources.append({"resource": relative, "draws": len(model.physical_draws), "zero_edit": "BYTE_IDENTICAL"})
    if relative in keep:
        retained[relative] = obj.name
    else:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh, do_unlink=True)

require(counts["draws"] == 1478 and len(resources) == 78, "retail reference corpus size")
require(counts["environment_preview"] == 1089, "generic environment coverage")
require(len(helpers) == 8, "all observed helper names")
require(not any(cache.warnings for cache in caches.values()), "missing texture or unknown material warning")

# Real resources supply the images; variants exist only as temporary test objects.
source = vehicle_root / "Astero" / "car.dx"
model = import_dx_resource(source, collection, load_textures=False, show_collision=False).model
draw = copy.deepcopy(next(item for item in model.physical_draws if item.unknown_0x24 == 7))
object.__setattr__(draw, "flags_0x20", bytes((1, 1, 1, 1)))
cache = caches["Astero"]
mat = cache.material_for_draw(draw)
clip = mat.node_tree.nodes["MR Alpha Greater Than 128"]
require(clip.operation == "GREATER_THAN", "alphatest comparator")
require(abs(clip.inputs[1].default_value - 128 / 255) < 1e-7, "alphatest threshold")
require(mat["mr_runtime_shader_family"] == "shader/base_env_alphatest", "alphatest family")

off = PreviewMaterialCache(source.parent, cache_directory=output / "textures" / "Astero", reflections=False)
off_mat = off.material_for_draw(draw)
require("MR Slot 1 Environment" not in off_mat.node_tree.nodes, "Reflections OFF")
require(off_mat["mr_runtime_shader_family"] == "shader/base_alphatest", "Reflections OFF family")
require(json.loads(off_mat["mr_texture_slots_json"])[1] != "Null", "Reflections OFF keeps raw slot")
object.__setattr__(draw, "flags_0x20", bytes((0, 0, 0, 0)))
object.__setattr__(draw, "unknown_0x24", 5)
no_attributes = cache.material_for_draw(draw)
require("MR Source Vertex Diffuse" not in no_attributes.node_tree.nodes, "byte2 OFF")
require("MR No Source UV" in no_attributes.node_tree.nodes, "byte3 OFF")

unknown = copy.deepcopy(draw)
object.__setattr__(unknown, "unknown_0x18", 1)
unknown_mat = cache.material_for_draw(unknown)
require(unknown_mat["mr_preview_confidence"] == "UNKNOWN", "unobserved branch warning")
require("MR Slot 0 Base" not in unknown_mat.node_tree.nodes, "unknown branch fallback")
require(cache.warnings, "unknown branch warning surfaced")

blend = output / "material-validation.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.wm.open_mainfile(filepath=str(blend))
require(all(Path(bpy.path.abspath(image.filepath)).exists() for image in bpy.data.images
            if image.get("mr_dxt_source")), "reloaded image paths")
for relative, name in retained.items():
    obj = bpy.data.objects[name]
    metadata = json.loads(obj["mr_metadata_json"])
    require(metadata["vehicle_material_semantics_version"] == "R_MAT1_V3", relative + ": reload metadata")
    for raw in metadata["draws"]:
        mat = obj.data.materials[obj[f"mr_draw_material_slot_{raw['draw_id']}"]]
        require(mat["mr_preview_semantics"] == "R_MAT1_RUNTIME_STAGES_V3", relative + ": reload material")
        require(mat.node_tree.nodes.get("MR Preview Surface") is not None, relative + ": reload nodes")

# Node edits cannot drive a DX material writer; canonical object/source data does.
obj = bpy.data.objects[retained["Bruno/car.dx"]]
before = obj["mr_metadata_json"]
for mat in obj.data.materials:
    mat.node_tree.nodes.clear()
dest = output / "edited-preview-zero.dx"
edited = export_dx_attributes(obj, dest)
require(edited.patch.data == Path(obj["mr_source_path"]).read_bytes(), "node-edited export")
require(dest.read_bytes() == Path(obj["mr_source_path"]).read_bytes(), "node-edited byte identity")
require(obj["mr_metadata_json"] == before, "node edits preserve canonical metadata")

report = {"status": "PASS", "blender_version": bpy.app.version_string,
          "resource_count": len(resources), "counts": dict(counts), "helper_preview_draws": dict(helpers),
          "raw_metadata": "PASS", "save_reload": "PASS", "zero_edit_exports": len(resources),
          "preview_nodes_edited_export": "BYTE_IDENTICAL", "synthetic_alphatest": "PASS",
          "synthetic_diffuse_uv_gates": "PASS", "reflections_off": "PASS", "unknown_warning": "PASS",
          "resources": resources}
(output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("R_MAT1_BLENDER_PASS", json.dumps({key: value for key, value in report.items() if key != "resources"}))
