"""Read-only R-DEMO GXM prefix and directive corpus audit."""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from master_rallye.gxm import parse_gxm_prefix_bytes, parse_gxm_geometry_prefix_bytes, parse_gxm_triangle_prefix_bytes

DIRECTIVE = re.compile(rb"\$[A-Za-z][A-Za-z0-9_.()/-]{2,100}")


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo-8", type=Path, required=True)
    ap.add_argument("--demo-9", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    roots = {"demo-8.4.1": args.demo_8.resolve(), "demo-9.3.1": args.demo_9.resolve()}
    output = args.output.resolve()
    for root in roots.values():
        if not root.is_dir() or root == output or root in output.parents or output in root.parents:
            raise SystemExit("corpus roots must exist and may not overlap output")
    output.mkdir(parents=True, exist_ok=True)
    header_rows = []
    material_rows = []
    directives = []
    path_prefixes = collections.Counter()
    for corpus_id, root in roots.items():
        for path in sorted(root.rglob("*.gxm")):
            relative = path.relative_to(root).as_posix()
            data = path.read_bytes()
            prefix = parse_gxm_prefix_bytes(data, f"{corpus_id}:{relative}")
            row = {"corpus_id": corpus_id, "relative_path": relative,
                   "size": len(data), "header_words": list(prefix.header_words),
                   "prefix_kind": prefix.prefix_kind, "material_count_parsed": len(prefix.materials),
                   "tail_offset": prefix.tail_offset,
                   "word_0x10_equals_3x_word_0x18": prefix.header_words[4] == 3 * prefix.header_words[6]}
            if prefix.prefix_kind == "material_table":
                geo = parse_gxm_geometry_prefix_bytes(data, prefix)
                triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geo)
                row["triangle_prefix"] = {"record_offset": triangles.record_offset,
                                          "record_count": triangles.record_count,
                                          "vector_c_offset": triangles.vector_c_offset,
                                          "vector_c_count": triangles.vector_c_count,
                                          "hierarchy_offset": triangles.hierarchy_offset,
                                          "vector_c_bounds": triangles.vector_c_bounds,
                                          "no_material_record_count": triangles.no_material_record_count,
                                          "no_vector_b_record_count": triangles.no_vector_b_record_count}
                row["geometry_prefix"] = {"vector_a_offset": geo.vector_a_offset,
                                          "vector_a_count": geo.vector_a_count,
                                          "vector_b_offset": geo.vector_b_offset,
                                          "vector_b_count": geo.vector_b_count,
                                          "sentinel_offset": geo.sentinel_offset,
                                          "remainder_offset": geo.remainder_offset,
                                          "vector_b_bounds": geo.vector_b_bounds}
                for index, material in enumerate(prefix.materials):
                    material_rows.append({"corpus_id": corpus_id, "relative_path": relative,
                                          "material_index": index, "name": material.name,
                                          "slots": [{"flags3": slot.flags3.hex(), "reference": slot.reference}
                                                    for slot in material.slots]})
                    for slot in material.slots:
                        if ":/" in slot.reference:
                            path_prefixes[slot.reference.split("/DataGx/")[0]] += 1
            header_rows.append(row)
            for hit in DIRECTIVE.finditer(data):
                for offset in range(max(0, hit.start() - 256), hit.start() + 1):
                    if offset + 2 > len(data):
                        continue
                    size = int.from_bytes(data[offset:offset + 2], "little")
                    if not (4 <= size <= 256 and offset + 2 <= hit.start() and offset + 2 + size >= hit.end()):
                        continue
                    raw = data[offset + 2:offset + 2 + size]
                    if all(32 <= byte <= 126 for byte in raw):
                        directives.append({"corpus_id": corpus_id, "relative_path": relative,
                                           "offset": hit.start(), "directive": hit.group().decode("ascii"),
                                           "string_offset": offset, "source_string": raw.decode("ascii")})
                        break
    write_json(output / "gxm-header-corpus.json", {"files": header_rows})
    write_json(output / "gxm-materials.json", {"materials": material_rows})
    write_json(output / "gxm-directives.json", {"occurrences": directives})
    by_corpus = collections.defaultdict(list)
    for row in header_rows:
        by_corpus[row["corpus_id"]].append(row)
    lines = ["# GXM header and geometry prefix", "",
             "All paths below are corpus-qualified. `word_0xNN` names avoid assigning unproved roles.", "",
             "For the `material_table` variant, 32 header bytes are followed by `word_0x0c` materials (zero in one frontend file). Each material has a u16-length ASCII name, a u8 slot count, and slots of three raw control bytes plus a u16-length ASCII reference. The remainder after the third float3 array stays opaque.", ""]
    for corpus_id, rows in by_corpus.items():
        variants = collections.Counter(r["prefix_kind"] for r in rows)
        geometry = [r for r in rows if "geometry_prefix" in r]
        lines += [f"## {corpus_id}", "",
                  f"- GXM files: {len(rows)}; variants: {dict(variants)}.",
                  f"- `word_0x10 == 3 * word_0x18`: {sum(r['word_0x10_equals_3x_word_0x18'] for r in rows)}/{len(rows)}.",
                  f"- Material-table files with unit-length float3 vector A array, finite float3 vector B and C arrays (B can be empty), indexed ten-word records, and 12 `FF` separator bytes: {len(geometry)}.", ""]
    lines += ["## Header fields", "",
              "| Offset | Observed interpretation | Evidence |", "|---:|---|---|",
              "| 0x00 | Packed variant/version word; low byte `02` in scanned corpus | CONFIRMED_BY_CORPUS |",
              "| 0x04 | Zero in scanned corpus | CONFIRMED_BY_CORPUS |",
              "| 0x08 | Nonzero in some nonvehicle variants; meaning unknown | CONFIRMED_BY_CORPUS |",
              "| 0x0C | Number of material records in the recognized material-table variant | CONFIRMED_BY_CORPUS |",
              "| 0x10 | Number of unit-length float3 vectors in recognized variant; equals 3 × word_0x18 in every file | CONFIRMED_BY_CORPUS |",
              "| 0x14 | Number of finite float3 vectors in array B in recognized variant | CONFIRMED_BY_CORPUS |",
              "| 0x18 | Number of ten-word records, each with three index triples; triangle interpretation is high confidence | HIGH_CONFIDENCE_INFERENCE |",
              "| 0x1C | Number of finite float3 vectors in array C; second record index triple addresses this array | CONFIRMED_BY_CORPUS |", "",
              "The parser refuses to locate geometry in variants whose material prefix is not proven. Array offsets and numeric bounds for every recognized file are in `gxm-header-corpus.json`.", ""]
    (output / "gxm-header.md").write_text("\n".join(lines), encoding="utf-8")
    counts = collections.Counter((d["corpus_id"], d["directive"]) for d in directives)
    dlines = ["# GXM source directives", "", "Only `$` tokens inside plausible u16-length printable ASCII strings are counted. A token is SOURCE_SIDE_EVIDENCE; its runtime meaning is not inferred from its name.", "",
              "| Corpus | Token | Occurrences |", "|---|---|---:|"]
    for (corpus_id, directive), count in sorted(counts.items()):
        dlines.append(f"| {corpus_id} | `{directive}` | {count} |")
    dlines += ["", f"Total raw token occurrences: {len(directives)}. Per-file offsets are in `gxm-directives.json`.", ""]
    (output / "gxm-directives.md").write_text("\n".join(dlines), encoding="utf-8")
    plines = ["# GXM development paths", "", "Source-side absolute paths occur in parsed material references. They do not identify a local installed path or prove runtime file lookup.", "",
              "| Source prefix | References |", "|---|---:|"]
    plines += [f"| `{prefix}` | {count} |" for prefix, count in path_prefixes.most_common()]
    (output / "development-paths.md").write_text("\n".join(plines) + "\n", encoding="utf-8")
    print("GXM", len(header_rows), "materials", len(material_rows), "directives", len(directives),
          "variants", dict(collections.Counter(r["prefix_kind"] for r in header_rows)))


if __name__ == "__main__":
    main()
