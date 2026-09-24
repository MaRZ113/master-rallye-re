"""Classify evidenced Master Rallye demo Debug lines; keep raw logs ignored."""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

try:
    from .demo_debug_capture import LOG_ROOT
except ImportError:  # direct script execution
    from demo_debug_capture import LOG_ROOT

TIMESTAMP = re.compile(r"^\d\d:\d\d:\d\d\.\d{3} \| ")
PATTERNS = (
    ("cached_dxt_load", re.compile(r"^Loaded cached DX texture: \[(?P<resource>.*)\]$"),
     "Loaded cached DX texture: [%s]"),
    ("cached_dxt_save", re.compile(r"^Saved cached texture: \[(?P<resource>.*)\]$"),
     "Saved cached texture: [%s]"),
    ("gxi_read", re.compile(r"^Reading GXI: \[(?P<resource>.*)\]$"),
     "Reading GXI: [%s]"),
    ("gxi_load_failure", re.compile(r"^Can't load GXI \[(?P<resource>.*)\]$"),
     "Can't load GXI [%s]"),
    ("cached_dxt_load_failure", re.compile(r"^Cannot load cached texture: \[(?P<resource>.*)\]$"),
     "Cannot load cached texture: [%s]"),
    ("shader_selection", re.compile(r"^Shader \[(?P<shader>[^\]]+)\], entry (?P<entry>\d+) selected$"),
     "Shader [%s], entry %d selected"),
)

# Human-observed 8.4.1 compiler-stage fragments. The full line syntax is not
# available yet, so these are substring matches rather than invented templates.
STAGE_FRAGMENTS = (
    ("model_gxm_read", "Reading GXM"),
    ("model_cook_begin", "Making dx model for"),
    ("sort_plane", "mCSortPlane"),
    ("vertex_welder", "Vertex welder"),
    ("convex_hull_build", "Building convex hull"),
    ("bsp_build", "Building BSP tree"),
    ("cylinder_build", "Building cylinder"),
    ("geometry_2d_parse", "Parsing 2d geometry"),
    ("land_database_build", "Building land database"),
    ("object_node_insert", "Inserting object nodes"),
    ("model_optimise", "Optimising model"),
    ("model_cache_disabled", "Caching disabled."),
)


def classify_line(line: str) -> dict:
    text = TIMESTAMP.sub("", line.strip())
    for category, pattern, template in PATTERNS:
        match = pattern.fullmatch(text)
        if match:
            return {"category": category, "template": template,
                    "fields": match.groupdict()}
    for category, fragment in STAGE_FRAGMENTS:
        if fragment in text:
            return {"category": category, "template": None,
                    "observed_fragment": fragment, "fields": {}}
    return {"category": "unclassified", "template": None, "fields": {}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = LOG_ROOT.resolve()
    source = args.input.resolve(strict=True)
    output = args.output.resolve()
    if root not in source.parents or root not in output.parents or output.suffix.lower() != ".json":
        raise SystemExit("input log and output JSON must be under ignored runtime-logs")
    counts: collections.Counter[str] = collections.Counter()
    examples: dict[str, dict] = {}
    unclassified = 0
    for raw in source.read_text(encoding="utf-8", errors="replace").splitlines():
        item = classify_line(raw)
        key = item["category"]
        counts[key] += 1
        if key == "unclassified":
            unclassified += 1
        elif key not in examples:
            examples[key] = item
    report = {"source_log": source.relative_to(root).as_posix(),
              "counts": dict(counts), "first_classified_examples": examples,
              "unclassified_line_count": unclassified,
              "status": "raw log is ignored; review examples before deriving a public catalog"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": dict(counts), "unclassified": unclassified}))


if __name__ == "__main__":
    main()
