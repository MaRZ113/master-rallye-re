#!/usr/bin/env python3
"""Read-only in-memory tag101 scale regression for protected vehicle DX."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from master_rallye.dx import parse_dx_bytes
from master_rallye.collision_scale import scale_dx_collision
from master_rallye.collision_writer import serialize_tag101

def run(root:Path):
    rows=[]
    for path in sorted(root.rglob("*.dx")):
        data=path.read_bytes()
        model=parse_dx_bytes(data)
        if model.collision.convex_hull is None: continue
        row={"resource":path.relative_to(root).as_posix(),"zero_edit":False,
             "nonuniform_scale":False,"unexpected_diff_count":None}
        try:
            if model.collision.errors:
                row["zero_edit"] = serialize_tag101(model.collision.convex_hull) == model.collision.convex_hull.raw
                row["status"]="KNOWN_NONFINITE_OUTLIER"
            else:
                zero=scale_dx_collision(data,(1,1,1))
                row["zero_edit"]=zero["data"]==data
                scaled=scale_dx_collision(data,(1.2,1.0,.9))
                row["nonuniform_scale"]=scaled["validation"]=="PASS"
                row["unexpected_diff_count"]=scaled["unexpected_diff_count"]
                row["changed_byte_count"]=scaled["changed_byte_count"]
                row["status"]="PASS"
        except Exception as error:
            row["status"]="FAIL";row["error"]=str(error)
        rows.append(row)
    summary={"tag101":len(rows),"zero_edit_identity":sum(r["zero_edit"] for r in rows),
             "nonuniform_scale_pass":sum(r["nonuniform_scale"] for r in rows),
             "known_nonfinite_outlier":sum(r["status"]=="KNOWN_NONFINITE_OUTLIER" for r in rows),
             "failures":sum(r["status"]=="FAIL" for r in rows),
             "unexpected_diff_total":sum(r["unexpected_diff_count"] or 0 for r in rows)}
    return {"summary":summary,"resources":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("vehicle_root",type=Path)
    p.add_argument("--json",required=True,type=Path)
    p.add_argument("--markdown",required=True,type=Path)
    a=p.parse_args()
    result=run(a.vehicle_root.resolve());a.json.parent.mkdir(parents=True,exist_ok=True)
    a.json.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    a.markdown.write_text("# Tag101 per-axis scaling corpus\n\n"
        "Protected originals were read only. Finite hulls were scaled in memory by (1.2, 1.0, 0.9); no game assets were written.\n\n"
        +"\n".join(f"- {k}: {v}" for k,v in result["summary"].items())+"\n",encoding="utf-8")
    print(json.dumps(result["summary"]))
    if result["summary"]["failures"] or result["summary"]["unexpected_diff_total"]:raise SystemExit(1)
if __name__=="__main__":main()
