"""V-MESH diagnostics: measure wheel/body alignment of a car.dx + complete.dx + wheel.dx set.

Reusable, donor-agnostic measurements (no GT data needed):

* frame offset: ``complete.dx`` equals ``car.dx`` translated by a per-vehicle constant dy
  (verified in all 25 stock donors); a candidate must keep that relation for its body draws;
* wheel hubs in both frames and tyre/body clearance (vertex + edge-midpoint + centroid samples);
* donor leftovers / crew headroom under the body roof; hull versus body extents.

Usage: python tools/vmesh_diagnose.py --donor-dir <retail Navara> --candidate-dir <family dir> --out report.json
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from master_rallye.dx import parse_dx  # noqa: E402

BODY_DRAWS = {"car": (3, 9, 24, 25, 35), "complete": (3, 9, 16, 25, 24)}
WHEEL_DRAWS_COMPLETE = (20, 21, 22, 23)


def draw_points(model, index):
    d = model.physical_draws[index]
    return list(model.vertices.positions[d.vertex_base:d.vertex_base + d.local_vertex_max + 1])


def draw_triangles(model, index):
    d = model.physical_draws[index]
    pos = model.vertices.positions
    out = []
    for t in range(d.triangle_count):
        a, b, c = (model.global_index_table.indices[d.index_start + 3 * t + k] for k in range(3))
        out.append((pos[a], pos[b], pos[c]))
    return out


def frame_offset(donor_car, donor_complete) -> dict:
    """Median/min/max dy between identical draws of a donor car.dx and complete.dx."""
    def keyed(m):
        out = {}
        for d in m.physical_draws:
            ps = m.vertices.positions[d.vertex_base:d.vertex_base + d.local_vertex_max + 1]
            out.setdefault((d.texture_slots[0].value, d.triangle_count, len(ps)), []).append(ps)
        return out
    a, b = keyed(donor_car), keyed(donor_complete)
    dys, dxs, dzs = [], [], []
    for key, ps in a.items():
        if key in b and len(ps) == 1 and len(b[key]) == 1 and key[1] >= 20:
            p, q = ps[0], b[key][0]
            dys.append(statistics.mean(v[1] for v in q) - statistics.mean(v[1] for v in p))
            dxs.append(statistics.mean(v[0] for v in q) - statistics.mean(v[0] for v in p))
            dzs.append(statistics.mean(v[2] for v in q) - statistics.mean(v[2] for v in p))
    if not dys:
        raise ValueError("no matching draws between car.dx and complete.dx")
    return {"dy": statistics.median(dys), "dy_min": min(dys), "dy_max": max(dys), "matched_draws": len(dys),
            "dx_abs_max": max(abs(v) for v in dxs), "dz_abs_max": max(abs(v) for v in dzs)}


def donor_hubs_complete(complete) -> list[tuple[float, float, float]]:
    pts = [p for i in WHEEL_DRAWS_COMPLETE for p in draw_points(complete, i)]
    hubs = []
    for sx in (-1, 1):
        for sz in (1, -1):
            q = [p for p in pts if p[0] * sx > 0 and p[2] * sz > 0]
            hubs.append(tuple((min(p[i] for p in q) + max(p[i] for p in q)) / 2 for i in range(3)))   # bbox centre
    return hubs


def wheel_extent(wheel) -> tuple[float, float]:
    ps = wheel.vertices.positions
    return ((max(p[1] for p in ps) - min(p[1] for p in ps)) / 2, (max(p[0] for p in ps) - min(p[0] for p in ps)) / 2)


def samples(tri):
    a, b, c = tri
    mid = lambda p, q: tuple((p[i] + q[i]) / 2 for i in range(3))
    cen = tuple((a[i] + b[i] + c[i]) / 3 for i in range(3))
    return [a, b, c, mid(a, b), mid(b, c), mid(c, a), cen]


def clearance(model, draws, hubs, radius, half_width) -> dict:
    """Penetration of body samples into the (visual) tyre cylinders, per hub."""
    out = []
    for hx, hy, hz in hubs:
        inside, deepest, gap = 0, 0.0, None
        for d in draws:
            for tri in draw_triangles(model, d):
                for si, p in enumerate(samples(tri)):
                    r = math.hypot(p[1] - hy, p[2] - hz)
                    if abs(p[0] - hx) <= half_width:
                        if r < radius:
                            inside += 1
                            deepest = max(deepest, radius - r)
                    outboard = (p[0] - hx) * (1 if hx > 0 else -1)
                    if si < 3 and p[1] > hy and half_width < outboard <= half_width + 0.35 and abs(p[2] - hz) < radius * 1.6:
                        gap = (r - radius) if gap is None else min(gap, r - radius)   # visible arch lip vs tyre
        out.append({"hub": [round(v, 3) for v in (hx, hy, hz)], "samples_inside_tyre": inside, "max_penetration_m": round(deepest, 4),
                    "arch_lip_gap_m": None if gap is None else round(gap, 4)})
    return {"tyre_radius": round(radius, 4), "tyre_half_width": round(half_width, 4), "hubs": out}


def bbox(points):
    return ([round(min(p[i] for p in points), 3) for i in range(3)], [round(max(p[i] for p in points), 3) for i in range(3)])


def roof_p99(points) -> float:
    ys = sorted(p[1] for p in points)
    return ys[int(len(ys) * 0.99)]


def open_edges_near_wheels(model, draws, hubs, radius, half_width, weld=1e-4) -> dict:
    """Surface continuity around the arches: edges used by a single triangle (positions welded) near each hub.

    A closed wheel house has no open edge except where the body itself ends (sills, bumpers).  Counted per hub in
    the side-view disc ``radius + 0.15`` on the hub side (``|x|`` beyond the tyre's inner face).
    """
    def key(p):
        return tuple(round(c / weld) for c in p)
    edges = {}
    for d in draws:
        for a, b, c in draw_triangles(model, d):
            for u, v in ((a, b), (b, c), (c, a)):
                k = tuple(sorted((key(u), key(v))))
                rec = edges.setdefault(k, [0, u, v])
                rec[0] += 1
    out = []
    for hx, hy, hz in hubs:
        n = 0
        total = 0
        for cnt, u, v in edges.values():
            mid = tuple((u[i] + v[i]) / 2 for i in range(3))
            if abs(mid[0]) < abs(hx) - half_width - 0.1 or mid[0] * hx < 0:
                continue
            if math.hypot(mid[1] - hy, mid[2] - hz) > radius + 0.15:
                continue
            total += 1
            n += cnt == 1
        # lip loop: edges whose both ends sit on one circle (within 3 mm) around the hub, outboard of the tyre
        lip_r = None
        for cnt, u, v in edges.values():
            if cnt == 1 and u[0] * hx > 0 and abs(u[0]) > abs(hx) - half_width:
                ru, rv = math.hypot(u[1] - hy, u[2] - hz), math.hypot(v[1] - hy, v[2] - hz)
                if abs(ru - rv) < 0.003 and radius < ru < radius + 0.2 and (lip_r is None or ru < lip_r):
                    lip_r = ru
        lip_total = lip_open = 0
        if lip_r is not None:
            for cnt, u, v in edges.values():
                if u[0] * hx <= 0 or v[0] * hx <= 0:
                    continue
                ru, rv = math.hypot(u[1] - hy, u[2] - hz), math.hypot(v[1] - hy, v[2] - hz)
                if abs(ru - lip_r) < 0.01 and abs(rv - lip_r) < 0.01 and abs(ru - rv) < 0.003 and abs(u[0]) > abs(hx) - half_width and abs(u[0] - v[0]) < 0.05:
                    lip_total += 1
                    lip_open += cnt == 1
        out.append({"hub": [round(hx, 3), round(hy, 3), round(hz, 3)], "edges_in_zone": total, "open_edges": n,
                    "lip_radius": None if lip_r is None else round(lip_r, 4), "lip_edges": lip_total, "lip_edges_open": lip_open})
    return {"zone_radius": round(radius + 0.15, 3), "hubs": out, "open_edges_total": sum(h["open_edges"] for h in out),
            "lip_edges_open_total": sum(h["lip_edges_open"] for h in out)}


def ground_clearance(model, draws, ground_y: float) -> dict:
    """Body clearance above the *physical* ground (hub height - physical tyre radius) in the given frame."""
    pts = [p for d in draws for p in draw_points(model, d)]
    skirt = sorted(p[1] for p in pts if abs(p[0]) > 0.85 and abs(p[2]) < 1.0)
    low = sorted(p[1] for p in pts)
    return {"ground_y": round(ground_y, 4), "lowest_body_vertex": round(low[0] - ground_y, 4),
            "lowest_side_skirt": round(skirt[0] - ground_y, 4) if skirt else None,
            "side_skirt_p5": round(skirt[len(skirt) // 20] - ground_y, 4) if skirt else None,
            "roof_p99_above_ground": round(roof_p99(pts) - ground_y, 4)}


def interior_containment(model, interior_draw, shell_draws) -> dict:
    """Cabin-shell points above/outside the paint+trim+glass shell bounding box (poke-through risk)."""
    inside = draw_points(model, interior_draw)
    shell = [p for d in shell_draws for p in draw_points(model, d)]
    lo = [min(p[i] for p in shell) for i in range(3)]
    hi = [max(p[i] for p in shell) for i in range(3)]
    roof = roof_p99(shell)
    return {"interior_top": round(max(p[1] for p in inside), 4), "shell_roof_p99": round(roof, 4),
            "interior_top_below_shell_roof_m": round(roof - max(p[1] for p in inside), 4),
            "points_outside_shell_bbox": sum(1 for p in inside if any(not (lo[i] <= p[i] <= hi[i]) for i in range(3)))}


def diagnose(donor_dir: Path, cand_dir: Path, crew_draws, leftover_draws, label: str, *, body_draws=None) -> dict:
    dcar, dcomp = parse_dx(donor_dir / "car.dx"), parse_dx(donor_dir / "complete.dx")
    ccar, ccomp = parse_dx(cand_dir / "car.dx"), parse_dx(cand_dir / "complete.dx")
    cwheel = parse_dx(cand_dir / "wheel.dx")
    body_draws = BODY_DRAWS if body_draws is None else body_draws
    off = frame_offset(dcar, dcomp)
    hubs_c = donor_hubs_complete(dcomp)
    hubs_r = [(x, y - off["dy"], z) for x, y, z in hubs_c]      # hypothesis H1: same relation as the donor pair
    r_vis, hw_vis = wheel_extent(cwheel)
    out = {"label": label, "donor_frame_offset": off,
           "hubs_complete_frame": [[round(v, 3) for v in h] for h in hubs_c],
           "hubs_car_frame_H1": [[round(v, 3) for v in h] for h in hubs_r],
           "visual_wheel": {"radius_wheel_dx": round(r_vis, 4), "half_width": round(hw_vis, 4)}}
    # frame consistency: body-role draws of the candidate must differ by the donor dy
    dev = []
    for a, b in zip(body_draws["car"], body_draws["complete"]):
        pa, pb = draw_points(ccar, a), draw_points(ccomp, b)
        if len(pa) == len(pb):
            dev.append(statistics.mean(p[1] for p in pb) - statistics.mean(p[1] for p in pa))
    out["candidate_frame_offset_body_draws"] = [round(v, 4) for v in dev]
    out["frame_offset_error_m"] = [round(v - off["dy"], 4) for v in dev]
    body_car = [p for d in body_draws["car"] for p in draw_points(ccar, d)]
    body_comp = [p for d in body_draws["complete"] for p in draw_points(ccomp, d)]
    out["body_bbox_car_frame"], out["body_bbox_complete_frame"] = bbox(body_car), bbox(body_comp)
    out["body_roof_p99_car_frame"] = round(roof_p99(body_car), 3)
    out["body_draws_checked"] = body_draws
    out["clearance_car_frame"] = clearance(ccar, body_draws["car"], hubs_r, r_vis, hw_vis)
    out["clearance_complete_frame"] = clearance(ccomp, body_draws["complete"], hubs_c, r_vis, hw_vis)
    out["open_edges_arches_car_frame"] = open_edges_near_wheels(ccar, body_draws["car"], hubs_r, r_vis, hw_vis)
    out["open_edges_arches_complete_frame"] = open_edges_near_wheels(ccomp, body_draws["complete"], hubs_c, r_vis, hw_vis)
    r_phys = wheel_extent(parse_dx(donor_dir / "wheel.dx"))[0]
    out["physical_tyre_radius_donor"] = round(r_phys, 4)
    out["ground_clearance_car_frame"] = ground_clearance(ccar, body_draws["car"], sum(h[1] for h in hubs_r) / 4 - r_phys)
    out["ground_clearance_complete_frame"] = ground_clearance(ccomp, body_draws["complete"], sum(h[1] for h in hubs_c) / 4 - r_phys)
    # Pool-based imports can repurpose draw 0. This legacy donor draw is not assumed to remain the cabin.
    out["interior_containment_complete"] = (interior_containment(ccomp, 0, body_draws["complete"])
                                           if 0 not in body_draws["complete"] else {"status": "NOT_APPLICABLE_DRAW0_REPURPOSED"})
    crew = [p for d in crew_draws for p in draw_points(ccar, d)]
    if crew:
        out["crew_bbox_car_frame"] = bbox(crew)
        out["crew_headroom_under_roof_m"] = round(roof_p99(body_car) - max(p[1] for p in crew), 3)
    if leftover_draws:
        left = [p for d in leftover_draws for p in draw_points(ccar, d)]
        lo, hi = bbox(left)
        out["donor_leftover_draws"] = {"draws": list(leftover_draws), "bbox": [lo, hi],
                                       "above_roof_m": round(hi[1] - roof_p99(body_car), 3)}
    hull = ccar.collision.convex_hull.representation_a.geometry_a.vertices
    out["hull_bbox_car_frame"] = bbox(hull)
    wheelbase = max(h[2] for h in hubs_c) - min(h[2] for h in hubs_c)
    out["hub_wheelbase"] = round(wheelbase, 3)
    out["body_length_over_wheelbase"] = round((out["body_bbox_car_frame"][1][2] - out["body_bbox_car_frame"][0][2]) / wheelbase, 3)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--donor-dir", type=Path, required=True)
    ap.add_argument("--candidate-dir", type=Path, required=True)
    ap.add_argument("--crew-draws", default="1,2,16,17,18,19,20")
    ap.add_argument("--leftover-draws", default="", help="donor draws kept in car.dx that are not crew (e.g. 0)")
    ap.add_argument("--label", default="candidate")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        ap.error("refusing to overwrite")
    ints = lambda s: tuple(int(x) for x in s.split(",") if x)
    report = diagnose(a.donor_dir, a.candidate_dir, ints(a.crew_draws), ints(a.leftover_draws), a.label)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
