"""Version-locked, copy-only retail vehicle physics-family bindings.

The retail build initializes its type-to-family catalog from immediate string
pointers in FUN_00458E70. This module can redirect those initializer inputs in
a new executable copy. It never attaches to a process and never edits the
source executable supplied by the caller.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .vehicle_config_analysis import VehicleConfigDocument, parse_vehicle_config
from .vehicle_family_broker import (
    FAMILY_BY_TYPE_ID,
    PLAYER_MODIFICATION_FIELDS,
    RETAIL_EXE_SHA256,
    analyze_family_identity,
    named_vehicle_path,
)


RETAIL_BUILD_NAME = "retail-2001-verified"
PE32_I386_MACHINE = 0x014C
PE32_MAGIC = 0x010B
IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040
IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040
IMAGE_SCN_MEM_READ = 0x40000000
BOUND_SECTION_NAME = b".rphys3"
BOUND_SECTION_CHARACTERISTICS = IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ
MAX_BOUND_FAMILY_BYTES = 0x10000

EXPECTED_BASE_GROUP_COUNTS = {
    "Dimensions": 8,
    "Chassis": 16,
    "Steering": 5,
    "Engine": 45,
    "Suspension": 48,
    "DamageParams": 25,
}
RETAIL_REQUIRED_BASE_SCHEMA_SHA256 = "3328204f77218f840ca734f54010b711188e69efdb7d84e84f87d7f08dac77bd"


@dataclass(frozen=True)
class FamilyCatalogEntry:
    type_id: int
    family: str
    push_instruction_va: int
    literal_va: int


# Push instruction VAs and family string VAs are from the retail Ghidra
# initializer/disassembly. Each PUSH imm32 is checked byte-for-byte before it
# is changed. Type IDs follow FUN_00458E70's calls into FUN_0045A0B0.
RETAIL_FAMILY_CATALOG = (
    FamilyCatalogEntry(0, "Landcruiser", 0x00458EBA, 0x006B3D50),
    FamilyCatalogEntry(1, "Pajero", 0x00458F21, 0x006B3D48),
    FamilyCatalogEntry(2, "Tata", 0x00458F88, 0x006B3D40),
    FamilyCatalogEntry(3, "Terrano", 0x00458FEF, 0x006B3D38),
    FamilyCatalogEntry(4, "Chevyblazer", 0x00459059, 0x006B3D2C),
    FamilyCatalogEntry(5, "Xtrail", 0x004590C3, 0x006B3D24),
    FamilyCatalogEntry(6, "Frontera", 0x0045912D, 0x006B3D18),
    FamilyCatalogEntry(7, "Navara", 0x00459197, 0x006B3D10),
    FamilyCatalogEntry(8, "Forester", 0x00459204, 0x006B3D04),
    FamilyCatalogEntry(9, "Jump", 0x0045926B, 0x006B3CFC),
    FamilyCatalogEntry(10, "Rmonster", 0x004592D5, 0x006B3CF0),
    FamilyCatalogEntry(11, "Patrol", 0x00459342, 0x006B3CE8),
    FamilyCatalogEntry(12, "Newrav", 0x004593A9, 0x006B3CE0),
    FamilyCatalogEntry(13, "Kiasportage", 0x00459413, 0x006B3CD4),
    FamilyCatalogEntry(14, "Wildcat", 0x0045947D, 0x006B3CCC),
    FamilyCatalogEntry(15, "Simmbugghini", 0x004594E7, 0x006B3CBC),
    FamilyCatalogEntry(16, "Astero", 0x00459551, 0x006B3CB4),
    FamilyCatalogEntry(17, "Kangoo", 0x004595BB, 0x006B3CAC),
    FamilyCatalogEntry(18, "Megane", 0x00459625, 0x006B3CA4),
    FamilyCatalogEntry(19, "Mattserati", 0x0045968F, 0x006B3C98),
    FamilyCatalogEntry(20, "Bruno", 0x004596F9, 0x006B3C90),
    FamilyCatalogEntry(21, "SeatBuggy", 0x00459763, 0x006B3C84),
    FamilyCatalogEntry(22, "Kamaz", 0x004597CD, 0x006B3C7C),
    FamilyCatalogEntry(23, "Icecream", 0x00459837, 0x006B3C70),
    FamilyCatalogEntry(24, "Ufo", 0x004598A1, 0x006B3C6C),
)
RETAIL_CATALOG_BY_FAMILY = {entry.family: entry for entry in RETAIL_FAMILY_CATALOG}


@dataclass(frozen=True)
class PhysicsBinding:
    carrier_type: str
    physics_family: str


@dataclass(frozen=True)
class PESection:
    name: bytes
    virtual_size: int
    virtual_address: int
    raw_size: int
    raw_pointer: int
    characteristics: int


@dataclass(frozen=True)
class PE32Layout:
    pe_offset: int
    coff_offset: int
    optional_offset: int
    section_table_offset: int
    number_of_sections: int
    size_of_optional_header: int
    machine: int
    image_base: int
    section_alignment: int
    file_alignment: int
    size_of_image: int
    size_of_headers: int
    size_of_initialized_data: int
    checksum_offset: int
    dll_characteristics: int
    base_relocation_rva: int
    base_relocation_size: int
    sections: tuple[PESection, ...]

    @property
    def section_table_end(self) -> int:
        return self.section_table_offset + 40 * self.number_of_sections

    def va_to_file_offset(self, va: int, *, length: int = 1) -> int:
        if va < self.image_base:
            raise ValueError(f"VA 0x{va:X} is below PE image base")
        rva = va - self.image_base
        for section in self.sections:
            relative = rva - section.virtual_address
            if relative >= 0 and relative + length <= section.raw_size:
                return section.raw_pointer + relative
        raise ValueError(f"VA range 0x{va:X}+0x{length:X} is not file-backed")


@dataclass(frozen=True)
class PlannedFamilyPatch:
    carrier_type: str
    type_id: int
    physics_family: str
    push_instruction_va: int
    push_file_offset: int
    old_pointer_va: int
    new_pointer_va: int
    pointer_source: str
    string_bytes_with_nul: int
    changed: bool


@dataclass(frozen=True)
class PEFamilyPatchResult:
    data: bytes
    patches: tuple[PlannedFamilyPatch, ...]
    added_section: bool
    section_rva: int | None
    section_file_offset: int | None
    section_raw_size: int
    source_sha256: str
    patched_sha256: str
    changed_ranges: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ValidatedBinding:
    binding: PhysicsBinding
    type_id: int
    base_group_counts: dict[str, int]
    player1_overlay_count: int
    pointer_source: str
    family_string_length: int


def _align(value: int, alignment: int) -> int:
    if alignment <= 0 or alignment & (alignment - 1):
        raise ValueError(f"invalid PE alignment 0x{alignment:X}")
    return (value + alignment - 1) & ~(alignment - 1)


def _u16(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def parse_pe32_layout(data: bytes) -> PE32Layout:
    """Parse the PE32 fields required for a new read-only data section."""
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ValueError("input is not a valid DOS/PE executable")
    pe_offset = _u32(data, 0x3C)
    if pe_offset + 24 > len(data) or data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise ValueError("PE signature/header is missing or truncated")
    coff_offset = pe_offset + 4
    machine = _u16(data, coff_offset)
    number_of_sections = _u16(data, coff_offset + 2)
    size_of_optional_header = _u16(data, coff_offset + 16)
    optional_offset = pe_offset + 24
    if optional_offset + size_of_optional_header > len(data):
        raise ValueError("PE optional header is truncated")
    if size_of_optional_header < 0xE0 or _u16(data, optional_offset) != PE32_MAGIC:
        raise ValueError("only a complete PE32 optional header is supported")
    section_table_offset = optional_offset + size_of_optional_header
    section_table_end = section_table_offset + number_of_sections * 40
    if section_table_end > len(data):
        raise ValueError("PE section table is truncated")
    sections: list[PESection] = []
    for index in range(number_of_sections):
        offset = section_table_offset + index * 40
        raw_name = data[offset:offset + 8].split(b"\0", 1)[0]
        sections.append(PESection(
            name=raw_name,
            virtual_size=_u32(data, offset + 8),
            virtual_address=_u32(data, offset + 12),
            raw_size=_u32(data, offset + 16),
            raw_pointer=_u32(data, offset + 20),
            characteristics=_u32(data, offset + 36),
        ))
    data_directory_offset = optional_offset + 96
    relocation_entry_offset = data_directory_offset + 5 * 8
    return PE32Layout(
        pe_offset=pe_offset,
        coff_offset=coff_offset,
        optional_offset=optional_offset,
        section_table_offset=section_table_offset,
        number_of_sections=number_of_sections,
        size_of_optional_header=size_of_optional_header,
        machine=machine,
        image_base=_u32(data, optional_offset + 28),
        section_alignment=_u32(data, optional_offset + 32),
        file_alignment=_u32(data, optional_offset + 36),
        size_of_image=_u32(data, optional_offset + 56),
        size_of_headers=_u32(data, optional_offset + 60),
        size_of_initialized_data=_u32(data, optional_offset + 8),
        checksum_offset=optional_offset + 64,
        dll_characteristics=_u16(data, optional_offset + 70),
        base_relocation_rva=_u32(data, relocation_entry_offset),
        base_relocation_size=_u32(data, relocation_entry_offset + 4),
        sections=tuple(sections),
    )


def _validate_family_component(family: str) -> bytes:
    named_vehicle_path(family)
    try:
        encoded = family.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("family names must use retail-compatible ASCII") from exc
    if len(encoded) + 1 > MAX_BOUND_FAMILY_BYTES:
        raise ValueError("family name is too long for the bounded binding section")
    return encoded


def parse_binding_config_text(text: str) -> tuple[PhysicsBinding, ...]:
    """Parse strict JSON config with separate carrier and physics identities."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid binding JSON: {exc}") from exc
    if not isinstance(document, dict) or set(document) != {"schema_version", "bindings"}:
        raise ValueError("binding config must contain only schema_version and bindings")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ValueError("unsupported binding config schema_version")
    rows = document["bindings"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("bindings must be a non-empty list")
    bindings: list[PhysicsBinding] = []
    seen_carriers: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"carrier_type", "physics_family"}:
            raise ValueError(
                f"binding {index} must contain only carrier_type and physics_family; "
                "model/resource identity is separate"
            )
        carrier = row["carrier_type"]
        target = row["physics_family"]
        _validate_family_component(carrier)
        _validate_family_component(target)
        folded = carrier.casefold()
        if folded in seen_carriers:
            raise ValueError(f"carrier type {carrier!r} is bound more than once")
        seen_carriers.add(folded)
        bindings.append(PhysicsBinding(carrier_type=carrier, physics_family=target))
    return tuple(bindings)


def load_binding_config(path: Path) -> tuple[PhysicsBinding, ...]:
    try:
        return parse_binding_config_text(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read binding config {path}: {exc}") from exc


def validate_binding_families(
    bindings: Iterable[PhysicsBinding],
    vehicle_config: VehicleConfigDocument,
    modifications_config: VehicleConfigDocument,
    *,
    catalog: tuple[FamilyCatalogEntry, ...] = RETAIL_FAMILY_CATALOG,
    required_base_schema_sha256: str = RETAIL_REQUIRED_BASE_SCHEMA_SHA256,
) -> tuple[ValidatedBinding, ...]:
    by_carrier = {entry.family: entry for entry in catalog}
    validated: list[ValidatedBinding] = []
    for binding in bindings:
        carrier = by_carrier.get(binding.carrier_type)
        if carrier is None:
            raise ValueError(
                f"carrier type {binding.carrier_type!r} is not initialized in the retail catalog"
            )
        target = binding.physics_family
        if target not in vehicle_config.families:
            raise ValueError(f"physics family {target!r} is absent from vehicles.xml")
        audit = analyze_family_identity(vehicle_config, modifications_config, target)
        if not audit.family_config_present:
            raise ValueError(f"physics family {target!r} has no base config root")
        schema_sha256 = family_schema_sha256(vehicle_config.families[target])
        if schema_sha256 != required_base_schema_sha256:
            raise ValueError(
                f"physics family {target!r} path/type schema differs from the audited "
                "retail broker schema"
            )
        if audit.base_group_counts != EXPECTED_BASE_GROUP_COUNTS:
            raise ValueError(
                f"physics family {target!r} base groups are incomplete or unexpected: "
                f"{audit.base_group_counts!r}"
            )
        if audit.missing_base_groups:
            raise ValueError(
                f"physics family {target!r} is missing broker groups: "
                f"{', '.join(audit.missing_base_groups)}"
            )
        if audit.player1_missing_modification_fields:
            raise ValueError(
                f"physics family {target!r} Player1 overlay misses: "
                f"{', '.join(audit.player1_missing_modification_fields)}"
            )
        if set(audit.player1_modification_fields) != set(PLAYER_MODIFICATION_FIELDS):
            raise ValueError(f"physics family {target!r} Player1 overlay shape is not exact")
        player1_rows = {
            path.removeprefix("Player1/Modifications/"): row
            for path, row in modifications_config.families[target].items()
            if path.startswith("Player1/Modifications/")
        }
        if any(player1_rows[field]["type"] != "Float" for field in PLAYER_MODIFICATION_FIELDS):
            raise ValueError(f"physics family {target!r} Player1 overlay has an unexpected type")
        if target in by_carrier:
            pointer_source = "existing stable executable family literal"
        else:
            pointer_source = "new read-only .rphys3 executable-section string"
        validated.append(ValidatedBinding(
            binding=binding,
            type_id=carrier.type_id,
            base_group_counts=dict(audit.base_group_counts),
            player1_overlay_count=len(audit.player1_modification_fields),
            pointer_source=pointer_source,
            family_string_length=len(_validate_family_component(target)),
        ))
    return tuple(validated)


def family_schema_sha256(fields: Mapping[str, Mapping[str, str]]) -> str:
    """Fingerprint relative XML paths and types, excluding mutable values."""
    rows = sorted((path, record["type"]) for path, record in fields.items())
    canonical = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def _windows_checksum(data: bytes, checksum_offset: int) -> int:
    """Calculate the PE checksum with the checksum field treated as zero."""
    mutable = bytearray(data)
    mutable[checksum_offset:checksum_offset + 4] = b"\0\0\0\0"
    total = 0
    limit = len(mutable) - (len(mutable) % 2)
    for offset in range(0, limit, 2):
        total += mutable[offset] | (mutable[offset + 1] << 8)
        total = (total & 0xFFFF) + (total >> 16)
    if limit < len(mutable):
        total += mutable[-1]
    total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    return (total + len(mutable)) & 0xFFFFFFFF


def _changed_ranges(before: bytes, after: bytes) -> tuple[dict[str, Any], ...]:
    if len(after) < len(before):
        raise ValueError("patched image unexpectedly shrank")
    changes: list[dict[str, Any]] = []
    cursor = 0
    while cursor < len(after):
        old = before[cursor] if cursor < len(before) else None
        new = after[cursor]
        if old == new:
            cursor += 1
            continue
        start = cursor
        old_bytes = bytearray()
        new_bytes = bytearray()
        while cursor < len(after):
            old = before[cursor] if cursor < len(before) else None
            new = after[cursor]
            if old == new:
                break
            if old is not None:
                old_bytes.append(old)
            new_bytes.append(new)
            cursor += 1
        changes.append({
            "offset": start,
            "length": cursor - start,
            "old_hex": old_bytes.hex(" "),
            "new_hex": new_bytes.hex(" "),
        })
    return tuple(changes)


def patch_family_initializer(
    source_data: bytes,
    bindings: Iterable[PhysicsBinding],
    *,
    catalog: tuple[FamilyCatalogEntry, ...] = RETAIL_FAMILY_CATALOG,
) -> PEFamilyPatchResult:
    """Patch exact retail initializer pointer operands in an in-memory copy."""
    layout = parse_pe32_layout(source_data)
    if layout.machine != PE32_I386_MACHINE or layout.image_base != 0x00400000:
        raise ValueError("family initializer patch requires the verified I386 image base")
    if layout.dll_characteristics & IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE:
        raise ValueError("dynamic-base images are not supported by this absolute-pointer patch")
    if layout.base_relocation_rva or layout.base_relocation_size:
        raise ValueError("images with base relocations are not supported by this patch")
    by_carrier = {entry.family: entry for entry in catalog}
    if catalog is RETAIL_FAMILY_CATALOG and (
        len(catalog) != 25 or tuple(entry.family for entry in catalog) != FAMILY_BY_TYPE_ID
    ):
        raise ValueError("family initializer map does not match the audited 25-entry retail catalog")

    selected = tuple(bindings)
    if not selected:
        raise ValueError("at least one family binding is required")
    seen_carriers: set[str] = set()
    entries: list[tuple[PhysicsBinding, FamilyCatalogEntry, bytes, int, str]] = []
    new_strings: dict[bytes, int] = {}
    new_payload = bytearray()

    for binding in selected:
        carrier = by_carrier.get(binding.carrier_type)
        if carrier is None:
            raise ValueError(f"unknown initialized carrier type {binding.carrier_type!r}")
        if carrier.family.casefold() in seen_carriers:
            raise ValueError(f"carrier type {binding.carrier_type!r} is bound more than once")
        seen_carriers.add(carrier.family.casefold())
        encoded = _validate_family_component(binding.physics_family)
        push_offset = layout.va_to_file_offset(carrier.push_instruction_va, length=5)
        expected_push = b"\x68" + struct.pack("<I", carrier.literal_va)
        if source_data[push_offset:push_offset + 5] != expected_push:
            raise ValueError(
                f"initializer signature mismatch for {carrier.family} at "
                f"0x{carrier.push_instruction_va:08X}"
            )
        literal_offset = layout.va_to_file_offset(carrier.literal_va, length=len(carrier.family) + 1)
        if source_data[literal_offset:literal_offset + len(carrier.family) + 1] != (
            carrier.family.encode("ascii") + b"\0"
        ):
            raise ValueError(f"family literal mismatch for {carrier.family}")

        target_entry = by_carrier.get(binding.physics_family)
        if target_entry is not None:
            target_literal_offset = layout.va_to_file_offset(
                target_entry.literal_va, length=len(target_entry.family) + 1
            )
            if source_data[target_literal_offset:target_literal_offset + len(target_entry.family) + 1] != (
                target_entry.family.encode("ascii") + b"\0"
            ):
                raise ValueError(f"target family literal mismatch for {target_entry.family}")
            target_va = target_entry.literal_va
            pointer_source = "existing stable executable family literal"
        else:
            encoded_nul = encoded + b"\0"
            if encoded_nul not in new_strings:
                new_strings[encoded_nul] = len(new_payload)
                new_payload.extend(encoded_nul)
            target_va = 0
            pointer_source = "new read-only .rphys3 executable-section string"
        entries.append((binding, carrier, encoded, target_va, pointer_source))

    output = bytearray(source_data)
    section_rva: int | None = None
    section_file_offset: int | None = None
    section_raw_size = 0
    added_section = bool(new_payload)
    if added_section:
        if layout.number_of_sections >= 0xFFFF:
            raise ValueError("PE section count cannot be increased safely")
        header_slot = layout.section_table_end
        next_header_end = header_slot + 40
        first_raw = min(
            (section.raw_pointer for section in layout.sections if section.raw_size),
            default=len(source_data),
        )
        if next_header_end > layout.size_of_headers or next_header_end > first_raw:
            raise ValueError("PE has no verified free section-header slot")
        if any(source_data[header_slot:next_header_end]):
            raise ValueError("PE section-header extension bytes are not zero")
        section_rva = _align(max(
            layout.size_of_image,
            max(section.virtual_address + max(section.virtual_size, section.raw_size)
                for section in layout.sections),
        ), layout.section_alignment)
        section_file_offset = _align(len(source_data), layout.file_alignment)
        section_raw_size = _align(len(new_payload), layout.file_alignment)
        if section_rva + len(new_payload) > 0xFFFFFFFF or section_file_offset + section_raw_size > 0xFFFFFFFF:
            raise ValueError("new section exceeds PE32 address or file limits")
        if section_file_offset > len(output):
            output.extend(b"\0" * (section_file_offset - len(output)))
        output.extend(new_payload)
        output.extend(b"\0" * (section_raw_size - len(new_payload)))
        new_header = struct.pack(
            "<8sIIIIIIHHI",
            BOUND_SECTION_NAME.ljust(8, b"\0"),
            len(new_payload),
            section_rva,
            section_raw_size,
            section_file_offset,
            0,
            0,
            0,
            0,
            BOUND_SECTION_CHARACTERISTICS,
        )
        output[header_slot:next_header_end] = new_header
        struct.pack_into("<H", output, layout.coff_offset + 2, layout.number_of_sections + 1)
        struct.pack_into(
            "<I", output, layout.optional_offset + 8,
            layout.size_of_initialized_data + section_raw_size,
        )
        new_size_of_image = _align(section_rva + len(new_payload), layout.section_alignment)
        struct.pack_into("<I", output, layout.optional_offset + 56, new_size_of_image)
        for encoded_nul, relative in new_strings.items():
            if layout.image_base + section_rva + relative > 0xFFFFFFFF:
                raise ValueError("family string VA overflows PE32")

    patches: list[PlannedFamilyPatch] = []
    for binding, carrier, encoded, target_va, pointer_source in entries:
        if pointer_source.startswith("new read-only"):
            assert section_rva is not None
            target_va = layout.image_base + section_rva + new_strings[encoded + b"\0"]
        if target_va == carrier.literal_va:
            push_offset = layout.va_to_file_offset(carrier.push_instruction_va, length=5)
            patches.append(PlannedFamilyPatch(
                carrier_type=carrier.family,
                type_id=carrier.type_id,
                physics_family=binding.physics_family,
                push_instruction_va=carrier.push_instruction_va,
                push_file_offset=push_offset,
                old_pointer_va=carrier.literal_va,
                new_pointer_va=target_va,
                pointer_source=pointer_source,
                string_bytes_with_nul=len(encoded) + 1,
                changed=False,
            ))
            continue
        push_offset = layout.va_to_file_offset(carrier.push_instruction_va, length=5)
        struct.pack_into("<I", output, push_offset + 1, target_va)
        patches.append(PlannedFamilyPatch(
            carrier_type=carrier.family,
            type_id=carrier.type_id,
            physics_family=binding.physics_family,
            push_instruction_va=carrier.push_instruction_va,
            push_file_offset=push_offset,
            old_pointer_va=carrier.literal_va,
            new_pointer_va=target_va,
            pointer_source=pointer_source,
            string_bytes_with_nul=len(encoded) + 1,
            changed=True,
        ))

    if bytes(output) != source_data:
        struct.pack_into("<I", output, layout.checksum_offset, 0)
        final_data = bytes(output)
        checksum = _windows_checksum(final_data, layout.checksum_offset)
        struct.pack_into("<I", output, layout.checksum_offset, checksum)
    final_data = bytes(output)
    return PEFamilyPatchResult(
        data=final_data,
        patches=tuple(patches),
        added_section=added_section,
        section_rva=section_rva,
        section_file_offset=section_file_offset,
        section_raw_size=section_raw_size,
        source_sha256=hashlib.sha256(source_data).hexdigest(),
        patched_sha256=hashlib.sha256(final_data).hexdigest(),
        changed_ranges=_changed_ranges(source_data, final_data),
    )


def _validate_retail_executable_bytes(data: bytes, expected_sha256: str = RETAIL_EXE_SHA256) -> str:
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"retail executable SHA-256 mismatch: {digest}")
    layout = parse_pe32_layout(data)
    if layout.machine != PE32_I386_MACHINE or layout.image_base != 0x00400000:
        raise ValueError("recognized hash has unexpected PE machine or image base")
    return digest


def _expected_config_group_counts(document: VehicleConfigDocument, family: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in document.families[family]:
        group = path.split("/", 1)[0]
        counts[group] = counts.get(group, 0) + 1
    return dict(sorted((key, value) for key, value in counts.items() if key in EXPECTED_BASE_GROUP_COUNTS))


def validate_binding_request(
    source_exe: Path,
    bindings: Iterable[PhysicsBinding],
    vehicle_config_path: Path,
    modifications_config_path: Path,
    *,
    expected_exe_sha256: str = RETAIL_EXE_SHA256,
    catalog: tuple[FamilyCatalogEntry, ...] = RETAIL_FAMILY_CATALOG,
    required_base_schema_sha256: str = RETAIL_REQUIRED_BASE_SCHEMA_SHA256,
) -> dict[str, Any]:
    """Read-only dry-run audit of build, catalog, family groups, and patch sites."""
    bindings = tuple(bindings)
    try:
        source_data = source_exe.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read retail executable {source_exe}: {exc}") from exc
    source_sha = _validate_retail_executable_bytes(source_data, expected_exe_sha256)
    vehicle_config = parse_vehicle_config(vehicle_config_path, build=RETAIL_BUILD_NAME)
    modifications_config = parse_vehicle_config(modifications_config_path, build=RETAIL_BUILD_NAME)
    validated = validate_binding_families(
        bindings,
        vehicle_config,
        modifications_config,
        catalog=catalog,
        required_base_schema_sha256=required_base_schema_sha256,
    )
    patch_result = patch_family_initializer(source_data, bindings, catalog=catalog)
    rows = []
    for row, patch in zip(validated, patch_result.patches):
        rows.append({
            "carrier_type": row.binding.carrier_type,
            "carrier_type_id": row.type_id,
            "current_family": row.binding.carrier_type,
            "physics_family": row.binding.physics_family,
            "base_groups": row.base_group_counts,
            "player1_overlay_fields": row.player1_overlay_count,
            "family_string_length": row.family_string_length,
            "pointer_source": row.pointer_source,
            "initializer_push_va": f"0x{patch.push_instruction_va:08X}",
            "initializer_file_offset": f"0x{patch.push_file_offset:08X}",
            "target_pointer_va": f"0x{patch.new_pointer_va:08X}",
            "changes_initializer": patch.changed,
        })
    return {
        "status": "VALID",
        "mode": "DRY_RUN_NO_FILES_WRITTEN",
        "build": RETAIL_BUILD_NAME,
        "retail_executable_sha256": source_sha,
        "retail_executable_size": len(source_data),
        "planned_executable_sha256": patch_result.patched_sha256,
        "planned_executable_size": len(patch_result.data),
        "vehicle_config": {
            "path": str(vehicle_config_path),
            "sha256": vehicle_config.sha256,
            "size": vehicle_config.file_size,
        },
        "modifications_config": {
            "path": str(modifications_config_path),
            "sha256": modifications_config.sha256,
            "size": modifications_config.file_size,
        },
        "bindings": rows,
        "planned_pe_section": (
            {
                "name": BOUND_SECTION_NAME.decode("ascii"),
                "virtual_address": f"0x{0x00400000 + patch_result.section_rva:08X}",
                "virtual_address_rva": f"0x{patch_result.section_rva:08X}",
                "file_offset": f"0x{patch_result.section_file_offset:08X}",
                "raw_size": patch_result.section_raw_size,
            }
            if patch_result.added_section else None
        ),
        "planned_changed_ranges": list(patch_result.changed_ranges),
        "source_executable_modified": False,
        "output_copy_required": True,
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=path.name + ".", suffix=".tmp", dir=path.parent, delete=False) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _manifest_paths(output_exe: Path) -> tuple[Path, Path]:
    return (
        output_exe.with_name(output_exe.name + ".original"),
        output_exe.with_name(output_exe.name + ".physics-bind.json"),
    )


def apply_binding_copy(
    source_exe: Path,
    output_exe: Path,
    bindings: Iterable[PhysicsBinding],
    vehicle_config_path: Path,
    modifications_config_path: Path,
    *,
    expected_exe_sha256: str = RETAIL_EXE_SHA256,
    catalog: tuple[FamilyCatalogEntry, ...] = RETAIL_FAMILY_CATALOG,
    required_base_schema_sha256: str = RETAIL_REQUIRED_BASE_SCHEMA_SHA256,
) -> dict[str, Any]:
    """Write a bound executable copy plus verified original backup/manifest."""
    bindings = tuple(bindings)
    source_path = source_exe.resolve()
    output_path = output_exe.resolve()
    if str(source_path).casefold() == str(output_path).casefold():
        raise ValueError("refusing to overwrite the source retail executable")
    source_data = source_path.read_bytes()
    source_sha = _validate_retail_executable_bytes(source_data, expected_exe_sha256)
    vehicle_config = parse_vehicle_config(vehicle_config_path, build=RETAIL_BUILD_NAME)
    modifications_config = parse_vehicle_config(modifications_config_path, build=RETAIL_BUILD_NAME)
    validated = validate_binding_families(
        bindings,
        vehicle_config,
        modifications_config,
        catalog=catalog,
        required_base_schema_sha256=required_base_schema_sha256,
    )
    patch = patch_family_initializer(source_data, bindings, catalog=catalog)
    backup_path, manifest_path = _manifest_paths(output_path)
    binding_rows = [asdict(binding) for binding in bindings]

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"existing binding manifest is unreadable: {manifest_path}") from exc
        if manifest.get("source_sha256") != source_sha or manifest.get("backup_name") != backup_path.name:
            raise ValueError("existing output manifest belongs to a different original executable")
        if not backup_path.is_file() or _sha256(backup_path.read_bytes()) != source_sha:
            raise ValueError("existing original backup is missing or has the wrong SHA-256")
        if manifest.get("status") == "applied":
            if not output_path.is_file() or _sha256(output_path.read_bytes()) != manifest.get("patched_sha256"):
                raise ValueError("bound output differs from its manifest; refusing to overwrite it")
            if manifest.get("bindings") == binding_rows:
                return {"status": "ALREADY_APPLIED", "output_exe": str(output_path), "manifest": str(manifest_path)}
            raise ValueError("a different binding is already applied; restore before applying another")
        if manifest.get("status") != "restored":
            raise ValueError("existing manifest has an unknown binding state")
        if not output_path.is_file() or _sha256(output_path.read_bytes()) != source_sha:
            raise ValueError("restored output is not byte-identical to its verified original backup")
    elif backup_path.exists() or output_path.exists():
        raise ValueError("output/backup already exists without a tool-owned manifest")

    if not backup_path.exists():
        _atomic_write(backup_path, source_data)
    manifest = {
        "schema_version": 1,
        "build": RETAIL_BUILD_NAME,
        "status": "applied",
        "source_exe_name": source_path.name,
        "source_sha256": source_sha,
        "output_exe_name": output_path.name,
        "backup_name": backup_path.name,
        "patched_sha256": patch.patched_sha256,
        "bindings": binding_rows,
        "validated_families": [asdict(row) for row in validated],
        "patches": [asdict(row) for row in patch.patches],
        "added_section": patch.added_section,
        "section_rva": patch.section_rva,
        "section_file_offset": patch.section_file_offset,
        "section_raw_size": patch.section_raw_size,
        "changed_ranges": list(patch.changed_ranges),
        "source_exe_modified": False,
    }
    _atomic_write(output_path, patch.data)
    _atomic_write(manifest_path, (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return {
        "status": "APPLIED_TO_COPY",
        "output_exe": str(output_path),
        "backup": str(backup_path),
        "manifest": str(manifest_path),
        "source_sha256": source_sha,
        "patched_sha256": patch.patched_sha256,
        "changed_ranges": list(patch.changed_ranges),
        "source_exe_modified": False,
    }


def restore_binding_copy(
    output_exe: Path,
    *,
    expected_source_sha256: str = RETAIL_EXE_SHA256,
) -> dict[str, Any]:
    """Restore only a tool-owned bound copy; leave source executable untouched."""
    output_path = output_exe.resolve()
    backup_path, manifest_path = _manifest_paths(output_path)
    if not manifest_path.is_file() or not backup_path.is_file():
        raise ValueError("no complete physics-binding manifest and original backup were found")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("physics-binding manifest is unreadable") from exc
    original_data = backup_path.read_bytes()
    source_sha = manifest.get("source_sha256")
    if manifest.get("build") != RETAIL_BUILD_NAME or source_sha != expected_source_sha256:
        raise ValueError("binding manifest does not identify the expected retail executable build")
    if _sha256(original_data) != source_sha:
        raise ValueError("original backup SHA-256 does not match the manifest")
    if manifest.get("backup_name") != backup_path.name or manifest.get("output_exe_name") != output_path.name:
        raise ValueError("manifest does not belong to this output/backup pair")
    if manifest.get("status") == "restored":
        if not output_path.is_file() or _sha256(output_path.read_bytes()) != source_sha:
            raise ValueError("manifest says restored, but output is not the original executable")
        return {"status": "ALREADY_RESTORED", "output_exe": str(output_path), "sha256": source_sha}
    if manifest.get("status") != "applied":
        raise ValueError("manifest is not in an applied state")
    if not output_path.is_file() or _sha256(output_path.read_bytes()) != manifest.get("patched_sha256"):
        raise ValueError("bound output changed since apply; refusing to overwrite it")
    _atomic_write(output_path, original_data)
    manifest["status"] = "restored"
    manifest["restored_sha256"] = source_sha
    manifest["source_exe_modified"] = False
    _atomic_write(manifest_path, (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return {"status": "RESTORED_COPY", "output_exe": str(output_path), "sha256": source_sha}
