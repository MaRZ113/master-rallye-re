#!/usr/bin/env python3
"""Generate four controlled R4E Astero runtime DX probes outside Git."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from master_rallye.dx import parse_dx_bytes
from master_rallye.r4e_writer import patch_dx_attributes
from master_rallye.vehicle_packaging import vehicle_dependencies,pack_sma

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("vehicle_dir",type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--sma-root",type=Path)
    args=parser.parse_args()
    vehicle=args.vehicle_dir.resolve()
    output=args.output.resolve()
    source=vehicle/"car.dx"
    data=source.read_bytes()
    model=parse_dx_bytes(data,source=str(source))
    if vehicle.name!="Astero" or not model.diagnostics.validated:
        raise ValueError("probes are deliberately bound to the validated Astero car.dx")
    draw=model.physical_draws
    expected={12:"mastersticker263-tga",11:"chromebar-tga",7:"acamo64b-tga",23:"windscreen32-tga"}
    for index,name in expected.items():
        if draw[index].texture_slots[0].value.casefold()!=name:
            raise ValueError(f"draw {index} source binding changed")
    deps=vehicle_dependencies(vehicle)
    probes={}
    uv=[list(item.values) for item in model.uv_sets]
    for index in range(draw[12].vertex_base,draw[12].vertex_base+draw[12].local_vertex_max+1):
        u,v=uv[0][index]
        uv[0][index]=(u+0.05,v)
    probes["E1_uv"]=(dict(uv_sets=uv),"Sticker mapping shifts by +0.05 U; geometry/collision unchanged.")
    normals=list(model.vertices.normals)
    for index in range(draw[11].vertex_base,draw[11].vertex_base+min(8,draw[11].local_vertex_max+1)):
        x,y,z=normals[index]
        angle=math.radians(15)
        normals[index]=(x*math.cos(angle)+z*math.sin(angle),y,-x*math.sin(angle)+z*math.cos(angle))
    probes["E2_normal"]=(dict(normals=normals),"Bullbar/chrome reflection orientation changes; silhouette/collision unchanged.")
    colors=bytearray(model.vertices.colors)
    for index in range(draw[7].vertex_base,draw[7].vertex_base+min(12,draw[7].local_vertex_max+1)):
        for channel in range(3):
            colors[index*4+channel]=colors[index*4+channel]//2
    probes["E3_color"]=(dict(colors=bytes(colors)),"Body patch darkens through stage-0 diffuse modulation; UV/geometry unchanged.")
    probes["E4_alpha"]=(dict(material_alpha={23:False}),"Existing windscreen alpha-family flag disabled; glass should appear opaque.")
    reports={}
    for name,(changes,expected_effect) in probes.items():
        patch=patch_dx_attributes(data,source=str(source),**changes)
        if patch.data==data:
            raise ValueError(f"{name} produced no change")
        destination=output/name/"DataGx"/"Vehicles"/"Astero"/"car.dx"
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(patch.data)
        report=patch.to_dict()
        report["candidate"]=name
        report["source"]="Astero/car.dx"
        report["expected_effect"]=expected_effect
        report["dependency_manifest"]=deps
        report["packaging_method"]="loose DataGx/Vehicles/Astero/car.dx"
        report["runtime_status"]="PENDING_HUMAN_TEST"
        (output/name/"validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        (output/name/"TEST_INSTRUCTIONS.txt").write_text(f"{name}: {expected_effect}\nBack up your game archive before using this candidate. Load Astero in a race. Test one candidate at a time, then restore the original. Record visuals and any crash.\n",encoding="utf-8")
        reports[name]={"classification":patch.classification,"changed_bytes":patch.diff.changed_byte_count,"sha256":patch.output_sha256}
    if args.sma_root:
        replacement=output/"E1_uv"/"DataGx"/"Vehicles"/"Astero"/"car.dx"
        archive=output/"E5_python_sma"/"Data.sma"
        info=pack_sma(args.sma_root,archive,{"DataGx/Vehicles/Astero/car.dx":replacement})
        original_archive=args.sma_root.resolve().parent/"Data.sma"
        info["original_archive_sha256"]=hashlib.sha256(original_archive.read_bytes()).hexdigest() if original_archive.is_file() else None
        info["override_source_sha256"]=hashlib.sha256(data).hexdigest()
        info["override_output_sha256"]=hashlib.sha256(replacement.read_bytes()).hexdigest()
        info["candidate"]="E5_python_sma"
        info["base_edit"]="E1_uv"
        info["runtime_status"]="PENDING_HUMAN_TEST"
        (archive.parent/"validation.json").write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8")
        (archive.parent/"TEST_INSTRUCTIONS.txt").write_text("E5: replace Data.sma only after backing up the original; load Astero in a race and verify the E1 sticker mapping shift and archive acceptance. Python ZIP runtime confirmation pending.\n",encoding="utf-8")
        reports["E5_python_sma"]=info
    print(json.dumps(reports,indent=2))
if __name__=="__main__":
    main()
