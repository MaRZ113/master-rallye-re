"""Prepare a private Turkey3 grass-source pilot without editing playable assets.

Only PS2 grass source triangles that exactly match validated retail PC compiled
triangles at 0.001 source units are admitted. Placement delegates to GRASS1's
FLOAT32_RECONSTRUCTION with explicit nearest-even CVT.W.S and full original
triangle activation. This is not the unrecovered incremental PS2 clip/history.
Original coordinates/image content are written only to ignored .assets/grass/.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile

PORT = Path(__file__).resolve().parents[1]
RESEARCH = PORT.parent
MAGIC = b"PS2GRS01"
VERSION = 1
HEADER = struct.Struct("<8s6I32s32s32s")
BIN = struct.Struct("<2i2I")
POINT = struct.Struct("<3f")
BIN_WORLD_SIZE = 8.0
MAX_POINTS = 250000
MAX_BINS = 65536
MAX_COORDINATE = 1000000.0
PSM_PATH = r"\TNG\DATAPSM\COURSE\TURKEY3\TURKEY3.PSM"
PSM_SHA = "dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc"
GXI_PATH = r"\TNG\DATAPSM\PARTICLES\GRASS1.GXI"
GXI_SHA = "519908ac79ca57591a8a38d3629286e25ffc51539705342864a5056785427eb6"
PC_DX_SHA = "724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8"
ASSET_RELATIVE = Path(".assets/grass/Turkey3Grass.ps2grass")
MATCH_TOLERANCE = 0.001


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _hash_bytes(value):
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("Source SHA-256 must contain exactly 64 hexadecimal characters")
    try:
        result = bytes.fromhex(value)
    except ValueError as error:
        raise ValueError("Invalid source SHA-256") from error
    if len(result) != 32:
        raise ValueError("Invalid source SHA-256 length")
    return result


def _point(value):
    if len(value) != 3 or not all(math.isfinite(v) and abs(v) <= MAX_COORDINATE for v in value):
        raise ValueError("Grass point must contain three finite bounded coordinates")
    try:
        # Bucket the serialized float32 coordinate, not a host-double precursor.
        result = POINT.unpack(POINT.pack(*value))
    except (OverflowError, struct.error) as error:
        raise ValueError("Grass point is outside float32 format") from error
    return result


def point_bin(value):
    return math.floor(value[0] / BIN_WORLD_SIZE), math.floor(value[2] / BIN_WORLD_SIZE)


def serialize_artifact(points, rgba_pixels, psm_sha=PSM_SHA, gxi_sha=GXI_SHA, pc_sha=PC_DX_SHA):
    """Stable bins with caller source/lattice order preserved inside each bin."""
    if not 0 < len(points) <= MAX_POINTS or len(rgba_pixels) != 32 * 32 * 4:
        raise ValueError("Unsupported grass point count or texture dimensions")
    bins = defaultdict(list)
    for value in points:
        p = _point(value)
        bins[point_bin(p)].append(p)  # Duplicate original samples stay distinct.
    if not 0 < len(bins) <= MAX_BINS:
        raise ValueError("Unsupported grass bin count")
    result = bytearray(HEADER.pack(MAGIC, VERSION, len(points), len(bins), 32, 32,
                                  len(rgba_pixels), _hash_bytes(psm_sha),
                                  _hash_bytes(gxi_sha), _hash_bytes(pc_sha)))
    first = 0
    ordered = sorted(bins.items(), key=lambda item: (item[0][1], item[0][0]))
    for (x, z), values in ordered:
        result.extend(BIN.pack(x, z, first, len(values)))
        first += len(values)
    for _, values in ordered:
        for p in values:
            result.extend(POINT.pack(*p))
    result.extend(rgba_pixels)
    return bytes(result)


def validate_artifact(data, expected_sha=None, expected_sources=None):
    """Independent structural readback plus optional whole-file/source identity."""
    if expected_sha is not None and sha(data) != expected_sha:
        raise ValueError("Grass artifact SHA-256 mismatch")
    if len(data) < HEADER.size:
        raise ValueError("Truncated grass artifact header")
    magic, version, count, bins, width, height, image_bytes, psm, gxi, pc = HEADER.unpack_from(data)
    if magic != MAGIC or version != VERSION:
        raise ValueError("Unsupported grass artifact magic/version")
    if not 0 < count <= MAX_POINTS or not 0 < bins <= min(MAX_BINS, count):
        raise ValueError("Grass artifact count budget exceeded")
    if (width, height, image_bytes) != (32, 32, 4096):
        raise ValueError("Grass artifact texture must be 32x32 RGBA")
    if expected_sources is not None and (psm.hex(), gxi.hex(), pc.hex()) != tuple(expected_sources):
        raise ValueError("Grass artifact source identities mismatch")
    point_offset = HEADER.size + bins * BIN.size
    texture_offset = point_offset + count * POINT.size
    if len(data) != texture_offset + image_bytes:
        raise ValueError("Grass artifact declared sections do not match file size")
    next_point, previous_key = 0, None
    minima, maxima = [math.inf] * 3, [-math.inf] * 3
    for i in range(bins):
        x, z, first, n = BIN.unpack_from(data, HEADER.size + i * BIN.size)
        key = (z, x)
        if previous_key is not None and key <= previous_key:
            raise ValueError("Grass bins must be strictly Z-then-X ordered")
        if first != next_point or not n or first + n > count:
            raise ValueError("Grass bins must cover contiguous nonempty point ranges")
        for point_index in range(first, first + n):
            p = _point(POINT.unpack_from(data, point_offset + point_index * POINT.size))
            if point_bin(p) != (x, z):
                raise ValueError("Grass point is outside its declared bin")
            for axis in range(3):
                minima[axis] = min(minima[axis], p[axis])
                maxima[axis] = max(maxima[axis], p[axis])
        next_point += n
        previous_key = key
    if next_point != count:
        raise ValueError("Grass bins do not cover the complete point array")
    return {"size": len(data), "sha256": sha(data), "point_count": count, "bin_count": bins,
            "bin_world_size": BIN_WORLD_SIZE, "texture_width": width, "texture_height": height,
            "texture_bytes": image_bytes, "psm_sha256": psm.hex(), "gxi_sha256": gxi.hex(),
            "pc_dx_sha256": pc.hex(), "bounds": {"min": minima, "max": maxima},
            "layout": {"header_size": HEADER.size, "bin_record_size": BIN.size,
                       "point_record_size": POINT.size, "bin_table_offset": HEADER.size,
                       "point_offset": point_offset, "texture_offset": texture_offset}}


def asset_path(path, port_root=PORT):
    root = Path(port_root).resolve()
    candidate = root
    for part in ASSET_RELATIVE.parts:
        candidate /= part
        if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
            raise ValueError("Refusing linked grass output components")
    destination = Path(path).resolve()
    if destination != root / ASSET_RELATIVE or not destination.is_relative_to(root):
        raise ValueError("Original grass output must be exactly ignored pc-port/" + ASSET_RELATIVE.as_posix())
    if destination.exists() and (not destination.is_file() or destination.stat().st_nlink > 1):
        raise ValueError("Refusing linked/nonregular grass output")
    return destination


def publish(data, destination):
    destination = asset_path(destination)
    if destination.exists() and destination.read_bytes() != data:
        raise ValueError("Refusing to overwrite a different private grass artifact")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".grass-", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def prepare(ps2_root, pc_root, sdk_root, output):
    sys.path.insert(0, str(RESEARCH / "tools"))
    import detail_runtime as d
    import geometry_delta as g
    import psbtool as p
    import tngtool as t
    import water_runtime as w
    from course_delta import EXPECTED
    ps2_root, pc_root, sdk_root = map(Path, (ps2_root, pc_root, sdk_root))
    output = asset_path(output)
    w.verify_inputs(ps2_root)
    manifest, _ = t.load_pak(ps2_root / "TNG.PAK")

    def extract(path):
        entries = [e for e in manifest["entries"] if e["kind"] == "file"
                   and t.logical_path(e["path"]) == t.logical_path(path)]
        if len(entries) != 1:
            raise ValueError("Missing/nonunique canonical grass resource: " + path)
        return t.read_payload(entries[0], ps2_root / "TNG.000")

    payload, psm_provenance = extract(PSM_PATH)
    gxi, gxi_provenance = extract(GXI_PATH)
    if sha(payload) != PSM_SHA or sha(gxi) != GXI_SHA:
        raise ValueError("Canonical Turkey3/grass source hash mismatch")
    texture = p.parse_gxi(gxi)
    if (texture["width"], texture["height"], len(gxi)) != (32, 32, 4104):
        raise ValueError("Unsupported original GRASS1 GXI format")
    model = d.decode_landscape(payload)
    eligible = []
    categories = {}
    for triangle, material in sorted(model.bindings.items()):
        category = d.directive_contract(model.materials[material])["detail_category"]
        if category == "grass" and d.eligibility(model.surface(triangle), category)["eligible"]:
            eligible.append(g.Face(str(triangle), str(material), tuple(model.surface(triangle))))
            categories[triangle] = material
    if len(eligible) != 2912:
        raise ValueError("Canonical Turkey3 eligible grass source count changed")
    old_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        pc = g.pc_adapter(pc_root, sdk_root, "TURKEY3")
        alignment = g.alignment(ps2_root, pc_root, sdk_root, "TURKEY3", manifest)
    finally:
        sys.dont_write_bytecode = old_bytecode
    if pc.source["sha256"] != PC_DX_SHA or alignment["route_residual"]["max_distance"] != 0:
        raise ValueError("Verified Turkey3 PC geometry/source alignment changed")
    relations, matcher = g.direction_match(eligible, pc.faces, g.PROFILES["baseline"], "UNMATCHED")
    matched = {int(row["source"]): row for row in relations
               if row["geometry_relation"] == "EXACT_TRIANGLE_MATCH"}
    if len(matched) != 2797:
        raise ValueError("Canonical exact Turkey3 grass/PC correspondence count changed")
    jitter, rng = d.jitter_table()
    points, per_material, pc_draws = [], Counter(), set()
    max_hash_absolute = 0.0
    for triangle in sorted(matched):
        polygon = list(reversed(model.surface(triangle)))
        coefficients = d.plane_coefficients(polygon)
        generated = d.scan_polygon(polygon, coefficients, "grass", jitter, "nearest_even")
        for sample in generated:
            x, z = sample["grid_x"], sample["grid_z"]
            value = d.add(d.add(d.mul(x, d.f32(21.123102)), d.mul(z, d.f32(-34.923172))),
                          d.mul(d.mul(x, -z), d.f32(184.12938)))
            if not -2**31 <= value < 2**31:
                raise ValueError("Unrecovered exceptional PS2 hash CVT.W.S input")
            max_hash_absolute = max(max_hash_absolute, abs(value))
            points.append(sample["position"])
        per_material[categories[triangle]] += len(generated)
        pc_draws.update(matched[triangle]["other_groups"])
    artifact = serialize_artifact(points, gxi[8:])
    info = validate_artifact(artifact, sha(artifact), (PSM_SHA, GXI_SHA, PC_DX_SHA))
    publish(artifact, output)
    return {"schema_version": 1, "phase": "PS2-GRASS-PORT1", "course": "TURKEY3",
            "source_identity": {name: {"size": (ps2_root / name).stat().st_size, "sha256": value}
                                for name, value in EXPECTED.items()},
            "source_psm": {"path": PSM_PATH, "provenance": psm_provenance,
                           "representation": "PS2_SPATIAL_TRIANGLE", "vertex_count": model.vertex_count,
                           "spatial_offset": model.proxy_offset, "triangle_table_offset": model.triangle_offset},
            "source_texture": {"path": GXI_PATH, "provenance": gxi_provenance, "format": texture,
                               "stored_row_order": "PRESERVED", "artifact_channel_order": "RGBA"},
            "pc_source": pc.source, "alignment": alignment,
            "selection": {"detail_category": "grass", "eligible_source_triangles": len(eligible),
                          "exact_pc_matched_source_triangles": len(matched),
                          "excluded_nonexact_source_triangles": len(eligible) - len(matched),
                          "match_tolerance_source_units": MATCH_TOLERANCE,
                          "maximum_corner_error": max(row["maximum_corner_error"] for row in matched.values()),
                          "matched_pc_draw_count": len(pc_draws),
                          "generation_counts_by_material_id": dict(sorted(per_material.items())),
                          "materials": [{"id": i, "offset": model.material_offsets[i], "name": model.materials[i]}
                                        for i in sorted(per_material)], "matcher": matcher},
            "artifact": {**info, "local_relative_path": ASSET_RELATIVE.as_posix()},
            "generation": {"activation": "FULL_ORIGINAL_TRIANGLE_ACTIVATION_RECONSTRUCTION",
                           "precision": "FLOAT32_RECONSTRUCTION", "rng": rng,
                           "hash_rounding": "nearest_even", "hash_rounding_provenance": "EXPLICIT_PILOT_INPUT_NOT_LIVE_FCSR",
                           "maximum_abs_hash_before_conversion": max_hash_absolute,
                           "pitch_float32": d.PITCH, "grass_lift_float32": d.LIFT["grass"],
                           "duplicate_points": "RETAINED", "point_order": "Z_THEN_X_BIN_THEN_ORIGINAL_TRIANGLE_SCANLINE_ORDER",
                           "bin_world_size": BIN_WORLD_SIZE, "no_extra_height_adjustment": True},
            "evidence_grade": "CONFIRMED_BY_BOTH", "runtime_validation": "NOT_PERFORMED",
            "limitations": ["Not PS2 incremental clipping, retained-pool history or exact initial population",
                            "Unmatched/nonexact source surfaces are deliberately excluded",
                            "Live PS2 FCSR, VU residency and projection scale ownership remain unknown",
                            "Original point heights are preserved; no arbitrary anti-occlusion lift",
                            "GXI stored alpha and D3D8 blend normalization differ from GS /128",
                            "No shrubs, stones, collision, wind, playable-course edit or full coordinates in report"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ps2-input-root", type=Path, required=True)
    parser.add_argument("--pc-input-root", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--asset-out", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args()
    report_out = args.report_out.resolve()
    if report_out != (PORT / "docs/grass-port1/source-contract.json").resolve():
        parser.error("Compact report must be exactly pc-port/docs/grass-port1/source-contract.json")
    if report_out.exists() and (report_out.is_symlink() or not report_out.is_file() or report_out.stat().st_nlink > 1):
        parser.error("Refusing linked/nonregular compact report output")
    report = prepare(args.ps2_input_root, args.pc_input_root, args.sdk_root, args.asset_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"asset": str(args.asset_out), "sha256": report["artifact"]["sha256"],
                      "point_count": report["artifact"]["point_count"], "bin_count": report["artifact"]["bin_count"],
                      "size": report["artifact"]["size"], "runtime_validation": "NOT_PERFORMED"}))


if __name__ == "__main__":
    main()
