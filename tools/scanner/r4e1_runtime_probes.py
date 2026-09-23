#!/usr/bin/env python3
"""Two isolated Astero R4E.1 runtime probes; outputs remain ignored."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.coords import SOURCE_AXES
from master_rallye.dx import parse_dx_bytes
from master_rallye.r4e_writer import patch_dx_attributes

EXPECTED_R4E_SOURCE_SHA256 = "b97949651ae1c0089a614beaa24f6b07bbea84735c70faf1570760a9aaa16d90"
NORMAL_DRAW = 11
ENV_DRAW = 7
NORMAL_SLOTS = ("chromebar-tga", "chrome-tga", "Null")
ENV_SLOTS = ("acamo64b-tga", "whitepaint-tga", "Null")


def rotate_source_y_90(value):
    """Right-handed +90 degree rotation about Master Rallye source +Y."""
    x, y, z = value
    return (z, y, -x)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _draw_vertices(draw):
    return range(draw.vertex_base, draw.vertex_base + draw.local_vertex_max + 1)


def _check_source(model):
    if SOURCE_AXES != "right-handed XYZ; observed vehicle up axis +Y":
        raise ValueError("source vertical-axis convention changed")
    if not model.diagnostics.validated:
        raise ValueError("source DX is not validated")
    draws = model.physical_draws
    if len(draws) <= max(NORMAL_DRAW, ENV_DRAW):
        raise ValueError("expected Astero draw IDs missing")
    normal_draw = draws[NORMAL_DRAW]
    env_draw = draws[ENV_DRAW]
    if normal_draw.draw_index != NORMAL_DRAW or normal_draw.tag != 2 or normal_draw.texture_tuple != NORMAL_SLOTS:
        raise ValueError("chrome draw identity/bindings changed")
    if env_draw.draw_index != ENV_DRAW or env_draw.tag != 2 or env_draw.texture_tuple != ENV_SLOTS:
        raise ValueError("body draw identity/bindings changed")
    normal_vertices = set(_draw_vertices(normal_draw))
    if len(normal_vertices) != 192 or min(normal_vertices) != 1820 or max(normal_vertices) != 2011:
        raise ValueError("chrome draw vertex range changed")
    for draw in draws:
        if draw.draw_index != NORMAL_DRAW and normal_vertices.intersection(_draw_vertices(draw)):
            raise ValueError(f"chrome draw vertices overlap draw {draw.draw_index}")
    if env_draw.unknown_0x24 != 7 or not env_draw.unknown_0x24 & 4:
        raise ValueError(f"body environment mask changed: {env_draw.unknown_0x24}")
    if env_draw.flags_0x20 != bytes.fromhex("00000101"):
        raise ValueError("body draw flags changed")
    return normal_draw, env_draw


def _semantic_audit(source, patch, field):
    before = parse_dx_bytes(source)
    after = parse_dx_bytes(patch.data)
    if not after.diagnostics.validated or before.local_indices != after.local_indices:
        raise ValueError("output topology validation failed")
    if before.vertices.positions != after.vertices.positions:
        raise ValueError("positions changed")
    if before.vertices.colors != after.vertices.colors:
        raise ValueError("colors changed")
    if [item.values for item in before.uv_sets] != [item.values for item in after.uv_sets]:
        raise ValueError("UVs changed")
    if before.collision.end_offset != after.collision.end_offset or source[before.collision.offset:before.collision.end_offset] != patch.data[after.collision.offset:after.collision.end_offset]:
        raise ValueError("collision bytes changed")
    if before.trailing.data != after.trailing.data:
        raise ValueError("trailing bytes changed")
    for old, new in zip(before.physical_draws, after.physical_draws):
        if old.texture_tuple != new.texture_tuple or old.flags_0x20 != new.flags_0x20:
            raise ValueError("texture references or flags changed")
        if field == "normal" and old.unknown_0x24 != new.unknown_0x24:
            raise ValueError("material mask changed")
        if field == "env" and old.draw_index != ENV_DRAW and old.unknown_0x24 != new.unknown_0x24:
            raise ValueError("unrelated material mask changed")
    if field == "env" and before.vertices.normals != after.vertices.normals:
        raise ValueError("normals changed")
    if field == "normal" and [x.field for x in patch.changes] != ["normal"] * len(patch.changes):
        raise ValueError("non-normal field patch")
    if field == "env" and [x.field for x in patch.changes] != ["material_env_bit"]:
        raise ValueError("non-env field patch")
    if patch.diff.unexpected_ranges or not patch.diff.valid:
        raise ValueError("unexpected changed byte range")
    return before, after


def _write_probe(destination: Path, patch, details: dict, instructions: str):
    if destination.exists():
        raise ValueError(f"candidate already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(patch.data)
    metadata = {
        **patch.to_dict(),
        **details,
        "candidate_path": str(destination.resolve()),
        "candidate_sha256": sha256(destination.read_bytes()),
        "unexpected_changed_range_count": len(patch.diff.unexpected_ranges),
        "runtime_status": "WAITING_FOR_HUMAN",
    }
    (destination.parent / "validation.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (destination.parent / "TEST_INSTRUCTIONS.txt").write_text(instructions, encoding="utf-8")
    return metadata


def build(source_path: Path, output: Path):
    source_path = source_path.resolve()
    output = output.resolve()
    if source_path.parent.name.casefold() != "astero" or source_path.name.casefold() != "car.dx":
        raise ValueError("probes require the original Astero/car.dx")
    source = source_path.read_bytes()
    if sha256(source) != EXPECTED_R4E_SOURCE_SHA256:
        raise ValueError("Astero source SHA-256 differs from the R4E candidate provenance; use the verified original backup")
    model = parse_dx_bytes(source, source=str(source_path))
    normal_draw, env_draw = _check_source(model)
    source_normals = model.vertices.normals
    affected = tuple(_draw_vertices(normal_draw))
    normals = list(source_normals)
    lengths_before = []
    for index in affected:
        old = source_normals[index]
        magnitude = math.sqrt(sum(x*x for x in old))
        if not math.isfinite(magnitude) or abs(magnitude - 1.0) > 1.0e-4:
            raise ValueError(f"source normal {index} is not approximately unit length")
        lengths_before.append(magnitude)
        normals[index] = rotate_source_y_90(old)
    normal_patch = patch_dx_attributes(source, normals=normals, source=str(source_path))
    before, after = _semantic_audit(source, normal_patch, "normal")
    changed_vertices = {change.identity for change in normal_patch.changes}
    if changed_vertices != set(affected):
        raise ValueError("normal patch did not change exactly all selected source vertices")
    lengths_after = []
    for index in affected:
        original = source_normals[index]
        expected = struct.unpack("<3f", struct.pack("<3f", *rotate_source_y_90(original)))
        actual = after.vertices.normals[index]
        if any(abs(a-b) > 1.0e-7 for a,b in zip(expected,actual)):
            raise ValueError(f"normal {index} does not match +90 source-Y rotation")
        old_length = lengths_before[index - affected[0]]
        new_length = math.sqrt(sum(x*x for x in actual))
        if abs(new_length - old_length) > 2.0e-6:
            raise ValueError(f"normal {index} length changed")
        lengths_after.append(new_length)
    for index in set(range(model.vertex_count)) - set(affected):
        if source_normals[index] != after.vertices.normals[index]:
            raise ValueError(f"unselected normal {index} changed")
    texture_hashes={}
    for name in (NORMAL_SLOTS[0], NORMAL_SLOTS[1], ENV_SLOTS[0], ENV_SLOTS[1]):
        path=source_path.parent/f"{name}.dxt"
        if not path.is_file():
            raise ValueError(f"missing referenced DXT: {path}")
        texture_hashes[path.name]=sha256(path.read_bytes())
    n1 = _write_probe(
        output/"N1_normal_rotation"/"car.dx",
        normal_patch,
        {
            "probe":"N1_normal_rotation",
            "source_resource":"Astero/car.dx",
            "source_sha256":sha256(source),
            "draw_id":NORMAL_DRAW,
            "draw_slots":list(normal_draw.texture_tuple),
            "source_vertex_start":affected[0],
            "source_vertex_end_inclusive":affected[-1],
            "targeted_normal_count":len(affected),
            "changed_normal_record_count":len(changed_vertices),
            "normal_transform":"right-handed +90 degrees around source +Y: (x,y,z)->(z,y,-x)",
            "source_normal_length_min_max":[min(lengths_before),max(lengths_before)],
            "output_normal_length_min_max":[min(lengths_after),max(lengths_after)],
            "unchanged_position_count":model.vertex_count,
            "unchanged_uv_set_count":len(model.uv_sets),
            "unchanged_color_byte_count":len(model.vertices.colors),
            "texture_sha256_unchanged":texture_hashes,
            "collision_preserved":True,
            "topology_preserved":True,
            "material_preserved":True,
        },
        "N1 NORMAL ROTATION — Astero race car.dx only\n"
        "1. Package this car.dx alone using the already runtime-confirmed full-tree SMA workflow.\n"
        "2. Keep game Reflections ON. Load Astero in a race.\n"
        "3. Inspect chromebar/chrome draw 11 against stock while rotating the camera/view where possible.\n"
        "4. Record: game loads? car loads? chrome geometry intact? reflection/shading orientation clearly changed? change follows edited surface? artifacts?\n"
        "Clear targeted difference confirms runtime normal writing. No clear difference remains INCONCLUSIVE and calls for a separate constant-normal probe. Crash/corruption is FAIL.\n"
    )
    env_patch = patch_dx_attributes(source, material_env={ENV_DRAW:False}, source=str(source_path))
    before, after = _semantic_audit(source, env_patch, "env")
    new_mask=after.physical_draws[ENV_DRAW].unknown_0x24
    if env_draw.unknown_0x24 != 7 or new_mask != 3:
        raise ValueError(f"unexpected environment mask transition {env_draw.unknown_0x24}->{new_mask}")
    if env_patch.diff.changed_byte_count != 1 or len(env_patch.changes) != 1:
        raise ValueError("environment probe changed more than one byte")
    if env_patch.changes[0].offset != env_draw.core_offset + 0x24:
        raise ValueError("environment mask offset mismatch")
    m1 = _write_probe(
        output/"M1_env_disable"/"car.dx",
        env_patch,
        {
            "probe":"M1_env_disable",
            "source_resource":"Astero/car.dx",
            "source_sha256":sha256(source),
            "draw_id":ENV_DRAW,
            "draw_slots":list(env_draw.texture_tuple),
            "feature_mask_offset":env_draw.core_offset+0x24,
            "old_feature_mask":env_draw.unknown_0x24,
            "new_feature_mask":new_mask,
            "changed_feature_bits":env_draw.unknown_0x24 ^ new_mask,
            "unchanged_position_count":model.vertex_count,
            "unchanged_normal_count":model.vertex_count,
            "unchanged_uv_set_count":len(model.uv_sets),
            "unchanged_color_byte_count":len(model.vertices.colors),
            "texture_sha256_unchanged":texture_hashes,
            "collision_preserved":True,
            "topology_preserved":True,
            "unknown_material_flags_preserved":True,
        },
        "M1 ENV FEATURE DISABLE — Astero race car.dx only\n"
        "1. Package this car.dx alone using the already runtime-confirmed full-tree SMA workflow.\n"
        "2. Keep game Reflections ON. Load Astero in a race.\n"
        "3. Compare body draw 7 against stock: acamo64b-tga livery should remain, whitepaint reflection contribution should disappear or change.\n"
        "4. Compare other reflective materials, including chrome, which were not edited.\n"
        "5. Record: game loads? car loads? slot0 body texture intact? targeted reflection removed? unrelated reflections unaffected? artifacts?\n"
        "A change only on draw 7 confirms the feature-bit writer. No change needs a narrow field investigation; unrelated changes need scope investigation.\n"
    )
    if sha256(source_path.read_bytes()) != EXPECTED_R4E_SOURCE_SHA256:
        raise ValueError("original DX source changed during probe generation")
    for name, expected in texture_hashes.items():
        if sha256((source_path.parent/name).read_bytes()) != expected:
            raise ValueError(f"referenced DXT changed during probe generation: {name}")
    return {"N1_normal_rotation":n1,"M1_env_disable":m1}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    results=build(args.source,args.output)
    print(json.dumps({name:{
        "source_sha256":item["source_sha256"],
        "candidate_sha256":item["candidate_sha256"],
        "changed_byte_count":item["diff"]["changed_byte_count"],
        "changed_field_count":len(item["changes"]),
        "unexpected_changed_range_count":item["unexpected_changed_range_count"],
        "runtime_status":item["runtime_status"],
    } for name,item in results.items()},indent=2))


if __name__=="__main__":
    main()
