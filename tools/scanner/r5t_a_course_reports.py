"""Generate course resource-graph, XML, SFL, legacy-field, and GXM reports."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from master_rallye.sfl import parse_sfl  # noqa: E402
from master_rallye.sidecar import parse_sidecar  # noqa: E402


BUILD_ORDER = ("demo-8.4.1", "demo-9.3.1", "demo-9.10.0", "retail")
BUILD_NAMES = {
    "demo-8.4.1": "Demo 8.4.1",
    "demo-9.3.1": "Demo 9.3.1",
    "demo-9.10.0": "Demo 9.10.0",
    "retail": "Retail",
}
DEVELOPER_HINTS = (
    "gordontrack", "flattrack", "russiaturkey", "boinds", "collisiontests",
    "racelineexample", "bsptopologytester", "gaboundaryfacepollutanttester",
    "gabspintersectiontester", "gabspnodrawfacetester",
)
REFERENCE_KEYS = ("model", "scene", "resource", "file", "texture", "path", "track", "course")
TRANSFORM_KEYS = ("row0", "row1", "row2", "row3")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def data_root(corpus_root: Path, build: str) -> Path:
    root = corpus_root / build
    return root / "Data.sma_unpacked" if build == "retail" else root


def normalize(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def xml_probe(path: Path, base: Path) -> dict[str, Any]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        return {"path": path.relative_to(base).as_posix(), "status": "error", "error": str(error)}

    elements: Counter[str] = Counter()
    attributes: Counter[str] = Counter()
    attribute_samples: dict[str, set[str]] = defaultdict(set)
    references: list[dict[str, str]] = []
    identifiers: list[dict[str, str]] = []
    transforms: list[dict[str, Any]] = []
    positions: list[dict[str, Any]] = []
    model_names: list[str] = []
    object_names: list[str] = []
    value_sample_count = 0

    for element in root.iter():
        tag = element.tag if isinstance(element.tag, str) else str(element.tag)
        folded_tag = tag.casefold()
        elements[tag] += 1
        attrs = {str(key): str(value) for key, value in element.attrib.items()}
        folded = {key.casefold(): value for key, value in attrs.items()}
        for key, value in attrs.items():
            attributes[key] += 1
            if len(attribute_samples[key]) < 12:
                attribute_samples[key].add(value)
            if any(token in key.casefold() for token in REFERENCE_KEYS):
                references.append({"element": tag, "attribute": key, "value": value})
            if any(token in key.casefold() for token in ("track", "course", "stage")):
                identifiers.append({"element": tag, "attribute": key, "value": value})
        name = folded.get("name")
        if name is not None and ("model" in folded_tag or "mesh" in folded_tag):
            model_names.append(name)
        if name is not None and ("object" in folded_tag or "node" in folded_tag):
            object_names.append(name)
        if all(key in folded for key in TRANSFORM_KEYS):
            if len(transforms) < 24:
                transforms.append({
                    "element": tag,
                    "name": name,
                    "rows": [folded[key] for key in TRANSFORM_KEYS],
                })
        if any(token in folded_tag for token in ("position", "translation", "transform")):
            if len(positions) < 24:
                positions.append({"element": tag, "attributes": attrs})
        if "value" in folded and value_sample_count < 24:
            value_sample_count += 1
            if any(token in folded_tag for token in ("marker", "transform", "position", "track")):
                positions.append({"element": tag, "name": name, "value": folded["value"]})

    explicit_resource_values = []
    for ref in references:
        if re.search(r"\.(?:dx|dxt|hnt|sfl|xml|fl|sf)(?:$|[?#])", ref["value"], re.I):
            explicit_resource_values.append(ref)

    return {
        "path": path.relative_to(base).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "status": "parsed",
        "root_tag": root.tag,
        "root_attributes": dict(sorted(root.attrib.items())),
        "element_count": sum(elements.values()),
        "element_names": dict(sorted(elements.items())),
        "attribute_names": dict(sorted(attributes.items())),
        "attribute_value_samples": {key: sorted(values) for key, values in sorted(attribute_samples.items())},
        "model_or_mesh_name_samples": sorted(set(model_names))[:100],
        "object_or_node_name_samples": sorted(set(object_names))[:100],
        "track_course_identifier_attributes": identifiers[:500],
        "raw_resource_reference_attributes": references[:1000],
        "explicit_extension_resource_references": explicit_resource_values[:500],
        "transform_row_samples": transforms,
        "position_named_element_or_value_samples": positions[:48],
    }


def discover_scene_xml(corpus_root: Path, course_corpus: dict[str, Any]) -> tuple[dict[str, Any], str]:
    builds = []
    aggregate_tags: Counter[str] = Counter()
    aggregate_attrs: Counter[str] = Counter()
    for build in course_corpus["builds"]:
        root = data_root(corpus_root, build["key"])
        race_dir = root / "DataScene" / "RaceTest"
        records = [xml_probe(path, root) for path in sorted(race_dir.glob("*.xml"), key=lambda item: item.name.casefold())]
        for record in records:
            aggregate_tags.update(record.get("element_names", {}))
            aggregate_attrs.update(record.get("attribute_names", {}))
        matched_by_course = {
            course["logical_course_name"]: [item["path"] for item in course["race_test_xml"]]
            for course in build["courses"]
        }
        builds.append({
            "build": build["key"],
            "race_test_xml_count": len(records),
            "matched_course_xml_count": sum(bool(paths) for paths in matched_by_course.values()),
            "matched_course_xml": matched_by_course,
            "files": records,
        })

    # Also inventory requested developer/test scene-name matches outside the main course folders.
    developer_xml = []
    for build_key in BUILD_ORDER:
        root = data_root(corpus_root, build_key)
        for directory in (root / "DataScene" / "RaceTest", root / "DataScene" / "Test"):
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.xml"), key=lambda item: item.name.casefold()):
                folded = path.as_posix().casefold()
                if any(hint in folded for hint in DEVELOPER_HINTS) or "test" in path.stem.casefold():
                    developer_xml.append({"build": build_key, **xml_probe(path, root)})

    report = {
        "schema": "r5t-a-racetest-xml-v1",
        "evidence": "CONFIRMED_BY_CORPUS: XML structure and literal values only; gameplay roles are not inferred",
        "builds": builds,
        "recurring_element_names": dict(aggregate_tags.most_common()),
        "recurring_attribute_names": dict(aggregate_attrs.most_common()),
        "developer_test_scene_inventory": developer_xml,
    }
    summary_lines = [
        "# RaceTest XML inventory (R5T-A)",
        "",
        "The report records XML tree shape and source attribute values. Names and values are retained as corpus evidence; gameplay semantics are not inferred.",
        "",
        "| Build | RaceTest XML files | Exact course-folder matches | Root |",
        "|---|---:|---:|---|",
    ]
    for item in builds:
        roots = Counter(file.get("root_tag") for file in item["files"] if file.get("status") == "parsed")
        summary_lines.append(
            f"| {BUILD_NAMES[item['build']]} | {item['race_test_xml_count']} | "
            f"{item['matched_course_xml_count']} | `{dict(roots)}` |"
        )
    summary_lines.extend([
        "",
        "## Repeating structure",
        "",
        f"- Most common element names across the scanned RaceTest XML: `{aggregate_tags.most_common(16)}`.",
        f"- Most common attribute names: `{aggregate_attrs.most_common(16)}`.",
        "- For each XML, JSON preserves root attributes, all element/attribute counts, exact-stem resource-like attributes, literal track/course identifier attributes, and bounded samples of transform rows and position-like values.",
        f"- Developer/test-name XML matches: {len(developer_xml)}; these are separately listed in JSON and remain inventory-only.",
        "",
        "## France1 / Italy1 and variants",
        "",
        "See per-file structures in `racetest-xml.json`; course names are paired to `DataGx/Course` by exact case-insensitive normalized stem.",
        "",
    ])
    return report, "\n".join(summary_lines)


def _exact_corpus_reference(value: str, file_index: dict[str, list[str]]) -> dict[str, Any]:
    literal = value.split("?", 1)[0].split("#", 1)[0].replace("\\", "/").strip("/")
    parts = literal.split("/") if literal else []
    if not parts or any(part in {".", ".."} for part in parts):
        return {"literal": value, "status": "unresolved", "reason": "unsafe_or_empty_path", "candidates": []}
    candidates = sorted(file_index.get(literal.casefold(), []), key=str.casefold)
    if len(candidates) == 1:
        status = "resolved"
        resolved_path = candidates[0]
    elif candidates:
        status = "ambiguous"
        resolved_path = None
    else:
        status = "unresolved"
        resolved_path = None
    return {"literal": value, "status": status, "resolved_path": resolved_path, "candidates": candidates}


def resource_graph(course_corpus: dict[str, Any], corpus_root: Path) -> tuple[dict[str, Any], str]:
    builds = []
    global_reference_users: dict[str, set[str]] = defaultdict(set)
    all_entries = Counter()
    for build in course_corpus["builds"]:
        root = data_root(corpus_root, build["key"])
        file_index: dict[str, list[str]] = defaultdict(list)
        for path in root.rglob("*"):
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                file_index[relative.casefold()].append(relative)
        courses = []
        summary = Counter()
        for course in build["courses"]:
            manifests = course["hnt"]
            manifest_entries = [entry for manifest in manifests for entry in manifest["entries"]]
            summary["course_folders"] += 1
            summary["scene_xml"] += bool(course["race_test_xml"])
            summary["hnt_files"] += len(manifests)
            summary["empty_hnt"] += sum(manifest["size_bytes"] == 0 for manifest in manifests)
            summary["model_dx"] += len(course["artifacts"].get(".dx", []))
            summary["sidecar_txt"] += len(course["artifacts"].get(".txt", []))
            summary["course_dxt"] += course["dxt_count"]
            summary["sfl_fl_sf"] += len(course["spatial_fields"])
            for entry in manifest_entries:
                key = entry["keyword"].casefold()
                summary[f"hnt_{key}"] += 1
                summary[f"resolution_{entry['status']}"] += 1
                all_entries[(build["key"], key, entry["status"])] += 1
                if entry.get("resolved_path"):
                    global_reference_users[f"{build['key']}:{entry['resolved_path'].casefold()}"].add(course["logical_course_name"])
            xml_references = [
                {"scene_xml": scene["path"], **_exact_corpus_reference(ref["value"], file_index)}
                for scene in course["race_test_xml"]
                for ref in scene["structure"].get("explicit_extension_resource_references", [])
            ]
            for reference in xml_references:
                summary[f"xml_reference_{reference['status']}"] += 1
            courses.append({
                "course": course["logical_course_name"],
                "matching_rule": "exact normalized course-folder stem",
                "scene_xml": [
                    {"path": item["path"], "sha256": item["sha256"], "size_bytes": item["size_bytes"]}
                    for item in course["race_test_xml"]
                ],
                "hnt": [
                    {
                        "path": manifest["path"],
                        "sha256": manifest["sha256"],
                        "size_bytes": manifest["size_bytes"],
                        "entries": manifest["entries"],
                        "unparsed_lines": manifest["unparsed_lines"],
                    }
                    for manifest in manifests
                ],
                "course_dx": [
                    {"path": item["path"], "size_bytes": item["size_bytes"], "sha256": item["sha256"], "header": item.get("header")}
                    for item in course["artifacts"].get(".dx", [])
                ],
                "txt": [
                    {key: item.get(key) for key in ("path", "size_bytes", "sha256", "parse_status", "declared_material_count", "material_count", "mesh_count", "mesh_span")}
                    for item in course["artifacts"].get(".txt", [])
                ],
                "dxt_count": course["dxt_count"],
                "spatial_fields": course["spatial_fields"],
                "explicit_xml_resource_reference_values": sorted({
                    value
                    for scene in course["race_test_xml"]
                    for value in scene["structure"].get("explicit_resource_reference_values", [])
                }),
                "xml_resource_references_exact_path": xml_references,
            })
        builds.append({"build": build["key"], "summary": dict(summary), "courses": courses})

    shared = [
        {"build_and_path": key, "course_users": sorted(users), "user_count": len(users)}
        for key, users in sorted(global_reference_users.items()) if len(users) > 1
    ]
    report = {
        "schema": "r5t-a-course-resource-graph-v1",
        "evidence": "CONFIRMED_BY_CORPUS: exact normalized-stem links and exact case-insensitive DataGx path resolution",
        "resolution_policy": "HNT Model -> .dx and Texture/FSTexture -> .dxt; explicit XML resource references use exact corpus-relative paths; no basename-only, extension, or fuzzy fallback",
        "builds": builds,
        "shared_dependencies": shared,
        "aggregate_hnt_counts": [
            {"build": build, "keyword": keyword, "status": status, "count": count}
            for (build, keyword, status), count in sorted(all_entries.items())
        ],
    }
    lines = [
        "# Course resource graph (R5T-A)",
        "",
        "Course folders are paired to RaceTest XML/HNT and ICont field files by an exact normalized stem. HNT paths resolve case-insensitively against the actual `DataGx` relative path; the resolver does not fall back to a matching basename.",
        "",
        "| Build | folders | scene XML | HNT | empty HNT | DX | TXT | DXT files | SFL/FL/SF | resolved HNT refs | unresolved HNT | ambiguous HNT | XML refs resolved/unresolved |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for build in builds:
        s = build["summary"]
        resolved = s.get("resolution_resolved", 0)
        unresolved = s.get("resolution_unresolved", 0)
        ambiguous = s.get("resolution_ambiguous", 0)
        lines.append(
            f"| {BUILD_NAMES[build['build']]} | {s.get('course_folders',0)} | {s.get('scene_xml',0)} | "
            f"{s.get('hnt_files',0)} | {s.get('empty_hnt',0)} | {s.get('model_dx',0)} | {s.get('sidecar_txt',0)} | "
            f"{s.get('course_dxt',0)} | {s.get('sfl_fl_sf',0)} | {resolved} | {unresolved} | {ambiguous} | "
            f"{s.get('xml_reference_resolved',0)}/{s.get('xml_reference_unresolved',0)} |"
        )
    lines.extend([
        "",
        "## Retail HNT graph",
        "",
    ])
    retail = next(item for item in builds if item["build"] == "retail")
    rs = retail["summary"]
    lines.extend([
        f"Retail contains {rs.get('hnt_files',0)} nonempty course HNT manifests, {rs.get('hnt_model',0)} Model entries, and {rs.get('hnt_texture',0)} Texture entries.",
        f"Exact path resolution: {rs.get('resolution_resolved',0)} resolved, {rs.get('resolution_unresolved',0)} unresolved, {rs.get('resolution_ambiguous',0)} ambiguous.",
        f"Shared resolved dependencies across course manifests: {len(shared)}.",
        "The single unresolved retail entry and every shared dependency are listed below and in JSON.",
        "",
    ])
    unresolved_records = [
        (build["build"], course["course"], manifest, entry)
        for build in builds for course in build["courses"] for manifest in course["hnt"] for entry in manifest["entries"]
        if entry["status"] != "resolved"
    ]
    for build_key, course_name, manifest, entry in unresolved_records:
        lines.append(
            f"- **{build_key} / {course_name}** `{manifest['path']}` line {entry['line_number']}: "
            f"`{entry['keyword']} [{entry['value']}]` -> {entry['status']}"
        )
    if not unresolved_records:
        lines.append("No unresolved or ambiguous references.")
    lines.extend(["", "## Shared dependencies", ""])
    for item in shared:
        lines.append(f"- `{item['build_and_path']}` used by {', '.join(item['course_users'])}.")
    if not shared:
        lines.append("None detected.")
    lines.extend([
        "",
        "HNT edges are dependency declarations; this report does not claim that every entry is runtime-essential.",
        "Explicit XML references are resolved only when their literal path exactly matches a corpus-relative file. Extensionless and other resource-like XML values remain uninterpreted in `racetest-xml.json`.",
        "",
    ])
    return report, "\n".join(lines)


def sfl_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    scanlines = b"".join(b"\x00" + pixels[row * width:(row + 1) * width] for row in range(height))
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanlines, 9))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def parse_legacy_field(path: Path, data_root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    record: dict[str, Any] = {
        "path": path.relative_to(data_root).as_posix(),
        "extension": path.suffix.casefold(),
        "size_bytes": len(data),
        "sha256": sha256_bytes(data),
        "first_64_hex": data[:64].hex(" "),
    }
    if len(data) < 20:
        record["parse_status"] = "shorter-than-20-byte-header"
        return record
    version, width_value, height_value, unknown_a, unknown_b = struct.unpack_from("<5f", data)
    if not math.isfinite(width_value) or not math.isfinite(height_value):
        record["parse_status"] = "nonfinite-dimension-candidates"
        return record
    width, height = round(width_value), round(height_value)
    cells = width * height
    exact = (
        width > 0 and height > 0
        and math.isclose(width_value, width, abs_tol=1e-5)
        and math.isclose(height_value, height, abs_tol=1e-5)
        and 20 + cells * 4 == len(data)
    )
    record.update({
        "parse_status": "20-byte-header-plus-4-byte-cells" if exact else "candidate-header-only",
        "header_f32": [version, width_value, height_value, unknown_a, unknown_b],
        "width_candidate": width,
        "height_candidate": height,
        "dimension_product": cells,
        "payload_bytes": len(data) - 20,
        "bytes_per_cell_if_dimensions_hold": (len(data) - 20) / cells if cells else None,
    })
    if exact:
        payload = data[20:]
        values = [item[0] for item in struct.iter_unpack("<f", payload)]
        finite_values = [value for value in values if math.isfinite(value)]
        counts = Counter(values)
        record.update({
            "payload_cell_count": len(values),
            "finite_float_count": len(finite_values),
            "nonfinite_float_count": len(values) - len(finite_values),
            "distinct_float32_values": len(counts),
            "frequent_float32_values": [
                {"value": value, "count": count}
                for value, count in counts.most_common(8)
            ],
            "float_range": [min(finite_values), max(finite_values)] if finite_values else None,
        })
    return record


def tga_header(path: Path, data_root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    result: dict[str, Any] = {
        "path": path.relative_to(data_root).as_posix(),
        "size_bytes": len(data),
        "sha256": sha256_bytes(data),
    }
    if len(data) >= 18:
        result.update({
            "image_type": data[2],
            "width": struct.unpack_from("<H", data, 12)[0],
            "height": struct.unpack_from("<H", data, 14)[0],
            "pixel_depth": data[16],
            "descriptor": data[17],
        })
    else:
        result["status"] = "shorter-than-tga-header"
    return result


def sfl_reports(corpus_root: Path, output_dir: Path, preview_dir: Path) -> tuple[dict[str, Any], str]:
    builds = []
    sfl_index: dict[tuple[str, str], dict[str, Any]] = {}
    for build in BUILD_ORDER:
        root = data_root(corpus_root, build)
        icont = root / "DataScene" / "ICont"
        fields = []
        if icont.is_dir():
            for path in sorted(icont.glob("*.sfl"), key=lambda item: item.name.casefold()):
                raw = path.read_bytes()
                parsed = parse_sfl(path)
                record = {
                    "path": path.relative_to(root).as_posix(),
                    "name": path.stem,
                    "size_bytes": len(raw),
                    "sha256": sha256_bytes(raw),
                    "payload_sha256": sha256_bytes(parsed.payload),
                    "header_hex": parsed.header.raw.hex(" "),
                    "first_float": parsed.header.first_float,
                    "width": parsed.header.width,
                    "height": parsed.header.height,
                    "unknown_float_0x0c": parsed.header.unknown_float_0x0c,
                    "unknown_float_0x10": parsed.header.unknown_float_0x10,
                    "payload_offset": parsed.payload_offset,
                    "payload_bytes": len(parsed.payload),
                    "min_value": parsed.value_min,
                    "max_value": parsed.value_max,
                    "distinct_value_count": parsed.distinct_value_count,
                    "value_counts": [[value, count] for value, count in parsed.value_counts],
                }
                fields.append(record)
                sfl_index[(build, normalize(path.stem))] = record
                if normalize(path.stem) in {"france1", "italy1", "francew", "francewflip", "italym1", "italym1flip", "italys3", "italys3flip"}:
                    sfl_png(preview_dir / build / f"{path.stem}.png", parsed.header.width, parsed.header.height, parsed.payload)

        legacy = []
        tgas = []
        if build == "demo-8.4.1":
            data_scene = root / "DataScene"
            for path in sorted(data_scene.rglob("*"), key=lambda item: item.as_posix().casefold()):
                if not path.is_file():
                    continue
                if path.suffix.casefold() in {".fl", ".sf"}:
                    legacy.append(parse_legacy_field(path, root))
                elif path.suffix.casefold() == ".tga" and re.search(r"(?:france1|italy1).*(?:fl|sf)|(?:france1|italy1)(?:fl|sf)", path.name, re.I):
                    tgas.append(tga_header(path, root))
        builds.append({"build": build, "sfl_count": len(fields), "sfl": fields, "legacy_fl_sf": legacy, "tga_visualizations": tgas})

    pairs = []
    retail_names = [item["name"] for item in next(item for item in builds if item["build"] == "retail")["sfl"]]
    retail_map = {normalize(item["name"]): item for item in next(item for item in builds if item["build"] == "retail")["sfl"]}
    for folded in sorted(retail_map):
        if not folded.endswith("flip"):
            continue
        base_name = folded[:-4]
        base = retail_map.get(base_name)
        flip = retail_map[folded]
        if base:
            pairs.append({
                "base": base["name"],
                "variant": flip["name"],
                "same_dimensions": (base["width"], base["height"]) == (flip["width"], flip["height"]),
                "same_header_bytes": base["header_hex"] == flip["header_hex"],
                "same_payload_hash": base["payload_sha256"] == flip["payload_sha256"],
                "base_payload_sha256": base["payload_sha256"],
                "variant_payload_sha256": flip["payload_sha256"],
            })

    cross_build = []
    for course in ("France1", "Italy1"):
        values = [sfl_index.get((build, normalize(course))) for build in BUILD_ORDER]
        cross_build.append({
            "course": course,
            "builds": [
                {
                    "build": build,
                    "present": value is not None,
                    "header_sha256": sha256_bytes(bytes.fromhex(value["header_hex"])) if value else None,
                    "payload_sha256": value["payload_sha256"] if value else None,
                    "size_bytes": value["size_bytes"] if value else None,
                }
                for build, value in zip(BUILD_ORDER, values)
            ],
            "all_present_payloads_identical": bool(values and all(value and value["payload_sha256"] == values[0]["payload_sha256"] for value in values)),
        })

    report = {
        "schema": "r5t-a-sfl-and-legacy-fields-v1",
        "sfl_structure": "20-byte header followed by exactly width*height bytes",
        "header_offsets": [
            {"offset": "0x00", "field": "float32 value 3.0 in observed retail corpus", "meaning": "UNKNOWN"},
            {"offset": "0x04", "field": "uint32 width", "meaning_confidence": "HIGH"},
            {"offset": "0x08", "field": "uint32 height", "meaning_confidence": "HIGH"},
            {"offset": "0x0C", "field": "float32", "meaning": "UNKNOWN coordinate-like value"},
            {"offset": "0x10", "field": "float32", "meaning": "UNKNOWN coordinate-like value"},
            {"offset": "0x14", "field": "payload bytes", "meaning": "UNKNOWN"},
        ],
        "builds": builds,
        "flip_or_reverse_payload_comparisons": pairs,
        "france1_italy1_cross_build": cross_build,
        "interpretation_boundary": "Payload visualization and byte comparisons only; height/surface/route semantics are UNKNOWN.",
    }

    total_sfl = sum(item["sfl_count"] for item in builds)
    valid = sum(
        1 for item in builds for field in item["sfl"]
        if field["size_bytes"] == 20 + field["width"] * field["height"]
    )
    lines = [
        "# SFL and historical FL/SF analysis (R5T-A)",
        "",
        f"Retail has **{next(item['sfl_count'] for item in builds if item['build']=='retail')}** ICont SFL files; all **{valid}/{total_sfl}** scanned SFL files across available builds satisfy the exact 20-byte header + W×H payload length.",
        "",
        "| Build | SFL files | Valid exact-size parse |",
        "|---|---:|---:|",
    ]
    for build in builds:
        good = sum(field["size_bytes"] == 20 + field["width"] * field["height"] for field in build["sfl"])
        lines.append(f"| {BUILD_NAMES[build['build']]} | {build['sfl_count']} | {good}/{build['sfl_count']} |")
    lines.extend([
        "",
        "Header word 0 is `float32 3.0` in the observed files. Width/height values and the 20-byte + W×H relation are corpus-confirmed; meanings of the other three header floats/fields and payload bytes remain UNKNOWN.",
        "",
        "## France1 / Italy1 and variant comparisons",
        "",
    ])
    for item in cross_build:
        lines.append(f"- {item['course']}: identical payload hashes across every present build = **{item['all_present_payloads_identical']}**.")
    for pair in pairs:
        lines.append(
            f"- {pair['base']} vs {pair['variant']}: dimensions equal={pair['same_dimensions']}, "
            f"header bytes equal={pair['same_header_bytes']}, payload hash equal={pair['same_payload_hash']}."
        )
    lines.extend([
        "",
        "## Demo 8.4.1 FL/SF",
        "",
        "The older FL/SF candidates use a different payload width in this corpus: their 20-byte headers store float32 version/width/height/unknown/unknown, and listed France1/Italy1 files satisfy 20 + width×height×4 bytes. This is structural evidence only; no cell meaning is assigned.",
        "",
    ])
    old = next(item for item in builds if item["build"] == "demo-8.4.1")
    for field in old["legacy_fl_sf"]:
        lines.append(
            f"- `{field['path']}`: {field['size_bytes']} B, {field.get('width_candidate')}×{field.get('height_candidate')}, "
            f"parse={field['parse_status']}, bytes/cell={field.get('bytes_per_cell_if_dimensions_hold')}.")
    lines.extend([
        "",
        "The old France1FL/France1SF TGA headers report 819×536, matching the DataScene-root FL/SF dimension candidates. The .gxi/TGA pairings are listed in JSON; spatial meaning is UNKNOWN.",
        "",
        "## Diagnostic previews",
        "",
        f"Raw byte-order grayscale previews are written under `{preview_dir.relative_to(REPO_ROOT).as_posix()}` (ignored research output). Rows are displayed in stored order and are not labeled as height or surface data.",
        "",
    ])
    return report, "\n".join(lines)


def gxm_probe(corpus_root: Path) -> tuple[dict[str, Any], str]:
    records = []
    directive_pattern = re.compile(
        r"\$(?:bsp|startline|finishline|splittime\d*|grndu?|grndv|landdb|draw|nodraw|surfacetype)(?=[:(\s\]]|$)|surface_[A-Za-z0-9_]+",
        re.I,
    )
    for build in BUILD_ORDER:
        root = data_root(corpus_root, build)
        course_root = root / "DataGx" / "Course"
        for path in sorted(course_root.glob("*/*.gxm"), key=lambda item: item.as_posix().casefold()) if course_root.is_dir() else ():
            data = path.read_bytes()
            if len(data) < 32:
                records.append({"build": build, "path": path.relative_to(root).as_posix(), "status": "short-header", "size_bytes": len(data)})
                continue
            words = struct.unpack_from("<8I", data, 0)
            printable_runs = [
                (match.start(), match.group().decode("ascii"))
                for match in re.finditer(rb"[\x20-\x7e]{4,}", data)
            ]
            directive_runs = [
                {"offset": offset, "text": value}
                for offset, value in printable_runs
                if directive_pattern.search(value)
            ]
            first_u16 = struct.unpack_from("<H", data, 32)[0] if len(data) >= 34 else None
            txt_path = path.with_suffix(".txt")
            materials_size = None
            mesh_span = None
            source_txt = None
            if txt_path.is_file():
                try:
                    txt_data = txt_path.read_text(encoding="latin-1")
                    sidecar = parse_sidecar(txt_path)
                    materials_size = sidecar.declared_material_count
                    mesh_span = sidecar.mesh_span
                    directive_lines = [
                        line for line in txt_data.splitlines()
                        if directive_pattern.search(line)
                    ]
                    family_counts = Counter(
                        match.group(0).split(":", 1)[0].casefold()
                        for line in directive_lines
                        for match in directive_pattern.finditer(line)
                    )
                    source_txt = {
                        "declared_material_count": sidecar.declared_material_count,
                        "parsed_material_count": len(sidecar.materials),
                        "mesh_count": len(sidecar.meshes),
                        "mesh_span": sidecar.mesh_span,
                        "directive_family_counts": dict(sorted(family_counts.items())),
                        "directive_source_lines_exact": directive_lines,
                        "first_directive_material_names": [
                            {"number": material.number, "raw_name": material.name}
                            for material in sidecar.materials
                            if directive_pattern.search(material.name)
                        ][:24],
                        "mesh_names": [
                            {"name": mesh.name, "index": mesh.index, "size": mesh.size}
                            for mesh in sidecar.meshes
                        ],
                    }
                except OSError:
                    pass
            records.append({
                "build": build,
                "path": path.relative_to(root).as_posix(),
                "size_bytes": len(data),
                "sha256": sha256_bytes(data),
                "header_words_u32": list(words),
                "first_32_hex": data[:32].hex(" "),
                "word_0x0c_matches_txt_material_count": materials_size == words[3] if materials_size is not None else None,
                "word_0x18_matches_txt_mesh_span": mesh_span == words[6] if mesh_span is not None else None,
                "word_0x10_equals_three_times_word_0x18": words[4] == 3 * words[6],
                "first_u16_at_0x20": first_u16,
                "u16_fits_existing_parser_length_bound": bool(first_u16 is not None and first_u16 <= 4096),
                "raw_printable_run_count": len(printable_runs),
                "raw_ascii_directive_string_runs": directive_runs[:200],
                "same_build_txt_source_oracle": source_txt,
                "gxm_geometry_hierarchy_status": "UNKNOWN; parser stops at body offset 0x20",
                "interpretation": "Raw string extraction only; post-header course grammar remains UNKNOWN.",
            })
    report = {
        "schema": "r5t-a-course-gxm-probe-v1",
        "evidence": "CONFIRMED_BY_CORPUS for header values and same-build TXT relations; raw ASCII runs are probes only; no full source GXM parse",
        "resources": records,
    }
    lines = [
        "# Course GXM probe (R5T-A)",
        "",
        "The two demo 8.4.1 France1/Italy1 sources have a 32-byte header. At body offset 0x20 the observed first uint16 values are 40159 and 49007; those values exceed the existing generic parser's 4,096-byte length bound if read using its vehicle-side string-prefix assumption. That assumption is not established for course GXM. No geometry/hierarchy parser is claimed.",
        "",
        "| Source | Bytes | Header word at 0x0C vs TXT materials | Word at 0x18 vs TXT mesh span | Word 0x10 = 3×0x18 | First u16 at 0x20 |",
        "|---|---:|---|---|---|---:|",
    ]
    for item in records:
        lines.append(
            f"| `{item['build']}/{item['path']}` | {item['size_bytes']} | "
            f"{item.get('word_0x0c_matches_txt_material_count')} | {item.get('word_0x18_matches_txt_mesh_span')} | "
            f"{item.get('word_0x10_equals_three_times_word_0x18')} | {item.get('first_u16_at_0x20')} |"
        )
    lines.extend([
        "",
        "Header relations above were checked against same-build TXT and are `CONFIRMED_BY_SOURCE_COMPILED_PAIR` only for those count relations. They do not establish the body layout or directive runtime meaning.",
        "",
        "The JSON retains same-build TXT material names, directive-bearing source lines, mesh names/counts and source spans alongside the raw GXM header probe. These TXT records are source-side oracle data, not proof of GXM body structure. The GXM reader boundary is the post-header body at 0x20; GXM hierarchy, geometry and source-to-DX mapping remain UNKNOWN.",
        "",
    ])
    return report, "\n".join(lines)


def txt_reports(course_corpus: dict[str, Any]) -> tuple[dict[str, Any], str]:
    family_re = re.compile(r"\$(?:bsp|startline|finishline|splittime\d*|grndu?|grndv|landdb|draw|nodraw|surfacetype)(?=[:(\s\]]|$)|surface_[A-Za-z0-9_]+", re.I)
    builds = []
    for build in course_corpus["builds"]:
        courses = []
        for course in build["courses"]:
            entries = course["artifacts"].get(".txt", [])
            if not entries:
                continue
            item = entries[0]
            lines = item.get("source_directive_lines", [])
            families = Counter(
                match.group(0).split(":", 1)[0].casefold()
                for line in lines for match in family_re.finditer(line)
            )
            courses.append({
                "course": course["logical_course_name"],
                "path": item["path"],
                "size_bytes": item["size_bytes"],
                "sha256": item["sha256"],
                "parse_status": item.get("parse_status"),
                "declared_material_count": item.get("declared_material_count"),
                "parsed_material_count": item.get("material_count"),
                "mesh_count": item.get("mesh_count"),
                "mesh_span": item.get("mesh_span"),
                "mesh_names": item.get("mesh_names", []),
                "directive_family_counts": dict(sorted(families.items())),
                "source_directive_lines_exact": lines,
            })
        builds.append({"build": build["name"], "courses": courses})

    report = {
        "schema": "r5t-a-course-txt-analysis-v1",
        "evidence": "CONFIRMED_BY_CORPUS for parser outcomes and preserved source strings; compiled meaning UNKNOWN",
        "builds": builds,
        "interpretation_boundary": "TXT material and mesh labels/directives are preserved source-side labels; they do not by themselves prove compiled or runtime semantics.",
    }
    lines = [
        "# Course TXT and source-label analysis (R5T-A)",
        "",
        "The existing TXT sidecar parser was run without format-specific relaxations. Source name strings and directive-bearing lines are preserved verbatim in JSON.",
        "",
        "| Build | Course | Parse | Materials declared/parsed | Mesh entries | Mesh span | Directive-bearing lines |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for build in builds:
        for course in build["courses"]:
            lines.append(
                f"| {build['build']} | {course['course']} | {course['parse_status']} | "
                f"{course['declared_material_count']}/{course['parsed_material_count']} | "
                f"{course['mesh_count']} | {course['mesh_span']} | {len(course['source_directive_lines_exact'])} |"
            )
    lines.extend(["", "## France1 and Italy1 source strings", ""])
    for build in builds:
        for course in build["courses"]:
            if course["course"].casefold() not in {"france1", "italy1"}:
                continue
            lines.append(f"### {build['build']} — {course['course']}")
            lines.append("")
            lines.append("Directive-family counts (a line may contain more than one token): " + ", ".join(
                f"`{name}` {count}" for name, count in course["directive_family_counts"].items()
            ))
            lines.append("")
            for raw in course["source_directive_lines_exact"][:12]:
                escaped = raw.replace("`", "\\`")
                lines.append("- `" + escaped + "`")
            if len(course["source_directive_lines_exact"]) > 12:
                lines.append(f"- … {len(course['source_directive_lines_exact']) - 12} additional exact lines are retained in JSON.")
            lines.append("")
    lines.extend([
        "## Parser boundary",
        "",
        "The shared sidecar parser extracts material names, texture records, declared material count, and `moMesh` spans. `moUnknown`/special directive-bearing lines remain preserved by the corpus probe but are not interpreted as scene nodes. `$bsp`, `$draw`, `$nodraw`, `$landdb`, `$grnd*`, and `$surfacetype` are string evidence only; their compiled/runtime meanings remain UNKNOWN.",
        "",
    ])
    return report, "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=REPO_ROOT.parent / "corpora")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "research" / "r5t_a")
    parser.add_argument("--preview-dir", type=Path, default=REPO_ROOT / ".research-output" / "r5t_a" / "sfl")
    args = parser.parse_args()
    corpus_root = args.corpus_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    course_corpus = json.loads((output_dir / "course-corpus.json").read_text(encoding="utf-8"))

    graph, graph_md = resource_graph(course_corpus, corpus_root)
    xml, xml_md = discover_scene_xml(corpus_root, course_corpus)
    sfl, sfl_md = sfl_reports(corpus_root, output_dir, args.preview_dir.resolve())
    gxm, gxm_md = gxm_probe(corpus_root)
    txt, txt_md = txt_reports(course_corpus)

    for name, report, markdown in (
        ("course-resource-graph", graph, graph_md),
        ("racetest-xml", xml, xml_md),
        ("sfl-analysis", sfl, sfl_md),
        ("course-gxm-probe", gxm, gxm_md),
        ("course-txt-analysis", txt, txt_md),
    ):
        (output_dir / f"{name}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        (output_dir / f"{name}.md").write_text(markdown, encoding="utf-8", newline="\n")
    print(json.dumps({
        "graph_build_summaries": {item["build"]: item["summary"] for item in graph["builds"]},
        "racetest_xml_counts": {item["build"]: item["race_test_xml_count"] for item in xml["builds"]},
        "sfl_counts": {item["build"]: item["sfl_count"] for item in sfl["builds"]},
        "legacy_fl_sf_count": len(next(item for item in sfl["builds"] if item["build"] == "demo-8.4.1")["legacy_fl_sf"]),
        "course_gxm_count": len(gxm["resources"]),
        "preview_dir": str(args.preview_dir.resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
