"""Read-only original Turkey3 tumbleweed and native tag101 wire validation.

This reuses PackFS, the proven PSM visual reader and the read-only reference
Course SDK collision reader/serializer. It does not construct an entity,
register a body, modify DX/PSM inputs or claim native physics admission.
Only compact metadata may be published. Original hull bytes, if requested,
must stay in ignored local storage and must never enter a handoff archive.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import importlib.metadata
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

PORT = Path(__file__).resolve().parents[1]
RESEARCH = PORT.parent
DEFAULT_SDK = Path("D:/Game/Master Rallye/master-rallye-re-course")
XML_PATH = r"\TNG\DATASCENE\RACETEST\TURKEY3.XML"
XML_SHA = "7c1c274cd8403bc7fcc2b5e2e8a13e57dccc44dade53a1be57d631ea073e51ce"
PSM_PATH = r"\TNG\DATAPSM\MISC\OBJECTS\TUMBLEWEED\TUMBLWEED.PSM"
PSM_SHA = "eb959250d0bdb6fa051fb69f4a852c4789be200613eb8e90678d36a48ab54bf4"
TAG101_SHA = "27cb1089bf997a0b20d6a4f98fee9827a9089972ff6e891fce5cf34e41e01d48"
GXI_SHA = "e34ca0193956eca2d03217fb18929b6ec0a78cfe2d9d6e6a081b8b10c934fc4f"
SOURCE_ID = XML_PATH + ":list:11:egg:13:ai:0"
MATRIX_SHA = "dbb65381027ae9e1c0d3f76271b1a7bd5eca952dfc03e2094ac290686e99f7dc"
MAX_WIRE_BYTES = 64 * 1024
PROBE_RANGES = ((0x19FE98, 0x19FF14), (0x1A0058, 0x1A00E0),
                (0x27D060, 0x27D0A0), (0x244230, 0x244250),
                (0x3946E0, 0x3947B0))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_identity(data, expected, label):
    if sha(data) != expected:
        raise ValueError("Canonical source hash mismatch: " + label)


def research_modules():
    sys.dont_write_bytecode = True
    path = str(RESEARCH / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    return tuple(importlib.import_module(name) for name in
                 ("tngtool", "spline_runtime", "rigid_runtime", "water_runtime", "psbtool"))


def sdk_modules(sdk):
    sdk = Path(sdk).resolve()
    for name in ("collision.py", "collision_writer.py"):
        if not (sdk / "src/master_rallye" / name).is_file():
            raise ValueError("Required read-only Course SDK dependency missing: " + name)
    sys.dont_write_bytecode = True
    sdk_src = str(sdk / "src")
    if sdk_src not in sys.path:
        sys.path.insert(0, sdk_src)
    collision = importlib.import_module("master_rallye.collision")
    writer = importlib.import_module("master_rallye.collision_writer")
    for module in (collision, writer):
        if not Path(module.__file__).resolve().is_relative_to(sdk / "src"):
            raise ValueError("Already imported Course SDK differs from explicitly selected SDK")
    return collision, writer


def validate_native_wire(raw, sdk, expected_sha=None):
    """Strict structural reparse + exact existing serializer, no native calls.

    Bytes start at the outer u32 tag. Native FUN_0057CE60 reads the payload
    after dispatch has consumed that tag; wire[4:] is the bounded reader input.
    Matching this byte grammar does not prove prototype registration/lifetime.
    """
    if not isinstance(raw, bytes) or not 108 <= len(raw) <= MAX_WIRE_BYTES:
        raise ValueError("Unsupported bounded tag101 wire size")
    if expected_sha is not None:
        checked_identity(raw, expected_sha, "tag101")
    if struct.unpack_from("<I", raw)[0] != 101:
        raise ValueError("Expected exact tag101 dispatch word")
    collision, writer = sdk_modules(sdk)
    parsed = collision.parse_collision_sections(raw, source="<private original PS2 tag101>", strict=True)
    hull = parsed.convex_hull
    if (hull is None or parsed.errors or parsed.tag_ids != (101,)
            or parsed.unparsed_data or parsed.end_offset != len(raw)):
        raise ValueError("Tag101 must consume the entire bounded stream without a trailer")
    if hull.base_scalar <= 0 or not math.isfinite(hull.base_scalar):
        raise ValueError("Positive finite source base scalar required")
    if writer.serialize_tag101(hull) != raw:
        raise ValueError("Existing PC tag101 serializer changed original bytes")
    return hull


def wire_accounting(hull):
    """Precise native counted-stream spans; no geometry arrays in metadata."""
    start = hull.tag_offset
    rows = [{"section": "dispatch_tag", "wire_offset": 0, "bytes": 4}]

    def add(name, begin, end):
        rows.append({"section": name, "wire_offset": begin - start,
                     "bytes": end - begin})

    def geometry(name, block):
        add(name + ".counts", block.offset, block.vertex_data_offset)
        add(name + ".xyz_f32", block.vertex_data_offset, block.triangle_data_offset)
        add(name + ".triangles_i32", block.triangle_data_offset, block.end_offset)

    geometry("base_geometry", hull.base_geometry)
    add("base_scalar_f32", hull.base_scalar_offset, hull.base_scalar_offset + 4)
    for name, rep in (("representation_a", hull.representation_a),
                      ("representation_b", hull.representation_b)):
        geometry(name + ".geometry_a", rep.geometry_a)
        geometry(name + ".geometry_b", rep.geometry_b)
        add(name + ".referenced_count_and_indices", rep.referenced_vertex_count_offset,
            rep.edge_count_offset)
        add(name + ".edge_count_and_pairs", rep.edge_count_offset, rep.face_count_offset)
        add(name + ".face_count_and_descriptors", rep.face_count_offset,
            rep.edge_face_adjacency_offset)
        add(name + ".edge_face_adjacency", rep.edge_face_adjacency_offset, rep.face_loop_offset)
        add(name + ".counted_face_edge_loops", rep.face_loop_offset, rep.face_scalar_offset)
        add(name + ".face_area_scalars_f32", rep.face_scalar_offset, rep.end_offset)
    cursor = 0
    for row in rows:
        if row["wire_offset"] != cursor or row["bytes"] < 0:
            raise ValueError("Non-contiguous native wire accounting")
        cursor += row["bytes"]
    if cursor != len(hull.raw):
        raise ValueError("Native wire accounting does not cover the complete hull")
    return rows


def raw_output_path(path):
    resolved = Path(path).resolve()
    roots = (PORT / ".assets/rigid", RESEARCH / "data/rigid-port1")
    if not any(resolved.is_relative_to(root.resolve()) and resolved != root.resolve()
               for root in roots):
        raise ValueError("Original hull bytes must remain under ignored .assets/rigid or data/rigid-port1")
    return resolved


def visual_attribute_summary(scene):
    """Original attribute byte hashes, without exporting the mesh arrays."""
    normals, uv, controls, colors, lengths = bytearray(), bytearray(), [], [], []
    for index in range(scene.vertex_count):
        at = 32 + 52 * index
        normal = struct.unpack_from("<3f", scene.payload, at)
        uv_values = struct.unpack_from("<4f", scene.payload, at + 20)
        if not all(math.isfinite(value) for value in (*normal, *uv_values)):
            raise ValueError("Original visual normal/UV contains non-finite values")
        normals.extend(scene.payload[at:at + 12])
        uv.extend(scene.payload[at + 20:at + 36])
        controls.append(struct.unpack_from("<I", scene.payload, at + 12)[0])
        colors.append(struct.unpack_from("<I", scene.payload, at + 16)[0])
        lengths.append(math.sqrt(sum(value * value for value in normal)))
    return {"normal_xyz_f32_sha256": sha(bytes(normals)), "uv_4f32_sha256": sha(bytes(uv)),
            "normal_length_host_diagnostic_range": [min(lengths), max(lengths)],
            "control_u32_sha256": sha(b"".join(struct.pack("<I", value) for value in controls)),
            "control_u32_unique_count": len(set(controls)),
            "control_bit0_set_source_vertex_count": sum(bool(value & 1) for value in controls),
            "color_word_u32_counts": {"0x%08x" % key: count for key, count in sorted(Counter(colors).items())},
            "color_conversion": "Original raw u32 retained; any private PC diffuse conversion requires an explicit render contract",
            "suppression": "Newest source strip vertex control bit0; winding/live culling remain separate"}


def verify_r5900_probe(elf, probe):
    """Cross-check a read-only EER listing against canonical ELF/Rabbitizer.

    ELF/PT_LOAD parsing delegates to the independent REVALIDATION2 verifier.
    This does not accept generic MIPS listings or substitute instruction bytes.
    """
    research_modules()
    from spline_runtime import ELF_SHA
    sys.path.insert(0, str(RESEARCH / "revalidation2/tools"))
    from verify_r5900_revalidation2 import parse_elf32_le, va_to_offset
    import rabbitizer
    data, listed = Path(elf).read_bytes(), Path(probe).read_bytes()
    checked_identity(data, ELF_SHA, "R5900 ELF")
    header = parse_elf32_le(data)
    text = listed.decode("utf-8-sig")
    if "LANGUAGE\tr5900:LE:32:default\n" not in text or "SHA256\t" + ELF_SHA not in text:
        raise ValueError("Probe must identify the exact original R5900 Ghidra program")
    rows = {}
    expected = {va for start, end in PROBE_RANGES for va in range(start, end, 4)}
    for line in text.splitlines():
        if not line.startswith("INS\t"):
            continue
        _, va_text, raw_text, ghidra = line.split("\t", 3)
        va, raw = int(va_text, 16), bytes.fromhex(raw_text)
        if len(raw) != 4 or va not in expected or va in rows:
            raise ValueError("Unexpected or duplicate R5900 instruction span")
        offset = va_to_offset(va, 4, header["load_segments"])
        if data[offset:offset + 4] != raw:
            raise ValueError("Ghidra bytes differ from canonical ELF")
        word = int.from_bytes(raw, "little")
        decoded = rabbitizer.Instruction(word, va, rabbitizer.InstrCategory.R5900)
        if not decoded.isValid():
            raise ValueError("Rabbitizer rejected original R5900 instruction")
        rows[va] = {"va": "0x%08x" % va, "original_word": "0x%08x" % word,
                    "rabbitizer_r5900": str(decoded), "ghidra_r5900": ghidra}
    if set(rows) != expected:
        raise ValueError("Ghidra R5900 probe is incomplete")
    compact = [rows[va] for va in sorted(rows)
               if 0x1A0058 <= va < 0x1A00C4 or 0x27D06C <= va < 0x27D098
               or 0x244230 <= va < 0x244250]
    return {"canonical_elf_sha256": ELF_SHA, "language": "r5900:LE:32:default",
            "compiler": "default", "ghidra": "12.1.4",
            "rabbitizer": importlib.metadata.version("rabbitizer"),
            "rabbitizer_category": "InstrCategory.R5900", "elf": header,
            "checked_original_words": len(rows), "byte_mismatches": 0,
            "invalid_r5900_words": 0, "original_probe_sha256": sha(listed),
            "ghidra_processing": "Existing EER project read-only; -noanalysis; no edits or surrogate bytes",
            "short_original_instruction_windows": compact, "runtime_validation": "NOT_PERFORMED"}


def prepare(ps2_root, sdk, native_wire=None):
    t, s, r, w, p = research_modules()
    corpus = s.Corpus(Path(ps2_root))

    def extract(path):
        entries = [e for e in corpus.manifest["entries"]
                   if t.logical_path(e["path"]).upper() == t.logical_path(path).upper()]
        if len(entries) != 1:
            raise ValueError("Missing or ambiguous exact original resource: " + path)
        return t.read_payload(entries[0], corpus.directory / "TNG.000")

    xml, xml_provenance = extract(XML_PATH)
    model, model_provenance = extract(PSM_PATH)
    checked_identity(xml, XML_SHA, XML_PATH)
    checked_identity(model, PSM_SHA, PSM_PATH)
    authored = r.parse_authored(xml, XML_PATH)
    records = authored["records"]
    if len(records) != 6 or any(row["family"] != "tumbleweed" for row in records):
        raise ValueError("Turkey3 requires the six exact authored source records")
    selected = [row for row in records if row["source_id"] == SOURCE_ID]
    if len(selected) != 1 or selected[0]["matrix_sha256"] != MATRIX_SHA:
        raise ValueError("Selected original Turkey3 source placement differs")
    for row in records:
        if row["resolved"] != dict(mass=5.0, moi=(2.0, 2.0, 2.0),
                                   trigger_distance=5.0, casts_shadow=True):
            raise ValueError("Original tumbleweed parameter contract differs")
    scene = w.decode_scene(model, terminator=101)
    inspection = r.inspect_model(model, PSM_PATH, sdk)
    if (scene.end != 5203 or len(model) != 9819 or scene.vertex_count != 96
            or len(scene.meshes) != 1
            or scene.meshes[0]["material"] != "bigshrub $shader(treeblend)"
            or inspection["visual"]["nonsuppressed_nondegenerate_triangles"] != 48):
        raise ValueError("Original tumbleweed visual/tag101 boundary differs")
    wire = model[scene.end:-4]
    hull = validate_native_wire(wire, sdk, TAG101_SHA)
    counts = [(rep.geometry_a.vertex_count, rep.geometry_a.triangle_count)
              for rep in (hull.representation_a, hull.representation_b)]
    if counts != [(8, 12), (26, 48)]:
        raise ValueError("Original tumbleweed convex A/B topology differs")
    mesh = scene.meshes[0]
    texture_ref = mesh["textures"]
    if len(texture_ref) != 1 or texture_ref[0]["slot"] != 0:
        raise ValueError("Original visual material texture slots differ")
    texture_path = ("\\TNG\\DATAPSM\\" + texture_ref[0]["name"] + ".GXI").upper()
    texture_bytes, texture_provenance = extract(texture_path)
    checked_identity(texture_bytes, GXI_SHA, texture_path)
    texture = p.parse_gxi(texture_bytes)
    if (texture["width"], texture["height"], len(texture_bytes)) != (64, 64, 16392):
        raise ValueError("Original tumbleweed texture format/dimensions differ")
    if native_wire is not None:
        output = raw_output_path(native_wire)
        output.parent.mkdir(parents=True, exist_ok=True)
        # Do not replace even an old private candidate without explicit caller action.
        with output.open("xb") as handle:
            handle.write(wire)
    return {
        "schema": "ps2-turkey3-tumbleweed-source-contract-v1",
        "evidence_grade": "CONFIRMED_BY_BOTH",
        "canonical_inputs": corpus.provenance,
        "scene": {"resource": XML_PATH, "sha256": XML_SHA, "packfs": xml_provenance,
                  "authored_record_count": 6, "live_instance_count": "UNKNOWN"},
        "selected_source": selected[0],
        "remaining_authored_source_ids": [row["source_id"] for row in records if row != selected[0]],
        "model": {"resource": PSM_PATH, "sha256": PSM_SHA, "bytes": len(model),
                  "packfs": model_provenance, "visual": inspection["visual"],
                  "mesh": mesh, "coordinate_frame": "MODEL_LOCAL",
                  "normal_offset": 0, "control_offset": 12, "rgba_offset": 16,
                  "uv_offset": 20, "position_offset": 36, "source_vertex_stride": 52,
                  "attributes": visual_attribute_summary(scene),
                  "unknown_fields": "All opaque mesh words/flags remain literal; no runtime reinterpretation"},
        "texture": {"resource": texture_path, "packfs": texture_provenance, "gxi": texture,
                    "active_draw_binding": "UNKNOWN; original material reference is confirmed"},
        "native_collision_wire": {
            "source_psm_tag_offset": scene.end, "source_psm_end_exclusive": len(model) - 4,
            "bytes_with_tag": len(wire), "sha256_with_tag": sha(wire),
            "bytes_reader_payload": len(wire) - 4, "sha256_reader_payload": sha(wire[4:]),
            "native_reader_input": "wire[4:] after tag101 dispatch; do not feed the u32 tag twice",
            "reader": "original PC 0x0057CE60", "representation_reader": "original PC 0x0057D140",
            "geometry_reader": "original PC 0x0057D640",
            "strict_sdk_parse": "PASS", "canonical_sdk_serializer_byte_identity": "PASS",
            "wire_accounting": wire_accounting(hull), "collision": r.shape_summary(hull),
            "transform_policy": "Keep all hull coordinates MODEL_LOCAL; apply original Egg/body pose once",
            "normal_policy": "Tag101 stores topology/areas, not the visual normal array; preserve all lists",
            "registration": "UNKNOWN; round-trip is not live native prototype admission",
            "replacement_hay_hull": False,
        },
        "physics_parameters": {"mass": 5.0, "local_moi_diagonal": [2.0, 2.0, 2.0],
                               "trigger_distance_authored": 5.0, "casts_shadow_authored": True,
                               "initial_pose": "Authored row-major en3d matrix; height may change at native initial placement",
                               "integrator_ported": False, "wind_claim": "NOT_FOUND_IN_TRACED_OWNER_OR_GRAVITY_CALLBACK"},
        "runtime_validation": "NOT_PERFORMED",
        "remaining_gates": ["Owned bounded native stream ABI", "Private prototype/resource registration",
                            "Safe installed-backend attachment", "Physics-thread admission",
                            "Cache invalidation and teardown", "Observed PC vehicle contact",
                            "Live visual pose synchronization", "Source strip winding/texture-state runtime validation"],
    }, wire


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ps2-root", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native-wire", type=Path)
    parser.add_argument("--elf", type=Path)
    parser.add_argument("--r5900-probe", type=Path)
    args = parser.parse_args()
    if bool(args.elf) != bool(args.r5900_probe):
        raise ValueError("Both --elf and --r5900-probe are required for independent instruction verification")
    sdk_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.sdk_root, text=True).strip()
    sdk_status = subprocess.check_output(["git", "status", "--porcelain"], cwd=args.sdk_root, text=True).strip()
    if sdk_status:
        raise ValueError("Read-only Course SDK contains changes; refuse an unrecorded parser version")
    report, _wire = prepare(args.ps2_root, args.sdk_root, args.native_wire)
    if args.elf is not None:
        report["r5900_revalidation"] = verify_r5900_probe(args.elf, args.r5900_probe)
    report["course_sdk"] = {"head": sdk_head, "status": "CLEAN", "read_only": True,
                            "file_sha256": {name: sha((args.sdk_root / "src/master_rallye" / name).read_bytes())
                                            for name in ("collision.py", "collision_writer.py")}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.output), "tag101_sha256": TAG101_SHA,
                      "native_admission": "NOT_PERFORMED"}, sort_keys=True))


if __name__ == "__main__":
    main()
