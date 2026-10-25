"""V-MESH4: reproducible build of the stance-, arch- and glass-polished GT3-Impreza-on-Navara addon bundle.

Same J.3-A/J.3-B pipeline and the same confirmed ID27/T2 identity as V-MESH2/3 (addon.json is generated
identically); only the geometry/texture inputs change:

* ``vmesh_geometry`` (V-MESH4 options): analytic wheel-house cut + continuous liner (``vmesh_arch``), ride-height
  lift, translucent GT glazing -> donor glass draw, cabin shell kept inside the paint shell;
* a same-size DXT edit of ``windscreen32-tga`` (the donor glass texture) so the glass is a uniform dark tint with one
  alpha value instead of the donor's grey ramp (R4D.1 M2 confirmed that this texture's alpha drives glass blending).

Refuses to overwrite; hashes the retail EXE before/after; never writes game files.
Result is READY_FOR_HUMAN_RUNTIME, not runtime-qualified.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import vmesh_diagnose as diag  # noqa: E402
import vmesh_geometry as geo  # noqa: E402
import vmesh_preview as preview  # noqa: E402
from build_vmesh3_impreza_experimental import collision_fit, risk_summary  # noqa: E402
from build_vmesh_impreza_experimental import (  # noqa: E402
    ADDON_ID, FAMILY, PAINT_RGBA, RETAIL_EXE_SHA256, Runner, dump, flat_png, sha, sha_file)
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from vmesh_gt3_to_dx import classify, measure_axles, parse_gt_obj  # noqa: E402

DEFAULT_RIDE_LIFT = 0.12          # m; see research/vehicles/vmesh4/README.md ("Stance")
DEFAULT_GLASS_RGB = (60, 78, 96)  # texture RGB; the donor glass draw multiplies it by its vertex grey (~0.67)
DEFAULT_GLASS_ALPHA = 0.58
GLASS_TEXTURE = "windscreen32-tga.dxt"
PALETTE = {0: [0.95, 0.5, 0.1], 3: [0.15, 0.3, 0.9], 9: [0.05, 0.05, 0.05], 16: [0.9, 0.1, 0.1],
           25: [0.95, 0.95, 0.2], 24: [0.1, 0.9, 0.9], 35: [0.1, 0.9, 0.9]}


def make_previews(out: Path, donor_dir: Path, after_family: Path, before_family: Path | None, blender: str) -> dict:
    """Race/frontend previews (texture + role colours) and a before/after contact sheet; best effort."""
    pdir = out / "preview"
    pdir.mkdir(exist_ok=True)
    made = {}
    views = ["side", "q34", "front34"]
    after_tex = preview.render(after_family, donor_dir, pdir / "after", "texture", views, blender)
    after_role = preview.render(after_family, donor_dir, pdir / "after_role", "role", ["q34", "top"], blender,
                                colors=PALETTE, hide=[20, 21, 22, 23], which=("complete",))
    glass_open = (preview.render(after_family, donor_dir, pdir / "after_glass_hidden", "texture", ["q34", "side"], blender,
                                 hide=[35], which=("race",))
                  + preview.render(after_family, donor_dir, pdir / "after_glass_hidden", "texture", ["q34", "side"], blender,
                                   hide=[24], which=("complete",)))
    made["after"] = [str(p) for p in after_tex + after_role + glass_open]
    tiles = []
    if before_family is not None:
        before_tex = preview.render(before_family, donor_dir, pdir / "before", "texture", views, blender)
        made["before"] = [str(p) for p in before_tex]
        # rows: before race (side q34 front34), after race, before complete, after complete
        for which in ("race", "complete"):
            tiles += [p for p in before_tex if p.name.startswith(which)] + [p for p in after_tex if p.name.startswith(which)]
        made["sheet"] = str(preview.contact_sheet(tiles, pdir / "sheet_before_after.png", 3, blender))
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gt-dir", type=Path, required=True, help="GT3 sb0097 CarModelSet dump directory (private)")
    ap.add_argument("--retail-root", type=Path, required=True)
    ap.add_argument("--retail-exe", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True, help="new directory (must not exist)")
    ap.add_argument("--before-candidate-dir", type=Path, default=None, help="V-MESH3 family dir to diagnose/render as 'before'")
    ap.add_argument("--lod", default="lod1")
    ap.add_argument("--gt-wheel-radius", type=float, default=geo.DEFAULT_GT_WHEEL_RADIUS)
    ap.add_argument("--ride-lift", type=float, default=DEFAULT_RIDE_LIFT, help="m the GT body is raised relative to the wheels")
    ap.add_argument("--arch-gap", type=float, default=geo.ARCH_GAP)
    ap.add_argument("--arch-sides", type=int, default=geo.ARCH_SIDES)
    ap.add_argument("--glass-alpha", type=float, default=DEFAULT_GLASS_ALPHA)
    ap.add_argument("--glass-rgb", default=",".join(str(v) for v in DEFAULT_GLASS_RGB))
    ap.add_argument("--blender", default=None, help="Blender executable for the (optional) previews")
    ap.add_argument("--skip-launcher", action="store_true")
    args = ap.parse_args()
    out = args.output_root.resolve()
    if out.exists():
        ap.error("output root exists; refusing to overwrite")
    glass_rgb = tuple(int(v) for v in args.glass_rgb.split(","))
    glass_rgba = (*glass_rgb, max(0, min(255, round(args.glass_alpha * 255))))
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
    plan = geo.plan_fit(ctx, axles, args.gt_wheel_radius, lift=args.ride_lift)
    options = geo.BuildOptions(arch_gap=args.arch_gap, arch_sides=args.arch_sides)
    cand, reports = {}, {}
    for profile, name in (("car", "car.dx"), ("complete", "complete.dx")):
        data, rep = geo.build_candidate(obj, donor[name], ctx, plan, profile, options)
        (out / "dx" / name).write_bytes(data)
        cand[name], reports[name] = data, rep
        dump(out / "reports" / f"convert-{profile}.json", rep)
    wheel, wrep = geo.build_wheel_candidate(donor["wheel.dx"], plan.wheel_scale)
    (out / "dx" / "wheel.dx").write_bytes(wheel)
    cand["wheel.dx"] = wheel
    dump(out / "reports" / "convert-wheel.json", wrep)
    fit = collision_fit(donor["car.dx"], reports["car.dx"])
    (out / "tex" / "colour-tga.png").write_bytes(flat_png(16, 16, PAINT_RGBA))
    glass_src = donor_dir / GLASS_TEXTURE
    (out / "tex" / "windscreen32-tga.png").write_bytes(flat_png(32, 32, glass_rgba))

    # 2. addon project (identity identical to V-MESH2/3)
    project = out / "project"
    run.mrtool("addon", "init", "--name", "Impreza Rally Prototype", "--class", "T2", "--donor", "Navara",
               "--family", FAMILY, "--donor-source", donor_dir, "--output", project)
    addon = json.loads((project / "addon.json").read_text(encoding="utf-8"))
    addon["description"] = ("PRIVATE experimental V-MESH4: Navara-donor T2 addon with a GT3-derived Impreza body mesh "
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
                                               "png": "../tex/colour-tga.png"},
                            GLASS_TEXTURE: {"source_sha256": sha_file(glass_src), "png": "../tex/windscreen32-tga.png"}},
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
    if (rt_family / GLASS_TEXTURE).read_bytes() == glass_src.read_bytes():
        raise SystemExit(f"{GLASS_TEXTURE} in the runtime bundle is still the donor texture")
    glass_dxt = (rt_family / GLASS_TEXTURE).read_bytes()
    after = diag.diagnose(donor_dir, rt_family, (1, 2, 16, 17, 18, 19, 20), (), "V-MESH4")
    before = (diag.diagnose(donor_dir, args.before_candidate_dir, (1, 2, 16, 17, 18, 19, 20), (), "V-MESH3 v3-exp-001")
              if args.before_candidate_dir else None)
    exe_after = sha_file(args.retail_exe)
    previews = {}
    if args.blender:
        try:
            previews = make_previews(out, donor_dir, rt_family, args.before_candidate_dir, args.blender)
        except Exception as exc:                                    # previews are diagnostic only
            previews = {"error": repr(exc)}
    report = {
        "status": "READY_FOR_HUMAN_RUNTIME_NOT_RUNTIME_QUALIFIED",
        "inputs": {"gt_obj_sha256": sha_file(obj), "gt_lod0_sha256": sha_file(lod0),
                   "donor_sha256": {n: sha(b) for n, b in donor.items()},
                   "retail_exe_sha256_before": exe_before, "retail_exe_sha256_after": exe_after},
        "fit": {"scale": plan.scale, "wheel_scale": plan.wheel_scale, "gt_wheel_radius": plan.gt_wheel_radius,
                "ride_lift_m": plan.lift, "arch_gap_m": options.arch_gap, "arch_sides": options.arch_sides,
                "axles_gt": axles, "frame_dy": ctx.frame_dy, "donor_hubs_complete": [list(h) for h in ctx.hubs_complete],
                "donor_wheel_radius": ctx.wheel_radius, "collision": fit, "paint_rgba": list(PAINT_RGBA),
                "glass_rgba_texture": list(glass_rgba), "glass_dxt_sha256": sha(glass_dxt)},
        "candidates": {n: {"sha256": sha(b)} for n, b in cand.items()},
        "steps": {k: ({"status": v.get("status")} if isinstance(v, dict) and "status" in v else v) for k, v in steps.items()},
        "bundle": {"plan_sha256": json.loads((out / "runtime" / "runtime-artifact.json").read_text(encoding="utf-8")).get("addon_plan_sha256"),
                   "resource_index_sha256": steps["runtime_prepare"].get("resource_index_sha256"),
                   "resource_count": steps["runtime_prepare"].get("resource_count"),
                   "launcher_sha256": sha_file(launcher_exe) if launcher_exe else None},
        "diagnostics_after": after, "diagnostics_before": before, "risks": risk_summary(cand, reports),
        "converter_reports": {n: {k: reports[n][k] for k in ("options", "lift_m", "arch", "glazing", "cabin", "crew",
                                                             "tyre_hover_if_physical_radius_is_donor_m", "visual_tyre_radius",
                                                             "normal_vs_face_agreement", "replaced_draw_stats")}
                              for n in reports},
        "previews": previews,
        "retail_exe_unchanged": exe_before == exe_after == RETAIL_EXE_SHA256,
    }
    dump(out / "reports" / "validation-report.json", report)
    dump(out / "reports" / "private-asset-hashes.json", {"private_assets_not_in_archive": {
        "gt_obj_sha256": report["inputs"]["gt_obj_sha256"], **{n: sha(b) for n, b in cand.items()},
        "colour-tga.png": sha_file(out / "tex" / "colour-tga.png"),
        "windscreen32-tga.png": sha_file(out / "tex" / "windscreen32-tga.png"), "launcher_sha256": report["bundle"]["launcher_sha256"],
        "plan_sha256": report["bundle"]["plan_sha256"]}})

    # 5. review archive (no GT/derived DX/DXT/executables/previews)
    members = [(f"tools/{n}", ROOT / "tools" / n) for n in (
        "vmesh_gt3_to_dx.py", "vmesh_geometry.py", "vmesh_arch.py", "vmesh_diagnose.py", "vmesh_preview.py",
        "_vmesh_blender_render.py", "_vmesh_blender_sheet.py", "build_vmesh_impreza_experimental.py",
        "build_vmesh3_impreza_experimental.py", "build_vmesh4_impreza_experimental.py")]
    members += [(f"tests/synthetic/{n}", ROOT / "tests/synthetic" / n) for n in (
        "test_vmesh_gt3_to_dx.py", "test_vmesh_geometry.py", "test_vmesh_arch.py")]
    members += [("project/addon.json", project / "addon.json"), ("project/vehicle-project.json", project / "vehicle-project.json")]
    members += [(f"reports/{p.name}", p) for p in sorted((out / "reports").glob("*.json"))] + [("reports/commands.log", log)]
    for sub in ("vmesh", "vmesh3", "vmesh4"):
        for doc in sorted((ROOT / "research/vehicles" / sub).glob("*.md")):
            members.append((f"docs/{sub}/{doc.name}", doc))
    zpath = out / "review" / "vmesh4-review-archive.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in sorted(members):
            info = zipfile.ZipInfo(arc, (2026, 10, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, Path(src).read_bytes())
    print(json.dumps({"status": report["status"], "output_root": str(out), "retail_exe_unchanged": report["retail_exe_unchanged"],
                      **{n: sha(b) for n, b in cand.items()}, "glass_dxt_sha256": sha(glass_dxt),
                      "plan_sha256": report["bundle"]["plan_sha256"], "launcher_sha256": report["bundle"]["launcher_sha256"],
                      "review_archive": str(zpath), "review_archive_sha256": sha_file(zpath)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
