#!/usr/bin/env python3
"""Byte-exact validation of the conservative template-preserving DXT writer."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.dxt import (
    decode_rgba_pixels,
    encode_dxt_pixels,
    has_transparency,
    parse_dxt,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(root: Path) -> dict:
    root = root.resolve()
    files = sorted(root.rglob("*.dxt"), key=lambda path: path.as_posix().casefold())
    records = []
    dimension_counts = Counter()
    family_counts = Counter()
    identical = 0
    header_differences = 0
    payload_differences = 0

    for path in files:
        original = path.read_bytes()
        texture = parse_dxt(path)
        upright_rgba = decode_rgba_pixels(texture)
        rebuilt = encode_dxt_pixels(
            texture,
            upright_rgba,
            texture.width,
            texture.height,
        )
        equal = rebuilt == original
        identical += int(equal)
        header_equal = rebuilt[:20] == original[:20]
        payload_equal = rebuilt[20:] == original[20:]
        header_differences += int(not header_equal)
        payload_differences += int(not payload_equal)
        dimension_counts[f"{texture.width}x{texture.height}"] += 1
        family = path.parent.name
        family_counts[family] += 1
        records.append({
            "path": path.relative_to(root).as_posix(),
            "family": family,
            "width": texture.width,
            "height": texture.height,
            "has_nonopaque_alpha": has_transparency(texture),
            "byte_size": len(original),
            "header_equal": header_equal,
            "payload_equal": payload_equal,
            "byte_identical": equal,
            "original_sha256": sha256(original),
            "rebuilt_sha256": sha256(rebuilt),
        })

    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_descriptor": "external read-only vehicle DXT tree (path omitted)",
        "pipeline": [
            "parse exact 20-byte header and stored BGRA plane",
            "convert stored bottom-up BGRA to upright RGBA",
            "convert upright RGBA to stored bottom-up BGRA",
            "prepend exact template header",
            "compare complete bytes and SHA-256",
        ],
        "summary": {
            "sample_count": len(records),
            "byte_identical": identical,
            "non_identical": len(records) - identical,
            "header_differences": header_differences,
            "payload_differences": payload_differences,
            "families": len(family_counts),
            "textures_with_nonopaque_alpha": sum(
                item["has_nonopaque_alpha"] for item in records
            ),
            "dimension_counts": dict(sorted(dimension_counts.items())),
            "family_counts": dict(sorted(family_counts.items())),
        },
        "files": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    report = validate(args.root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = report["summary"]
    print(
        f"DXT round-trip: {summary['byte_identical']}/{summary['sample_count']} "
        f"byte-identical; header differences {summary['header_differences']}; "
        f"payload differences {summary['payload_differences']}"
    )
    return 0 if summary["non_identical"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
