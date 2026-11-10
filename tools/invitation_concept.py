"""Build the Invitation new-entry concept package from the Retail corpus.

Outputs (ignored, default ``research-output/invitation_concept``):

* ``p0/``      stock scenes copied under the new entry names: proves the EXE
               entry retarget (tools/patch_invitation_entries.py) in runtime
               without new geometry.
* ``<Entry>/`` per new course: stitched route JSON/OBJ, corridor-cropped atlas
               OBJ for Blender, synthesized SFL heading field, generated
               RaceTest XML and HNT, and a budget report.
* ``concept-report.json`` with every number quoted in the docs.

Entries: InvFrance, InvItaly, InvSpain, InvTurkey (full-country routes through
each country's shared road network) and InvGrandFinal (one signature window of
each country placed in a single world and joined by authored liaison roads).

Original game files are read-only inputs. No compiled DX/tag100 is produced:
geometry must go through Blender -> source (GXM) -> Demo 9.10 cooker, which
still lacks a GXM writer (see docs/course-new-entries.md).
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.course_atlas import (  # noqa: E402
    AtlasStage,
    AtlasTriangle,
    build_country_atlas,
    crop_to_corridor,
    read_marker_list,
    resample_route,
    route_length,
    self_overlap_length,
    stitch_routes,
    clear_route_end,
    write_atlas_obj,
    write_route_obj,
)
from master_rallye.course_entry import build_entry_hnt, build_entry_racetest  # noqa: E402
from master_rallye.course_sfl_field import grid_for_route, synthesize_pursuit_field  # noqa: E402

COUNTRIES = {
    "France": {"France1": "France1", "France2": "France2", "FranceM": "France_M", "FranceS1": "France_S1",
               "FranceS2": "France_S2", "FranceW": "France_W"},
    "Italy": {"Italy1": "Italy1", "Italy2": "Italy2", "Italy3": "Italy3", "ItalyM1": "Italy_M1",
              "ItalyM2": "Italy_M2", "ItalyS1": "Italy_S1", "ItalyS2": "Italy_S2", "ItalyS3": "Italy_S3",
              "ItalyS4": "Italy_S4", "ItalyW1": "Italy_W1", "ItalyW2": "Italy_W2"},
    "Spain": {"Spain1": "Spain1", "Spain2": "Spain2", "SpainM": "Spain_M", "SpainS1": "Spain_S1",
              "SpainS2": "Spain_S2", "SpainW": "Spain_W"},
    "Turkey": {"Turkey1": "Turkey1", "Turkey2": "Turkey2", "Turkey3": "Turkey3", "TurkeyM": "Turkey_m",
               "TurkeyS1": "Turkey_s1", "TurkeyS2": "Turkey_s2", "TurkeyW": "Turkey_w"},
}
P0_SOURCES = {"InvFrance": "FranceM", "InvItaly": "ItalyS4", "InvTurkey": "TurkeyM"}
CORRIDOR_RADIUS = 300.0
FINAL_WINDOW = 6000.0
LIAISON_LENGTH = 600.0


def best_route(country: str, stages: list[AtlasStage], keep_clear: float = 10.0):
    best = None
    for first in stages:
        for reverse_first in (False, True):
            trial = [AtlasStage(s.name, s.dx_path, s.xml_path,
                                list(reversed(s.raceline)) if (reverse_first and s.name == first.name) else s.raceline)
                     for s in stages]
            route = stitch_routes(country, trial, first=first.name, keep_clear=keep_clear)
            score = route.length - 3.0 * self_overlap_length(route.samples)
            if best is None or score > best[0]:
                best = (score, route)
    return best[1]


def signature_window(samples, length):
    """Window of ``length`` with the most heading change plus elevation range."""
    pts = resample_route(samples, 10.0)
    n = max(2, int(length / 10.0))
    if len(pts) <= n:
        return pts
    turn = [0.0]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        h1 = math.atan2(b[2] - a[2], b[0] - a[0])
        h2 = math.atan2(c[2] - b[2], c[0] - b[0])
        turn.append(abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi))
    turn.append(0.0)
    best = None
    running = sum(turn[:n])
    for start in range(0, len(pts) - n):
        if start:
            running += turn[start + n - 1] - turn[start - 1]
        ys = [p[1] for p in pts[start:start + n]]
        score = running + (max(ys) - min(ys)) / 20.0
        if best is None or score > best[0]:
            best = (score, start)
    return pts[best[1]:best[1] + n]


def rigid(points, pivot, yaw, offset):
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for x, y, z in points:
        rx, rz = x - pivot[0], z - pivot[2]
        out.append((rx * c - rz * s + offset[0], y - pivot[1] + offset[1], rx * s + rz * c + offset[2]))
    return out


def heading(a, b):
    return math.atan2(b[2] - a[2], b[0] - a[0])


def hermite(p0, d0, p1, d1, count):
    out = []
    for k in range(1, count):
        t = k / count
        h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
        out.append(tuple(h00 * p0[i] + h10 * d0[i] + h01 * p1[i] + h11 * d1[i] for i in range(3)))
    return out


def _hash_points(points, cell):
    grid = {}
    for p in points:
        grid.setdefault((math.floor(p[0] / cell), math.floor(p[2] / cell)), []).append(p)
    return grid


def corridor_clearance(points, grid, cell):
    """Smallest X/Z distance from ``points`` to the hashed placed corridors."""
    best = math.inf
    for p in points:
        cx, cz = math.floor(p[0] / cell), math.floor(p[2] / cell)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for q in grid.get((cx + dx, cz + dz), ()):
                    best = min(best, math.hypot(p[0] - q[0], p[2] - q[2]))
    return best


def layout_grand_final(windows, keep_first_in_place=False):
    """Place country windows end-to-start, yawed to continue the previous heading.

    Each placement must keep ``2 * CORRIDOR_RADIUS`` clearance from every
    already placed corridor, except the liaison zone around its own start.
    Candidates sweep the yaw in 15 degree steps; the best-clearance one wins.
    """
    cell = 2 * CORRIDOR_RADIUS
    placed_points, transforms, combined, liaison_spans = [], [], [], []
    cursor = (0.0, 0.0, 0.0)
    yaw_out = 0.0
    if keep_first_in_place:
        # The first window keeps its native frame (identity matrix): its pivot
        # and origin coincide and the first yaw candidate (extra = 0) is zero.
        first = windows[0][1]
        cursor = tuple(first[0])
        yaw_out = heading(first[0], first[min(5, len(first) - 1)])
    for country, pts in windows:
        start_yaw = heading(pts[0], pts[min(5, len(pts) - 1)])
        grid = _hash_points(placed_points, cell)
        best = None
        for step in range(0, 24):
            extra = math.radians(15 * ((step + 1) // 2) * (1 if step % 2 else -1))
            if abs(extra) > math.radians(120):
                continue
            yaw = yaw_out - start_yaw + extra
            direction = (math.cos(yaw_out + extra / 2), 0.0, math.sin(yaw_out + extra / 2))
            origin = cursor if not placed_points else tuple(cursor[i] + direction[i] * LIAISON_LENGTH for i in range(3))
            moved = rigid(pts, pts[0], yaw, origin)
            # The liaison zone (first ~LIAISON_LENGTH of the new window) may be close to the previous end.
            skip = int(2 * CORRIDOR_RADIUS / 10.0)
            clearance = corridor_clearance(moved[skip::3], grid, cell) if placed_points else math.inf
            score = min(clearance, 4 * cell) - abs(math.degrees(extra))
            if best is None or score > best[0]:
                best = (score, yaw, origin, moved, clearance, math.degrees(extra))
        _, yaw, origin, moved, clearance, extra_deg = best
        if combined:
            a, b = combined[-1], moved[0]
            da = [combined[-1][i] - combined[-2][i] for i in range(3)]
            db = [moved[1][i] - moved[0][i] for i in range(3)]
            scale = LIAISON_LENGTH / max(1e-6, math.hypot(da[0], da[2]))
            scale_b = LIAISON_LENGTH / max(1e-6, math.hypot(db[0], db[2]))
            bridge = hermite(a, [c * scale for c in da], b, [c * scale_b for c in db], 25)
            liaison_spans.append({"after": transforms[-1]["country"], "before": country,
                                  "start_index": len(combined), "samples": len(bridge),
                                  "height_step": round(b[1] - a[1], 1), "turn_degrees": round(extra_deg, 1)})
            combined.extend(bridge)
        combined.extend(moved)
        placed_points.extend(moved[::3])
        transforms.append({"country": country, "pivot": pts[0], "yaw_degrees": round(math.degrees(yaw), 3),
                           "origin": [round(c, 3) for c in origin],
                           "clearance_to_previous": None if clearance == math.inf else round(clearance, 1),
                           "clearance_ok": clearance >= 2 * CORRIDOR_RADIUS})
        cursor = moved[-1]
        yaw_out = heading(moved[-2], moved[-1])
    return combined, transforms, liaison_spans


def transform_triangles(tris, pivot, yaw, origin):
    return [AtlasTriangle(tuple(rigid(t.positions, pivot, yaw, origin)), t.uvs, t.texture, t.stages) for t in tris]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--retail", type=Path, default=ROOT.parent / "corpora/retail/Data.sma_unpacked")
    parser.add_argument("--output", type=Path, default=ROOT / "research-output/invitation_concept")
    parser.add_argument("--textures", action="store_true", help="decode DXT textures to PNG for the OBJ atlases")
    parser.add_argument("--countries", default=",".join(COUNTRIES))
    parser.add_argument("--keep-clear", type=float, default=10.0,
                        help="stop a leg where it comes this close to earlier route (limits need clearance)")
    parser.add_argument("--final-only", action="store_true",
                        help="reuse <Entry>_route.json from a previous run and only rebuild InvGrandFinal")
    args = parser.parse_args()
    racetest = args.retail / "DataScene/RaceTest"
    course_root = args.retail / "DataGx/Course"
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    report: dict = {"corridor_radius": CORRIDOR_RADIUS, "entries": {}}

    # P0: retarget mechanism test using untouched stock scenes under new names.
    p0 = out / "p0/DataScene/RaceTest"
    p0.mkdir(parents=True, exist_ok=True)
    for entry, stock in P0_SOURCES.items():
        shutil.copyfile(racetest / f"{stock}.xml", p0 / f"{entry}.xml")
        hnt = next(p for p in racetest.glob("*.hnt") if p.stem.lower() == stock.lower())
        shutil.copyfile(hnt, p0 / f"{entry}.hnt")
    report["p0"] = P0_SOURCES

    windows = []
    for country in [c.strip() for c in args.countries.split(",") if c.strip()]:
        entry = f"Inv{country}"
        target = out / entry
        stages = []
        for stem, folder in COUNTRIES[country].items():
            dx = next((course_root / folder).glob("*.dx"))
            stages.append(AtlasStage(stem, dx, racetest / f"{stem}.xml", read_marker_list(racetest / f"{stem}.xml", "RaceLine")))
        route_json = target / f"{entry}_route.json"
        if args.final_only:
            saved = json.loads(route_json.read_text(encoding="utf-8"))
            route_dict = saved["route"]
            samples = [tuple(p) for p in saved["samples"]]
            used = [leg["stage"] for leg in route_dict["legs"]]
        else:
            print(f"[{entry}] stitching {len(stages)} stage routes", flush=True)
            route = best_route(country, stages, keep_clear=args.keep_clear)
            route_dict = route.to_dict()
            samples = clear_route_end(resample_route(route.samples, 20.0))  # finish clear of earlier route
            used = [leg.stage for leg in route.legs]
        print(f"[{entry}] building atlas", flush=True)
        atlas = build_country_atlas(country, stages)
        corridor = crop_to_corridor(atlas, samples, CORRIDOR_RADIUS)
        template = racetest / f"{used[0]}.xml"
        report["entries"][entry] = {
            "route": route_dict,
            "atlas": atlas.summary(),
            "corridor_triangles": len(corridor),
            "corridor_textures": len({t.texture for t in corridor}),
        }
        if not args.final_only:
            model_name = "course\\{0}\\{0}".format(entry.lower())
            write_atlas_obj(atlas.triangles, target / "atlas_full", stem=f"{entry}_full",
                            textures=atlas.texture_sources, decode_textures=args.textures)
            write_atlas_obj(corridor, target / "atlas_corridor", stem=f"{entry}_corridor",
                            textures=atlas.texture_sources, decode_textures=args.textures)
            write_route_obj({f"{entry}_route": samples, **{f"src_{s.name}": s.raceline for s in stages}},
                            target / f"{entry}_routes.obj")
            route_json.write_text(json.dumps(
                {"route": route_dict, "samples": [[round(c, 3) for c in p] for p in samples]}, indent=1), encoding="utf-8")
            print(f"[{entry}] SFL + RaceTest", flush=True)
            (target / f"{entry.lower()}.sfl").write_bytes(synthesize_pursuit_field(samples, grid_for_route(samples), lookahead=12.0))
            xml, xml_report = build_entry_racetest(template, entry_name=entry, model_name=model_name, route=samples,
                                                   source_xmls=[racetest / f"{s}.xml" for s in used])
            (target / f"{entry}.xml").write_bytes(xml)
            (target / f"{entry}.hnt").write_bytes(build_entry_hnt(model_name, sorted(
                "course\\{}\\{}".format(entry.lower(), t) for t in {tri.texture for tri in corridor} if t != "null")))
            report["entries"][entry]["racetest"] = xml_report
        print(f"[{entry}] route {route_dict['length']:.0f} m, corridor tris {len(corridor)}", flush=True)
        windows.append((country, signature_window(samples, FINAL_WINDOW), atlas, template))

    if len(windows) == 4:
        print("[InvGrandFinal] layout", flush=True)
        combined, transforms, liaisons = layout_grand_final([(c, w) for c, w, _, _ in windows])
        target = out / "InvGrandFinal"
        tris = []
        for (country, window, atlas, _), tf in zip(windows, transforms):
            local = crop_to_corridor(atlas, window, CORRIDOR_RADIUS)
            tris += transform_triangles(local, tuple(tf["pivot"]), math.radians(tf["yaw_degrees"]), tuple(tf["origin"]))
        write_atlas_obj(tris, target / "atlas_corridor", stem="InvGrandFinal_corridor",
                        textures={k: v for _, _, a, _ in windows for k, v in a.texture_sources.items()},
                        decode_textures=args.textures)
        write_route_obj({"InvGrandFinal_route": combined}, target / "InvGrandFinal_routes.obj")
        (target / "invgrandfinal.sfl").write_bytes(synthesize_pursuit_field(combined, grid_for_route(combined), lookahead=12.0))
        # Pace notes/cameras/sounds cannot be transferred across the rigid
        # country transforms yet; the scene keeps only route-derived data.
        xml, xml_report = build_entry_racetest(windows[0][3], entry_name="InvGrandFinal",
                                               model_name="course\\invgrandfinal\\invgrandfinal",
                                               route=combined, source_xmls=[])
        (target / "InvGrandFinal.xml").write_bytes(xml)
        (target / "InvGrandFinal_layout.json").write_text(json.dumps(
            {"transforms": transforms, "liaisons": liaisons, "length": round(route_length(combined), 1),
             "samples": [[round(c, 3) for c in p] for p in combined]}, indent=1), encoding="utf-8")
        report["entries"]["InvGrandFinal"] = {
            "length": round(route_length(combined), 1), "window_per_country": FINAL_WINDOW,
            "liaisons": liaisons, "transforms": transforms, "corridor_triangles": len(tris),
            "self_overlap_length": round(self_overlap_length(combined), 1),
            "racetest": xml_report,
        }
    (out / "concept-report.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
