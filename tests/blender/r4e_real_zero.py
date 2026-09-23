"""R4E full vehicle Blender zero-edit attribute export audit."""
import json
import sys
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/"src"),str(root/"blender")]
from master_rallye_io.blender_mesh import create_collection,import_dx_resource
from master_rallye_io.blender_export import export_dx_attributes
vehicle_root=Path(sys.argv[sys.argv.index("--")+1]).resolve()
output=Path(sys.argv[sys.argv.index("--")+2]).resolve()
collection=create_collection("R4E Corpus")
report={"resources":0,"byte_identical":0,"failures":[]}
for source in sorted(vehicle_root.rglob("*.dx")):
    report["resources"]+=1
    try:
        imported=import_dx_resource(source,collection,load_textures=False,show_collision=False)
        dest=output/"dx"/source.parent.name/source.name
        result=export_dx_attributes(imported.object,dest)
        if dest.read_bytes()!=source.read_bytes():
            raise ValueError("non-identical zero edit")
        report["byte_identical"]+=1
        mesh=imported.object.data
        bpy.data.objects.remove(imported.object,do_unlink=True)
        bpy.data.meshes.remove(mesh,do_unlink=True)
    except Exception as error:
        report["failures"].append({"source":str(source),"error":str(error)})
(output/"report.json").parent.mkdir(parents=True,exist_ok=True)
(output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print("R4E_REAL_BLENDER_ZERO",json.dumps(report))
if report["failures"]:
    raise SystemExit(1)
