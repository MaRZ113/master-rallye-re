#!/usr/bin/env python3
"""Generate the read-only R-PHYS2.1 named-family config coverage audit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.vehicle_config_analysis import parse_vehicle_config  # noqa: E402
from master_rallye.vehicle_family_broker import (  # noqa: E402
    build_family_config_report,
    write_family_config_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora-root", type=Path, required=True,
                        help="read-only root containing the retail corpus")
    parser.add_argument("--output-dir", type=Path, default=Path(".research-output/r-phys2.1/config"),
                        help="ignored output directory")
    args = parser.parse_args()

    retail_data = args.corpora_root / "retail" / "Data.sma_unpacked" / "DataGame"
    vehicle_config = parse_vehicle_config(retail_data / "vehicles.xml", build="retail")
    modifications_config = parse_vehicle_config(retail_data / "Modifications.xml", build="retail")
    report = build_family_config_report(vehicle_config, modifications_config)
    json_path, markdown_path = write_family_config_report(report, args.output_dir)
    print(json.dumps({
        "json": str(json_path),
        "markdown": str(markdown_path),
        "families": [
            {
                "name": row["family_name"],
                "config": row["family_config_present"],
                "type_ids": row["family_type_ids"],
                "base_fields": row["base_field_count"],
                "missing_base_groups": row["missing_base_groups"],
                "player1_overlay_missing": row["player1_missing_modification_fields"],
                "player2_overlay_missing": row["player2_missing_modification_fields"],
            }
            for row in report["families"]
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
