"""Compare two demo-era DX files without using the retail draw parser."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from master_rallye.demo_dx import compare_demo_dx

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / ".research-output" / "r-demo2"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--first", type=Path, required=True)
    ap.add_argument("--second", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True,
                    help="metadata JSON below ignored .research-output/r-demo2")
    args = ap.parse_args()
    first = args.first.resolve(strict=True)
    second = args.second.resolve(strict=True)
    output = args.output.resolve()
    if REPORT_ROOT.resolve() not in output.parents or output.suffix.lower() != ".json":
        ap.error("output must be JSON under .research-output/r-demo2")
    report = compare_demo_dx(first.read_bytes(), second.read_bytes(),
                             first_source=str(first), second_source=str(second))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"],
                      "first_sha256": report["first"]["sha256"],
                      "second_sha256": report["second"]["sha256"]}))


if __name__ == "__main__":
    main()
