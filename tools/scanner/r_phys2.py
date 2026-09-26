#!/usr/bin/env python3
"""Build a read-only R-PHYS2 corpus, executable-xref, and identity audit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.vehicle_runtime_identity import (  # noqa: E402
    analyze_vehicle_runtime_identity,
    write_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora-root", type=Path, required=True,
                        help="read-only root containing demo-8.4.1, demo-9.3.1, demo-9.10.0, retail")
    parser.add_argument("--rphys1-analysis", type=Path, required=True,
                        help="existing ignored R-PHYS1 machine report")
    parser.add_argument("--ghidra-xrefs", type=Path,
                        help="optional Ghidra vehicle-string-xref JSON report")
    parser.add_argument("--output-dir", type=Path, default=Path(".research-output/r-phys2"),
                        help="ignored output directory")
    args = parser.parse_args()
    result = analyze_vehicle_runtime_identity(
        args.corpora_root, args.rphys1_analysis, args.ghidra_xrefs
    )
    write_outputs(result, args.output_dir)
    scan = result["text_and_metadata_scan"]
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "text_files_scanned": scan["text_file_count"],
        "compiled_metadata_files_scanned": scan["compiled_metadata_file_count"],
        "matching_source_files": scan["hit_file_count"],
        "hit_category_counts": scan["hit_category_counts"],
        "trooper_9_10_to_retail": result["trooper_config_survival"].get("status_counts"),
        "runtime_binding_status": result["identity_layers"]["runtime_physics_object"]["status"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
