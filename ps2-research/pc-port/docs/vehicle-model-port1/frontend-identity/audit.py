"""Read-only PC COMPLETE source identity and bounded live-menu layout join.

Writes compact hashes, material references, ranges and matrices; no mesh arrays,
memory reads, resource mutation, renderer edits or original asset writes.
The live F10 layout join is not substituted for an upload-mirror geometry hash.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT / "ps2-research/pc-port/tools"),
               r"D:/Game/Master Rallye/master-rallye-re-course/src"]

PC = Path(r"D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles")
LOGS = Path(r"D:/Game/Master Rallye Pristine/MRRRenderer/logs")
OUT = Path(__file__).parent
EXE_SHA = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
FRONTEND_SCENE = "FrontendScreens/VehicleSelect"
EMITTER_RVA = 0x17707e
FRONTEND_FILES = ["frame-23804-d1-00001235.jsonl", "frame-23804-d1-00002726.jsonl"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def faces(model, draw):
    ids = model.draw_global_indices(draw)
    return [tuple(model.vertices.positions[i] for i in ids[n:n+3])
            for n in range(0, len(ids), 3)]


def source_record(model, draw, logical_path):
    from prepare_reflection_pilot import geometry_signature
    fs = faces(model, draw)
    digest = geometry_signature(fs)
    return {"source_id": logical_path + ":record:" + draw.record_path,
            "draw_index": draw.draw_index, "record_path": draw.record_path,
            "record_offset": draw.offset, "vertex_base": draw.vertex_base,
            "vertices": draw.local_vertex_max + 1,
            "index_start": draw.index_start, "index_count": draw.index_count,
            "triangles": len(fs), "flags_hex": draw.flags_0x20.hex(),
            "texture_slots": [s.value for s in draw.texture_slots],
            "geometry_sha256": digest,
            "runtime_identity_status": "CURRENT_UPLOAD_MIRROR_DIGEST_REQUIRED"}


def source_inventory(pc_root):
    from master_rallye.dx import parse_dx
    complete = []
    hits = collections.defaultdict(list)
    unsupported = []
    scanned = []
    for path in sorted(pc_root.glob("*/*.dx")):
        logical_path = path.relative_to(pc_root).as_posix()
        try:
            model = parse_dx(path)
        except Exception as error:
            unsupported.append({"path": logical_path, "error": str(error)})
            continue
        source = {"path": logical_path, "sha256": sha(path.read_bytes()),
                  "size": path.stat().st_size, "vertices": model.vertex_count,
                  "triangles": model.triangle_count,
                  "draws": [source_record(model, d, logical_path)
                            for d in model.physical_draws]}
        scanned.append(source)
        for d in source["draws"]:
            hits[d["geometry_sha256"]].append({"path": logical_path,
                "source_id": d["source_id"], "draw_index": d["draw_index"]})
        if path.name.lower() == "complete.dx":
            complete.append(source)
    for source in complete:
        for d in source["draws"]:
            owners = sorted(hits[d["geometry_sha256"]], key=lambda h: h["source_id"])
            d["identical_source_owners"] = owners
            d["unique_to_complete_resource"] = {h["path"] for h in owners} == {source["path"]}
            d["unique_to_vehicle_family"] = {h["path"].split("/")[0] for h in owners} == {source["path"].split("/")[0]}
    return {"complete_resources": complete, "dx_resources_scanned": len(scanned),
            "unsupported_sources": unsupported,
            "limitations": ["Vehicle corpus only; all game/UI/scene resources not exhaustively decoded.",
                "Float32 unsigned position digest retains repeated triangles; UV/color/normal identity is a separate contract."]}


def frontend_context(begin, epoch):
    """Fail-closed recorded context. This is not a live runtime permission API."""
    scene = epoch.get("scene", {})
    return (begin.get("exe_sha256") == EXE_SHA and begin.get("build") == "PRISTINE_RETAIL"
            and scene.get("read_complete") is True and scene.get("countdown") == 0
            and scene.get("requested_name") == FRONTEND_SCENE
            and scene.get("committed_name") == FRONTEND_SCENE
            and scene.get("job_source") == "DataScene/FrontendScreens/VehicleSelect.xml"
            and epoch.get("live_certificate_valid") is False
            and epoch.get("frame") == begin.get("frame"))


def draw_observation(draw):
    state = draw["state"]
    matrices = state["matrices"]
    return {"frame": draw["frame"], "draw_sequence": draw["draw_index"],
            "args": draw["arguments"][:5], "hr": draw.get("result"),
            "emitter_rva": draw.get("semantic_owner_return_rva"),
            "fvf": state["vertex_shader"], "vb": state["streams"][0],
            "ib": state["indices"], "textures": state["textures"][:2],
            "world": matrices.get("256"), "view": matrices.get("2"),
            "projection": matrices.get("3"),
            "render_states": {k: state["render_states"].get(k)
                for k in ["7", "14", "15", "19", "20", "22", "23", "27"]},
            "stage0": {k: state["texture_stage_states"][0].get(k)
                for k in ["1", "2", "3", "4", "5", "6", "11", "24"]},
            "stage1": {k: state["texture_stage_states"][1].get(k)
                for k in ["1", "2", "3", "4", "5", "6", "11", "24"]}}


def layout_join(source_draws, live_draws):
    """Join complete source layout under a single relative IB relocation.

    Never promotes draw counts/ranges to a persistent geometry identity.
    Requires one-to-one whole set, no duplicated ambiguous source records.
    """
    if len(source_draws) != len(live_draws):
        return {"status": "INCOMPLETE_DRAW_SET", "matches": []}
    offsets = sorted({live["args"][3] - src["index_start"]
        for src in source_draws for live in live_draws
        if src["vertices"] == live["args"][2] and src["triangles"] == live["args"][4]})
    solutions = []
    for offset in offsets:
        pairs = []
        used = set()
        for src in source_draws:
            found = [n for n, live in enumerate(live_draws)
                if live["args"][0] == 4 and live["args"][2] == src["vertices"]
                and live["args"][3] == src["index_start"] + offset
                and live["args"][4] == src["triangles"]]
            if len(found) != 1 or found[0] in used:
                break
            n = found[0]
            used.add(n)
            pairs.append({"source_id": src["source_id"], "source_draw": src["draw_index"],
                          "geometry_sha256": src["geometry_sha256"],
                          "observation": live_draws[n]})
        if len(pairs) == len(source_draws):
            solutions.append({"index_start_offset": offset, "matches": pairs})
    if len(solutions) != 1:
        return {"status": "AMBIGUOUS_LAYOUT" if solutions else "LAYOUT_NOT_FOUND", "matches": []}
    return {"status": "COMPLETE_SET_LAYOUT_CORRELATION", **solutions[0],
            "evidence_grade": "STATIC_INFERENCE_FROM_CONFIRMED_RUNTIME_ARGUMENTS",
            "suppression_authorized": False,
            "missing_link": "Runtime position digest computed from current full-coverage CPU upload mirrors"}


def analyze_frame(path, source_draws):
    begin = epoch = None
    indexed = []
    bad = 0
    for line in path.open(encoding="utf8"):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if record.get("type") == "frame_begin":
            begin = record
        elif record.get("type") == "race_epoch_snapshot":
            epoch = record
        elif record.get("type") == "draw" and record.get("slot") == 71:
            indexed.append(record)
    if not begin or not epoch:
        raise ValueError("Missing frame or scene context")
    eligible = [draw_observation(d) for d in indexed
                if d.get("semantic_owner_return_rva") == EMITTER_RVA]
    return {"file": path.name, "sha256": sha(path.read_bytes()), "frame": begin["frame"],
            "exe_sha256": begin["exe_sha256"], "proxy_sha256": begin["proxy_sha256"],
            "scene": epoch["scene"], "current_frontend_context": frontend_context(begin, epoch),
            "successful_reset_epoch": begin.get("quality", {}).get("successful_reset_epoch"),
            "unparsed_lines": bad, "indexed_draws": len(indexed),
            "shared_emitter_draws": len(eligible),
            "layout_join": layout_join(source_draws, eligible)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pc-root", type=Path, default=PC)
    parser.add_argument("--logs-dir", type=Path, default=LOGS)
    parser.add_argument("--out", type=Path, default=OUT / "source-and-live-evidence.json")
    args = parser.parse_args()
    inventory = source_inventory(args.pc_root)
    source = next(s for s in inventory["complete_resources"] if s["path"] == "Forester/complete.dx")
    frames = [analyze_frame(args.logs_dir / name, source["draws"]) for name in FRONTEND_FILES]
    observations = [f["layout_join"]["matches"] for f in frames]
    same_resource_generations = all(
        [m["observation"]["vb"] for m in observations[0]] == [m["observation"]["vb"] for m in other]
        and [m["observation"]["ib"] for m in observations[0]] == [m["observation"]["ib"] for m in other]
        for other in observations[1:])
    report = {"schema_version": 1, "phase": "PS2-VEHICLE-MODEL-PORT1_FRONTEND_IDENTITY",
              "source_evidence": "CONFIRMED_BY_BYTES", "runtime_evidence": "RECORDED_RUNTIME_ARGUMENTS_AND_MATRICES",
              "source_inventory": inventory, "primary_candidate": "WOOLDAND_COMPLETE_TO_PC_FORESTER_COMPLETE",
              "frames": frames, "same_resource_generations": same_resource_generations,
              "pose_changes": {"world_changes": observations[0][0]["observation"]["world"]["bits"] != observations[1][0]["observation"]["world"]["bits"],
                "view_unchanged": observations[0][0]["observation"]["view"]["bits"] == observations[1][0]["observation"]["view"]["bits"],
                "projection_unchanged": observations[0][0]["observation"]["projection"]["bits"] == observations[1][0]["observation"]["projection"]["bits"]},
              "runtime_suppression_authority": "NOT_YET_PROVEN_CURRENT_UPLOAD_MIRROR_JOIN_REQUIRED",
              "visibility": "COMPLETE_AUTHORED_SOURCE_NOT_RACE_CAR_WHEEL_INSTANCE",
              "limitations": ["No ReadProcessMemory, native hooks or full GPU buffer readback performed.",
                "Numerical pointers, creation serials and draw ordinals are historical observations, never persistent identity.",
                "One session, two rotated frontend frames; model switching/recreation/reset not independently captured here."]}
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"complete_resources": len(inventory["complete_resources"]),
                      "dx_resources_scanned": inventory["dx_resources_scanned"],
                      "primary_records": len(source["draws"]),
                      "primary_unique_complete_records": sum(d["unique_to_complete_resource"] for d in source["draws"]),
                      "frames": [{"frame": f["frame"], "context": f["current_frontend_context"], "status": f["layout_join"]["status"]} for f in frames],
                      "output": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
