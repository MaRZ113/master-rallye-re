#!/usr/bin/env python3
"""Repeatable R4E zero-edit DX/DXT corpus audit (outputs ignored reports)."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes,encode_png,encode_dxt_pixels
from master_rallye.r4e_writer import patch_dx_attributes
from master_rallye.texture_authoring import decode_rgba_png

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("unpacked_root",type=Path)
    parser.add_argument("--report",required=True,type=Path)
    args=parser.parse_args()
    root=args.unpacked_root.resolve()
    dx=list((root/"DataGx"/"Vehicles").rglob("*.dx"))
    dxt=list(root.rglob("*.dxt"))
    report={"dx_total":len(dx),"dx_identical":0,"dx_collision_preserved":0,"dx_topology_preserved":0,"dxt_total":len(dxt),"dxt_identical":0,"failures":[]}
    for path in dx:
        try:
            data=path.read_bytes(); model=parse_dx_bytes(data)
            patch=patch_dx_attributes(data,positions=model.vertices.positions,normals=[value if all(math.isfinite(x) for x in value) else None for value in model.vertices.normals],uv_sets=[item.values for item in model.uv_sets],colors=model.vertices.colors)
            if patch.data!=data or patch.diff.changed_byte_count:
                raise ValueError("zero edit changed bytes")
            report["dx_identical"]+=1
            report["dx_collision_preserved"]+=int(patch.collision_sha256==patch_dx_attributes(patch.data).collision_sha256)
            report["dx_topology_preserved"]+=int(patch.topology_sha256==patch_dx_attributes(patch.data).topology_sha256)
        except Exception as error:
            report["failures"].append({"path":str(path.relative_to(root)),"error":str(error)})
    for path in dxt:
        try:
            data=path.read_bytes(); texture=parse_dxt_bytes(data)
            width,height,rgba=decode_rgba_png(encode_png(texture))
            rebuilt=encode_dxt_pixels(texture,rgba,width,height)
            if rebuilt!=data:
                raise ValueError("zero edit changed bytes")
            report["dxt_identical"]+=1
        except Exception as error:
            report["failures"].append({"path":str(path.relative_to(root)),"error":str(error)})
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:value if key!="failures" else len(value) for key,value in report.items()}))
    return int(bool(report["failures"]))
if __name__=="__main__":
    raise SystemExit(main())
