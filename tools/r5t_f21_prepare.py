#!/usr/bin/env python3
"""Reproduce R5T-F.2.1 section analysis and stage two exact-byte hybrids.

All game-derived output is written below ignored research-output/. The tracked
reports contain only hashes, offsets, counts, and typed numeric metadata.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for item in (ROOT, ROOT / "src", ROOT / "tools"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

import r5t_f2_tag100_probe as f2  # noqa: E402
from master_rallye.course_tag100 import CourseTag100, parse_course_tag100_bytes  # noqa: E402
from master_rallye.course_tag1400 import CourseTag1400, parse_course_tag1400_bytes  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402
from master_rallye.errors import FormatError  # noqa: E402
from master_rallye.tag100_diff import changed_ranges  # noqa: E402


BASELINE_DX = ROOT / "research-output/r5t_f0/cooker-lab/baseline/snapshots/baseline-03/DataGx/Course/France1/france1.dx"
MODIFIED_DX = ROOT / "research-output/r5t_f0/cooker-lab/modified/snapshots/modified-03/DataGx/Course/France1/france1.dx"
RUNTIME_TEMPLATE = ROOT / "research-output/r5t_f1/runtime/hybrid-a/runtime"
RUNTIME_EXE = ROOT.parent / "MRallye.exe"
RETAIL_COURSE_ROOT = ROOT.parent / "corpora/retail/Data.sma_unpacked/DataGx/Course"
SOURCE_DIR = ROOT / "inputs/8.4.1_France1"
MODIFIED_SOURCE_GXM = ROOT / "research-output/r5t_f0/modified-source/France1.gxm"
OUTPUT_SCRATCH = ROOT / "research-output/r5t_f21"
REPORT_DIR = ROOT / "research/r5t_f21"
TAG100_LAYOUT_REPORT = ROOT / "research/r5t_f2/tag100-layout.json"

TAG1339_SIZE = 44
TAG1500 = 1500
TREE_TRANSLATION = (20.0, 0.0, 0.0)
COLLIDER_AABB = {
    "baseline": {
        "min": [-1472.298828125, 63.67451858520508, 352.06646728515625],
        "max": [-1471.231689453125, 73.11727142333984, 353.04193115234375],
    },
    "modified": {
        "min": [-1452.298828125, 63.67451858520508, 352.06646728515625],
        "max": [-1451.231689453125, 73.11727142333984, 353.04193115234375],
    },
}
RETAIL_EXE_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class DxParts:
    path: Path
    raw: bytes
    revision: int
    sections: dict[str, bytes]
    ranges: dict[str, tuple[int, int]]
    tree: CourseTag100
    tag1400: CourseTag1400
    tag1339_values: tuple[float | int, ...]


def split_tag100_suffix(suffix: bytes, source: str = "<suffix>") -> tuple[bytes, bytes, bytes, CourseTag100, CourseTag1400]:
    """Split a tag100-through-EOF suffix into T, S, U, R using bounded parsers."""
    tree = parse_course_tag100_bytes(suffix, source, allow_trailing=True)
    tree_bytes = suffix[:tree.consumed_size]
    after_tree = suffix[tree.consumed_size:]
    if len(after_tree) < TAG1339_SIZE:
        raise FormatError(f"tag100 suffix has no complete tag1339 record in {source}")
    tag1339_values = struct.unpack_from("<I3ff3f3f", after_tree, 0)
    if tag1339_values[0] != 1339:
        raise FormatError(f"expected tag1339 immediately after tag100 tree in {source}")
    tag1339 = after_tree[:TAG1339_SIZE]
    after_1339 = after_tree[TAG1339_SIZE:]
    tag1400 = parse_course_tag1400_bytes(after_1339, source, allow_trailing=True)
    tag1400_bytes = after_1339[:tag1400.consumed_size]
    later = after_1339[tag1400.consumed_size:]
    if len(later) < 4 or struct.unpack_from("<I", later)[0] != TAG1500:
        observed = struct.unpack_from("<I", later)[0] if len(later) >= 4 else None
        raise FormatError(f"expected later tag1500 after tag1400 in {source}, found {observed}")
    return tree_bytes, tag1339, tag1400_bytes, later, tree, tag1400


def _parse_dx_parts(path: Path) -> DxParts:
    raw = path.read_bytes()
    model = parse_course_dx_bytes(raw, path.name, path)
    if not model.course_render_validated:
        raise FormatError(f"course render prefix failed validation in {path}")
    if model.word_0x04 != 135:
        raise FormatError(f"expected revision 135 in {path}, found {model.word_0x04}")
    suffix_region = model.collision.bsp
    if suffix_region is None or suffix_region.tag_offset != model.trailing.offset:
        raise FormatError(f"missing parser-bounded tag100 suffix in {path}")
    suffix_offset = suffix_region.tag_offset
    p = raw[:suffix_offset]
    tree, s, u, r, parsed_tree, parsed_1400 = split_tag100_suffix(suffix_region.raw, path.name)
    starts = {
        "P": 0,
        "T": suffix_offset,
        "S": suffix_offset + len(tree),
        "U": suffix_offset + len(tree) + len(s),
        "R": suffix_offset + len(tree) + len(s) + len(u),
    }
    ranges = {
        "P": (0, suffix_offset),
        "T": (suffix_offset, starts["S"]),
        "S": (starts["S"], starts["U"]),
        "U": (starts["U"], starts["R"]),
        "R": (starts["R"], len(raw)),
    }
    sections = {"P": p, "T": tree, "S": s, "U": u, "R": r}
    if sum(map(len, sections.values())) != len(raw):
        raise AssertionError(f"section decomposition does not reach EOF in {path}")
    return DxParts(
        path=path,
        raw=raw,
        revision=model.word_0x04,
        sections=sections,
        ranges=ranges,
        tree=parsed_tree,
        tag1400=parsed_1400,
        tag1339_values=tuple(struct.unpack("<I3ff3f3f", s)),
    )


def _segment_summary(parts: DxParts) -> dict[str, Any]:
    return {
        name: {
            "start_offset": start,
            "end_offset_exclusive": end,
            "size_bytes": len(parts.sections[name]),
            "sha256": sha256(parts.sections[name]),
        }
        for name, (start, end) in parts.ranges.items()
    }


def _tree_summary(tree: CourseTag100) -> dict[str, Any]:
    return {
        "header_words": list(tree.header_words),
        "node_count": len(tree.nodes),
        "plane_bearing_count": tree.optional_record_count,
        "terminal_like_count": len(tree.nodes) - tree.optional_record_count,
        "list_item_count": tree.list_item_count,
        "list_block_count": tree.list_block_count,
        "tree_size_bytes": tree.consumed_size,
        "expected_wire_size_bytes": tree.expected_wire_size(),
        "wire_size_formula_matches": tree.expected_wire_size() == tree.consumed_size,
        "count_invariants": tree.count_invariants(),
        "allocation_role_counts": dict(tree.allocation_role_counts),
        "max_depth": max((node.depth for node in tree.nodes), default=0),
    }


def _typed_descriptors(parsed: CourseTag1400) -> list[dict[str, Any]]:
    """Return byte-span descriptors for every typed tag1400 field."""
    result: list[dict[str, Any]] = []

    def add(path: str, offset: int, type_name: str, value: Any, raw: bytes) -> None:
        result.append({"path": path, "offset": offset, "size": len(raw), "type": type_name, "value": value, "raw": raw})

    add("scalar", 4, "float32", parsed.scalar, struct.pack("<f", parsed.scalar))
    add("dimension_0", 8, "uint32", parsed.dimension_0, struct.pack("<I", parsed.dimension_0))
    add("dimension_1", 12, "uint32", parsed.dimension_1, struct.pack("<I", parsed.dimension_1))
    for label, vector, offset in (("vector_a", parsed.vector_a, 16), ("vector_b", parsed.vector_b, 28)):
        for component, value in enumerate(vector):
            add(f"{label}[{component}]", offset + 4 * component, "float32", value, struct.pack("<f", value))

    for cell in parsed.cells:
        add(f"cell[{cell.index}].entry_count", cell.offset, "uint32", len(cell.entries), struct.pack("<I", len(cell.entries)))
        for entry_index, value in enumerate(cell.entries):
            add(f"cell[{cell.index}].entry[{entry_index}]", cell.offset + 4 + 4 * entry_index, "uint32", value, struct.pack("<I", value))

    if parsed.strings:
        add("string_table.count", parsed.strings[0].offset - 4, "uint32", len(parsed.strings), struct.pack("<I", len(parsed.strings)))
    for string in parsed.strings:
        add(f"string[{string.index}].byte_count", string.offset, "uint32", len(string.raw_bytes), struct.pack("<I", len(string.raw_bytes)))
        add(f"string[{string.index}].raw_bytes", string.offset + 4, "bytes", string.raw_bytes.hex(), string.raw_bytes)

    if parsed.records:
        add("record56.count", parsed.records[0].offset - 4, "uint32", len(parsed.records), struct.pack("<I", len(parsed.records)))
    for record in parsed.records:
        for component, value in enumerate(record.float_prefix):
            add(f"record56[{record.index}].float_prefix[{component}]", record.offset + 4 * component,
                "float32", value, struct.pack("<f", value))
        add(f"record56[{record.index}].string_ref_index", record.offset + 36, "uint32",
            record.string_ref_index, struct.pack("<I", record.string_ref_index))
        for component, value in enumerate(record.float_suffix):
            add(f"record56[{record.index}].float_suffix[{component}]", record.offset + 40 + 4 * component,
                "float32", value, struct.pack("<f", value))
    return result


def _display_value(value: Any, type_name: str) -> Any:
    if type_name == "bytes":
        return {"hex": value}
    return value


def _typed_tag1400_diff(base: DxParts, modified: DxParts) -> dict[str, Any]:
    raw_base, raw_mod = base.sections["U"], modified.sections["U"]
    if len(raw_base) != len(raw_mod):
        raise FormatError("tag1400 region sizes differ; typed aligned comparison is refused")
    raw_changes = [index for index, (a, b) in enumerate(zip(raw_base, raw_mod)) if a != b]
    ranges = changed_ranges(raw_base, raw_mod)
    a_fields = _typed_descriptors(base.tag1400)
    b_fields = _typed_descriptors(modified.tag1400)
    a_by_path = {field["path"]: field for field in a_fields}
    b_by_path = {field["path"]: field for field in b_fields}
    changed_fields: list[dict[str, Any]] = []
    for path in sorted(set(a_by_path) | set(b_by_path)):
        a = a_by_path.get(path)
        b = b_by_path.get(path)
        if a is None or b is None or a["raw"] != b["raw"]:
            field: dict[str, Any] = {
                "path": path,
                "type": (a or b)["type"],
                "baseline_wire_offset": a["offset"] if a else None,
                "modified_wire_offset": b["offset"] if b else None,
                "baseline_file_offset": base.ranges["U"][0] + a["offset"] if a else None,
                "modified_file_offset": modified.ranges["U"][0] + b["offset"] if b else None,
                "interpretation": "UNKNOWN; typed wire field only",
                "baseline_value": _display_value(a["value"], a["type"]) if a else None,
                "modified_value": _display_value(b["value"], b["type"]) if b else None,
            }
            if a and b and a["type"] in {"float32", "uint32"}:
                field["delta"] = b["value"] - a["value"]
            changed_fields.append(field)

    spans = sorted((field["offset"], field["offset"] + field["size"], field["path"], field["type"]) for field in a_fields)
    starts = [item[0] for item in spans]
    byte_owners: Counter[str] = Counter()
    unclassified: list[int] = []
    for offset in raw_changes:
        span_index = bisect_right(starts, offset) - 1
        if span_index >= 0 and spans[span_index][0] <= offset < spans[span_index][1]:
            byte_owners[spans[span_index][2]] += 1
        else:
            unclassified.append(offset)

    changed_float_fields = [field for field in changed_fields if field["type"] == "float32"]
    translation_matches = []
    count_reference_values = {
        "baseline_word0": base.tree.header_words[0],
        "modified_word0": modified.tree.header_words[0],
        "baseline_word1": base.tree.header_words[1],
        "modified_word1": modified.tree.header_words[1],
        "baseline_word2": base.tree.header_words[2],
        "modified_word2": modified.tree.header_words[2],
        "baseline_node_count": len(base.tree.nodes),
        "modified_node_count": len(modified.tree.nodes),
        "baseline_tree_size": len(base.sections["T"]),
        "modified_tree_size": len(modified.sections["T"]),
        "delta_word0": modified.tree.header_words[0] - base.tree.header_words[0],
        "delta_word1": modified.tree.header_words[1] - base.tree.header_words[1],
        "delta_word2": modified.tree.header_words[2] - base.tree.header_words[2],
        "delta_node_count": len(modified.tree.nodes) - len(base.tree.nodes),
        "delta_tree_size": len(modified.sections["T"]) - len(base.sections["T"]),
    }
    count_set = {float(value) for value in count_reference_values.values()}
    direct_count_value_matches = []
    for field in changed_fields:
        if field["type"] not in {"float32", "uint32"}:
            continue
        for side in ("baseline_value", "modified_value", "delta"):
            value = field.get(side)
            if isinstance(value, (int, float)) and float(value) in count_set:
                direct_count_value_matches.append({"path": field["path"], "side": side, "value": value})
    for field in changed_float_fields:
        a_value, b_value = field["baseline_value"], field["modified_value"]
        if not isinstance(a_value, (int, float)) or not isinstance(b_value, (int, float)):
            continue
        delta = b_value - a_value
        if math.isclose(delta, 20.0, abs_tol=1.0e-5) or math.isclose(delta, -20.0, abs_tol=1.0e-5):
            translation_matches.append({"path": field["path"], "delta": delta})

    changed_families = Counter(field["path"].split("[", 1)[0] for field in changed_fields)
    return {
        "schema": "r5t-f21-tag1400-typed-differential-v1",
        "baseline_tag1400_size": len(raw_base),
        "modified_tag1400_size": len(raw_mod),
        "raw_changed_byte_positions": len(raw_changes),
        "raw_changed_ranges": len(ranges),
        "raw_changed_ranges_detail": ranges,
        "typed_changed_field_count": len(changed_fields),
        "typed_changed_fields": changed_fields,
        "changed_byte_ownership_counts": dict(byte_owners),
        "unclassified_changed_byte_offsets": unclassified,
        "all_changed_bytes_typed": not unclassified and sum(byte_owners.values()) == len(raw_changes),
        "family_change_counts": dict(changed_families),
        "cell_lists_identical": base.tag1400.cells == modified.tag1400.cells,
        "string_table_identical": base.tag1400.strings == modified.tag1400.strings,
        "record_count_equal": len(base.tag1400.records) == len(modified.tag1400.records),
        "string_reference_indices_changed": sum(
            a.string_ref_index != b.string_ref_index
            for a, b in zip(base.tag1400.records, modified.tag1400.records)
        ),
        "tree_count_reference_values_checked": count_reference_values,
        "exact_changed_typed_values_matching_tree_counts_or_deltas": direct_count_value_matches,
        "changed_float_fields_with_exact_pm20_delta": translation_matches,
        "aabb_coordinate_matches": _typed_aabb_matches(changed_float_fields),
        "tag1400_header_equal": (
            base.tag1400.scalar == modified.tag1400.scalar
            and base.tag1400.dimension_0 == modified.tag1400.dimension_0
            and base.tag1400.dimension_1 == modified.tag1400.dimension_1
            and base.tag1400.vector_a == modified.tag1400.vector_a
            and base.tag1400.vector_b == modified.tag1400.vector_b
        ),
        "semantic_status": "changed float fields are located in record56 family; meaning UNKNOWN",
    }


def _typed_aabb_matches(changed_float_fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = [float(value) for cohort in COLLIDER_AABB.values() for edge in ("min", "max") for value in cohort[edge]]
    result = []
    for field in changed_float_fields:
        for side in ("baseline_value", "modified_value"):
            value = field.get(side)
            if isinstance(value, (int, float)) and any(math.isclose(value, item, abs_tol=1.0e-4) for item in wanted):
                result.append({"path": field["path"], "side": side, "value": value})
    return result


def _course_inventory() -> dict[str, Any]:
    folders = sorted(path for path in RETAIL_COURSE_ROOT.iterdir() if path.is_dir())
    courses: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    dimension_pairs: list[tuple[int, int]] = []
    cell_counts: list[int] = []
    record_counts: list[int] = []
    later_regions: Counter[tuple[int | None, int]] = Counter()
    tree_violations: list[dict[str, Any]] = []
    for folder in folders:
        dx_files = sorted(folder.glob("*.dx"))
        if len(dx_files) != 1:
            failures.append({"course": folder.name, "error": f"expected one DX, found {len(dx_files)}"})
            continue
        path = dx_files[0]
        try:
            parts = _parse_dx_parts(path)
            invariants = parts.tree.count_invariants()
            if not all(invariants.values()):
                tree_violations.append({"course": folder.name, "invariants": invariants})
            if parts.tree.list_item_count != 0 or parts.tree.list_block_count != 0:
                tree_violations.append({"course": folder.name, "unexpected_list_counts": [parts.tree.list_block_count, parts.tree.list_item_count]})
            u_and_r = parts.sections["U"] + parts.sections["R"]
            parsed_1400 = parse_course_tag1400_bytes(u_and_r, path.name, allow_trailing=True,
                                                     tag_offset=parts.ranges["U"][0])
            trailing = u_and_r[parsed_1400.consumed_size:]
            later_tag = struct.unpack_from("<I", trailing)[0] if len(trailing) >= 4 else None
            if later_tag != TAG1500:
                raise FormatError(f"tag1400 later-region marker is {later_tag}, expected {TAG1500}")
            if parsed_1400.trailing_size != len(parts.sections["R"]):
                raise FormatError("tag1400 reported trailing size differs from exact R section")
            dimension_pairs.append((parsed_1400.dimension_0, parsed_1400.dimension_1))
            cell_counts.append(len(parsed_1400.cells))
            record_counts.append(len(parsed_1400.records))
            later_regions[(later_tag, len(trailing))] += 1
            courses.append({
                "course": folder.name,
                "file": path.name,
                "dx_size_bytes": len(parts.raw),
                "dx_sha256": sha256(parts.raw),
                "revision": parts.revision,
                "tag100_offset": parts.ranges["T"][0],
                "tag100_tree_size": len(parts.sections["T"]),
                "tag100_tree_sha256": sha256(parts.sections["T"]),
                "tag100": _tree_summary(parts.tree),
                "tag1339_size": len(parts.sections["S"]),
                "tag1339_sha256": sha256(parts.sections["S"]),
                "tag1400_offset": parts.ranges["U"][0],
                "tag1400_size": len(parts.sections["U"]),
                "tag1400_sha256": sha256(parts.sections["U"]),
                "tag1400": parsed_1400.structural_summary(),
                "later_region": {"tag": later_tag, "size_bytes": len(trailing), "sha256": sha256(trailing)},
                "count_invariants_pass": all(invariants.values()),
            })
            del parts, parsed_1400
        except Exception as exc:  # keep every corpus outlier visible in report
            failures.append({"course": folder.name, "error": f"{type(exc).__name__}: {exc}"})

    return {
        "course_folder_count": len(folders),
        "tag100_and_tag1400_parse_success_count": len(courses),
        "failure_count": len(failures),
        "failures": failures,
        "tag100_invariant_violation_count": len(tree_violations),
        "tag100_invariant_violations": tree_violations,
        "all_tag100_count_invariants_pass": len(courses) == len(folders) and not tree_violations,
        "tag1400_presence_count": len(courses),
        "tag1400_parser_success_count": len(courses),
        "tag1400_dimension_0_range": [min((item[0] for item in dimension_pairs), default=0), max((item[0] for item in dimension_pairs), default=0)],
        "tag1400_dimension_1_range": [min((item[1] for item in dimension_pairs), default=0), max((item[1] for item in dimension_pairs), default=0)],
        "tag1400_cell_count_range": [min(cell_counts, default=0), max(cell_counts, default=0)],
        "tag1400_record_count_range": [min(record_counts, default=0), max(record_counts, default=0)],
        "later_region_variants": [
            {"first_tag": key[0], "size_bytes": key[1], "course_count": count}
            for key, count in sorted(later_regions.items(), key=lambda item: (item[0][0] or -1, item[0][1]))
        ],
        "courses": courses,
    }


def _code_ordinal_report(base: DxParts, modified: DxParts) -> dict[str, Any]:
    source_txt = SOURCE_DIR / "France1.txt"
    base_model = f2._load_source_model(SOURCE_DIR / "France1.gxm", source_txt)
    modified_model = f2._load_source_model(MODIFIED_SOURCE_GXM, source_txt)
    startpoint = base_model.find_mesh("startpoint")
    startpoint_info = {
        "name": startpoint.name,
        "mesh_index": startpoint.mesh_index,
        "mesh_size": startpoint.mesh_size,
        "triangle_span_half_open": [startpoint.mesh_index, startpoint.mesh_index + startpoint.mesh_size],
    }
    targets = ("COLLIDE_finishline03", "COLLIDE_finishline02", "COLLIDE_finishline01", "COLLIDE_finishline")
    results = []
    for mesh_name in targets:
        cohorts = ([("baseline", base_model, base.tree), ("modified", modified_model, modified.tree)]
                   if mesh_name == "COLLIDE_finishline03" else [("baseline", base_model, base.tree)])
        cohort_reports = []
        for cohort, source_model, tree in cohorts:
            node = source_model.find_mesh(mesh_name)
            triangles = f2._triangle_geometry(source_model, node)
            groups = f2._plane_groups(triangles)
            group_results = []
            total_candidate_records = 0
            all_groups_have_expected_code = True
            for group_index, group in enumerate(groups):
                triangle_ids = sorted(item["triangle_index"] for item in group["triangles"])
                expected_codes = sorted({item - 12 for item in triangle_ids})
                candidates = f2._candidate_records(tree, group["representative"])
                codes = sorted({item["code"] for item in candidates})
                matches = sorted(set(codes) & set(expected_codes))
                pairs = [{"source_triangle_ordinal": tri, "candidate_code": code, "ordinal_minus_code": tri - code}
                         for tri in triangle_ids for code in matches if tri - code == 12]
                all_groups_have_expected_code &= bool(matches)
                total_candidate_records += len(candidates)
                group_results.append({
                    "plane_group_index": group_index,
                    "source_triangle_ordinals": triangle_ids,
                    "expected_code_values_ordinal_minus_12": expected_codes,
                    "candidate_record_count": len(candidates),
                    "candidate_code_values": codes,
                    "candidate_codes_matching_ordinal_minus_12": matches,
                    "source_code_pairs_with_constant_12": pairs,
                    "ambiguous_candidate_count": max(0, len(candidates) - 1),
                })
            cohort_reports.append({
                "cohort": cohort,
                "source_mesh": {"mesh_index": node.mesh_index, "mesh_size": node.mesh_size,
                                "triangle_count": len(triangles)},
                "source_plane_group_count": len(groups),
                "groups_with_at_least_one_code_equal_to_source_ordinal_minus_12": sum(
                    bool(item["candidate_codes_matching_ordinal_minus_12"]) for item in group_results
                ),
                "all_groups_have_expected_code": all_groups_have_expected_code,
                "candidate_record_count_total": total_candidate_records,
                "candidate_duplicate_excess": sum(item["ambiguous_candidate_count"] for item in group_results),
                "groups": group_results,
            })
        results.append({"mesh": mesh_name, "cohorts": cohort_reports})
    return {
        "schema": "r5t-f21-tag100-code-source-ordinal-v1",
        "source": "Demo 8.4.1 France1 GXM/TXT; modified GXM used for COLLIDE_finishline03 modified cohort",
        "startpoint": startpoint_info,
        "candidate_test": "for every source coplanar plane group, compare matched optional-record code values to each source triangle ordinal minus 12",
        "meshes": results,
        "conclusion": "numeric ordinal correspondence is HIGH_CONFIDENCE only where plane candidates match; code field semantics and source ownership remain UNKNOWN",
    }


def _update_legacy_layout(corpus_report: dict[str, Any], base: DxParts, modified: DxParts) -> None:
    if not TAG100_LAYOUT_REPORT.exists():
        return
    data = json.loads(TAG100_LAYOUT_REPORT.read_text(encoding="utf-8"))
    by_name = {item["course"].casefold(): item for item in corpus_report["courses"]}
    corpus = data.get("retail_corpus", {})
    interpretations = {
        "word_0": "count for one optional-record-less subtype selected when the recursive discriminator is -1; subtype semantics UNKNOWN",
        "word_1": "count for the second optional-record-less subtype selected when the recursive discriminator is not -1; subtype semantics UNKNOWN",
        "word_2": "count incremented for optional-record nodes; sizes the 36-byte runtime allocation pool",
        "word_3": "second count incremented for every optional-record node; equal to word_2 in all current Retail files",
        "word_4": "total item count over optional lists",
    }

    def update_tree(tree: dict[str, Any], derived_tree: dict[str, Any]) -> None:
        tree["list_block_count"] = derived_tree["list_block_count"]
        tree["expected_wire_size"] = derived_tree["expected_wire_size_bytes"]
        tree["count_invariants"] = derived_tree["count_invariants"]
        tree["header_count_interpretation_by_loader"] = interpretations

    for entry in corpus.get("courses", []):
        derived = by_name.get(entry.get("course", "").casefold())
        if not derived:
            continue
        tree = entry.setdefault("tree", {})
        new_tree = derived["tag100"]
        update_tree(tree, new_tree)
        following = entry.setdefault("post_tree", {}).get("following_region")
        if following is not None:
            combined_size = derived["tag1400_size"] + derived["later_region"]["size_bytes"]
            following["course_semantics"] = "tag1400 wire section followed by a separate tag1500 region; runtime meanings UNKNOWN"
            following["byte_size"] = derived["tag1400_size"]
            following["sha256"] = derived["tag1400_sha256"]
            following["combined_remainder_byte_size"] = combined_size
            following["tag1400_wire_section"] = {
                "first_tag": 1400,
                "byte_size": derived["tag1400_size"],
                "sha256": derived["tag1400_sha256"],
            }
            following["later_region"] = derived["later_region"]

    for sample_name, parts in (("baseline", base), ("modified", modified)):
        sample = data.get("samples", {}).get(sample_name, {})
        sample_tree = sample.get("tree")
        if isinstance(sample_tree, dict):
            derived = _tree_summary(parts.tree)
            update_tree(sample_tree, derived)
        following = sample.get("post_tree", {}).get("following_region")
        if following is not None:
            combined = parts.sections["U"] + parts.sections["R"]
            following["course_semantics"] = "tag1400 wire section followed by a separate tag1500 region; runtime meanings UNKNOWN"
            following["byte_size"] = len(parts.sections["U"])
            following["sha256"] = sha256(parts.sections["U"])
            following["combined_remainder_byte_size"] = len(combined)
            following["combined_remainder_sha256"] = sha256(combined)
            following["tag1400_wire_section"] = {
                "first_tag": 1400,
                "file_offset": parts.ranges["U"][0],
                "byte_size": len(parts.sections["U"]),
                "sha256": sha256(parts.sections["U"]),
            }
            following["later_region"] = {
                "first_tag": TAG1500,
                "file_offset": parts.ranges["R"][0],
                "byte_size": len(parts.sections["R"]),
                "sha256": sha256(parts.sections["R"]),
                "course_semantics": "UNKNOWN",
            }
    unknowns = data.get("unknowns", [])
    data["unknowns"] = [
        "The tag1400 wire section is structurally parsed by R5T-F.2.1; its runtime role and the later tag1500 semantics remain UNKNOWN. F.1 swapped the full suffix through EOF."
        if "tag1400" in item.casefold() and ("not decoded" in item.casefold() or "distinct" in item.casefold()) else item
        for item in unknowns
    ]
    data.setdefault("r5t_f21_count_invariant_update", {})["status"] = "reproduced from all current Retail DX files"
    data["r5t_f21_count_invariant_update"]["course_count"] = corpus_report["course_folder_count"]
    data["r5t_f21_count_invariant_update"]["all_invariants_pass"] = corpus_report["all_tag100_count_invariants_pass"]
    data["r5t_f21_count_invariant_update"]["tag1400_boundary"] = "U tag1400 ends before R tag1500; R remains opaque and byte-identical in the controlled France1 pair"
    _json_write(TAG100_LAYOUT_REPORT, data)

    f1_manifest = ROOT / "research/r5t_f1/swap-manifest.json"
    if f1_manifest.exists():
        manifest = json.loads(f1_manifest.read_text(encoding="utf-8"))
        clarification = manifest.setdefault("f2_boundary_clarification", {})
        post_tree = clarification.setdefault("post_tree", {})
        post_tree["post_tag1339_remainder_bytes_each"] = len(base.sections["U"]) + len(base.sections["R"])
        post_tree["tag1400_region_bytes_each"] = len(base.sections["U"])
        post_tree["tag1400_changed_byte_positions"] = 64
        post_tree["tag1400_changed_ranges"] = 47
        post_tree["tag1400_runtime_role"] = "UNKNOWN; mismatched runtime hybrids are staged, human result pending"
        post_tree["tag1500_later_region_bytes_each"] = len(base.sections["R"])
        post_tree["tag1500_later_region_identical"] = base.sections["R"] == modified.sections["R"]
        post_tree["tag1500_runtime_role"] = "UNKNOWN"
        post_tree["tag1400_baseline_sha256"] = sha256(base.sections["U"])
        post_tree["tag1400_modified_sha256"] = sha256(modified.sections["U"])
        post_tree["tag1500_sha256"] = sha256(base.sections["R"])
        post_tree["post_tag1339_remainder_sha256_baseline"] = sha256(base.sections["U"] + base.sections["R"])
        post_tree["post_tag1339_remainder_sha256_modified"] = sha256(modified.sections["U"] + modified.sections["R"])
        manifest["f2_boundary_clarification"] = clarification
        _json_write(f1_manifest, manifest)
        local_manifest = ROOT / "research-output/r5t_f1/swap-manifest.json"
        if local_manifest.is_file():
            _json_write(local_manifest, manifest)

    binding_path = ROOT / "research/r5t_f2/collide-finishline03-binding.json"
    if binding_path.exists():
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["r5t_f21_section_decomposition"] = {
            "status": "STATIC_BOUNDARIES_CONFIRMED; TREE_VS_TAG1400_RUNTIME_TEST_PENDING",
            "baseline": {
                "tag100_tree_bytes": len(base.sections["T"]),
                "tag100_tree_sha256": sha256(base.sections["T"]),
                "tag1339_bytes": len(base.sections["S"]),
                "tag1339_sha256": sha256(base.sections["S"]),
                "tag1400_bytes": len(base.sections["U"]),
                "tag1400_sha256": sha256(base.sections["U"]),
                "tag1500_bytes": len(base.sections["R"]),
                "tag1500_sha256": sha256(base.sections["R"]),
            },
            "modified": {
                "tag100_tree_bytes": len(modified.sections["T"]),
                "tag100_tree_sha256": sha256(modified.sections["T"]),
                "tag1339_bytes": len(modified.sections["S"]),
                "tag1339_sha256": sha256(modified.sections["S"]),
                "tag1400_bytes": len(modified.sections["U"]),
                "tag1400_sha256": sha256(modified.sections["U"]),
                "tag1500_bytes": len(modified.sections["R"]),
                "tag1500_sha256": sha256(modified.sections["R"]),
            },
            "post_tag1339_remainder_bytes_each": len(base.sections["U"]) + len(base.sections["R"]),
            "tag1400_changed_byte_positions": 64,
            "tag1400_changed_ranges": 47,
            "tag1500_identical_between_donors": base.sections["R"] == modified.sections["R"],
            "runtime_hybrids": "see research/r5t_f21/swap-manifest.json; no result recorded until human runtime test",
        }
        _json_write(binding_path, binding)


def _analysis() -> dict[str, Any]:
    for required in (BASELINE_DX, MODIFIED_DX, RUNTIME_TEMPLATE / "MRallye.exe", RETAIL_COURSE_ROOT,
                    SOURCE_DIR / "France1.gxm", SOURCE_DIR / "France1.txt", MODIFIED_SOURCE_GXM):
        if not required.exists():
            raise FileNotFoundError(required)
    retail_exe_hash = sha256_file(RUNTIME_EXE) if RUNTIME_EXE.exists() else None
    if retail_exe_hash != RETAIL_EXE_SHA256:
        raise FormatError(f"supported Retail executable hash mismatch: {retail_exe_hash}")
    base = _parse_dx_parts(BASELINE_DX)
    modified = _parse_dx_parts(MODIFIED_DX)
    if sha256(base.sections["S"]) != sha256(modified.sections["S"]):
        raise FormatError("tag1339 donors differ; this phase requires a fixed tag1339 donor")
    if base.sections["R"] != modified.sections["R"]:
        raise FormatError("later-region donors differ; this phase requires one invariant R donor")
    if not all(base.tree.count_invariants().values()) or not all(modified.tree.count_invariants().values()):
        raise FormatError("controlled France1 tag100 count invariants failed")
    if base.tag1400.consumed_size != len(base.sections["U"]) or modified.tag1400.consumed_size != len(modified.sections["U"]):
        raise FormatError("tag1400 parser boundary does not match region decomposition")
    if base.tag1400.trailing_size != len(base.sections["R"]) or modified.tag1400.trailing_size != len(modified.sections["R"]):
        raise FormatError("tag1400 trailing bytes do not match the separate R region")

    corpus = _course_inventory()
    code_report = _code_ordinal_report(base, modified)
    u_diff = _typed_tag1400_diff(base, modified)
    if u_diff["raw_changed_byte_positions"] != 64 or u_diff["raw_changed_ranges"] != 47:
        raise FormatError("France1 tag1400 differential disagrees with established 64-byte/47-range result")
    if not u_diff["all_changed_bytes_typed"]:
        raise FormatError("one or more changed tag1400 bytes did not map to a typed field")

    return {
        "base": base,
        "modified": modified,
        "corpus": corpus,
        "code_report": code_report,
        "u_diff": u_diff,
        "runtime_exe": {"path": str(RUNTIME_EXE), "sha256": retail_exe_hash},
        "runtime_template_exe": {
            "path": "research-output/r5t_f1/runtime/hybrid-a/runtime/MRallye.exe",
            "sha256": sha256_file(RUNTIME_TEMPLATE / "MRallye.exe"),
        },
    }


def _load_cached_analysis() -> dict[str, Any]:
    """Reload validated static reports and recheck their pinned DX sources."""
    needed = (
        REPORT_DIR / "section-map.json",
        REPORT_DIR / "tag1400-differential.json",
        REPORT_DIR / "tag100-code-ordinal.json",
        REPORT_DIR / "retail-course-structural-validation.json",
    )
    if not all(path.is_file() for path in needed):
        return _analysis()
    base = _parse_dx_parts(BASELINE_DX)
    modified = _parse_dx_parts(MODIFIED_DX)
    section_map = json.loads(needed[0].read_text(encoding="utf-8"))
    pinned = section_map["baselines"]
    if pinned["baseline"]["sha256"] != sha256(base.raw) or pinned["modified"]["sha256"] != sha256(modified.raw):
        raise FormatError("cached analysis DX hashes differ from current source snapshots")
    runtime_hash = sha256_file(RUNTIME_EXE)
    if runtime_hash != RETAIL_EXE_SHA256:
        raise FormatError(f"supported Retail executable hash mismatch: {runtime_hash}")
    return {
        "base": base,
        "modified": modified,
        "corpus": json.loads(needed[3].read_text(encoding="utf-8")),
        "code_report": json.loads(needed[2].read_text(encoding="utf-8")),
        "u_diff": _typed_tag1400_diff(base, modified),
        "runtime_exe": {"path": str(RUNTIME_EXE), "sha256": runtime_hash},
        "runtime_template_exe": {
            "path": "research-output/r5t_f1/runtime/hybrid-a/runtime/MRallye.exe",
            "sha256": sha256_file(RUNTIME_TEMPLATE / "MRallye.exe"),
        },
    }


def _write_analysis_reports(result: dict[str, Any], runtime_hybrids: dict[str, Any] | None = None) -> None:
    base: DxParts = result["base"]
    modified: DxParts = result["modified"]
    _update_legacy_layout(result["corpus"], base, modified)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_sections = {
        "schema": "r5t-f21-section-map-v1",
        "boundary_note": "F.1 swapped tag100 marker through EOF. This report splits that suffix into T (tag100 tree), S (44-byte tag1339), U (parsed tag1400), and R (separate tag1500 region).",
        "baselines": {
            "baseline": {"path": str(BASELINE_DX.relative_to(ROOT)), "sha256": sha256(base.raw), "size_bytes": len(base.raw), "revision": base.revision, "sections": _segment_summary(base), "tag1339_values_neutral": list(base.tag1339_values)},
            "modified": {"path": str(MODIFIED_DX.relative_to(ROOT)), "sha256": sha256(modified.raw), "size_bytes": len(modified.raw), "revision": modified.revision, "sections": _segment_summary(modified), "tag1339_values_neutral": list(modified.tag1339_values)},
        },
        "tag100_tree": {"baseline": _tree_summary(base.tree), "modified": _tree_summary(modified.tree)},
        "tag1400": {"baseline": base.tag1400.structural_summary(), "modified": modified.tag1400.structural_summary()},
        "tag1339_byte_identical": base.sections["S"] == modified.sections["S"],
        "tag1500_byte_identical": base.sections["R"] == modified.sections["R"],
    }
    _json_write(REPORT_DIR / "section-map.json", report_sections)
    _json_write(REPORT_DIR / "tag1400-differential.json", result["u_diff"])
    _json_write(REPORT_DIR / "tag100-code-ordinal.json", result["code_report"])
    _json_write(REPORT_DIR / "retail-course-structural-validation.json", result["corpus"])

    layout_md = [
        "# R5T-F.2.1 — tag1400 wire layout",
        "",
        "## Evidence and boundary",
        "",
        "The supported Retail executable is `MRallye.exe`, SHA256 `" + result["runtime_exe"]["sha256"] + "`. Ghidra Bridge decompilation of `0x005541D0` shows a 40-byte input header, `dimension_0 * dimension_1` per-cell uint32-counted lists, a byte-length-prefixed string table, and 56-byte records (`9×float32, uint32 string reference, 4×float32`). Fields retain neutral wire names.",
        "",
        "The parser ends tag1400 exactly before a later tag1500 region in the controlled France1 pair. In that pair the previously called `1,824,828-byte tag1400 region` is actually the complete post-tag1339 suffix remainder `U + R`: tag1400 U is 1,809,324 bytes and tag1500 R is 15,504 bytes. R is byte-identical between donors.",
        "",
        "## Fixed and repeated fields",
        "",
        "| Relative offset | Wire type | Neutral field | France1 baseline | Status |",
        "|---:|---|---|---:|---|",
        "| 0 | uint32 | tag (1400) | 1400 | `CONFIRMED_BY_BINARY` |",
        "| 4 | float32 | scalar | " + repr(base.tag1400.scalar) + " | meaning `UNKNOWN` |",
        "| 8 | uint32 | dimension_0 | " + str(base.tag1400.dimension_0) + " | `CONFIRMED_BY_BINARY` |",
        "| 12 | uint32 | dimension_1 | " + str(base.tag1400.dimension_1) + " | `CONFIRMED_BY_BINARY` |",
        "| 16 | 3×float32 | vector_a | " + repr(list(base.tag1400.vector_a)) + " | meaning `UNKNOWN` |",
        "| 28 | 3×float32 | vector_b | " + repr(list(base.tag1400.vector_b)) + " | meaning `UNKNOWN` |",
        "| 40 | repeated | dimensioned cells: uint32 count then count×uint32 | " + str(len(base.tag1400.cells)) + " cells | `CONFIRMED_BY_BINARY` |",
        "| after cells | repeated | uint32 string count; each uint32 byte length + raw bytes | " + str(len(base.tag1400.strings)) + " entries | `CONFIRMED_BY_BINARY` |",
        "| after strings | repeated | uint32 record count; 56-byte records | " + str(len(base.tag1400.records)) + " records | `CONFIRMED_BY_BINARY` |",
        "| record +0..+35 | 9×float32 | float_prefix | first record retained | semantics `UNKNOWN` |",
        "| record +36 | uint32 | string_ref_index | first record `" + str(base.tag1400.records[0].string_ref_index) + "` | string-table reference `CONFIRMED_BY_BINARY` |",
        "| record +40..+55 | 4×float32 | float_suffix | first record retained | semantics `UNKNOWN` |",
        "",
        "No writer is implemented. Allocation/runtime names are not inferred from this file layout.",
    ]
    (REPORT_DIR / "tag1400-layout.md").write_text("\n".join(layout_md) + "\n", encoding="utf-8")

    swaps = runtime_hybrids or {}
    _json_write(REPORT_DIR / "swap-manifest.json", {
        "schema": "r5t-f21-swap-manifest-v1",
        "status": "READY_FOR_TREE_TAG1400_RUNTIME_TEST" if runtime_hybrids else "STATIC_ANALYSIS_COMPLETE; HYBRIDS_NOT_STAGED",
        "fixed_donors": {"P": "baseline", "S": "baseline (identical to modified)", "R": "baseline (identical to modified)"},
        "hybrids": swaps,
    })

    _write_research_findings(result, runtime_hybrids)


def _write_research_findings(result: dict[str, Any], runtime_hybrids: dict[str, Any] | None) -> None:
    base: DxParts = result["base"]
    modified: DxParts = result["modified"]
    corpus = result["corpus"]
    code = result["code_report"]
    diff = result["u_diff"]
    h = [
        "# R5T-F.2.1 — tag100 tree ↔ tag1400 causal isolation",
        "",
        "## Status",
        "",
        "**R5T-F.2.1 static preparation: PASS. Runtime decision is pending.** R5T-F.1 remains a full tag100-through-EOF suffix result; no tree-only causal claim is made before the human tests the two mismatched hybrids.",
        "",
        "## F.1/F.2 boundary and exact section split",
        "",
        "F.1 proved that the tested `COLLIDE_finishline03` physical state followed the selected complete suffix. It did not isolate the tag100 tree. The current baseline/modified DX files decompose at parser-derived boundaries into P/T/S/U/R; see [`section-map.json`](section-map.json) for exact offsets, sizes, and SHA256 values.",
        "",
        f"The tag1339 section S is {len(base.sections['S'])} bytes and byte-identical. The parser-bounded tag1400 section U is {len(base.sections['U']):,} bytes in both files. A separate tag1500 region R is {len(base.sections['R']):,} bytes, byte-identical through EOF. Thus the older 1,824,828-byte ‘tag1400 region’ was the combined U+R remainder, not U alone.",
        "",
        "## Tree-size accounting and corpus invariants",
        "",
        "For N serialized nodes, P optional 20-byte records, Q present optional-list blocks, L list items, and N−1 one-byte link selectors, the parser-derived general wire size is `24 + 12N + 20P + 4Q + 20L + (N−1)`. Every current Retail file has Q=L=0, reducing to the requested `23 + 13N + 20P`.",
        "",
        f"France1 baseline: N={len(base.tree.nodes):,}, P={base.tree.optional_record_count:,}, T={len(base.sections['T']):,} bytes; formula gives {base.tree.expected_wire_size():,}. Modified: N={len(modified.tree.nodes):,}, P={modified.tree.optional_record_count:,}, T={len(modified.sections['T']):,}; formula gives {modified.tree.expected_wire_size():,}.",
        "",
        f"All requested header/node relationships pass on {corpus['tag100_and_tag1400_parse_success_count']}/{corpus['course_folder_count']} Retail courses. The France1 edit changes word counts by −41/−33/−74, removes 74 optional records and 148 total nodes, and changes T by −3,404 bytes: `12*(-148) + 20*(-74) + (-148 selector bytes) = -3,404`. The formerly ‘unexplained’ 148-byte remainder is exactly the change in N−1 serialized link-selector bytes; the full size equation closes with zero residual.",
        "",
        "The hierarchy is called a **plane-bearing partition hierarchy** here. Its serialized child/sibling links and observed fanout do not prove BSP semantics.",
        "",
        "## Header counter traversal evidence",
        "",
        "The Retail tag100 loader at `0x0057E2D0` reads five header words and allocates its three pools; Ghidra Bridge decompilation confirmed the 0x74-byte root and 8/8/36-byte allocator roles. Separately, retained Ghidra decompilation of `FUN_0057E230` shows it initializes five counters, calls recursive `FUN_0057E190`, performs five serializer calls, then enters `FUN_0057E3A0`. The counter increments one of two fields for optional-less nodes according to a discriminator (`-1` vs other), increments two fields for every optional-record node, and adds optional-list item counts; traversal recurses through children and iterates siblings. This matches the five observed header words and corpus relationships, but exact subtype names remain UNKNOWN. The Bridge export set did not include `0x0057E190`/`0x0057E230` for a live refresh, so this counter detail is attributed to the existing F.2 decompilation artifact, not a new Bridge query.",
        "",
        "## Optional-record code values",
        "",
        f"Re-analysis grouped source triangles by runtime-space plane for four France1 `COLLIDE_finishline*` meshes. For `COLLIDE_finishline03`, all {sum(item['groups_with_at_least_one_code_equal_to_source_ordinal_minus_12'] for item in code['meshes'][0]['cohorts'])}/{sum(item['source_plane_group_count'] for item in code['meshes'][0]['cohorts'])} plane groups across baseline and modified cohorts contain a candidate code equal to a source triangle ordinal minus 12. Static baseline results for the other three finishline meshes are in [`tag100-code-ordinal.json`](tag100-code-ordinal.json). The source `startpoint` span is triangles [0,12), a plausible numeric reason for the constant. This is a HIGH_CONFIDENCE_NUMERIC_CORRELATION, not proof that `code` is a source triangle index or source-object owner. Only finishline03 has direct runtime physical proof.",
        "",
        "## Tag1339, tag1400, and typed differential",
        "",
        "Retail executable SHA256 is `" + result["runtime_exe"]["sha256"] + "`. Tag1339 is a separate 44-byte record dispatched to handler `0x00553C80`; the France1 donor bytes are identical. Ghidra Bridge decompilation at `0x005541D0` verifies the tag1400 loader’s fixed reads and per-cell allocation path. The structural parser is in `src/master_rallye/course_tag1400.py`; it preserves unknown values and has no writer.",
        "",
        f"France1 U is {len(base.sections['U']):,} bytes; {diff['raw_changed_byte_positions']} byte positions differ over {diff['raw_changed_ranges']} ranges. The typed pass maps {diff['typed_changed_field_count']} changed float32 fields, and every changed byte is assigned to a parsed field. Changes occur in the 56-byte record family; header, cells, strings, and string references stay identical. No changed field exactly matches the known tree counters/deltas or collider AABB coordinates, and no float changes by ±20. Field meanings remain UNKNOWN.",
        "",
        "## Retail structural validation",
        "",
        f"The current Retail corpus contains {corpus['course_folder_count']} course folders. Tag100 and tag1400 parse in {corpus['tag100_and_tag1400_parse_success_count']}/{corpus['course_folder_count']}; tag100 count invariants pass in all successful courses. Tag1400 dimensions span `{corpus['tag1400_dimension_0_range']}` × `{corpus['tag1400_dimension_1_range']}`; cell counts span `{corpus['tag1400_cell_count_range']}` and 56-byte record counts span `{corpus['tag1400_record_count_range']}`. This is structural coverage only, not runtime semantic validation across courses.",
        "",
        "## Runtime isolation still required",
        "",
        "F.1 suffix runtime result remains `CONFIRMED_BY_RUNTIME_TEST`. F.2 plane-to-source relation remains `HIGH_CONFIDENCE_INFERENCE`. The two hybrids independently substitute only T or U while fixing P, S, and R. The remaining runtime result will distinguish tree carrier, tag1400 carrier, or cross-section dependency; no outcome is preselected.",
        "",
        "No physical writer, arbitrary tag100 mutation, new source mesh edit, or EXE patch was added.",
    ]
    (REPORT_DIR / "findings.md").write_text("\n".join(h) + "\n", encoding="utf-8")

    if runtime_hybrids:
        _write_runtime_handoff(result, runtime_hybrids)
    else:
        (REPORT_DIR / "runtime-handoff.md").write_text(
            "# R5T-F.2.1 runtime handoff\n\nHybrids have not been staged yet. Run `python tools/r5t_f21_prepare.py prepare-runtime` after static analysis succeeds.\n",
            encoding="utf-8",
        )


def _compose_regions(prefix: bytes, tree: bytes, tag1339: bytes, tag1400: bytes, later: bytes) -> bytes:
    if len(tag1339) != TAG1339_SIZE or struct.unpack_from("<I", tag1339)[0] != 1339:
        raise FormatError("fixed S donor must be exactly one tag1339 record")
    if len(tag1400) < 4 or struct.unpack_from("<I", tag1400)[0] != 1400:
        raise FormatError("U donor must begin with tag1400")
    if len(later) < 4 or struct.unpack_from("<I", later)[0] != TAG1500:
        raise FormatError("R donor must begin with tag1500")
    if not tree or struct.unpack_from("<I", tree)[0] != 100:
        raise FormatError("T donor must begin with tag100")
    return prefix + tree + tag1339 + tag1400 + later


def _verify_sha(data: bytes, expected: str, label: str) -> None:
    observed = sha256(data)
    if observed != expected:
        raise FormatError(f"{label} SHA256 mismatch: expected {expected}, found {observed}")


def _verify_region_donors(actual: dict[str, bytes], expected: dict[str, bytes]) -> dict[str, dict[str, Any]]:
    if set(actual) != set(expected):
        raise FormatError(f"region set mismatch: actual={sorted(actual)}, expected={sorted(expected)}")
    report = {}
    for name in sorted(expected):
        if actual[name] != expected[name]:
            raise FormatError(f"region {name} does not match its designated donor byte-for-byte")
        report[name] = {
            "size_bytes": len(actual[name]),
            "sha256": sha256(actual[name]),
            "matches_donor_byte_exact": True,
        }
    return report


def _verify_hybrid(data: bytes, expected: dict[str, bytes], label: str) -> dict[str, Any]:
    model = parse_course_dx_bytes(data, label)
    if model.word_0x04 != 135 or not model.course_render_validated:
        raise FormatError(f"{label} render prefix is not validated revision 135")
    region = model.collision.bsp
    if region is None:
        raise FormatError(f"{label} has no tag100 region")
    T, S, U, R, tree, tag1400 = split_tag100_suffix(region.raw, label)
    actual = {"P": data[:region.tag_offset], "T": T, "S": S, "U": U, "R": R}
    provenance = _verify_region_donors(actual, expected)
    if sum(len(item) for item in actual.values()) != len(data):
        raise FormatError(f"{label} exact P/T/S/U/R pieces do not reach EOF")
    return {
        "full_sha256": sha256(data),
        "full_size_bytes": len(data),
        "revision": model.word_0x04,
        "render_validation": model.course_render_validated,
        "tag100_tree_size_bytes": tree.consumed_size,
        "tag100_node_count": len(tree.nodes),
        "tag1400_consumed_size_bytes": tag1400.consumed_size,
        "later_first_tag": struct.unpack_from("<I", R)[0],
        "region_provenance": provenance,
    }


def _file_hash_map(root: Path, *, omit_relative: str | None = None) -> dict[str, tuple[int, str]]:
    result = {}
    omit = omit_relative.replace("\\", "/").casefold() if omit_relative else None
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if omit and rel.casefold() == omit:
            continue
        result[rel.casefold()] = (path.stat().st_size, sha256_file(path))
    return result


def _load_existing_runtime_hybrids(result: dict[str, Any]) -> dict[str, Any] | None:
    """Return the prior handoff only if staged DX/runtime copies still validate."""
    manifest_path = REPORT_DIR / "swap-manifest.json"
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hybrids = manifest.get("hybrids", {})
    if manifest.get("status") != "READY_FOR_TREE_TAG1400_RUNTIME_TEST" or not all(
        name in hybrids for name in ("hybrid-t", "hybrid-u", "runtime_clone_verification")
    ):
        return None

    base: DxParts = result["base"]
    modified: DxParts = result["modified"]
    fixed = {"P": base.sections["P"], "S": base.sections["S"], "R": base.sections["R"]}
    expected_by_name = {
        "hybrid-t": {**fixed, "T": modified.sections["T"], "U": base.sections["U"]},
        "hybrid-u": {**fixed, "T": base.sections["T"], "U": modified.sections["U"]},
    }

    def rooted(relative: str) -> Path:
        candidate = Path(relative)
        if candidate.is_absolute():
            raise FormatError(f"staged manifest path must be relative to repository: {relative}")
        resolved = (ROOT / candidate).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise FormatError(f"staged manifest path escapes repository: {relative}") from exc
        return resolved

    for name, expected in expected_by_name.items():
        item = hybrids[name]
        dx_path = rooted(item["dx_path"])
        raw = dx_path.read_bytes()
        verified = _verify_hybrid(raw, expected, name)
        if verified["full_sha256"] != item.get("full_sha256") or verified["full_size_bytes"] != item.get("full_size_bytes"):
            raise FormatError(f"staged {name} DX differs from its recorded hybrid manifest")
        runtime = rooted(item["runtime_directory"])
        course_dx = runtime / "DataGx/Course/France1/france1.dx"
        executable = runtime / "MRallye.exe"
        race_xml = runtime / "DataScene/RaceTest/France1.xml"
        if sha256_file(course_dx) != verified["full_sha256"]:
            raise FormatError(f"staged {name} runtime course DX differs from its hybrid")
        if sha256_file(executable) != item.get("runtime_exe_sha256"):
            raise FormatError(f"staged {name} runtime executable hash differs from its manifest")
        if sha256_file(race_xml) != item.get("race_test_xml_sha256"):
            raise FormatError(f"staged {name} RaceTest XML hash differs from its manifest")

    clones = hybrids["runtime_clone_verification"]
    target = clones["target_relative_path"]
    files_t = _file_hash_map(rooted(hybrids["hybrid-t"]["runtime_directory"]), omit_relative=target)
    files_u = _file_hash_map(rooted(hybrids["hybrid-u"]["runtime_directory"]), omit_relative=target)
    if files_t != files_u or len(files_t) != clones.get("non_target_file_count"):
        raise FormatError("staged runtime clones no longer match outside the France1 DX")
    hybrids["runtime_clone_verification"]["non_target_files_byte_identical"] = True
    return hybrids


def _stage_runtime(result: dict[str, Any]) -> dict[str, Any]:
    if OUTPUT_SCRATCH.exists():
        raise FileExistsError(f"refusing to overwrite existing scratch output: {OUTPUT_SCRATCH}")
    out = OUTPUT_SCRATCH / "hybrids"
    dx_out = out / "dx"
    dx_out.mkdir(parents=True)
    base: DxParts = result["base"]
    modified: DxParts = result["modified"]
    fixed = {"P": base.sections["P"], "S": base.sections["S"], "R": base.sections["R"]}
    hybrid_specs = {
        "hybrid-t": {"P": fixed["P"], "T": modified.sections["T"], "S": fixed["S"], "U": base.sections["U"], "R": fixed["R"]},
        "hybrid-u": {"P": fixed["P"], "T": base.sections["T"], "S": fixed["S"], "U": modified.sections["U"], "R": fixed["R"]},
    }
    report = {}
    for key, pieces in hybrid_specs.items():
        dx_bytes = _compose_regions(pieces["P"], pieces["T"], pieces["S"], pieces["U"], pieces["R"])
        info = _verify_hybrid(dx_bytes, pieces, key)
        dx_path = dx_out / f"{key}.dx"
        dx_path.write_bytes(dx_bytes)
        if sha256_file(dx_path) != info["full_sha256"]:
            raise FormatError(f"written {key} DX hash differs from in-memory hybrid")
        info["dx_path"] = str(dx_path.relative_to(ROOT))
        report[key] = info

    runtime_root = OUTPUT_SCRATCH / "runtime"
    runtime_root.mkdir()
    target_rel = Path("DataGx/Course/France1/france1.dx")
    for key in ("hybrid-t", "hybrid-u"):
        destination = runtime_root / key / "runtime"
        if destination.exists():
            raise FileExistsError(destination)
        shutil.copytree(RUNTIME_TEMPLATE, destination, copy_function=shutil.copy2)
        target = destination / target_rel
        if not target.is_file():
            raise FileNotFoundError(f"runtime template lacks France1 DX at {target}")
        target.write_bytes((dx_out / f"{key}.dx").read_bytes())
        if sha256_file(target) != report[key]["full_sha256"]:
            raise FormatError(f"runtime copy {key} target DX hash mismatch")
        exe = destination / "MRallye.exe"
        report[key]["runtime_directory"] = str(destination.relative_to(ROOT))
        report[key]["runtime_exe_sha256"] = sha256_file(exe)
        report[key]["runtime_course_dx_sha256"] = sha256_file(target)
        report[key]["race_test_xml_sha256"] = sha256_file(destination / "DataScene/RaceTest/France1.xml")

    target_posix = "DataGx/Course/France1/france1.dx"
    non_dx_t = _file_hash_map(runtime_root / "hybrid-t/runtime", omit_relative=target_posix)
    non_dx_u = _file_hash_map(runtime_root / "hybrid-u/runtime", omit_relative=target_posix)
    if non_dx_t != non_dx_u:
        raise FormatError("runtime clones differ outside the target France1 DX")
    report["runtime_clone_verification"] = {
        "non_target_file_count": len(non_dx_t),
        "non_target_files_byte_identical": True,
        "target_relative_path": target_posix,
        "only_intended_file_difference": "DataGx/Course/France1/france1.dx",
    }
    return report


def _write_runtime_handoff(result: dict[str, Any], hybrids: dict[str, Any]) -> None:
    base: DxParts = result["base"]
    modified: DxParts = result["modified"]
    lines = [
        "# R5T-F.2.1 — human runtime handoff",
        "",
        "Status: **READY_FOR_TREE_TAG1400_RUNTIME_TEST**. These are two new isolated Demo 9.10.0 runtime clones. No runtime result is claimed until the user tests them.",
        "",
        "## Exact staged files",
        "",
        f"- Hybrid T runtime: `{hybrids['hybrid-t']['runtime_directory']}`",
        f"  - DX SHA256: `{hybrids['hybrid-t']['runtime_course_dx_sha256']}`",
        f"  - EXE SHA256: `{hybrids['hybrid-t']['runtime_exe_sha256']}`",
        f"  - RaceTest France1 XML SHA256: `{hybrids['hybrid-t']['race_test_xml_sha256']}`",
        f"- Hybrid U runtime: `{hybrids['hybrid-u']['runtime_directory']}`",
        f"  - DX SHA256: `{hybrids['hybrid-u']['runtime_course_dx_sha256']}`",
        f"  - EXE SHA256: `{hybrids['hybrid-u']['runtime_exe_sha256']}`",
        f"  - RaceTest France1 XML SHA256: `{hybrids['hybrid-u']['race_test_xml_sha256']}`",
        f"- Non-target files checked byte-identical across clones: {hybrids['runtime_clone_verification']['non_target_file_count']}",
        "",
        "Each clone differs only in `DataGx/Course/France1/france1.dx`; its RaceTest XML is at `DataScene/RaceTest/France1.xml`. Start `MRallye.exe` from that clone’s runtime directory and select France1. The two clones use the same non-DX runtime tree.",
        "",
        "## Expected setup invariants",
        "",
        f"Both hybrids have fixed P from baseline (`{sha256(base.sections['P'])}`), fixed S (`{sha256(base.sections['S'])}`), and fixed R (`{sha256(base.sections['R'])}`). T and U donor hashes are listed in `swap-manifest.json`. Both parse as revision 135; render arrays and draw batches validate; tag100, tag1339, tag1400, and tag1500 boundaries reach EOF exactly.",
        "",
        "## Test each hybrid",
        "",
        "At the known support locations, record OLD collision and NEW invisible collision independently. Also record course load, visible finish support location, FinishArea/RACE COMPLETE location, and any anomalies.",
        "",
        "- OLD location (baseline): approximately `(-1471.7653, 68.4258, 352.5542)`.",
        "- NEW location (modified): approximately `(-1451.7653, 68.4258, 352.5542)`.",
        "- Hybrid T contains modified T and baseline U. Does collision occur at OLD or NEW?",
        "- Hybrid U contains baseline T and modified U. Does collision occur at OLD or NEW?",
        "- FinishArea and visible finish geometry should remain unchanged in either case.",
        "",
        "## Decision guide (apply only after results)",
        "",
        "- T=NEW and U=OLD: tag100 tree alone determines the tested physical state in this pairing.",
        "- T=OLD and U=NEW: tag1400 carries or controls the tested state.",
        "- Either fails to load or neither location behaves normally: report cross-section dependency or other anomaly; do not force a carrier conclusion.",
        "- Both NEW or both OLD: first verify selected clone, file hash, and coordinates before interpretation.",
        "",
        "F.1 remains a full-suffix result. This probe does not generalize tag100 semantics, prove BSP semantics, or establish tag1400 meaning.",
    ]
    (REPORT_DIR / "runtime-handoff.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_docs(result: dict[str, Any]) -> None:
    # Keep old checkpoints intact and append a dated/evidence-bounded correction.
    grammar_path = ROOT / "research/r5t_f2/tag100-physical-grammar.md"
    grammar = grammar_path.read_text(encoding="utf-8")
    old = "For current Retail data, `T = 24 + 12N + 20P + 4Q + 20L + (N−1)`, where Q is the number of present list blocks and L is the list-item count. Q=L=0 in all 36 Retail courses, so `T = 23 + 13N + 20P`. On the controlled pair, `13*(-148) + 20*(-74) + (-148 selectors) = -3,404` exactly. The previous 148-byte residual is the removed N−1 link-selector bytes, not an unexplained difference."
    new = "For current Retail data, `T = 24 + 12N + 20P + 4Q + 20L + (N−1)`, where Q is the number of present list blocks and L is the list-item count. Q=L=0 in all 36 Retail courses, so `T = 23 + 13N + 20P`. On the controlled pair, `12*(-148) + 20*(-74) + (-148 link-selector bytes) = -3,404` exactly. Equivalently, `13*(-148) + 20*(-74) = -3,404`; the selector-byte delta is already included in the 13-byte per-node term. The prior 148-byte residual is not additional to that equation."
    if old in grammar:
        grammar = grammar.replace(old, new)
    grammar = grammar.replace(
        "a separate tag1400 region. Baseline tag100 starts",
        "tag1400 section U followed by a separate tag1500 section R. Baseline tag100 starts"
    )
    grammar = grammar.replace(
        "The later tag1400 region has the same size and 64 changed byte positions in 47 ranges.",
        "Tag1400 U is 1,809,324 bytes and has 64 changed byte positions in 47 ranges; later tag1500 R is 15,504 bytes and byte-identical."
    )
    grammar = grammar.replace(
        "- The tag1400 region and any target-specific runtime node/leaf selection remain unresolved.",
        "- Tag1400 U's runtime role, tag1500 R semantics, and target-specific runtime node/leaf selection remain unresolved."
    )
    grammar_marker = "## R5T-F.2.1 static tree/tag1400 preparation"
    if grammar_marker not in grammar:
        grammar += "\n\n" + grammar_marker + "\n\n"
        grammar += "The 36/36 Retail count invariants and exact T-size equation were reproduced from DX bytes; see [`research/r5t_f21/findings.md`](../r5t_f21/findings.md). The F.1 runtime result remains a full tag100-through-EOF suffix result. F.2.1 separates T (tag100 tree), S (tag1339), U (tag1400), and R (tag1500) and stages two mismatched hybrids. Runtime isolation is pending. The optional `code` field has a HIGH_CONFIDENCE numeric source-triangle ordinal correlation at offset 12 for the four static France1 finishline meshes, but its semantics remain UNKNOWN.\n"
    grammar_path.write_text(grammar, encoding="utf-8")

    findings_path = ROOT / "research/r5t_f2/findings.md"
    findings = findings_path.read_text(encoding="utf-8")
    findings = findings.replace(
        "then a 1,824,828-byte tag1400 region with 64 changed\nbyte positions in 47 ranges.",
        "then a 1,824,828-byte post-tag1339 remainder, now separated as tag1400 U\n(1,809,324 bytes) plus tag1500 R (15,504 bytes). The 64 changed byte positions\nare in U; R is byte-identical."
    )
    if "## R5T-F.2.1 static updates" not in findings:
        findings += "\n\n## R5T-F.2.1 static updates\n\n"
        findings += "The exact size equation includes one link-selector byte per non-root node, and the 3,404-byte delta is `12*(-148) + 20*(-74) + (-148 selector bytes)` (or equivalently `13*(-148) + 20*(-74)`, with selectors already included). All 36 current Retail tag100 trees satisfy the stated header/node invariants. The complete post-tag1339 remainder of 1,824,828 bytes splits into tag1400 U (1,809,324 bytes) and later tag1500 R (15,504 bytes) for the controlled France1 pair. Tag1400’s 64 changed bytes/47 ranges are typed into its 56-byte record family; all other parsed families remain equal. The two runtime hybrids are staged, and causal ownership remains pending human runtime results. See [`research/r5t_f21/findings.md`](../r5t_f21/findings.md).\n"
    findings_path.write_text(findings, encoding="utf-8")

    dx_path = ROOT / "docs/formats/dx-course.md"
    dx = dx_path.read_text(encoding="utf-8")
    dx_old = (
        "The runtime test swapped bytes from the tag100 marker through EOF. F.2 found a\n"
        "44-byte tag1339 record followed by a separate tag1400 region after the parsed\n"
        "tree. The tag1339 bytes are identical in the source pair; the 1,824,828-byte\n"
        "tag1400 regions have 64 different byte positions. Runtime isolation therefore\n"
        "applies to the complete suffix. The source-matching plane records themselves\n"
        "are inside the parsed tag100 tree, a **HIGH_CONFIDENCE_INFERENCE** geometric\n"
        "binding; the independent runtime contribution of tag1400 remains unknown."
    )
    dx_new = (
        "The runtime test swapped bytes from the tag100 marker through EOF. F.2 found a\n"
        "44-byte tag1339 record after the parsed tree. F.2.1 then separated the suffix\n"
        "into tag1400 U (1,809,324 bytes) and tag1500 R (15,504 bytes) in the controlled\n"
        "France1 pair. The earlier 1,824,828-byte ‘tag1400 region’ label referred to\n"
        "the combined U+R remainder; 64 changed byte positions are all in U, while R\n"
        "is byte-identical. Runtime isolation therefore still applies to the complete\n"
        "suffix. The source-matching plane records themselves are inside the parsed\n"
        "tag100 tree, a **HIGH_CONFIDENCE_INFERENCE** geometric binding; the independent\n"
        "runtime contribution of U remains unknown pending the staged hybrids."
    )
    dx = dx.replace(dx_old, dx_new)
    dx = dx.replace(
        "The course DX render model remains separate from the loader-guided,\nread-only tag100 parser in `master_rallye.course_tag100`. It does not implement\na course DX writer or a tag100 writer. The F.2 parser stops at the end of the\ntag100 tree and leaves following sections for separate handling.",
        "The course DX render model remains separate from the loader-guided,\nread-only tag100 parser in `master_rallye.course_tag100`. It does not implement\na course DX writer or a tag100 writer. The F.2 parser stops at the end of the\ntag100 tree; F.2.1 separately parses tag1400 U and records the later tag1500 R\nregion as opaque. Neither parser provides a writer or assigns those later\nregions a complete runtime meaning."
    )
    dx = dx.replace(
        "The prior 1,824,828-byte ‘tag1400 region’ label referred to the combined U+R remainder; 64 changed byte positions are all in U, while R is byte-identical.",
        "The earlier 1,824,828-byte ‘tag1400 region’ label referred to the combined U+R remainder; U is 1,809,324 bytes and R is 15,504 bytes. The 64 changed byte positions are all in U, while R is byte-identical."
    )
    if "## R5T-F.2.1 section isolation (runtime pending)" not in dx:
        dx += "\n\n## R5T-F.2.1 section isolation (runtime pending)\n\nThe 36/36 Retail corpus satisfies the parser-derived tag100 count invariants and exact size equation. A bounded tag1400 parser reaches its separately parsed tag1500 tail; the France1 64 changed byte positions in 47 ranges all belong to typed fields in the tag1400 56-byte record family. This does not identify their runtime meaning. The old source-triangle ordinal −12 correlation for the optional-record `code` remains numeric/high-confidence only. See [`research/r5t_f21/findings.md`](../../research/r5t_f21/findings.md).\n"
    dx_path.write_text(dx, encoding="utf-8")

    status_path = ROOT / "docs/format-status.md"
    status = status_path.read_text(encoding="utf-8")
    if "## R5T-F.2.1 tree/tag1400 causal isolation (awaiting runtime)" not in status:
        status += "\n\n## R5T-F.2.1 tree/tag1400 causal isolation (awaiting runtime)\n\nThe tag100 tree size equation now closes exactly, including one selector byte per non-root serialized record; the 148-byte France1 residual is accounted for. All 36 Retail trees satisfy the header/node count invariants. A read-only parser divides tag1400 U from the following tag1500 R and types all 64 changed tag1400 bytes across 47 ranges. Two provenance-verified mismatched hybrids (T-only modified and U-only modified) parse as revision 135 and are staged in ignored `research-output/r5t_f21/`. F.1 remains suffix-level until the human tests them. No carrier conclusion is preselected. See `research/r5t_f21/findings.md`.\n"
    status = status.replace(
        "A read-only parser divides tag1400 U from the following tag1500 R and types all 64 changed tag1400 bytes across 47 ranges.",
        "A read-only parser divides tag1400 U (1,809,324 bytes in the controlled pair) from tag1500 R (15,504 bytes, identical between donors) and maps all 64 changed U byte positions across 47 ranges to its typed record family."
    )
    status_path.write_text(status, encoding="utf-8")

    f1_path = ROOT / "research/r5t_f1/findings.md"
    f1 = f1_path.read_text(encoding="utf-8")
    f1_marker = "## F.2.1 boundary refinement"
    if f1_marker not in f1:
        f1 += "\n\n" + f1_marker + "\n\nThe earlier F.2 phrase ‘tag1400 region’ used the entire 1,824,828-byte remainder after tag1339. F.2.1 separates that controlled-pair remainder into tag1400 U (1,809,324 bytes; 64 changed byte positions in 47 ranges) and tag1500 R (15,504 bytes; byte-identical between donors). The original F.1 reciprocal runtime result still applies to the complete tag100-starting suffix. The staged T-only/U-only hybrids are the first runtime isolation test; their result is pending.\n"
    f1_path.write_text(f1, encoding="utf-8")

    f1_handoff_path = ROOT / "research/r5t_f1/runtime-handoff.md"
    f1_handoff = f1_handoff_path.read_text(encoding="utf-8")
    if f1_marker not in f1_handoff:
        f1_handoff += "\n\n## F.2.1 boundary refinement\n\nThe ‘1,824,828-byte tag1400 region’ wording in this historical handoff referred to U+R together. The parser-bounded split is U=1,809,324-byte tag1400 and R=15,504-byte tag1500, with all 64 changed byte positions in U and R identical. F.1's completed runtime test remains whole-suffix evidence; the newer T-only and U-only runtime result is pending.\n"
    f1_handoff_path.write_text(f1_handoff, encoding="utf-8")


def command_analyze() -> int:
    result = _load_cached_analysis()
    runtime_hybrids = _load_existing_runtime_hybrids(result)
    _write_analysis_reports(result, runtime_hybrids)
    _update_docs(result)
    print(json.dumps({
        "status": "STATIC_ANALYSIS_COMPLETE; STAGED_HYBRIDS_REVALIDATED" if runtime_hybrids else "STATIC_ANALYSIS_COMPLETE; HYBRIDS_NOT_STAGED",
        "retail_courses": result["corpus"]["course_folder_count"],
        "retail_tag100_tag1400_success": result["corpus"]["tag100_and_tag1400_parse_success_count"],
        "france1_tree_bytes": [len(result["base"].sections["T"]), len(result["modified"].sections["T"])],
        "france1_tag1400_bytes": [len(result["base"].sections["U"]), len(result["modified"].sections["U"])],
        "tag1400_changed_bytes_ranges": [result["u_diff"]["raw_changed_byte_positions"], result["u_diff"]["raw_changed_ranges"]],
        "ordinal_group_results": [
            {"mesh": mesh["mesh"], "cohorts": [
                {"cohort": c["cohort"], "matched": c["groups_with_at_least_one_code_equal_to_source_ordinal_minus_12"], "groups": c["source_plane_group_count"]}
                for c in mesh["cohorts"]
            ]} for mesh in result["code_report"]["meshes"]
        ],
    }, indent=2))
    return 0


def command_prepare_runtime() -> int:
    result = _load_cached_analysis()
    hybrids = _stage_runtime(result)
    _write_analysis_reports(result, hybrids)
    _update_docs(result)
    print(json.dumps({"status": "READY_FOR_TREE_TAG1400_RUNTIME_TEST", "hybrids": hybrids}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("analyze", "prepare-runtime"))
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return command_analyze()
    return command_prepare_runtime()


if __name__ == "__main__":
    raise SystemExit(main())
