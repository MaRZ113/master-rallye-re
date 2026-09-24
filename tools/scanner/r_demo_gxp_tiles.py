"""Audit same-build GXP to tiled DXT byte correspondence in demo 9.3.1.

Only metadata and hashes are emitted. The input corpus is read-only and the
output directory must be disjoint from it.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

from master_rallye.dxt import parse_dxt_bytes
from master_rallye.gxp import gxp_tile_bgra, parse_gxp

CORPUS_ID = "demo-9.3.1"


def inspect_source(root: Path, path: Path) -> dict:
    relative = path.relative_to(root).as_posix()
    image = parse_gxp(path)
    pattern = re.compile(re.escape(path.stem) + r"_000_(\d{3})\.dxt", re.IGNORECASE)
    candidates = []
    for sibling in path.parent.iterdir():
        hit = pattern.fullmatch(sibling.name)
        if sibling.is_file() and hit:
            candidates.append((int(hit.group(1)), sibling))
    candidates.sort()
    row = {"corpus_id": CORPUS_ID, "relative_path": relative,
           "width": image.width, "height": image.height,
           "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
           "tile_count": len(candidates), "tiles": []}
    if not candidates:
        row["status"] = "no_same_stem_tiled_dxt"
        return row
    numbers = [number for number, _ in candidates]
    if numbers != list(range(len(numbers))):
        row["status"] = "noncontiguous_tile_numbers"
        return row

    x = y = row_height = 0
    for number, target in candidates:
        if x >= image.width:
            x = 0
            y += row_height
            row_height = 0
        target_relative = target.relative_to(root).as_posix()
        data = target.read_bytes()
        dxt = parse_dxt_bytes(data, f"{CORPUS_ID}:{target_relative}")
        if y >= image.height:
            row["status"] = "tile_outside_source"
            return row
        payload = gxp_tile_bgra(image, x, y, dxt.width, dxt.height)
        expected = (struct.pack("<5I", 0x0000FEED, 1, zlib.crc32(payload) & 0xFFFFFFFF,
                                dxt.width, dxt.height) + payload)
        tile = {"corpus_id": CORPUS_ID, "relative_path": target_relative,
                "tile_index": number, "x": x, "y": y,
                "width": dxt.width, "height": dxt.height,
                "sha256": hashlib.sha256(data).hexdigest(),
                "payload_identical": payload == dxt.bgra,
                "complete_identical": expected == data}
        row["tiles"].append(tile)
        x += dxt.width
        row_height = max(row_height, dxt.height)
    row["covered_source"] = x >= image.width and y + row_height >= image.height
    row["status"] = ("all_tiles_byte_identical" if row["covered_source"] and
                     all(t["complete_identical"] for t in row["tiles"])
                     else "incomplete_or_mismatch")
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo-9", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.demo_9.resolve()
    output = args.output.resolve()
    if not root.is_dir() or root == output or root in output.parents or output in root.parents:
        raise SystemExit("corpus root must exist and may not overlap output")
    output.mkdir(parents=True, exist_ok=True)
    rows = [inspect_source(root, path) for path in sorted(root.rglob("*.gxp"))]
    counts = collections.Counter(row["status"] for row in rows)
    tile_count = sum(row["tile_count"] for row in rows)
    result = {"corpus_id": CORPUS_ID, "files": rows, "status_counts": dict(counts),
              "total_dxt_tiles": tile_count}
    (output / "gxp-dxt-tiles.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# GXP to tiled DXT correspondence", "",
             f"Corpus: `{CORPUS_ID}`. GXP files: {len(rows)}; DXT tile candidates: {tile_count}.",
             "", "Candidate rule: same folder and case-insensitive `<GXP stem>_000_NNN.dxt` with contiguous numbering. Tiles are laid left to right until their widths cover the source width, then continue on the next row. The source rectangle is converted from top-down RGBA to bottom-up BGRA within each tile; unused right and top tile pixels are zero. Complete DXT headers and CRC32 are checked.",
             "", "| Status | GXP files |", "|---|---:|"]
    for status, count in sorted(counts.items()):
        lines.append(f"| {status} | {count} |")
    lines += ["", "## GXP without same-stem DXT tiles", ""]
    lines += [f"- `{CORPUS_ID}:{row['relative_path']}`" for row in rows if not row["tile_count"]]
    lines += ["", "This is **CONFIRMED_BY_BYTES** for the paired files and does not establish whether the game generates or loads the tiles at runtime. Per-file source and tile SHA256, dimensions, offsets, and comparison status are in `gxp-dxt-tiles.json`.", ""]
    (output / "gxp-dxt-tiles.md").write_text("\n".join(lines), encoding="utf-8")
    print("GXP", len(rows), "DXT tiles", tile_count, "statuses", dict(counts))


if __name__ == "__main__":
    main()
