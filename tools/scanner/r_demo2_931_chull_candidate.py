"""Build a byte-audited 9.3.1 Trooper $chull +0.10 X candidate in scratch."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from master_rallye.gxm import (  # noqa: E402
    parse_gxm_geometry_prefix_bytes,
    parse_gxm_prefix_bytes,
    parse_gxm_triangle_prefix_bytes,
)
from master_rallye.sidecar import parse_sidecar  # noqa: E402

CORPUS_ID = "demo-9.3.1"
SOURCE_SHA256 = "5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642"
SIDECAR_SHA256 = "66bbce78328eb224ab7170bb2df978116f4f38ade24d689d336a05c23b576779"
EXPECTED_HEADER = (132866, 0, 0, 22, 5937, 2376, 1979, 1353)
EXPECTED_HULL = ("$chull(Trooper)", 1911, 68)
DELTA_X = 0.10
SCRATCH_ROOT = REPO_ROOT / ".research-output" / "r-demo2"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_ranges(offsets: list[int]) -> list[dict[str, int | str]]:
    ranges: list[list[int]] = []
    for offset in offsets:
        if ranges and ranges[-1][1] == offset:
            ranges[-1][1] += 1
        else:
            ranges.append([offset, offset + 1])
    return [{"start": start, "end_exclusive": end,
             "hex_start": f"0x{start:X}", "hex_end_exclusive": f"0x{end:X}"}
            for start, end in ranges]


def _masked_hash(data: bytes, fields: list[tuple[int, int]]) -> str:
    masked = bytearray(data)
    for offset, size in fields:
        masked[offset:offset + size] = bytes(size)
    return sha256(bytes(masked))


def _header_counts(prefix, geometry, triangles) -> dict[str, object]:
    return {
        "header_words": list(prefix.header_words),
        "prefix_kind": prefix.prefix_kind,
        "material_count": len(prefix.materials),
        "vector_a_count": geometry.vector_a_count,
        "vector_b_count": geometry.vector_b_count,
        "triangle_record_count": triangles.record_count,
        "vector_c_count": triangles.vector_c_count,
    }


def build_candidate(data: bytes, sidecar_path: Path, *, source: str = "9.3.1 Trooper car.gxm") -> tuple[bytes, dict]:
    """Translate only the exact sidecar-associated Trooper hull C.x fields."""
    prefix = parse_gxm_prefix_bytes(data, source)
    geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)
    sidecar = parse_sidecar(sidecar_path)
    hulls = [mesh for mesh in sidecar.meshes if mesh.name == "$chull(Trooper)"]
    if len(hulls) != 1 or not sidecar.meshes or sidecar.meshes[-1] != hulls[0]:
        raise ValueError("expected one final $chull(Trooper) sidecar directive")
    hull = hulls[0]
    if sidecar.mesh_span != triangles.record_count:
        raise ValueError("sidecar mesh span does not match GXM triangle-record count")
    if hull.index < 0 or hull.size <= 0 or hull.index + hull.size > triangles.record_count:
        raise ValueError("$chull(Trooper) triangle-record range is outside the GXM")

    hull_indices: set[int] = set()
    body_indices: set[int] = set()
    for record_index in range(triangles.record_count):
        words = struct.unpack_from("<10I", data, triangles.record_offset + record_index * 52)
        target = hull_indices if hull.index <= record_index < hull.index + hull.size else body_indices
        target.update(words[4:7])
    if not hull_indices:
        raise ValueError("$chull(Trooper) has no referenced Vector C positions")
    if hull_indices & body_indices:
        raise ValueError("$chull(Trooper) Vector C positions are shared with other mesh records")

    candidate = bytearray(data)
    allowed_offsets: set[int] = set()
    fields: list[tuple[int, int]] = []
    edits = []
    for index in sorted(hull_indices):
        offset = triangles.vector_c_offset + index * 12
        old = struct.unpack_from("<3f", data, offset)
        replacement_bytes = struct.pack("<f", old[0] + DELTA_X)
        new_x = struct.unpack("<f", replacement_bytes)[0]
        if not math.isfinite(new_x) or replacement_bytes == data[offset:offset + 4]:
            raise ValueError(f"Vector C[{index}].x did not change to a finite float32")
        candidate[offset:offset + 4] = replacement_bytes
        fields.append((offset, 4))
        allowed_offsets.update(range(offset, offset + 4))
        edits.append({
            "vector_c_index": index,
            "x_float_offset": offset,
            "x_float_offset_hex": f"0x{offset:X}",
            "x_bytes_before_hex": data[offset:offset + 4].hex(),
            "x_bytes_after_hex": replacement_bytes.hex(),
            "before_xyz": list(old),
            "after_xyz": [new_x, old[1], old[2]],
            "realized_delta_xyz": [new_x - old[0], 0.0, 0.0],
        })

    candidate_bytes = bytes(candidate)
    if len(candidate_bytes) != len(data):
        raise ValueError("candidate changed file size")
    changed_offsets = [i for i, (old, new) in enumerate(zip(data, candidate_bytes)) if old != new]
    if not changed_offsets or not set(changed_offsets) <= allowed_offsets:
        raise ValueError("byte difference occurred outside selected Vector C.x fields")

    edited_prefix = parse_gxm_prefix_bytes(candidate_bytes, source + " candidate")
    edited_geometry = parse_gxm_geometry_prefix_bytes(candidate_bytes, edited_prefix)
    edited_triangles = parse_gxm_triangle_prefix_bytes(candidate_bytes, edited_prefix, edited_geometry)
    if (edited_prefix.header_words != prefix.header_words or
            edited_prefix.materials != prefix.materials or
            edited_geometry != geometry or
            edited_triangles.record_offset != triangles.record_offset or
            edited_triangles.record_count != triangles.record_count or
            edited_triangles.vector_c_offset != triangles.vector_c_offset or
            edited_triangles.hierarchy_offset != triangles.hierarchy_offset):
        raise ValueError("candidate changed parsed GXM structure or offsets")
    if data[:triangles.vector_c_offset] != candidate_bytes[:triangles.vector_c_offset]:
        raise ValueError("candidate changed bytes before the Vector C array")
    if data[triangles.hierarchy_offset:] != candidate_bytes[triangles.hierarchy_offset:]:
        raise ValueError("candidate changed hierarchy or tail bytes")
    for index in range(triangles.vector_c_count):
        offset = triangles.vector_c_offset + index * 12
        if index not in hull_indices and data[offset:offset + 12] != candidate_bytes[offset:offset + 12]:
            raise ValueError(f"candidate changed non-hull Vector C[{index}]")
        if data[offset + 4:offset + 12] != candidate_bytes[offset + 4:offset + 12]:
            raise ValueError(f"candidate changed Vector C[{index}].y/z")

    masked_before = _masked_hash(data, fields)
    masked_after = _masked_hash(candidate_bytes, fields)
    if masked_before != masked_after:
        raise ValueError("non-target bytes differ after masking approved C.x fields")
    report = {
        "schema": "r-demo2.8-931-chull-candidate-v1",
        "corpus_id": CORPUS_ID,
        "status": "CANDIDATE_PREPARED_RUNTIME_UNTESTED",
        "source_sha256": sha256(data),
        "candidate_sha256": sha256(candidate_bytes),
        "source_size": len(data),
        "candidate_size": len(candidate_bytes),
        "file_size_unchanged": len(data) == len(candidate_bytes),
        "gxm": _header_counts(prefix, geometry, triangles),
        "offsets": {
            "vector_a": geometry.vector_a_offset,
            "vector_b": geometry.vector_b_offset,
            "triangle_records": triangles.record_offset,
            "vector_c": triangles.vector_c_offset,
            "hierarchy_tail": triangles.hierarchy_offset,
        },
        "chull": {
            "directive": hull.name,
            "triangle_record_start": hull.index,
            "triangle_record_end_exclusive": hull.index + hull.size,
            "triangle_record_count": hull.size,
            "gxm_triangle_record_count": triangles.record_count,
            "unique_vector_c_indices": sorted(hull_indices),
            "unique_vector_c_count": len(hull_indices),
            "overlap_with_other_mesh_vector_c_indices": sorted(hull_indices & body_indices),
        },
        "translation_source_xyz": [DELTA_X, 0.0, 0.0],
        "modified_vector_count": len(edits),
        "edited_vector_c_x_fields": edits,
        "changed_byte_count": len(changed_offsets),
        "changed_byte_offsets": changed_offsets,
        "changed_byte_ranges_end_exclusive": changed_ranges(changed_offsets),
        "allowed_target_x_field_ranges_end_exclusive": [
            {"start": offset, "end_exclusive": offset + size,
             "hex_start": f"0x{offset:X}", "hex_end_exclusive": f"0x{offset + size:X}"}
            for offset, size in fields
        ],
        "non_target_bytes_identical": True,
        "masked_source_sha256": masked_before,
        "masked_candidate_sha256": masked_after,
        "vector_a_b_material_triangle_hierarchy_bytes_unchanged": True,
        "native_plane_replay": {
            "status": "NOT_RUN_UNSUPPORTED_FOR_9_3_1",
            "reason": "The available R-DEMO2.7 native-style replay pins demo-8.4.1 GXM and EXE hashes; no validated 9.3.1 replay exists.",
        },
    }
    return candidate_bytes, report


def render_report(report: dict, *, source_path: Path, sidecar_path: Path, candidate_path: Path) -> str:
    hull = report["chull"]
    lines = [
        "# Demo 9.3.1 Trooper `$chull` +0.10 X candidate",
        "",
        "Status: **candidate prepared; runtime cooking not yet performed**.",
        "",
        "## Input and candidate",
        "",
        f"- Original GXM: `{source_path}`",
        f"- Original GXM SHA256: `{report['source_sha256']}` ({report['source_size']} bytes)",
        f"- Sidecar: `{sidecar_path}`",
        f"- Candidate: `{candidate_path}`",
        f"- Candidate SHA256: `{report['candidate_sha256']}` ({report['candidate_size']} bytes)",
        "",
        "## Parsed hull and edit",
        "",
        f"- Header words: `{report['gxm']['header_words']}`",
        f"- Counts: materials={report['gxm']['material_count']}, Vector A={report['gxm']['vector_a_count']}, Vector B={report['gxm']['vector_b_count']}, triangle records={report['gxm']['triangle_record_count']}, Vector C={report['gxm']['vector_c_count']}.",
        f"- Directive: `{hull['directive']}`, records `[ {hull['triangle_record_start']}, {hull['triangle_record_end_exclusive']} )` ({hull['triangle_record_count']} records).",
        f"- Derived unique Vector C positions ({hull['unique_vector_c_count']}): `{hull['unique_vector_c_indices']}`.",
        f"- Modified vectors: {report['modified_vector_count']}; translation in GXM source coordinates: `{report['translation_source_xyz']}`.",
        "- Only the selected Vector C X float32 fields changed. Vector A/B, materials, triangle records and order, winding, hierarchy/tail, Y/Z components, and file layout were byte-preserved.",
        "",
        "## Byte audit",
        "",
        f"- Changed bytes: {report['changed_byte_count']}.",
        "- Exact differing byte ranges (end offsets exclusive):",
    ]
    lines.extend(f"  - `[0x{item['start']:X}, 0x{item['end_exclusive']:X})` ({item['end_exclusive'] - item['start']} bytes)" for item in report["changed_byte_ranges_end_exclusive"])
    lines.extend([
        "- Exact differing byte offsets: `" + ", ".join(f"0x{offset:X}" for offset in report["changed_byte_offsets"]) + "`.",
        "- Masked source/candidate SHA256: `" + report["masked_source_sha256"] + "` / `" + report["masked_candidate_sha256"] + "` (equal after zeroing only approved C.x fields).",
        "",
        "## Native-style plane replay",
        "",
        "Not run. The available replay is pinned to demo 8.4.1 source and executable hashes; it does not support this 9.3.1 corpus safely. No 9.3.1 decision-signature result is claimed.",
        "",
        "## Runtime and DX oracle results",
        "",
        "Pending human runtime cooking. See `r-demo2.8-931-chull-oracle.md` for the three-DX procedure. The candidate is not runtime-confirmed.",
        "",
        "### Runtime result placeholder",
        "",
        "- Baseline A/B byte identity: pending.",
        "- Modified DX SHA256 and size: pending.",
        "- Render/collision semantic comparison: pending.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gxm", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="ignored output directory below this repository's .research-output/r-demo2")
    args = parser.parse_args()
    source = args.gxm.resolve(strict=True)
    sidecar = args.sidecar.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    scratch = SCRATCH_ROOT.resolve()
    if scratch not in output_dir.parents:
        parser.error("--output-dir must be below ignored .research-output/r-demo2")
    if source.parent != sidecar.parent or source.name.casefold() != "car.gxm" or sidecar.name.casefold() != "trooper.txt":
        parser.error("the exact same-build car.gxm and Trooper.txt siblings are required")
    source_bytes = source.read_bytes()
    sidecar_bytes = sidecar.read_bytes()
    if sha256(source_bytes) != SOURCE_SHA256:
        parser.error("source GXM SHA256 does not match the pinned demo-9.3.1 original")
    if sha256(sidecar_bytes) != SIDECAR_SHA256:
        parser.error("Trooper.txt SHA256 does not match the pinned demo-9.3.1 sidecar")
    prefix = parse_gxm_prefix_bytes(source_bytes, str(source))
    geometry = parse_gxm_geometry_prefix_bytes(source_bytes, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(source_bytes, prefix, geometry)
    sidecar_model = parse_sidecar(sidecar)
    hulls = [mesh for mesh in sidecar_model.meshes if mesh.name == "$chull(Trooper)"]
    if (prefix.header_words != EXPECTED_HEADER or len(hulls) != 1 or
            (hulls[0].name, hulls[0].index, hulls[0].size) != EXPECTED_HULL or
            triangles.record_count != 1979 or triangles.vector_c_count != 1353):
        parser.error("parsed 9.3.1 source layout differs from the reviewed candidate target")
    target_names = ("trooper-931-chull-xplus010.gxm",
                    "trooper-931-chull-xplus010-audit.json",
                    "trooper-931-chull-xplus010-report.md")
    targets = [output_dir / name for name in target_names]
    if any(path.exists() for path in targets):
        parser.error("refusing to overwrite an existing candidate or audit artifact")
    candidate, report = build_candidate(source_bytes, sidecar, source=str(source))
    derived_indices = report["chull"]["unique_vector_c_indices"]
    if derived_indices != list(range(1317, 1353)):
        parser.error("derived 9.3.1 hull Vector C set differs from the reviewed set")
    report.update({
        "source_path": str(source),
        "sidecar_path": str(sidecar),
        "sidecar_sha256": sha256(sidecar_bytes),
        "candidate_path": str(targets[0]),
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    targets[0].write_bytes(candidate)
    targets[1].write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    targets[2].write_text(render_report(report, source_path=source, sidecar_path=sidecar,
                                        candidate_path=targets[0]), encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("source_sha256", "candidate_sha256", "source_size", "changed_byte_count",
                       "modified_vector_count", "changed_byte_ranges_end_exclusive", "status")}, indent=2))


if __name__ == "__main__":
    main()
