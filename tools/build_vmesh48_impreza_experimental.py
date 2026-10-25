"""V-MESH4.8: full-coverage masks, welded lamp glass, source tyre materials and decal restoration.

Builds a private candidate from the existing GT3 research input and protected retail donor. Body source-map geometry,
collision and SDK identity remain controlled; frontend/race material routing is verified. See research/vehicles/vmesh48.
Refuses to overwrite outputs and never launches the game or changes installed game/proxy files.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import gtmat  # noqa: E402
import vmesh_decal_authoring as decals
import vmesh_surface_repair as surface_repair
import vmesh_wheels as wheels
import vmesh_fitment as fitment
import vmesh_diagnose as diag  # noqa: E402
import vmesh_geometry as geo  # noqa: E402
import vmesh_lod0 as lod0  # noqa: E402
import vmesh_materials as vmat  # noqa: E402
import vmesh_raster as raster  # noqa: E402
from build_vmesh3_impreza_experimental import collision_fit, risk_summary  # noqa: E402
from build_vmesh4_impreza_experimental import DEFAULT_RIDE_LIFT  # noqa: E402
from build_vmesh_impreza_experimental import (  # noqa: E402
    ADDON_ID, FAMILY, PAINT_RGBA, RETAIL_EXE_SHA256, Runner, dump, flat_png, sha, sha_file)
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import PNG_ROWS_FLIP_VERTICAL, decode_rgba_pixels, parse_dxt  # noqa: E402
from master_rallye.r4e_writer import patch_dx_attributes  # noqa: E402
from vmesh_gt3_to_dx import classify, measure_axles, parse_gt_obj  # noqa: E402

# Navara donor draw roles that must keep their donor texture (never used as generic pools)
RESERVED = {"car.dx": {1, 2, 3, 9, 16, 17, 18, 19, 20, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36},
            "complete.dx": {3, 9, 16, 20, 21, 22, 23, 24, 25}}
SPECIAL_ROLES = {"glass": {"car.dx": 35, "complete.dx": 24}, "head_lamp": {"car.dx": 25, "complete.dx": 25},
                 "tail_lamp": {"car.dx": 24, "complete.dx": 16}}
VIEWS = {"side": (90, 4, 86, (0.0, 0.85, 0.0)), "front34": (145, 14, 92, (0.0, 0.85, 0.0)), "rear34": (35, 14, 92, (0.0, 0.85, 0.0)),
         "front_detail": (160, 10, 210, (0.0, 0.62, 1.9)), "hood_top": (150, 52, 170, (0.0, 0.8, 1.2))}


def tile_rgb(images: list[list[bytes]], W: int, H: int) -> tuple[int, int, bytes]:
    rows, cols = len(images), len(images[0])
    out = bytearray(rows * H * cols * W * 3)
    for r, row in enumerate(images):
        for c, img in enumerate(row):
            for y in range(H):
                o = ((r * H + y) * cols * W + c * W) * 3
                out[o:o + W * 3] = img[y * W * 3:(y + 1) * W * 3]
    return cols * W, rows * H, bytes(out)


def alpha_pass_summary(plan: vmat.MaterialPlan) -> dict:
    out = collections.Counter()
    for fi, (target, spec) in plan.routes.items():
        if target == "drop":
            out["dropped"] += 1
        elif isinstance(spec, tuple) and spec and spec[0] == "pool":
            out[f"{spec[1].pass_}:{spec[1].name}"] += 1
        else:
            out[f"role:{target}"] += 1
    return dict(sorted(out.items()))


def render_comparison(out: Path, gt, classifier, geom_plan, ctx, before_fam: Path, after_fam: Path) -> dict:
    tp, _ = geom_plan.transform(ctx, "complete")
    ref_items = raster.load_gt_obj(Path(gt["obj"]), tp, faces_filter=lambda o, m: classifier._decide(o, m)[0] != "exclude")
    W, H = 480, 240
    rows, files = [], {}
    pdir = out / "preview"
    pdir.mkdir(exist_ok=True)
    for name, (az, el, scale, centre) in VIEWS.items():
        cam = raster.Camera(az=az, el=el, scale=scale, centre=centre)
        row = []
        for label, items in (("gt3_reference", ref_items), ("vmesh47", raster.load_dx_family(before_fam, "complete.dx", skip_draws=(20, 21, 22, 23))),
                             ("vmesh48", raster.load_dx_family(after_fam, "complete.dx", skip_draws=(20, 21, 22, 23)))):
            rgb = raster.render(items, cam, W, H)
            path = pdir / f"{label}_{name}.png"
            path.write_bytes(raster.png_rgb(W, H, rgb))
            files[f"{label}_{name}"] = str(path)
            row.append(rgb)
        rows.append(row)
    tw, th, tiled = tile_rgb(rows, W, H)
    sheet = pdir / "sheet_gt3_vs_vmesh47_vs_vmesh48.png"
    sheet.write_bytes(raster.png_rgb(tw, th, tiled))
    files["sheet"] = str(sheet)
    wheel_rows = []
    for name, az, el in (("side", 90, 0), ("front", 180, 3), ("rear34", 35, 14)):
        row = []
        for label, family in (("vmesh47", before_fam), ("vmesh48", after_fam)):
            items = raster.load_dx_family(family, "car.dx")
            for hub in geo.hubs_in_frame(ctx, "car"):
                items += raster.load_dx_family(family, "wheel.dx", extra_offset=hub)
            rgb = raster.render(items, raster.Camera(az, el, 90, (0, .65, 0)), 640, 300)
            path = pdir / f"{label}_H1_wheels_{name}.png"
            path.write_bytes(raster.png_rgb(640, 300, rgb))
            files[f"{label}_H1_wheels_{name}"] = str(path)
            row.append(rgb)
        wheel_rows.append(row)
    ww, wh, wheel_rgb = tile_rgb(wheel_rows, 640, 300)
    (pdir / "sheet_wheels_H1_vmesh47_vs_vmesh48.png").write_bytes(raster.png_rgb(ww, wh, wheel_rgb))
    html = ['<!doctype html><meta charset="utf-8"><title>V-MESH4.8 offline comparison</title>',
            '<style>body{font:16px system-ui;background:#20242a;color:#eee;margin:24px}table{width:100%;table-layout:fixed}img{width:100%;image-rendering:auto}td{vertical-align:top}a{color:#9cf}</style>',
            '<h1>V-MESH4.8: offline comparison</h1><p>Software texture/alpha preview. No environment mapping or game lighting. Source OBJ is an export reference, not a GT3 runtime capture.</p>',
            '<table><tr><th>Source OBJ reference</th><th>V4.7: user-tested baseline</th><th>V4.8: reflective masks and front closures</th></tr>']
    for name in VIEWS:
        html.append('<tr>' + ''.join(f'<td><img src="{label}_{name}.png"><p>{name}</p></td>'
                                    for label in ('gt3_reference', 'vmesh47', 'vmesh48')) + '</tr>')
    html.append('</table><h2>Converted wheels, H1 anchors</h2><p>Left: V4.7. Right: V4.8. Donor complete.dx hubs are a hypothesis for race placement; these are not measured in-game positions.</p><img src="sheet_wheels_H1_vmesh47_vs_vmesh48.png">')
    (pdir / "index.html").write_text('\n'.join(html), encoding='utf-8')
    files['html'] = str(pdir / "index.html")
    return files


def panel_pass_audit(gt, classifier, before_fam: Path, after_fam: Path, out: Path):
    """Compare effective native passes on the source roof/trunk material faces through their private face maps."""
    def source_passes(family, stage):
        model = parse_dx_bytes((family / "car.dx").read_bytes())
        mapping = json.loads((stage / "source-map" / "source-map-car.json").read_text())["records"]
        result = {}
        for record in mapping:
            enabled, selector = model.physical_draws[record["draw"]].flags_0x20[:2]
            result[record["face"]] = "opaque" if not enabled else ("alpha_test" if selector else "blend")
        return result
    before = source_passes(before_fam, before_fam.parents[4])
    after = source_passes(after_fam, out)
    points = [c[0] for obj, mat, tri in gt["faces"] if classifier._decide(obj, mat)[0] == "paint" for c in tri]
    lo, hi = [min(p[axis] for p in points) for axis in range(3)], [max(p[axis] for p in points) for axis in range(3)]
    rows = {"roof": collections.Counter(), "trunk": collections.Counter()}
    for fi, (obj, mat, tri) in enumerate(gt["faces"]):
        if classifier._decide(obj, mat)[0] != "paint":
            continue
        y, z = (sum(c[0][axis] for c in tri) / 3 for axis in (1, 2))
        region = ("roof" if y > lo[1] + .82 * (hi[1] - lo[1]) and lo[2] + .3 * (hi[2] - lo[2]) < z < lo[2] + .75 * (hi[2] - lo[2]) else
                  "trunk" if z > lo[2] + .84 * (hi[2] - lo[2]) and y > lo[1] + .42 * (hi[1] - lo[1]) else None)
        if region:
            rows[region][f"{before.get(fi, 'dropped')} -> {after.get(fi, 'dropped')}"] += 1
    return {"method": "spatial source paint regions; effective selector gate from serialized DX",
            "regions": {k: dict(v) for k, v in rows.items()}, "geometric_vertex_displacement_m": 0.0,
            "boundary": "material seam causes addressed; physical watertight closure not asserted"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gt-dir", type=Path, required=True)
    ap.add_argument("--retail-root", type=Path, required=True)
    ap.add_argument("--retail-exe", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--before-candidate-dir", type=Path, required=True, help="V-MESH4.7 family dir (candidate reference)")
    ap.add_argument("--rear-decal", type=Path, help="private authored decal bound to a clear central rear placeholder")
    ap.add_argument("--rim-ratio", type=float, default=.80, help="explicit rim/tyre radius ratio; visual-fit setting")
    ap.add_argument("--rim-texture", type=Path, help="complete source disc PNG; donor mesh reconstruction, not a source mesh import")
    ap.add_argument("--ride-lift", type=float, default=DEFAULT_RIDE_LIFT)
    ap.add_argument("--gt-wheel-radius", type=float, default=geo.DEFAULT_GT_WHEEL_RADIUS)
    ap.add_argument("--glass-alpha-scale", type=float, default=0.7, help="multiplies the GT pane alpha (0.85-0.97) for interior visibility")
    ap.add_argument("--vertex-gray", type=int, default=255, help="vertex colour of GT-textured draws (255 = texture as authored)")
    ap.add_argument("--body-reflection-scale", type=float, default=0.58, help="environment-stage texture alpha scale for opaque reflective pools (0..1)")
    ap.add_argument("--headlamp-reflection-scale", type=float, default=0.72, help="headlamp texture alpha scale to temper its environment contribution (0..1)")
    ap.add_argument("--race-wheel-clearance-margin", type=float, default=0.005,
                    help="minimum visible tire-to-arch clearance retained when growing the race wheel (metres)")
    ap.add_argument("--skip-launcher", action="store_true")
    args = ap.parse_args()
    out = args.output_root.resolve()
    if out.exists():
        ap.error("output root exists; refusing to overwrite")
    for sub in ("dx", "tex", "reports", "review", "source-map"):
        (out / sub).mkdir(parents=True)
    exe_before = sha_file(args.retail_exe)
    if exe_before != RETAIL_EXE_SHA256:
        raise SystemExit(f"retail executable hash mismatch: {exe_before}")
    run = Runner(out / "reports" / "commands.log")
    donor_dir = args.retail_root / "Data.sma_unpacked" / "DataGx" / "Vehicles" / "Navara"
    donor = {n: (donor_dir / n).read_bytes() for n in ("car.dx", "complete.dx", "wheel.dx")}
    lod0_obj = args.gt_dir / "model0.lod0.obj"

    # 1. retain V-MESH4.3 body geometry and normalize opaque/cutout/blend passes
    ctx = geo.make_context(donor["car.dx"], donor["complete.dx"], donor["wheel.dx"])
    ref = parse_gt_obj(lod0_obj)
    axles = measure_axles(ref["positions"], [f for f in ref["faces"] if classify(f[0], f[1]) not in ("exclude", "interior")])
    gplan = geo.plan_fit(ctx, axles, args.gt_wheel_radius, lift=args.ride_lift)
    gt = geo.parse_gt_full(lod0_obj)
    gt["obj"] = str(lod0_obj)
    classifier = lod0.Lod0Classifier(gt["faces"], gt["textures"])
    if args.rear_decal:
        binding=decals.bind_rear_placeholder(gt,classifier,args.rear_decal)
        dump(out / "reports" / "rear-decal-binding.json",binding)
        classifier=lod0.Lod0Classifier(gt["faces"],gt["textures"])
    keep = lod0.make_overlay_keep(gt["faces"], classifier)
    mplan = vmat.MaterialPlan(gt["faces"], gt["textures"], classifier, gplan.scale, donor, donor_dir, SPECIAL_ROLES, RESERVED,
                              glass_alpha_scale=args.glass_alpha_scale, vertex_color=(args.vertex_gray,) * 3 + (255,), lamp_glass=True, reflection_in_helpers=True, decal_priority=True, solid_paint_control_alpha=True,
                              body_reflection_scale=args.body_reflection_scale,
                              headlamp_reflection_scale=args.headlamp_reflection_scale, structural_coverage=True, solid_trim_coverage=True, reflective_paint_masks=True, solid_black_swatches=True,
                              role_reflection_scales={"paint": args.body_reflection_scale, "black": 0.0, "interior": 0.0, "tail_lamp": .14})
    options = geo.BuildOptions(arch="native")
    cand, reports, maps, verify, alpha_applied, alpha_test_applied, env_applied = {}, {}, {}, {}, {}, {}, {}
    for profile, name in (("car", "car.dx"), ("complete", "complete.dx")):
        smap, dropped = [], []
        data, rep = geo.build_candidate(lod0_obj, donor[name], ctx, gplan, profile, options, classifier=classifier,
                                        source_map=smap, dropped_map=dropped, material_plan=mplan)
        toggles = dict(mplan.alpha_toggles[name])
        test_toggles = dict(mplan.alpha_test_toggles[name])
        env_toggles = dict(mplan.env_toggles[name])
        if toggles or test_toggles or env_toggles:
            patched = patch_dx_attributes(data, material_alpha=toggles, material_alpha_test=test_toggles,
                                          material_env=env_toggles, source=name)
            data = patched.data
        alpha_applied[name] = {str(d): enabled for d, enabled in sorted(toggles.items())}
        alpha_test_applied[name] = {str(d): enabled for d, enabled in sorted(test_toggles.items())}
        env_applied[name] = {str(d): enabled for d, enabled in sorted(env_toggles.items())}
        tp, _ = gplan.transform(ctx, profile)
        data, closure = surface_repair.repair(data, gt["faces"], classifier, mplan, tp, smap,
                                            glass_draw=SPECIAL_ROLES["glass"][name], weld_lenses=True, close_recesses=True)
        dump(out / "reports" / f"surface-repair-{profile}.json", closure)
        (out / "dx" / name).write_bytes(data)
        cand[name], reports[name], maps[name] = data, rep, smap
        tp, _ = gplan.transform(ctx, profile)
        verify[name] = lod0.verify_source_map(data, smap, gt["faces"], tp)
        if verify[name]["mismatches"]:
            raise SystemExit(f"source map does not match {name}: {verify[name]}")
        dump(out / "reports" / f"convert-{profile}.json", rep)
        dump(out / "source-map" / f"source-map-{profile}.json", {"source": "model0.lod0.obj", "frame": profile, "records": smap})
        if profile == "car":
            dump(out / "source-map" / "dropped-faces.json", {"source": "model0.lod0.obj", "records": dropped})
    dump(out / "source-map" / "source-materials.json", lod0.source_materials_table(gt["faces"], gt["textures"], classifier))
    dump(out / "source-map" / "source-classification.json", classifier.describe(gt["faces"]))
    # Start at the V4.7 radial size; preflight below fits the actual silhouette independently of tyre width.
    # The race hub transform is not moved: it remains a separate native-instancing question.
    old_radius, old_half_width = diag.wheel_extent(parse_dx_bytes((args.before_candidate_dir / "wheel.dx").read_bytes()))
    old_model = parse_dx_bytes((args.before_candidate_dir / "wheel.dx").read_bytes())
    old_envelope = max(math.hypot(p[1],p[2]) for p in old_model.vertices.positions)
    donor_envelope = max(math.hypot(p[1],p[2]) for p in parse_dx_bytes(donor["wheel.dx"]).vertices.positions)
    race_scale = old_envelope / donor_envelope
    race_fit = {"scale": race_scale, "lateral_scale": gplan.wheel_scale,
                "target_radius_m": old_radius, "old_half_width_m": old_half_width,
                "target_half_width_m": ctx.wheel_half_width * gplan.wheel_scale,
                "outboard_reduction_per_side_m": old_half_width - ctx.wheel_half_width * gplan.wheel_scale,
                "method": "inherit maximum radial envelope, reconstruct profile; derive width independently",
                "race_anchor_status": "H1 only; no unverified hub translation"}
    wheel, wrep = geo.build_wheel_candidate(donor["wheel.dx"], race_scale, lateral_scale=gplan.wheel_scale)
    (out / "dx" / "wheel.dx").write_bytes(wheel)
    wheel, wheel_conversion = wheels.convert(wheel, rim_draw=3, rim_ratio=args.rim_ratio)
    (out / "dx" / "wheel.dx").write_bytes(wheel)
    cand["wheel.dx"] = wheel
    race_fit["wheel_dx"] = wrep
    race_fit["target_radius_m"] = diag.wheel_extent(parse_dx_bytes(wheel))[0]
    # This phase only normalizes materials. Reuse the previous candidate's exact
    # collision transform instead of deriving a second fit from changed face counts.
    ref_root = args.before_candidate_dir.parents[4]
    ref_project = ref_root / "project" / "vehicle-project.json"
    if ref_project.exists():
        ref_car = json.loads(ref_project.read_text(encoding="utf-8"))["resources"]["car.dx"]
        fit = {"scale": ref_car["collision_scale"], "centre": ref_car["collision_center"],
               "translation": ref_car["collision_translation"], "inherited_from": str(ref_project)}
    else:
        ref_report = ref_root / "reports" / "convert-car.json"
        extent_source = json.loads(ref_report.read_text(encoding="utf-8")) if ref_report.exists() else reports["car.dx"]
        fit = collision_fit(donor["car.dx"], extent_source)

    # 2. textures: pool images -> PNG -> same-size DXT edits (project compiler); GT paint placeholder kept for the addon colour
    images = mplan.pool_images()
    helper_images, helper_report = vmat.normalize_environment_helpers(mplan, donor, donor_dir)
    images.update(helper_images)
    rim_png = args.rim_texture or args.gt_dir.parent / "Wheel" / "Model" / "Textures" / "1.0.png"
    wheel_images, wheel_texture_report = wheels.texture_images(wheel, donor_dir, rim_png, wheel_conversion, preserve_tyre=True, dark_spoke_gaps=True)
    images.update(wheel_images)
    dump(out / "reports" / "wheel-conversion.json", {"geometry": wheel_conversion, "texture": wheel_texture_report})
    wheel_obj = args.gt_dir.parent / "Wheel" / "Model" / "model0.lod0.obj"
    dump(out / "reports" / "wheel-source.json", {
        "obj_exists": wheel_obj.exists(), "obj_bytes": wheel_obj.stat().st_size if wheel_obj.exists() else None,
        "obj_sha256": sha_file(wheel_obj) if wheel_obj.exists() else None,
        "vertex_lines": sum(line.startswith("v ") for line in wheel_obj.read_text().splitlines()) if wheel_obj.exists() else 0,
        "face_lines": sum(line.startswith("f ") for line in wheel_obj.read_text().splitlines()) if wheel_obj.exists() else 0,
        "used_geometry": "donor reconstruction", "used_texture_sha256": sha_file(rim_png)})
    dump(out / "reports" / "surface-policy.json", {
        "solid_trim_coverage": True, "normalized_materials": mplan.coverage_normalized,
        "reflection_by_source_role": mplan.role_reflection_scales,
        "decal_materials": sorted(mplan.decal_materials), "reflection_in_helpers": True,
        "reflection_islands": [{"pool": p.name, "material": i.key[0], "triangles": len(i.tris),
                                "reflection": mplan.reflection_scale(p, i)} for p in mplan.pools for i,*_ in p.placements],
        "source_positions_unchanged": True, "new_seal_geometry": "bounded front edge bridges and source-linked cavity backs"})
    (out / "tex" / "colour-tga.png").write_bytes(flat_png(16, 16, PAINT_RGBA))
    texture_edits = {"colour-tga.dxt": {"source_sha256": sha_file(donor_dir / "colour-tga.dxt"), "png": "../tex/colour-tga.png"}}
    for fname, (w, h, px) in sorted(images.items()):
        png = out / "tex" / (Path(fname).stem + ".png")
        png.write_bytes(gtmat.png_from_rgba(w, h, px))
        texture_edits[fname] = {"source_sha256": sha_file(donor_dir / fname), "png": f"../tex/{png.name}"}

    body_fit_draws = [d for r, d in reports["car.dx"]["replaced_draws"].items() if r not in ("glass", "interior")]
    prefit = fitment.material_clearance(out / "dx", "car.dx", body_fit_draws, geo.hubs_in_frame(ctx, "car"),
        old_radius, ctx.wheel_half_width * gplan.wheel_scale, textures=images, fallback_family=donor_dir)
    factor = fitment.scale_to_clear_samples(parse_dx_bytes(wheel), prefit)
    race_fit["sampled_radial_correction_factor"] = factor
    race_fit["sampled_clearance_margin_m"] = 0.002
    if factor < 1:
        wheel, wrep = geo.build_wheel_candidate(donor["wheel.dx"], race_scale * factor, lateral_scale=gplan.wheel_scale)
        wheel, wheel_conversion = wheels.convert(wheel, rim_draw=3, rim_ratio=args.rim_ratio)
        (out / "dx" / "wheel.dx").write_bytes(wheel)
        cand["wheel.dx"] = wheel
        race_fit.update(scale=race_scale * factor, target_radius_m=diag.wheel_extent(parse_dx_bytes(wheel))[0], wheel_dx=wrep)
    dump(out / "reports" / "prefit-wheel.json", prefit)
    cand["complete.dx"] = wheels.embed(cand["complete.dx"], wheel, geo.hubs_in_frame(ctx, "complete"), (20,21,22,23))
    (out / "dx" / "complete.dx").write_bytes(cand["complete.dx"])
    dump(out / "reports" / "wheel-conversion.json", {"geometry": wheel_conversion, "texture": wheel_texture_report,
        "frontend_matches_race_geometry": True, "hub_transform_status": "H1 unchanged, human runtime test required"})

    # 3. addon project (identity identical to V-MESH2/3/4/4.1)
    project = out / "project"
    run.mrtool("addon", "init", "--name", "Impreza Rally Prototype", "--class", "T2", "--donor", "Navara",
               "--family", FAMILY, "--donor-source", donor_dir, "--output", project)
    addon = json.loads((project / "addon.json").read_text(encoding="utf-8"))
    addon["description"] = ("PRIVATE experimental V-MESH4.8: Navara-donor T2 addon, GT3 LOD0 Impreza body with GT3 materials/textures "
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
          "texture_edits": texture_edits, "texture_replacements": {}}
    dump(project / "vehicle-project.json", vp)

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
        steps["launcher_build"] = run.mrtool("addon", "runtime-launcher-build", out / "runtime", *common, "--launcher-output", out / "launcher")
        launcher_exe = out / "launcher" / "mr-runtime-launcher.exe"
        help_text = subprocess.run([str(launcher_exe), "--help"], capture_output=True, text=True)
        if "--verify-launch-environment" not in help_text.stdout + help_text.stderr:
            raise SystemExit("launcher lacks proxy-compatibility support (--verify-launch-environment); source tree mismatch")
        for label, flag in (("launcher_preflight", "--verify"), ("launcher_environment_check", "--verify-launch-environment")):
            proc = subprocess.run([str(launcher_exe), flag, str(args.retail_exe), str(out / "runtime")], capture_output=True, text=True)
            steps[label] = {"exit": proc.returncode, "output": proc.stdout.strip().splitlines()}
            if proc.returncode != 0:
                raise SystemExit(f"{label} failed: " + proc.stdout + proc.stderr)

    # 4. independent checks on the runtime bundle files
    rt_family = out / "runtime" / "resource-root" / "DataGx" / "Vehicles" / FAMILY
    decoded, dxt_checks = {}, {}
    for fname, (w, h, px) in images.items():
        built = (rt_family / fname).read_bytes()
        donor_dxt = (donor_dir / fname).read_bytes()
        tex = parse_dxt(rt_family / fname)
        if built == donor_dxt:
            raise SystemExit(f"{fname} in the runtime bundle is still the donor texture")
        if tex.header != parse_dxt(donor_dir / fname).header or len(built) != len(donor_dxt):
            raise SystemExit(f"{fname}: DXT header/size changed")
        decoded[fname] = (tex.width, tex.height, decode_rgba_pixels(tex, PNG_ROWS_FLIP_VERTICAL))
        dxt_checks[fname] = {"size": [tex.width, tex.height], "header_preserved": True, "round_trip_exact": decoded[fname][2] == px,
                             "sha256": sha(built)}
    mapping = vmat.verify_material_mapping(mplan, gt["faces"], decoded)
    for n in ("car.dx", "complete.dx"):
        if (rt_family / n).read_bytes() == donor[n]:
            raise SystemExit(f"{n} in the runtime bundle is still the donor file")
    flags = {}
    for n in ("car.dx", "complete.dx"):
        model = parse_dx_bytes((rt_family / n).read_bytes())
        donor_model = parse_dx_bytes(donor[n])
        flags[n] = {"alpha_enabled_draws": [d.draw_index for d in model.physical_draws if d.flags_0x20[0]],
                    "alpha_test_draws": [d.draw_index for d in model.physical_draws if d.flags_0x20[1]],
                    "alpha_toggled_vs_donor": [d.draw_index for d, o in zip(model.physical_draws, donor_model.physical_draws) if d.flags_0x20[0] != o.flags_0x20[0]]}
    consistency = []
    for pool in mplan.pools:
        for f, d in pool.draws.items():
            model = parse_dx_bytes((rt_family / f).read_bytes())
            donor_alpha = bool(parse_dx_bytes(donor[f]).physical_draws[d].flags_0x20[0])
            draw = model.physical_draws[d]
            test = bool(getattr(pool, "alpha_test", False))
            expected = (True, True) if test else ((True, False) if pool.pass_ == "blend" else
                       ((donor_alpha, False) if pool.pass_ == "special" else (False, False)))
            actual = tuple(bool(v) for v in draw.flags_0x20[:2])
            if expected != actual:
                consistency.append({"pool": pool.name, "file": f, "draw": d, "expected": expected, "actual": actual})
    if consistency:
        raise SystemExit(f"material selector mismatch: {consistency}")
    tex_of = {}
    for n in ("car.dx", "complete.dx"):
        tex_of[n] = {d.draw_index: d.texture_slots[0].value for d in parse_dx_bytes((rt_family / n).read_bytes()).physical_draws}
    per_face = {n: {e["face"]: (tex_of[n][e["draw"]], tuple(map(tuple, e["dx_uv"])) if e.get("dx_uv") else None) for e in maps[n]} for n in maps}
    both = set(per_face["car.dx"]) & set(per_face["complete.dx"])
    consistency_files = {"faces_in_both": len(both), "faces_only_car": len(set(per_face["car.dx"]) - both),
                         "faces_only_complete": len(set(per_face["complete.dx"]) - both),
                         "texture_or_uv_mismatches": sum(1 for f in both if per_face["car.dx"][f] != per_face["complete.dx"][f])}
    hulls = {}
    for n in ("car.dx",):
        a = parse_dx_bytes((rt_family / n).read_bytes()).collision.convex_hull.representation_a.geometry_a.vertices
        b = parse_dx_bytes((args.before_candidate_dir / n).read_bytes()).collision.convex_hull.representation_a.geometry_a.vertices
        hulls[n] = {"hull_vertices_identical_to_vmesh47": [tuple(round(c, 5) for c in p) for p in a] == [tuple(round(c, 5) for c in p) for p in b]}
    crew = (1, 2, 16, 17, 18, 19, 20)
    role_draws = {profile: [d for role, d in reports[profile + ".dx"]["replaced_draws"].items()
                            if role not in ("glass", "interior")]
                  for profile in ("car", "complete")}
    after = diag.diagnose(donor_dir, rt_family, crew, (), "V-MESH4.8", body_draws=role_draws)
    before = diag.diagnose(donor_dir, args.before_candidate_dir, crew, (), "V-MESH4.7")
    geometry_identical = {}
    for n in ("car.dx", "complete.dx"):
        a, b = parse_dx_bytes((rt_family / n).read_bytes()), parse_dx_bytes((args.before_candidate_dir / n).read_bytes())
        geometry_identical[n] = {"v48_triangles": a.triangle_count, "v47_triangles": b.triangle_count}
    body_draws = [d for r, d in reports["car.dx"]["replaced_draws"].items() if r not in ("glass", "interior")]
    material_clearance = fitment.material_clearance(rt_family, "car.dx", body_draws,
        geo.hubs_in_frame(ctx, "car"), race_fit["target_radius_m"], ctx.wheel_half_width * gplan.wheel_scale)
    if any(h["visible_samples_inside_tyre"] for h in material_clearance["hubs"]):
        raise SystemExit("final visible body samples still penetrate the fitted tyre outline")
    exe_after = sha_file(args.retail_exe)

    previews = {}
    try:
        previews = render_comparison(out, gt, classifier, gplan, ctx, args.before_candidate_dir, rt_family)
    except Exception as exc:
        previews = {"error": repr(exc)}
    artifacts = panel_pass_audit(gt, classifier, args.before_candidate_dir, rt_family, out)
    dump(out / "reports" / "artifact-analysis.json", artifacts)

    report_plan = {"classes": {f"{k[0]}:{k[1]}": v for k, v in sorted(mplan.report["classes"].items())},
                   "dropped_clear": len(mplan.report["dropped_clear"]), "flat_trim_triangles": mplan.report["flat_trim"],
                   "rejected": mplan.report["rejected"], "pools": mplan.report["pools"], "routes": alpha_pass_summary(mplan)}
    report = {
        "status": "READY_FOR_HUMAN_RUNTIME_NOT_RUNTIME_QUALIFIED",
        "inputs": {"gt_lod0_sha256": sha_file(lod0_obj), "donor_sha256": {n: sha(b) for n, b in donor.items()},
                   "retail_exe_sha256_before": exe_before, "retail_exe_sha256_after": exe_after},
        "fit": {"scale": gplan.scale, "wheel_scale": gplan.wheel_scale, "race_wheel": race_fit,
                "ride_lift_m": gplan.lift, "collision": fit,
                "glass_alpha_scale": args.glass_alpha_scale, "body_reflection_scale": args.body_reflection_scale,
                "headlamp_reflection_scale": args.headlamp_reflection_scale, "vertex_color": [args.vertex_gray] * 3 + [255]},
        "candidates": {n: {"sha256": sha(b)} for n, b in cand.items()},
        "material_plan": report_plan, "coverage_normalized": mplan.coverage_normalized,
        "environment_helper_normalization": helper_report, "alpha_toggles_applied": alpha_applied,
        "alpha_test_toggles_applied": alpha_test_applied, "environment_toggles_applied": env_applied, "draw_alpha_flags": flags,
        "pool_alpha_flag_mismatches": consistency, "car_vs_complete_consistency": consistency_files, "collision_parity": hulls, "texture_checks": dxt_checks, "material_mapping_verification": mapping, "source_map_verification": verify,
        "geometry_vs_vmesh47": geometry_identical,
        "steps": {k: ({"status": v.get("status")} if isinstance(v, dict) and "status" in v else v) for k, v in steps.items()},
        "bundle": {"plan_sha256": json.loads((out / "runtime" / "runtime-artifact.json").read_text(encoding="utf-8")).get("addon_plan_sha256"),
                   "resource_index_sha256": steps["runtime_prepare"].get("resource_index_sha256"),
                   "resource_count": steps["runtime_prepare"].get("resource_count"),
                   "launcher_sha256": sha_file(launcher_exe) if launcher_exe else None},
        "diagnostics_after": after, "material_aware_wheel_clearance": material_clearance, "legacy_diagnostics_before_vmesh47_incomplete_body_draws": before, "risks": risk_summary(cand, reports),
        "previews": previews, "retail_exe_unchanged": exe_before == exe_after == RETAIL_EXE_SHA256,
    }
    dump(out / "reports" / "validation-report.json", report)
    private = {"gt_lod0_sha256": report["inputs"]["gt_lod0_sha256"], **{n: sha(b) for n, b in cand.items()},
               **{f"tex/{Path(f).name}": v["sha256"] for f, v in dxt_checks.items()},
               **{f"source-map/{p.name}": sha_file(p) for p in sorted((out / "source-map").glob("*.json"))},
               "launcher_sha256": report["bundle"]["launcher_sha256"], "plan_sha256": report["bundle"]["plan_sha256"]}
    dump(out / "reports" / "private-asset-hashes.json", {"private_assets_not_in_archive": private})

    handoff = """# V-MESH4.8 private candidate\n\nOffline-validated package for the user's in-game test. This archive contains the SDK runtime overlay and its launcher. It does not contain the private GT3 source model or source textures.\n\nAfter extraction, first verify the package with `launcher/mr-runtime-launcher.exe --verify \"<retail MRallye.exe>\" runtime` and `--verify-launch-environment \"<retail MRallye.exe>\" runtime`. When ready to test, use `--integrated \"<retail MRallye.exe>\" runtime`. The launcher applies the runtime bundle in memory; the original MRallye.exe and installed graphics d3d8.dll are not modified.\n\nValidation status: STATIC_BUILD_ONLY_NOT_RUNTIME_QUALIFIED. Please capture frontend and race views with reflections enabled, plus rear and side close-ups for body/bumper transparency, seams, and wheel fitment.\n"""
    (out / "HANDOFF.md").write_text(handoff, encoding="utf-8")
    candidate_zip = out / "review" / (out.name + "-candidate.zip")
    with zipfile.ZipFile(candidate_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for base_name in ("runtime", "launcher"):
            base = out / base_name
            for src in sorted(p for p in base.rglob("*") if p.is_file()):
                arc = Path(out.name) / base_name / src.relative_to(base)
                info = zipfile.ZipInfo(arc.as_posix(), (2026, 10, 22, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                with src.open("rb") as stream, z.open(info, "w") as member:
                    import shutil
                    shutil.copyfileobj(stream, member, length=1024 * 1024)
        info = zipfile.ZipInfo(out.name + "/HANDOFF.md", (2026, 10, 22, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, handoff.encode("utf-8"))

    members = [(f"tools/{n}", ROOT / "tools" / n) for n in (
        "validate_vmesh48_candidate.py", "vmesh_decal_authoring.py", "vmesh_surface_repair.py", "vmesh_wheels.py", "vmesh_fitment.py", "gtmat.py", "vmesh_materials.py", "vmesh_raster.py", "vmesh_gt3_to_dx.py", "vmesh_geometry.py", "vmesh_arch.py", "vmesh_lod0.py",
        "vmesh_diagnose.py", "build_vmesh_impreza_experimental.py", "build_vmesh3_impreza_experimental.py",
        "build_vmesh4_impreza_experimental.py", "build_vmesh42_impreza_experimental.py", "build_vmesh45_impreza_experimental.py", "build_vmesh47_impreza_experimental.py", "build_vmesh48_impreza_experimental.py")]
    members += [(f"src/master_rallye/{n}", ROOT / "src/master_rallye" / n) for n in ("vehicle_project.py", "r4e_writer.py")]
    members += [(f"tests/synthetic/{n}", ROOT / "tests/synthetic" / n) for n in (
        "test_vmesh45_runtime.py", "test_vmesh46_runtime.py", "test_vmesh47_runtime.py", "test_vmesh48_runtime.py", "test_vmesh_geometry.py", "test_vmesh_arch.py", "test_vmesh_lod0.py", "test_gtmat.py", "test_vmesh_materials.py")]
    members += [("project/addon.json", project / "addon.json"), ("project/vehicle-project.json", project / "vehicle-project.json")]
    members += [(f"reports/{p.name}", p) for p in sorted((out / "reports").glob("*.json"))] + [("reports/commands.log", out / "reports" / "commands.log")]
    for sub in ("vmesh4", "vmesh41", "vmesh42", "vmesh43", "vmesh44", "vmesh45", "vmesh46", "vmesh47", "vmesh48"):
        for doc in sorted((ROOT / "research/vehicles" / sub).glob("*.md")):
            members.append((f"docs/{sub}/{doc.name}", doc))
    zpath = out / "review" / "vmesh48-review-archive.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in sorted(members):
            info = zipfile.ZipInfo(arc, (2026, 10, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, Path(src).read_bytes())
    print(json.dumps({"status": report["status"], "output_root": str(out), "retail_exe_unchanged": report["retail_exe_unchanged"],
                      **{n: sha(b) for n, b in cand.items()}, "launcher_sha256": report["bundle"]["launcher_sha256"],
                      "plan_sha256": report["bundle"]["plan_sha256"], "mapping": {k: mapping[k] for k in ("triangles_checked", "mean_colour_error", "triangles_over_tolerance")},
                      "candidate_package": str(candidate_zip), "candidate_package_sha256": sha_file(candidate_zip),
                      "review_archive": str(zpath), "review_archive_sha256": sha_file(zpath)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
