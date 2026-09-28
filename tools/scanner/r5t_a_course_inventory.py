"""Create a read-only inventory of course resources across supplied builds."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from master_rallye.dx import parse_dx  # noqa: E402
from master_rallye.dx_course import parse_course_dx  # noqa: E402
from master_rallye.hnt import parse_hnt, resolve_hnt_entries  # noqa: E402
from master_rallye.sidecar import parse_sidecar  # noqa: E402
from master_rallye.sfl import parse_sfl  # noqa: E402


BUILD_NAMES = {
    "demo-8.4.1": "Demo 8.4.1",
    "demo-9.3.1": "Demo 9.3.1",
    "demo-9.10.0": "Demo 9.10.0",
    "retail": "Retail",
}
COURSE_EXTENSIONS = {".dx", ".txt", ".gxm", ".dxt"}
SPATIAL_EXTENSIONS = {".sfl", ".fl", ".sf"}
DEVELOPER_TERMS = (
    "gordontrack", "flattrack", "russiaturkey", "boinds", "collisiontests",
    "racelineexample", "bsptopologytester", "gaboundaryfacepollutanttester",
    "gabspintersectiontester", "gabspnodrawfacetester",
)


def normalize_name(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path, base: Path, *, include_hash: bool = True) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": path.relative_to(base).as_posix(),
        "size_bytes": path.stat().st_size,
    }
    if include_hash:
        record["sha256"] = sha256(path)
    return record


def xml_structure(path: Path) -> dict[str, Any]:
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except (ET.ParseError, OSError) as error:
        return {"status": "error", "error": str(error)}

    tags: Counter[str] = Counter()
    attributes: Counter[str] = Counter()
    explicit_refs: list[str] = []
    element_count = 0
    for element in root.iter():
        element_count += 1
        tags[element.tag] += 1
        for name, value in element.attrib.items():
            attributes[name] += 1
            if re.search(r"\.(?:dx|dxt|hnt|sfl|xml)(?:$|[?#])", value, re.I):
                explicit_refs.append(value)
    return {
        "status": "parsed",
        "root_tag": root.tag,
        "root_attributes": dict(sorted(root.attrib.items())),
        "element_count": element_count,
        "element_names": dict(sorted(tags.items())),
        "attribute_names": dict(sorted(attributes.items())),
        "explicit_resource_reference_values": sorted(set(explicit_refs)),
    }


def txt_structure(path: Path) -> dict[str, Any]:
    try:
        sidecar = parse_sidecar(path)
        text = path.read_text(encoding="latin-1")
        directives = sorted({
            line.strip() for line in text.splitlines()
            if re.search(r"\$(?:bsp|startline|finishline|splittime|grnd|grndu|grndv|landdb|draw|nodraw)", line, re.I)
        })
        return {
            "parse_status": "parsed",
            "declared_material_count": sidecar.declared_material_count,
            "material_count": len(sidecar.materials),
            "mesh_count": len(sidecar.meshes),
            "mesh_span": sidecar.mesh_span,
            "mesh_names": [mesh.name for mesh in sidecar.meshes],
            "source_directive_lines": directives,
        }
    except (OSError, ValueError) as error:
        return {
            "parse_status": "error",
            "error": str(error),
        }


def dx_header(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 16:
        return {"status": "truncated", "byte_size": len(data), "first_16_hex": data.hex(" ")}
    magic, revision, word_0x08, vertex_count = __import__("struct").unpack_from("<4I", data, 0)
    return {
        "status": "header-read",
        "magic": f"0x{magic:08X}",
        "revision": revision,
        "word_0x08": word_0x08,
        "vertex_count": vertex_count,
        "file_size": len(data),
        "first_16_hex": data[:16].hex(" "),
    }


def match_named_files(directory: Path, course_key: str, extensions: set[str]) -> list[Path]:
    if not directory.is_dir():
        return []
    result = []
    for path in directory.iterdir():
        if path.is_file() and path.suffix.casefold() in extensions:
            stem = path.name[:-1] if path.name.casefold().endswith(".xml#") else path.stem
            if normalize_name(stem) == course_key:
                result.append(path)
    return sorted(result, key=lambda item: item.name.casefold())


def build_paths(corpus_root: Path, build_key: str) -> tuple[Path, Path]:
    build_root = corpus_root / build_key
    data_root = build_root / "Data.sma_unpacked" if build_key == "retail" else build_root
    return build_root, data_root


def inspect_course_folder(
    build_root: Path,
    data_root: Path,
    course_dir: Path,
    data_gx_root: Path,
    hash_cache: dict[Path, str],
) -> dict[str, Any]:
    course_key = normalize_name(course_dir.name)
    artifacts: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(course_dir.iterdir(), key=lambda item: item.name.casefold()):
        if not path.is_file() or path.suffix.casefold() not in COURSE_EXTENSIONS:
            continue
        record = file_record(path, data_root, include_hash=False)
        record["sha256"] = hash_cache.setdefault(path, sha256(path))
        if path.suffix.casefold() == ".dx":
            record["header"] = dx_header(path)
            try:
                model = parse_dx(path)
                record["vehicle_parser"] = {"status": "parsed", "summary": model.to_summary()}
            except Exception as error:
                record["vehicle_parser"] = {
                    "status": "unsupported",
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            try:
                model = parse_course_dx(path)
                record["course_parser"] = {
                    "status": "parsed" if model.course_render_validated else "invalid",
                    "draw_count": len(model.physical_draws),
                    "triangle_count": model.triangle_count,
                    "vertex_count": model.vertex_count,
                    "uv_set_count": len(model.uv_sets),
                    "local_index_count": len(model.local_indices),
                    "root_wrapper_tag": model.course_wrapper.tag if model.course_wrapper else None,
                    "root_record_count": len(model.course_root_records),
                    "batch_count": len(model.course_batches),
                    "batch_record_counts": [batch.record_count for batch in model.course_batches],
                    "trailing_size": len(model.trailing.data),
                    "collision_tags": list(model.collision.tag_ids),
                    "validation_errors": list(model.diagnostics.errors),
                }
            except Exception as error:
                record["course_parser"] = {
                    "status": "unsupported",
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
        elif path.suffix.casefold() == ".txt":
            record.update(txt_structure(path))
        artifacts.setdefault(path.suffix.casefold(), []).append(record)

    for texture in artifacts.get(".dxt", []):
        texture.pop("sha256", None)
        # The per-texture hashes are retained in the separate texture catalog below.

    texture_files = [
        file_record(path, data_root, include_hash=False)
        for path in sorted(course_dir.glob("*.dxt"), key=lambda item: item.name.casefold())
    ]
    for record, path in zip(texture_files, sorted(course_dir.glob("*.dxt"), key=lambda item: item.name.casefold())):
        record["sha256"] = hash_cache.setdefault(path, sha256(path))

    race_dir = data_root / "DataScene" / "RaceTest"
    xml_paths = match_named_files(race_dir, course_key, {".xml"})
    hnt_paths = match_named_files(race_dir, course_key, {".hnt"})
    spatial_paths: list[Path] = []
    for directory in (data_root / "DataScene" / "ICont", data_root / "DataScene"):
        spatial_paths.extend(match_named_files(directory, course_key, SPATIAL_EXTENSIONS))
    spatial_paths = sorted(set(spatial_paths), key=lambda item: item.as_posix().casefold())

    scenes = []
    for path in xml_paths:
        scenes.append({
            **file_record(path, data_root, include_hash=False),
            "sha256": hash_cache.setdefault(path, sha256(path)),
            "structure": xml_structure(path),
        })
    manifests = []
    for path in hnt_paths:
        document = parse_hnt(path)
        resolutions = resolve_hnt_entries(document, data_gx_root)
        manifests.append({
            **file_record(path, data_root, include_hash=False),
            "sha256": hash_cache.setdefault(path, sha256(path)),
            "entry_count": len(document.entries),
            "entries": [
                {
                    "line_number": result.entry.line_number,
                    "keyword": result.entry.keyword,
                    "value": result.entry.value,
                    "raw_line": result.entry.raw_line,
                    "status": result.status,
                    "resolved_path": result.resolved_path,
                    "candidates": list(result.candidates),
                }
                for result in resolutions
            ],
            "unparsed_lines": list(document.unparsed_lines),
        })

    spatial = []
    for path in spatial_paths:
        record = {
            **file_record(path, data_root, include_hash=False),
            "sha256": hash_cache.setdefault(path, sha256(path)),
        }
        if path.suffix.casefold() == ".sfl":
            try:
                field = parse_sfl(path)
                record["parse"] = {
                    "status": "parsed",
                    "width": field.header.width,
                    "height": field.header.height,
                    "first_float": field.header.first_float,
                    "unknown_float_0x0c": field.header.unknown_float_0x0c,
                    "unknown_float_0x10": field.header.unknown_float_0x10,
                    "distinct_values": field.distinct_value_count,
                    "min_value": field.value_min,
                    "max_value": field.value_max,
                }
            except Exception as error:
                record["parse"] = {"status": "error", "error": str(error)}
        spatial.append(record)

    return {
        "logical_course_name": course_dir.name,
        "normalized_course_key": course_key,
        "resource_folder": course_dir.relative_to(data_root).as_posix(),
        "artifacts": artifacts,
        "dxt_count": len(texture_files),
        "dxt": texture_files,
        "race_test_xml": scenes,
        "hnt": manifests,
        "spatial_fields": spatial,
    }


def inspect_build(
    corpus_root: Path,
    build_key: str,
    hash_cache: dict[Path, str],
) -> dict[str, Any]:
    build_root, data_root = build_paths(corpus_root, build_key)
    data_gx_root = data_root / "DataGx"
    course_root = data_gx_root / "Course"
    if not course_root.is_dir():
        return {"name": BUILD_NAMES[build_key], "key": build_key, "status": "missing-course-root", "courses": []}

    courses = [
        inspect_course_folder(build_root, data_root, folder, data_gx_root, hash_cache)
        for folder in sorted(course_root.iterdir(), key=lambda item: item.name.casefold())
        if folder.is_dir()
    ]
    race_dir = data_root / "DataScene" / "RaceTest"
    icont_dir = data_root / "DataScene" / "ICont"
    summary = {
        "course_folders": len(courses),
        "course_dx": sum(len(course["artifacts"].get(".dx", [])) for course in courses),
        "course_txt": sum(len(course["artifacts"].get(".txt", [])) for course in courses),
        "course_gxm": sum(len(course["artifacts"].get(".gxm", [])) for course in courses),
        "course_dxt": sum(course["dxt_count"] for course in courses),
        "matched_racetest_xml": sum(bool(course["race_test_xml"]) for course in courses),
        "matched_hnt": sum(bool(course["hnt"]) for course in courses),
        "empty_hnt": sum(
            1 for course in courses for manifest in course["hnt"] if manifest["size_bytes"] == 0
        ),
        "matched_sfl": sum(
            1 for course in courses for item in course["spatial_fields"]
            if Path(item["path"]).suffix.casefold() == ".sfl"
        ),
        "matched_fl": sum(
            1 for course in courses for item in course["spatial_fields"]
            if Path(item["path"]).suffix.casefold() == ".fl"
        ),
        "matched_sf": sum(
            1 for course in courses for item in course["spatial_fields"]
            if Path(item["path"]).suffix.casefold() == ".sf"
        ),
        "all_racetest_xml_files": sum(1 for path in race_dir.glob("*.xml")) if race_dir.is_dir() else 0,
        "all_racetest_hnt_files": sum(1 for path in race_dir.glob("*.hnt")) if race_dir.is_dir() else 0,
        "all_icont_sfl_files": sum(1 for path in icont_dir.glob("*.sfl")) if icont_dir.is_dir() else 0,
        "all_icont_fl_files": sum(1 for path in icont_dir.glob("*.fl")) if icont_dir.is_dir() else 0,
        "all_icont_sf_files": sum(1 for path in icont_dir.glob("*.sf")) if icont_dir.is_dir() else 0,
    }
    return {
        "name": BUILD_NAMES[build_key],
        "key": build_key,
        "build_root_label": f"corpora/{build_key}",
        "data_root_label": f"corpora/{build_key}/Data.sma_unpacked" if build_key == "retail" else f"corpora/{build_key}",
        "summary": summary,
        "courses": courses,
    }


def inventory_developer_assets(corpus_root: Path) -> list[dict[str, Any]]:
    matches = []
    for build_key in BUILD_NAMES:
        build_root, _ = build_paths(corpus_root, build_key)
        for path in build_root.rglob("*"):
            if not path.is_file():
                continue
            normalized = path.as_posix().casefold()
            if any(term in normalized for term in DEVELOPER_TERMS):
                matches.append({
                    "build": build_key,
                    "path": path.relative_to(build_root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                })
    return matches


def find_course(build: dict[str, Any], name: str) -> dict[str, Any] | None:
    key = normalize_name(name)
    return next((item for item in build["courses"] if item["normalized_course_key"] == key), None)


def layer_records(course: dict[str, Any] | None) -> dict[str, dict[str, Any] | None]:
    if course is None:
        return {key: None for key in ("dx", "txt", "gxm", "xml", "hnt", "sfl", "fl", "sf")}
    result: dict[str, dict[str, Any] | None] = {}
    for key, extension in (("dx", ".dx"), ("txt", ".txt"), ("gxm", ".gxm")):
        records = course["artifacts"].get(extension, [])
        result[key] = records[0] if len(records) == 1 else {"ambiguous": records} if records else None
    for key in ("xml", "hnt"):
        records = course["race_test_xml"] if key == "xml" else course["hnt"]
        result[key] = records[0] if len(records) == 1 else {"ambiguous": records} if records else None
    for key in ("sfl", "fl", "sf"):
        records = [item for item in course["spatial_fields"] if Path(item["path"]).suffix.casefold() == f".{key}"]
        result[key] = records[0] if len(records) == 1 else {"ambiguous": records} if records else None
    return result


def evolution_json(inventory: dict[str, Any]) -> dict[str, Any]:
    builds = inventory["builds"]
    matrix = {}
    for course_name in ("France1", "Italy1"):
        versions = {}
        for build in builds:
            course = find_course(build, course_name)
            versions[build["key"]] = {
                "course_folder": course,
                "layers": layer_records(course),
            }
        matrix[course_name] = versions
    return {
        "schema": "r5t-a-course-evolution-v1",
        "evidence_labels": ["CONFIRMED_BY_BINARY", "CONFIRMED_BY_CORPUS", "UNKNOWN"],
        "courses": matrix,
    }


def write_course_report(path: Path, course_name: str, evolution: dict[str, Any]) -> None:
    layers = ("gxm", "dx", "txt", "hnt", "xml", "sfl", "fl", "sf")
    lines = [
        f"# {course_name} course evolution (R5T-A)",
        "",
        "All paths below are archive-relative. Hashes identify files in the supplied local corpus.",
        "Layer presence and same-build file pairing are `CONFIRMED_BY_CORPUS`; source-to-compiled and cooker semantics remain `UNKNOWN` unless separately stated.",
        "",
        "| Layer | 8.4.1 | 9.3.1 | 9.10.0 | Retail |",
        "|---|---|---|---|---|",
    ]
    for layer in layers:
        cells = []
        for build_key in BUILD_NAMES:
            version = evolution["courses"][course_name][build_key]
            record = version["layers"].get(layer)
            if record is None:
                cells.append("absent")
            elif "ambiguous" in record:
                cells.append(f"ambiguous ({len(record['ambiguous'])})")
            else:
                size = record.get("size_bytes", "?")
                digest = record.get("sha256", "")
                suffix = f"; rev {record.get('header', {}).get('revision')}" if layer == "dx" and record.get("header") else ""
                cells.append(f"{size} B{suffix}; `{digest[:12]}`")
        lines.append(f"| {layer.upper()} | " + " | ".join(cells) + " |")
    lines.extend([
        "",
        "## Resource inventory",
        "",
        "Dxt assets are recorded per course folder in `course-corpus.json`; each entry carries its byte size and SHA-256.",
        "Matching is exact after case-folding and removing filename separators. Unmatched or ambiguous paths stay explicit.",
        "",
    ])
    lines.extend([
        "## Structural snapshot",
        "",
        "| Build | DX rev | Vertices | Course DX parse / draws / triangles | TXT materials / mesh entries / span | SFL dimensions |",
        "|---|---:|---:|---|---|---|",
    ])
    for build_key in BUILD_NAMES:
        course = evolution["courses"][course_name][build_key]["course_folder"]
        if course is None:
            lines.append(f"| {BUILD_NAMES[build_key]} | — | — | absent | absent | absent |")
            continue
        dx_records = course["artifacts"].get(".dx", [])
        txt_records = course["artifacts"].get(".txt", [])
        dx = dx_records[0] if len(dx_records) == 1 else None
        txt = txt_records[0] if len(txt_records) == 1 else None
        header = dx.get("header", {}) if dx else {}
        parsed = dx.get("course_parser", {}) if dx else {}
        if parsed.get("status") == "parsed":
            dx_summary = f"parsed / {parsed['draw_count']} / {parsed['triangle_count']}"
        else:
            revision = header.get("revision")
            dx_summary = (
                f"unsupported revision {revision}"
                if revision is not None and revision != 135
                else f"unsupported: {parsed.get('error_type', 'no unique DX')}"
            )
        txt_summary = (
            f"{txt.get('material_count')}/{txt.get('declared_material_count')} / "
            f"{txt.get('mesh_count')} / {txt.get('mesh_span')}"
            if txt else "absent"
        )
        sfl = course["spatial_fields"]
        sfl = next((item for item in sfl if Path(item["path"]).suffix.casefold() == ".sfl"), None)
        sfl_parse = sfl.get("parse", {}) if sfl else {}
        sfl_dimensions = (
            f"{sfl_parse.get('width')}×{sfl_parse.get('height')}"
            if sfl_parse.get("status") == "parsed" else "absent"
        )
        lines.append(
            f"| {BUILD_NAMES[build_key]} | {header.get('revision', '—')} | "
            f"{header.get('vertex_count', '—')} | {dx_summary} | {txt_summary} | {sfl_dimensions} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def markdown_summary(inventory: dict[str, Any]) -> str:
    lines = [
        "# Course corpus inventory (R5T-A)",
        "",
        "External game files were read in place. Reports contain relative paths, structural metadata, and hashes only.",
        "",
        "| Build | Course folders | DX | TXT | GXM | DXT | matched XML | matched HNT | SFL | FL | SF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for build in inventory["builds"]:
        s = build["summary"]
        lines.append(
            f"| {build['name']} | {s['course_folders']} | {s['course_dx']} | {s['course_txt']} | "
            f"{s['course_gxm']} | {s['course_dxt']} | {s['matched_racetest_xml']} | "
            f"{s['matched_hnt']} ({s['empty_hnt']} empty) | {s['matched_sfl']} | {s['matched_fl']} | {s['matched_sf']} |"
        )
    lines.extend([
        "",
        "Counts are computed from each build's `DataGx/Course` directories and exact normalized-stem matches in `DataScene`.",
        "Retail reference point: all 36 course resource folders are represented individually, including flip variants.",
        "",
        "## France1 and Italy1",
        "",
        "See `france1-evolution.md` and `italy1-evolution.md` for layer-level sizes, revisions, and hashes.",
        "",
        "## Developer/test asset name matches",
        "",
    ])
    if not inventory["developer_asset_matches"]:
        lines.append("No requested developer/test names matched in the supplied corpora.")
    else:
        for item in inventory["developer_asset_matches"]:
            lines.append(f"- `{item['build']}/{item['path']}` ({item['size_bytes']} B; `{item['sha256'][:12]}`)")
    lines.extend([
        "",
        "The machine-readable report includes every course-folder DX/TXT/GXM/DXT file and matched XML/HNT/SFL/FL/SF resource, with SHA-256 and parse status where applicable.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=REPO_ROOT.parent / "corpora")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "research" / "r5t_a")
    args = parser.parse_args()

    corpus_root = args.corpus_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    hash_cache: dict[Path, str] = {}
    inventory = {
        "schema": "r5t-a-course-corpus-v1",
        "corpus_root_label": "../corpora",
        "evidence_labels": ["CONFIRMED_BY_BINARY", "CONFIRMED_BY_CORPUS", "UNKNOWN"],
        "builds": [inspect_build(corpus_root, build_key, hash_cache) for build_key in BUILD_NAMES],
        "developer_asset_matches": inventory_developer_assets(corpus_root),
    }
    json_path = output_dir / "course-corpus.json"
    json_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "course-corpus.md").write_text(markdown_summary(inventory), encoding="utf-8", newline="\n")

    evolution = evolution_json(inventory)
    (output_dir / "course-evolution.json").write_text(
        json.dumps(evolution, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    for course_name in ("France1", "Italy1"):
        write_course_report(output_dir / f"{course_name.casefold()}-evolution.md", course_name, evolution)

    print(json.dumps({
        "course_corpus_json": str(json_path),
        "course_count_by_build": {build["key"]: build.get("summary", {}).get("course_folders") for build in inventory["builds"]},
        "developer_asset_matches": len(inventory["developer_asset_matches"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
