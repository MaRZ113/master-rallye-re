"""Bounded placement evidence; optional original data stays in ignored assets."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import os
import tempfile

RESEARCH = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RESEARCH / "tools"))
sys.path.insert(0, str(RESEARCH / "pc-port/tools"))
import detail_runtime as detail
import geometry_delta as geometry
import tngtool
import water_runtime
import prepare_grass_pilot as grass


def publish_private(artifact,course,category,directory):
    root=RESEARCH/'pc-port/.assets/grass'
    if directory.resolve()!=root.resolve():raise ValueError('Only ignored pc-port/.assets/grass is an asset destination')
    for path in (root.parent,root):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Linked private asset root')
    stem={'FRANCE1':'France1','ITALY_S1':'ItalyS1'}[course]
    destination=root/(stem+('Grass' if category=='grass' else 'Shrubs')+'.ps2grass')
    if destination.exists() and (destination.is_symlink() or destination.stat().st_nlink!=1 or destination.read_bytes()!=artifact):
        raise ValueError('Refusing to overwrite a different or linked private artifact')
    root.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.grass3-',suffix='.tmp',dir=root)
    try:
        with os.fdopen(fd,'wb') as f:f.write(artifact);f.flush();os.fsync(f.fileno())
        os.replace(name,destination)
    finally:
        if os.path.exists(name):os.unlink(name)
    return destination.name

def compare(ps2, pc, sdk, course,asset_directory=None):
    start = time.monotonic()
    water_runtime.verify_inputs(ps2)
    manifest, _ = tngtool.load_pak(ps2 / "TNG.PAK")
    known = json.loads((RESEARCH / "pc-port/docs/grass-port3/course-inventory.json").read_text())
    source = next(row for row in known["courses"] if row["course"] == course)
    lookup = {tngtool.logical_path(e["path"]): e for e in manifest["entries"] if e["kind"] == "file"}
    payload, _ = tngtool.read_payload(lookup[tngtool.logical_path(source["resource"])], ps2 / "TNG.000")
    if hashlib.sha256(payload).hexdigest() != source["psm_sha256"]:
        raise ValueError("Original course source identity mismatch")
    model = detail.decode_landscape(payload)
    sys.dont_write_bytecode = True
    target = geometry.pc_adapter(pc, sdk, course)
    alignment = geometry.alignment(ps2, pc, sdk, course, manifest)
    # geometry.alignment independently validates identical identity landscape
    # matrices. Retain route outliers; never fit geometry to eliminate them.
    if alignment["route_residual"]["within_one_world_unit"] < 0.99:
        raise ValueError("Independent route agreement below bounded selected-course gate")
    categories = {}
    jitter, rng = detail.jitter_table()
    for category in ("grass", "shrubs"):
        faces = [geometry.Face(str(tri), str(mat), tuple(model.surface(tri)))
                 for tri, mat in sorted(model.bindings.items())
                 if detail.directive_contract(model.materials[mat])["detail_category"] == category
                 and detail.eligibility(model.surface(tri), category)["eligible"]]
        relations, stats = geometry.direction_match(faces, target.faces, geometry.PROFILES["baseline"], "UNMATCHED")
        matched = [row for row in relations if row["geometry_relation"] == "EXACT_TRIANGLE_MATCH"]
        points, material_counts, draw_ids = [], Counter(), set()
        max_hash_absolute=0.0
        maximum_abs_hash = 0.0
        digest = hashlib.sha256()
        for row in matched:
            tri = int(row["source"])
            polygon = list(reversed(model.surface(tri)))
            generated = detail.scan_polygon(polygon, detail.plane_coefficients(polygon), category, jitter, "nearest_even")
            for sample in generated:
                x,z=sample['grid_x'],sample['grid_z']
                h=detail.add(detail.add(detail.mul(x,detail.f32(21.123102)),detail.mul(z,detail.f32(-34.923172))),
                             detail.mul(detail.mul(x,-z),detail.f32(184.12938)))
                if not -2**31<=h<2**31:raise ValueError('Unrecovered exceptional R5900 hash CVT.W.S input')
                max_hash_absolute=max(max_hash_absolute,abs(h))
                x, z = sample["grid_x"], sample["grid_z"]
                value_hash = detail.add(detail.add(detail.mul(x, detail.f32(21.123102)),
                                                  detail.mul(z, detail.f32(-34.923172))),
                                        detail.mul(detail.mul(x, -z), detail.f32(184.12938)))
                if not -2**31 <= value_hash < 2**31:
                    raise ValueError("Unproved CVT.W.S overflow in selected source placement")
                maximum_abs_hash = max(maximum_abs_hash, abs(value_hash))
                value = tuple(sample["position"])
                digest.update(struct.pack("<3f", *value))
                points.append(value)
                material_counts[model.bindings[tri]] += 1
            draw_ids.update(int(group.rsplit(":draw:", 1)[1]) for group in row["other_groups"])
        texture = next(t for t in known["textures"] if t["category"] == category)
        gxi, _ = tngtool.read_payload(lookup[tngtool.logical_path(texture["resource"])], ps2 / "TNG.000")
        if hashlib.sha256(gxi).hexdigest()!=texture['sha256'] or len(gxi)!=4104:
            raise ValueError('Canonical particle texture identity mismatch')
        if hashlib.sha256(gxi).hexdigest() != texture["sha256"]:
            raise ValueError("Canonical category image identity mismatch")
        artifact = grass.serialize_artifact(points, gxi[8:], source["psm_sha256"], texture["sha256"], target.source["sha256"])
        layout = grass.validate_artifact(artifact)
        if asset_directory:
            pinned=json.loads((RESEARCH/'pc-port/docs/grass-port3'/('france1-placement.json' if course=='FRANCE1' else 'italys1-placement.json')).read_text())
            if layout['sha256']!=pinned['categories'][category]['artifact']['sha256']:
                raise ValueError('Placement differs from independently frozen comparison')
            publish_private(artifact,course,category,asset_directory)
        categories[category] = {"eligible_triangles": len(faces), "strict_matched_triangles": len(matched),
                                "excluded_nonexact_triangles": len(faces)-len(matched),
                                "pc_draws": sorted(draw_ids), "matcher_statistics": stats,
                                "reconstructed_point_count": len(points), "generated_xyz_sha256": digest.hexdigest(),
                                "maximum_abs_hash_before_int_conversion": maximum_abs_hash,
                                "generated_xyz_digest_contract": "Original sorted source-triangle scanline order, each XYZ <3f",
                                "maximum_abs_hash_before_conversion": max_hash_absolute,
                                "per_material_point_counts": dict(sorted(material_counts.items())),
                                "artifact": layout,
                                "publish_status": "PRIVATE_IGNORED_ASSET_WRITTEN" if asset_directory else "NO_ASSET_WRITTEN"}
        print(course, category, len(faces), len(matched), len(points), layout["sha256"], flush=True)
    print("elapsed_seconds", time.monotonic()-start, flush=True)
    return {"schema_version": 1, "course": course, "source_psm_sha256": source["psm_sha256"],
            "pc_source": {key: value for key, value in target.source.items() if key != "txt_dinghy_leads"},
            "alignment": alignment, "categories": categories,
            "matching_tolerance": 0.001, "generation": "SYNTHETIC_FULL_TRIANGLE_ACTIVATION",
            "hash_rounding": "EXPLICIT_NEAREST_EVEN_NOT_LIVE_FCSR", "rng": rng,
            "numeric_precision": "FLOAT32_RECONSTRUCTION", "runtime_validation": "NOT_PERFORMED",
            "evidence_grade": "CONFIRMED_BY_BYTES",
            "limitations": ["Nonexact source triangles excluded", "No original incremental clipping/history replay",
                            "No camera/VU live equivalence", "Original projected-size cap and inherited GS state not ported exactly"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ps2", type=Path, required=True)
    p.add_argument("--pc", type=Path, required=True)
    p.add_argument("--sdk", type=Path, required=True)
    p.add_argument("--course", choices=("FRANCE1", "ITALY_S1"), required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument('--asset-directory',type=Path)
    a = p.parse_args()
    result = compare(a.ps2, a.pc, a.sdk, a.course,a.asset_directory)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
