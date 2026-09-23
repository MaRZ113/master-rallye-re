#!/usr/bin/env python3
"""Dry-run zero-edit R4F rebuild of every protected original vehicle DX."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from master_rallye.dx import parse_dx_bytes
from master_rallye.errors import DxWriteError
from master_rallye.topology_writer import rebuild_topology


def run(root: Path) -> dict:
    rows=[]
    for source in sorted(root.rglob("*.dx")):
        name=source.relative_to(root).as_posix()
        row={"resource":name,"parse":False,"rebuild":False,"reparse":False,
             "semantic_equivalent":False,"byte_identical":False,"blocked":False,"failed":False}
        try:
            data=source.read_bytes()
            model=parse_dx_bytes(data)
            row["parse"]=model.diagnostics.validated
            result=rebuild_topology(data)
            row.update(rebuild=True,reparse=result.output_model.diagnostics.validated,
                       semantic_equivalent=result.semantic_equivalent,byte_identical=result.byte_identical,
                       source_core_end=result.source_core_end,output_core_end=result.output_core_end)
        except DxWriteError as error:
            row["blocked"]=True
            row["error"]=str(error)
        except Exception as error:
            row["failed"]=True
            row["error"]=str(error)
        rows.append(row)
    summary={"total":len(rows)}
    for key in ("parse","rebuild","reparse","semantic_equivalent","byte_identical","blocked","failed"):
        summary["parsed" if key=="parse" else "rebuilt" if key=="rebuild" else "reparsed" if key=="reparse" else key]=sum(bool(row[key]) for row in rows)
    return {"summary":summary,"resources":rows}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("vehicle_root",type=Path)
    parser.add_argument("--json",type=Path,required=True)
    parser.add_argument("--markdown",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.vehicle_root.resolve())
    args.json.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    summary=report["summary"]
    args.markdown.write_text(
        "# R4F zero-edit render-core rebuild corpus\n\n"
        "Protected original vehicle DX files were parsed, rebuilt in memory, reparsed and compared. No game bytes were saved.\n\n"
        + ", ".join(f"{key}: {value}" for key,value in summary.items())
        + ". Details and any blockers are in `rebuild-corpus.json`.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary))
    if any(row["blocked"] or not row["reparse"] or not row["semantic_equivalent"] for row in report["resources"]):
        raise SystemExit(1)


if __name__=="__main__":
    main()
