"""V-MESH3: reproducible build of the frame- and wheel-corrected GT3-Impreza-on-Navara addon bundle.

Same J.3-A/J.3-B pipeline and the same confirmed ID27/T2 identity as V-MESH2 (addon.json is
generated identically); only the geometry pipeline changes (``vmesh_geometry.py``):
race/frontend frame offset, hub-anchored fit, scaled visual wheels, GT cabin shell in both
models, relocated crew, hull fit in the race frame, and measured before/after diagnostics.

Refuses to overwrite; hashes the retail EXE before/after; never writes game files.
Result is READY_FOR_HUMAN_RUNTIME, not runtime-qualified.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import vmesh_diagnose as diag  # noqa: E402
import vmesh_geometry as geo  # noqa: E402
from build_vmesh_impreza_experimental import (  # noqa: E402
    ADDON_ID, FAMILY, PAINT_RGBA, RETAIL_EXE_SHA256, Runner, dump, flat_png, sha, sha_file)
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from vmesh_gt3_to_dx import classify, measure_axles, parse_gt_obj  # noqa: E402


def collision_fit(donor_car: bytes, car_report: dict) -> dict:
    """Per-axis scale/translation moving the donor tag101 hull onto the GT body in the *race* frame.

    X/Z follow the body extents; the hull floor keeps the donor's height (donor hull floor sits at
    hub level), the top follows the body roof (p99, excluding antennas).
    """
    hull = parse_dx_bytes(donor_car).collision.convex_hull.representation_a.geometry_a.vertices
    lo = [min(p[i] for p in hull) for i in range(3)]
    hi = [max(p[i] for p in hull) for i in range(3)]
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    ext = car_report["body_extent"]
    b_lo, b_hi = list(ext["min"]), list(ext["max"])
    b_lo[1], b_hi[1] = lo[1], ext["roof_y_p99"]
    scale = [(b_hi[i] - b_lo[i]) / (hi[i] - lo[i]) for i in range(3)]
    new_min_y = c[1] - scale[1] * (c[1] - lo[1])
    trans = [0.0, lo[1] - new_min_y, (b_lo[2] + b_hi[2]) / 2 - c[2]]
    return {"hull_bbox": [lo, hi], "scale": [round(v, 4) for v in scale],
            "centre": [round(v, 4) for v in c], "translation": [round(v, 4) for v in trans],
            "target_bbox": [b_lo, b_hi]}


def risk_summary(cand: dict[str, bytes], reports: dict) -> dict:
    out = {}
    for name in ("car.dx", "complete.dx"):
        o = parse_dx_bytes(cand[name])
        rep = reports[name]
        rows = []
        for draw in o.physical_draws:
            if draw.draw_index in rep["filler_draws"]:
                rows.append({"draw": draw.draw_index, "tag": draw.tag, "group": draw.group_label,
                             "texture": draw.texture_slots[0].value, "alpha_flag": draw.flags_0x20[0]})
        out[name] = {"filler_draws": len(rows), "filler_alpha_blended": [r["draw"] for r in rows if r["alpha_flag"]],
                     "filler_group_members": [r["draw"] for r in rows if r["tag"] in (7, 8)],
                     "filler_point": rep["filler_point"], "max_vertices_in_one_draw": max(d.local_vertex_max + 1 for d in o.physical_draws),
                     "omitted_gt_faces": sum(rep["exclusion_breakdown"].values()), "omitted_gt_breakdown": rep["exclusion_breakdown"],
                     "relief": rep["relief"]}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gt-dir", type=Path, required=True, help="GT3 sb0097 CarModelSet dump directory (private)")
    ap.add_argument("--retail-root", type=Path, required=True)
    ap.add_argument("--retail-exe", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True, help="new directory (must not exist)")
    ap.add_argument("--before-candidate-dir", type=Path, default=None, help="V-MESH2 family dir to diagnose as 'before'")
    ap.add_argument("--lod", default="lod1")
    ap.add_argument("--gt-wheel-radius", type=float, default=geo.DEFAULT_GT_WHEEL_RADIUS)
    ap.add_argument("--skip-launcher", action="store_true")
    args = ap.parse_args()
    out = args.output_root.resolve()
    if out.exists():
        ap.error("output root exists; refusing to overwrite")
    for sub in ("dx", "tex", "reports", "review"):
        (out / sub).mkdir(parents=True)
    exe_before = sha_file(args.retail_exe)
    if exe_before != RETAIL_EXE_SHA256:
        raise SystemExit(f"retail executable hash mismatch: {exe_before}")
    log = out / "reports" / "commands.log"
    run = Runner(log)
    donor_dir = args.retail_root / "Data.sma_unpacked" / "DataGx" / "Vehicles" / "Navara"
    donor = {n: (donor_dir / n).read_bytes() for n in ("car.dx", "complete.dx", "wheel.dx")}
    obj, lod0 = args.gt_dir / f"model0.{args.lod}.obj", args.gt_dir / "model0.lod0.obj"

    # 1. geometry
    ctx = geo.make_context(donor["car.dx"], donor["complete.dx"], donor["wheel.dx"])
    ref = parse_gt_obj(lod0)
    axles = measure_axles(ref["positions"], [f for f in ref["faces"] if classify(f[0], f[1]) not in ("exclude", "interior")])
    plan = geo.plan_fit(ctx, axles, args.gt_wheel_radius)
    cand, reports = {}, {}
    for profile, name in (("car", "car.dx"), ("complete", "complete.dx")):
        data, rep = geo.build_candidate(obj, donor[name], ctx, plan, profile, geo.BuildOptions.v3())
        (out / "dx" / name).write_bytes(data)
        cand[name], reports[name] = data, rep
        dump(out / "reports" / f"convert-{profile}.json", rep)
    wheel, wrep = geo.build_wheel_candidate(donor["wheel.dx"], plan.wheel_scale)
    (out / "dx" / "wheel.dx").write_bytes(wheel)
    cand["wheel.dx"] = wheel
    dump(out / "reports" / "convert-wheel.json", wrep)
    fit = collision_fit(donor["car.dx"], reports["car.dx"])
    (out / "tex" / "colour-tga.png").write_bytes(flat_png(16, 16, PAINT_RGBA))

    # 2. addon project (identity identical to V-MESH2)
    project = out / "project"
    run.mrtool("addon", "init", "--name", "Impreza Rally Prototype", "--class", "T2", "--donor", "Navara",
               "--family", FAMILY, "--donor-source", donor_dir, "--output", project)
    addon = json.loads((project / "addon.json").read_text(encoding="utf-8"))
    addon["description"] = ("PRIVATE experimental V-MESH3: Navara-donor T2 addon with a GT3-derived Impreza body mesh "
                            "(private research sample; not for redistribution).")
    addon["frontend"].update(manufacturer="SUBARU", model="IMPREZA PROTOTYPE", combined="SUBARU IMPREZA PROTOTYPE")
    addon["race_colour_rgba"] = [0.05, 0.3, 0.9, 1.0]
    addon["results"]["display_name"] = "TEST DRIVER"
    dump(project / "addon.json", addon)
    vp = {"vehicle_name": "Navara", "source_vehicle_dir": str(donor_dir),
          "resources": {
              "car.dx": {"source_sha256": sha(donor["car.dx"]), "topology_candidate": "../dx/car.dx",
                         "collision_scale": fit["scale"], "collision_center": fit["centre"],
                         "collision_translation": fit["translation"]},
              "complete.dx": {"source_sha256": sha(donor["complete.dx"]), "topology_candidate": "../dx/complete.dx"},
              "wheel.dx": {"source_sha256": sha(donor["wheel.dx"]), "topology_candidate": "../dx/wheel.dx"}},
          "texture_edits": {"colour-tga.dxt": {"source_sha256": sha_file(donor_dir / "colour-tga.dxt"),
                                               "png": "../tex/colour-tga.png"}},
          "texture_replacements": {}}
    dump(project / "vehicle-project.json", vp)

    # 3. validate + author build + runtime bundle
    retail_args = ["--retail-data-sma", args.retail_root / "Data.sma", "--retail-data-root", args.retail_root / "Data.sma_unpacked"]
    steps = {}
    steps["validate_vehicle"] = run.mrtool("validate-vehicle", project / "vehicle-project.json")
    steps["project_validate"] = run.mrtool("addon", "project-validate", project, *retail_args)
    steps["project_build"] = run.mrtool("addon", "project-build", project, *retail_args, "--output", out / "author-build")
    steps["author_verify"] = run.mrtool("addon", "verify", out / "author-build")
    m1 = ROOT / "research/vehicles/sdk/examples/mercedes-ml320.json"
    common = ["--manifest", m1, "--manifest", project / "addon.json", "--project-build", f"{ADDON_ID}={out / 'author-build'}"]
    steps["runtime_prepare"] = run.mrtool("addon", "runtime-prepare", *common, "--output", out / "runtime")
    steps["runtime_verify"] = run.mrtool("addon", "runtime-verify", out / "runtime", *common)
    launcher_exe = None
    if not args.skip_launcher:
        steps["launcher_build"] = run.mrtool("addon", "runtime-launcher-build", out / "runtime", *common,
                                             "--launcher-output", out / "launcher")
        launcher_exe = out / "launcher" / "mr-runtime-launcher.exe"
        proc = subprocess.run([str(launcher_exe), "--verify", str(args.retail_exe), str(out / "runtime")], capture_output=True, text=True)
        steps["launcher_preflight"] = {"exit": proc.returncode, "output": proc.stdout.strip().splitlines()}
        if proc.returncode != 0:
            raise SystemExit("launcher preflight failed: " + proc.stdout + proc.stderr)

    # 4. independent checks, diagnostics (before/after), risks
    rt_family = out / "runtime" / "resource-root" / "DataGx" / "Vehicles" / FAMILY
    for n in ("car.dx", "complete.dx", "wheel.dx"):
        if (rt_family / n).read_bytes() == donor[n]:
            raise SystemExit(f"{n} in the runtime bundle is still the donor file")
    after = diag.diagnose(donor_dir, rt_family, (1, 2, 16, 17, 18, 19, 20), (), "V-MESH3")
    before = (diag.diagnose(donor_dir, args.before_candidate_dir, (1, 2, 16, 17, 18, 19, 20), (0,), "V-MESH2 exp-001")
              if args.before_candidate_dir else None)
    exe_after = sha_file(args.retail_exe)
    report = {
        "status": "READY_FOR_HUMAN_RUNTIME_NOT_RUNTIME_QUALIFIED",
        "inputs": {"gt_obj_sha256": sha_file(obj), "gt_lod0_sha256": sha_file(lod0),
                   "donor_sha256": {n: sha(b) for n, b in donor.items()},
                   "retail_exe_sha256_before": exe_before, "retail_exe_sha256_after": exe_after},
        "fit": {"scale": plan.scale, "wheel_scale": plan.wheel_scale, "gt_wheel_radius": plan.gt_wheel_radius,
                "axles_gt": axles, "frame_dy": ctx.frame_dy, "donor_hubs_complete": [list(h) for h in ctx.hubs_complete],
                "donor_wheel_radius": ctx.wheel_radius, "collision": fit, "paint_rgba": list(PAINT_RGBA)},
        "candidates": {n: {"sha256": sha(b)} for n, b in cand.items()},
        "steps": {k: ({"status": v.get("status")} if isinstance(v, dict) and "status" in v else v) for k, v in steps.items()},
        "bundle": {"plan_sha256": json.loads((out / "runtime" / "runtime-artifact.json").read_text(encoding="utf-8")).get("addon_plan_sha256"),
                   "resource_index_sha256": steps["runtime_prepare"].get("resource_index_sha256"),
                   "resource_count": steps["runtime_prepare"].get("resource_count"),
                   "launcher_sha256": sha_file(launcher_exe) if launcher_exe else None},
        "diagnostics_after": after, "diagnostics_before": before, "risks": risk_summary(cand, reports),
        "converter_reports": {n: {k: reports[n][k] for k in ("relief", "cabin", "crew", "tyre_hover_if_physical_radius_is_donor_m",
                                                             "visual_tyre_radius", "normal_vs_face_agreement", "replaced_draw_stats")}
                              for n in reports},
        "retail_exe_unchanged": exe_before == exe_after == RETAIL_EXE_SHA256,
    }
    dump(out / "reports" / "validation-report.json", report)
    dump(out / "reports" / "private-asset-hashes.json", {"private_assets_not_in_archive": {
        "gt_obj_sha256": report["inputs"]["gt_obj_sha256"], **{n: sha(b) for n, b in cand.items()},
        "colour-tga.png": sha_file(out / "tex" / "colour-tga.png"), "launcher_sha256": report["bundle"]["launcher_sha256"],
        "plan_sha256": report["bundle"]["plan_sha256"]}})

    # 5. review archive (no GT/derived DX/DXT/executables)
    members = [(f"tools/{n}", ROOT / "tools" / n) for n in (
        "vmesh_gt3_to_dx.py", "vmesh_geometry.py", "vmesh_diagnose.py", "build_vmesh_impreza_experimental.py",
        "build_vmesh3_impreza_experimental.py")]
    members += [(f"tests/synthetic/{n}", ROOT / "tests/synthetic" / n) for n in ("test_vmesh_gt3_to_dx.py", "test_vmesh_geometry.py")]
    members += [("project/addon.json", project / "addon.json"), ("project/vehicle-project.json", project / "vehicle-project.json")]
    members += [(f"reports/{p.name}", p) for p in sorted((out / "reports").glob("*.json"))] + [("reports/commands.log", log)]
    for sub in ("vmesh", "vmesh3"):
        for doc in sorted((ROOT / "research/vehicles" / sub).glob("*.md")):
            members.append((f"docs/{sub}/{doc.name}", doc))
    zpath = out / "review" / "vmesh3-review-archive.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in sorted(members):
            info = zipfile.ZipInfo(arc, (2026, 10, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, Path(src).read_bytes())
    print(json.dumps({"status": report["status"], "output_root": str(out), "retail_exe_unchanged": report["retail_exe_unchanged"],
                      **{n: sha(b) for n, b in cand.items()}, "plan_sha256": report["bundle"]["plan_sha256"],
                      "launcher_sha256": report["bundle"]["launcher_sha256"], "review_archive": str(zpath),
                      "review_archive_sha256": sha_file(zpath)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
