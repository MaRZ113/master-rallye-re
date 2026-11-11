#!/usr/bin/env python3
"""EXTRA-GHOST1: relocate the GHOST1 Ghost Mode / five-difficulty caves into a loader-owned region.

The GHOST1 test EXEs (master-rallye-re-ghost, research/ghost, 08e18ec) placed their caves in the
.text slack 0x68E2A0..0x68EE20 and a buffer in .data slack 0x70CC00. SDK33 (Extra Options roster)
occupies that same .text slack, so the loader cannot reuse those addresses. This tool:

1. reassembles both original cave sources at their original bases with tools/ghidra/AsmCave.java and
   requires the pinned GHOST1 bytes (proves the sources are the deployed caves);
2. translates every cave-owned address literal to the loader region (code page RX at BASE, data
   page RW at BASE+0x1000; the INI path moves to a 0x200-byte data slot) and reassembles;
3. independently checks the relocated listing against the original one: same instructions and
   lengths, bytes differ only in translated literals and rel32 branches to the same retail targets;
4. writes src/native/rmod1/extra_ghost_plan.hpp (code page image, hook table, optional NOP spans).

Ghidra is only needed for --assemble; listings are kept in research/extra-ghost1/listings so the
header is reproducible from the committed listings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "research/extra-ghost1"
RETAIL = ROOT.parent / "corpora/retail/MRallye.exe"
RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
GHIDRA = ROOT.parent / "_reverse-tools/ghidra-bridge-main/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat"

BASE = 0x70020000          # after the fixed F3 code/data regions 0x70000000..0x7001FFFF
SIZE = 0x2000
OLD_PAGE, OLD_DATA = 0x68E000, 0x70C000
INI_OLD, INI_NEW, INI_CAPACITY = 0x68ECC0, BASE + 0x1100, 0x200

CAVES = {  # name: (source, original base, sha256 of the GHOST1 bytes)
    "progress": ("ghost_progress_cave.asm", 0x68E2A0,
                 "682ec532dfe4d3ae593508270376a81d742b3009e4795376e10adc4d9818e8cd"),
    "menu": ("ghost3_menu_cave.asm", 0x68E390,
             "5e870739faaf12909e3e3ff303ad268172b199e44bf3daa66633ea9481bb0e25"),
}
ENTRY = {"progress": 0x68E2A0, "modes": 0x68E390, "diff": 0x68E4D8, "fmt": 0x68E508,
         "init": 0x68E57D, "accept": 0x68E5BA, "start": 0x68E639, "focus": 0x68E6EE,
         "initshow": 0x68E7AD, "exithide": 0x68E7D2, "modeidx": 0x68E7EF, "gtype": 0x68E826}
STRINGS = [  # GHOST1 MENU_STRINGS; the INI path is written by the loader at INI_NEW
    (0x68EC00, "Frontend/QuickModeSelect/GhostList"), (0x68EC30, "Frontend/QuickModeSelect/Ghost"),
    (0x68EC50, "Frontend/QuickRace/GhostMode"), (0x68EC70, "VERY EASY"), (0x68EC80, "EXTREME"),
    (0x68EC90, "kernel32.dll"), (0x68ECA0, "GetPrivateProfileIntA"), (0x68ECE0, "Ghost"),
    (0x68ECF0, "WithOpponents"), (0x68ED00, "RecordAllModes"), (0x68ED10, "UseAlphaModel"),
    (0x68ED20, r"DataGx\Vehicles\%sAlpha\car.dx"), (0x68ED40, r"DataGx\Vehicles\%sAlpha\wheel.dx"),
    (0x68ED70, "Vehicles/%s/car"), (0x68ED80, "Vehicles/%s/wheel"),
    (0x68EDA0, "Frontend/QuickModeSelect/LeftArrowGhost"),
    (0x68EDD0, "Frontend/QuickModeSelect/RightArrowGhost"), (0x68EE00, "%s%s%s"),
]
GHOST, DIFFICULTY = 1, 2


def translate(v: int) -> int:
    if v == INI_OLD:
        return INI_NEW
    if OLD_PAGE <= v < OLD_PAGE + 0x1000:
        return BASE + (v - OLD_PAGE)
    if OLD_DATA <= v < OLD_DATA + 0x1000:
        return BASE + 0x1000 + (v - OLD_DATA)
    return v


def rel32(at: int, target: int) -> str:
    return ((target - (at + 5)) & 0xFFFFFFFF).to_bytes(4, "little").hex()


def hooks() -> list[tuple[str, int, int, str, str]]:
    """(id, features, va, old, new). GHOST1 G1..G4.3 table minus file-only / forced / attract entries."""
    e = {k: translate(v) for k, v in ENTRY.items()}
    return [
        ("ghost-sample-fabs", GHOST, 0x4BAF50, "d9442420d84c2420dee9d9fa", "d9442420d8c8dee9d9e1d9fa"),
        ("ghost-progress", GHOST, 0x4BFDE8, "e8f38c0100", "e8" + rel32(0x4BFDE8, e["progress"])),
        ("modes-list", GHOST | DIFFICULTY, 0x479FC0, "8d4c241468a8686b00", "e9" + rel32(0x479FC0, e["modes"]) + "90909090"),
        ("mode-focus", GHOST, 0x47A1C2, "8bc689771083e800740e4874074875166a07eb066a04eb026a01",
         "897710" + "8d447601" + "50" + "90" * 18),
        ("mode-right-arrow", GHOST, 0x47A286, "83fe02", "83fe03"),
        ("mode-init", GHOST, 0x47A560, "e82b3b0300", "e8" + rel32(0x47A560, e["init"])),
        ("mode-accept", GHOST, 0x47A8EE, "e86d370300", "e8" + rel32(0x47A8EE, e["accept"])),
        ("race-start-flags", GHOST, 0x47B871, "e87a280300", "e8" + rel32(0x47B871, e["start"])),
        ("difficulty-level", DIFFICULTY, 0x47B8C8, "40", "90"),
        ("difficulty-right-arrow", DIFFICULTY, 0x47A2CD, "83ff02", "83ff04"),
        ("difficulty-summary", DIFFICULTY, 0x47B70D, "e8dea500008b10556a418bc8ff520c",
         "55" + "e8" + rel32(0x47B70E, e["diff"]) + "90" * 9),
        ("mode-accept-ids", GHOST, 0x47A0A9, "83f808", "83f80b"),
        ("mode-exit-hide", GHOST, 0x47A0E1, "6a04e828c207008bc8e841bf0700", "e8" + rel32(0x47A0E1, e["exithide"]) + "90" * 9),
        ("mode-first-show", GHOST, 0x47A152, "6a016a006a04e8b3c107008bc8e80cbf0700", "e8" + rel32(0x47A152, e["initshow"]) + "90" * 13),
        ("ghost-type-focus", GHOST, 0x47A3CE, "e82db40a00", "e8" + rel32(0x47A3CE, e["focus"])),
        ("summary-mode-text", GHOST, 0x47B3CF, "e81ca900008b108d4eff51eb08", "e8" + rel32(0x47B3CF, e["modeidx"]) + "51" + "eb0d" + "90" * 5),
        ("summary-ghost-type", GHOST, 0x47B43D, "6800596f00", "e8" + rel32(0x47B43D, e["gtype"])),
        ("alpha-car-name", GHOST, 0x4BFE9C, "e819221000", "e8" + rel32(0x4BFE9C, e["fmt"])),
        ("alpha-wheel-name", GHOST, 0x4BFEEE, "e8c7211000", "e8" + rel32(0x4BFEEE, e["fmt"])),
    ]


def run_asm(source: Path, base: int, out: Path) -> None:
    script = source.parent
    cmd = ["powershell", "-NoProfile", "-Command",
           f"& '{GHIDRA}' '{Path.home() / 'AppData/Local/Temp/gh/pcproj'}' PC -process MRallye.exe -readOnly "
           f"-noanalysis -scriptPath '{ROOT / 'tools/ghidra'}' -postScript AsmCave.java '{out}' {base:x} '{source}'"]
    subprocess.run(cmd, check=True, capture_output=True)
    if not out.exists():
        raise SystemExit(f"AsmCave produced no listing for {source}")


def parse_listing(path: Path) -> tuple[bytes, list[tuple[int, bytes, str, str | None]]]:
    lines = path.read_text().splitlines()
    code = bytes.fromhex(lines[0].split()[1])
    ins, label = [], None
    for line in lines[1:]:
        if line.endswith(":"):
            label = line[:-1]
            continue
        m = re.match(r"([0-9a-f]{8})\s+([0-9a-f]+)\s+(.*)", line)
        if m:
            ins.append((int(m.group(1), 16), bytes.fromhex(m.group(2)), m.group(3), label))
            label = None
    return code, ins


def relocate_source(text: str) -> str:
    return re.sub(r"0x[0-9a-fA-F]+", lambda m: hex(translate(int(m.group(0), 16))), text)


def expected_relocation(o: tuple, base_delta: int) -> bytes:
    """Model of the relocated instruction derived from the original one alone."""
    at, b, text, _ = o
    new_at = at + base_delta
    out = bytearray(b)
    op = b[0]
    if op in (0xE8, 0xE9) and len(b) == 5:
        target = (at + 5 + int.from_bytes(b[1:5], "little", signed=True)) & 0xFFFFFFFF
        out[1:5] = ((translate(target) - (new_at + 5)) & 0xFFFFFFFF).to_bytes(4, "little")
        return bytes(out)
    if op == 0x0F and len(b) == 6 and 0x80 <= b[1] <= 0x8F:
        raise SystemExit(f"near Jcc at {at:#x} not expected in GHOST1 caves")
    literals = {int(x, 16) for x in re.findall(r"0x[0-9a-fA-F]+", text)}
    for v in literals:
        if translate(v) == v:
            continue
        raw = v.to_bytes(4, "little")
        hits = [i for i in range(len(b) - 3) if b[i:i + 4] == raw]
        if len(hits) != 1:
            raise SystemExit(f"literal {v:#x} not uniquely encoded at {at:#x}: {text}")
        out[hits[0]:hits[0] + 4] = translate(v).to_bytes(4, "little")
    return bytes(out)


def verify(orig: list, new: list, delta: int) -> int:
    if len(orig) != len(new):
        raise SystemExit("relocated instruction count differs")
    changed = 0
    for o, n in zip(orig, new):
        if n[0] != o[0] + delta or len(n[1]) != len(o[1]) or n[3] != o[3]:
            raise SystemExit(f"layout differs at {o[0]:#x}: {o[2]} / {n[2]}")
        if n[1][0] in (0x66, 0x67):
            raise SystemExit(f"operand-size prefix at {n[0]:#x}")
        model = expected_relocation(o, delta)
        if model != n[1]:
            raise SystemExit(f"unexplained byte change at {o[0]:#x}: {o[1].hex()} -> {n[1].hex()} model {model.hex()}")
        changed += model != o[1]
    return changed


def nop_span(ins: list, first_text: str, count: int, after_label: str) -> tuple[int, int]:
    """Offset/size (relative to BASE) of `count` instructions starting at first_text after a label."""
    start = next(i for i, x in enumerate(ins) if x[3] == after_label)
    for i in range(start, len(ins)):
        if ins[i][2] == first_text:
            span = ins[i:i + count]
            return span[0][0] - BASE, sum(len(x[1]) for x in span)
    raise SystemExit(f"cannot find {first_text} after {after_label}")


def header(page: bytes, hook_rows: list, nops: list) -> str:
    rows = "".join(f'    {{"{i}", {f}u, 0x{va:08x}u, "{old}", "{new}"}},\n' for i, f, va, old, new in hook_rows)
    nop_rows = "".join(f'    {{"{name}", {f}u, 0x{off:04x}u, {size}u}},\n' for name, f, off, size in nops)
    lines = [",".join(f"0x{x:02x}" for x in page[i:i + 24]) for i in range(0, len(page), 24)]
    return (
        "#pragma once\n// Generated by tools/build_extra_ghost_plan.py from research/extra-ghost1 listings. Do not edit.\n"
        "#include <cstdint>\nnamespace extra_ghost_plan {\n"
        f"inline constexpr std::uint32_t kBase = 0x{BASE:08x}u, kSize = 0x{SIZE:x}u, kCodePage = 0x1000u;\n"
        f"inline constexpr std::uint32_t kIniPath = 0x{INI_NEW:08x}u, kIniPathCapacity = 0x{INI_CAPACITY:x}u;\n"
        f"inline constexpr std::uint32_t kGhost = {GHOST}u, kDifficulty = {DIFFICULTY}u;\n"
        f'inline constexpr char kPageSha256[] = "{hashlib.sha256(page).hexdigest()}";\n'
        "struct Hook { const char* id; std::uint32_t features; std::uint32_t va; const char* expected_hex; const char* replacement_hex; };\n"
        "// Applied when any listed feature is enabled.\n"
        f"inline constexpr Hook kHooks[] = {{\n{rows}}};\n"
        "// Cave instructions replaced by NOP when the named feature is DISABLED.\n"
        "struct NopSpan { const char* id; std::uint32_t feature; std::uint32_t offset; std::uint32_t size; };\n"
        f"inline constexpr NopSpan kNops[] = {{\n{nop_rows}}};\n"
        "inline constexpr std::uint8_t kPage[0x1000] = {\n" + ",\n".join(lines) + "\n};\n}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--assemble", action="store_true", help="run Ghidra AsmCave (otherwise reuse listings)")
    ap.add_argument("--check", action="store_true", help="verify the committed header instead of writing it")
    a = ap.parse_args()
    retail = RETAIL.read_bytes()
    if hashlib.sha256(retail).hexdigest() != RETAIL_SHA256:
        raise SystemExit("corpora/retail/MRallye.exe is not the pinned retail build")
    listings = WORK / "listings"
    listings.mkdir(exist_ok=True)
    (WORK / "relocated").mkdir(exist_ok=True)
    page = bytearray(0x1000)
    report = {"base": f"{BASE:#x}", "caves": {}}
    parsed = {}
    for name, (src, old_base, digest) in CAVES.items():
        source = WORK / "source" / src
        moved = WORK / "relocated" / src
        moved.write_text(relocate_source(source.read_text()), newline="\n")
        old_l, new_l = listings / f"{name}.original.txt", listings / f"{name}.relocated.txt"
        if a.assemble:
            for p in (old_l, new_l):
                p.unlink(missing_ok=True)
            run_asm(source, old_base, old_l)
            run_asm(moved, translate(old_base), new_l)
        old_code, old_ins = parse_listing(old_l)
        if hashlib.sha256(old_code).hexdigest() != digest:
            raise SystemExit(f"{name}: original reassembly differs from GHOST1 deployed bytes")
        new_code, new_ins = parse_listing(new_l)
        changed = verify(old_ins, new_ins, translate(old_base) - old_base)
        off = translate(old_base) - BASE
        page[off:off + len(new_code)] = new_code
        parsed[name] = new_ins
        report["caves"][name] = {"offset": f"{off:#x}", "size": len(new_code), "relocated_instructions": changed,
                                 "sha256": hashlib.sha256(new_code).hexdigest()}
    end_code = max(int(c["offset"], 16) + c["size"] for c in report["caves"].values())
    if end_code > 0xC00:
        raise SystemExit("caves overlap the string table")
    for va, text in STRINGS:
        raw = text.encode("ascii") + b"\0"
        off = translate(va) - BASE
        if any(page[off:off + len(raw)]):
            raise SystemExit(f"string {text} overlaps")
        page[off:off + len(raw)] = raw
    rows = hooks()
    used = []
    for i, f, va, old, new in rows:
        o, n = bytes.fromhex(old), bytes.fromhex(new)
        if len(o) != len(n) or retail[va - 0x400000:va - 0x400000 + len(o)] != o:
            raise SystemExit(f"{i}: retail preimage differs")
        if any(va < b and a2 < va + len(o) for a2, b in used):
            raise SystemExit(f"{i}: overlaps another hook")
        used.append((va, va + len(o)))
    menu = parsed["menu"]
    nops = [("ghost-mode-entry", GHOST) + nop_span(menu, "PUSH 0x1", 3, "modes_lbl"),
            ("difficulty-list-entries", DIFFICULTY) + nop_span(menu, "MOV EBX,EDI", 7, "modes_lbl")]
    report["nops"] = [{"id": n[0], "offset": f"{n[2]:#x}", "size": n[3]} for n in nops]
    out = ROOT / "src/native/rmod1/extra_ghost_plan.hpp"
    text = header(bytes(page), rows, nops)
    if a.check:
        if out.read_bytes().replace(b"\r\n", b"\n") != text.encode("ascii"):
            raise SystemExit("extra_ghost_plan.hpp differs from the committed listings")
        print("PASS extra_ghost_plan.hpp reproduces from listings")
        return
    out.write_bytes(text.encode("ascii"))
    report["page_sha256"] = hashlib.sha256(bytes(page)).hexdigest()
    report["hooks"] = len(rows)
    (WORK / "plan-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
