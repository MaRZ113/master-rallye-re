"""GRASS3 compact original-course inventory; delegates every game parser."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

RESEARCH = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RESEARCH / "tools"))
import detail_runtime as detail
import tngtool
import water_runtime
import psbtool


def category_inventory(model):
    material_counts = Counter(model.bindings.values())
    eligible = Counter()
    digest = {key: hashlib.sha256() for key in ("grass", "shrubs")}
    area = Counter()
    for triangle, material in sorted(model.bindings.items()):
        category = detail.directive_contract(model.materials[material])["detail_category"]
        points = model.surface(triangle)
        if detail.eligibility(points, category)["eligible"]:
            eligible[material] += 1
            digest[category].update(struct.pack("<II", triangle, material))
            for p in points:
                digest[category].update(struct.pack("<3f", *p))
            a, b, c = points
            area[category] += abs((b[0]-a[0])*(c[2]-a[2])-(b[2]-a[2])*(c[0]-a[0])) / 2
    materials = [{"id": i, "offset": model.material_offsets[i], "name": name,
                  **detail.directive_contract(name), "bound_spatial_triangles": material_counts[i],
                  "slope_eligible_float32": eligible[i]}
                 for i, name in enumerate(model.materials)]
    categories = {}
    for category in ("grass", "shrubs"):
        selected = [m for m in materials if m["detail_category"] == category]
        categories[category] = {"directive_present": bool(selected),
                               "material_ids": [m["id"] for m in selected],
                               "bound_spatial_triangles": sum(m["bound_spatial_triangles"] for m in selected),
                               "slope_eligible_float32": sum(m["slope_eligible_float32"] for m in selected),
                               "eligible_source_digest": digest[category].hexdigest(),
                               "eligible_projected_area_diagnostic": area[category]}
    return {"materials": materials, "categories": categories}


def inventory(root):
    water_runtime.verify_inputs(root)
    from course_delta import EXPECTED
    canonical = {name: {"size": (root/name).stat().st_size, "sha256": expected}
                 for name, expected in sorted(EXPECTED.items())}
    manifest, _ = tngtool.load_pak(root / "TNG.PAK")
    entries = {tngtool.logical_path(e["path"]): e for e in manifest["entries"] if e["kind"] == "file"}
    frozen = json.loads((RESEARCH / "grass1/corpus-checks.json").read_text())
    rows = []
    for known in sorted(frozen["courses"], key=lambda row: row["course"]):
        payload, provenance = tngtool.read_payload(entries[tngtool.logical_path(known["resource"])], root / "TNG.000")
        digest = hashlib.sha256(payload).hexdigest()
        if digest != known["source_sha256"]:
            raise ValueError("Frozen original landscape identity changed: " + known["course"])
        model = detail.decode_landscape(payload)
        row = {"course": known["course"], "resource": known["resource"], "psm_sha256": digest,
               "representation": "PS2_SPATIAL_TRIANGLE", "runtime_visibility": "UNKNOWN",
               "source_triangles": len(model.triangles)//3, "spatial_offset": model.proxy_offset,
               "triangle_offset": model.triangle_offset, **category_inventory(model)}
        rows.append(row)
        print(known["course"], [(c, row["categories"][c]["slope_eligible_float32"]) for c in ("grass", "shrubs")], flush=True)
    textures = []
    for category, resource in (("grass", r"\TNG\DATAPSM\PARTICLES\GRASS1.GXI"),
                               ("shrubs", r"\TNG\DATAPSM\PARTICLES\BUSH1.GXI")):
        payload, provenance = tngtool.read_payload(entries[tngtool.logical_path(resource)], root / "TNG.000")
        parsed = psbtool.parse_gxi(payload)
        textures.append({"category": category, "resource": resource,
                         "sha256": hashlib.sha256(payload).hexdigest(), "width": parsed["width"],
                         "height": parsed["height"], "stored_alpha_min": min(payload[11::4]),
                         "stored_alpha_max": max(payload[11::4]),
                         "stored_alpha_distinct": len(set(payload[11::4]))})
    return {"schema_version": 1, "phase": "PS2-GRASS3", "canonical_inputs": canonical,
            "decoder": "Existing detail_runtime.decode_landscape; exact original tag103/material bindings",
            "evidence_grade": "CONFIRMED_BY_BYTES", "numeric_precision": "FLOAT32_RECONSTRUCTION",
            "eligible_source_digest_contract": "SHA256 ordered triangle-ID/material-ID <II then each original vertex <3f; not generated placement digest",
            "placement_contract": {"pitch_float32_bits": "3faa3d71", "slope_normal_y_strict_min": 0.975,
                                   "grass_lift_and_size": 0.33, "shrubs_lift_and_size": 0.4,
                                   "original_camera_square_width": 60, "original_radial_fade": True,
                                   "static_full_triangle_reconstruction_is_original_runtime_history": False},
            "textures": textures, "courses": rows,
            "summary": {"courses": len(rows), **{c + "_directive_courses": sum(r["categories"][c]["directive_present"] for r in rows) for c in ("grass", "shrubs")},
                        **{c + "_eligible_courses": sum(r["categories"][c]["slope_eligible_float32"] > 0 for r in rows) for c in ("grass", "shrubs")}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
