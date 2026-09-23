"""Packaged R4G addon import/registration smoke without repository src imports."""
import sys
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/"dist/master_rallye_io.zip"))
import master_rallye_io
master_rallye_io.register()
source=Path(sys.argv[sys.argv.index("--")+1]).resolve()
assert bpy.ops.import_scene.master_rallye_vehicle(
    directory=str(source),load_textures=False,show_collision=False)=={"FINISHED"}
objects={obj.get("mr_resource_name"):obj for obj in bpy.data.objects if "mr_metadata_json" in obj}
assert {"car.dx","complete.dx","wheel.dx"}<=set(objects)
assert objects["car.dx"]["mr_resource_role"]=="RACE BODY"
assert hasattr(bpy.ops.object,"master_rallye_validate_vehicle")
print("R4G_PACKAGED_PASS",len(objects))
