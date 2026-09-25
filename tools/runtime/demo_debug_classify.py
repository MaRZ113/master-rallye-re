"""Parse real DebugView output and classify observed demo cooker stages."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LOG_ROOT = REPOSITORY_ROOT / ".research-output" / "r-demo2" / "debugview"
DEBUG_LINE = re.compile(r"^\s*(?P<sequence>\d+)\s+(?P<relative_time>\d+(?:\.\d+)?)\s+(?P<pid>\d+)\s+(?P<message>.*)$")
STAGES = (
    ("sort_plane", "Inserting moSortPlane nodes"),
    ("vertex_welder", "Vertex welder"),
    ("convex_hull", "Building convex hull"),
    ("bsp_tree", "Building BSP tree"),
    ("cylinder", "Building cylinder"),
    ("geometry_2d", "Parsing 2d geometry"),
    ("land_database", "Building land database"),
    ("object_nodes", "Inserting object nodes"),
    ("model_optimise", "Optimising model"),
)


def parse_debug_lines(text: str) -> dict:
    processes: dict[int, dict] = defaultdict(lambda: {"messages": [], "stages": [], "models": [], "compiled_models": []})
    ignored = 0
    for line_number, raw in enumerate(text.splitlines(), 1):
        match = DEBUG_LINE.match(raw.rstrip("\r\n"))
        if not match:
            if raw.strip():
                ignored += 1
            continue
        pid = int(match.group("pid"))
        message = match.group("message").rstrip()
        record = {"sequence": int(match.group("sequence")),
                  "relative_time": float(match.group("relative_time")),
                  "pid": pid, "message": message, "line": line_number}
        proc = processes[pid]
        proc["messages"].append(record)
        if message.startswith("Reading GXM: ["):
            proc["models"].append(message[len("Reading GXM: ["):].rstrip("]"))
        elif message.startswith("Making dx model for"):
            named = re.search(r"named\s*:\s*\[([^\]]+)\]", message)
            proc["compiled_models"].append(named.group(1) if named else message)
        stage_name = next((name for name, fragment in STAGES if fragment in message), None)
        if stage_name:
            stage = {"name": stage_name, "label": message.rstrip(" -"),
                     "status": "pending", "sequence": record["sequence"]}
            if proc["compiled_models"]:
                stage["compiled_model"] = proc["compiled_models"][-1]
            if proc["models"]:
                stage["gxm_source"] = proc["models"][-1]
            if stage_name == "land_database" and not message.rstrip().endswith("-"):
                stage["status"] = "done"  # this observed logger emits a single non-paired action line
            proc["stages"].append(stage)
        elif message.casefold() == "done" and proc["stages"] and proc["stages"][-1]["status"] == "pending":
            proc["stages"][-1]["status"] = "done"
            proc["stages"][-1]["completion_sequence"] = record["sequence"]
        elif message.casefold() == "not necessary" and proc["stages"] and proc["stages"][-1]["status"] == "pending":
            proc["stages"][-1]["status"] = "not necessary"
            proc["stages"][-1]["completion_sequence"] = record["sequence"]
    result = {}
    for pid, proc in processes.items():
        for stage in proc["stages"]:
            if stage["status"] == "pending":
                stage["status"] = "incomplete"
        last_stage = proc["stages"][-1] if proc["stages"] else None
        classification = "CRASH_DURING_CONVEX_HULL_BUILD" if last_stage and last_stage["name"] == "convex_hull" and last_stage["status"] == "incomplete" else "NORMAL_OR_UNKNOWN_TERMINATION"
        result[str(pid)] = {"pid": pid, "messages": proc["messages"], "models": proc["models"],
                            "compiled_models": proc["compiled_models"], "stages": proc["stages"], "last_started_stage": last_stage["label"] if last_stage and last_stage["status"] == "incomplete" else None,
                            "last_completed_stage": next((s["label"] for s in reversed(proc["stages"]) if s["status"] in ("done", "not necessary")), None),
                            "final_message": proc["messages"][-1]["message"] if proc["messages"] else None,
                            "classification": classification}
    return {"processes": result, "unparsed_nonempty_lines": ignored}


def classify_line(line: str) -> dict:
    """Backward-compatible one-line categorizer for older callers/tests."""
    match = DEBUG_LINE.match(line.strip())
    text = match.group("message") if match else re.sub(r"^\d\d:\d\d:\d\d\.\d{3} \| ", "", line.strip())
    legacy = (
        ("cached_dxt_load", re.compile(r"^Loaded cached DX texture: \[(?P<resource>.*)\]$")),
        ("cached_dxt_save", re.compile(r"^Saved cached texture: \[(?P<resource>.*)\]$")),
        ("gxi_read", re.compile(r"^Reading GXI: \[(?P<resource>.*)\]$")),
        ("gxi_load_failure", re.compile(r"^Can't load GXI \[(?P<resource>.*)\]$")),
        ("cached_dxt_load_failure", re.compile(r"^Cannot load cached texture: \[(?P<resource>.*)\]$")),
        ("shader_selection", re.compile(r"^Shader \[(?P<shader>[^\]]+)\], entry (?P<entry>\d+) selected$")),
    )
    for category, pattern in legacy:
        match = pattern.fullmatch(text)
        if match:
            return {"category": category, "template": pattern.pattern, "fields": match.groupdict()}
    for category, fragment in (("model_gxm_read", "Reading GXM"), ("model_cook_begin", "Making dx model for"),
                               ("sort_plane", "Inserting moSortPlane nodes"), ("vertex_welder", "Vertex welder"),
                               ("convex_hull_build", "Building convex hull"), ("bsp_build", "Building BSP tree"),
                               ("cylinder_build", "Building cylinder"), ("geometry_2d_parse", "Parsing 2d geometry"),
                               ("land_database_build", "Building land database"), ("object_node_insert", "Inserting object nodes"),
                               ("model_optimise", "Optimising model"), ("model_cache_disabled", "Caching disabled.")):
        if fragment in text:
            return {"category": category, "template": None, "observed_fragment": fragment, "fields": {}}
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
    report = parse_debug_lines(source.read_text(encoding="utf-8", errors="replace"))
    report["source_log"] = source.relative_to(root).as_posix()
    report["status"] = "raw log is ignored; report contains only parsed runtime messages"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"processes": {pid: {"classification": p["classification"], "message_count": len(p["messages"]), "stages": p["stages"]} for pid, p in report["processes"].items()}, "output": str(output)}))


if __name__ == "__main__":
    main()
