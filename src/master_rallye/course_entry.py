"""Concept generator for a new RaceTest scene on a stitched route.

This is an experimental *new-file* writer, unlike the source-preserving G0/G1.1
transaction in :mod:`master_rallye.course_race_authoring`. It starts from a
Retail template scene, keeps every component it does not understand, and
rebuilds only route-shaped data:

* ``landscape`` model name and ``gaIContAIManager`` dataset name;
* ``RaceLine`` and the four limit lists (new marker topology; Marker Dir keeps
  the Retail placeholder ``1 0 0`` because its use is unknown);
* StartArea/FinishArea, start-relative eggs (Cars, StartSplitTime) and
  end-relative data re-anchored with a rigid route-frame transform;
* SplitTime eggs (main and visual companions) placed by route fraction;
* RacePaceNotes, Cameras and EnvironmentSounds transferred from the source
  stages whose road the new route actually follows.

None of this output is runtime-tested. Topology-changing marker lists are
outside every confirmed authoring result; see docs/course-new-entries.md.
"""
from __future__ import annotations

import copy
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

Vec3 = tuple[float, float, float]
LIMIT_LISTS = ("LeftInnerLimit", "LeftOuterLimit", "RightInnerLimit", "RightOuterLimit")


def _fmt(v: float) -> str:
    return f"{v:.2f}"


def _vec(raw: str) -> Vec3:
    parts = raw.split()
    return float(parts[0]), float(parts[1]), float(parts[2])


class RouteFrame:
    """Arc-length parameterised route with X/Z forward and lateral axes."""

    def __init__(self, samples: Sequence[Vec3]) -> None:
        if len(samples) < 2:
            raise ValueError("route needs two samples")
        self.samples = list(samples)
        self.cum = [0.0]
        for a, b in zip(self.samples, self.samples[1:]):
            self.cum.append(self.cum[-1] + math.dist(a, b))
        self.total = self.cum[-1]

    def forward(self, k: int) -> tuple[float, float]:
        a = self.samples[max(0, min(k, len(self.samples) - 2))]
        b = self.samples[max(1, min(k + 1, len(self.samples) - 1))]
        dx, dz = b[0] - a[0], b[2] - a[2]
        n = math.hypot(dx, dz) or 1.0
        return dx / n, dz / n

    def nearest(self, p: Vec3) -> int:
        return min(range(len(self.samples)), key=lambda k: (self.samples[k][0] - p[0]) ** 2 + (self.samples[k][2] - p[2]) ** 2)

    def local(self, p: Vec3) -> tuple[float, float, float, float, int]:
        """Return (distance along route, lateral, height delta, yaw, index)."""
        k = self.nearest(p)
        fx, fz = self.forward(k)
        base = self.samples[k]
        ox, oz = p[0] - base[0], p[2] - base[2]
        along = ox * fx + oz * fz
        side = fx * oz - fz * ox
        return self.cum[k] + along, side, p[1] - base[1], math.atan2(fz, fx), k

    def local_near(self, p: Vec3, around: float, window: float = 100.0) -> tuple[float, float]:
        """(along, side) using only samples within ``window`` of arc length ``around``.

        Avoids snapping to another part of a route that passes nearby.
        """
        lo = next((i for i, c in enumerate(self.cum) if c >= around - window), 0)
        hi = next((i for i, c in enumerate(self.cum) if c > around + window), len(self.cum) - 1)
        k = min(range(lo, hi + 1), key=lambda i: (self.samples[i][0] - p[0]) ** 2 + (self.samples[i][2] - p[2]) ** 2)
        fx, fz = self.forward(k)
        base = self.samples[k]
        ox, oz = p[0] - base[0], p[2] - base[2]
        return self.cum[k] + ox * fx + oz * fz, fx * oz - fz * ox

    def at(self, distance: float) -> tuple[Vec3, float, int]:
        """Point on the route at arc length, plus its yaw and segment index."""
        distance = max(0.0, min(self.total, distance))
        k = max(0, min(len(self.cum) - 2, next((i for i in range(len(self.cum) - 1) if self.cum[i + 1] >= distance), len(self.cum) - 2)))
        seg = self.cum[k + 1] - self.cum[k] or 1.0
        f = (distance - self.cum[k]) / seg
        a, b = self.samples[k], self.samples[k + 1]
        p = tuple(a[i] + (b[i] - a[i]) * f for i in range(3))
        fx, fz = self.forward(k)
        return p, math.atan2(fz, fx), k  # type: ignore[return-value]

    def place(self, distance: float, side: float, dy: float) -> tuple[Vec3, float]:
        """Place by arc length; beyond either end, extrapolate along the end tangent."""
        p, yaw, _ = self.at(distance)
        fx, fz = math.cos(yaw), math.sin(yaw)
        overshoot = distance - self.total if distance > self.total else min(0.0, distance)
        p = (p[0] + fx * overshoot, p[1], p[2] + fz * overshoot)
        # lateral axis (-fz, fx) has local side +1 (see ``local``)
        return (p[0] - fz * side, p[1] + dy, p[2] + fx * side), yaw


def _rotate_xz(v: Vec3, angle: float) -> Vec3:
    c, s = math.cos(angle), math.sin(angle)
    return v[0] * c - v[2] * s, v[1], v[0] * s + v[2] * c


@dataclass(frozen=True)
class Placement:
    """How an object keeps its relation to the route when re-anchored."""

    mode: str  # "start", "end" or "fraction"


def _remap_point(p: Vec3, old: RouteFrame, new: RouteFrame, mode: str) -> tuple[Vec3, float]:
    along, side, dy, yaw_old, _ = old.local(p)
    if mode == "start":
        target = along
    elif mode == "end":
        target = new.total - (old.total - along)
    else:
        target = along / (old.total or 1.0) * new.total
    q, yaw_new = new.place(target, side, dy)
    return q, yaw_new - yaw_old


def _matrix_value(egg: ET.Element) -> ET.Element | None:
    return egg.find("Value[@Name='en3d Matrix']")


def _remap_egg(egg: ET.Element, old: RouteFrame, new: RouteFrame, mode: str) -> None:
    m = _matrix_value(egg)
    if m is None:
        return
    row3 = m.get("Row3", "0 0 0 1").split()
    p = (float(row3[0]), float(row3[1]), float(row3[2]))
    q, dyaw = _remap_point(p, old, new, mode)
    for row in ("Row0", "Row1", "Row2"):
        parts = m.get(row, "0 0 0 0").split()
        r = _rotate_xz((float(parts[0]), float(parts[1]), float(parts[2])), dyaw)
        m.set(row, " ".join((*(_fmt(c) for c in r), parts[3])))
    m.set("Row3", " ".join((*(_fmt(c) for c in q), row3[3])))


def _list(root: ET.Element, name: str) -> ET.Element | None:
    return next((lst for lst in root.iter("List") if lst.get("Name") == name), None)


def _marker_positions(lst: ET.Element | None) -> list[Vec3]:
    if lst is None:
        return []
    return [_vec(m.find("Value[@Name='Marker Pos']").get("Value", "")) for m in lst.findall("Marker")]


def _rewrite_markers(lst: ET.Element, positions: Sequence[Vec3]) -> None:
    prototype = lst.find("Marker")
    if prototype is None:
        raise ValueError(f"list {lst.get('Name')} has no Marker prototype")
    tail = prototype.tail
    for marker in lst.findall("Marker"):
        lst.remove(marker)
    for index, p in enumerate(positions):
        marker = copy.deepcopy(prototype)
        marker.set("No", str(index))
        marker.find("Value[@Name='Marker Pos']").set("Value", " ".join(_fmt(c) for c in p))
        marker.tail = tail
        lst.append(marker)


def limit_profile(xml_path: Path) -> dict[str, float]:
    """Median signed lateral offset of each limit list from the stage RaceLine."""
    root = ET.parse(xml_path).getroot()
    route = RouteFrame(_marker_positions(_list(root, "RaceLine")))
    out = {}
    for name in LIMIT_LISTS:
        sides = sorted(route.local(p)[1] for p in _marker_positions(_list(root, name)))
        if sides:
            out[name] = sides[len(sides) // 2]
    return out


def offset_polyline(route: RouteFrame, side: float, spacing: float) -> list[Vec3]:
    count = max(2, int(route.total / spacing) + 1)
    return [route.place(route.total * k / (count - 1), side, 0.0)[0] for k in range(count)]


_MIRRORED = {"LeftInnerLimit": "RightInnerLimit", "RightInnerLimit": "LeftInnerLimit",
             "LeftOuterLimit": "RightOuterLimit", "RightOuterLimit": "LeftOuterLimit"}


def transfer_limits(
    route: Sequence[Vec3],
    legs: Sequence[tuple[Path, bool]],
    *,
    owner_radius: float = 25.0,
    accept_radius: float = 150.0,
    gap: float = 150.0,
    spacing: float = 25.0,
    min_side: float = 8.0,
    clearance_gap: float = 200.0,
    clearance_share: float = 0.45,
    shrink_zones: Sequence[tuple[float, float]] = (),
) -> tuple[dict[str, list[Vec3]], dict]:
    """Rebuild the four limit lists from the Retail stages the route drives.

    Every route sample is owned by the nearest leg whose RaceLine follows it in
    the same direction. A source limit marker is kept when its nearest route
    sample is owned by that marker's stage. Reversed legs swap Left/Right.
    Route spans longer than ``gap`` without a transferred marker get offset
    markers from the median lateral offset of the transferred ones, so the
    corridor has no holes. Synthetic constant offsets alone fold across the
    road in tight corners; Retail limits follow the real road.
    """
    frame = RouteFrame(route)
    legs = list(legs)
    sources = []
    # Both orientations of every stage are candidates; the direction test in
    # the ownership pass picks the one the route actually drives. (Stitching
    # may reverse the first stage without recording it in the leg flags.)
    for path in dict.fromkeys(path for path, _ in legs):
        root = ET.parse(path).getroot()
        line = _marker_positions(_list(root, "RaceLine"))
        for reversed_leg in (False, True):
            oriented = list(reversed(line)) if reversed_leg else line
            sources.append((path, reversed_leg, RouteFrame(oriented), root))
    owner: list[int | None] = []
    for k, p in enumerate(frame.samples):
        fx, fz = frame.forward(k)
        best = None
        for index, (_, _, src, _) in enumerate(sources):
            j = src.nearest(p)
            # Distance to the adjacent segments, not the sample: some Retail
            # RaceLines are 40-50 units apart between samples.
            d = math.inf
            for a_index in (j - 1, j):
                if 0 <= a_index < len(src.samples) - 1:
                    a, b = src.samples[a_index], src.samples[a_index + 1]
                    ex, ez = b[0] - a[0], b[2] - a[2]
                    length_sq = ex * ex + ez * ez or 1e-9
                    t = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[2] - a[2]) * ez) / length_sq))
                    d = min(d, math.hypot(a[0] + ex * t - p[0], a[2] + ez * t - p[2]))
            sx, sz = src.forward(j)
            if d <= owner_radius and fx * sx + fz * sz > 0.5 and (best is None or d < best[0]):
                best = (d, index)
        owner.append(best[1] if best else None)
    result: dict[str, list[Vec3]] = {}
    stats: dict = {"unowned_samples": sum(o is None for o in owner)}
    # Station grid shared by all four lists, with the clearance to any other
    # part of the route (> clearance_gap of arc length away). gaLimitsAI
    # re-selects the globally nearest marker every 15 ticks, so a limit closer
    # to another route portion than to its own (hairpins, parallel legs)
    # classifies a centred car as outside.
    count = max(2, int(frame.total // spacing) + 1)
    stations = [frame.total * step / (count - 1) for step in range(count)]
    caps = []
    for along in stations:
        q = frame.at(along)[0]
        clearance = math.inf
        for k, other in enumerate(frame.samples):
            if abs(frame.cum[k] - along) > clearance_gap:
                clearance = min(clearance, math.hypot(other[0] - q[0], other[2] - q[2]))
        cap = clearance_share * clearance
        for zone_along, factor in shrink_zones:
            if abs(zone_along - along) <= 100.0:
                cap *= factor
        # Never narrower than 12 units to the inner limit: shrinking below
        # min_side drops stations and leaves holes the game cannot bridge.
        caps.append(max(cap, 15.0))
    inner_magnitude: dict[str, list[float]] = {}
    for name in LIMIT_LISTS:
        expected = -1.0 if name.startswith("Left") else 1.0
        picked: list[tuple[float, float, Vec3]] = []
        for index, (_, reversed_leg, _, root) in enumerate(sources):
            source_name = _MIRRORED[name] if reversed_leg else name
            for p in _marker_positions(_list(root, source_name)):
                along, side, _, _, k = frame.local(p)
                # At junctions a stage's limit can cross the mouth of the road
                # the stitched route turns into; a marker on (or across) the
                # driven road puts the car "outside" and triggers resets.
                if owner[k] != index or abs(side) > accept_radius or side * expected < min_side:
                    continue
                picked.append((along, side, p))
        picked.sort(key=lambda item: item[0])
        kept: list[tuple[float, float, Vec3]] = []
        for item in picked:
            if kept and item[0] - kept[-1][0] < 5.0:
                continue
            kept.append(item)
        sides = sorted(s for _, s, _ in kept)
        median = sides[len(sides) // 2] if sides else (-30.0 if name.startswith("Left") else 30.0)
        # gaLimitsAI tests the car against two consecutive segments (markers
        # i, i+1, i+2) of each list, so the list must be one smooth monotonic
        # polyline. Interleaved markers of different stages (-40, -110, -40)
        # make near-lateral segments that classify a centred car as outside.
        # Keep only the corridor width from the Retail markers: interpolate
        # the lateral offset, median-smooth it and emit evenly spaced markers.
        profile = [(a, sd) for a, sd, _ in kept] or [(0.0, median)]
        raw = []
        cursor = 0
        for along in stations:
            while cursor + 1 < len(profile) and profile[cursor + 1][0] < along:
                cursor += 1
            a0, s0 = profile[cursor]
            a1, s1 = profile[min(cursor + 1, len(profile) - 1)]
            t = 0.0 if a1 <= a0 else max(0.0, min(1.0, (along - a0) / (a1 - a0)))
            raw.append((along, s0 + (s1 - s0) * t))
        window = 3
        smoothed = []
        for i, (along, _) in enumerate(raw):
            values = sorted(v for _, v in raw[max(0, i - window):i + window + 1])
            smoothed.append((along, values[len(values) // 2]))
        side_key = "Left" if name.startswith("Left") else "Right"
        capped = []
        for index, (along, side) in enumerate(smoothed):
            magnitude = abs(side)
            if "Inner" in name:
                magnitude = min(magnitude, 0.8 * caps[index])
            else:
                magnitude = min(max(magnitude, inner_magnitude[side_key][index] + 4.0), caps[index])
            capped.append((along, expected * magnitude))
        if "Inner" in name:
            inner_magnitude[side_key] = [abs(v) for _, v in capped]
        filled: list[Vec3] = []
        filler = 0
        last_along = -math.inf
        for along, side in capped:
            # Shrink the offset on the inside of tight corners until the
            # marker stays on its own side and keeps advancing along the
            # route (reversed segments flip the side test).
            for _ in range(8):
                q = frame.place(along, side, 0.0)[0]
                q_along, q_side = frame.local_near(q, along)
                if q_side * expected >= min_side and q_along > last_along + 1.0:
                    filled.append(q)
                    last_along = q_along
                    break
                side *= 0.75
            else:
                # No offset passes: keep the station at the minimum offset
                # rather than leave a gap (a chord across a hairpin gap cuts
                # the corner and classifies the car outside).
                q = frame.place(along, expected * min_side, 0.0)[0]
                q_along = frame.local_near(q, along)[0]
                if q_along > last_along - 10.0:
                    filled.append(q)
                    last_along = max(last_along, q_along)
                else:
                    filler += 1  # dropped: would run backwards
        result[name] = filled
        stats[name] = {"transferred": len(kept), "dropped_stations": filler, "markers": len(filled), "median_side": round(median, 2)}
    return result, stats


def validated_limits(route: Sequence[Vec3], legs: Sequence[tuple[Path, bool]], *, rounds: int = 8,
                     lateral: Sequence[float] = (-4.0, 0.0, 4.0)) -> tuple[dict[str, list[Vec3]], dict]:
    """``transfer_limits`` plus Retail ``gaLimitsAI`` emulation.

    The route is scanned with the car on and beside the RaceLine; every
    station within 100 units of a sample classified outside the inner limits
    has its corridor cap shrunk by 0.8, until no sample fails or ``rounds``
    is exhausted.
    """
    from .course_limits_emulator import scan_route

    zones: list[tuple[float, float]] = []
    for attempt in range(rounds + 1):
        limits, stats = transfer_limits(route, legs, shrink_zones=zones)
        lists = dict(limits)
        lists["RaceLine"] = list(route)
        bad = sorted({row["along"] for row in scan_route(lists, route, lateral) if row["state"] != 0})
        stats["emulated_outside_samples"] = len(bad)
        stats["emulation_rounds"] = attempt
        if not bad:
            break
        zones += [(along, 0.8) for along in bad]
    stats["emulated_outside_at"] = bad[:20]
    return limits, stats


def replace_limit_lists(xml_bytes: bytes, limits: dict[str, list[Vec3]]) -> bytes:
    root = ET.fromstring(xml_bytes)
    for name, positions in limits.items():
        lst = _list(root, name)
        if lst is not None and positions:
            _rewrite_markers(lst, positions)
    return ET.tostring(root, encoding="unicode").encode("utf-8")


def _within(route: RouteFrame, p: Vec3, radius: float) -> bool:
    k = route.nearest(p)
    q = route.samples[k]
    return (q[0] - p[0]) ** 2 + (q[2] - p[2]) ** 2 <= radius * radius


def _collect_transfer(
    sources: Iterable[Path], route: RouteFrame, list_name: str, radius: float, direction_check: bool
) -> list[tuple[float, ET.Element]]:
    found: list[tuple[float, ET.Element]] = []
    for path in sources:
        root = ET.parse(path).getroot()
        lst = _list(root, list_name)
        if lst is None:
            continue
        src_route = RouteFrame(_marker_positions(_list(root, "RaceLine")))
        children = lst.findall("Egg") + lst.findall("Marker")
        for child in children:
            if child.tag == "Egg":
                m = _matrix_value(child)
                if m is None:
                    continue
                r = m.get("Row3", "").split()
                p = (float(r[0]), float(r[1]), float(r[2]))
            else:
                p = _vec(child.find("Value[@Name='Marker Pos']").get("Value", ""))
            if not _within(route, p, radius):
                continue
            along, _, _, yaw_new, _ = route.local(p)
            if direction_check:
                yaw_src = src_route.local(p)[3]
                if math.cos(yaw_new - yaw_src) < 0.5:
                    continue  # this note was authored for the opposite direction
            found.append((along, child))
    found.sort(key=lambda item: item[0])
    deduped: list[tuple[float, ET.Element]] = []
    for along, child in found:
        if deduped and abs(deduped[-1][0] - along) < 8.0 and (
            list_name == "RacePaceNotes" or deduped[-1][1].get("Name") == child.get("Name")
        ):
            continue  # the same corner/object authored in several overlapping stages
        deduped.append((along, child))
    return deduped


def build_entry_racetest(
    template_xml: Path,
    *,
    entry_name: str,
    model_name: str,
    route: Sequence[Vec3],
    source_xmls: Sequence[Path],
    marker_spacing: float = 20.0,
) -> tuple[bytes, dict]:
    """Return (XML bytes, report) for a new course entry scene."""
    from .course_atlas import resample_route

    tree = ET.parse(template_xml)
    root = tree.getroot()
    old_route = RouteFrame(_marker_positions(_list(root, "RaceLine")))
    samples = resample_route(route, marker_spacing)
    new_route = RouteFrame(samples)
    report: dict = {"entry": entry_name, "template": template_xml.name, "route_length": round(new_route.total, 1),
                    "raceline_markers": len(samples)}

    for value in root.iter("Value"):
        if value.get("Name") == "AI DataSet Name":
            value.set("Value", f"ICont/{entry_name.lower()}")
    landscape = _list(root, "landscape")
    if landscape is not None:
        for egg in landscape.findall("Egg"):
            v = egg.find("Value[@Name='en3d Model Name']")
            if v is not None:
                v.set("Value", model_name)

    # Start/finish areas and start-relative eggs keep their local route frame.
    for name, mode in (("StartArea", "start"), ("FinishArea", "end")):
        lst = _list(root, name)
        if lst is not None:
            _rewrite_markers(lst, [_remap_point(p, old_route, new_route, mode)[0] for p in _marker_positions(lst)])
    cars = _list(root, "Cars")
    for egg in (cars.findall("Egg") if cars is not None else []):
        _remap_egg(egg, old_route, new_route, "start")
    splits = _list(root, "SplitTimes")
    for egg in (splits.findall("Egg") if splits is not None else []):
        _remap_egg(egg, old_route, new_route, "start" if egg.get("Name") == "StartSplitTime" else "fraction")

    # Limits: lateral profile from the template stage applied along the new route.
    profile = limit_profile(template_xml)
    for name in LIMIT_LISTS:
        lst = _list(root, name)
        if lst is not None and name in profile:
            _rewrite_markers(lst, offset_polyline(new_route, profile[name], marker_spacing))
    report["limit_profile"] = {k: round(v, 2) for k, v in profile.items()}
    _rewrite_markers(_list(root, "RaceLine"), samples)

    # Transfer route-specific content from every source stage.
    for list_name, radius, direction in (("RacePaceNotes", 12.0, True), ("Cameras", 60.0, False),
                                         ("EnvironmentSounds", 250.0, False)):
        lst = _list(root, list_name)
        if lst is None:
            continue
        moved = _collect_transfer(source_xmls, new_route, list_name, radius, direction)
        tail = (lst.findall("Egg") + lst.findall("Marker") or [None])[0]
        tail_text = tail.tail if tail is not None else None
        for child in lst.findall("Egg") + lst.findall("Marker"):
            lst.remove(child)
        for index, (_, child) in enumerate(moved):
            clone = copy.deepcopy(child)
            clone.tail = tail_text
            if clone.tag == "Marker":
                clone.set("No", str(index))
            elif list_name == "RacePaceNotes":
                clone.set("Name", f"PaceNote{index + 1}")
                trigger = clone.find(".//Value[@Name='Pace Note Trigger ID (Unique)']")
                if trigger is not None:
                    trigger.set("Value", str(index + 1))
            lst.append(clone)
        report[f"{list_name}_transferred"] = len(moved)

    data = ET.tostring(root, encoding="unicode")
    return data.encode("utf-8"), report


def build_entry_hnt(model_name: str, textures: Iterable[str]) -> bytes:
    """HNT manifest: one Model line plus Texture lines (Retail syntax)."""
    lines = [f"Model\t[{model_name}]"]
    lines += [f"Texture\t[{t}]" for t in textures]
    return ("\r\n".join(lines) + "\r\n").encode("ascii")
