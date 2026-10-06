"""Derive R-GRID8 native start transforms and maintain its human audit table."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from r_ai1_mixed_class import REPOSITORY, sha256, verify_capture
from r_grid8_candidate import EXPECTED_CANDIDATE_SHA256, TRACK_IDS
import r_grid8_candidate as candidate_builder

STATUS_VALUES = (
    "PASS_CLEAR", "PASS_TIGHT", "CAR_OVERLAP", "STATIC_GEOMETRY_CONTACT",
    "TERRAIN_OR_BOUNDARY_CONTACT", "PHYSICS_UNSTABLE", "INVALID_POSITION",
    "NOT_TESTED",
)
ISSUE_TAGS = (
    "CAR_OVERLAP", "STATIC_GEOMETRY_CONTACT", "TERRAIN_OR_BOUNDARY_CONTACT",
    "PHYSICS_UNSTABLE", "INVALID_POSITION",
)
SLOTS = tuple(f"Car{i}" for i in range(8))
DEFAULT_CORPUS = REPOSITORY.parent / "corpora" / "retail" / "Data.sma_unpacked"
AUDIT_DIR = REPOSITORY / "research" / "general-re" / "grid8"
SDK_PATH = REPOSITORY / "research" / "r5t_sdk1" / "retail-corpus-validation.json"
CAPACITY_PATH = REPOSITORY / "research" / "r-ai2-1" / "course-start-capacity.json"
CAPACITY_MAP_PATH = REPOSITORY / "research" / "r-ai2-1" / "capacity-8-map.json"
AUDIT_JSON = AUDIT_DIR / "grid8-audit.json"
AUDIT_CSV = AUDIT_DIR / "grid8-audit.csv"
TRANSFORMS_JSON = AUDIT_DIR / "grid8-predicted-transforms.json"
COURSES_MD = AUDIT_DIR / "canonical-courses.md"
CHECKLIST_MD = AUDIT_DIR / "runtime-checklist.md"
GRID_LENGTH_PER_CAR = 6.0
ROW_SPACING = 8.0
GRID_LENGTH_SCALE = 0.1666666716337204  # retail float at 0x00690D4C


def _f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _vec3(raw: str) -> tuple[float, float, float]:
    values = tuple(_f32(float(part)) for part in raw.split())
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise ValueError("Invalid RaceTest Marker Pos")
    return values


def _start_area(data: bytes) -> tuple[list[str], list[tuple[float, float, float]]]:
    root = ET.fromstring(data)
    start_lists = [item for item in root.iter("List") if item.get("Name") == "StartArea"]
    if len(start_lists) != 1:
        raise ValueError("Expected exactly one StartArea list")
    raw_positions = []
    points = []
    for marker in start_lists[0].findall("Marker"):
        values = [item for item in marker.findall("Value")
                  if item.get("Name") == "Marker Pos"]
        if len(values) != 1:
            raise ValueError("Expected exactly one Marker Pos per StartArea marker")
        raw = values[0].get("Value", "")
        raw_positions.append(raw)
        points.append(_vec3(raw))
    if len(points) < 2:
        raise ValueError("Native start grid requires at least two StartArea markers")
    return raw_positions, points


def native_grid(points: list[tuple[float, float, float]], count: int = 8) -> dict:
    """Mirror the bounded normal Quick Race path in 0x0048EB40 for N=8.

    Coordinates are derived values rounded through the native float fields.
    The grid is not collision-tested; see each record's evidence caveat.
    """
    if count != 8:
        raise ValueError("R-GRID8 transform model is intentionally fixed at N=8")
    p0, p1 = points[:2]
    dx = _f32(p1[0] - p0[0])
    dz = _f32(p1[2] - p0[2])
    direction_length = math.sqrt(dx * dx + dz * dz)
    if direction_length == 0:
        raise ValueError("StartArea edge has no XZ direction")
    forward = (_f32(dx / direction_length), 0.0, _f32(dz / direction_length))
    side_length = math.sqrt(forward[2] * forward[2] + forward[0] * forward[0])
    side = (_f32(-forward[2] / side_length), 0.0,
            _f32(forward[0] / side_length))
    full_length = _f32(math.sqrt(sum((p1[i] - p0[i]) ** 2 for i in range(3))))
    cells_per_row = math.trunc(abs(full_length * GRID_LENGTH_SCALE))
    if cells_per_row == 0:
        cells_per_row = 2

    # Retail's helper at 0x005C2E5C sets x87 RC=truncate before FISTP.
    offset = tuple(_f32(full_length * component * 0.5) for component in forward)
    row_origin = list(p1)
    position = [_f32(row_origin[i] - offset[i]) for i in range(3)]
    step = tuple(_f32(component * GRID_LENGTH_PER_CAR) for component in forward)
    row_step = tuple(_f32(component * ROW_SPACING) for component in side)
    transforms = []
    position_index = 0
    for row in range(math.ceil(count / cells_per_row)):
        if row:
            row_origin = [_f32(row_origin[i] - row_step[i]) for i in range(3)]
            position = [_f32(row_origin[i] - offset[i]) for i in range(3)]
        for column in range(cells_per_row):
            if position_index >= count:
                break
            # Normal Quick Race has Ghost OFF; native slot enumeration begins
            # at NumCars-1 and decrements after every generated grid point.
            slot = count - 1 - position_index
            transforms.append({
                "slot": slot,
                "participant": f"Car{slot}",
                "position_index": position_index,
                "row": row,
                "column": column,
                "position_xyz": [round(value, 6) for value in position],
                "orientation_basis": {
                    "forward_xzy": [round(forward[0], 8), 0.0,
                                    round(forward[2], 8)],
                    "side_xzy": [round(side[0], 8), 0.0,
                                 round(side[2], 8)],
                    "up_xyz": [0.0, 1.0, 0.0],
                    "yaw_radians_if_local_forward_is_positive_z": round(
                        math.atan2(forward[0], forward[2]), 8),
                },
            })
            position = [_f32(position[i] - step[i]) for i in range(3)]
            position_index += 1
    if len(transforms) != count or sorted(row["slot"] for row in transforms) != list(range(count)):
        raise ValueError("Grid formula failed to produce each Car0..Car7 exactly once")
    return {
        "participant_count": count,
        "full_start_edge_length_float32": round(full_length, 8),
        "longitudinal_cells_per_row": cells_per_row,
        "longitudinal_step_world_units": GRID_LENGTH_PER_CAR,
        "lateral_row_step_world_units": ROW_SPACING,
        "start_edge_direction_forward_xz": [round(forward[0], 8), round(forward[2], 8)],
        "side_basis_xz": [round(side[0], 8), round(side[2], 8)],
        "position_order": "Car7, Car6, ... Car0; Ghost OFF normal Quick Race path",
        "clearance": "UNKNOWN_NOT_PHYSICALLY_TESTED",
        "transforms": transforms,
    }


def _inputs(data_root: Path) -> tuple[list[dict], dict[int, list[dict]], dict]:
    sdk = json.loads(SDK_PATH.read_text(encoding="utf-8"))
    capacity = json.loads(CAPACITY_PATH.read_text(encoding="utf-8"))
    mapping = json.loads(CAPACITY_MAP_PATH.read_text(encoding="utf-8"))
    projects = sdk["course_projects"]
    courses = capacity["courses"]
    registrations = capacity["native_scene_registration"]["registered_scene_ids"]
    if len(projects) != 36 or len(courses) != 36 or len(registrations) != 39:
        raise ValueError("Expected the reviewed 36-course / 39-registration retail map")
    if [item.get("race_scene_id") for item in registrations] != list(TRACK_IDS):
        raise ValueError("Registered scene ID set changed; candidate guard must be reviewed")
    if mapping.get("runtime_verified_total") != 8:
        raise ValueError("R-AI2.1 eight-car closure evidence missing")
    by_identity = {item["course"]: item for item in courses}
    if len(by_identity) != 36:
        raise ValueError("Duplicate canonical course identity in source map")
    aliases: dict[int, list[dict]] = {}
    for registration in registrations:
        aliases.setdefault(registration["corpus_course"], []).append(registration)
    for course_name in {item["identity"] for item in projects}:
        if course_name not in by_identity:
            raise ValueError(f"Course project {course_name} absent from R-AI2.1 corpus audit")
    return projects, aliases, {"courses": by_identity, "map": capacity, "data_root": data_root}


def derive(data_root: Path = DEFAULT_CORPUS) -> tuple[dict, dict, list[dict]]:
    projects, aliases_by_course, inputs = _inputs(data_root)
    course_map = inputs["courses"]
    transform_rows = []
    audit_rows = []
    source_rows = []
    for project in projects:
        course = project["identity"]
        course_evidence = course_map[course]
        relative = project["race_test_xml"]
        source_path = data_root / relative
        data = source_path.read_bytes()
        digest = sha256(data)
        if digest != course_evidence["sha256"]:
            raise ValueError(f"Retail RaceTest changed from reviewed hash: {relative}")
        if course_evidence["authored_actor_indices"] != list(range(8)):
            raise ValueError(f"Course template slots changed: {course}")
        raw_positions, points = _start_area(data)
        semantic_bytes = json.dumps(raw_positions, ensure_ascii=False,
                                    separators=(",", ":")).encode("utf-8")
        start_hash = hashlib.sha256(semantic_bytes).hexdigest()
        grid = native_grid(points)
        course_aliases = aliases_by_course.get(course, [])
        if not course_aliases:
            raise ValueError(f"No native scene registration maps to {course}")
        registration_ids = [item["race_scene_id"] for item in course_aliases]
        # FinishingType is a Quick Race state field, not a RaceTest course field.
        # The same normal Quick Race N=8 runtime path used value zero.
        transform_rows.append({
            "canonical_course": course,
            "frontend_scene_ids": registration_ids,
            "scene_aliases": [item["course"] for item in course_aliases],
            "race_test_resource": relative.replace("\\", "/"),
            "race_test_sha256": digest,
            "start_area": {
                "identifier": "StartArea / first two Marker Pos values",
                "semantic_sha256": start_hash,
                "all_marker_positions_source": raw_positions,
            },
            "quick_race_finishing_type": 0,
            "finishing_type_evidence": "CONFIRMED_BY_RUNTIME in normal R-AI2.1 Quick Race; not authored per course",
            "grid": grid,
            "derivation_evidence": {
                "function_va": "0x0048EB40",
                "start_area_owner": "first StartArea Marker Pos=P0; second=P1",
                "count_source": "normal Quick Race Race/NumCars=8",
                "length_conversion": "0x005C2E5C sets x87 round mode to truncate; K=trunc(abs(L/6)), zero fallback K=2",
                "ghost_policy": "Ghost OFF candidate; special ghost start-position skip is not modeled",
                "human_clearance": "NOT PROVEN BY PREDICTED TRANSFORMS",
            },
        })
        source_rows.append({
            "canonical_course": course,
            "frontend_scene_ids": registration_ids,
            "scene_aliases": [item["course"] for item in course_aliases],
            "race_test_resource": relative.replace("\\", "/"),
            "race_test_sha256": digest,
            "start_area_identifier": "StartArea / first two Marker Pos values",
            "start_area_semantic_sha256": start_hash,
            "predicted_grid_available": True,
            "runtime_status": "NOT_TESTED",
            "issue_tags": [],
            "affected_slots": [],
            "human_note": "",
            "capture_label": "",
            "screenshot_reference": "",
            "tested_candidate_sha256": "",
            "tested_at": "",
            "candidate_sha256_for_test": EXPECTED_CANDIDATE_SHA256,
            "quick_race_finishing_type": 0,
            "finishing_type_evidence": "normal Quick Race mode; not authored per course",
        })

    transforms = {
        "phase": "R-GRID8",
        "status": "STATIC_PREDICTION_ONLY",
        "source_exe_sha256": "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4",
        "candidate_sha256": EXPECTED_CANDIDATE_SHA256,
        "course_count": len(transform_rows),
        "participant_count": 8,
        "unique_registered_scene_ids": list(TRACK_IDS),
        "formula_owner": "0x0048EB40",
        "courses": transform_rows,
        "limitation": "Positions are static formula predictions in RaceTest coordinates. No terrain, collider, tree, barrier, actor-radius, or runtime-impulse clearance test is implied.",
    }
    audit = {
        "phase": "R-GRID8",
        "status": "READY_FOR_HUMAN_AUDIT",
        "candidate_sha256_for_test": EXPECTED_CANDIDATE_SHA256,
        "candidate_profile": "retail-r-grid8-audit",
        "status_values": list(STATUS_VALUES),
        "issue_tag_values": list(ISSUE_TAGS),
        "audit_unit": "canonical physical RaceTest resource; scene aliases are listed but not presumed to change geometry",
        "course_count": len(source_rows),
        "scene_registration_count": 39,
        "courses": source_rows,
    }
    return transforms, audit, source_rows


CSV_FIELDS = (
    "canonical_course", "frontend_scene_ids", "scene_aliases", "race_test_resource",
    "race_test_sha256", "start_area_identifier", "start_area_semantic_sha256",
    "predicted_grid_available", "quick_race_finishing_type", "runtime_status",
    "issue_tags", "affected_slots", "human_note", "capture_label",
    "screenshot_reference", "tested_candidate_sha256", "tested_at",
)


def _csv_value(row: dict, key: str) -> str:
    value = row.get(key, "")
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_csv(rows: list[dict]) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with AUDIT_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row, key) for key in CSV_FIELDS})


def _slug(course: str) -> str:
    return course.lower().replace("_", "-")


def _write_checklist(rows: list[dict]) -> None:
    groups = ("France", "Italy", "Spain", "Turkey")
    lines = [
        "# R-GRID8 human runtime checklist", "",
        "UI ordering is not independently mapped in this phase. The checklist follows the canonical retail RaceTest corpus grouped by country; aliases stay attached to the physical resource.", "",
        "## Prepare the isolated test copy", "",
        "1. Copy the pristine retail game folder to a disposable test directory. Do not replace the corpus EXE or use a progressed save. Put `.research-output/general-re/grid8/MRallye.exe` in that copy as `MRallye.exe`.",
        "2. Verify the staged executable is exactly `" + EXPECTED_CANDIDATE_SHA256 + "` with `Get-FileHash <staged-MRallye.exe> -Algorithm SHA256`.",
        "3. Start that staged game and use Quick Race → Race, Humans=1, visible Opponents=Three, Class=T1, player CarID0 / TOMMEK DIRTBEAST, Ghost=OFF. Keep the local/offline mode and do not load Replay.", "",
        "## Capture and classify one start", "",
        "While the race is active (after all eight cars spawn), run from the `master-rallye-re-general` root:", "",
        "```powershell",
        'python tools/r_grid8_observe.py --observatory "D:\\Game\\Master Rallye Pristine\\Observatory" --candidate "<staged-install>\\MRallye.exe" grid8-<course-slug>',
        "```", "",
        "Use the snapshot JSON path printed by the tool. Its `.dump.bin` sidecar is required. Validate it with:", "",
        "```powershell",
        'python tools/grid8_audit.py check-capture --candidate "<staged-install>\\MRallye.exe" --observatory "D:\\Game\\Master Rallye Pristine\\Observatory" --snapshot "<capture>.json" --course <CanonicalCourse>',
        "```", "",
        "Observe the countdown and first 5–15 seconds: check Car0..Car7 independently, visible spacing, static objects, boundary/terrain contact, and any immediate impulse. Then exit normally to the frontend; do not enter Results and do not run native Debug→Dump after Results. Return to Quick Race and select the next course. The false-Attract fix is present; if the menu/race lifecycle changes unexpectedly, record it and restart rather than hiding it.", "",
        "The checker can prove Broker state only, not visible actors or physical clearance. Record exactly one primary status in `grid8-audit.json`; for every non-clean result, add issue tags, affected CarN slots, a capture label, and a useful note. Keep screenshot references local and do not commit runtime captures/screenshots.", "",
    ]
    for prefix in groups:
        lines.extend((f"## {prefix}", ""))
        for row in rows:
            if not row["canonical_course"].startswith(prefix):
                continue
            ids = ",".join(str(value) for value in row["frontend_scene_ids"])
            lines.append(f"- [ ] `{row['canonical_course']}` — scene ID(s) `{ids}` — `grid8-{_slug(row['canonical_course'])}`")
        lines.append("")
    lines.extend((
        "## Three-course smoke", "",
        "1. `Italy_S4` — historical Track10 eight-car full-lifecycle reference and reported launch/geometry anomaly. Recheck the affected slot; do not presume this course is clear.",
        "2. `France1` — first non-Italy course smoke; physical clearance remains untested.",
        "3. `Spain1` — cross-country smoke; physical clearance remains untested.", "",
        "No distinct course is documented as an eight-car `PASS_CLEAR` before R-GRID8. Italy_S4 is both the historical eight-car lifecycle reference and the reported geometry concern; this checklist preserves that ambiguity instead of inventing a known-safe course. France1 and Spain1 are prospective smoke cases, not prior passes.", "",
        "After each smoke: write the result with `python tools/grid8_audit.py record --course <name> --status <STATUS> ...`; do not proceed after a severe structural/physics anomaly until reviewed.", "",
    ))
    CHECKLIST_MD.write_text("\n".join(lines), encoding="utf-8")


def _write_canonical_md(rows: list[dict]) -> None:
    lines = [
        "# R-GRID8 canonical retail course map", "",
        "The 39 native scene registrations map to 36 canonical physical RaceTest resources. The current record identifies resource aliases, not distinct geometry. The exact Quick Race selector ordering was not recovered here; this list is grouped by canonical country/resource identity.", "",
        "| Canonical course | Frontend/native scene ID(s) | Aliases | RaceTest | StartArea semantic SHA256 | Edge length | K | Quick Race FinishingType |",
        "|---|---:|---|---|---|---:|---:|---:|",
    ]
    transform_doc = json.loads(TRANSFORMS_JSON.read_text(encoding="utf-8"))
    by_name = {row["canonical_course"]: row for row in transform_doc["courses"]}
    for row in rows:
        geometry = by_name[row["canonical_course"]]
        grid = geometry["grid"]
        aliases = ", ".join(geometry["scene_aliases"])
        ids = ", ".join(str(v) for v in geometry["frontend_scene_ids"])
        lines.append(
            f"| {row['canonical_course']} | {ids} | {aliases} | `{row['race_test_resource']}` | `{row['start_area_semantic_sha256']}` | {grid['full_start_edge_length_float32']:.6f} | {grid['longitudinal_cells_per_row']} | 0* |"
        )
    lines.extend((
        "", "`*` FinishingType 0 is the normal Quick Race test mode confirmed by R-AI2.1 runtime captures; it is not an authored per-course field. The special FinishingType 1 path remains outside the eight-car full-race proof.", "",
        "All predicted transforms are derived from RaceTest StartArea markers through native `0x0048EB40`; they do not prove vehicle-radius clearance, terrain contact, tree/barrier contact, or stability.", "",
    ))
    COURSES_MD.write_text("\n".join(lines), encoding="utf-8")


def initialize(data_root: Path = DEFAULT_CORPUS) -> dict:
    transforms, fresh_audit, fresh_rows = derive(data_root)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if AUDIT_JSON.exists():
        existing = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
        existing_rows = {row["canonical_course"]: row for row in existing.get("courses", [])}
        for row in fresh_rows:
            previous = existing_rows.get(row["canonical_course"])
            if previous:
                for field in ("runtime_status", "issue_tags", "affected_slots", "human_note",
                              "capture_label", "screenshot_reference", "tested_candidate_sha256", "tested_at"):
                    row[field] = previous.get(field, row[field])
        if set(existing_rows) not in (set(), {row["canonical_course"] for row in fresh_rows}):
            raise ValueError("Existing human audit table course set differs; refusing overwrite")
    fresh_audit["courses"] = fresh_rows
    TRANSFORMS_JSON.write_text(json.dumps(transforms, indent=2) + "\n", encoding="utf-8")
    AUDIT_JSON.write_text(json.dumps(fresh_audit, indent=2) + "\n", encoding="utf-8")
    write_csv(fresh_rows)
    _write_canonical_md(fresh_rows)
    _write_checklist(fresh_rows)
    return {"course_count": len(fresh_rows), "transform_count": sum(len(c["grid"]["transforms"]) for c in transforms["courses"]),
            "scene_registration_count": 39, "runtime_status": "NOT_TESTED"}


def load_audit() -> dict:
    if not AUDIT_JSON.exists():
        raise FileNotFoundError("Run `python tools/grid8_audit.py init` first")
    return json.loads(AUDIT_JSON.read_text(encoding="utf-8"))


def summary() -> dict:
    audit = load_audit()
    counts = {status: 0 for status in STATUS_VALUES}
    for row in audit["courses"]:
        status = row["runtime_status"]
        if status not in counts:
            raise ValueError(f"Unknown R-GRID8 status: {status}")
        counts[status] += 1
    return {"phase": "R-GRID8", "status_counts": counts,
            "completed_courses": len(audit["courses"]) - counts["NOT_TESTED"],
            "total_courses": len(audit["courses"]), "runtime_proof": "HUMAN AUDIT REQUIRED"}


def record(course: str, status: str, *, slots: list[str], tags: list[str], note: str,
           capture_label: str, screenshot_reference: str, candidate_sha256: str) -> dict:
    validate_result_fields(status, slots, tags)
    if candidate_sha256.lower() != EXPECTED_CANDIDATE_SHA256:
        raise ValueError("Human result must refer to the exact R-GRID8 candidate")
    audit = load_audit()
    matching = [row for row in audit["courses"] if row["canonical_course"] == course]
    if len(matching) != 1:
        raise ValueError("Unknown or ambiguous canonical course")
    row = matching[0]
    row.update(runtime_status=status, issue_tags=list(dict.fromkeys(tags)),
               affected_slots=list(dict.fromkeys(slots)), human_note=note,
               capture_label=capture_label, screenshot_reference=screenshot_reference,
               tested_candidate_sha256=candidate_sha256.lower(),
               tested_at=datetime.now().astimezone().isoformat(timespec="seconds"))
    AUDIT_JSON.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    write_csv(audit["courses"])
    return row


def validate_result_fields(status: str, slots: list[str], tags: list[str]) -> None:
    if status not in STATUS_VALUES:
        raise ValueError("Invalid R-GRID8 status")
    if any(slot not in SLOTS for slot in slots):
        raise ValueError("Affected slots must be Car0..Car7")
    if any(tag not in ISSUE_TAGS for tag in tags):
        raise ValueError("Invalid issue tag")
    if status in ("NOT_TESTED", "PASS_CLEAR") and (slots or tags):
        raise ValueError(f"{status} cannot have affected slots or issue tags")
    if status != "NOT_TESTED" and status != "PASS_CLEAR" and not slots:
        raise ValueError("Every non-clean result must identify affected slot(s)")


def validate_snapshot_state(snapshot: dict, course_row: dict, profile: dict) -> dict:
    """Validate active-race roster/state after the caller proves JSON/raw provenance."""
    from research_build_profiles import vehicle

    source = snapshot.get("source", {})
    course = course_row["canonical_course"]
    expected_label = f"grid8-{_slug(course)}"
    if source.get("label") != expected_label:
        raise ValueError(f"Expected capture label {expected_label!r}")
    if (source.get("freshness") != "post_baseline_complete_dump_proven" or
            source.get("broker_dump_variant") != "native_stock"):
        raise ValueError("Need a fresh active-race capture using the stock native Dump")

    values = {}
    for entry in snapshot.get("entries", []):
        path = entry.get("path")
        if not isinstance(path, str) or path in values:
            raise ValueError("Invalid or duplicate Broker path")
        values[path] = entry.get("value")

    def get(path: str):
        if path not in values:
            raise ValueError("Missing Broker path: " + path)
        return values[path]

    guards = {
        "Race/NumCars": 8,
        "Race/NumPlayers": 1,
        "Race/Type": 2,
        "Race/FinishingType": 0,
        "Race/AttractMode": False,
        "Race/NumNetworkPlayers": 0,
        "Race/NetworkSyncActive": False,
        "Race/GhostPlayback": False,
        "Frontend/QuickRace/Ghost": 0,
    }
    for path, expected in guards.items():
        actual = get(path)
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f"Unexpected {path}: {actual!r}")
    if values.get("Race/Networked") is True:
        raise ValueError("Capture reports a networked race")
    scene_id = get("Frontend/QuickRace/Track")
    if type(scene_id) is not int or scene_id not in course_row["frontend_scene_ids"]:
        raise ValueError("Captured Quick Race scene ID does not match the selected course")

    participants = []
    subsystem_paths = {}
    roster = candidate_builder.capacity.ROSTER
    if len(roster) != 8 or len(set(roster)) != 8:
        raise ValueError("R-AI2.1 deterministic roster changed")
    for slot, car_id in enumerate(roster):
        prefix = f"Race/Car{slot}/"
        participant = {key: get(prefix + key) for key in
                       ("CarID", "CarClass", "PlayerType", "DriverID", "CarType", "WheelType")}
        stock = vehicle("retail-pristine", car_id)
        expected = {
            "CarID": car_id,
            "CarClass": stock["class"],
            "PlayerType": 1 if slot == 0 else 2,
            "DriverID": 30 if slot == 0 else slot - 1,
        }
        for key, wanted in expected.items():
            if type(participant[key]) is not int or participant[key] != wanted:
                raise ValueError(f"Car{slot} {key} does not match the deterministic roster")
        for key in ("CarType", "WheelType"):
            if not isinstance(participant[key], str) or participant[key].casefold() != stock[key].casefold():
                raise ValueError(f"Car{slot} {key} does not match stock Vehicle ID {car_id}")
        for namespace in ("Vehicles", "Physics", "Controller", "Network"):
            count = sum(path.startswith(f"{namespace}/Car{slot}/") for path in values)
            subsystem_paths[f"{namespace}/Car{slot}"] = count
            if namespace in ("Vehicles", "Physics", "Network") and not count:
                raise ValueError(f"Missing {namespace}/Car{slot} Broker state")
        participants.append({"slot": slot, **participant})

    return {
        "status": "GRID8_BROKER_STATE_MATCH_ONLY",
        "runtime_full_pass": False,
        "human_actor_visibility_proven": False,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA256,
        "profile_origin": profile.get("profile_origin"),
        "compatibility_family": profile.get("compatibility_family"),
        "vehicle_registry_profile": profile.get("vehicle_registry_profile", "unknown"),
        "capture_label": source["label"],
        "canonical_course": course,
        "scene_id": scene_id,
        "race_num_cars": 8,
        "race_num_players": 1,
        "finishing_type": 0,
        "participants": participants,
        "subsystem_path_counts_not_actor_proof": subsystem_paths,
    }


def check_capture(candidate: Path, snapshot_path: Path, observatory: Path,
                  course: str) -> dict:
    """Verify one active-race Broker pair without promoting it to actor proof."""
    from research_build_profiles import check_broker_capture, resolve_build
    from r_ai1_observe import load_profile

    image = candidate.read_bytes()
    manifest = candidate_builder.verify(image)
    profile = resolve_build(image)
    if (profile.get("profile_origin") != "locally_audited" or
            profile.get("compatibility_family") != "retail-broker-v1"):
        raise ValueError("R-GRID8 requires a locally audited retail-broker-v1 candidate")

    observe = load_profile(observatory, candidate)
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    raw = snapshot_path.with_suffix(".dump.bin").read_bytes()
    verify_capture(snapshot, raw, observe.core.parse_dump_bytes)
    check_broker_capture(snapshot, profile)
    audit = load_audit()
    matches = [row for row in audit["courses"] if row["canonical_course"] == course]
    if len(matches) != 1:
        raise ValueError("Unknown canonical course")
    result = validate_snapshot_state(snapshot, matches[0], profile)
    result["candidate_sha256"] = manifest["output_sha256"]
    result["profile_origin"] = profile["profile_origin"]
    result["compatibility_family"] = profile["compatibility_family"]
    result["vehicle_registry_profile"] = profile.get("vehicle_registry_profile", "unknown")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--data-root", type=Path, default=DEFAULT_CORPUS)
    sub.add_parser("status")
    sub.add_parser("summary")
    rec = sub.add_parser("record")
    rec.add_argument("--course", required=True)
    rec.add_argument("--status", choices=STATUS_VALUES, required=True)
    rec.add_argument("--slots", nargs="*", default=[])
    rec.add_argument("--tag", action="append", default=[])
    rec.add_argument("--note", default="")
    rec.add_argument("--capture-label", default="")
    rec.add_argument("--screenshot-reference", default="")
    rec.add_argument("--candidate-sha256", default=EXPECTED_CANDIDATE_SHA256)
    check = sub.add_parser("check-capture")
    check.add_argument("--candidate", type=Path, required=True)
    check.add_argument("--snapshot", type=Path, required=True)
    check.add_argument("--observatory", type=Path, required=True)
    check.add_argument("--course", required=True)
    args = parser.parse_args()
    if args.command == "init":
        result = initialize(args.data_root)
    elif args.command in ("summary", "status"):
        result = summary()
        if args.command == "status":
            audit = load_audit()
            result["courses"] = [{"course": row["canonical_course"], "status": row["runtime_status"]}
                                  for row in audit["courses"]]
    elif args.command == "record":
        result = record(args.course, args.status, slots=args.slots, tags=args.tag,
                        note=args.note, capture_label=args.capture_label,
                        screenshot_reference=args.screenshot_reference,
                        candidate_sha256=args.candidate_sha256)
    else:
        result = check_capture(args.candidate, args.snapshot, args.observatory, args.course)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
