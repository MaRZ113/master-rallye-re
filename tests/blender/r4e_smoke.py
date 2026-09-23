"""Synthetic R4E Blender attribute export smoke."""
import sys
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/"src"),str(root/"blender")]
from master_rallye_io.blender_mesh import create_collection,import_dx_resource
from master_rallye_io.blender_export import export_dx_attributes

fixture=Path(sys.argv[sys.argv.index("--")+1]).resolve()
out=Path(sys.argv[sys.argv.index("--")+2]).resolve()
collection=create_collection("R4E Test")
result=import_dx_resource(fixture/"synthetic.dx",collection,load_textures=False,show_collision=False)
obj=result.object
original=(fixture/"synthetic.dx").read_bytes()
zero=export_dx_attributes(obj,out/"zero.dx")
assert zero.patch.data==original,zero.patch.to_dict()
mesh=obj.data
layer=mesh.uv_layers["MR UV 0"]
for loop in mesh.loops:
    if loop.vertex_index==0:
        layer.data[loop.index].uv.x+=0.125
uv=export_dx_attributes(obj,out/"uv.dx")
assert uv.patch.classification=="SAME_TOPOLOGY_GEOMETRY_ATTRIBUTES"
normal=mesh.attributes["mr_source_normal"].data[0]
normal.vector=(0.125,0,2)
both=export_dx_attributes(obj,out/"normal.dx")
assert any(x.field=="normal" for x in both.patch.changes)
normal.vector=(0,0,2)
for loop in mesh.loops:
    if loop.vertex_index==0:
        layer.data[loop.index].uv.x-=0.125
colors=mesh.color_attributes["MR Vertex Color"]
colors.data[0].color_srgb=(0.25,0.5,0.75,1)
color=export_dx_attributes(obj,out/"color.dx")
assert any(x.field=="vertex_color_raw" for x in color.patch.changes)
colors.data[0].color_srgb=(1,1,1,1)
# A deliberately divergent loop for the same source vertex must fail.
loop_ids=[loop.index for loop in mesh.loops if loop.vertex_index==0]
assert len(loop_ids)>1
layer.data[loop_ids[0]].uv.x+=0.1
try:
    export_dx_attributes(obj,out/"seam.dx")
except Exception as error:
    assert "REQUIRES_R4F_TOPOLOGY_WRITER" in str(error),error
else:
    raise AssertionError("UV seam accepted")
layer.data[loop_ids[0]].uv.x-=0.1
source_normals=[tuple(item.vector) for item in mesh.attributes["mr_source_normal"].data]
mesh.attributes.remove(mesh.attributes["mr_source_normal"])
corner_normals=mesh.attributes.new("mr_source_normal","FLOAT_VECTOR","CORNER")
for loop in mesh.loops:
    corner_normals.data[loop.index].vector=source_normals[loop.vertex_index]
corner_normals.data[loop_ids[0]].vector=(1,0,0)
try:
    export_dx_attributes(obj,out/"normal_seam.dx")
except Exception as error:
    assert "REQUIRES_R4F_TOPOLOGY_WRITER" in str(error),error
else:
    raise AssertionError("normal corner divergence accepted")
corner_normals.data[loop_ids[0]].vector=source_normals[0]
source_colors=[tuple(item.color_srgb) for item in mesh.color_attributes["MR Vertex Color"].data]
mesh.color_attributes.remove(mesh.color_attributes["MR Vertex Color"])
corner_colors=mesh.color_attributes.new("MR Vertex Color","BYTE_COLOR","CORNER")
for loop in mesh.loops:
    corner_colors.data[loop.index].color_srgb=source_colors[loop.vertex_index]
corner_colors.data[loop_ids[0]].color_srgb=(0,0,0,1)
try:
    export_dx_attributes(obj,out/"color_seam.dx")
except Exception as error:
    assert "REQUIRES_R4F_TOPOLOGY_WRITER" in str(error),error
else:
    raise AssertionError("color corner divergence accepted")
print("R4E_BLENDER_PASS")
