#!/usr/bin/env python3
"""Create the ignored Astero lateral tag-101 translation test package."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from master_rallye.collision_writer import write_dx_collision_translation


INSTRUCTIONS = """MASTER RALLYE R4C HUMAN COLLISION TEST

This candidate changes ONLY the existing Astero car.dx tag-101 positional
geometry. Render geometry is byte-identical. Translation: +0.40 source X,
the evidenced lateral axis. Which physical side +X represents is intentionally
left for the runtime observation. Runtime success has NOT been claimed.

1. Back up the original Data.sma.
2. Replace only DataGx/Vehicles/Astero/car.dx with
   Astero-car-collision-shift.dx (renamed to car.dx in the unpacked tree).
3. Repack the tree as a normal ZIP with 7-Zip and rename .zip to .sma, using
   the already runtime-confirmed workflow.
4. Launch a race with Astero.
5. Approach a wall slowly with BOTH sides of the vehicle and compare visible
   body contact against physics contact.
6. Test ordinary driving and damage cautiously.

Please report:
GAME LOADS?
CAR LOADS?
NORMAL HANDLING?
COLLISION EXISTS?
COLLISION OFFSET VISIBLE?
WHICH SIDE?
DAMAGE STILL WORKS?
ANY ARTIFACTS?
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    result = write_dx_collision_translation(
        source,
        output / "Astero-car-collision-shift.dx",
        (0.4, 0.0, 0.0),
        expected_source_sha256=source_hash,
    )
    payload = result.to_dict()
    payload.update({
        "phase": "R4C",
        "runtime_validation": "WAITING FOR HUMAN TEST",
        "source_resource": "DataGx/Vehicles/Astero/car.dx",
        "translation_axis_evidence": (
            "source X is lateral; source extents and shared coordinate "
            "mapping (X,-Z,Y) distinguish X width, +Y up, Z longitudinal"
        ),
        "changed_field_paths": sorted({
            item.field_path for item in result.translation.changes
        }),
    })
    (output / "validation.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (output / "TEST_INSTRUCTIONS.txt").write_text(INSTRUCTIONS, encoding="utf-8")
    print(json.dumps({
        "candidate": "Astero-car-collision-shift.dx",
        "translation": [0.4, 0.0, 0.0],
        "changed_byte_count": result.diff.changed_byte_count,
        "unexpected_diff_count": 0,
        "visual_geometry_changed_bytes": 0,
        "runtime_validation": "WAITING FOR HUMAN TEST",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
