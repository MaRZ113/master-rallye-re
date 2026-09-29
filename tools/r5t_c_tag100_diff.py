#!/usr/bin/env python3
"""Compare course DX tag100 slices using the parsed render boundary."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from master_rallye.tag100_diff import (
    analyze_tag100_diff,
    extract_tag100_from_dx,
    render_tag100_diff_markdown,
)
from master_rallye.errors import MasterRallyeError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline_dx", type=Path, help="validated course DX baseline")
    parser.add_argument("modified_dx", type=Path, help="validated course DX modified output")
    parser.add_argument("--json-out", type=Path, help="optional derived JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="optional Markdown report path")
    parser.add_argument("--normal-tolerance", type=float, default=0.01)
    args = parser.parse_args()
    try:
        baseline = extract_tag100_from_dx(args.baseline_dx)
        modified = extract_tag100_from_dx(args.modified_dx)
        report = analyze_tag100_diff(
            baseline, modified, normal_tolerance=args.normal_tolerance
        )
        markdown = render_tag100_diff_markdown(report)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        if args.markdown_out:
            args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_out.write_text(markdown, encoding="utf-8")
        if not args.json_out and not args.markdown_out:
            print(markdown)
        else:
            print(json.dumps({
                "summary": report["summary"],
                "json_out": str(args.json_out) if args.json_out else None,
                "markdown_out": str(args.markdown_out) if args.markdown_out else None,
            }, indent=2))
    except (OSError, ValueError, MasterRallyeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
