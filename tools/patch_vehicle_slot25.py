"""Fail-closed retail Master Rallye ID25/Astero proof-of-concept patcher.

The only supported input is the unmodified retail executable with SOURCE_SHA256.
The output is a separate, local test copy; no game data is changed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import struct


SOURCE_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
IMAGE_BASE = 0x400000
STUB_VA = 0x68E2A0
HOOK_VA = 0x458D3F
INITIALIZER_VA = 0x45A0B0
STRING_CONSTRUCTOR_VA = 0x4D11D0
ORIGINAL_CONTINUATION_CALL_VA = 0x4598D0
ASTERO_LITERAL_VA = 0x6B3CB4
TEXT_VIRTUAL_SIZE_OLD = 0x28D294
TEXT_VIRTUAL_SIZE_NEW = 0x28D300
SMALLCARSHEET_FRAME_MAX = 29


@dataclass(frozen=True)
class VehicleSlotProfile:
    """Semantic inputs for the already allocated retail record25 only."""

    profile_id: str
    slot_id: int
    vehicle_class: int
    internal_name: str
    stats: tuple[int, int, int, int]
    smallcarsheet_index: int
    float_bits: tuple[int, int, int, int]
    donor_record_id: int | None
    stats_source: str
    floats_source: str

    @property
    def meta(self) -> int:
        """Legacy R5V-C name for the now-identified +0x1C selector."""
        return self.smallcarsheet_index


ASTERO_PROOF_PROFILE = VehicleSlotProfile(
    profile_id="astero-proof", slot_id=25, vehicle_class=2,
    internal_name="Astero", stats=(6, 6, 8, 8), smallcarsheet_index=0,
    float_bits=(0x3D8B1C04, 0x3F092D67, 0x3EF74E40, 0x3F800000),
    donor_record_id=16, stats_source="retail Astero ID16",
    floats_source="retail Astero ID16",
)
TROOPER_PROFILE = VehicleSlotProfile(
    profile_id="trooper", slot_id=25, vehicle_class=2,
    internal_name="Trooper", stats=(6, 6, 8, 8), smallcarsheet_index=0,
    float_bits=(0x3D8B1C04, 0x3F092D67, 0x3EF74E40, 0x3F800000),
    donor_record_id=16,
    stats_source="Astero ID16 cosmetic donor; retail Trooper has no registry record",
    floats_source="Astero ID16 cosmetic donor; physics family remains retail Trooper",
)
TROOPER_SMALLCARSHEET29_PROFILE = replace(
    TROOPER_PROFILE,
    profile_id="trooper-smallsheet29",
    smallcarsheet_index=29,
)
SLOT25_PROFILES = {
    profile.profile_id: profile
    for profile in (ASTERO_PROOF_PROFILE, TROOPER_PROFILE,
                    TROOPER_SMALLCARSHEET29_PROFILE)
}


class PatchError(ValueError):
    """Input or patch operation did not match the one supported retail image."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def parse_pe(data: bytes) -> dict:
    if len(data) < 0x400 or data[:2] != b"MZ":
        raise PatchError("Missing DOS/PE header")
    pe = _u32(data, 0x3C)
    if pe + 0x108 >= len(data) or data[pe:pe + 4] != b"PE\0\0":
        raise PatchError("Missing PE signature")
    coff = pe + 4
    if _u16(data, coff) != 0x14C or _u16(data, coff + 2) != 4:
        raise PatchError("Expected 32-bit x86 PE with four sections")
    optional = coff + 20
    optional_size = _u16(data, coff + 16)
    if optional_size != 0xE0 or _u16(data, optional) != 0x10B:
        raise PatchError("Unexpected PE32 optional header")
    if _u32(data, optional + 28) != IMAGE_BASE:
        raise PatchError("Unexpected PE image base")
    if _u32(data, optional + 32) != 0x1000 or _u32(data, optional + 36) != 0x1000:
        raise PatchError("Unexpected PE section/file alignment")
    if _u32(data, optional + 56) != 0x311000:
        raise PatchError("Unexpected PE SizeOfImage")
    sections = []
    section_table = optional + optional_size
    for i in range(4):
        sh = section_table + i * 40
        name = data[sh:sh + 8].split(b"\0", 1)[0].decode("ascii")
        sections.append({
            "name": name,
            "header_offset": sh,
            "virtual_size": _u32(data, sh + 8),
            "rva": _u32(data, sh + 12),
            "raw_size": _u32(data, sh + 16),
            "raw_offset": _u32(data, sh + 20),
            "characteristics": _u32(data, sh + 36),
        })
    text, rdata, dsection, rsrc = sections
    if ([s["name"] for s in sections] != [".text", ".rdata", ".data", ".rsrc"]
            or text["rva"] != 0x1000 or text["raw_offset"] != 0x1000
            or text["raw_size"] != 0x28E000
            or text["virtual_size"] != TEXT_VIRTUAL_SIZE_OLD
            or text["characteristics"] != 0x60000020
            or rdata["rva"] != 0x28F000):
        raise PatchError("Unexpected retail section layout")
    if text["rva"] + TEXT_VIRTUAL_SIZE_NEW >= rdata["rva"]:
        raise PatchError("Expanded .text would overlap .rdata")
    return {"pe_offset": pe, "image_base": IMAGE_BASE, "sections": sections}


def va_to_file_offset(pe: dict, va: int, size: int = 1) -> int:
    rva = va - pe["image_base"]
    if rva < 0 or size < 1:
        raise PatchError("Invalid virtual address or size")
    for section in pe["sections"]:
        start = section["rva"]
        if start <= rva and rva + size <= start + section["raw_size"]:
            return section["raw_offset"] + rva - start
    raise PatchError(f"VA 0x{va:X} is outside section raw bytes")


def _rel32(call_va: int, target_va: int) -> bytes:
    delta = target_va - (call_va + 5)
    if not -(1 << 31) <= delta < (1 << 31):
        raise PatchError("Relative call out of range")
    return b"\xE8" + struct.pack("<i", delta)


def _validate_profile(profile: VehicleSlotProfile) -> VehicleSlotProfile:
    if profile.slot_id != 25 or profile.vehicle_class != 2:
        raise PatchError("Only allocated retail slot25 in class2 is supported")
    try:
        encoded = profile.internal_name.encode("ascii")
    except (AttributeError, UnicodeEncodeError) as exc:
        raise PatchError("Internal vehicle name must be non-empty ASCII") from exc
    if not encoded or b"/" in encoded or b"\\" in encoded or b"\x00" in encoded:
        raise PatchError("Internal vehicle name must be one safe path component")
    if len(profile.stats) != 4 or len(profile.float_bits) != 4:
        raise PatchError("Slot25 profile requires four stats and four float bit patterns")
    if any(not 0 <= value <= 0x7F for value in profile.stats):
        raise PatchError("Initializer byte-push arguments must be in range 0..127")
    if not 0 <= profile.smallcarsheet_index <= SMALLCARSHEET_FRAME_MAX:
        raise PatchError(
            "SmallCarSheet index must address a retail frame in range "
            f"0..{SMALLCARSHEET_FRAME_MAX}"
        )
    if any(not 0 <= value <= 0xFFFFFFFF for value in profile.float_bits):
        raise PatchError("Float bit patterns must be uint32 values")
    return profile


def get_profile(profile_id: str) -> VehicleSlotProfile:
    try:
        return SLOT25_PROFILES[profile_id.casefold()]
    except (AttributeError, KeyError) as exc:
        raise PatchError(f"Unknown slot25 profile: {profile_id}") from exc


def build_stub(
    profile: VehicleSlotProfile = ASTERO_PROOF_PROFILE,
    *,
    name_literal_va: int = ASTERO_LITERAL_VA,
) -> bytes:
    """Call the original initializer with a fresh owned profile-name string."""
    profile = _validate_profile(profile)
    code = bytearray()

    def emit(raw: bytes) -> None:
        code.extend(raw)

    def call(target: int) -> None:
        emit(_rel32(STUB_VA + len(code), target))

    emit(b"\x56\x8B\xF1\x83\xEC\x10")  # preserve ESI; ESI = registry; reserve four floats
    for offset, bits in enumerate(profile.float_bits):
        emit(b"\xC7\x44\x24" + bytes((offset * 4,)) + struct.pack("<I", bits))
    emit(b"\x6A\x00\x8B\xCC\x68" + struct.pack("<I", name_literal_va))
    call(STRING_CONSTRUCTOR_VA)
    # The initializer receives right-to-left stack values. The record-stat
    # tuple retains its R5V-C field order, so reverse it at the push site.
    for value in (profile.smallcarsheet_index, *reversed(profile.stats),
                  profile.vehicle_class, profile.slot_id):
        emit(b"\x6A" + bytes((value,)))
    emit(b"\x8D\x8E\x18\x05\x00\x00")  # ECX = registry + 0x518 = record25
    call(INITIALIZER_VA)
    emit(b"\x8B\xCE")  # original call was made with ECX = registry
    call(ORIGINAL_CONTINUATION_CALL_VA)
    emit(b"\x5E\xC3")  # restore ESI and return to 0x458D44
    return bytes(code)


def _persistent_literal(data: bytes, pe: dict, text: str) -> int | None:
    encoded = text.encode("ascii") + b"\x00"
    if text == "Astero":
        offset = va_to_file_offset(pe, ASTERO_LITERAL_VA, len(encoded))
        if data[offset:offset + len(encoded)] != encoded:
            raise PatchError("Astero donor literal mismatch")
        return ASTERO_LITERAL_VA
    for section in pe["sections"]:
        if section["characteristics"] & 0x80000000:
            continue
        start = section["raw_offset"]
        end = start + section["raw_size"]
        offset = data.find(encoded, start, end)
        if offset >= 0:
            return IMAGE_BASE + section["rva"] + offset - start
    return None


def _injection_payload(data: bytes, pe: dict, profile: VehicleSlotProfile) -> tuple[bytes, dict]:
    persistent_va = _persistent_literal(data, pe, profile.internal_name)
    encoded_name = profile.internal_name.encode("ascii") + b"\x00"
    if persistent_va is not None:
        stub = build_stub(profile, name_literal_va=persistent_va)
        return stub, {
            "storage": "existing-read-only-section",
            "virtual_address": persistent_va,
            "size": len(encoded_name),
        }

    provisional = build_stub(profile, name_literal_va=0)
    literal_va = STUB_VA + len(provisional)
    stub = build_stub(profile, name_literal_va=literal_va)
    payload = stub + encoded_name
    text = pe["sections"][0]
    text_start_va = IMAGE_BASE + text["rva"]
    relative_end = STUB_VA - text_start_va + len(payload)
    new_virtual_size = max(TEXT_VIRTUAL_SIZE_NEW, relative_end)
    if relative_end > text["raw_size"] or text["rva"] + new_virtual_size >= pe["sections"][1]["rva"]:
        raise PatchError("Slot25 stub and name exceed available read-only .text padding")
    return payload, {
        "storage": "appended-to-read-only-text-section",
        "virtual_address": literal_va,
        "size": len(encoded_name),
    }


def _operation(name: str, offset: int, original: bytes, replacement: bytes,
               purpose: str, *, va: int | None = None) -> dict:
    if len(original) != len(replacement):
        raise PatchError(f"Patch {name} changes file length")
    return {"name": name, "file_offset": offset, "virtual_address": va,
            "rva": None if va is None else va - IMAGE_BASE,
            "original_bytes": original.hex(), "replacement_bytes": replacement.hex(),
            "semantic_purpose": purpose}


def build_operations(
    data: bytes,
    pe: dict,
    profile: VehicleSlotProfile = ASTERO_PROOF_PROFILE,
) -> list[dict]:
    profile = _validate_profile(profile)
    text = pe["sections"][0]
    payload, _ = _injection_payload(data, pe, profile)
    text_start_va = IMAGE_BASE + text["rva"]
    relative_end = STUB_VA - text_start_va + len(payload)
    virtual_size = max(TEXT_VIRTUAL_SIZE_NEW, relative_end)
    operations = [
        _operation("text_virtual_size", text["header_offset"] + 8,
                   struct.pack("<I", TEXT_VIRTUAL_SIZE_OLD),
                   struct.pack("<I", virtual_size),
                   "Declare the zero-padded executable tail containing the stub as mapped .text"),
        _operation("registry_hook", va_to_file_offset(pe, HOOK_VA, 5),
                   _rel32(HOOK_VA, ORIGINAL_CONTINUATION_CALL_VA),
                   _rel32(HOOK_VA, STUB_VA),
                   "Call slot25 initializer stub; stub preserves original call", va=HOOK_VA),
        _operation("class2_capacity", va_to_file_offset(pe, 0x480A65),
                   b"\x0B", b"\x0C", "Class-2 navigation count 11 to 12", va=0x480A65),
        _operation("id25_unlock_only", va_to_file_offset(pe, 0x45A282, 4),
                   b"\x6A\x0F\xE8\x87", b"\xB0\x01\x5E\xC3",
                   "Test-only true result for ID25 case; leave all other cases intact", va=0x45A282),
        _operation("slot25_stub", va_to_file_offset(pe, STUB_VA, len(payload)),
                   b"\x00" * len(payload), payload,
                   f"Construct owned {profile.internal_name} temporary; initialize record25; call original continuation", va=STUB_VA),
    ]
    return operations


def validate_operations(data: bytes, operations: list[dict]) -> None:
    ordered = sorted(operations, key=lambda op: op["file_offset"])
    prior_end = -1
    for op in ordered:
        start = op["file_offset"]
        original = bytes.fromhex(op["original_bytes"])
        replacement = bytes.fromhex(op["replacement_bytes"])
        if start < prior_end or start < 0 or start + len(original) > len(data):
            raise PatchError(f"Overlapping or out-of-bounds patch: {op['name']}")
        if data[start:start + len(original)] != original:
            raise PatchError(f"Original bytes mismatch: {op['name']} at 0x{start:X}")
        if len(original) != len(replacement):
            raise PatchError(f"Size mismatch: {op['name']}")
        prior_end = start + len(original)


def make_candidate(
    data: bytes,
    *,
    expected_sha256: str = SOURCE_SHA256,
    profile: VehicleSlotProfile = ASTERO_PROOF_PROFILE,
) -> tuple[bytes, dict]:
    profile = _validate_profile(profile)
    digest = sha256(data)
    if digest != expected_sha256.lower():
        raise PatchError(f"Unsupported source SHA256: {digest}")
    pe = parse_pe(data)
    payload, string_location = _injection_payload(data, pe, profile)
    if profile.internal_name == "Astero" and ASTERO_LITERAL_VA not in range(
        string_location["virtual_address"],
        string_location["virtual_address"] + len(profile.internal_name) + 1,
    ):
        raise PatchError("Astero persistent literal mismatch")
    operations = build_operations(data, pe, profile)
    validate_operations(data, operations)
    result = bytearray(data)
    for op in operations:
        start = op["file_offset"]
        raw = bytes.fromhex(op["replacement_bytes"])
        result[start:start + len(raw)] = raw
    output = bytes(result)
    for op in operations:
        start = op["file_offset"]
        raw = bytes.fromhex(op["replacement_bytes"])
        if output[start:start + len(raw)] != raw:
            raise PatchError(f"Post-patch byte mismatch: {op['name']}")
    manifest = {
        "phase": ("R5V-C" if profile.profile_id == "astero-proof" else
                  "R5V-E0.1a" if profile.profile_id == "trooper-smallsheet29" else
                  "R5V-E0"),
        "build": "retail", "source_sha256": digest,
        "patched_sha256": sha256(output), "image_base": IMAGE_BASE,
        "record25": {"id": profile.slot_id, "class": profile.vehicle_class,
                     "donor_id": profile.donor_record_id, "name": profile.internal_name,
                     "stats": list(profile.stats), "meta": profile.smallcarsheet_index,
                     "float_bits": [f"{value:08x}" for value in profile.float_bits],
                     "initializer_va": INITIALIZER_VA, "record_offset_from_registry": 0x518,
                     "owned_name": "temporary deep-copied by original initializer"},
        "injection": {"entry_va": STUB_VA, "size": len(payload),
                      "return_va": HOOK_VA + 5,
                      "original_call_va": ORIGINAL_CONTINUATION_CALL_VA,
                      "section": ".text"},
        "unlock_override": "ID25 only; current game-local Bonus2 flag is false",
        "operations": operations,
        "runtime_validation": "WAITING FOR HUMAN P0",
    }
    if profile.profile_id != "astero-proof":
        manifest["injection"]["name_literal"] = string_location
        manifest["profile"] = {
            "profile_id": profile.profile_id,
            "stats_source": profile.stats_source,
            "floats_source": profile.floats_source,
        }
        if profile.profile_id != "trooper":
            # Preserve the existing Trooper manifest shape for reproducibility.
            manifest["record25"]["smallcarsheet_index"] = profile.smallcarsheet_index
            manifest["profile"]["smallcarsheet_index"] = profile.smallcarsheet_index
    return output, manifest


def write_candidate(
    source: Path, output: Path, manifest_path: Path, *, dry_run: bool = False,
    profile: VehicleSlotProfile = ASTERO_PROOF_PROFILE,
) -> dict:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    manifest_path = manifest_path.resolve(strict=False)
    if source == output or (output.exists() and os.path.samefile(source, output)):
        raise PatchError("Output executable must differ from source")
    if (manifest_path in (source, output)
            or (manifest_path.exists() and os.path.samefile(source, manifest_path))
            or (manifest_path.exists() and output.exists()
                and os.path.samefile(output, manifest_path))):
        raise PatchError("Manifest path must differ from source and output")
    if output.exists() or (manifest_path.exists() and not dry_run):
        raise PatchError("Output already exists; choose a new path")
    data = source.read_bytes()
    if profile == ASTERO_PROOF_PROFILE:
        candidate, manifest = make_candidate(data)
    else:
        candidate, manifest = make_candidate(data, profile=profile)
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(candidate)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if sha256(output.read_bytes()) != manifest["patched_sha256"]:
            raise PatchError("Written candidate hash mismatch")
    return manifest


def verify_existing(
    source: Path, output: Path, manifest_path: Path, *,
    profile: VehicleSlotProfile = ASTERO_PROOF_PROFILE,
) -> dict:
    """Rebuild in memory from clean retail and compare candidate and manifest."""
    source = source.resolve(strict=True)
    output = output.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    if source == output or os.path.samefile(source, output):
        raise PatchError("Candidate path must differ from source")
    if profile == ASTERO_PROOF_PROFILE:
        expected, manifest = make_candidate(source.read_bytes())
    else:
        expected, manifest = make_candidate(source.read_bytes(), profile=profile)
    actual = output.read_bytes()
    if actual != expected:
        raise PatchError("Candidate bytes differ from deterministic clean-source rebuild")
    try:
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise PatchError("Invalid candidate manifest") from exc
    if stored != manifest:
        raise PatchError("Candidate manifest does not match clean-source rebuild")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Unmodified supported retail MRallye.exe")
    parser.add_argument("output", type=Path, help="New test-copy path")
    parser.add_argument("--manifest", type=Path, help="JSON manifest output path")
    parser.add_argument("--profile", choices=sorted(SLOT25_PROFILES), default="astero-proof",
                        help="record25 initializer profile (default: astero-proof)")
    parser.add_argument("--dry-run", action="store_true", help="Verify and report without writing")
    parser.add_argument("--verify-existing", action="store_true",
                        help="Rebuild in memory and verify existing output and manifest")
    args = parser.parse_args()
    if args.dry_run and args.verify_existing:
        parser.error("--dry-run and --verify-existing are mutually exclusive")
    manifest_path = args.manifest or args.output.with_suffix(".manifest.json")
    try:
        if args.verify_existing:
            manifest = verify_existing(args.source, args.output, manifest_path,
                                       profile=get_profile(args.profile))
        else:
            manifest = write_candidate(args.source, args.output, manifest_path,
                                       dry_run=args.dry_run,
                                       profile=get_profile(args.profile))
    except (PatchError, OSError, struct.error) as exc:
        parser.exit(2, f"slot25 patch refused: {exc}\n")
    print(json.dumps({"dry_run": args.dry_run, "verified_existing": args.verify_existing,
                      "source_sha256": manifest["source_sha256"],
                      "patched_sha256": manifest["patched_sha256"],
                      "patches": len(manifest["operations"]),
                      "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
