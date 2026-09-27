#!/usr/bin/env python3
"""Compare same-source Demo 9.3.1 and 9.10.0 DX outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.cooker_diff import compare_cooker_dx


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rev131_dx", type=Path)
    parser.add_argument("rev135_dx", type=Path)
    parser.add_argument("--source131", type=Path, help="source GXM/GXI used for rev131")
    parser.add_argument("--source135", type=Path, help="source GXM/GXI used for rev135")
    parser.add_argument("--report", type=Path, help="write the JSON report to this path")
    args = parser.parse_args()
    if (args.source131 is None) != (args.source135 is None):
        parser.error("--source131 and --source135 must be supplied together")

    source_hashes = None
    if args.source131 is not None:
        source_hashes = (_file_hash(args.source131), _file_hash(args.source135))
    result = compare_cooker_dx(
        args.rev131_dx.read_bytes(), args.rev135_dx.read_bytes(),
        first_source=str(args.rev131_dx), second_source=str(args.rev135_dx),
        source_hashes=source_hashes,
    )
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    print(
        f"{args.rev131_dx.name} -> {args.rev135_dx.name}: "
        f"geometry={result['geometry_equivalence']['classification']}, "
        f"same-source={result['source_identity']['status']}, "
        f"draws={result['draws'].get('declared_record_count', 'unresolved')}, "
        f"per-record-delta={result['draws'].get('per_record_size_delta', 'unresolved')}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
