"""V-MESH2: reproducible build of the experimental GT3-Impreza-on-Navara addon bundle.

One command builds, from a private GT3 OBJ dump and the pinned retail Navara donor:

  DX candidates -> addon project -> author build -> J.3-B runtime bundle ->
  launcher -> launcher preflight -> validation report -> review archive

It only reads retail/GT inputs and writes into a new output root (never
overwrites).  The retail executable is hashed before/after and never written.
The generated bundle is READY_FOR_HUMAN_RUNTIME, not runtime-qualified.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import vmesh_gt3_to_dx as conv  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402

RETAIL_EXE_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
ADDON_ID = "impreza-rally-prototype"
FAMILY = "ImprezaProto"
PAINT_RGBA = (35, 95, 230, 255)  # flat Subaru-blue placeholder for Navara's 16x16 colour-tga


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha(Path(path).read_bytes())


def flat_png(width: int, height: int, rgba) -> bytes:
    import struct
    import zlib
    raw = b"".join(b"\x00" + bytes(rgba) * width for _ in range(height))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


class Runner:
    def __init__(self, log: Path):
        self.log = log
        self.env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))

    def mrtool(self, *args: str) -> dict:
        cmd = [sys.executable, str(ROOT / "tools" / "mrtool.py"), *map(str, args)]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=self.env, cwd=str(ROOT))
        with self.log.open("a", encoding="utf-8") as handle:
            handle.write("$ " + " ".join(cmd) + "\n" + proc.stdout + proc.stderr + f"\n[exit {proc.returncode}]\n")
        if proc.returncode != 0:
            raise SystemExit(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout[-800:]}{proc.stderr[-800:]}")
        text = proc.stdout
        start = text.find("\n{\n")
        try:
            return json.loads(text[start + 1:] if start >= 0 else text)
        except json.JSONDecodeError:
            return {"stdout_tail": text[-400:]}


def collision_fit(donor_car: bytes, body_extent: dict) -> dict:
    """Per-axis scale/translation moving Navara's tag101 hull onto the GT body extents."""
    hull = parse_dx_bytes(donor_car).collision.convex_hull.representation_a.geometry_a.vertices
    lo = [min(p[i] for p in hull) for i in range(3)]
    hi = [max(p[i] for p in hull) for i in range(3)]
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    b_lo, b_hi = body_extent["min"], list(body_extent["max"])
    b_hi[1] = body_extent["roof_y_p99"]        # ignore antenna tips for the roof
    scale = [(b_hi[i] - b_lo[i]) / (hi[i] - lo[i]) for i in range(3)]
    new_min_y = c[1] - scale[1] * (c[1] - lo[1])
    trans = [0.0, lo[1] - new_min_y, (b_lo[2] + b_hi[2]) / 2 - c[2]]  # keep hull floor; centre in Z
    return {"hull_bbox": [lo, hi], "scale": [round(v, 4) for v in scale],
            "centre": [round(v, 4) for v in c], "translation": [round(v, 4) for v in trans]}


def risk_analysis(donor: dict[str, bytes], cand: dict[str, bytes], reports: dict) -> dict:
    out = {}
    for name in ("car.dx", "complete.dx"):
        d, o = parse_dx_bytes(donor[name]), parse_dx_bytes(cand[name])
        rep = reports[name]
        keep = set(rep["kept_draws"])
        fillers = []
        for draw in o.physical_draws:
            if draw.draw_index not in rep["filler_draws"]:
                continue
            pts = o.vertices.positions[draw.vertex_base:draw.vertex_base + draw.local_vertex_max + 1]
            a, b, c = pts[:3]
            u = [b[i] - a[i] for i in range(3)]
            w = [c[i] - a[i] for i in range(3)]
            cross = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            fillers.append({"draw": draw.draw_index, "tag": draw.tag, "group": draw.group_label,
                            "texture": draw.texture_slots[0].value, "alpha_flag": draw.flags_0x20[0],
                            "triangles": draw.triangle_count, "area_m2": round(0.5 * math.sqrt(sum(x * x for x in cross)), 6)})
        tiny = sum(1 for draw in o.physical_draws if draw.draw_index not in rep["filler_draws"]
                   for _ in [0] if draw.triangle_count < 1)
        body = [v for r in rep["replaced_draws"].values() for v in
                o.vertices.positions[o.physical_draws[r].vertex_base:o.physical_draws[r].vertex_base + o.physical_draws[r].local_vertex_max + 1]]
        kept_pts = [p for i in keep for p in o.vertices.positions[o.physical_draws[i].vertex_base:o.physical_draws[i].vertex_base + o.physical_draws[i].local_vertex_max + 1]]
        bb = lambda ps: ([round(min(p[k] for p in ps), 3) for k in range(3)], [round(max(p[k] for p in ps), 3) for k in range(3)])
        b_lo, b_hi = bb(body)
        out[name] = {
            "filler_draws": fillers,
            "filler_alpha_blended": [f["draw"] for f in fillers if f["alpha_flag"]],
            "filler_group_members": [f["draw"] for f in fillers if f["tag"] in (7, 8)],
            "max_vertices_in_one_draw": max(d.local_vertex_max + 1 for d in o.physical_draws),
            "kept_donor_draws": sorted(keep),
            "kept_points_outside_gt_body_bbox": sum(1 for p in kept_pts if any(p[k] < b_lo[k] - 1e-3 or p[k] > b_hi[k] + 1e-3 for k in range(3))),
            "kept_bbox": bb(kept_pts), "gt_body_bbox": [b_lo, b_hi],
            "omitted_gt_faces": sum(rep["exclusion_breakdown"].values()),
            "omitted_gt_breakdown": rep["exclusion_breakdown"],
            "tag7_tag8_hierarchy_equal_to_donor": all(
                (x.tag, x.group_label, x.control_words) == (y.tag, y.group_label, y.control_words)
                for x, y in zip(d.physical_draws, o.physical_draws)),
        }
    return out


def structural_checks(root_rt: Path, donor_dir: Path) -> dict:
    out = {}
    for f in ("car.dx", "complete.dx", "wheel.dx"):
        a, b = (donor_dir / f).read_bytes(), (root_rt / f).read_bytes()
        d, o = parse_dx_bytes(a), parse_dx_bytes(b)
        r = {"sha256": sha(b), "identical_to_donor": a == b, "draws": [len(d.physical_draws), len(o.physical_draws)],
             "draw_identity_and_texture_strings_equal": all(
                 (x.tag, x.group_label, x.control_words, [t.value for t in x.texture_slots], x.flags_0x20, x.unknown_0x24)
                 == (y.tag, y.group_label, y.control_words, [t.value for t in y.texture_slots], y.flags_0x20, y.unknown_0x24)
                 for x, y in zip(d.physical_draws, o.physical_draws)),
             "triangles": [d.triangle_count, o.triangle_count], "vertices": [len(d.vertices.positions), len(o.vertices.positions)],
             "validated": bool(o.diagnostics.validated), "diagnostics_equal_to_donor": str(d.diagnostics) == str(o.diagnostics),
             "all_positions_finite": all(math.isfinite(c) for p in o.vertices.positions for c in p)}
        if f == "car.dx":
            g = o.collision.convex_hull.representation_a.geometry_a.vertices
            r["hull_bbox"] = [[round(min(p[i] for p in g), 3) for i in range(3)], [round(max(p[i] for p in g), 3) for i in range(3)]]
        out[f] = r
    t = parse_dxt_bytes((root_rt / "colour-tga.dxt").read_bytes())
    out["colour-tga.dxt"] = {"size": [t.width, t.height],
                             "distinct_pixels": len({bytes(t.bgra[i:i + 4]) for i in range(0, len(t.bgra), 4)})}
    out["dxt_differing_from_donor"] = sorted(p.name for p in root_rt.glob("*.dxt")
                                             if (donor_dir / p.name).exists() and (donor_dir / p.name).read_bytes() != p.read_bytes())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gt-dir", type=Path, required=True, help="GT3 sb0097 CarModelSet dump directory (private)")
    ap.add_argument("--retail-root", type=Path, required=True, help="pinned retail root with Data.sma and Data.sma_unpacked")
    ap.add_argument("--retail-exe", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True, help="new directory (must not exist)")
    ap.add_argument("--lod", default="lod1")
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
    donor = {n: (donor_dir / n).read_bytes() for n in ("car.dx", "complete.dx")}
    obj, lod0 = args.gt_dir / f"model0.{args.lod}.obj", args.gt_dir / "model0.lod0.obj"

    # 1. DX candidates
    cand, reports = {}, {}
    for profile, name in (("car", "car.dx"), ("complete", "complete.dx")):
        data, rep = conv.build_candidate(obj, donor[name], None, lod0, profile)
        (out / "dx" / name).write_bytes(data)
        cand[name], reports[name] = data, rep
        dump(out / "reports" / f"convert-{profile}.json", rep)
    fit = collision_fit(donor["car.dx"], reports["car.dx"]["body_extent"])
    (out / "tex" / "colour-tga.png").write_bytes(flat_png(16, 16, PAINT_RGBA))

    # 2. addon project
    project = out / "project"
    run.mrtool("addon", "init", "--name", "Impreza Rally Prototype", "--class", "T2", "--donor", "Navara",
               "--family", FAMILY, "--donor-source", donor_dir, "--output", project)
    addon = json.loads((project / "addon.json").read_text(encoding="utf-8"))
    addon["description"] = ("PRIVATE experimental V-MESH2: Navara-donor T2 addon with a GT3-derived Impreza body mesh "
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
              "complete.dx": {"source_sha256": sha(donor["complete.dx"]), "topology_candidate": "../dx/complete.dx"}},
          "texture_edits": {"colour-tga.dxt": {"source_sha256": sha_file(donor_dir / "colour-tga.dxt"),
                                               "png": "../tex/colour-tga.png"}},
          "texture_replacements": {}}
    dump(project / "vehicle-project.json", vp)

    # 3. validate + author build
    retail_args = ["--retail-data-sma", args.retail_root / "Data.sma", "--retail-data-root", args.retail_root / "Data.sma_unpacked"]
    steps = {}
    steps["validate_vehicle"] = run.mrtool("validate-vehicle", project / "vehicle-project.json")
    steps["project_validate"] = run.mrtool("addon", "project-validate", project, *retail_args)
    steps["project_build"] = run.mrtool("addon", "project-build", project, *retail_args, "--output", out / "author-build")
    steps["author_verify"] = run.mrtool("addon", "verify", out / "author-build")

    # 4. runtime bundle
    m1 = ROOT / "research/vehicles/sdk/examples/mercedes-ml320.json"
    m2 = project / "addon.json"
    pb = f"{ADDON_ID}={out / 'author-build'}"
    common = ["--manifest", m1, "--manifest", m2, "--project-build", pb]
    steps["runtime_prepare"] = run.mrtool("addon", "runtime-prepare", *common, "--output", out / "runtime")
    steps["runtime_verify"] = run.mrtool("addon", "runtime-verify", out / "runtime", *common)
    launcher_exe = None
    if not args.skip_launcher:
        steps["launcher_build"] = run.mrtool("addon", "runtime-launcher-build", out / "runtime", *common,
                                             "--launcher-output", out / "launcher")
        launcher_exe = out / "launcher" / "mr-runtime-launcher.exe"
        proc = subprocess.run([str(launcher_exe), "--verify", str(args.retail_exe), str(out / "runtime")],
                              capture_output=True, text=True)
        steps["launcher_preflight"] = {"exit": proc.returncode, "output": proc.stdout.strip().splitlines()}
        if proc.returncode != 0:
            raise SystemExit("launcher preflight failed: " + proc.stdout + proc.stderr)

    # 5. independent checks + risk analysis
    rt_family = out / "runtime" / "resource-root" / "DataGx" / "Vehicles" / FAMILY
    structural = structural_checks(rt_family, donor_dir)
    risks = risk_analysis(donor, {n: (rt_family / n).read_bytes() for n in ("car.dx", "complete.dx")}, reports)
    exe_after = sha_file(args.retail_exe)
    report = {
        "status": "READY_FOR_HUMAN_RUNTIME_NOT_RUNTIME_QUALIFIED",
        "inputs": {"gt_obj": str(obj), "gt_obj_sha256": sha_file(obj), "gt_lod0_sha256": sha_file(lod0),
                   "donor_car_sha256": sha(donor["car.dx"]), "donor_complete_sha256": sha(donor["complete.dx"]),
                   "retail_exe_sha256_before": exe_before, "retail_exe_sha256_after": exe_after},
        "fit": {"scale": reports["car.dx"]["scale"], "axles_gt": reports["car.dx"]["axles_gt"],
                "donor_axle_z": reports["car.dx"]["donor_axle_z"], "body_extent": reports["car.dx"]["body_extent"],
                "collision": fit, "paint_rgba": list(PAINT_RGBA)},
        "candidates": {n: {"sha256": sha(b), "output_triangles": reports[n]["rebuild"]["output_triangle_count"],
                           "output_vertices": reports[n]["rebuild"]["output_vertex_count"],
                           "replaced_draw_stats": reports[n]["replaced_draw_stats"]} for n, b in cand.items()},
        "steps": {k: ({"status": v.get("status")} if isinstance(v, dict) and "status" in v else v) for k, v in steps.items()},
        "bundle": {"plan_sha256": steps["runtime_prepare"].get("addon_plan_sha256") or json.loads((out / "runtime" / "runtime-artifact.json").read_text(encoding="utf-8")).get("addon_plan_sha256"),
                   "resource_index_sha256": steps["runtime_prepare"].get("resource_index_sha256"),
                   "resource_count": steps["runtime_prepare"].get("resource_count"),
                   "launcher_sha256": sha_file(launcher_exe) if launcher_exe else None},
        "structural": structural, "risks": risks,
        "retail_exe_unchanged": exe_before == exe_after == RETAIL_EXE_SHA256,
    }
    dump(out / "reports" / "validation-report.json", report)

    # 6. review archive (no GT/derived DX/DXT, no runtime resource root, no executables)
    hashes = {"private_assets_not_in_archive": {
        "gt_obj_sha256": report["inputs"]["gt_obj_sha256"], "car.dx": sha(cand["car.dx"]), "complete.dx": sha(cand["complete.dx"]),
        "colour-tga.png": sha_file(out / "tex" / "colour-tga.png"),
        "launcher_sha256": report["bundle"]["launcher_sha256"], "plan_sha256": report["bundle"]["plan_sha256"]}}
    dump(out / "reports" / "private-asset-hashes.json", hashes)
    members = [("tools/vmesh_gt3_to_dx.py", ROOT / "tools/vmesh_gt3_to_dx.py"),
               ("tools/build_vmesh_impreza_experimental.py", ROOT / "tools/build_vmesh_impreza_experimental.py"),
               ("tests/synthetic/test_vmesh_gt3_to_dx.py", ROOT / "tests/synthetic/test_vmesh_gt3_to_dx.py"),
               ("project/addon.json", project / "addon.json"), ("project/vehicle-project.json", project / "vehicle-project.json"),
               ("reports/validation-report.json", out / "reports/validation-report.json"),
               ("reports/private-asset-hashes.json", out / "reports/private-asset-hashes.json"),
               ("reports/convert-car.json", out / "reports/convert-car.json"),
               ("reports/convert-complete.json", out / "reports/convert-complete.json"),
               ("reports/commands.log", log)]
    for doc in sorted((ROOT / "research/vehicles/vmesh").glob("*.md")):
        members.append((f"docs/{doc.name}", doc))
    zpath = out / "review" / "vmesh2-review-archive.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in sorted(members):
            info = zipfile.ZipInfo(arc, (2026, 10, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, Path(src).read_bytes())
    print(json.dumps({"status": report["status"], "output_root": str(out), "retail_exe_unchanged": report["retail_exe_unchanged"],
                      "car_dx": sha(cand["car.dx"]), "complete_dx": sha(cand["complete.dx"]),
                      "plan_sha256": report["bundle"]["plan_sha256"], "launcher_sha256": report["bundle"]["launcher_sha256"],
                      "review_archive": str(zpath), "review_archive_sha256": sha_file(zpath)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
