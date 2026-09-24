"""Prepare one fail-closed GXM vector-C edit in an ignored scratch tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from master_rallye.gxm import (
    parse_gxm_prefix_bytes, parse_gxm_geometry_prefix_bytes,
    parse_gxm_triangle_prefix_bytes,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--relative-output", type=Path, required=True)
    parser.add_argument("--vector-index", type=int, required=True)
    parser.add_argument("--axis", type=int, choices=(0, 1, 2), required=True)
    parser.add_argument("--delta", type=float, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    scratch = args.scratch_root.resolve()
    output = (scratch / args.relative_output).resolve()
    if source == output or source in scratch.parents or scratch == source or scratch not in output.parents:
        raise SystemExit("scratch output must be separate from source and stay within scratch root")
    if output.exists():
        raise SystemExit("refusing to overwrite existing scratch candidate")
    data = source.read_bytes()
    if sha256(data) != args.expected_sha256.lower():
        raise SystemExit("source SHA256 differs from manifest")
    prefix = parse_gxm_prefix_bytes(data, str(source))
    geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)
    if not 0 <= args.vector_index < triangles.vector_c_count:
        raise SystemExit("vector index out of range")
    if not math.isfinite(args.delta) or abs(args.delta) > 0.25 or args.delta == 0:
        raise SystemExit("delta must be finite, nonzero, and no larger than 0.25")
    references = 0
    for index in range(triangles.record_count):
        values = struct.unpack_from("<10I", data, triangles.record_offset + index * 52)
        references += values[4:7].count(args.vector_index)
    if references < 2:
        raise SystemExit("selected vector is not referenced by at least two triangle records")
    offset = triangles.vector_c_offset + args.vector_index * 12 + args.axis * 4
    old = struct.unpack_from("<f", data, offset)[0]
    replacement = struct.pack("<f", old + args.delta)
    if replacement == data[offset:offset + 4]:
        raise SystemExit("float32 value would not change")
    candidate = bytearray(data)
    candidate[offset:offset + 4] = replacement
    candidate = bytes(candidate)
    edited_prefix = parse_gxm_prefix_bytes(candidate, str(output))
    edited_geometry = parse_gxm_geometry_prefix_bytes(candidate, edited_prefix)
    edited_triangles = parse_gxm_triangle_prefix_bytes(candidate, edited_prefix, edited_geometry)
    if (prefix.header_words != edited_prefix.header_words or
        prefix.materials != edited_prefix.materials or
        geometry.vector_a_offset != edited_geometry.vector_a_offset or
        triangles.record_offset != edited_triangles.record_offset or
        triangles.record_count != edited_triangles.record_count):
        raise SystemExit("structural metadata changed")
    changed = [index for index, (a, b) in enumerate(zip(data, candidate)) if a != b]
    if not changed or any(index < offset or index >= offset + 4 for index in changed):
        raise SystemExit("unexpected byte difference")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    report = {"source_sha256": sha256(data), "candidate_sha256": sha256(candidate),
              "source_size": len(data), "candidate_size": len(candidate),
              "vector_c_index": args.vector_index, "axis": args.axis,
              "references_by_triangle_records": references,
              "float_offset": offset, "old_value": old,
              "new_value": struct.unpack("<f", replacement)[0],
              "changed_byte_offsets": changed,
              "status": "STRUCTURAL_CANDIDATE_ONLY; runtime untested"}
    output.with_suffix(output.suffix + ".audit.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
