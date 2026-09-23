"""Blender edit-mode duplicate-face topology test on protected Astero source."""
import json
import sys
from pathlib import Path

import bpy
import bmesh

root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/"src"),str(root/"blender")]
from master_rallye_io.blender_mesh import create_collection,import_dx_resource
from master_rallye_io.blender_topology_export import export_topology,preview_topology
from master_rallye_io.operators.export_dx_topology import OBJECT_OT_master_rallye_assign_draw

source=Path(sys.argv[sys.argv.index("--")+1]).resolve()
output=Path(sys.argv[sys.argv.index("--")+2]).resolve()
obj=import_dx_resource(source,create_collection("R4F Edit"),load_textures=False,show_collision=False).object
bpy.context.view_layer.objects.active=obj
obj.select_set(True)
mesh=obj.data
old_vertices=len(mesh.vertices)
old_faces=len(mesh.polygons)
face_id=next(p.index for p in mesh.polygons if mesh.attributes["mr_source_triangle"].data[p.index].value==
             2772//3+27)
bpy.ops.object.mode_set(mode="EDIT")
bm=bmesh.from_edit_mesh(mesh)
bm.faces.ensure_lookup_table()
original=bm.faces[face_id]
result=bmesh.ops.duplicate(bm,geom=[original]+list(original.verts)+list(original.edges))
new_faces=[item for item in result["geom"] if isinstance(item,bmesh.types.BMFace)]
new_verts=[item for item in result["geom"] if isinstance(item,bmesh.types.BMVert)]
assert len(new_faces)==1 and len(new_verts)==3,(len(new_faces),len(new_verts))
normal=original.normal.normalized()
for vertex in new_verts:
    vertex.co+=normal*.05
for item in bm.faces:
    item.select=False
new_faces[0].select=True
bmesh.update_edit_mesh(mesh)
bpy.utils.register_class(OBJECT_OT_master_rallye_assign_draw)
assert bpy.ops.object.master_rallye_assign_draw(draw_id=7)=={"FINISHED"}
assert obj.mode=="EDIT"
bpy.ops.object.mode_set(mode="OBJECT")
assert len(mesh.vertices)==old_vertices+3
assert len(mesh.polygons)==old_faces+1
face=mesh.polygons[-1]
assert not mesh.attributes["mr_source_face_valid"].data[face.index].value
assert mesh.attributes["mr_draw_assignment_valid"].data[face.index].value
assert mesh.attributes["mr_draw_id"].data[face.index].value==7
for point in range(old_vertices,len(mesh.vertices)):
    assert mesh.attributes["mr_generated_vertex"].data[point].value
    assert not mesh.attributes["mr_source_vertex_valid"].data[point].value
_,rebuilt,compiled=preview_topology(obj)
assert rebuilt.output_vertex_count==old_vertices+3
assert rebuilt.output_triangle_count==old_faces+1
assert rebuilt.changed_draws==(7,)
assert compiled.generated_for_new_geometry==3
assert rebuilt.external_diff_count==0
exported,report=export_topology(obj,output)
assert exported.data==rebuilt.data
print("R4F_BLENDER_EDIT_PASS",json.dumps({"candidate_sha256":rebuilt.output_sha256,"compilation":compiled.to_dict()}))
