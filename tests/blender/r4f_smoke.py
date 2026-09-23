"""Protected-source Blender topology exporter smoke; output stays ignored."""
import json
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/"src"),str(root/"blender")]
from master_rallye_io.blender_mesh import create_collection,import_dx_resource
from master_rallye_io.blender_topology_export import preview_topology,export_topology

source=Path(sys.argv[sys.argv.index("--")+1]).resolve()
output=Path(sys.argv[sys.argv.index("--")+2]).resolve() if len(sys.argv[sys.argv.index("--")+1:])>1 else None
obj=import_dx_resource(source,create_collection("R4F Audit"),load_textures=False,show_collision=False).object
path,rebuilt,compiled=preview_topology(obj)
assert rebuilt.output_model.diagnostics.validated
assert rebuilt.source_vertex_count==rebuilt.output_vertex_count
assert rebuilt.source_triangle_count==rebuilt.output_triangle_count
assert path==source
if output is not None:
    safe,_=export_topology(obj,output)
    assert safe.status in {"SOURCE_IDENTICAL","NO_CHANGE"} or safe.patch.diff.changed_byte_count==0
    assert output.read_bytes()==source.read_bytes()
    assert json.loads(obj["mr_topology_last_export_json"])["mode"]=="SAFE_SAME_TOPOLOGY_PATCH"
    layer=obj.data.uv_layers["MR UV 0"]
    for loop in obj.data.loops:
        if loop.vertex_index==0:
            layer.data[loop.index].uv.x+=0.01
    edited_path=output.with_name("uv-route.dx")
    safe_edit,_=export_topology(obj,edited_path)
    assert safe_edit.patch.classification=="SAME_TOPOLOGY_GEOMETRY_ATTRIBUTES"
    assert edited_path.read_bytes()!=source.read_bytes()
print("R4F_BLENDER_ZERO",json.dumps({"source":str(source),"byte_identical":rebuilt.byte_identical,"semantic_equivalent":rebuilt.semantic_equivalent,"compiled":compiled.to_dict()}))
