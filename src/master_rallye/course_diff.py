"""Read-only semantic comparison of two Master Rallye course resource trees."""
from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

from .course_gxm import parse_course_gxm_bytes, parse_course_gxm_object_table_bytes
from .course_source import parse_course_txt_bytes
from .dx_course import parse_course_dx_bytes
from .dx import parse_dx_common_prefix
from .errors import BoundsError, FormatError
from .hnt import parse_hnt_bytes
from .sfl import parse_sfl_bytes
from .sidecar import parse_sidecar


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _node_paths(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id = {node["node_id"]: node for node in nodes}
    result: dict[str, dict[str, Any]] = {}
    sibling_counts: Counter[tuple[int | None, str, str]] = Counter()
    for node in nodes:
        parent_id = node["parent_id"]
        parent_path = result.get(str(parent_id), {}).get("path", "")
        sibling_key = (parent_id, node["class_name"], node["name"])
        sibling_counts[sibling_key] += 1
        segment = f'{node["class_name"]}[{node["name"]}]#{sibling_counts[sibling_key]}'
        path = f"{parent_path}/{segment}" if parent_path else segment
        result[str(node["node_id"])] = {**node, "path": path}
    return result


def _dx_semantics(data: bytes, source: str) -> dict[str, Any]:
    try:
        model = parse_course_dx_bytes(data, source)
    except (BoundsError, FormatError) as course_error:
        prefix = parse_dx_common_prefix(data, source)
        vertex_count = len(prefix.vertices.positions)
        vertex_bytes = vertex_count * 12
        index_bytes = len(prefix.local_indices) * 2
        return {
            "status": "prefix_only",
            "kind": ".dx",
            "course_parser_boundary": f"{type(course_error).__name__}: {course_error}",
            "revision": prefix.word_0x04,
            "vertex_count": vertex_count,
            "triangle_count": len(prefix.local_indices) // 3,
            "common_prefix_offset": prefix.draw_table_offset,
            "render_validated": None,
            "render_hashes": {
                "positions": _sha(data[prefix.vertices.position_offset:prefix.vertices.position_offset + vertex_bytes]),
                "normals": _sha(data[prefix.vertices.normal_offset:prefix.vertices.normal_offset + vertex_bytes]),
                "colors": _sha(data[prefix.vertices.color_offset:prefix.vertices.color_offset + vertex_count * 4]),
                "uv_sets": [
                    _sha(data[uv.offset:uv.offset + vertex_count * 8]) for uv in prefix.uv_sets
                ],
                "local_indices": _sha(data[prefix.local_index_offset:prefix.local_index_offset + index_bytes]),
            },
            "opaque_after_common_prefix": {
                "offset": prefix.draw_table_offset,
                "byte_size": len(data) - prefix.draw_table_offset,
                "sha256": _sha(data[prefix.draw_table_offset:]),
                "tag100": None,
                "tag_semantics": "not parsed; common-prefix boundary only",
            },
        }

    vertex_count = model.vertex_count
    vertex_bytes = vertex_count * 12
    index_bytes = len(model.local_indices) * 2
    material_buckets: Counter[tuple[tuple[str, ...], str, int]] = Counter()
    record_tags: Counter[int] = Counter()
    for draw in model.physical_draws:
        record_tags[draw.tag] += 1
        if draw.index_count:
            material_buckets[(draw.texture_tuple, draw.flags_0x20.hex(), draw.unknown_0x24)] += draw.triangle_count

    root_shape = [
        {
            "tag": record.tag,
            "children": record.declared_child_count,
            "index_count": record.index_count,
        }
        for record in model.course_root_records
    ]
    bsp = model.collision.bsp
    return {
        "status": "parsed",
        "kind": ".dx",
        "course_parser_boundary": "full revision-135 course render parser",
        "revision": model.word_0x04,
        "vertex_count": vertex_count,
        "triangle_count": model.triangle_count,
        "physical_draw_count": len(model.physical_draws),
        "indexed_draw_count": sum(1 for draw in model.physical_draws if draw.index_count),
        "declared_top_level_record_count": model.declared_top_level_record_count,
        "root_record_shape": root_shape,
        "batch_count": len(model.course_batches),
        "batch_record_counts": [batch.record_count for batch in model.course_batches],
        "render_validated": model.course_render_validated,
        "common_prefix_offset": model.draw_table_offset,
        "render_hashes": {
            "positions": _sha(data[model.vertices.position_offset:model.vertices.position_offset + vertex_bytes]),
            "normals": _sha(data[model.vertices.normal_offset:model.vertices.normal_offset + vertex_bytes]),
            "colors": _sha(data[model.vertices.color_offset:model.vertices.color_offset + vertex_count * 4]),
            "uv_sets": [
                _sha(data[uv.offset:uv.offset + vertex_count * 8]) for uv in model.uv_sets
            ],
            "local_indices": _sha(data[model.local_index_offset:model.local_index_offset + index_bytes]),
        },
        "record_tag_counts": {str(key): value for key, value in sorted(record_tags.items())},
        "material_buckets": [
            {"textures": list(key[0]), "flags_0x20": key[1], "unknown_0x24": key[2], "triangles": count}
            for key, count in sorted(material_buckets.items())
        ],
        "trailing": {
            "offset": model.trailing.offset,
            "byte_size": len(model.trailing.data),
            "sha256": model.trailing.sha256,
            "collision_tags": list(model.collision.tag_ids),
            "tag100": None if bsp is None else {
                "offset": bsp.tag_offset,
                "byte_size": len(bsp.raw),
                "sha256": bsp.sha256,
                "boundary_status": bsp.status,
            },
        },
        "warnings": list(model.diagnostics.warnings),
    }


def _txt_semantics(path: Path, data: bytes) -> dict[str, Any]:
    sidecar = parse_sidecar(path)
    doc = parse_course_txt_bytes(data, path.name)
    materials = [
        {
            "number": item.number,
            "name": item.name,
            "textures": [
                {
                    "slot": texture.slot,
                    "source_tga": texture.source_tga,
                    "resource_stem": texture.resource_stem,
                    "has_alpha": texture.has_alpha,
                    "uses_alpha": texture.uses_alpha,
                    "is_noise": texture.is_noise,
                }
                for texture in item.textures
            ],
        }
        for item in sidecar.materials
    ]
    meshes = [
        {"name": item.name, "index": item.index, "size": item.size}
        for item in sidecar.meshes
    ]
    nodes = [
        {
            "node_id": item.node_id,
            "line_number": item.line_number,
            "indent": item.indent,
            "class_name": item.class_name,
            "name": item.name,
            "parent_id": item.parent_id,
            "mesh_index": item.mesh_index,
            "mesh_size": item.mesh_size,
            "literal_tokens": list(item.literal_tokens),
            "raw_line": item.raw_line,
        }
        for item in doc.nodes
    ]
    paths = _node_paths(nodes)
    stable_nodes = [
        {
            "path": item["path"],
            "class_name": item["class_name"],
            "name": item["name"],
            "mesh_index": item["mesh_index"],
            "mesh_size": item["mesh_size"],
            "literal_tokens": item["literal_tokens"],
        }
        for item in paths.values()
    ]
    helper_counts = Counter(token for node in nodes for token in node["literal_tokens"])
    semantic = {
        "status": "parsed",
        "kind": ".txt",
        "declared_material_count": sidecar.declared_material_count,
        "material_count": len(materials),
        "mesh_count": len(meshes),
        "mesh_span": sidecar.mesh_span,
        "node_count": len(nodes),
        "unparsed_node_line_count": len(doc.unparsed_node_lines),
        "literal_helper_token_counts": dict(sorted(helper_counts.items())),
        "material_names_sha256": _sha(json.dumps(materials, sort_keys=True, ensure_ascii=False).encode("utf-8")),
        "mesh_records_sha256": _sha(json.dumps(meshes, sort_keys=True, ensure_ascii=False).encode("utf-8")),
        "node_records_sha256": _sha(json.dumps(stable_nodes, sort_keys=True, ensure_ascii=False).encode("utf-8")),
        "unparsed_node_lines": list(doc.unparsed_node_lines),
    }
    return {**semantic, "_materials": materials, "_meshes": meshes, "_nodes": stable_nodes}


def _xml_semantics(data: bytes, source: str) -> dict[str, Any]:
    root = ET.fromstring(data)
    counts: Counter[str] = Counter()
    records: dict[str, dict[str, Any]] = {}

    def walk(element: ET.Element, path: str) -> None:
        tag = str(element.tag)
        counts[tag] += 1
        records[path] = {
            "tag": tag,
            "attributes": dict(sorted(element.attrib.items())),
            "text": (element.text or "").strip(),
        }
        sibling_counts: Counter[str] = Counter()
        for child in list(element):
            child_tag = str(child.tag)
            sibling_counts[child_tag] += 1
            walk(child, f"{path}/{child_tag}[{sibling_counts[child_tag]}]")

    walk(root, f"{root.tag}[1]")
    return {
        "status": "parsed",
        "kind": ".xml",
        "root_tag": str(root.tag),
        "element_count": sum(counts.values()),
        "tag_counts": dict(sorted(counts.items())),
        "_tree": records,
    }


def _semantics(path: Path, data: bytes) -> dict[str, Any]:
    suffix = path.suffix.casefold()
    if suffix == ".dx":
        return _dx_semantics(data, path.name)
    if suffix == ".txt":
        return _txt_semantics(path, data)
    if suffix == ".gxm":
        gxm = parse_course_gxm_bytes(data, path.name)
        result = {
            "status": "parsed",
            "kind": ".gxm",
            "header_words_u32": list(gxm.header_words),
            "opaque_record_count": gxm.record_count,
            "opaque_record_stride": gxm.record_stride,
            "opaque_record_bytes": len(gxm.opaque_records),
            "opaque_record_sha256": _sha(gxm.opaque_records),
            "opaque_tail_bytes": len(gxm.opaque_tail),
            "opaque_tail_sha256": _sha(gxm.opaque_tail),
        }
        txt_path = path.with_suffix(".txt")
        if txt_path.is_file():
            txt = parse_course_txt_bytes(txt_path.read_bytes(), txt_path.name)
            table = parse_course_gxm_object_table_bytes(data, txt, path.name)
            class_counts = Counter(node.class_name for node in table.nodes)
            helper_counts = Counter(
                token for node in txt.nodes for token in node.literal_tokens
            )
            stable_nodes = [
                {
                    "class_name": node.class_name,
                    "name": node.name,
                    "parent_id": node.parent_id,
                    "record_control_u16": node.record_control_u16,
                    "mesh_index": node.mesh_index,
                    "mesh_size": node.mesh_size,
                    "child_count": node.child_count,
                }
                for node in table.nodes
            ]
            result["object_table"] = {
                "status": "cross_checked_with_txt",
                "offset": table.table_offset,
                "byte_size": table.table_size,
                "sha256": _sha(data[table.table_offset:]),
                "node_count": len(table.nodes),
                "class_counts": dict(sorted(class_counts.items())),
                "helper_token_counts": dict(sorted(helper_counts.items())),
                "node_records_sha256": _sha(
                    json.dumps(stable_nodes, sort_keys=True, ensure_ascii=False).encode("utf-8")
                ),
                "crosscheck": table.txt_crosscheck,
            }
        else:
            result["object_table"] = {
                "status": "not_parsed",
                "reason": "paired same-stem TXT sidecar is unavailable",
            }
        return result
    if suffix == ".hnt":
        hnt = parse_hnt_bytes(data, path.name)
        entries = [
            {"keyword": item.keyword, "value": item.value, "raw_line": item.raw_line}
            for item in hnt.entries
        ]
        return {
            "status": "parsed",
            "kind": ".hnt",
            "entry_count": len(entries),
            "entries": entries,
            "unparsed_lines": list(hnt.unparsed_lines),
        }
    if suffix == ".sfl":
        field = parse_sfl_bytes(data, path.name)
        return {
            "status": "parsed",
            "kind": ".sfl",
            "header_raw_hex": field.header.raw.hex(),
            "first_float": field.header.first_float,
            "width": field.header.width,
            "height": field.header.height,
            "unknown_float_0x0c": field.header.unknown_float_0x0c,
            "unknown_float_0x10": field.header.unknown_float_0x10,
            "payload_sha256": _sha(field.payload),
            "value_counts": [list(pair) for pair in field.value_counts],
            "_payload": field.payload,
        }
    if suffix in {".xml", ".racetest"}:
        return _xml_semantics(data, path.name)
    return {"status": "hash_only", "kind": suffix or "<no-extension>"}


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _counter_diff(left: list[Any], right: list[Any]) -> dict[str, list[Any]]:
    a = Counter(_stable_json(value) for value in left)
    b = Counter(_stable_json(value) for value in right)
    return {
        "removed": [json.loads(key) for key in sorted(a.keys() | b.keys()) for _ in range(max(0, a[key] - b[key]))],
        "added": [json.loads(key) for key in sorted(a.keys() | b.keys()) for _ in range(max(0, b[key] - a[key]))],
    }


def _compare_semantics(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    supported = {"parsed", "prefix_only"}
    if left.get("status") not in supported or right.get("status") not in supported:
        return {"status": "not_compared", "reason": "one or both parser results are not parsed"}
    kind = left.get("kind")
    if kind != right.get("kind"):
        return {"status": "not_compared", "reason": "resource types differ"}
    if kind == ".dx":
        fields = (
            "course_parser_boundary", "revision", "vertex_count", "triangle_count", "physical_draw_count",
            "indexed_draw_count", "declared_top_level_record_count", "root_record_shape",
            "batch_count", "batch_record_counts", "render_validated", "common_prefix_offset", "render_hashes",
            "record_tag_counts", "material_buckets", "trailing",
        )
        return {
            "status": "compared",
            "comparison_scope": "full-course-render" if left["status"] == right["status"] == "parsed" else "common-prefix-only",
            "base_parse_status": left["status"],
            "modified_parse_status": right["status"],
            "changed_fields": [
                key for key in fields if key in left and key in right and left[key] != right[key]
            ],
        }
    if kind == ".txt":
        material_diff = _counter_diff(left["_materials"], right["_materials"])
        mesh_diff = _counter_diff(left["_meshes"], right["_meshes"])
        node_diff = _counter_diff(left["_nodes"], right["_nodes"])
        fields = [
            key for key in ("declared_material_count", "mesh_span", "literal_helper_token_counts")
            if left.get(key) != right.get(key)
        ]
        return {
            "status": "compared",
            "changed_fields": fields,
            "materials": material_diff,
            "meshes": mesh_diff,
            "nodes": node_diff,
        }
    if kind == ".sfl":
        result: dict[str, Any] = {
            "status": "compared",
            "header_changed": left["header_raw_hex"] != right["header_raw_hex"],
            "dimensions_changed": (left["width"], left["height"]) != (right["width"], right["height"]),
            "changed_cell_count": None,
            "changed_cell_bounds": None,
        }
        if not result["dimensions_changed"] and len(left["_payload"]) == len(right["_payload"]):
            changed = [i for i, (a, b) in enumerate(zip(left["_payload"], right["_payload"])) if a != b]
            result["changed_cell_count"] = len(changed)
            if changed:
                width = left["width"]
                xs = [i % width for i in changed]
                ys = [i // width for i in changed]
                result["changed_cell_bounds"] = [min(xs), min(ys), max(xs), max(ys)]
        return result
    if kind == ".xml":
        a, b = left["_tree"], right["_tree"]
        added_paths = sorted(b.keys() - a.keys())
        removed_paths = sorted(a.keys() - b.keys())
        changed_paths = sorted(key for key in a.keys() & b.keys() if a[key] != b[key])
        return {
            "status": "compared",
            "root_changed": left["root_tag"] != right["root_tag"],
            "added_elements": [{"path": key, "element": b[key]} for key in added_paths[:200]],
            "removed_elements": [{"path": key, "element": a[key]} for key in removed_paths[:200]],
            "changed_elements": [
                {"path": key, "base": a[key], "modified": b[key]} for key in changed_paths[:200]
            ],
            "truncated": len(added_paths) + len(removed_paths) + len(changed_paths) > 200,
        }
    if kind == ".hnt":
        diff = _counter_diff(left["entries"], right["entries"])
        return {"status": "compared", **diff, "unparsed_lines_changed": left["unparsed_lines"] != right["unparsed_lines"]}
    if kind == ".gxm":
        fields = (
            "header_words_u32", "opaque_record_count", "opaque_record_stride",
            "opaque_record_sha256", "opaque_tail_bytes", "opaque_tail_sha256",
            "object_table",
        )
        return {"status": "compared", "changed_fields": [key for key in fields if left.get(key) != right.get(key)]}
    return {"status": "hash_only"}


def _inventory(root: Path) -> dict[str, tuple[str, Path, bytes, str]]:
    if not root.is_dir():
        raise ValueError(f"course tree must be a directory: {root}")
    result: dict[str, tuple[str, Path, bytes, str]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        key = relative.casefold()
        if key in result:
            raise ValueError(f"case-insensitive path collision in {root}: {relative}")
        data = path.read_bytes()
        result[key] = (relative, path, data, _sha(data))
    return result


def diff_course_trees(base: Path, modified: Path) -> dict[str, Any]:
    """Compare resource trees without writing to either input directory."""
    base = base.resolve()
    modified = modified.resolve()
    left_index = _inventory(base)
    right_index = _inventory(modified)
    suffixes = (".dx", ".txt", ".gxm", ".hnt", ".xml", ".sfl", ".fl", ".sf", ".dxt", ".gxi")
    inventory_counts: dict[str, dict[str, int]] = {}
    for label, index in (("base", left_index), ("modified", right_index)):
        counts = Counter(Path(entry[0]).suffix.casefold() for entry in index.values())
        inventory_counts[label] = {suffix: counts.get(suffix, 0) for suffix in suffixes}

    changed_records: list[dict[str, Any]] = []
    identical = 0
    added = sorted(right_index.keys() - left_index.keys())
    removed = sorted(left_index.keys() - right_index.keys())
    for key in sorted(left_index.keys() & right_index.keys()):
        left_entry = left_index[key]
        right_entry = right_index[key]
        if left_entry[3] == right_entry[3]:
            identical += 1
            continue
        path_name = right_entry[0]
        left_semantics: dict[str, Any]
        right_semantics: dict[str, Any]
        try:
            left_semantics = _semantics(left_entry[1], left_entry[2])
        except Exception as exc:  # keep one malformed/unsupported resource from hiding other differences
            left_semantics = {"status": "parse_failed", "kind": left_entry[1].suffix.casefold(), "error": f"{type(exc).__name__}: {exc}"}
        try:
            right_semantics = _semantics(right_entry[1], right_entry[2])
        except Exception as exc:
            right_semantics = {"status": "parse_failed", "kind": right_entry[1].suffix.casefold(), "error": f"{type(exc).__name__}: {exc}"}
        comparison = _compare_semantics(left_semantics, right_semantics)
        left_public = {key: value for key, value in left_semantics.items() if not key.startswith("_")}
        right_public = {key: value for key, value in right_semantics.items() if not key.startswith("_")}
        changed_records.append({
            "path": path_name,
            "status": "changed",
            "base": {"bytes": len(left_entry[2]), "sha256": left_entry[3], "semantics": left_public},
            "modified": {"bytes": len(right_entry[2]), "sha256": right_entry[3], "semantics": right_public},
            "semantic_diff": comparison,
        })

    def raw_record(keys: list[str], index: dict[str, tuple[str, Path, bytes, str]], status: str) -> list[dict[str, Any]]:
        return [
            {"path": index[key][0], "status": status, "bytes": len(index[key][2]), "sha256": index[key][3]}
            for key in keys
        ]

    changed_records.extend(raw_record(removed, left_index, "removed"))
    changed_records.extend(raw_record(added, right_index, "added"))
    changed_records.sort(key=lambda item: item["path"].casefold())
    return {
        "schema": "mrtool-diff-course-v1",
        "base": str(base),
        "modified": str(modified),
        "inventory_counts": inventory_counts,
        "summary": {
            "base_file_count": len(left_index),
            "modified_file_count": len(right_index),
            "identical_file_count": identical,
            "changed_file_count": sum(item["status"] == "changed" for item in changed_records),
            "added_file_count": len(added),
            "removed_file_count": len(removed),
        },
        "files": changed_records,
    }


def render_course_diff_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Course resource semantic diff",
        "",
        f"- Base: `{report['base']}`",
        f"- Modified: `{report['modified']}`",
        f"- Identical files: {summary['identical_file_count']}",
        f"- Changed / added / removed: {summary['changed_file_count']} / {summary['added_file_count']} / {summary['removed_file_count']}",
        "",
        "| Path | Status | Semantic changes |",
        "|---|---|---|",
    ]
    for item in report["files"]:
        diff = item.get("semantic_diff", {})
        if "changed_fields" in diff:
            detail = ", ".join(diff["changed_fields"]) or "none"
        elif diff.get("status") == "compared":
            detail = ", ".join(key for key, value in diff.items() if key != "status" and value not in (False, None, [], {})) or "none"
        else:
            detail = diff.get("reason", diff.get("status", "hash only"))
        lines.append(f"| `{item['path']}` | {item['status']} | {detail} |")
    lines.extend([
        "",
        "SFL changed-cell coordinates are raster indices only. GXM bank/tail hashes and unknown DX sections are retained without assigning runtime semantics.",
        "",
    ])
    return "\n".join(lines)
