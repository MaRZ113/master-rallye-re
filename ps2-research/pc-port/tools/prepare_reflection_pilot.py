"""Read-only PS2/PC source validation and local asset preparation for PORT1.

Uses existing PackFS/PSM and Course SDK readers. No game file is written.
The extracted original GXI may only be written to this port's ignored .assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

PORT = Path(__file__).resolve().parents[1]
RESEARCH = PORT.parent
ENV_SHA = "aa15159a5f3f668244dd3b1c5c7b8322d8f41ac626c3a1741222b797252ad1e4"
TATA_PSM_SHA = "9397b4b9b60567a3ac3f5e0ac752a6794b3fea9ace8c2bb524db53bb565e6c84"
TATA_DX_SHA = "45b7bfba6938e259c0ac6d79a42a878a8c66b1e53547a53a6d23343092fb34cb"
ENV_PATH = r"\TNG\DATAPSM\COMMONTEXTURES\ENVSOURCE64X64.GXI"
TATA_PATH = r"\TNG\DATAPSM\VEHICLES\TATA\CAR.PSM"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def geometry_signature(faces) -> str:
    """Same bitwise unsigned float32 position digest as the live CPU mirror."""
    hashes = []
    for face in faces:
        corners = []
        for point in face:
            corners.append(tuple(struct.unpack("<I", struct.pack("<f", 0.0 if x == 0.0 else x))[0]
                                 for x in point))
        hashes.append(sha(b"".join(struct.pack("<III", *p) for p in sorted(corners))))
    return sha("".join(sorted(hashes)).encode("ascii"))


def prepare(ps2_root: Path, pc_root: Path, sdk: Path, asset_out: Path | None):
    sys.path.insert(0, str(RESEARCH / "tools"))
    sys.path.insert(0, str(sdk / "src"))
    import tngtool as t
    import reflection_runtime as r
    import water_runtime as w
    from master_rallye.dx import parse_dx

    w.verify_inputs(ps2_root)
    from course_delta import EXPECTED
    source_identity = {name: {"size": (ps2_root / name).stat().st_size, "sha256": expected}
                       for name, expected in EXPECTED.items()}
    manifest, _ = t.load_pak(ps2_root / "TNG.PAK")
    def extract(path):
        entries = [e for e in manifest["entries"] if t.logical_path(e["path"]) == t.logical_path(path)]
        if len(entries) != 1:
            raise ValueError("Nonunique or missing canonical PackFS resource: " + path)
        return t.read_payload(entries[0], ps2_root / "TNG.000")
    env, env_provenance = extract(ENV_PATH)
    psm, psm_provenance = extract(TATA_PATH)
    if sha(env) != ENV_SHA or sha(psm) != TATA_PSM_SHA:
        raise ValueError("Canonical resource payload hash mismatch")
    if len(env) != 16392 or struct.unpack_from("<IHH", env) != (0x13039, 64, 64):
        raise ValueError("Unsupported original ENV GXI layout")
    scene = r.decode_vehicle(psm)
    mesh = next(m for m in scene.meshes if m["path"] == "root.3")
    ps2_faces, strip_control = w.mesh_triangles(scene, mesh)
    dx = pc_root / "DataGx" / "Vehicles" / "Tata" / "car.dx"
    if t.file_hash(dx) != TATA_DX_SHA:
        raise ValueError("PC protected-retail Tata CAR DX hash mismatch")
    model = parse_dx(dx)
    draw = model.physical_draws[19]
    slots = [s.value for s in draw.texture_slots]
    if slots != ["tatabon-tga", "whitepaint-tga", "Null"] or draw.index_count != 165:
        raise ValueError("Verified Tata material record differs from source contract")
    indices = model.draw_global_indices(draw)
    pc_faces = [tuple(model.vertices.positions[i] for i in indices[n:n+3])
                for n in range(0, len(indices), 3)]
    signature = geometry_signature(pc_faces)
    same_signature = []
    for d in model.physical_draws:
        ids = model.draw_global_indices(d)
        faces = [tuple(model.vertices.positions[i] for i in ids[n:n+3])
                 for n in range(0, len(ids), 3)]
        if geometry_signature(faces) == signature:
            same_signature.append(d.draw_index)
    if same_signature != [19]:
        raise ValueError("Target position signature is not unique within Tata CAR source")
    ps2_match = sum(any(w.corner_error(a, b) <= 0.001 for b in pc_faces) for a in ps2_faces)
    pc_match = sum(any(w.corner_error(a, b) <= 0.001 for b in ps2_faces) for a in pc_faces)
    if asset_out is not None:
        asset_out = asset_out.resolve()
        if not asset_out.is_relative_to((PORT / ".assets").resolve()):
            raise ValueError("Original GXI output must remain under ignored pc-port/.assets")
        if asset_out.exists() and asset_out.read_bytes() != env:
            raise ValueError("Refusing to overwrite a different local asset")
        asset_out.parent.mkdir(parents=True, exist_ok=True)
        asset_out.write_bytes(env)
    return {
        "schema_version": 1, "phase": "PS2-REFLECTION-PORT1",
        "ps2_input_identity": source_identity,
        "ps2_material": {"resource": TATA_PATH, "provenance": psm_provenance,
            "mesh_path": mesh["path"], "node_offset": mesh["node_offset"],
            "material": mesh["material"], "material_offset": mesh["material_offset"],
            "textures": mesh["textures"], "source_triangles": len(ps2_faces),
            "contract": r.material_contract(mesh["material"], mesh["textures"][1]["name"]),
            "strip_control": strip_control},
        "pc_material": {"source": "DataGx/Vehicles/Tata/car.dx", "sha256": TATA_DX_SHA,
            "record_index": draw.draw_index, "record_path": draw.record_path,
            "record_offset": draw.offset, "vertex_base": draw.vertex_base,
            "vertex_count": draw.local_vertex_max + 1, "index_start": draw.index_start,
            "index_count": draw.index_count, "source_triangles": len(pc_faces),
            "texture_slots": slots, "flags_hex": draw.flags_0x20.hex(),
            "diffuse_alpha_values": sorted({model.vertices.colors[i*4+3] for i in indices}),
            "geometry_sha256": signature, "signature_unique_in_car_dx": same_signature},
        "geometry_comparison": {"coordinates": "MODEL_LOCAL_SOURCE",
            "tolerance": 0.001, "ps2_faces_matching_pc": ps2_match,
            "pc_faces_matching_ps2": pc_match, "same_geometry_not_required": True,
            "runtime_submission": "NOT_YET_CAPTURED_FOR_THIS_PILOT"},
        "env_source": {"path": ENV_PATH, "provenance": env_provenance,
            "width": 64, "height": 64, "channel_order": "RGBA",
            "row_order": "original row order retained",
            "conversion": "BGRA; RGB=floor(original RGB*80/128); alpha=255",
            "precision": "APPROXIMATE_D3D8_IMAGE_CONVERSION",
            "dynamic_framebuffer_component": "NOT_IMPLEMENTED"},
        "evidence_grade": "CONFIRMED_BY_BOTH",
        "runtime_validation": "NOT_PERFORMED",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ps2-input-root", type=Path, required=True)
    parser.add_argument("--pc-retail-root", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--asset-out", type=Path)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.ps2_input_root, args.pc_retail_root, args.sdk_root, args.asset_out)
    if not args.report_out.resolve().is_relative_to(PORT.resolve()):
        parser.error("Compact report must remain inside pc-port")
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.report_out), "pc_geometry_sha256":
                      report["pc_material"]["geometry_sha256"],
                      "geometry_comparison": report["geometry_comparison"]}))


if __name__ == "__main__":
    main()
