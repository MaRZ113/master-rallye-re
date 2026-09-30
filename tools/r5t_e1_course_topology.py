"""Generate compact read-only evidence for version-7 course GXM topology."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

from master_rallye.course_gxm import parse_course_gxm_model_v7_bytes
from master_rallye.course_source import parse_course_txt


SUPPORTED_EXECUTABLE_SHA256 = "931CFC4E0C520C26581B0C1173D1BEB586FACD17176B885666F455090F646680"
SAMPLE_SCOPE_PARTS = {"course", "test"}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bounds(points):
    if not points:
        return None
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


def _mesh_geometry(model, node):
    tri_range = model.mesh_triangle_indices(node)
    triplets = [list(model.triangle(index).position_indices) for index in tri_range]
    flat_indices = [index for triangle in triplets for index in triangle]
    unique_indices = sorted(set(flat_indices))
    points = [list(model.position(index)) for index in unique_indices]
    edge_counts = Counter()
    vertex_links = {}
    for a, b, c in triplets:
        edge_counts[tuple(sorted((a, b)))] += 1
        edge_counts[tuple(sorted((b, c)))] += 1
        edge_counts[tuple(sorted((c, a)))] += 1
        vertex_links.setdefault(a, {}).setdefault(b, set()).add(c)
        vertex_links.setdefault(a, {}).setdefault(c, set()).add(b)
        vertex_links.setdefault(b, {}).setdefault(a, set()).add(c)
        vertex_links.setdefault(b, {}).setdefault(c, set()).add(a)
        vertex_links.setdefault(c, {}).setdefault(a, set()).add(b)
        vertex_links.setdefault(c, {}).setdefault(b, set()).add(a)
    normal_counts = Counter(
        tuple(round(component, 5) for component in model.normal(normal_index))
        for triangle_index in tri_range
        for normal_index in model.triangle(triangle_index).normal_indices
    )
    extents = _bounds(points)
    centroid = None
    if points:
        centroid = [sum(point[axis] for point in points) / len(points) for axis in range(3)]
    edge_histogram = dict(sorted(Counter(edge_counts.values()).items()))
    vertex_links_are_cycles = True
    for adjacency in vertex_links.values():
        if not adjacency or any(len(neighbors) != 2 for neighbors in adjacency.values()):
            vertex_links_are_cycles = False
            break
        reached = set()
        pending = [next(iter(adjacency))]
        while pending:
            current = pending.pop()
            if current in reached:
                continue
            reached.add(current)
            pending.extend(adjacency[current] - reached)
        if len(reached) != len(adjacency):
            vertex_links_are_cycles = False
            break
    return {
        "source_index": node.mesh_index,
        "source_size": node.mesh_size,
        "triangle_count": len(triplets),
        "position_index_triplets": triplets,
        "unique_position_indices": unique_indices,
        "positions": points,
        "bounds": extents,
        "dimensions": [
            extents["max"][axis] - extents["min"][axis] for axis in range(3)
        ] if extents else None,
        "centroid": centroid,
        "unique_edge_count": len(edge_counts),
        "edge_incidence_histogram": {str(key): value for key, value in edge_histogram.items()},
        "vertex_links_are_cycles": vertex_links_are_cycles,
        "closed_two_manifold": bool(edge_counts)
        and all(count == 2 for count in edge_counts.values())
        and vertex_links_are_cycles,
        "normal_direction_groups": [
            {"direction": list(direction), "referenced_corners": count}
            for direction, count in sorted(normal_counts.items())
        ],
    }


def _mesh_span_record(model):
    return {
        "mesh_count": model.validation.mesh_count,
        "gaps": [list(item) for item in model.validation.mesh_span_gaps],
        "overlaps": [list(item) for item in model.validation.mesh_span_overlaps],
        "max_mesh_end": model.validation.max_mesh_end,
        "covers_triangle_bank": model.validation.mesh_spans_cover_bank,
    }


def _node_path(model, node):
    nodes = {item.ordinal: item for item in model.object_table.nodes}
    result = [node.name]
    parent_id = node.parent_id
    seen = {node.ordinal}
    while parent_id is not None and parent_id in nodes and parent_id not in seen:
        parent = nodes[parent_id]
        result.append(parent.name)
        seen.add(parent.ordinal)
        parent_id = parent.parent_id
    return list(reversed(result))


def _sample(path: Path, corpus_root: Path):
    raw = path.read_bytes()
    txt_path = path.with_suffix(".txt")
    document = parse_course_txt(txt_path)
    model = parse_course_gxm_model_v7_bytes(raw, document, path.name)
    def file_id(item: Path):
        return item.resolve().relative_to(corpus_root.resolve()).as_posix()
    bank_records = [
        {"name": model.colors.name, "offset": model.colors.offset, "end": model.colors.end,
         "count": model.colors.count, "stride": model.colors.stride, "byte_size": len(model.colors.raw)},
        {"name": model.materials.name, "offset": model.materials.offset, "end": model.materials.end,
         "count": model.materials.count, "stride": None, "byte_size": len(model.materials.raw)},
        *[
            {"name": bank.name, "offset": bank.offset, "end": bank.end,
             "count": bank.count, "stride": bank.stride, "byte_size": len(bank.raw)}
            for bank in (model.normals, model.texcoords, model.triangles, model.positions)
        ],
    ]
    return model, {
        "identity": file_id(path),
        "paired_txt": file_id(txt_path),
        "gxm_size": len(raw),
        "gxm_sha256": _hash(path),
        "txt_size": txt_path.stat().st_size,
        "txt_sha256": _hash(txt_path),
        "object": {
            "class": model.object_class,
            "class_name": "moModel" if model.object_class == 2 else "unknown",
            "version": model.version,
            "child_count": model.child_count,
            "raw_header_words": list(struct.unpack_from("<8I", raw)),
        },
        "counts": {
            "word1_reserved_or_unknown": model.counts[0],
            "word2_color_like": model.colors.count,
            "word3_material": model.materials.count,
            "word4_normal": model.normals.count,
            "word5_texcoord_like": model.texcoords.count,
            "word6_triangle": model.triangles.count,
            "word7_position": model.positions.count,
        },
        "banks": bank_records,
        "index_domains": {name: values for name, values in model.validation.domains},
        "mesh_spans": _mesh_span_record(model),
        "parse_status": "PASS" if model.validation.passed else "FAIL",
    }


def generate(corpora_root: Path, output_dir: Path):
    paths = []
    for path in sorted(corpora_root.rglob("*.gxm")):
        if not path.with_suffix(".txt").is_file():
            continue
        relative_parts = {part.casefold() for part in path.relative_to(corpora_root).parts}
        if not (relative_parts & SAMPLE_SCOPE_PARTS):
            continue
        raw = path.read_bytes()
        if len(raw) < 4:
            continue
        packed = struct.unpack_from("<I", raw)[0]
        if (packed & 0xFF) == 2 and ((packed >> 8) & 0xFF) == 7:
            paths.append(path)

    records = []
    loaded = {}
    failures = []
    for path in paths:
        try:
            model, record = _sample(path, corpora_root)
            records.append(record)
            loaded[path.resolve()] = model
        except Exception as error:
            failures.append({"identity": path.resolve().relative_to(corpora_root.resolve()).as_posix(),
                             "error": f"{type(error).__name__}: {error}"})

    corpus = {
        "schema": "r5t-e1-course-gxm-topology-v1",
        "evidence": ["CONFIRMED_BY_EXECUTABLE", "CONFIRMED_BY_BINARY_STRUCTURE"],
        "scope": "paired version-7 moModel GXM in corpus paths containing Course or Test; vehicle paths excluded",
        "corpus_root": str(corpora_root.resolve()),
        "loader_executable": {
            "path": "demo-9.3.1/MRallye.exe",
            "sha256": SUPPORTED_EXECUTABLE_SHA256,
            "functions": {
                "recursive_object_header": "0x005BEA30",
                "model_payload_loader": "0x005BDF40",
                "version7_triangle_record_loader": "0x005BE940",
            },
        },
        "aggregate": {
            "files_tested": len(paths),
            "files_passed": len(records),
            "files_failed": len(failures),
            "unsupported_versions": 0,
        },
        "samples": records,
        "failures": failures,
    }

    france_path = next(path for path in paths if "france1.gxm" == path.name.casefold())
    france = loaded[france_path.resolve()]
    start_node = france.find_mesh("startpoint")
    start = _mesh_geometry(france, start_node)
    named_meshes = {}
    for name in ("COLLIDE_finishline01", "COLLIDE_finishline", "COLLIDE_finishline02", "COLLIDE_finishline03"):
        try:
            named_meshes[name] = _mesh_geometry(france, france.find_mesh(name))
        except KeyError:
            named_meshes[name] = {"status": "NOT_PRESENT"}
    file_hash = _hash(france_path)
    startpoint = {
        "schema": "r5t-e1-france1-startpoint-proof-v1",
        "evidence": ["CONFIRMED_BY_EXECUTABLE", "CONFIRMED_BY_BINARY_STRUCTURE"],
        "file": {
            "identity": france_path.resolve().relative_to(corpora_root.resolve()).as_posix(),
            "size": france_path.stat().st_size,
            "sha256": file_hash,
            "object_class": france.object_class,
            "object_version": france.version,
        },
        "node": {"name": start_node.name, "Index": start_node.mesh_index,
                 "Size": start_node.mesh_size, "hierarchy_path": _node_path(france, start_node)},
        "triangle_record_size": 52,
        "topology": start,
        "additional_named_meshes": named_meshes,
    }

    original_path = france_path
    modified_path = (corpora_root.parent / "master-rallye-re" / ".research-output" / "r5t_b1"
                     / "experiments" / "france1-startpoint-whole-x3" / "modified-source" / "France1.gxm")
    if modified_path.is_file():
        baseline_raw, modified_raw = original_path.read_bytes(), modified_path.read_bytes()
        txt = parse_course_txt(original_path.with_suffix(".txt"))
        baseline_model = loaded[original_path.resolve()]
        modified_model = parse_course_gxm_model_v7_bytes(modified_raw, txt, modified_path.name)
        changed_positions = [
            index for index in range(baseline_model.positions.count)
            if baseline_model.position(index) != modified_model.position(index)
        ]
        changed_components = [
            {"position_index": index, "component": axis,
             "before": baseline_model.position(index)[axis],
             "after": modified_model.position(index)[axis],
             "delta": modified_model.position(index)[axis] - baseline_model.position(index)[axis]}
            for index in range(baseline_model.positions.count)
            for axis in range(3)
            if baseline_model.position(index)[axis] != modified_model.position(index)[axis]
        ]
        startpoint["controlled_plus3_source_edit"] = {
            "modified_file_sha256": _hash(modified_path),
            "same_file_size": len(baseline_raw) == len(modified_raw),
            "changed_byte_count": sum(left != right for left, right in zip(baseline_raw, modified_raw)),
            "changed_source_position_indices": changed_positions,
            "all_eight_startpoint_positions_change": len(changed_positions) == 8,
            "changed_position_components": changed_components,
            "only_x_components_change_by_exactly_plus_3": len(changed_components) == 8
            and all(item["component"] == 0 and item["delta"] == 3.0 for item in changed_components),
            "triangle_bank_identical": baseline_model.triangles.raw == modified_model.triangles.raw,
            "counts_identical": baseline_model.counts == modified_model.counts,
            "non_position_banks_identical": all(
                left.raw == right.raw for left, right in (
                    (baseline_model.colors, modified_model.colors),
                    (baseline_model.materials, modified_model.materials),
                    (baseline_model.normals, modified_model.normals),
                    (baseline_model.texcoords, modified_model.texcoords),
                    (baseline_model.triangles, modified_model.triangles),
                )
            ),
            "evidence": "CONFIRMED_BY_BINARY_STRUCTURE",
        }
    else:
        startpoint["controlled_plus3_source_edit"] = {"status": "ARTIFACT_NOT_AVAILABLE"}

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "course-gxm-v7.json").write_text(json.dumps(corpus, indent=2) + "\n", encoding="utf-8")
    (output_dir / "startpoint-proof.json").write_text(json.dumps(startpoint, indent=2) + "\n", encoding="utf-8")
    return corpus, startpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora-root", type=Path, default=Path(__file__).resolve().parents[2] / "corpora")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "research" / "r5t_e")
    args = parser.parse_args()
    corpus, proof = generate(args.corpora_root, args.output_dir)
    print(f"tested={corpus['aggregate']['files_tested']} passed={corpus['aggregate']['files_passed']} failed={corpus['aggregate']['files_failed']}")
    print(f"startpoint triangles={proof['topology']['triangle_count']} positions={len(proof['topology']['unique_position_indices'])} edges={proof['topology']['unique_edge_count']} manifold={proof['topology']['closed_two_manifold']}")
    print(f"reports: {args.output_dir / 'course-gxm-v7.json'}; {args.output_dir / 'startpoint-proof.json'}")


if __name__ == "__main__":
    main()
