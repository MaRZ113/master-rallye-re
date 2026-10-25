"""V-MESH4.1: reproducible build of the LOD0-sourced GT3-Impreza-on-Navara addon bundle.

Same J.3-A/J.3-B pipeline, the same confirmed ID27/T2 identity, the same fit/stance/collision/glass-texture inputs as
V-MESH4 (kept untouched as the reference); what changes is the source geometry and how it is used:

* ``model0.lod0.obj`` is the primary source (its wheel arches, wheel houses, wing legs, mirrors and glazing are real
  geometry); nothing is cut, relieved, subdivided or reconstructed (``BuildOptions(arch="native")``);
* roles come from the content-driven ``vmesh_lod0.Lod0Classifier`` (texture alpha/luminance, object structure), not from
  LOD1 material names;
* the original per-corner UVs, normals indices, objects and materials of every emitted triangle are written to a private
  source map, and the source materials/textures to a material table, for the later material importer.  The game candidate
  still uses temporary donor materials (single-texel UVs, donor draws, paint/glass edits as in V-MESH4).

Refuses to overwrite; hashes the retail EXE before/after; never writes game files.
Result is READY_FOR_HUMAN_RUNTIME, not runtime-qualified.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import vmesh_diagnose as diag  # noqa: E402
import vmesh_geometry as geo  # noqa: E402
import vmesh_lod0 as lod0  # noqa: E402
import vmesh_preview as preview  # noqa: E402
from build_vmesh3_impreza_experimental import collision_fit, risk_summary  # noqa: E402
from build_vmesh4_impreza_experimental import (  # noqa: E402
    DEFAULT_GLASS_ALPHA, DEFAULT_GLASS_RGB, DEFAULT_RIDE_LIFT, GLASS_TEXTURE, PALETTE)
from build_vmesh_impreza_experimental import (  # noqa: E402
    ADDON_ID, FAMILY, PAINT_RGBA, RETAIL_EXE_SHA256, Runner, dump, flat_png, sha, sha_file)
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from vmesh_gt3_to_dx import classify, measure_axles, parse_gt_obj  # noqa: E402

BLENDER_OBJ_VIEWS = {"side": (90, 0, 0.62), "q34": (35, 14, 0.62), "top": (90, 89, 0.62)}


def _tri_area(t) -> float:
    a, b, c = (p[0] for p in t)
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return 0.5 * math.sqrt(sum(x * x for x in n))


def structural_stats(gt_dir: Path, lod: str, ctx, plan, axles) -> dict:
    """Structure of one GT LOD with the classification that applies to it (LOD1: V-MESH4 rules; LOD0: content-driven)."""
    gt = geo.parse_gt_full(gt_dir / f"model0.{lod}.obj")
    faces, textures = gt["faces"], gt["textures"]
    pos = {c[2][0] for _, _, t in faces for c in t}
    objects = sorted({o for o, _, _ in faces})
    materials = sorted({m for _, m, _ in faces})
    if lod == "lod0":
        cl = lod0.Lod0Classifier(faces, textures)
        role_of = lambda o, m: cl._decide(o, m)[0]
    else:
        glazing = geo.find_glazing_materials(faces, textures)

        def role_of(o, m):
            r = classify(o, m)
            if glazing and r == "black" and m in glazing:
                return "glass"
            if glazing and r == "glass":
                return "black"
            return r
    tp, _ = plan.transform(ctx, "complete")
    hubs = geo.hubs_in_frame(ctx, "complete")
    vis_r = plan.wheel_scale * ctx.wheel_radius
    roles, role_area, excl = {}, {}, {}
    arch_disc_area = 0.0
    arch_disc_tris = 0
    for o, m, t in faces:
        r = role_of(o, m)
        roles[r] = roles.get(r, 0) + 1
        a = _tri_area(t)
        role_area[r] = role_area.get(r, 0.0) + a * plan.scale ** 2
        if r == "exclude":
            key = "reflection" if "reflection" in o else "lit_lamp" if "_tail_lamp_on" in o else "untextured_shell"
            excl[key] = excl.get(key, 0) + 1
        if r in ("paint", "black"):
            c = tp(tuple(sum(p[0][i] for p in t) / 3 for i in range(3)))
            for hx, hy, hz in hubs:
                if c[0] * hx > 0 and abs(c[0]) > abs(hx) - 0.15 and math.hypot(c[1] - plan.lift - hy, c[2] - hz) < vis_r + 0.03:
                    arch_disc_tris += 1
                    arch_disc_area += a * plan.scale ** 2
                    break
    return {"lod": lod, "triangles": len(faces), "positions": len(pos), "objects": len(objects), "object_names": objects,
            "materials": len(materials), "textures_with_files": sum(1 for m in materials if m in textures),
            "faces_with_uv": sum(1 for _, _, t in faces if all(c[3] is not None for c in t)),
            "faces_with_normals": sum(1 for _, _, t in faces if all(c[1] is not None for c in t)),
            "roles_triangles": roles, "roles_area_m2": {k: round(v, 3) for k, v in sorted(role_area.items())},
            "excluded_by_reason": excl,
            "body_surface_inside_wheel_arch_discs_before_any_cut": {"triangles": arch_disc_tris, "area_m2": round(arch_disc_area, 3)}}


def render_raw_obj_sheet(gt_dir: Path, out: Path, blender: str) -> dict:
    """Grey-shaded renders of the raw LOD0/LOD1 OBJ (geometry only) and a 2x3 sheet."""
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for lod in ("lod1", "lod0"):
        cfg = {"objs": [str(gt_dir / f"model0.{lod}.obj")], "mode": "role", "out": str(out / lod),
               "views": {k: v for k, v in BLENDER_OBJ_VIEWS.items() if k != "top"}, "colors": {}, "hide": []}
        subprocess.run([blender, "-b", "--python", str(ROOT / "tools" / "_vmesh_blender_render.py"), "--", json.dumps(cfg)],
                       check=True, capture_output=True)
        made += [out / f"{lod}_{v}.png" for v in cfg["views"]]
    sheet = preview.contact_sheet(made, out / "sheet_lod1_vs_lod0.png", 2, blender)
    return {"images": [str(p) for p in made], "sheet": str(sheet)}


def make_previews(out: Path, donor_dir: Path, after_family: Path, before_family: Path, blender: str) -> dict:
    pdir = out / "preview"
    pdir.mkdir(exist_ok=True)
    views = ["side", "q34", "front34"]
    after_tex = preview.render(after_family, donor_dir, pdir / "after", "texture", views, blender)
    before_tex = preview.render(before_family, donor_dir, pdir / "before_vmesh4", "texture", views, blender)
    role = preview.render(after_family, donor_dir, pdir / "after_role", "role", ["q34", "top"], blender,
                          colors=PALETTE, hide=[20, 21, 22, 23], which=("complete",))
    open_glass = (preview.render(after_family, donor_dir, pdir / "after_glass_hidden", "texture", ["q34", "side"], blender,
                                 hide=[35], which=("race",))
                  + preview.render(after_family, donor_dir, pdir / "after_glass_hidden", "texture", ["q34", "side"], blender,
                                   hide=[24], which=("complete",)))
    tiles = []
    for which in ("race", "complete"):
        tiles += [p for p in before_tex if p.name.startswith(which)] + [p for p in after_tex if p.name.startswith(which)]
    sheet = preview.contact_sheet(tiles, pdir / "sheet_vmesh4_vs_vmesh41.png", 3, blender)
    return {"after": [str(p) for p in after_tex + role + open_glass], "before": [str(p) for p in before_tex], "sheet": str(sheet)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gt-dir", type=Path, required=True, help="GT3 sb0097 CarModelSet dump directory (private)")
    ap.add_argument("--retail-root", type=Path, required=True)
    ap.add_argument("--retail-exe", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True, help="new directory (must not exist)")
    ap.add_argument("--before-candidate-dir", type=Path, required=True, help="V-MESH4 family dir (reference, untouched)")
    ap.add_argument("--ride-lift", type=float, default=DEFAULT_RIDE_LIFT)
    ap.add_argument("--gt-wheel-radius", type=float, default=geo.DEFAULT_GT_WHEEL_RADIUS)
    ap.add_argument("--glass-alpha", type=float, default=DEFAULT_GLASS_ALPHA)
    ap.add_argument("--glass-rgb", default=",".join(str(v) for v in DEFAULT_GLASS_RGB))
    ap.add_argument("--blender", default=None, help="Blender executable for the (optional) previews")
    ap.add_argument("--skip-launcher", action="store_true")
    args = ap.parse_args()
    out = args.output_root.resolve()
    if out.exists():
        ap.error("output root exists; refusing to overwrite")
    glass_rgba = (*(int(v) for v in args.glass_rgb.split(",")), max(0, min(255, round(args.glass_alpha * 255))))
    for sub in ("dx", "tex", "reports", "review", "source-map"):
        (out / sub).mkdir(parents=True)
    exe_before = sha_file(args.retail_exe)
    if exe_before != RETAIL_EXE_SHA256:
        raise SystemExit(f"retail executable hash mismatch: {exe_before}")
    run = Runner(out / "reports" / "commands.log")
    donor_dir = args.retail_root / "Data.sma_unpacked" / "DataGx" / "Vehicles" / "Navara"
    donor = {n: (donor_dir / n).read_bytes() for n in ("car.dx", "complete.dx", "wheel.dx")}
    lod0_obj, lod1_obj = args.gt_dir / "model0.lod0.obj", args.gt_dir / "model0.lod1.obj"

    # 1. geometry (LOD0, native arches)
    ctx = geo.make_context(donor["car.dx"], donor["complete.dx"], donor["wheel.dx"])
    ref = parse_gt_obj(lod0_obj)
    axles = measure_axles(ref["positions"], [f for f in ref["faces"] if classify(f[0], f[1]) not in ("exclude", "interior")])
    plan = geo.plan_fit(ctx, axles, args.gt_wheel_radius, lift=args.ride_lift)
    gt = geo.parse_gt_full(lod0_obj)
    classifier = lod0.Lod0Classifier(gt["faces"], gt["textures"])
    overlay_keep = lod0.make_overlay_keep(gt["faces"], classifier)
    options = geo.BuildOptions(arch="native")
    cand, reports, maps, verify = {}, {}, {}, {}
    for profile, name in (("car", "car.dx"), ("complete", "complete.dx")):
        smap: list = []
        dropped: list = []
        data, rep = geo.build_candidate(lod0_obj, donor[name], ctx, plan, profile, options, classifier=classifier,
                                        overlay_keep=overlay_keep, source_map=smap, dropped_map=dropped)
        (out / "dx" / name).write_bytes(data)
        cand[name], reports[name], maps[name] = data, rep, smap
        tp, _ = plan.transform(ctx, profile)
        verify[name] = lod0.verify_source_map(data, smap, gt["faces"], tp)
        if verify[name]["mismatches"]:
            raise SystemExit(f"source map does not match {name}: {verify[name]}")
        dump(out / "reports" / f"convert-{profile}.json", rep)
        dump(out / "source-map" / f"source-map-{profile}.json", {"source": "model0.lod0.obj", "frame": profile, "records": smap})
        if profile == "car":
            dump(out / "source-map" / "dropped-overlays.json", {"source": "model0.lod0.obj", "records": dropped})
    materials = lod0.source_materials_table(gt["faces"], gt["textures"], classifier)
    dump(out / "source-map" / "source-materials.json", materials)
    dump(out / "source-map" / "source-classification.json", classifier.describe(gt["faces"]))
    wheel, wrep = geo.build_wheel_candidate(donor["wheel.dx"], plan.wheel_scale)
    (out / "dx" / "wheel.dx").write_bytes(wheel)
    cand["wheel.dx"] = wheel
    dump(out / "reports" / "convert-wheel.json", wrep)
    fit = collision_fit(donor["car.dx"], reports["car.dx"])
    (out / "tex" / "colour-tga.png").write_bytes(flat_png(16, 16, PAINT_RGBA))
    glass_src = donor_dir / GLASS_TEXTURE
    (out / "tex" / "windscreen32-tga.png").write_bytes(flat_png(32, 32, glass_rgba))
    lod_report = {"lod0": structural_stats(args.gt_dir, "lod0", ctx, plan, axles),
                  "lod1": structural_stats(args.gt_dir, "lod1", ctx, plan, axles),
                  "lod0_classification_reasons": sorted({f"{r['role']}: {r['reason']}" for r in classifier.describe(gt["faces"])}),
                  "overlay_policy": {"dropped_supported_decal_triangles": reports["car.dx"]["alpha_cutouts"].get("tris_dropped_overlay_or_invisible", 0),
                                     "kept_unsupported_overlay_triangles": reports["car.dx"]["alpha_cutouts"].get("overlay_tris_kept_unsupported_surface", 0)},
                  "glazing_materials": classifier.glazing, "head_lamp_objects": sorted(classifier.lamp_objects)}
    dump(out / "reports" / "lod-comparison.json", lod_report)

    # 2. addon project (identity identical to V-MESH2/3/4)
    project = out / "project"
    run.mrtool("addon", "init", "--name", "Impreza Rally Prototype", "--class", "T2", "--donor", "Navara",
               "--family", FAMILY, "--donor-source", donor_dir, "--output", project)
    addon = json.loads((project / "addon.json").read_text(encoding="utf-8"))
    addon["description"] = ("PRIVATE experimental V-MESH4.1: Navara-donor T2 addon with a GT3 LOD0-derived Impreza body mesh "
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
          "texture_edits": {"colour-tga.dxt": {"source_sha256": sha_file(donor_dir / "colour-tga.dxt"), "png": "../tex/colour-tga.png"},
                            GLASS_TEXTURE: {"source_sha256": sha_file(glass_src), "png": "../tex/windscreen32-tga.png"}},
          "texture_replacements": {}}
    dump(project / "vehicle-project.json", vp)

    # 3. validate + author build + runtime bundle + launcher
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
        help_text = subprocess.run([str(launcher_exe), "--help"], capture_output=True, text=True)
        has_env_check = "--verify-launch-environment" in (help_text.stdout + help_text.stderr)
        for label, flag in (("launcher_preflight", "--verify"), ("launcher_environment_check", "--verify-launch-environment")):
            if flag == "--verify-launch-environment" and not has_env_check:
                steps[label] = {"exit": None, "output": ["launcher has no --verify-launch-environment (proxy support absent)"]}
                raise SystemExit("launcher lacks proxy-compatibility support (--verify-launch-environment); source tree mismatch")
            proc = subprocess.run([str(launcher_exe), flag, str(args.retail_exe), str(out / "runtime")], capture_output=True, text=True)
            steps[label] = {"exit": proc.returncode, "output": proc.stdout.strip().splitlines()}
            if proc.returncode != 0:
                raise SystemExit(f"{label} failed: " + proc.stdout + proc.stderr)

    # 4. independent checks, diagnostics, previews
    rt_family = out / "runtime" / "resource-root" / "DataGx" / "Vehicles" / FAMILY
    for n in ("car.dx", "complete.dx", "wheel.dx"):
        if (rt_family / n).read_bytes() == donor[n]:
            raise SystemExit(f"{n} in the runtime bundle is still the donor file")
    if (rt_family / GLASS_TEXTURE).read_bytes() == glass_src.read_bytes():
        raise SystemExit(f"{GLASS_TEXTURE} in the runtime bundle is still the donor texture")
    glass_dxt = (rt_family / GLASS_TEXTURE).read_bytes()
    crew = (1, 2, 16, 17, 18, 19, 20)
    after = diag.diagnose(donor_dir, rt_family, crew, (), "V-MESH4.1")
    before = diag.diagnose(donor_dir, args.before_candidate_dir, crew, (), "V-MESH4 v4-exp-001")
    exe_after = sha_file(args.retail_exe)
    previews = {}
    if args.blender:
        try:
            previews = make_previews(out, donor_dir, rt_family, args.before_candidate_dir, args.blender)
            previews["raw_lod_sheet"] = render_raw_obj_sheet(args.gt_dir, out / "preview" / "raw_lods", args.blender)
        except Exception as exc:                                    # previews are diagnostic only
            previews = {"error": repr(exc)}
    report = {
        "status": "READY_FOR_HUMAN_RUNTIME_NOT_RUNTIME_QUALIFIED",
        "inputs": {"gt_lod0_sha256": sha_file(lod0_obj), "gt_lod1_sha256": sha_file(lod1_obj),
                   "donor_sha256": {n: sha(b) for n, b in donor.items()},
                   "retail_exe_sha256_before": exe_before, "retail_exe_sha256_after": exe_after},
        "fit": {"scale": plan.scale, "wheel_scale": plan.wheel_scale, "gt_wheel_radius": plan.gt_wheel_radius,
                "ride_lift_m": plan.lift, "arch": "native (source geometry, no cut)", "axles_gt": axles,
                "frame_dy": ctx.frame_dy, "donor_wheel_radius": ctx.wheel_radius, "collision": fit,
                "glass_rgba_texture": list(glass_rgba), "glass_dxt_sha256": sha(glass_dxt)},
        "candidates": {n: {"sha256": sha(b)} for n, b in cand.items()},
        "source_map_verification": verify,
        "steps": {k: ({"status": v.get("status")} if isinstance(v, dict) and "status" in v else v) for k, v in steps.items()},
        "bundle": {"plan_sha256": json.loads((out / "runtime" / "runtime-artifact.json").read_text(encoding="utf-8")).get("addon_plan_sha256"),
                   "resource_index_sha256": steps["runtime_prepare"].get("resource_index_sha256"),
                   "resource_count": steps["runtime_prepare"].get("resource_count"),
                   "launcher_sha256": sha_file(launcher_exe) if launcher_exe else None},
        "diagnostics_after": after, "diagnostics_before_vmesh4": before, "risks": risk_summary(cand, reports),
        "converter_reports": {n: {k: reports[n][k] for k in ("options", "lift_m", "arch", "alpha_cutouts", "gt_face_roles", "exclusion_breakdown",
                                                             "cabin", "crew", "normal_vs_face_agreement", "replaced_draw_stats")}
                              for n in reports},
        "lod_comparison": lod_report, "previews": previews,
        "retail_exe_unchanged": exe_before == exe_after == RETAIL_EXE_SHA256,
    }
    dump(out / "reports" / "validation-report.json", report)
    private = {"gt_lod0_sha256": report["inputs"]["gt_lod0_sha256"], **{n: sha(b) for n, b in cand.items()},
               "colour-tga.png": sha_file(out / "tex" / "colour-tga.png"),
               "windscreen32-tga.png": sha_file(out / "tex" / "windscreen32-tga.png"),
               "source-map-car.json": sha_file(out / "source-map" / "source-map-car.json"),
               "source-map-complete.json": sha_file(out / "source-map" / "source-map-complete.json"),
               "source-materials.json": sha_file(out / "source-map" / "source-materials.json"),
               "dropped-overlays.json": sha_file(out / "source-map" / "dropped-overlays.json"),
               "launcher_sha256": report["bundle"]["launcher_sha256"], "plan_sha256": report["bundle"]["plan_sha256"]}
    dump(out / "reports" / "private-asset-hashes.json", {"private_assets_not_in_archive": private})

    # 5. review archive (no GT/derived DX/DXT/source maps/executables/previews)
    members = [(f"tools/{n}", ROOT / "tools" / n) for n in (
        "vmesh_gt3_to_dx.py", "vmesh_geometry.py", "vmesh_arch.py", "vmesh_lod0.py", "vmesh_diagnose.py", "vmesh_preview.py",
        "_vmesh_blender_render.py", "_vmesh_blender_sheet.py", "build_vmesh_impreza_experimental.py",
        "build_vmesh3_impreza_experimental.py", "build_vmesh4_impreza_experimental.py", "build_vmesh41_impreza_experimental.py")]
    members += [(f"tests/synthetic/{n}", ROOT / "tests/synthetic" / n) for n in (
        "test_vmesh_gt3_to_dx.py", "test_vmesh_geometry.py", "test_vmesh_arch.py", "test_vmesh_lod0.py")]
    members += [("project/addon.json", project / "addon.json"), ("project/vehicle-project.json", project / "vehicle-project.json")]
    members += [(f"reports/{p.name}", p) for p in sorted((out / "reports").glob("*.json"))] + [("reports/commands.log", out / "reports" / "commands.log")]
    for sub in ("vmesh", "vmesh3", "vmesh4", "vmesh41"):
        for doc in sorted((ROOT / "research/vehicles" / sub).glob("*.md")):
            members.append((f"docs/{sub}/{doc.name}", doc))
    zpath = out / "review" / "vmesh41-review-archive.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in sorted(members):
            info = zipfile.ZipInfo(arc, (2026, 10, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, Path(src).read_bytes())
    print(json.dumps({"status": report["status"], "output_root": str(out), "retail_exe_unchanged": report["retail_exe_unchanged"],
                      **{n: sha(b) for n, b in cand.items()}, "glass_dxt_sha256": sha(glass_dxt),
                      "plan_sha256": report["bundle"]["plan_sha256"], "launcher_sha256": report["bundle"]["launcher_sha256"],
                      "source_map_verified": {n: v["verified_exact"] for n, v in verify.items()},
                      "review_archive": str(zpath), "review_archive_sha256": sha_file(zpath)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
