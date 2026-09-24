"""Prepare a fail-closed Trooper GXM $chull-only translation in ignored scratch."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from master_rallye.gxm import (parse_gxm_prefix_bytes,
                                parse_gxm_geometry_prefix_bytes,
                                parse_gxm_triangle_prefix_bytes)
from master_rallye.sidecar import parse_sidecar


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_relative(root: Path, relative: Path) -> Path:
    if relative.is_absolute():
        raise ValueError("corpus path must be relative")
    path = (root / relative).resolve(strict=True)
    if root not in path.parents:
        raise ValueError("corpus path escaped root")
    return path


def changed_ranges(before: bytes, after: bytes) -> list[list[int]]:
    if len(before) != len(after):
        raise ValueError("candidate changed file length")
    differences = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    ranges = []
    for offset in differences:
        if ranges and ranges[-1][1] == offset:
            ranges[-1][1] += 1
        else:
            ranges.append([offset, offset + 1])
    return ranges


def build_candidate(data: bytes, sidecar_path: Path, dx_data: bytes,
                    delta_x: float, source: str) -> tuple[bytes, dict]:
    if not math.isfinite(delta_x) or not 0.1 <= abs(delta_x) <= 0.6:
        raise ValueError("lateral delta must be finite, nonzero, and 0.1..0.6")
    prefix = parse_gxm_prefix_bytes(data, source)
    geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)
    sidecar = parse_sidecar(sidecar_path)
    hulls = [mesh for mesh in sidecar.meshes if mesh.name == "$chull(Trooper)"]
    if len(hulls) != 1 or not sidecar.meshes or sidecar.meshes[-1] != hulls[0]:
        raise ValueError("expected one final Trooper $chull mesh")
    hull = hulls[0]
    if sidecar.mesh_span != triangles.record_count or hull.index + hull.size != triangles.record_count:
        raise ValueError("sidecar and GXM record spans disagree")
    if (hull.index, hull.size, triangles.record_count) != (1911, 68, 1979):
        raise ValueError("unrecognized Trooper hull record range")
    body_refs = set()
    hull_refs = set()
    for record_index in range(triangles.record_count):
        record = struct.unpack_from("<10I", data, triangles.record_offset + record_index * 52)
        (hull_refs if hull.index <= record_index < hull.index + hull.size else body_refs).update(record[4:7])
    if hull_refs & body_refs or len(hull_refs) != 36 or sorted(hull_refs) != list(range(1317, 1353)):
        raise ValueError("hull positions are shared or differ from the audited Trooper source")

    if len(dx_data) < 16 or struct.unpack_from("<I", dx_data)[0] != 0xD00D:
        raise ValueError("paired demo DX header is invalid")
    dx_count = struct.unpack_from("<I", dx_data, 12)[0]
    if not 0 < dx_count <= 100000 or 16 + dx_count * 12 > len(dx_data):
        raise ValueError("paired demo DX leading position array is invalid")
    dx_positions = {tuple(round(x, 4) for x in struct.unpack_from("<3f", dx_data, 16 + i * 12))
                    for i in range(dx_count)}
    def source_position(index: int) -> tuple[float, float, float]:
        return struct.unpack_from("<3f", data, triangles.vector_c_offset + 12 * index)
    def dx_axis(point: tuple[float, float, float]) -> tuple[float, float, float]:
        return (round(point[0], 4), round(point[2], 4), round(-point[1], 4))
    hull_dx_matches = sum(dx_axis(source_position(i)) in dx_positions for i in hull_refs)
    body_dx_matches = sum(dx_axis(source_position(i)) in dx_positions for i in body_refs)
    if hull_dx_matches or body_dx_matches < 1000:
        raise ValueError("same-build leading DX position cross-check differs")

    candidate = bytearray(data)
    allowed_offsets = set()
    changes = []
    for index in sorted(hull_refs):
        offset = triangles.vector_c_offset + 12 * index
        old = source_position(index)
        new_x_bytes = struct.pack("<f", old[0] + delta_x)
        new_x = struct.unpack("<f", new_x_bytes)[0]
        if new_x_bytes == data[offset:offset + 4]:
            raise ValueError("a hull coordinate did not change")
        candidate[offset:offset + 4] = new_x_bytes
        allowed_offsets.update(range(offset, offset + 4))
        changes.append({"vector_c_index": index, "float_offset": offset,
                        "before": list(old), "after": [new_x, old[1], old[2]]})
    candidate = bytes(candidate)
    actual_changed = {i for i, (a, b) in enumerate(zip(data, candidate)) if a != b}
    if not actual_changed or not actual_changed <= allowed_offsets or len(candidate) != len(data):
        raise ValueError("candidate changed unexpected bytes")
    new_prefix = parse_gxm_prefix_bytes(candidate, source + " candidate")
    new_geometry = parse_gxm_geometry_prefix_bytes(candidate, new_prefix)
    new_triangles = parse_gxm_triangle_prefix_bytes(candidate, new_prefix, new_geometry)
    if (new_prefix.header_words != prefix.header_words or
        new_prefix.materials != prefix.materials or
        new_geometry.vector_a_offset != geometry.vector_a_offset or
        new_triangles.record_offset != triangles.record_offset or
        new_triangles.record_count != triangles.record_count or
        new_triangles.hierarchy_offset != triangles.hierarchy_offset or
        candidate[triangles.hierarchy_offset:] != data[triangles.hierarchy_offset:]):
        raise ValueError("GXM structure or hierarchy changed")
    report = {"source_sha256": sha(data), "candidate_sha256": sha(candidate),
              "source_size": len(data), "candidate_size": len(candidate),
              "chull_mesh_name": hull.name, "chull_record_start": hull.index,
              "chull_record_count": hull.size, "chull_vector_c_indices": sorted(hull_refs),
              "edited_vertex_count": len(changes), "translation_source_xyz": [delta_x, 0.0, 0.0],
              "body_position_index_overlap": len(hull_refs & body_refs),
              "body_dx_leading_position_matches": body_dx_matches,
              "chull_dx_leading_position_matches": hull_dx_matches,
              "changed_byte_count": len(actual_changed),
              "changed_byte_ranges_end_exclusive": changed_ranges(data, candidate),
              "edited_vertices": changes,
              "status": "STRUCTURAL_CANDIDATE_ONLY_RUNTIME_UNTESTED"}
    return candidate, report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus-root", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True, help="car.gxm path relative to corpus")
    ap.add_argument("--sidecar", type=Path, required=True, help="Trooper.txt path relative to corpus")
    ap.add_argument("--paired-dx", type=Path, required=True, help="car.dx path relative to corpus")
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--scratch-root", type=Path, required=True)
    ap.add_argument("--relative-output", type=Path, required=True)
    ap.add_argument("--delta-x", type=float, default=0.4)
    args = ap.parse_args()
    root = args.corpus_root.resolve(strict=True)
    scratch = args.scratch_root.resolve()
    if root == scratch or root in scratch.parents or scratch in root.parents:
        raise SystemExit("corpus and scratch roots must be disjoint")
    source = checked_relative(root, args.source)
    sidecar = checked_relative(root, args.sidecar)
    dx = checked_relative(root, args.paired_dx)
    if source.parent != sidecar.parent or source.parent != dx.parent:
        raise SystemExit("Trooper source, sidecar and paired DX must be same-build siblings")
    if source.name.lower() != "car.gxm" or dx.name.lower() != "car.dx":
        raise SystemExit("candidate is restricted to Trooper car resources")
    output = (scratch / args.relative_output).resolve()
    if scratch not in output.parents or output.exists() or output.suffix.lower() != ".gxm":
        raise SystemExit("new .gxm output must stay under scratch root")
    data = source.read_bytes()
    if sha(data) != args.expected_sha256.lower():
        raise SystemExit("source hash differs from expected manifest")
    candidate, report = build_candidate(data, sidecar, dx.read_bytes(), args.delta_x,
                                         "demo-8.4.1:" + args.source.as_posix())
    report.update({"corpus_id": "demo-8.4.1", "relative_path": args.source.as_posix(),
                   "sidecar_relative_path": args.sidecar.as_posix(),
                   "paired_dx_relative_path": args.paired_dx.as_posix(),
                   "paired_dx_sha256": sha(dx.read_bytes()),
                   "scratch_relative_path": args.relative_output.as_posix()})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    output.with_suffix(".audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("source_sha256", "candidate_sha256", "edited_vertex_count",
                       "changed_byte_count", "body_position_index_overlap", "status")}, indent=2))


if __name__ == "__main__":
    main()
