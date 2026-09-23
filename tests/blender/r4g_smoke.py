"""Blender R4G vehicle project and collision controls smoke on protected Astero."""
import json
import sys
from pathlib import Path
import bpy

root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/"src"),str(root/"blender")]
import master_rallye_io
master_rallye_io.register()
source=Path(sys.argv[sys.argv.index("--")+1]).resolve()
output=Path(sys.argv[sys.argv.index("--")+2]).resolve()
candidate=Path(sys.argv[sys.argv.index("--")+3]).resolve()
assert bpy.ops.import_scene.master_rallye_vehicle(
    directory=str(source),load_textures=False,show_collision=True)=={"FINISHED"}
objects={obj.get("mr_resource_name"):obj for obj in bpy.data.objects if "mr_metadata_json" in obj}
assert {"car.dx","complete.dx","wheel.dx"}<=set(objects)
assert objects["car.dx"]["mr_resource_role"]=="RACE BODY"
assert objects["complete.dx"]["mr_resource_role"]=="PRESENTATION"
assert objects["wheel.dx"]["mr_resource_role"]=="WHEEL TEMPLATE"
car=objects["car.dx"]
bpy.ops.object.select_all(action="DESELECT")
car.select_set(True)
bpy.context.view_layer.objects.active=car
car["mr_collision_scale"]=[1.2,1.0,1.0]
assert bpy.ops.object.master_rallye_collision_preview()=={"FINISHED"}
assert car["mr_collision_validation_status"]=="PASS"
assert json.loads(car["mr_collision_preview_json"])["radius"]>0
car["mr_last_export_path"]=str(candidate)
assert bpy.ops.object.master_rallye_bounds_visibility(visible=True)=={"FINISHED"}
assert len([item for item in bpy.data.objects if item.get("mr_bounds_owner")==str(source/"car.dx")])==2
project=output/"project.json"
assert bpy.ops.export_scene.master_rallye_vehicle_project(filepath=str(project))=={"FINISHED"}
assert bpy.ops.object.master_rallye_validate_vehicle()=={"FINISHED"}
assert car["mr_vehicle_validation_status"]=="PASS"
assert bpy.ops.export_scene.master_rallye_build_vehicle(directory=str(output/"build"))=={"FINISHED"}
manifest=json.loads((output/"build"/"manifest.json").read_text(encoding="utf-8"))
assert manifest["status"]=="PASS" and len(manifest["files"])==1
print("R4G_BLENDER_PASS",json.dumps({"resources":len(objects),"staged":len(manifest["files"])}))
