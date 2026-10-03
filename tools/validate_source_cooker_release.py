#!/usr/bin/env python3
"""Validate a built Source Cooker release archive."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from build_source_cooker_release import validate_release_zip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Source Cooker release ZIP")
    args = parser.parse_args(argv)
    try:
        members = validate_release_zip(args.archive)
    except (OSError, ValueError) as exc:
        print(f"invalid release: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: {args.archive} ({len(members)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
