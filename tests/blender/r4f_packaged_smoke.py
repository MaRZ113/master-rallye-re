"""Check vendored R4F preview without adding repository src to sys.path."""
import json
import sys
from pathlib import Path
import bpy
bpy.ops.preferences.addon_enable(module="master_rallye_io")
from master_rallye_io.blender_mesh import create_collection,import_dx_resource
from master_rallye_io.blender_topology_export import preview_topology
source=Path(sys.argv[sys.argv.index("--")+1]).resolve()
obj=import_dx_resource(source,create_collection("R4F Packaged"),load_textures=False,show_collision=False).object
_,rebuilt,compiled=preview_topology(obj)
assert rebuilt.byte_identical and compiled.compiled_vertex_count==rebuilt.source_vertex_count
print("R4F_PACKAGED_PASS",json.dumps({"vertices":rebuilt.output_vertex_count,"draws":len(rebuilt.output_model.physical_draws)}))
