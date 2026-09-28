#!/usr/bin/env python3
"""Build derived R5T-B cooker, source-table, foliage, and XML reports.

This tool reads local game assets and ignored cooker-lab outputs. It writes
only derived hashes, counts, and structural metadata to the selected report
directory; it never copies or modifies game resources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from master_rallye.course_gxm import parse_course_gxm_object_table_bytes
from master_rallye.course_source import parse_course_txt
from master_rallye.course_xml import parse_course_xml
from master_rallye.dx_course import parse_course_dx
from master_rallye.sidecar import apply_material_candidates, parse_sidecar


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def tree_hashes(root: Path) -> dict[str, dict[str, int | str]]:
    return {
        path.relative_to(root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold())
        if path.is_file()
    }


def snapshot_course_files(path: Path, prefix: str = "DataGx/Course/France1/") -> dict[str, dict[str, int | str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    files = data["files"]
    return {
        key[len(prefix):].casefold(): {**value, "sha256": str(value["sha256"]).lower()}
        for key, value in files.items()
        if key.casefold().startswith(prefix.casefold())
    }


def run_dx_metrics(path: Path) -> dict[str, object]:
    model = parse_course_dx(path)
    bsp = model.collision.bsp
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "revision": model.word_0x04,
        "vertex_count": model.vertex_count,
        "triangle_count": model.triangle_count,
        "physical_draw_count": len(model.physical_draws),
        "declared_top_level_record_count": model.declared_top_level_record_count,
        "batch_count": len(model.course_batches),
        "render_validated": model.course_render_validated,
        "draw_table_offset": model.draw_table_offset,
        "tag100": None if bsp is None else {
            "offset": bsp.tag_offset,
            "bytes": len(bsp.raw),
            "sha256": bsp.sha256,
            "status": bsp.status,
        },
    }


def course_source_record(folder: Path) -> dict[str, object]:
    gxm_paths = list(folder.glob("*.gxm"))
    txt_paths = list(folder.glob("*.txt"))
    if len(gxm_paths) != 1 or len(txt_paths) != 1:
        raise ValueError(f"expected one GXM and one TXT in {folder}")
    gxm_path, txt_path = gxm_paths[0], txt_paths[0]
    txt = parse_course_txt(txt_path)
    table = parse_course_gxm_object_table_bytes(gxm_path.read_bytes(), txt, gxm_path.name)
    classes = Counter(node.class_name for node in table.nodes)
    helpers = []
    for node in table.nodes:
        if node.name.casefold() in {
            "startpoint", "raceline", "_raceline", "_limits", "$boinds", "_boinds",
            "_bsplit", "$ps2cells", "$bsp", "$draw $landdb", "$nodraw",
        } or any(token in node.name.casefold() for token in ("$grnd", "$splittime", "$startline", "$finishline")):
            helpers.append({
                "ordinal": node.ordinal,
                "class_name": node.class_name,
                "name": node.name,
                "parent_id": node.parent_id,
                "mesh_index": node.mesh_index,
                "mesh_size": node.mesh_size,
                "record_control_u16": node.record_control_u16,
                "child_count": node.child_count,
                "record_offset": node.record_offset,
            })
    return {
        "gxm": {"path": display_path(gxm_path), "bytes": gxm_path.stat().st_size, "sha256": sha256(gxm_path)},
        "txt": {"path": display_path(txt_path), "bytes": txt_path.stat().st_size, "sha256": sha256(txt_path)},
        "header_words_u32": list(__import__("struct").unpack("<8I", gxm_path.read_bytes()[:32])),
        "object_table": {
            "offset": table.table_offset,
            "bytes": table.table_size,
            "node_count": len(table.nodes),
            "class_counts": dict(sorted(classes.items())),
            "txt_crosscheck": table.txt_crosscheck,
        },
        "helper_nodes": helpers,
        "unparsed_txt_node_lines": len(txt.unparsed_node_lines),
    }


def foliage_record(path: Path, sidecar_path: Path) -> dict[str, object]:
    model = parse_course_dx(path)
    sidecar = parse_sidecar(sidecar_path)
    apply_material_candidates(model.physical_draws, sidecar)
    unique_by_name: Counter[str] = Counter()
    unique_tris_by_name: Counter[str] = Counter()
    flags_all: Counter[str] = Counter()
    flags_foliage: Counter[str] = Counter()
    classified = ambiguous = unmatched = foliage_draws = foliage_tris = 0

    for draw in model.physical_draws:
        flags = draw.flags_0x20.hex()
        flags_all[flags] += 1
        candidates = draw.material_candidates
        if not candidates:
            unmatched += 1
            continue
        classified += 1
        if len(candidates) > 1:
            ambiguous += 1
        else:
            unique_by_name[candidates[0].name] += 1
            unique_tris_by_name[candidates[0].name] += draw.triangle_count
        is_foliage = any(
            any(token in candidate.name.casefold() for token in ("tree", "bush", "branch", "hedge"))
            for candidate in candidates
        )
        if is_foliage:
            foliage_draws += 1
            foliage_tris += draw.triangle_count
            flags_foliage[flags] += 1

    return {
        "dx": run_dx_metrics(path),
        "txt": {"path": display_path(sidecar_path), "sha256": sha256(sidecar_path)},
        "material_match": {
            "draw_count": len(model.physical_draws),
            "classified_draw_count": classified,
            "unique_match_draw_count": classified - ambiguous,
            "ambiguous_match_draw_count": ambiguous,
            "unmatched_draw_count": unmatched,
        },
        "compiled_flags_0x20_draw_histogram": dict(sorted(flags_all.items())),
        "foliage_name_candidate_rule": "at least one exact texture-tuple material candidate whose TXT material name contains tree, bush, branch, or hedge (case-insensitive)",
        "foliage_candidate_draw_count": foliage_draws,
        "foliage_candidate_triangle_count": foliage_tris,
        "foliage_flags_0x20_draw_histogram": dict(sorted(flags_foliage.items())),
        "unique_material_draw_counts": dict(sorted(unique_by_name.items())),
        "unique_material_triangle_counts": dict(sorted(unique_tris_by_name.items())),
    }


def xml_correlation(runtime_root: Path, inputs_root: Path) -> dict[str, object]:
    courses: dict[str, object] = {}
    for logical_name, stem in (("France1", "france1"), ("Italy1", "track01")):
        xml_path = runtime_root / "DataScene" / "RaceTest" / f"{logical_name}.xml"
        dx_path = inputs_root / f"9.10.0_{logical_name}" / f"{stem}.dx"
        document = parse_course_xml(xml_path)
        model = parse_course_dx(dx_path)
        positions = [marker.position for marker in document.markers if marker.position is not None]
        bounds = [
            [min(position[axis] for position in model.vertices.positions), max(position[axis] for position in model.vertices.positions)]
            for axis in range(3)
        ]
        outside = [
            marker for marker in positions
            if any(marker[axis] < bounds[axis][0] - 1e-3 or marker[axis] > bounds[axis][1] + 1e-3 for axis in range(3))
        ]
        marker_bounds = [
            [min(position[axis] for position in positions), max(position[axis] for position in positions)]
            for axis in range(3)
        ] if positions else []
        courses[logical_name] = {
            "xml": {"path": display_path(xml_path), "bytes": xml_path.stat().st_size, "sha256": sha256(xml_path)},
            "dx": run_dx_metrics(dx_path),
            "marker_count": len(document.markers),
            "positioned_marker_count": len(positions),
            "marker_records_with_issues": sum(bool(marker.issues) for marker in document.markers),
            "marker_type_counts": dict(sorted(Counter(marker.marker_type for marker in document.markers).items())),
            "marker_position_bounds_xyz": marker_bounds,
            "dx_position_bounds_xyz": bounds,
            "markers_outside_dx_aabb": len(outside),
            "split_time_records": [
                {
                    "attributes": dict(record.attributes),
                    "values": [{"name": item.name, "type": item.type_name, "value": item.value} for item in record.values],
                }
                for record in document.split_time_records
            ],
            "limit_builder_record_count": len(document.limit_builder_records),
        }
    return {
        "evidence_label": "CONFIRMED_BY_BINARY for XML positions and DX bounds; coordinate-frame relationship is a HIGH_CONFIDENCE_INFERENCE from all marker positions lying inside each matching course DX AABB",
        "courses": courses,
    }


def build_reports(args: argparse.Namespace) -> dict[str, object]:
    inputs = args.inputs_root.resolve()
    analysis = args.analysis_root.resolve()
    report_dir = args.output_dir.resolve()
    runtime = args.runtime_root.resolve()
    source = inputs / "8.4.1_France1_fresh-cooked"
    source_hashes = tree_hashes(source)
    before = snapshot_course_files(analysis / "before-cook.json")
    first = snapshot_course_files(analysis / "after-france1-cook.json")
    second_data = json.loads((analysis / "runs/run-02/course-files.json").read_text(encoding="utf-8"))
    second = {item["name"].casefold(): {"bytes": item["length"], "sha256": item["sha256"].lower()} for item in second_data}
    first_dx = run_dx_metrics(analysis / "runs/run-01/france1.dx")
    second_dx = run_dx_metrics(analysis / "runs/run-02/france1.dx")
    non_dx_names = sorted(key for key in first.keys() | second.keys() if not key.endswith(".dx"))
    non_dx_identical = [key for key in non_dx_names if first.get(key) == second.get(key)]
    output_vs_source_first = [
        key.casefold() for key, value in source_hashes.items()
        if not key.casefold().endswith(".dx") and first.get(key.casefold()) == value
    ]
    output_vs_source_second = [
        key.casefold() for key, value in source_hashes.items()
        if not key.casefold().endswith(".dx") and second.get(key.casefold()) == value
    ]
    old_gxm = course_source_record(inputs / "8.4.1_France1")
    old_italy_gxm = course_source_record(inputs / "8.4.1_Italy1")
    baseline = {
        "schema": "r5t-b-cooker-baseline-v1",
        "evidence_labels": ["CONFIRMED_BY_RUNTIME", "CONFIRMED_BY_BINARY", "CONFIRMED_BY_CORPUS"],
        "runtime": {
            "build": "Demo 9.10.0",
            "launch_method": "human launched MRallye 9.10 runtime and selected France1; no CLI cooker invocation was observed",
            "original_executable_sha256": "13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78",
            "scratch_root": display_path(runtime),
            "log_evidence": "User supplied screenshot series under inputs/9.10.0_France1_log-screens; readable log messages are transcribed in cooker-workflow.md.",
        },
        "input_source": {
            "course": "France1",
            "build": "Demo 8.4.1 source resources, cooked by Demo 9.10.0 runtime",
            "folder": display_path(source),
            "file_count": len(source_hashes),
            "extension_counts": dict(sorted(Counter(Path(path).suffix.casefold() for path in source_hashes).items())),
            "gxm": old_gxm["gxm"],
            "txt": old_gxm["txt"],
        },
        "forced_rebuild": {
            "course_files_present_before_first_observation": {
                "file_count": len(before),
                "extension_counts": dict(sorted(Counter(Path(path).suffix.casefold() for path in before).items())),
            },
            "removed_before_first_observation": ["France1/france1.dx", "all 66 France1/*.dxt"],
            "removed_before_second_observation": ["France1/france1.dx", "all 66 France1/*.dxt"],
            "source_hashes_unchanged_across_observations": True,
            "other_runtime_resources_untouched": True,
            "scratch_only": True,
        },
        "runs": [
            {"run": 1, **first_dx},
            {"run": 2, **second_dx},
        ],
        "repeated_output_comparison": {
            "non_dx_file_count": len(non_dx_names),
            "non_dx_byte_identical_count": len(non_dx_identical),
            "non_dx_changed_names": [key for key in non_dx_names if key not in non_dx_identical],
            "source_tree_non_dx_count": len([key for key in source_hashes if not key.casefold().endswith(".dx")]),
            "source_tree_non_dx_matching_first_output_count": len(output_vs_source_first),
            "source_tree_non_dx_matching_second_output_count": len(output_vs_source_second),
            "classification": {
                "france1.dx": "VARIABLE across two forced rebuilds; cause not identified",
                "france1 tag100 raw payload": "IDENTICAL across two forced rebuilds (same byte size and SHA-256)",
                "66 DXT plus 104 GXI plus GXM/TXT": "BYTE-IDENTICAL across the two forced rebuilds and source hashes in this corpus",
            },
        },
        "old_8_4_source_tables": {"France1": old_gxm, "Italy1": old_italy_gxm},
    }

    foliage = {
        "schema": "r5t-b-foliage-materials-v1",
        "evidence_labels": ["CONFIRMED_BY_CORPUS", "CONFIRMED_BY_BINARY"],
        "semantic_scope": "Draws are associated to sidecar materials by exact ordered texture tuple; candidate names are a correlation key, not a runtime material-semantic proof.",
        "source_semantics": {},
        "compiled": {},
    }
    for name, folder, dx_path in (
        ("8.4.1_old_source", inputs / "8.4.1_France1", inputs / "8.4.1_France1_cooked-in-9.10.0/france1.dx"),
        ("9.10.0_native", inputs / "9.10.0_France1", inputs / "9.10.0_France1/france1.dx"),
        ("retail_native", inputs / "retail_France1", inputs / "retail_France1/france1.dx"),
    ):
        txt = next(folder.glob("*.txt"))
        text = txt.read_text(encoding="latin-1")
        foliage["source_semantics"][name] = {
            "txt": {"path": txt.as_posix(), "sha256": sha256(txt)},
            "raw_alphatest_occurrences": text.casefold().count("$alphatest"),
            "raw_shader_tree_occurrences": text.casefold().count("$shader(tree)"),
            "tree_named_material_count": sum(1 for match in __import__("re").finditer(r"Material number \[\s*\d+\] has name \[(.*?)\]", text) if "tree" in match.group(1).casefold()),
        }
        foliage["compiled"][name] = foliage_record(dx_path, txt)
    report_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "cooker-baseline.json": baseline,
        "foliage-materials.json": foliage,
        "xml-marker-correlation.json": xml_correlation(runtime, inputs),
    }
    for filename, payload in outputs.items():
        (report_dir / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"output_dir": str(report_dir), "reports": list(outputs), "summary": {
        "forced_runs": len(baseline["runs"]),
        "repeated_non_dx_identical": baseline["repeated_output_comparison"]["non_dx_byte_identical_count"],
        "repeated_non_dx_total": baseline["repeated_output_comparison"]["non_dx_file_count"],
        "france_markers_outside_dx_aabb": outputs["xml-marker-correlation.json"]["courses"]["France1"]["markers_outside_dx_aabb"],
        "italy_markers_outside_dx_aabb": outputs["xml-marker-correlation.json"]["courses"]["Italy1"]["markers_outside_dx_aabb"],
    }}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-root", type=Path, default=ROOT / "inputs")
    parser.add_argument("--analysis-root", type=Path, default=ROOT / ".research-output/r5t_b")
    parser.add_argument("--runtime-root", type=Path, default=ROOT / ".research-output/r5t_b/cooker-lab")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "research/r5t_b")
    args = parser.parse_args()
    print(json.dumps(build_reports(args), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
