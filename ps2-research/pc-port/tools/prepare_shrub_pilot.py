"""Prepare Turkey3's original shrub category as a separate private pilot asset.

Reuse the first grass pilot's artifact format and validation without altering its
source or asset. Only original slope-eligible shrub triangles with strict retail
PC compiled-geometry correspondence are admitted. Original incremental activation
and live PS2 population remain unknown; this is full-triangle reconstruction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
import tempfile

import prepare_grass_pilot as grass

PORT = grass.PORT
RESEARCH = grass.RESEARCH
PSM_PATH = grass.PSM_PATH
PSM_SHA = grass.PSM_SHA
PC_DX_SHA = grass.PC_DX_SHA
GXI_PATH = r"\TNG\DATAPSM\PARTICLES\BUSH1.GXI"
GXI_SHA = "2e4178614fbcbb3dbc3eaf5931001d2a566e76d59ef6adf7e66cd372556d40e9"
ASSET_RELATIVE = Path(".assets/grass/Turkey3Shrubs.ps2grass")
REPORT_RELATIVE = Path("docs/grass-port2/source-contract.json")
ELIGIBLE_TRIANGLES = 3835
MATCHED_TRIANGLES = 3702
POINT_COUNT = 146498


def asset_path(path, port_root=PORT):
    """Only the new private output is writable; first grass is never replaced."""
    root = Path(port_root).resolve()
    destination = Path(path).resolve()
    if destination != root / ASSET_RELATIVE or not destination.is_relative_to(root):
        raise ValueError("Original shrub output must be exactly ignored pc-port/" + ASSET_RELATIVE.as_posix())
    component = root
    for part in ASSET_RELATIVE.parts:
        component /= part
        if component.is_symlink() or getattr(component, "is_junction", lambda: False)():
            raise ValueError("Refusing linked shrub output components")
    if destination.exists() and (not destination.is_file() or destination.stat().st_nlink > 1):
        raise ValueError("Refusing linked/nonregular shrub output")
    return destination


def publish(data, destination):
    destination = asset_path(destination)
    if destination.exists() and destination.read_bytes() != data:
        raise ValueError("Refusing to overwrite a different private shrub artifact")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".shrubs-", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def source_category(name):
    # Keep original spelling semantics, including singular shrub rejection.
    sys.path.insert(0, str(RESEARCH / "tools"))
    import detail_runtime as detail
    return detail.directive_contract(name)["detail_category"]


def serialize_artifact(points, rgba_pixels):
    return grass.serialize_artifact(points, rgba_pixels, PSM_SHA, GXI_SHA, PC_DX_SHA)


def validate_artifact(data, expected_sha=None):
    return grass.validate_artifact(data, expected_sha, (PSM_SHA, GXI_SHA, PC_DX_SHA))


def prepare(ps2_root, pc_root, sdk_root, output):
    sys.path.insert(0, str(RESEARCH / "tools"))
    import detail_runtime as detail
    import geometry_delta as geometry
    import psbtool
    import tngtool
    import water_runtime
    from course_delta import EXPECTED
    ps2_root, pc_root, sdk_root = map(Path, (ps2_root, pc_root, sdk_root))
    output = asset_path(output)
    water_runtime.verify_inputs(ps2_root)
    manifest, _ = tngtool.load_pak(ps2_root / "TNG.PAK")

    def extract(path):
        entries = [entry for entry in manifest["entries"] if entry["kind"] == "file"
                   and tngtool.logical_path(entry["path"]) == tngtool.logical_path(path)]
        if len(entries) != 1:
            raise ValueError("Missing/nonunique canonical shrub resource: " + path)
        return tngtool.read_payload(entries[0], ps2_root / "TNG.000")

    payload, psm_provenance = extract(PSM_PATH)
    gxi, gxi_provenance = extract(GXI_PATH)
    if grass.sha(payload) != PSM_SHA or grass.sha(gxi) != GXI_SHA:
        raise ValueError("Canonical Turkey3/BUSH1 source hash mismatch")
    texture = psbtool.parse_gxi(gxi)
    if (texture["width"], texture["height"], len(gxi)) != (32, 32, 4104):
        raise ValueError("Unsupported original BUSH1 GXI format")
    model = detail.decode_landscape(payload)
    eligible, categories = [], {}
    for triangle, material in sorted(model.bindings.items()):
        category = detail.directive_contract(model.materials[material])["detail_category"]
        if category == "shrubs" and detail.eligibility(model.surface(triangle), category)["eligible"]:
            eligible.append(geometry.Face(str(triangle), str(material), tuple(model.surface(triangle))))
            categories[triangle] = material
    if len(eligible) != ELIGIBLE_TRIANGLES:
        raise ValueError("Canonical Turkey3 eligible shrub source count changed")
    old_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        pc = geometry.pc_adapter(pc_root, sdk_root, "TURKEY3")
        alignment = geometry.alignment(ps2_root, pc_root, sdk_root, "TURKEY3", manifest)
    finally:
        sys.dont_write_bytecode = old_bytecode
    if pc.source["sha256"] != PC_DX_SHA or alignment["route_residual"]["max_distance"] != 0:
        raise ValueError("Verified Turkey3 PC geometry/source alignment changed")
    relations, matcher = geometry.direction_match(eligible, pc.faces, geometry.PROFILES["baseline"], "UNMATCHED")
    matched = {int(row["source"]): row for row in relations
               if row["geometry_relation"] == "EXACT_TRIANGLE_MATCH"}
    if len(matched) != MATCHED_TRIANGLES:
        raise ValueError("Canonical exact Turkey3 shrub/PC correspondence count changed")
    jitter, rng = detail.jitter_table()
    points, per_material, pc_draws = [], Counter(), set()
    maximum_abs_hash = 0.0
    for triangle in sorted(matched):
        polygon = list(reversed(model.surface(triangle)))
        coefficients = detail.plane_coefficients(polygon)
        generated = detail.scan_polygon(polygon, coefficients, "shrubs", jitter, "nearest_even")
        for sample in generated:
            x, z = sample["grid_x"], sample["grid_z"]
            value = detail.add(detail.add(detail.mul(x, detail.f32(21.123102)),
                                          detail.mul(z, detail.f32(-34.923172))),
                               detail.mul(detail.mul(x, -z), detail.f32(184.12938)))
            if not -2**31 <= value < 2**31:
                raise ValueError("Unrecovered exceptional PS2 shrub hash CVT.W.S input")
            maximum_abs_hash = max(maximum_abs_hash, abs(value))
            points.append(sample["position"])
        per_material[categories[triangle]] += len(generated)
        pc_draws.update(matched[triangle]["other_groups"])
    if len(points) != POINT_COUNT:
        raise ValueError("Canonical Turkey3 shrub reconstruction count changed")
    artifact = serialize_artifact(points, gxi[8:])
    info = validate_artifact(artifact, grass.sha(artifact))
    publish(artifact, output)
    return {"schema_version": 1, "phase": "PS2-GRASS2", "course": "TURKEY3",
            "source_identity": {name: {"size": (ps2_root / name).stat().st_size, "sha256": value}
                                for name, value in EXPECTED.items()},
            "source_psm": {"path": PSM_PATH, "provenance": psm_provenance,
                           "representation": "PS2_SPATIAL_TRIANGLE", "vertex_count": model.vertex_count,
                           "spatial_offset": model.proxy_offset, "triangle_table_offset": model.triangle_offset},
            "source_texture": {"path": GXI_PATH, "provenance": gxi_provenance, "format": texture,
                               "stored_row_order": "PRESERVED", "artifact_channel_order": "RGBA"},
            "pc_source": pc.source, "alignment": alignment,
            "selection": {"detail_category": "shrubs", "original_point_pool": 0,
                          "eligible_source_triangles": len(eligible),
                          "exact_pc_matched_source_triangles": len(matched),
                          "excluded_nonexact_source_triangles": len(eligible) - len(matched),
                          "match_tolerance_source_units": grass.MATCH_TOLERANCE,
                          "maximum_corner_error": max(row["maximum_corner_error"] for row in matched.values()),
                          "matched_pc_draw_count": len(pc_draws),
                          "generation_counts_by_material_id": dict(sorted(per_material.items())),
                          "materials": [{"id": i, "offset": model.material_offsets[i], "name": model.materials[i]}
                                        for i in sorted(per_material)], "matcher": matcher},
            "artifact": {**info, "local_relative_path": ASSET_RELATIVE.as_posix()},
            "generation": {"activation": "SYNTHETIC_FULL_TRIANGLE_ACTIVATION",
                           "precision": "FLOAT32_RECONSTRUCTION", "rng": rng,
                           "hash_rounding": "nearest_even", "hash_rounding_provenance": "EXPLICIT_PILOT_INPUT_NOT_LIVE_FCSR",
                           "maximum_abs_hash_before_conversion": maximum_abs_hash,
                           "pitch_float32": detail.PITCH, "shrub_lift_float32": detail.LIFT["shrubs"],
                           "shrub_to_grass_sprite_scale_ratio": detail.div(detail.LIFT["shrubs"], detail.LIFT["grass"]),
                           "duplicate_points": "RETAINED",
                           "point_order": "Z_THEN_X_BIN_THEN_ORIGINAL_TRIANGLE_SCANLINE_ORDER",
                           "bin_world_size": grass.BIN_WORLD_SIZE, "no_extra_height_adjustment": True},
            "evidence_grade": "CONFIRMED_BY_BOTH", "runtime_validation": "NOT_PERFORMED",
            "first_grass_preservation": "SEPARATE_OUTPUT_AND_SOURCE_IDENTITY",
            "limitations": ["No original incremental clipping, retained-pool history or exact initial population",
                            "Unmatched/nonexact source surfaces are excluded",
                            "Live PS2 FCSR, VU residency and projection scale ownership remain unknown",
                            "BUSH1 versus screenshot correspondence is not a controlled runtime draw capture",
                            "GXI stored alpha and D3D8 blend normalization differ from GS /128",
                            "No collision, wind, playable-course edit or full coordinates in report"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ps2-input-root", type=Path, required=True)
    parser.add_argument("--pc-input-root", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--asset-out", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args()
    report_out = args.report_out.resolve()
    if report_out != (PORT / REPORT_RELATIVE).resolve():
        parser.error("Compact report must be exactly pc-port/" + REPORT_RELATIVE.as_posix())
    if report_out.exists() and (report_out.is_symlink() or not report_out.is_file() or report_out.stat().st_nlink > 1):
        parser.error("Refusing linked/nonregular compact report output")
    report = prepare(args.ps2_input_root, args.pc_input_root, args.sdk_root, args.asset_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"asset": str(args.asset_out), "sha256": report["artifact"]["sha256"],
                      "point_count": report["artifact"]["point_count"],
                      "bin_count": report["artifact"]["bin_count"],
                      "size": report["artifact"]["size"], "runtime_validation": "NOT_PERFORMED"}))


if __name__ == "__main__":
    main()
