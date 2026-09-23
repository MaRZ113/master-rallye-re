"""Read-only-source Blender audit for R4E.1 normal and environment edits."""
import json
import math
import struct
import sys
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"blender")]
from master_rallye.dx import parse_dx
from master_rallye_io.blender_mesh import create_collection,import_dx_resource
from master_rallye_io.blender_export import export_dx_attributes

source=Path(sys.argv[sys.argv.index("--")+1]).resolve()
output=Path(sys.argv[sys.argv.index("--")+2]).resolve()
model=parse_dx(source)
obj=import_dx_resource(source,create_collection("R4E.1 Audit"),load_textures=False,show_collision=False).object
metadata=json.loads(obj["mr_metadata_json"])
assert metadata["draws"][7]["unknown_0x24"]==7
assert metadata["draws"][7]["texture_slots"][:2]==["acamo64b-tga","whitepaint-tga"]
normal_attribute=obj.data.attributes["mr_source_normal"]
first=1820
assert tuple(normal_attribute.data[first].vector)==model.vertices.normals[first]
for index in range(first,2012):
    x,y,z=model.vertices.normals[index]
    normal_attribute.data[index].vector=(z,y,-x)
normal_result=export_dx_attributes(obj,output/"blender-N1.dx")
normal_model=parse_dx(output/"blender-N1.dx")
for index in range(first,2012):
    x,y,z=model.vertices.normals[index]
    expected=struct.unpack("<3f",struct.pack("<3f",z,y,-x))
    assert normal_model.vertices.normals[index]==expected
assert normal_result.patch.diff.valid
assert {item.field for item in normal_result.patch.changes}=={"normal"}
for index in range(first,2012):
    normal_attribute.data[index].vector=model.vertices.normals[index]
obj["mr_material_env_edits_json"]=json.dumps({"7":False})
env_result=export_dx_attributes(obj,output/"blender-M1.dx")
env_model=parse_dx(output/"blender-M1.dx")
assert env_model.physical_draws[7].unknown_0x24==3
assert env_result.patch.diff.changed_byte_count==1
assert [item.field for item in env_result.patch.changes]==["material_env_bit"]
assert env_model.vertices.normals==model.vertices.normals
assert env_model.vertices.positions==model.vertices.positions
print("R4E1_BLENDER_AUDIT_PASS",json.dumps({"normal_records":len(normal_result.patch.changes),"env_changed_bytes":env_result.patch.diff.changed_byte_count}))
