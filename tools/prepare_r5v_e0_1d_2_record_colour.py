"""Prepare the isolated R5V-E0.1d.2 VehicleRecord-tail colour diagnostic.

The only accepted input is the previously runtime-confirmed ID25 Trooper /
SmallCarSheet29 candidate. This changes the four initializer immediates for
record25's tail vector; the alpha immediate already equals 1.0 and stays intact.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA256 = "e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df"
BASELINE_REL = Path(
    "research-output/r5v_e0_1b/runtime-test/trooper-smallsheet29-baseline/"
    "MRallye_slot25_trooper_smallsheet29_baseline.exe"
)
BASELINE_MANIFEST_REL = BASELINE_REL.with_name("patch-manifest.json")
OUTPUT_DIR_REL = Path("research-output/r5v_e0_1d_2/runtime-test")
OUTPUT_NAME = "MRallye_slot25_trooper_redrecordcolour_test.exe"

SOURCE_RGBA_BITS = ("3d8b1c04", "3f092d67", "3ef74e40", "3f800000")
DIAGNOSTIC_RGBA_BITS = ("3f800000", "00000000", "00000000", "3f800000")
STACK_IMMEDIATE_FIELDS = (
    (6, 0x00, 10),
    (14, 0x04, 18),
    (22, 0x08, 26),
    (30, 0x0C, 34),
)


class PatchError(ValueError):
    """Input bytes or manifest do not match the reviewed baseline."""


def _word_bytes(bits: str) -> bytes:
    return int(bits, 16).to_bytes(4, "little")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rewrite_tail_stub(stub: bytes) -> tuple[bytes, list[int]]:
    """Replace only the ID25 initializer's four verified stack immediates."""
    if len(stub) != 94:
        raise PatchError(f"Expected the 94-byte reviewed initializer stub, got {len(stub)}")
    if stub[:6] != bytes.fromhex("56 8B F1 83 EC 10"):
        raise PatchError("Unexpected ID25 stub prologue")

    out = bytearray(stub)
    permitted_offsets: set[int] = set()
    for (instruction_offset, stack_displacement, immediate_offset), expected, replacement in zip(
        STACK_IMMEDIATE_FIELDS, SOURCE_RGBA_BITS, DIAGNOSTIC_RGBA_BITS
    ):
        if stub[instruction_offset:instruction_offset + 4] != bytes(
            (0xC7, 0x44, 0x24, stack_displacement)
        ):
            raise PatchError(f"Unexpected float store at stub +0x{instruction_offset:X}")
        old = _word_bytes(expected)
        if stub[immediate_offset:immediate_offset + 4] != old:
            raise PatchError(f"Unexpected source float at stub +0x{immediate_offset:X}")
        out[immediate_offset:immediate_offset + 4] = _word_bytes(replacement)
        permitted_offsets.update(range(immediate_offset, immediate_offset + 4))

    changed = [i for i, (before, after) in enumerate(zip(stub, out)) if before != after]
    if not set(changed).issubset(permitted_offsets):
        raise PatchError("Rewrite changed bytes outside the four float immediates")
    if out[STACK_IMMEDIATE_FIELDS[-1][2]:STACK_IMMEDIATE_FIELDS[-1][2] + 4] != _word_bytes("3f800000"):
        raise PatchError("The alpha immediate must remain 1.0")
    return bytes(out), changed


def _read_baseline_manifest(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PatchError(f"Cannot read baseline manifest: {path}") from exc


def build_candidate(root: Path = ROOT) -> tuple[Path, dict]:
    source_path = root / BASELINE_REL
    source_manifest_path = root / BASELINE_MANIFEST_REL
    try:
        source = source_path.read_bytes()
    except OSError as exc:
        raise PatchError(f"Cannot read the approved baseline candidate: {source_path}") from exc
    actual_source_sha = sha256(source)
    if actual_source_sha != BASELINE_SHA256:
        raise PatchError(f"Baseline SHA-256 mismatch: {actual_source_sha}")

    source_manifest = _read_baseline_manifest(source_manifest_path)
    record = source_manifest.get("record25", {})
    if (source_manifest.get("phase") != "R5V-E0.1a"
            or source_manifest.get("patched_sha256") != BASELINE_SHA256
            or record.get("id") != 25
            or record.get("class") != 2
            or record.get("name") != "Trooper"
            or record.get("smallcarsheet_index") != 29
            or tuple(str(x).lower() for x in record.get("float_bits", ())) != SOURCE_RGBA_BITS):
        raise PatchError("Baseline manifest does not describe the approved Trooper/29 profile")

    stub_op = next(
        (op for op in source_manifest.get("operations", []) if op.get("name") == "slot25_stub"),
        None,
    )
    injection = source_manifest.get("injection", {})
    if stub_op is None or int(stub_op.get("file_offset", -1)) != int(injection.get("entry_va", 0)) - int(
        source_manifest.get("image_base", 0)
    ):
        raise PatchError("Baseline manifest has inconsistent ID25 stub addresses")
    stub_offset = int(stub_op["file_offset"])
    source_stub = bytes.fromhex(stub_op["replacement_bytes"])
    if len(source_stub) != int(injection.get("size", -1)):
        raise PatchError("Baseline stub size does not match its manifest")
    if source[stub_offset:stub_offset + len(source_stub)] != source_stub:
        raise PatchError("Baseline stub bytes do not match their manifest")

    new_stub, relative_changes = rewrite_tail_stub(source_stub)
    candidate = bytearray(source)
    candidate[stub_offset:stub_offset + len(new_stub)] = new_stub
    candidate_bytes = bytes(candidate)
    actual_changes = [i for i, (before, after) in enumerate(zip(source, candidate_bytes)) if before != after]
    expected_changes = [stub_offset + i for i in relative_changes]
    if actual_changes != expected_changes:
        raise PatchError("Whole-file diff includes bytes outside the reviewed colour immediates")

    output_dir = root / OUTPUT_DIR_REL
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_NAME
    manifest_path = output_dir / "patch-manifest.json"
    diff_path = output_dir / "binary-diff.txt"
    instructions_path = output_dir / "TEST_INSTRUCTIONS.txt"
    for path in (output_path, manifest_path, diff_path, instructions_path):
        if path.exists():
            raise PatchError(f"Refusing to overwrite an existing diagnostic artifact: {path}")

    output_sha = sha256(candidate_bytes)
    output_path.write_bytes(candidate_bytes)
    operations = []
    for lane, ((_, displacement, immediate_offset), before, after) in enumerate(
        zip(STACK_IMMEDIATE_FIELDS, SOURCE_RGBA_BITS, DIAGNOSTIC_RGBA_BITS)
    ):
        operations.append({
            "lane": lane,
            "record_offset": f"0x{0x24 + lane * 4:02X}",
            "stack_displacement": f"0x{displacement:02X}",
            "file_offset": f"0x{stub_offset + immediate_offset:X}",
            "original_bits": before,
            "replacement_bits": after,
            "changed": before != after,
        })
    result_manifest = {
        "phase": "R5V-E0.1d.2",
        "purpose": "ID25 record-tail red diagnostic only",
        "source": str(BASELINE_REL).replace("\\", "/"),
        "source_sha256": actual_source_sha,
        "candidate": OUTPUT_NAME,
        "candidate_sha256": output_sha,
        "candidate_size": len(candidate_bytes),
        "record25": {
            "id": 25,
            "class": 2,
            "runtime_family": "Trooper",
            "smallcarsheet_index": 29,
            "stats": [6, 6, 8, 8],
            "record_tail_offset": "0x24",
            "source_rgba_bits": list(SOURCE_RGBA_BITS),
            "diagnostic_rgba_bits": list(DIAGNOSTIC_RGBA_BITS),
        },
        "stub": {
            "file_offset": f"0x{stub_offset:X}",
            "virtual_address": f"0x{int(injection['entry_va']):X}",
            "size": len(source_stub),
            "whole_stub_unchanged_except_float_immediates": True,
        },
        "changed_file_offsets": [f"0x{x:X}" for x in actual_changes],
        "operations": operations,
        "runtime_status": "prepared; awaiting human test",
        "prohibited_changes": [
            "HUD XML", "Car0 override bypass", "registry capacity", "SmallCarSheet",
            "stats", "runtime-family name", "model/physics/collision",
        ],
    }
    manifest_path.write_text(json.dumps(result_manifest, indent=2) + "\n", encoding="utf-8")
    diff_lines = [
        "R5V-E0.1d.2 exact byte diff",
        f"source_sha256={actual_source_sha}",
        f"candidate_sha256={output_sha}",
        f"stub_file_offset=0x{stub_offset:X}",
        "Only the three RGB dword immediates differ; alpha remains 3F800000 (1.0).",
    ]
    for operation in operations:
        if operation["changed"]:
            diff_lines.append(
                f"{operation['file_offset']}: {operation['original_bits']} -> "
                f"{operation['replacement_bits']} (record +{operation['record_offset']})"
            )
    diff_path.write_text("\n".join(diff_lines) + "\n", encoding="utf-8")
    instructions_path.write_text(_test_instructions(), encoding="utf-8")
    return output_path, result_manifest


def _test_instructions() -> str:
    return """R5V-E0.1d.2 — ID25 record-colour diagnostic

Candidate: MRallye_slot25_trooper_redrecordcolour_test.exe
Pair it with the same isolated retail data and normal HUD XML used for the
runtime-confirmed Trooper / SmallCarSheet29 P0 baseline. Do not use the red XML
archive and do not use either Car0 colour-bypass executable.

The candidate changes only VehicleRecord[25]'s three RGB initializer words.
It retains ID25, T3/class 2, Trooper model/physics/collision, stats 6/6/8/8,
SmallCarSheet29 index 29, the internal name, original initializer, and alpha 1.

Run it only in a disposable copy of the game installation. In Quick Race,
select ID25 and observe the bottom Player1 progress marker. The predicted result
is that this marker changes from Astero's aquamarine to red. Confirm that the
Trooper model, Forklift SmallCarSheet29 icons, frontend stats, and opponent
marker colours remain unchanged. Do not use campaign/save progress for this
test.

Return the actual result for each observation, including crashes or any effect
outside the Player1 marker. A static trace and this candidate do not count as a
runtime PASS until that human result is reported.
"""


def main() -> None:
    output_path, manifest = build_candidate()
    print(f"candidate={output_path}")
    print(f"sha256={manifest['candidate_sha256']}")
    print(f"changed_offsets={','.join(manifest['changed_file_offsets'])}")


if __name__ == "__main__":
    main()
