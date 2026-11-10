"""AI route (RaceLine), limits, route checks and the native AI heading field.

Native AI data of a course is exactly two things (CONFIRMED by the Retail scene
and ``gaIContAIManager``): the RaceLine marker list in the RaceTest and the
``DataScene/ICont/<name>.sfl`` heading field. The field is synthesised from the
route with the pure-pursuit model fitted to Retail fields
(:func:`master_rallye.course_sfl_field.synthesize_pursuit_field`), which is
what the game's AI steers by. Player movement is not restricted by the route:
the only player-facing restriction is gaLimitsAI (reset beyond the outer
limits), which the ``wide`` mode moves far away for open terrain.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..course_atlas import resample_route
from ..course_entry import RouteFrame, offset_polyline
from .model import CourseProject

LIMIT_NAMES = ("LeftInnerLimit", "LeftOuterLimit", "RightInnerLimit", "RightOuterLimit")
# Retail median lateral offsets (France1/Spain2/Turkey1/Italy2): inner 19..45, outer 30..75.
LIMIT_PRESETS = {"road": (25.0, 45.0), "wide": (150.0, 300.0)}


def raceline(project: CourseProject) -> list:
    pts = [tuple(p) for p in project.route.points]
    if len(pts) < 2:
        return pts
    return resample_route(pts, max(5.0, project.route.spacing))


def limit_lists(project: CourseProject, line=None) -> dict:
    line = line if line is not None else raceline(project)
    mode = project.limits.mode
    if mode == "manual" and project.limits.lists:
        return {k: [tuple(p) for p in v] for k, v in project.limits.lists.items()}
    if mode == "wide":
        inner, outer = LIMIT_PRESETS["wide"]
    else:
        inner, outer = project.limits.inner, project.limits.outer
    if len(line) < 2:
        return {name: [] for name in LIMIT_NAMES}
    frame = RouteFrame(line)
    spacing = max(5.0, project.route.spacing)
    return {"LeftInnerLimit": offset_polyline(frame, -inner, spacing),
            "LeftOuterLimit": offset_polyline(frame, -outer, spacing),
            "RightInnerLimit": offset_polyline(frame, inner, spacing),
            "RightOuterLimit": offset_polyline(frame, outer, spacing)}


def sfl_bytes(project: CourseProject, line=None) -> bytes:
    from ..course_sfl_field import synthesize_pursuit_field
    line = line if line is not None else raceline(project)
    if len(line) < 2:
        raise ValueError("the AI route needs at least two points")
    return synthesize_pursuit_field(line)


@dataclass
class RouteIssue:
    severity: str
    message: str
    position: tuple
    index: int = -1


def _yaw(a, b):
    return math.atan2(b[0] - a[0], b[2] - a[2])


def route_issues(project: CourseProject, heights=None) -> list[RouteIssue]:
    """Sharp corners, duplicate points, steep grades, start/finish/checkpoint order along the route."""
    pts = [tuple(p) for p in project.route.points]
    out: list[RouteIssue] = []
    if len(pts) < 2:
        out.append(RouteIssue("error", "the AI route needs at least two points", (0.0, 0.0, 0.0)))
        return out
    line = resample_route(pts, 5.0)
    for i in range(1, len(pts)):
        if math.dist(pts[i], pts[i - 1]) < 0.5:
            out.append(RouteIssue("warning", "route points closer than 0.5 m", pts[i], i))
    # turn per 20 m of arc length
    window = 4
    for i in range(window, len(line) - window):
        a = _yaw(line[i - window], line[i])
        b = _yaw(line[i], line[i + window])
        turn = abs((b - a + math.pi) % (2 * math.pi) - math.pi)
        if turn > math.radians(100):
            out.append(RouteIssue("warning", f"very sharp corner ({math.degrees(turn):.0f} degrees within 40 m)", line[i]))
        if i + 1 < len(line):
            run = math.hypot(line[i + 1][0] - line[i][0], line[i + 1][2] - line[i][2])
            if run > 1e-6 and abs(line[i + 1][1] - line[i][1]) / run > 0.6:
                out.append(RouteIssue("warning", "route grade steeper than 60 %", line[i]))
    if heights is not None:
        for p in line[::4]:
            g = heights(p[0], p[2])
            if g is None:
                out.append(RouteIssue("error", "AI route leaves the terrain", p))
            elif abs(p[1] - g) > 6.0:
                out.append(RouteIssue("warning", f"AI route is {p[1] - g:+.1f} m from the ground (use Snap Route)", p))
    frame = RouteFrame(line)
    def along(p):
        return frame.local(p)[0], abs(frame.local(p)[1])
    s0, d0 = along(project.start.center)
    s1, d1 = along(project.finish.center)
    if d0 > 30:
        out.append(RouteIssue("error", f"start area is {d0:.0f} m away from the AI route", project.start.center))
    if d1 > 30:
        out.append(RouteIssue("error", f"finish area is {d1:.0f} m away from the AI route", project.finish.center))
    if s1 <= s0:
        out.append(RouteIssue("error", "the finish is not after the start along the AI route (reverse the route?)",
                              project.finish.center))
    last = s0
    for i, cp in enumerate(project.checkpoints):
        s, d = along(cp.center)
        if d > max(cp.radius, 25.0):
            out.append(RouteIssue("error", f"checkpoint {i + 1} is {d:.0f} m from the AI route", cp.center, i))
        if s < last:
            out.append(RouteIssue("error", f"checkpoint {i + 1} comes before the previous gate along the route",
                                  cp.center, i))
        if not (s0 <= s <= s1):
            out.append(RouteIssue("error", f"checkpoint {i + 1} is outside the start-finish part of the route",
                                  cp.center, i))
        last = s
    # Retail: the final RaceLine marker must not pass close to its own finish early (E2.1 progress jump)
    for i, p in enumerate(line[:-30]):
        if math.dist(p, project.finish.center) < 40.0 and frame.cum[i] < frame.total - 200:
            out.append(RouteIssue("warning", "the route passes near the finish long before it ends", p))
            break
    return out


def heading_at(line, index) -> float:
    a = line[max(0, index - 1)]
    b = line[min(len(line) - 1, index + 1)]
    return math.degrees(_yaw(a, b))


def snap_to_ground(points, heights, lift: float = 0.0):
    out = []
    for p in points:
        g = heights(p[0], p[2])
        out.append((p[0], (g + lift) if g is not None else p[1], p[2]))
    return out


def place_along(line, count: int, *, start_fraction: float = 0.15, end_fraction: float = 0.9):
    """``count`` evenly spaced (position, heading) pairs between two route fractions."""
    if len(line) < 2 or count <= 0:
        return []
    frame = RouteFrame(line)
    out = []
    for k in range(count):
        f = start_fraction + (end_fraction - start_fraction) * (k + 0.5) / count
        p, yaw, _ = frame.at(frame.total * f)
        fx, fz = math.cos(yaw), math.sin(yaw)
        out.append((p, math.degrees(math.atan2(fx, fz))))
    return out


def auto_pacenotes(line, *, spacing: float = 250.0):
    """Pace-note arrows at significant corners.

    Retail notes are sparse ``gps_arrow`` eggs (median 315 m apart, Distance 20).
    The ID choice follows the Retail statistics: IDs 23/22 mostly mark turns of
    one sign, 12/3 the other, grouped by severity. It is an approximation; the
    Studio lets every note ID be edited.
    """
    if len(line) < 6:
        return []
    frame = RouteFrame(line)
    notes, last = [], -1e9
    s = 40.0
    while s < frame.total - 60:
        y0 = frame.at(s)[1]
        best = 0.0
        for look in (25.0, 50.0, 75.0):
            dy = (frame.at(s + look)[1] - y0 + math.pi) % (2 * math.pi) - math.pi
            if abs(dy) > abs(best):
                best = dy
        deg = math.degrees(best)
        if abs(deg) > 25 and s - last > spacing * 0.5:
            severe = abs(deg) > 45
            note = (23 if severe else 22) if deg > 0 else (12 if severe else 3)
            p, yaw, _ = frame.at(max(0.0, s - 20.0))
            fx, fz = math.cos(yaw), math.sin(yaw)
            notes.append((p, math.degrees(math.atan2(fx, fz)), note))
            last = s
        s += 10.0
    return notes


def simulate_ai_path(sfl: bytes, start, heading_deg: float, *, step: float = 1.0, max_turn_deg: float = 6.0,
                     max_steps: int = 40000, stop_at=None, stop_radius: float = 15.0):
    """Path a car would follow by steering along the native AI heading field.

    The heading byte of a cell is ``256 * atan2(-dx, dz) / 2pi`` (course_sfl_field);
    the simulated car turns towards it by at most ``max_turn_deg`` per metre.
    It is a preview of the steering field, not of the game's vehicle dynamics.
    """
    from ..sfl import parse_sfl_bytes
    from ..course_sfl_field import sample
    field = parse_sfl_bytes(sfl, "<studio>")
    x, y, z = start
    ang = math.radians(heading_deg)          # game heading: 0 = +Z, 90 = +X
    out = [(x, y, z)]
    limit = math.radians(max_turn_deg) * step
    for _ in range(max_steps):
        value = sample(field, x, z)
        if value is None:
            break
        a = value * 2 * math.pi / 256.0
        target = math.atan2(-math.sin(a), math.cos(a))   # direction (dx, dz) = (-sin a, cos a) as a heading
        diff = (target - ang + math.pi) % (2 * math.pi) - math.pi
        ang += max(-limit, min(limit, diff))
        x += math.sin(ang) * step
        z += math.cos(ang) * step
        out.append((x, y, z))
        if stop_at is not None and math.hypot(x - stop_at[0], z - stop_at[2]) < stop_radius:
            break
    return out
