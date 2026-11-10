"""Loose-file runtime package for the five-race Invitation experiment (R5T-INV E1).

The game reads ``DataScene/...`` next to the EXE, so nothing is packed into
``Data.sma``. Without a course geometry writer, every new course reuses the
Retail stage models already in ``Data.sma``:

* InvFrance / InvItaly / InvSpain / InvTurkey: one scene with *several*
  ``landscape`` eggs (every stage model the stitched route uses). Stages of a
  country share one world frame, so the identity matrix lines them up.
* InvGrandFinal: one 6 km window per country. Each country's stage models get
  an ``en3d Matrix`` (yaw + translation) so the end of one window meets the
  start of the next with matching road height and heading; no void liaison.

Runtime unknowns this package tests: several landscape eggs in one scene, and
whether a non-identity landscape matrix moves render, collision and AI data
together. Retail scenes always have exactly one identity landscape egg.

Inputs: a finished ``tools/invitation_concept.py`` run. Output (ignored):
``research-output/invitation_concept/runtime5``.
"""
from __future__ import annotations

import argparse
import itertools
import copy
import json
import math
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import invitation_concept as concept  # noqa: E402
from master_rallye.course_atlas import (  # noqa: E402
    degenerate_shared_triangles, read_marker_list, resample_route, route_length, self_overlap_length)
from master_rallye.course_entry import (  # noqa: E402
    LIMIT_LISTS, _MIRRORED, RouteFrame, build_entry_racetest, replace_limit_lists, validated_limits)
from master_rallye.dx_course import parse_course_dx  # noqa: E402
from master_rallye.course_sfl_field import grid_for_route, synthesize_pursuit_field  # noqa: E402

ENTRIES = ("InvFrance", "InvItaly", "InvSpain", "InvTurkey", "InvGrandFinal")
STAGE_FOLDERS = {stem: folder for country in concept.COUNTRIES.values() for stem, folder in country.items()}


def stage_model(xml_path: Path) -> str:
    root = ET.parse(xml_path).getroot()
    for lst in root.iter("List"):
        if lst.get("Name") == "landscape":
            return lst.find("Egg").find("Value[@Name='en3d Model Name']").get("Value")
    raise ValueError(f"no landscape in {xml_path}")


def stage_hnt(racetest: Path, stem: str) -> list[str]:
    hnt = next(p for p in racetest.glob("*.hnt") if p.stem.lower() == stem.lower())
    return [line for line in hnt.read_text(encoding="latin-1").splitlines() if line.strip()]


def matrix_rows(yaw: float, pivot, origin) -> dict[str, str]:
    """Row-vector matrix for ``p' = R_y(yaw) (p - pivot) + origin`` (see concept.rigid)."""
    c, s = math.cos(yaw), math.sin(yaw)
    px, py, pz = pivot
    ox, oy, oz = origin
    tx = ox - c * px + s * pz
    tz = oz - s * px - c * pz
    f = lambda v: f"{v:.6f}"  # noqa: E731
    return {"Row0": f"{f(c)} 0.000000 {f(s)} 0.000000", "Row1": "0.000000 1.000000 0.000000 0.000000",
            "Row2": f"{f(-s)} 0.000000 {f(c)} 0.000000", "Row3": f"{f(tx)} {f(oy - py)} {f(tz)} 1.000000"}


def set_landscapes(xml_bytes: bytes, landscapes: list[tuple[str, dict[str, str] | None]]) -> bytes:
    root = ET.fromstring(xml_bytes)
    lst = next(l for l in root.iter("List") if l.get("Name") == "landscape")
    prototype = lst.find("Egg")
    tail = prototype.tail
    for egg in lst.findall("Egg"):
        lst.remove(egg)
    for model, rows in landscapes:
        egg = copy.deepcopy(prototype)
        egg.tail = tail
        egg.find("Value[@Name='en3d Model Name']").set("Value", model)
        if rows:
            matrix = egg.find("Value[@Name='en3d Matrix']")
            for key, value in rows.items():
                matrix.set(key, value)
        lst.append(egg)
    return ET.tostring(root, encoding="unicode").encode("utf-8")


def union_hnt(lines_per_stage: list[list[str]]) -> bytes:
    seen, out = set(), []
    for lines in lines_per_stage:
        for line in lines:
            key = line.strip().lower()
            if key not in seen:
                seen.add(key)
                out.append(line.rstrip())
    models = [l for l in out if l.lower().startswith("model")]
    return ("\r\n".join(models + [l for l in out if l not in models]) + "\r\n").encode("latin-1")


def stages_near(window, stage_lines: dict[str, list], radius: float = 15.0) -> list[str]:
    """Smallest greedy set of stages whose RaceLines cover the window's road."""
    probe = window[::3]
    covers = {}
    for name, line in stage_lines.items():
        pts = resample_route(line, 10.0)
        covers[name] = {k for k, p in enumerate(probe)
                        if min((p[0] - q[0]) ** 2 + (p[2] - q[2]) ** 2 for q in pts) <= radius * radius}
    left, used = set(range(len(probe))), []
    while left:
        name = max(covers, key=lambda n: len(covers[n] & left))
        if not covers[name] & left:
            break  # remaining samples are covered by no stage (should not happen for stitched routes)
        used.append(name)
        left -= covers[name]
    return used


def build_country_folder(course_root: Path, out_root: Path, country: str, stems: list[str]) -> tuple[str, list[str], list[str]]:
    """Copy the stage DX/TXT of ``stems`` and one shared DXT set into ``course/inv<country>``.

    Retail DX texture slots store bare names (``grass-tga``); the folder comes
    from the model path. One folder therefore makes every stage share one
    texture set and keeps the scene under the ~256-texture runtime limit
    (diag6/diag11). For names whose content differs between stages the first
    listed stage wins.
    """
    folder = f"inv{country.lower()}"
    target = out_root / "DataGx/Course" / folder
    target.mkdir(parents=True, exist_ok=True)
    models, textures = [], {}
    for stem in stems:
        source = course_root / STAGE_FOLDERS[stem]
        dx = next(source.glob("*.dx"))
        shutil.copyfile(dx, target / dx.name)
        for txt in source.glob("*.txt"):
            shutil.copyfile(txt, target / f"{dx.stem}.txt")
        models.append(f"course\\{folder}\\{dx.stem}")
        for dxt in sorted(source.glob("*.dxt")):
            key = dxt.stem.lower()
            if key not in textures:
                textures[key] = dxt
    for key, dxt in textures.items():
        shutil.copyfile(dxt, target / f"{key}.dxt")
    return folder, models, sorted(textures)


def dressing_zones(racetest: Path, stems: list[str], route, radius: float = 60.0, keep: float = 200.0):
    """Start/finish areas of the used Retail stages away from the new route's own start/finish."""
    zones = []
    ends = (route[0], route[-1])
    for stem in stems:
        root = ET.parse(racetest / f"{stem}.xml").getroot()
        for name in ("StartArea", "FinishArea"):
            points = [tuple(map(float, v.get("Value").split())) for lst in root.iter("List") if lst.get("Name") == name
                      for v in lst.iter("Value") if v.get("Name") == "Marker Pos"]
            if not points:
                continue
            cx, cz = sum(p[0] for p in points) / len(points), sum(p[2] for p in points) / len(points)
            if all(math.hypot(cx - e[0], cz - e[2]) > keep for e in ends):
                zones.append((cx, cz, radius))
    return zones


def hnt_for(folder_models: list[tuple[str, list[str], list[str]]]) -> bytes:
    lines = [f"Model\t[{model}]" for folder, models, _ in folder_models for model in models]
    lines += [f"Texture\t[course\\{folder}\\{texture}]" for folder, _, textures in folder_models for texture in textures]
    return ("\r\n".join(lines) + "\r\n").encode("latin-1")


def referenced_textures(dx_path: Path) -> set[str]:
    model = parse_course_dx(dx_path)
    return {slot.value.lower() for draw in model.physical_draws for slot in draw.texture_slots
            if slot.value.lower() != "null"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--retail", type=Path, default=ROOT.parent / "corpora/retail/Data.sma_unpacked")
    parser.add_argument("--concept", type=Path, default=ROOT / "research-output/invitation_concept")
    parser.add_argument("--output", type=Path, default=ROOT / "research-output/invitation_concept/runtime5")
    parser.add_argument("--final-countries", default="France,Italy,Spain",
                        help="countries in the Grand Final (all four exceed the texture limit)")
    args = parser.parse_args()
    racetest = args.retail / "DataScene/RaceTest"
    course_root = args.retail / "DataGx/Course"
    if args.output.exists():
        shutil.rmtree(args.output)
    scene_dir = args.output / "DataScene/RaceTest"
    icont_dir = args.output / "DataScene/ICont"
    scene_dir.mkdir(parents=True, exist_ok=True)
    icont_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {"entries": {}}
    windows, folders, country_limits, country_routes = [], {}, {}, {}

    for country in ("France", "Italy", "Spain", "Turkey"):
        entry = f"Inv{country}"
        saved = json.loads((args.concept / entry / f"{entry}_route.json").read_text(encoding="utf-8"))
        samples = [tuple(p) for p in saved["samples"]]
        legs = [leg["stage"] for leg in saved["route"]["legs"]]
        folder, models, textures = build_country_folder(course_root, args.output, country, legs)
        folders[country] = (folder, dict(zip(legs, models)))
        xml = (args.concept / entry / f"{entry}.xml").read_bytes()
        xml = set_landscapes(xml, [(m, None) for m in models])
        leg_sources = [(racetest / f"{leg['stage']}.xml", bool(leg["reversed"])) for leg in saved["route"]["legs"]]
        limits, limit_stats = validated_limits(samples, leg_sources)
        country_limits[country] = limits
        country_routes[country] = samples
        xml = replace_limit_lists(xml, limits)
        (scene_dir / f"{entry}.xml").write_bytes(xml)
        (scene_dir / f"{entry}.hnt").write_bytes(hnt_for([(folder, models, textures)]))
        shutil.copyfile(args.concept / entry / f"{entry.lower()}.sfl", icont_dir / f"{entry.lower()}.sfl")
        used = set().union(*(referenced_textures(next((course_root / STAGE_FOLDERS[s]).glob("*.dx"))) for s in legs))
        report["entries"][entry] = {"length": saved["route"]["length"], "landscapes": models, "limits": limit_stats,
                                    "folder_textures": len(textures), "referenced_textures": len(used)}
        if country in args.final_countries.split(","):
            stage_lines = {s: read_marker_list(racetest / f"{s}.xml", "RaceLine") for s in legs}
            window = concept.signature_window(samples, concept.FINAL_WINDOW)
            windows.append((country, window, stages_near(window, stage_lines), racetest / f"{legs[0]}.xml"))
        print(f"[{entry}] {saved['route']['length']:.0f} m, {len(models)} landscapes, "
              f"{len(used)} referenced / {len(textures)} folder textures", flush=True)

    # Hide triangles drawn twice by overlapping stage models (z-fighting).
    # Grand Final stages go first so the models it loads alone stay complete.
    final_stems = {country: stems for country, _, stems, _ in windows}
    for country, (folder, model_by_stage) in folders.items():
        order = final_stems.get(country, []) + [s for s in model_by_stage if s not in final_stems.get(country, [])]
        paths = [args.output / "DataGx/Course" / folder / (model_by_stage[s].split("\\")[-1] + ".dx") for s in order]
        dedupe = degenerate_shared_triangles(paths, hide_zones=dressing_zones(racetest, list(model_by_stage),
                                                                               country_routes[country]))
        report["entries"][f"Inv{country}"]["hidden_duplicate_triangles"] = dedupe
        print(f"[Inv{country}] hidden duplicates: " + ", ".join(f"{k} {v['hidden']}/{v['triangles']}" for k, v in dedupe.items()), flush=True)

    # Grand Final: direct end-to-start junctions (no liaison over the void).
    # The first window keeps its native frame; the others are placed by
    # landscape matrices (diag5: collision follows, ground textures did not).
    concept.LIAISON_LENGTH = 0.0
    count = len(windows)
    best = None
    for order in itertools.permutations(range(count)):
        for flips in itertools.product((False, True), repeat=count):
            trial = [(windows[i][0], list(reversed(windows[i][1])) if flip else windows[i][1])
                     for i, flip in zip(order, flips)]
            combined, transforms, _ = concept.layout_grand_final(trial, keep_first_in_place=True)
            clearances = [t["clearance_to_previous"] for t in transforms[1:]]
            score = (min(clearances) >= 2 * concept.CORRIDOR_RADIUS, min(clearances))
            if best is None or score > best[0]:
                best = (score, order, flips, combined, transforms)
    _, order, flips, combined, transforms = best
    flips_in_order = list(flips)
    windows = [(windows[i][0], list(reversed(windows[i][1])) if flip else windows[i][1], windows[i][2], windows[i][3])
               for i, flip in zip(order, flips)]
    print(f"[InvGrandFinal] order {[w[0] for w in windows]}, reversed {list(flips)}, "
          f"min clearance {best[0][1]:.0f}", flush=True)
    route = [combined[0]]
    for p in combined[1:]:
        if math.dist(p, route[-1]) > 0.5:
            route.append(p)
    landscapes, layout, used = [], [], set()
    hnt_parts = []
    gf_limits = {name: [] for name in LIMIT_LISTS}
    for (country, window, stems, _), tf, flipped in zip(windows, transforms, flips_in_order):
        window_frame = RouteFrame(window)
        for name in LIMIT_LISTS:
            source = _MIRRORED[name] if flipped else name
            for q in country_limits[country][source]:
                along, side, _, _, _ = window_frame.local(q)
                if -20.0 <= along <= window_frame.total + 20.0 and abs(side) <= 150.0:
                    gf_limits[name].append(concept.rigid([q], tf["pivot"], math.radians(tf["yaw_degrees"]), tf["origin"])[0])
    for (country, window, stems, _), tf in zip(windows, transforms):
        rows = matrix_rows(math.radians(tf["yaw_degrees"]), tf["pivot"], tf["origin"])
        identity = abs(tf["yaw_degrees"]) < 1e-9 and all(abs(a - b) < 1e-2 for a, b in zip(tf["pivot"], tf["origin"]))
        folder, model_by_stage = folders[country]
        models = [model_by_stage[s] for s in stems]
        refs = set()
        for stem in stems:
            refs |= referenced_textures(next((course_root / STAGE_FOLDERS[stem]).glob("*.dx")))
        landscapes += [(m, None if identity else rows) for m in models]
        hnt_parts.append((folder, models, sorted(refs)))
        used |= {f"{folder}/{t}" for t in refs}
        layout.append({**tf, "stages": stems, "identity": identity, "matrix": None if identity else rows})
    xml, xml_report = build_entry_racetest(windows[0][3], entry_name="InvGrandFinal",
                                           model_name="unused", route=route, source_xmls=[])
    xml = set_landscapes(xml, landscapes)
    gf_frame = RouteFrame(route)
    # Same side rule as transfer_limits: no marker on or across the driven road.
    side_ok = lambda name, q: gf_frame.local(q)[1] * (-1.0 if name.startswith("Left") else 1.0) >= 8.0  # noqa: E731
    xml = replace_limit_lists(xml, {name: sorted((q for q in points if side_ok(name, q)),
                                                 key=lambda q: gf_frame.local(q)[0])
                                    for name, points in gf_limits.items()})
    (scene_dir / "InvGrandFinal.xml").write_bytes(xml)
    (scene_dir / "InvGrandFinal.hnt").write_bytes(hnt_for(hnt_parts))
    samples = resample_route(route, 20.0)
    (icont_dir / "invgrandfinal.sfl").write_bytes(synthesize_pursuit_field(samples, grid_for_route(samples), lookahead=12.0))
    report["entries"]["InvGrandFinal"] = {
        "countries": [w[0] for w in windows], "length": round(route_length(route), 1),
        "self_overlap_length": round(self_overlap_length(route), 1), "landscapes": len(landscapes),
        "referenced_textures": len(used), "layout": layout, "racetest": xml_report,
    }
    print(f"[InvGrandFinal] {route_length(route):.0f} m, {len(landscapes)} landscapes, "
          f"{len(used)} referenced textures", flush=True)
    (args.output / "runtime5-report.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
