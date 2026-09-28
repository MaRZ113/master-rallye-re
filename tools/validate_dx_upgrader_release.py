#!/usr/bin/env python3
"""Validate the curated standalone Master Rallye DX Upgrader ZIP."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_dx_upgrader_release import validate_release_zip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="release ZIP to validate")
    args = parser.parse_args(argv)
    members = validate_release_zip(args.archive)
    digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    print(f"Release validation: PASS ({len(members)} files)")
    print(f"SHA256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
