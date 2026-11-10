"""RaceTest scene, markers and HNT for a Studio course.

The environment template (a Retail scene, default France1) contributes the
components that are not tied to a place: Network, Physics, Cars (the grid is
computed at runtime from StartArea/RaceLine by 0x48EB40), Sky, CameraManagers,
RaceLogic (starter, finish area, finish, timer), HUD, IContManager and
AttractMode. Everything placed on the course is generated from the project:

* ``landscape`` model ``course\\<key>\\<key>``;
* StartArea/FinishArea: four native ``Marker Pos`` corners;
* checkpoints = the native Master Rallye checkpoint, which *is* a
  ``gaRaceSplitTimeAI`` Egg (Split Time ID, trigger Radius, ExtraTime seconds
  added to the countdown, see ``gaHudAiCheckPoint``) plus four visual boards
  ``<name>-0..3`` (model ``misc\\checkpoints\\checkpoint``), and the
  ``gaRacePostFirstSplitTimeAI`` count/time of the first gate;
* RaceLine, the four gaLimitsAI lists, pace-note arrows, replay cameras and
  environment sound sources.
"""
from __future__ import annotations

import copy
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from .ai import LIMIT_NAMES, auto_pacenotes, limit_lists, raceline
from .model import CourseProject

CHECKPOINT_MODEL = "misc\\checkpoints\\checkpoint"


class SceneError(ValueError):
    pass


def _f(v: float) -> str:
    return f"{v:.2f}"


def matrix_rows(position, heading_deg: float = 0.0):
    h = math.radians(heading_deg)
    fx, fz = math.sin(h), math.cos(h)
    return {"Row0": f"{_f(fz)} 0.00 {_f(-fx)} 0.00", "Row1": "0.00 1.00 0.00 0.00",
            "Row2": f"{_f(fx)} 0.00 {_f(fz)} 0.00",
            "Row3": f"{_f(position[0])} {_f(position[1])} {_f(position[2])} 1.00"}


def _list(root, name):
    for lst in root.iter("List"):
        if lst.get("Name") == name:
            return lst
    return None


def _value(element, name):
    return element.find(f".//Value[@Name='{name}']")


def _set(element, name, value):
    node = _value(element, name)
    if node is None:
        raise SceneError(f"template lacks value {name!r}")
    node.set("Value", value)


def _set_matrix(egg, position, heading):
    node = egg.find("Value[@Name='en3d Matrix']")
    if node is None:
        raise SceneError(f"egg {egg.get('Name')} has no en3d Matrix")
    for k, v in matrix_rows(position, heading).items():
        node.set(k, v)


def _ai_names(egg):
    return [v.get("Value") for v in egg.iter("Value") if v.get("Name") == "AI Name"]


def _replace_markers(lst, points, *, marker_type=None, first_type=None):
    template = lst.find("Marker")
    if template is None:
        raise SceneError(f"marker list {lst.get('Name')} has no template marker")
    template = copy.deepcopy(template)
    for m in lst.findall("Marker"):
        lst.remove(m)
    for i, p in enumerate(points):
        m = copy.deepcopy(template)
        m.set("No", str(i))
        _set(m, "Marker Pos", f"{_f(p[0])} {_f(p[1])} {_f(p[2])}")
        if first_type and i == 0:
            _set(m, "Marker Type", first_type)
        elif marker_type:
            _set(m, "Marker Type", marker_type)
        lst.append(m)


def _ensure_marker_list(root, name, template_name="RaceLine"):
    lst = _list(root, name)
    if lst is None:
        markers = root.find("MarkerLists")
        source = _list(root, template_name)
        lst = copy.deepcopy(source)
        lst.set("Name", name)
        markers.append(lst)
    return lst


def build_racetest(project: CourseProject, template_xml: Path, *, sound_templates: dict | None = None) -> tuple[bytes, dict]:
    tree = ET.parse(template_xml)
    root = tree.getroot()
    key = project.course_key()
    report = {"template": Path(template_xml).name, "course": key}
    line = raceline(project)
    if len(line) < 2:
        raise SceneError("the course needs an AI route (RaceLine) with at least two points")

    # landscape: exactly one model egg -> the Studio DX
    land = _list(root, "landscape")
    eggs = land.findall("Egg")
    if not eggs:
        raise SceneError("template has no landscape egg")
    for extra in eggs[1:]:
        land.remove(extra)
    _set(eggs[0], "en3d Model Name", f"course\\{key.lower()}\\{key.lower()}")
    _set_matrix(eggs[0], (0.0, 0.0, 0.0), 0.0)

    # AI dataset
    for v in root.iter("Value"):
        if v.get("Name") == "AI DataSet Name":
            v.set("Value", f"ICont/{key.lower()}")

    # sounds: keep managers, drop place-bound sources, add the project's anchors
    sound = _list(root, "Sound")
    library = dict(sound_templates or {})
    if sound is not None:
        for egg in list(sound.findall("Egg")):
            names = _ai_names(egg)
            if any(n in ("enAiSoundSource", "gaAiWaterfallSound") for n in names):
                library.setdefault(egg.get("Name"), copy.deepcopy(egg))
                if not project.environment.keep_template_sounds:
                    sound.remove(egg)
        placed = 0
        for anchor in project.sounds:
            tmpl = library.get(anchor.template)
            if tmpl is None:
                report.setdefault("missing_sound_templates", []).append(anchor.template)
                continue
            egg = copy.deepcopy(tmpl)
            egg.set("Name", anchor.name or f"{anchor.template}_{placed}")
            _set_matrix(egg, anchor.position, 0.0)
            sound.append(egg)
            placed += 1
        report["sound_sources"] = placed

    # checkpoints
    splits = _list(root, "SplitTimes")
    start_split = next((e for e in splits.findall("Egg") if "gaRacePostFirstSplitTimeAI" in _ai_names(e)), None)
    gate = next((e for e in splits.findall("Egg") if "gaRaceSplitTimeAI" in _ai_names(e)), None)
    if start_split is None or gate is None:
        raise SceneError("template has no native StartSplitTime/SplitTime eggs")
    board = next((e for e in splits.findall("Egg") if e.get("Name") == f"{gate.get('Name')}-0"), None)
    gate, board = copy.deepcopy(gate), copy.deepcopy(board) if board is not None else None
    for egg in list(splits.findall("Egg")):
        if egg is not start_split:
            splits.remove(egg)
    _set(start_split, "TimeToFirstCheckpoint", f"{project.environment.time_to_first_checkpoint:.5f}")
    _set(start_split, "numberOfSplitTimePoints", str(len(project.checkpoints)))
    _set(start_split, "PercentageTimeChange", f"{project.environment.percentage_time_change:.5f}")
    _set_matrix(start_split, project.start.center, project.start.heading)
    for i, cp in enumerate(project.checkpoints):
        name = f"SplitTime{i}"
        egg = copy.deepcopy(gate)
        egg.set("Name", name)
        _set_matrix(egg, cp.center, cp.heading)
        _set(egg, "Split Time ID", str(i))
        _set(egg, "Radius", f"{cp.radius:.5f}")
        _set(egg, "ExtraTime", f"{cp.extra_time:.5f}")
        splits.append(egg)
        if cp.boards and board is not None:
            for k in range(4):
                ang = math.radians(cp.heading + 45.0 + 90.0 * k)
                r = cp.board_spacing / math.sqrt(2.0)
                p = (cp.center[0] + r * math.sin(ang), cp.center[1], cp.center[2] + r * math.cos(ang))
                b = copy.deepcopy(board)
                b.set("Name", f"{name}-{k}")
                _set(b, "en3d Model Name", CHECKPOINT_MODEL)
                _set_matrix(b, p, cp.heading + 90.0)
                splits.append(b)
    report["checkpoints"] = len(project.checkpoints)

    # pace notes
    notes = _list(root, "RacePaceNotes")
    if notes is not None:
        template_note = notes.find("Egg")
        for egg in list(notes.findall("Egg")):
            notes.remove(egg)
        mode = project.build.pacenotes
        if mode == "manual":
            items = [(n.position, n.heading, n.note_id, n.distance) for n in project.pacenotes]
        elif mode == "auto":
            items = [(p, h, nid, 20.0) for p, h, nid in auto_pacenotes(line)]
        else:
            items = []
        if template_note is not None:
            for i, (p, h, nid, dist) in enumerate(items):
                egg = copy.deepcopy(template_note)
                egg.set("Name", f"PaceNote{i}")
                _set_matrix(egg, (p[0], p[1] + 1.0, p[2]), h)
                _set(egg, "Pace Note Trigger ID (Unique)", str(i))
                _set(egg, "Pace Note ID (Graphics to Display)", str(int(nid)))
                _set(egg, "Distance", f"{dist:.5f}")
                notes.append(egg)
        report["pace_notes"] = len(items)

    # marker lists
    _replace_markers(_list(root, "RaceLine"), line)
    _replace_markers(_ensure_marker_list(root, "StartArea"), project.start.quad())
    _replace_markers(_ensure_marker_list(root, "FinishArea"), project.finish.quad())
    lists = limit_lists(project, line)
    for name in LIMIT_NAMES:
        _replace_markers(_ensure_marker_list(root, name), lists[name])
    cams = project.environment.replay_cameras or auto_cameras(line)
    cam_list = _list(root, "Cameras")
    if cam_list is not None:
        _replace_markers(cam_list, cams, marker_type="markers\\green_marker", first_type="markers\\yellow_marker")
    report.update({"raceline_markers": len(line), "limits": {k: len(v) for k, v in lists.items()},
                   "replay_cameras": len(cams), "limits_mode": project.limits.mode})

    ET.indent(root, "  ")
    text = ET.tostring(root, encoding="unicode")
    return text.replace("\n", "\r\n").encode("utf-8") + b"\r\n", report


def auto_cameras(line, spacing: float = 140.0, side: float = 14.0, height: float = 5.0):
    from ..course_entry import RouteFrame
    if len(line) < 2:
        return []
    frame = RouteFrame(line)
    out, s, k = [], 0.0, 0
    while s <= frame.total:
        p = frame.place(s, side if k % 2 == 0 else -side, height)[0]
        out.append(p)
        s += spacing
        k += 1
    return out


def build_hnt(key: str, textures) -> bytes:
    lower = key.lower()
    lines = [f"Model\t[course\\{lower}\\{lower}]"] + [f"Texture\t[course\\{lower}\\{t}]" for t in textures]
    return ("\r\n".join(lines) + "\r\n").encode("ascii")


def read_scene(path: Path) -> dict:
    """Markers/route/checkpoints of an existing RaceTest scene (for Retail import)."""
    root = ET.parse(path).getroot()
    def markers(name):
        lst = _list(root, name)
        if lst is None:
            return []
        return [tuple(float(v) for v in _value(m, "Marker Pos").get("Value").split()) for m in lst.findall("Marker")]
    def row3(egg):
        node = egg.find("Value[@Name='en3d Matrix']")
        return tuple(float(v) for v in node.get("Row3").split()[:3]), node
    out = {"raceline": markers("RaceLine"), "start": markers("StartArea"), "finish": markers("FinishArea"),
           "limits": {n: markers(n) for n in LIMIT_NAMES}, "cameras": markers("Cameras"),
           "checkpoints": [], "pacenotes": [], "sounds": [], "landscape": []}
    land = _list(root, "landscape")
    for egg in (land.findall("Egg") if land is not None else []):
        out["landscape"].append(_value(egg, "en3d Model Name").get("Value"))
    splits = _list(root, "SplitTimes")
    for egg in (splits.findall("Egg") if splits is not None else []):
        names = _ai_names(egg)
        if "gaRaceSplitTimeAI" in names:
            pos, node = row3(egg)
            r2 = [float(v) for v in node.get("Row2").split()[:3]]
            out["checkpoints"].append({"name": egg.get("Name"), "center": pos,
                                       "radius": float(_value(egg, "Radius").get("Value")),
                                       "extra_time": float(_value(egg, "ExtraTime").get("Value")),
                                       "id": int(_value(egg, "Split Time ID").get("Value")),
                                       "boards": any(e.get("Name", "").startswith(egg.get("Name") + "-")
                                                     for e in splits.findall("Egg"))})
        if "gaRacePostFirstSplitTimeAI" in names:
            out["first_time"] = float(_value(egg, "TimeToFirstCheckpoint").get("Value"))
            out["percentage"] = float(_value(egg, "PercentageTimeChange").get("Value"))
    notes = _list(root, "RacePaceNotes")
    for egg in (notes.findall("Egg") if notes is not None else []):
        pos, node = row3(egg)
        r2 = [float(v) for v in node.get("Row2").split()[:3]]
        out["pacenotes"].append({"position": pos, "heading": math.degrees(math.atan2(r2[0], r2[2])),
                                 "id": int(_value(egg, "Pace Note ID (Graphics to Display)").get("Value")),
                                 "distance": float(_value(egg, "Distance").get("Value"))})
    sound = _list(root, "Sound")
    for egg in (sound.findall("Egg") if sound is not None else []):
        if "enAiSoundSource" in _ai_names(egg) or "gaAiWaterfallSound" in _ai_names(egg):
            out["sounds"].append({"name": egg.get("Name"), "position": row3(egg)[0]})
    return out
