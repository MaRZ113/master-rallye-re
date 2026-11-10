"""Create an EXE *copy* whose Invitation races (Race IDs 36..38) load new RaceTest scenes.

Retail ``FUN_004598d0`` registers 39 race records (IDs 0..38, 0x2C bytes each,
``registry+0x54C``) by pushing a ``RaceTest/<name>`` string before each
``FUN_0045a330`` call. Invitation reuses the FranceS1/Turkey3/ItalyM1 string
pointers also used by Race IDs 24/9/29. This tool changes only the three
Invitation ``push imm32`` operands so the shared stock entries stay untouched.

New strings go into the zero tail of ``.rdata`` (file 0x2AD432..0x2AE000);
``.rdata`` VirtualSize grows to 0x1F000, which still ends at ``.data``'s RVA.
That region is not used by the known vehicle-slot or AI-randomizer patches,
which extend ``.text``. The original EXE is read-only input.

Runtime status: NOT RUNTIME-TESTED. Use the P0 package first (stock XML copies
under new names) to prove the entry mechanism before testing new geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
IMAGE_BASE = 0x400000
RDATA_HEADER_INDEX = 1
RDATA_RVA = 0x28F000
RDATA_RAW = 0x28F000
RDATA_VSIZE_OLD = 0x1E432
RDATA_VSIZE_NEW = 0x1F000
STRING_AREA_VA = 0x6AD440
STRING_AREA_END_VA = 0x6AE000
# (race id, operand VA of `push imm32`, retail string VA, retail string)
INVITATION_SITES = (
    (36, 0x459F5E, 0x6B3E48, "RaceTest/FranceS1"),
    (37, 0x459F8C, 0x6B3F70, "RaceTest/Turkey3"),
    (38, 0x459FBA, 0x6B3DE8, "RaceTest/ItalyM1"),
)




def _va_to_offset(va: int) -> int:
    # .text, .rdata and the file-backed part of .data have identical RVA/raw
    # mapping in the retail image (raw .data ends at file 0x2F6000).
    if not 0x401000 <= va <= 0x6F6000:
        raise PatchError(f"VA 0x{va:X} outside the file-backed image")
    return va - IMAGE_BASE


def _section_header_offset(data: bytes, index: int) -> int:
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    optional_size = struct.unpack_from("<H", data, pe + 20)[0]
    return pe + 24 + optional_size + 40 * index


# Five-race extension (Race IDs 39, 40). Every site is verified before writing.
TEXT_HEADER_INDEX = 0
TEXT_VSIZE_OLD = 0x28D294
TEXT_VSIZE_NEW = 0x28E000          # whole file-backed .text; next section starts at RVA 0x28F000
REGISTER_CAVE_VA = 0x68E384        # free in the pristine image and in the AI/vehicle patch layouts
REGISTER_CAVE_END_VA = 0x68E400
CLAMP_CAVE_VA = 0x68EFC0           # after the AI preview caves (which end <= 0x68EFC0)
CLAMP_CAVE_END_VA = 0x68F000
STRING_CTOR_VA = 0x4D11D0          # std::string(const char*) as used by FUN_004598D0
RACE_REGISTER_VA = 0x45A330
EXTRA_RACES = ((39, 3), (40, 4))   # (race id, stage index inside Invitation)
FIVE_RACE_SITES = (
    # (va, original hex, replacement hex, purpose)
    (0x45A3E0, "000c0000", "580c0000", "registry allocation 0xC00 -> 0xC58 (41 race records)"),
    (0x458D0F, "27", "29", "race array vector-constructor count 39 -> 41"),
    (0x458E29, "27", "29", "race array vector-destructor count 39 -> 41"),
    (0x45B1F4, "26", "28", "FUN_0045B170 Invitation last race 38 -> 40"),
    (0x47F3B6, "27", "29", "FUN_0047F320 race->mode map: Invitation covers IDs 36..40"),
)


class PatchError(RuntimeError):
    pass


def _rel32(source_va: int, size: int, target_va: int) -> bytes:
    return struct.pack("<i", target_va - (source_va + size))


def _register_cave(string_vas: list[int]) -> bytes:
    """Run the replaced race-38 call, register IDs 39/40 like FUN_004598D0, jump back."""
    code = bytearray()

    def call(target: int) -> None:
        code.extend(b"\xe8" + _rel32(REGISTER_CAVE_VA + len(code), 5, target))

    call(RACE_REGISTER_VA)  # race 38: its arguments are already on the stack
    for (race_id, stage), string_va in zip(EXTRA_RACES, string_vas):
        code.extend(bytes.fromhex("6aff6aff518bcc"))            # params 9,10 = -1; string slot; ecx=&slot
        code.extend(b"\x68" + struct.pack("<I", string_va))     # "RaceTest/<name>"
        call(STRING_CTOR_VA)
        code.extend(bytes.fromhex("6a006a006a006a02"))          # params 7,6,5 = 0; param 4 = 2 (as 36..38)
        code.extend(bytes((0x6A, stage, 0x6A, 0x00, 0x6A, race_id)))  # stage, 0, race id
        code.extend(b"\x8d\x8e" + struct.pack("<I", 0x54C + race_id * 0x2C))  # lea ecx,[esi+record]
        call(RACE_REGISTER_VA)
    code.extend(b"\xe9" + _rel32(REGISTER_CAVE_VA + len(code), 5, 0x459FDC))  # pop esi; pop ecx; ret
    return bytes(code)


def _progress_skip_caves() -> tuple[bytes, int, int]:
    """Skip every progress write of FUN_0045B3F0 for stages 4/5 (Race IDs 39/40).

    Retail key tables end at Won_Invitation3 / BestTime_Invitation3; the next
    slots (`__IGNORE`, `BestTime_Master`, ...) are not usable keys, and an
    E1.2 runtime run crashed writing through Won index 109 after race 4.
    """
    won_va = CLAMP_CAVE_VA
    won = bytearray()
    won += bytes.fromhex("85ff0f8e") + _rel32(won_va + 2, 6, 0x45B473)                     # test edi,edi; jle skip
    won += bytes.fromhex("83ff030f8f") + _rel32(won_va + len(won) + 3, 6, 0x45B473)        # cmp edi,3; jg skip
    won += bytes.fromhex("83fb030f8d") + _rel32(won_va + len(won) + 3, 6, 0x45B473)        # cmp ebx,3; jge skip
    won += bytes.fromhex("e9") + _rel32(won_va + len(won), 5, 0x45B43C)                      # original Won write
    best_va = (won_va + len(won) + 1) & ~1
    best = bytearray(bytes.fromhex("8d340383fe267e06"))  # lea esi,[ebx+eax]; cmp esi,0x26; jle normal
    best += bytes.fromhex("5be9") + _rel32(best_va + len(best) + 1, 5, 0x45B50B)  # pop ebx; jmp epilogue (no BestTime)
    best += bytes.fromhex("56e8") + _rel32(best_va + len(best) + 1, 5, 0x4B0310)  # normal: push esi; call
    best += bytes.fromhex("e9") + _rel32(best_va + len(best), 5, 0x45B480)
    padding = bytes(best_va - (won_va + len(won)))
    return bytes(won) + padding + bytes(best), won_va, best_va


def _write(out: bytearray, va: int, original: bytes, replacement: bytes, purpose: str, changes: list) -> None:
    offset = _va_to_offset(va)
    if bytes(out[offset:offset + len(original)]) != original:
        raise PatchError(f"unexpected bytes at 0x{va:X} ({purpose})")
    out[offset:offset + len(replacement)] = replacement
    changes.append({"va": f"0x{va:X}", "original": original.hex(), "replacement": replacement.hex(),
                    "purpose": purpose})


def _apply_five_race_extension(out: bytearray, extra_string_vas: list[int], changes: list) -> None:
    for va, original, replacement, purpose in FIVE_RACE_SITES:
        _write(out, va, bytes.fromhex(original), bytes.fromhex(replacement), purpose, changes)
    cave = _register_cave(extra_string_vas)
    if REGISTER_CAVE_VA + len(cave) > REGISTER_CAVE_END_VA:
        raise PatchError("registration cave overflows its window")
    _write(out, REGISTER_CAVE_VA, bytes(len(cave)), cave, "register Race IDs 39, 40 (code cave)", changes)
    _write(out, 0x459FD7, bytes.fromhex("e854030000"), b"\xe9" + _rel32(0x459FD7, 5, REGISTER_CAVE_VA),
           "FUN_004598D0: last registration continues through the cave", changes)
    # BestTime getter FUN_004B0000 indexes its key table by race ID; index 40
    # is the '__NO_SAVE' sentinel (not a string), which crashed race 5 at start.
    guard_va = (REGISTER_CAVE_VA + len(cave) + 3) & ~3
    guard = bytearray(bytes.fromhex("837c2404277e08c744240426000000"))  # cmp [esp+4],39; jle; mov [esp+4],38
    guard += bytes.fromhex("6aff68e8b86800")                                # original SEH prologue
    guard += bytes.fromhex("e9") + _rel32(guard_va + len(guard), 5, 0x4B0007)
    if guard_va + len(guard) > REGISTER_CAVE_END_VA:
        raise PatchError("BestTime guard overflows the registration window")
    _write(out, guard_va, bytes(len(guard)), bytes(guard), "BestTime read guard: race 40 reads race 38 (code cave)", changes)
    _write(out, 0x4B0000, bytes.fromhex("6aff68e8b86800"), bytes.fromhex("e9") + _rel32(0x4B0000, 5, guard_va)
           + bytes.fromhex("9090"), "FUN_004B0000 BestTime getter enters through the guard", changes)
    caves, won_va, best_va = _progress_skip_caves()
    if CLAMP_CAVE_VA + len(caves) > CLAMP_CAVE_END_VA:
        raise PatchError("progress cave overflows")
    _write(out, CLAMP_CAVE_VA, bytes(len(caves)), caves, "progress skip for stages 4/5 (code cave)", changes)
    _write(out, 0x45B433, bytes.fromhex("85ff7e3c83ff037f37"), bytes.fromhex("e9") + _rel32(0x45B433, 5, won_va) + bytes.fromhex("90909090"),
           "FUN_0045B3F0: no Won/position write for Invitation stages 4/5", changes)
    _write(out, 0x45B477, bytes.fromhex("8d340356e8904e0500"), bytes.fromhex("e9") + _rel32(0x45B477, 5, best_va) + bytes.fromhex("90909090"),
           "FUN_0045B3F0: no BestTime read/write for Race IDs 39/40", changes)
    text_header = _section_header_offset(out, TEXT_HEADER_INDEX)
    if out[text_header:text_header + 5] != b".text":
        raise PatchError("unexpected .text header")
    tvsize, _, traw, _ = struct.unpack_from("<IIII", out, text_header + 8)
    if tvsize != TEXT_VSIZE_OLD or traw < TEXT_VSIZE_NEW:
        raise PatchError("unexpected .text header sizes")
    struct.pack_into("<I", out, text_header + 8, TEXT_VSIZE_NEW)
    changes.append({"text_virtual_size": [f"0x{TEXT_VSIZE_OLD:X}", f"0x{TEXT_VSIZE_NEW:X}"]})


def build_patch(data: bytes, names: list[str], *, keep_cd_attract: bool = False,
                model_cache_mb: int = 384, large_address_aware: bool = True,
                invitation_difficulty: int | None = None) -> tuple[bytearray, dict]:
    if hashlib.sha256(data).hexdigest() != RETAIL_SHA256:
        raise PatchError("input is not the pristine Retail MRallye.exe")
    if len(names) not in (3, 5):
        raise PatchError("three (IDs 36..38) or five (IDs 36..40) Invitation names are required")
    out = bytearray(data)
    header = _section_header_offset(out, RDATA_HEADER_INDEX)
    if out[header:header + 6] != b".rdata":
        raise PatchError("unexpected section order")
    vsize, rva, raw_size, raw_ptr = struct.unpack_from("<IIII", out, header + 8)
    if (vsize, rva, raw_ptr) != (RDATA_VSIZE_OLD, RDATA_RVA, RDATA_RAW) or raw_size < RDATA_VSIZE_NEW:
        raise PatchError("unexpected .rdata header")
    area = out[_va_to_offset(STRING_AREA_VA):_va_to_offset(STRING_AREA_END_VA)]
    if any(area):
        raise PatchError(".rdata tail is not zero; refusing to overwrite")

    cursor = STRING_AREA_VA
    string_vas = []
    for name in names:
        text = f"RaceTest/{name}".encode("ascii") + b"\0"
        if cursor + len(text) > STRING_AREA_END_VA:
            raise PatchError("string area exhausted")
        out[_va_to_offset(cursor):_va_to_offset(cursor) + len(text)] = text
        string_vas.append(cursor)
        cursor = (cursor + len(text) + 15) & ~15
    changes = []
    for (race_id, operand_va, old_va, old_text), string_va in zip(INVITATION_SITES, string_vas):
        operand = _va_to_offset(operand_va)
        if out[operand - 1] != 0x68 or struct.unpack_from("<I", out, operand)[0] != old_va:
            raise PatchError(f"race {race_id}: push operand mismatch at 0x{operand_va:X}")
        old_bytes = out[_va_to_offset(old_va):_va_to_offset(old_va) + len(old_text) + 1]
        if old_bytes != old_text.encode("ascii") + b"\0":
            raise PatchError(f"race {race_id}: retail string mismatch")
        struct.pack_into("<I", out, operand, string_va)
        changes.append({"race_id": race_id, "operand_va": f"0x{operand_va:X}", "old": old_text,
                        "new": f"RaceTest/{names[race_id - 36]}", "string_va": f"0x{string_va:X}"})
    struct.pack_into("<I", out, header + 8, RDATA_VSIZE_NEW)
    if len(names) == 5:
        _apply_five_race_extension(out, string_vas[3:], changes)
    if model_cache_mb != 32:
        # FUN_0053BA80 sets the model cache budget to 32 MB; FUN_0053BE70 evicts
        # least-recently-used models (including the current scene's landscapes)
        # once loaded model sizes exceed it, leaving dangling land databases.
        _write(out, 0x53BA99, bytes.fromhex("00000002"), struct.pack("<I", model_cache_mb << 20),
               f"model cache budget 32 MB -> {model_cache_mb} MB", changes)
    if large_address_aware:
        pe = struct.unpack_from("<I", out, 0x3C)[0]
        characteristics = struct.unpack_from("<H", out, pe + 22)[0]
        struct.pack_into("<H", out, pe + 22, characteristics | 0x20)
        changes.append({"pe_characteristics": [hex(characteristics), hex(characteristics | 0x20)],
                        "purpose": "IMAGE_FILE_LARGE_ADDRESS_AWARE (4 GB user space on 64-bit Windows)"})
    if not keep_cd_attract:
        # Every second Loading screen stats <CD>:\SETUP.DLL; on failure it sets
        # Race/AttractMode, which hijacks multi-race events after race 1.
        # Same 5-byte redirect as the runtime-validated R-AI1.1 hardening
        # (master-rallye-re research/r-ai1-1/attract-loading-fix.md).
        _write(out, 0x464F69, bytes.fromhex("68841f6b00"), bytes((0xE9,)) + _rel32(0x464F69, 5, 0x464F46),
               "Loading media check failure reuses the Race/Starter success path (no forced AttractMode)", changes)
    if invitation_difficulty is not None:
        if not 0 <= invitation_difficulty <= 4:
            raise PatchError("AI difficulty levels are 0 VEasy, 1 Easy, 2 Medium, 3 Hard, 4 Extream")
        # FUN_0045BE10 (Cup/Invitation competitors): for Cup 5 (Invitation) the
        # level is 2 + (rand(1..10) >= 3), i.e. Hard 80 % / Medium 20 %. Replace
        # the computation with a fixed level; Rallye Cups keep their own branch.
        _write(out, 0x45BFB6, bytes.fromhex("33c083ff030f9dc083c0028bf0"),
               bytes((0xBE,)) + struct.pack("<I", invitation_difficulty) + bytes((0x90,)) * 8,
               f"Invitation AI difficulty fixed to {invitation_difficulty}", changes)
    manifest = {
        "schema": "master-rallye-invitation-entries-v2",
        "races": len(names),
        "input_sha256": RETAIL_SHA256,
        "output_sha256": hashlib.sha256(out).hexdigest(),
        "rdata_virtual_size": [f"0x{RDATA_VSIZE_OLD:X}", f"0x{RDATA_VSIZE_NEW:X}"],
        "changes": changes,
        "runtime_status": "3-race retarget CONFIRMED_BY_RUNTIME (P0); 5-race extension NOT_RUNTIME_TESTED",
    }
    return out, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("exe", type=Path, help="pristine Retail MRallye.exe (read-only)")
    parser.add_argument("output", type=Path, help="patched copy path (must differ from input)")
    parser.add_argument("--names", default="InvFrance,InvTurkey,InvItaly",
                        help="three (Race IDs 36..38) or five (36..40) RaceTest scene names")
    parser.add_argument("--model-cache-mb", type=int, default=384,
                        help="model cache budget in MB (Retail 32; 32 keeps the original bytes)")
    parser.add_argument("--no-laa", action="store_true", help="do not set LARGE_ADDRESS_AWARE")
    parser.add_argument("--invitation-difficulty", type=int, default=None,
                        help="fixed Invitation AI level 0..4 (Retail: Hard 80%% / Medium 20%%; 4 = Extream, "
                             "the Challenge 11 level)")
    parser.add_argument("--keep-cd-attract", action="store_true",
                        help="do not apply the Loading media-check AttractMode redirect")
    args = parser.parse_args()
    if args.output.resolve() == args.exe.resolve():
        raise SystemExit("refusing in-place patch")
    patched, manifest = build_patch(args.exe.read_bytes(), [n.strip() for n in args.names.split(",")],
                                    keep_cd_attract=args.keep_cd_attract,
                                    model_cache_mb=args.model_cache_mb, large_address_aware=not args.no_laa,
                                    invitation_difficulty=args.invitation_difficulty)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    args.output.with_suffix(".json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
