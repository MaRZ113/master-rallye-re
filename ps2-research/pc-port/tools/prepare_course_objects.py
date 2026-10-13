"""Prepare the private Turkey3 source-geometry preview from canonical PackFS.

This writes no playable course asset. Original mesh/texture content may only be
written to ignored pc-port/.assets/course-objects/Turkey3Puddles.ps2obj.
The material is a static source-data preview, not a reconstructed PS2 draw.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

PORT = Path(__file__).resolve().parents[1]
RESEARCH = PORT.parent
MAGIC = b"PS2OBJ01"
VERSION = 1
HEADER = struct.Struct("<8s4I32s32s")
MESH = struct.Struct("<4I")
VERTEX = struct.Struct("<3fI2f")
PSM_PATH = r"\TNG\DATAPSM\COURSE\TURKEY3\TURKEY3.PSM"
PSM_SHA = "dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc"
GXI_PATH = r"\TNG\DATAPSM\COURSE\TURKEY3\WATER-TGA.GXI"
GXI_SHA = "65a8318d8c432764c91d56b53b843f8096b4629d3f53894d4d6d5caf46945d34"
MATERIAL = "water $surfacetype(water) $shader(puddle)"
ASSET_RELATIVE = Path(".assets/course-objects/Turkey3Puddles.ps2obj")
GEOMETRY_KIND = "SOURCE_GEOMETRY_STATIC_MATERIAL_PREVIEW"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def argb_from_source(word):
    """Authored packed 0xRRGGBBAA -> D3DCOLOR 0xAARRGGBB; no alpha remap."""
    if not isinstance(word, int) or not 0 <= word <= 0xffffffff:
        raise ValueError("Packed source color must be uint32")
    return ((word & 0xff) << 24) | (word >> 8)


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


def serialize_artifact(meshes, vertices, rgba_pixels, psm_sha=PSM_SHA, gxi_sha=GXI_SHA):
    """Versioned bounded format; synthetic inputs are allowed for focused tests."""
    if not 0 < len(meshes) <= 1024 or not 0 < len(vertices) <= 1000000:
        raise ValueError("Artifact mesh/vertex budget outside supported bounds")
    if len(rgba_pixels) != 64 * 64 * 4:
        raise ValueError("Artifact primary texture must contain 64x64 RGBA pixels")
    result = bytearray(HEADER.pack(MAGIC, VERSION, len(meshes), len(vertices),
                                  len(rgba_pixels), _hash_bytes(psm_sha), _hash_bytes(gxi_sha)))
    next_vertex = 0
    for mesh in meshes:
        values = tuple(mesh[k] for k in ("node_offset", "material_offset", "first_vertex", "vertex_count"))
        if any(not isinstance(v, int) or not 0 <= v <= 0xffffffff for v in values):
            raise ValueError("Mesh fields must be uint32")
        node, material, first, count = values
        if material <= node or first != next_vertex or not count or count % 3:
            raise ValueError("Mesh table must cover contiguous complete triangle lists")
        next_vertex += count
        if next_vertex > len(vertices):
            raise ValueError("Mesh range outside vertex array")
        result.extend(MESH.pack(*values))
    if next_vertex != len(vertices):
        raise ValueError("Mesh table does not cover complete vertex array")
    for vertex in vertices:
        if len(vertex) != 6 or not isinstance(vertex[3], int) or not 0 <= vertex[3] <= 0xffffffff:
            raise ValueError("Preview vertex must contain XYZ, ARGB and original UVxy")
        if not all(math.isfinite(v) for v in (vertex[0], vertex[1], vertex[2], vertex[4], vertex[5])):
            raise ValueError("Non-finite preview vertex")
        try:
            result.extend(VERTEX.pack(*vertex))
        except (OverflowError, struct.error) as error:
            raise ValueError("Preview vertex outside float32/uint32 format") from error
    result.extend(rgba_pixels)
    return bytes(result)


def validate_artifact(data):
    """Independent structural readback before publishing the private artifact."""
    if len(data) < HEADER.size:
        raise ValueError("Truncated artifact header")
    magic, version, meshes, vertices, texture_bytes, psm, gxi = HEADER.unpack_from(data)
    if magic != MAGIC or version != VERSION:
        raise ValueError("Unsupported artifact magic/version")
    if not 0 < meshes <= 1024 or not 0 < vertices <= 1000000 or texture_bytes != 16384:
        raise ValueError("Unsupported artifact count/texture budget")
    expected = HEADER.size + meshes * MESH.size + vertices * VERTEX.size + texture_bytes
    if len(data) != expected:
        raise ValueError("Artifact size does not match declared sections")
    rows, next_vertex, pos = [], 0, HEADER.size
    for _ in range(meshes):
        node, material, first, count = MESH.unpack_from(data, pos)
        pos += MESH.size
        if material <= node or first != next_vertex or not count or count % 3:
            raise ValueError("Artifact has invalid mesh ownership/ranges")
        next_vertex += count
        if next_vertex > vertices:
            raise ValueError("Artifact mesh range exceeds vertex array")
        rows.append(dict(node_offset=node, material_offset=material, first_vertex=first, vertex_count=count))
    if next_vertex != vertices:
        raise ValueError("Artifact mesh table does not cover vertex array")
    minima, maxima = [math.inf] * 3, [-math.inf] * 3
    for _ in range(vertices):
        vertex = VERTEX.unpack_from(data, pos)
        pos += VERTEX.size
        if not all(math.isfinite(v) for v in (vertex[0], vertex[1], vertex[2], vertex[4], vertex[5])):
            raise ValueError("Artifact contains non-finite XYZ/UV")
        for axis in range(3):
            minima[axis] = min(minima[axis], vertex[axis])
            maxima[axis] = max(maxima[axis], vertex[axis])
    return {"size": len(data), "sha256": sha(data), "mesh_count": meshes,
            "vertex_count": vertices, "triangle_count": vertices // 3,
            "texture_bytes": texture_bytes, "psm_sha256": psm.hex(), "gxi_sha256": gxi.hex(),
            "bounds": {"min": minima, "max": maxima}, "meshes": rows,
            "layout": {"header_size": HEADER.size, "mesh_record_size": MESH.size,
                       "vertex_record_size": VERTEX.size, "mesh_table_offset": HEADER.size,
                       "vertices_offset": HEADER.size + meshes * MESH.size,
                       "texture_offset": pos}}


def asset_path(path, port_root=PORT):
    port = Path(port_root).resolve()
    expected = port / ASSET_RELATIVE
    candidate = port
    for part in ASSET_RELATIVE.parts:
        candidate = candidate / part
        if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
            raise ValueError("Refusing linked course-object output components")
    path = Path(path).resolve()
    if path != expected or not path.is_relative_to(port):
        raise ValueError("Original geometry output must be exactly ignored pc-port/" + ASSET_RELATIVE.as_posix())
    if path.exists() and (path.is_symlink() or not path.is_file() or path.stat().st_nlink > 1):
        raise ValueError("Refusing linked/nonregular original geometry output")
    return path


def collect_preview_vertices(scene, mesh):
    """Preserve source strips, ADC suppression, raw UVxy and packed source tint.

    Consecutive source-triple ordering is retained. Runtime parity/strip-flag
    culling is unresolved; the independently configured preview uses CULL_NONE.
    """
    sys.path.insert(0, str(RESEARCH / "tools"))
    import water_runtime as w
    vertices, suppressed, degenerate = [], 0, 0
    for strip in mesh["strips"]:
        for newest in range(strip["start"] + 2, strip["start"] + strip["count"]):
            if scene.control(newest) & 1:
                suppressed += 1
                continue
            indices = (newest - 2, newest - 1, newest)
            positions = tuple(scene.position(i) for i in indices)
            if w.area_normal(positions)[0] <= 1e-7:
                degenerate += 1
                continue
            for index, position in zip(indices, positions):
                source_at = 32 + index * 52
                color = struct.unpack_from("<I", scene.payload, source_at + 16)[0]
                uv = struct.unpack_from("<2f", scene.payload, source_at + 20)
                if not all(math.isfinite(v) for v in uv):
                    raise ValueError("Non-finite original primary UV")
                vertices.append((*position, argb_from_source(color), *uv))
    return vertices, {"adc_suppressed": suppressed, "diagnostic_degenerate": degenerate}


def prepare(ps2_root, asset_out):
    sys.path.insert(0, str(RESEARCH / "tools"))
    import tngtool as t
    import water_runtime as w
    import psbtool as p
    from course_delta import EXPECTED
    ps2_root = Path(ps2_root)
    output = asset_path(asset_out)
    w.verify_inputs(ps2_root)
    manifest, _ = t.load_pak(ps2_root / "TNG.PAK")

    def extract(path):
        entries = [e for e in manifest["entries"] if e["kind"] == "file"
                   and t.logical_path(e["path"]) == t.logical_path(path)]
        if len(entries) != 1:
            raise ValueError("Missing/nonunique canonical resource: " + path)
        return t.read_payload(entries[0], ps2_root / "TNG.000")

    payload, psm_provenance = extract(PSM_PATH)
    gxi, gxi_provenance = extract(GXI_PATH)
    if sha(payload) != PSM_SHA or sha(gxi) != GXI_SHA:
        raise ValueError("Original Turkey3 resource hash mismatch")
    texture = p.parse_gxi(gxi)
    if texture["width"] != 64 or texture["height"] != 64 or len(gxi) != 16392:
        raise ValueError("Unsupported original primary GXI dimensions")
    scene = w.decode_scene(payload)
    selected = [m for m in scene.meshes if m["classification"]["water_mode"] == 9]
    if len(selected) != 17:
        raise ValueError("Canonical Turkey3 puddle owner count changed")
    meshes, vertices, evidence = [], [], []
    for mesh in selected:
        if mesh["material"] != MATERIAL or len(mesh["textures"]) != 1 or mesh["textures"][0]["slot"] != 0:
            raise ValueError("Unexpected Turkey3 source material/texture slots")
        if t.logical_path(mesh["textures"][0]["name"]) != t.logical_path(r"Course\turkey3\water-tga"):
            raise ValueError("Unexpected original Turkey3 primary texture reference")
        values, excluded = collect_preview_vertices(scene, mesh)
        row = {"node_offset": mesh["node_offset"], "material_offset": mesh["material_offset"],
               "first_vertex": len(vertices), "vertex_count": len(values)}
        meshes.append(row)
        vertices.extend(values)
        evidence.append({**row, "path": mesh["path"], "material": mesh["material"],
                         "texture_slots": mesh["textures"], "strip_count": len(mesh["strips"]),
                         "source_strip_offsets": [st["offset"] for st in mesh["strips"]],
                         "excluded": excluded, "triangle_count": len(values) // 3})
    if len(vertices) != 2235 or sum(e["strip_count"] for e in evidence) != 51:
        raise ValueError("Canonical Turkey3 selected geometry counts changed")
    artifact = serialize_artifact(meshes, vertices, gxi[8:])
    info = validate_artifact(artifact)
    if info["size"] != 70384:
        raise ValueError("Canonical private artifact size differs from format contract")
    if output.exists() and output.read_bytes() != artifact:
        raise ValueError("Refusing to overwrite a different local course-object artifact")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(artifact)
    return {"schema_version": 1, "phase": "PS2-COURSE-OBJECTS1", "course": "TURKEY3",
            "geometry_kind": GEOMETRY_KIND, "coordinate_frame": "GAME_SOURCE_IDENTITY",
            "source_identity": {name: {"size": (ps2_root / name).stat().st_size, "sha256": value}
                                for name, value in EXPECTED.items()},
            "source_psm": {"path": PSM_PATH, "provenance": psm_provenance,
                           "visual_vertex_count": scene.vertex_count, "visual_tree_end": scene.end},
            "source_texture": {"path": GXI_PATH, "provenance": gxi_provenance, "format": texture,
                               "stored_row_order": "PRESERVED", "artifact_channel_order": "RGBA"},
            "artifact": {**info, "local_relative_path": ASSET_RELATIVE.as_posix(),
                         "source_meshes": evidence},
            "source_vertex_policy": {"xyz": "ORIGINAL_FLOAT32_UNCHANGED", "uv": "ORIGINAL_FIRST_TWO_FLOAT32",
                                     "color": "SOURCE_0xRRGGBBAA_TO_D3DCOLOR_ARGB_NO_REMAP",
                                     "winding": "CONSECUTIVE_SOURCE_TRIPLES; runtime parity UNKNOWN",
                                     "adc": "NEWEST_CONTROL_BIT0_SUPPRESSES", "area_cutoff": 1e-7},
            "material_policy": "STATIC_PRIMARY_SOURCE_TEXTURE_PREVIEW; NOT_PS2_MODE9_PARITY",
            "evidence_grade": "CONFIRMED_BY_BOTH", "runtime_validation": "NOT_PERFORMED",
            "limitations": ["Source UV/color are rewritten by PS2 mode9 at runtime; not reproduced here",
                            "Secondary WATERSURFACE2 pass and global basis are not implemented",
                            "405 source centroids above and340 below nearest covering PC surface in frozen WATER1 comparison",
                            "Original XYZ is never lifted; parts may remain occluded by different PC terrain",
                            "Authored source meshes are not proved simultaneously visible PS2 draws",
                            "No collision data or playable course asset is generated"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ps2-input-root", type=Path, required=True)
    parser.add_argument("--asset-out", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args()
    report_out = args.report_out.resolve()
    if not report_out.is_relative_to((PORT / "docs/course-objects1").resolve()):
        parser.error("Compact reports must stay under pc-port/docs/course-objects1")
    if report_out.exists() and (report_out.is_symlink() or not report_out.is_file() or report_out.stat().st_nlink > 1):
        parser.error("Refusing linked/nonregular compact report output")
    report = prepare(args.ps2_input_root, args.asset_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"asset": str(args.asset_out), "sha256": report["artifact"]["sha256"],
                      "size": report["artifact"]["size"], "triangles": report["artifact"]["triangle_count"],
                      "runtime_validation": "NOT_PERFORMED"}))


if __name__ == "__main__":
    main()
