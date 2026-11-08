#!/usr/bin/env python3
"""GHOST1 G1 test kit: re-enable the retail Ghost Mode chain without a menu.

Builds a patched COPY of the retail MRallye.exe and a loose-file kit:

* ``--exe-name`` (default ``MRallye_ghost1.exe``) - retail EXE with the byte patches in ``patches()``;
* ``DataGx/Vehicles/<Car>Alpha`` - demo Alpha vehicle resources upgraded from
  DX revision 131 to retail revision 135 with the R-DEMO DX Upgrader;
* ``Ghosts/*.ghost`` - optional seed ghost files copied unchanged.

The retail EXE, demo folders and seed ghosts are only read. Output goes to a
new directory that must not exist yet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
IMAGE_BASE = 0x400000  # .text, .rdata and .data have raw offset == RVA in retail

# Ghost type index read through Frontend/QuickRace/Ghost (0x4AE0F0).
# 0x4BC030 (best ever) reads type 1, 0x4BC170 (session best) reads type 0.
GHOST_TYPES = {"sessionbest": 0, "bestever": 1, "steelmonkeys": 2}

# Assembled from research/ghost1/ghost_progress_cave.asm with tools/ghidra/AsmCave.java at
# PROGRESS_CAVE_VA (zero padding after .text VirtualSize). All branches are short; calls are E8 rel32.
PROGRESS_CAVE_VA = 0x68E2A0
PROGRESS_CAVE_HEX = (
    "535657558b74241856ff742418e82ea8e4ff83ec08685cf66a008d4c2404e8bd22e4ff8d042450e8f46ee5ff"
    "89c1e84d6ae5ff85c0741d8b78048b480885ff741389c829f899bb48000000f7fb89c383fb027d0a83c408"
    "5d5f5e5bc20800c7442404ffff7f7f31c983cdff8d5738d902d826d8c8d94204d86604d8c8dec1d94208d8"
    "6608d8c8dec1d8542404dfe09e7306d954240489cdddd84183c24839d97ccd85ed7838896c2404db442404"
    "4b895c2404da742404d95c240468bc516e008d4c2404e81822e4ffff7424048d44240450e84aabe4ff89c1"
    "e8539be4ff83c4085d5f5e5bc20800"
)

# G3 native GHOST mode (research/ghost1/ghost3_menu_cave.asm, assembled at MENU_CAVE_VA).
MENU_CAVE_VA = 0x68E390
MENU_CAVE_HEX = (
    "6083ec0889eb6a016a3ee88400000089fb6a016870ec6800e8b50000006a006880ec6800e8a90000006a10e8"
    "f438f3ff83c40485c0744a89c331c9890b894b04894b08894b0c6a006a3fe8440000006a016a3fe83b000000"
    "6a026a3fe8320000006800ec68008d4c2404e88121e4ff538d44240450e8b6aae4ff89c1e86fa4e4ff83c408"
    "618d4c241468a8686b00e9a6bbdeff83ec04e8c578dfff8b10ff74240cff74240c89c1ff520c508d4c2404e8"
    "8c2de4ff8d0c24516a01ff730889d9e8dc96d7ffff3424e8a467f2ff83c408c2080083ec04ff7424088d4c24"
    "04e85e2de4ff8b4308837c240c0074038b43048d0c24516a015089d9e8a396d7ffff3424e86b67f2ff83c408"
    "c208006890ec6800ff1538f2680085c0742768a0ec680050ff15c0f0680085c0741768c0ec6800ff74240cff"
    "74240c68e0ec6800ffd0c208008b442408c208008b44240485c07508b870ec6800c2040083f8047c08b880ec"
    "6800c204004850e8f477dfff8b106a4189c1ff520cc2040053565781ec000100008bb42414010000bb20ed68"
    "00bf70ed680081fee86e6e00740abb40ed6800bf80ed68006a016810ed6800e85bffffff85c07424ffb42418"
    "010000538d44240850e8643bf3ff83c40c8d042450ff1500f1680083f8ff750789bc241401000081c4000100"
    "005f5e5be93d3bf3ffe80efbe1ff83f801753283ec046850ec68008d4c2404e8e81fe4ff8d042450e81fa9e4"
    "ff89c1e8b881e4ff83c40485c0b8010000007405b804000000c3515383ec0431db837c2410047547c7442410"
    "01000000436830ec68008d4c2404e8a11fe4ff8d042450e8d8a8e4ff89c1e87181e4ff5068b4586e008d4c24"
    "08e8821fe4ff8d44240450e8b8a8e4ff89c1e8f199e4ff6850ec68008d4c2404e8631fe4ff538d44240450e8"
    "98a8e4ff89c1e8d199e4ff83c4045b59e927fae1ff51535683ec046850ec68008d4c2404e8331fe4ff8d0424"
    "50e86aa8e4ff89c1e80381e4ff31db85c00f95c37522e89500e2ff89c1e81efae1ff83f80275116a0068f0ec"
    "6800e818feffff85c00f95c389de85f675156a006800ed6800e801feffff85c00f95c389de31db68d41d6b00"
    "8d4c2404e8cf1ee4ff538d44240450e804a8e4ff89c1e8dd93e4ff68bc1d6b008d4c2404e8af1ee4ff568d44"
    "240450e8e4a7e4ff89c1e8bd93e4ff83c4045e5b59e902fae1ffe80d71e9ff53565083ec0468e86a6b008d4c"
    "2404e8791ee4ff8d042450e8b0a7e4ff89c1e84980e4ff31db83f8030f94c36830ec68008d4c2404e8531ee4"
    "ff8d042450e88aa7e4ff89c1e82380e4ff89c631c085f60f9fc021d85068a0ed68008d4c2408e8291ee4ff8d"
    "44240450e85fa7e4ff89c1e89898e4ff31c083fe020f9cc021d85068d0ed68008d4c2408e8ff1de4ff8d4424"
    "0450e835a7e4ff89c1e86e98e4ff83c4045883f80a7505b80100000083f80b7505b8030000005e5bc36a016a"
    "006a04e8587be6ff89c1e8b178e6ff6a016a006a05e8467be6ff89c1e89f78e6ffc36a04e8377be6ff89c1e8"
    "5078e6ff6a05e8297be6ff89c1e84278e6ffc35383ec046850ec68008d4c2404e87f1de4ff8d042450e8b6a6"
    "e4ff89c1e84f7fe4ff31db85c00f95c383c404e8d074dfff8b1089d95bc3515283ec046850ec68008d4c2404"
    "e8471de4ff8d042450e87ea6e4ff89c1e8177fe4ff85c0b800596f00745b68b4586e008d4c2404e8201de4ff"
    "8d042450e857a6e4ff89c1e8f07ee4ff50e87a74dfff8b106a3f89c1ff520c50689c576b006a02e86474dfff"
    "8b106a1c89c1ff520c506800ee68006800cc7000e81538f3ff83c414b800cc700083c4045a59870424ffe0"
)
MENU_ENTRY = {"modes": 0x68E390, "diff": 0x68E4D8, "fmt": 0x68E508, "init": 0x68E57D,
              "accept": 0x68E5BA, "start": 0x68E639, "focus": 0x68E6EE, "initshow": 0x68E7AD,
              "exithide": 0x68E7D2, "modeidx": 0x68E7EF, "gtype": 0x68E826}
MENU_STRINGS = [
    (0x68EC00, 'Frontend/QuickModeSelect/GhostList'),
    (0x68EC30, 'Frontend/QuickModeSelect/Ghost'),
    (0x68EC50, 'Frontend/QuickRace/GhostMode'),
    (0x68EC70, 'VERY EASY'),
    (0x68EC80, 'EXTREME'),
    (0x68EC90, 'kernel32.dll'),
    (0x68ECA0, 'GetPrivateProfileIntA'),
    (0x68ECC0, r'.\MRallyeExtras.ini'),
    (0x68ECE0, 'Ghost'),
    (0x68ECF0, 'WithOpponents'),
    (0x68ED00, 'RecordAllModes'),
    (0x68ED10, 'UseAlphaModel'),
    (0x68ED20, r'DataGx\Vehicles\%sAlpha\car.dx'),
    (0x68ED40, r'DataGx\Vehicles\%sAlpha\wheel.dx'),
    (0x68ED70, 'Vehicles/%s/car'),
    (0x68ED80, 'Vehicles/%s/wheel'),
    (0x68EDA0, 'Frontend/QuickModeSelect/LeftArrowGhost'),
    (0x68EDD0, 'Frontend/QuickModeSelect/RightArrowGhost'),
    (0x68EE00, '%s%s%s'),
]


def rel32(at: int, target: int) -> str:
    return ((target - (at + 5)) & 0xFFFFFFFF).to_bytes(4, "little").hex()


def menu_patches() -> list[dict]:
    out = [
        {"va": MENU_CAVE_VA, "old": "00" * (len(MENU_CAVE_HEX) // 2), "new": MENU_CAVE_HEX,
         "why": "G3 code caves: ModeList+GhostList, init/accept/start hooks"},
        {"va": 0x479FC0, "old": "8d4c241468a8686b00",
         "new": "e9" + rel32(0x479FC0, MENU_ENTRY["modes"]) + "90909090",
         "why": "list builder 0x479BB0: JMP cave before publishing ModeList (append GHOST, build GhostList)"},
        {"va": 0x47A1C2, "old": "8bc689771083e800740e4874074875166a07eb066a04eb026a01",
         "new": "897710" + "8d447601" + "50" + "90" * 18,
         "why": "QuickModeSelect update: focus button = 3*mode+1 (1/4/7 as before, 10 for GHOST)"},
        {"va": 0x47A286, "old": "83fe02", "new": "83fe03",
         "why": "QuickModeSelect update: right mode arrow enabled while mode < 3"},
        {"va": 0x47A560, "old": "e82b3b0300", "new": "e8" + rel32(0x47A560, MENU_ENTRY["init"]),
         "why": "QuickModeSelect init: reopen on GHOST when QuickRace mode 1 + GhostMode"},
        {"va": 0x47A8EE, "old": "e86d370300", "new": "e8" + rel32(0x47A8EE, MENU_ENTRY["accept"]),
         "why": "QuickModeSelect accept: GHOST -> QuickRace mode 1, GhostMode, ghost type"},
        {"va": 0x47B871, "old": "e87a280300", "new": "e8" + rel32(0x47B871, MENU_ENTRY["start"]),
         "why": "Quick Race setup: GhostPlayback / Car0 RecordSpline from GhostMode + MRallyeExtras.ini"},
        # G4: five difficulty levels (menu index = ICont level 0..4 VEasy..Extream).
        {"va": 0x47B8C8, "old": "40", "new": "90",
         "why": "Quick Race setup: Race/DifficultyLevel = menu index (was index + 1)"},
        {"va": 0x47A2CD, "old": "83ff02", "new": "83ff04",
         "why": "QuickModeSelect update: difficulty right arrow while index < 4"},
        {"va": 0x47B70D, "old": "e8dea500008b10556a418bc8ff520c",
         "new": "55" + "e8" + rel32(0x47B70E, MENU_ENTRY["diff"]) + "90" * 9,
         "why": "Quick Race summary: difficulty text for ICont level 0..4 (VERY EASY/EXTREME added)"},
        # G4.1: GHOST panel behaviour (owner run: overlay stayed visible, no arrows, Enter ignored).
        {"va": 0x47A0A9, "old": "83f808", "new": "83f80b",
         "why": "QuickModeSelect update: accept button IDs 1..11 (GHOST rows are 10/11)"},
        {"va": 0x47A0E1, "old": "6a04e828c207008bc8e841bf0700",
         "new": "e8" + rel32(0x47A0E1, MENU_ENTRY["exithide"]) + "90" * 9,
         "why": "QuickModeSelect exit: hide panel groups 4 and 5 (retail hid only 2..4)"},
        {"va": 0x47A152, "old": "6a016a006a04e8b3c107008bc8e80cbf0700",
         "new": "e8" + rel32(0x47A152, MENU_ENTRY["initshow"]) + "90" * 13,
         "why": "QuickModeSelect first update: reset panel groups 4 and 5 (retail did 2..4)"},
        {"va": 0x47A3CE, "old": "e82db40a00", "new": "e8" + rel32(0x47A3CE, MENU_ENTRY["focus"]),
         "why": "QuickModeSelect update: GHOST TYPE row arrows + focus 10/11 -> Arrow1/Arrow2 highlight"},
        # G4.2: Quick Race summary shows GHOST and the ghost type.
        {"va": 0x47B3CF, "old": "e81ca900008b108d4eff51eb08",
         "new": "e8" + rel32(0x47B3CF, MENU_ENTRY["modeidx"]) + "51" + "eb0d" + "90" * 5,
         "why": "Quick Race summary: mode 1 text index = 1 (GHOST) when GhostMode, else 0 (PRACTICE)"},
        {"va": 0x47B43D, "old": "6800596f00", "new": "e8" + rel32(0x47B43D, MENU_ENTRY["gtype"]),
         "why": "Quick Race summary: GhostTypeString = ghost type text in GHOST mode (was always empty)"},
        {"file_offset": 0x268, "old": "08e60500", "new": "00f00500",
         "why": ".data VirtualSize 0x5E608 -> 0x5F000: writable buffer 0x70CC00 for GhostTypeString"},
        # G4: Alpha model fallback / UseAlphaModel.
        {"va": 0x4BFE9C, "old": "e819221000", "new": "e8" + rel32(0x4BFE9C, MENU_ENTRY["fmt"]),
         "why": "ghost car model name: plain Vehicles/%s/car if UseAlphaModel=0 or Alpha car.dx missing"},
        {"va": 0x4BFEEE, "old": "e8c7211000", "new": "e8" + rel32(0x4BFEEE, MENU_ENTRY["fmt"]),
         "why": "ghost wheel model name: plain Vehicles/%s/wheel if UseAlphaModel=0 or Alpha wheel.dx missing"},
    ]
    for va, text in MENU_STRINGS:
        raw = text.encode("ascii") + bytes(1)
        out.append({"va": va, "old": "00" * len(raw), "new": raw.hex(), "why": f"string {text}"})
    return out


EXTRAS_INI = r"""[Ghost]
; Read by MRallye_ghost EXE builds on every Quick Race start / ghost load (no restart needed).
; 1 = ghost also appears in Quick Race RACE mode with AI opponents
;     (uses the GHOST TYPE chosen last time in GHOST mode).
WithOpponents = 0
; 1 = record ghost files in every Quick Race mode, not only GHOST.
RecordAllModes = 0
; 1 = translucent <Car>Alpha ghost model when DataGx\Vehicles\<Car>Alpha exists;
; 0 = ghost always uses the normal car model.
UseAlphaModel = 1
"""

FORCE_VAS = {0x449245, 0x44926A, 0x4AE0F0}  # G1 constant enables, replaced by the G3 menu


def patches(ghost_type: int, menu: bool = False) -> list[dict]:
    base = [
        {
            "va": 0x449245,
            "old": "6a00",
            "new": "6a01",
            "why": "gaFrontendAI ctor: Race/GhostPlayback default 0 -> 1",
        },
        {
            "va": 0x44926A,
            "old": "6a00",
            "new": "6a01",
            "why": "gaFrontendAI ctor: Race/Car0/RecordSpline default 0 -> 1",
        },
        {
            "va": 0x48EB14,
            "old": "6a00",
            "new": "6a01",
            "why": "0x48E9C0: keep Race/GhostPlayback=1 when no ghost record was found",
        },
        {
            # Sample decoder 0x4BADC0 rebuilds forward.y = sqrt(1 - x^2 - z^2) from
            # quantised x/z; for a level car the radicand is often slightly negative,
            # FSQRT returns NaN and the ghost matrix is NaN for ~0.8 s ("flying").
            # FLD a; FMUL [a] -> FLD a; FMUL ST0,ST0 frees 2 bytes for FABS.
            "va": 0x4BAF50,
            "old": "d9442420d84c2420dee9d9fa",
            "new": "d9442420d8c8dee9d9e1d9fa",
            "why": "ghost sample decode: forward.y = sqrt(|1 - x^2 - z^2|) instead of NaN",
        },
        {
            "va": 0x4AE0F0,
            "old": "5168b4586e00",
            "new": "b8" + ghost_type.to_bytes(4, "little").hex() + "c3",
            "why": f"Frontend/QuickRace/Ghost reader returns constant {ghost_type}",
        },
        {
            # Same redirect the d3d8 renderer's legacy_attract_guard (R-ATTR1) applies in memory,
            # but only on the exact retail EXE; a patched ghost EXE needs it in the file.
            "va": 0x464F69,
            "old": "68841f6b00",
            "new": "e9d8ffffff",
            "why": "Loading media-check failure -> stock Race/Starter path (no forced AttractMode)",
        },
        # G1.2: restore Race/Ghost/Progress (HUD ghost marker). Demo 9.3.1
        # gaRaceLineAI (0x46D890) wrote it; retail dropped that branch.
        {
            "file_offset": 0x218,
            "old": "94d22800",
            "new": "00e02800",
            "why": ".text VirtualSize 0x28D294 -> 0x28E000 so the code cave lies inside the section",
        },
        {
            "va": PROGRESS_CAVE_VA,
            "old": "00" * (len(PROGRESS_CAVE_HEX) // 2),
            "new": PROGRESS_CAVE_HEX,
            "why": "code cave: call the Race/Ghost/Position setter, then Race/Ghost/Progress = "
                   "nearest RaceLine point / (count-1) (research/ghost1/ghost_progress_cave.asm)",
        },
        {
            "va": 0x4BFDE8,
            "old": "e8f38c0100",
            "new": "e8" + ((PROGRESS_CAVE_VA - (0x4BFDE8 + 5)) & 0xFFFFFFFF).to_bytes(4, "little").hex(),
            "why": "ghost playback update: CALL 0x4D8AE0 (Position setter) -> CALL code cave",
        },
    ]
    if not menu:
        return base
    return [p for p in base if p.get("va") not in FORCE_VAS] + menu_patches()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_exe(src: Path, dst: Path, ghost_type: int, menu: bool = False) -> list[dict]:
    if sha256(src) != RETAIL_SHA256:
        raise SystemExit(f"{src}: not the pinned retail EXE ({RETAIL_SHA256})")
    data = bytearray(src.read_bytes())
    applied = []
    used: list[tuple[int, int]] = []
    for p in patches(ghost_type, menu):
        off = p["file_offset"] if "file_offset" in p else p["va"] - IMAGE_BASE
        old, new = bytes.fromhex(p["old"]), bytes.fromhex(p["new"])
        for a, b in used:
            if off < b and a < off + len(old):
                raise SystemExit(f"patch at file offset {off:#x} overlaps [{a:#x}, {b:#x})")
        used.append((off, off + len(old)))
        if len(old) != len(new) or data[off : off + len(old)] != old:
            raise SystemExit(f"unexpected bytes at file offset {off:#x}")
        data[off : off + len(new)] = new
        entry = {**p, "file_offset": f"{off:#x}"}
        if "va" in p:
            entry["va"] = f"{p['va']:#x}"
        applied.append(entry)
    dst.write_bytes(bytes(data))
    return applied


def upgrade_alpha(upgrader: Path, src_dir: Path, dst_dir: Path) -> None:
    dx_out = dst_dir.parent / (dst_dir.name + ".dx-upgrade")
    subprocess.run(
        [sys.executable, str(upgrader), "--vehicle-dir", str(src_dir), "--output-dir", str(dx_out)],
        check=True,
    )
    dst_dir.mkdir(parents=True)
    for f in src_dir.iterdir():
        if f.suffix.lower() == ".dxt":
            shutil.copy2(f, dst_dir / f.name)
    for f in dx_out.glob("*.dx"):
        shutil.copy2(f, dst_dir / f.name)
    shutil.rmtree(dx_out)


def copy_retail_alpha(src_dir: Path, dst_dir: Path) -> None:
    """<Car>Alpha = the retail race body and wheel of the same car.

    The ghost loads only Vehicles/<Car>Alpha/car and /wheel (0x4BFE00) and sets
    the translucency flag itself, so the retail race resources are a valid
    first approximation of the demo Alpha models (which drop crew/details).
    DX texture slots are bare names resolved in the same folder.
    """
    dst_dir.mkdir(parents=True)
    for f in src_dir.iterdir():
        if f.name.lower() in ("car.dx", "wheel.dx") or f.suffix.lower() == ".dxt":
            shutil.copy2(f, dst_dir / f.name)
    missing = [n for n in ("car.dx", "wheel.dx") if not (dst_dir / n).exists()]
    if missing:
        raise SystemExit(f"{src_dir}: missing {missing}")


DXT_HEADER = 20  # .dxt = 20-byte header + uncompressed BGRA (docs/format-status.md)


def make_translucent(car_dir: Path, vehicles_src: Path, alpha_scale: float) -> dict:
    """G2: turn a retail-copy <Car>Alpha folder into a translucent ghost model.

    Mirrors the demo Alpha folders: every texture alpha is scaled (demo: 0xFF -> 0x7F,
    cut-outs stay 0) and every draw is alpha-blended (draw core +0x20: byte0 alpha on,
    byte1 alpha test off -> SRCALPHA/INVSRCALPHA, see master_rallye.material_semantics).
    Depth write (+0x24 bit 2) is left as authored.
    """
    sys.path.insert(0, str(vehicles_src))
    from master_rallye.dx import parse_dx_bytes  # noqa: E402  (Vehicle SDK reader)

    stats = {"draws_blended": 0, "textures": 0}
    for name in ("car.dx", "wheel.dx"):
        path = car_dir / name
        data = bytearray(path.read_bytes())
        model = parse_dx_bytes(bytes(data), str(path))
        for d in model.physical_draws:
            at = d.core_offset + 0x20
            if data[at] != 1 or data[at + 1] != 0:
                data[at], data[at + 1] = 1, 0
                stats["draws_blended"] += 1
        if parse_dx_bytes(bytes(data), str(path)).physical_draws.__len__() != len(model.physical_draws):
            raise SystemExit(f"{path}: draw count changed after flag edit")
        path.write_bytes(bytes(data))
    for tex in car_dir.glob("*.dxt"):
        data = bytearray(tex.read_bytes())
        w, h = struct.unpack_from("<II", data, 0x0C)
        if len(data) != DXT_HEADER + w * h * 4:
            raise SystemExit(f"{tex}: unexpected .dxt size")
        for i in range(DXT_HEADER + 3, len(data), 4):
            data[i] = int(data[i] * alpha_scale + 0.5)
        tex.write_bytes(bytes(data))
        stats["textures"] += 1
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--retail-exe", type=Path, required=True)
    ap.add_argument("--alpha-mode", choices=("retail-copy", "demo-upgrade"), default="retail-copy")
    ap.add_argument("--alpha-source", type=Path, required=True,
                    help="retail-copy: unpacked retail DataGx/Vehicles; "
                         "demo-upgrade: demo DataGx/Vehicles with <Car>Alpha folders")
    ap.add_argument("--cars", nargs="+", default=["all"],
                    help="car folder names, or 'all' (retail-copy: every folder with car.dx and wheel.dx)")
    ap.add_argument("--ghosts", type=Path, nargs="*", default=[], help="seed .ghost files")
    ap.add_argument("--ghost-type", choices=sorted(GHOST_TYPES), default="bestever")
    ap.add_argument("--upgrader", type=Path, help="R-DEMO tools/upgrade_dx_131_to_135.py (demo-upgrade)")
    ap.add_argument("--exe-name", default="MRallye_ghost1.exe")
    ap.add_argument("--menu", action="store_true", help="G3: native GHOST mode instead of forced ghost")
    ap.add_argument("--frontend-xml", type=Path, help="retail DataScene/FrontendScreens/QuickModeSelect.xml")
    ap.add_argument("--translucent", action="store_true",
                    help="G2: blend every Alpha draw and scale texture alpha (needs --vehicles-src)")
    ap.add_argument("--alpha-scale", type=float, default=127 / 255, help="texture alpha factor (demo: 0x7F/0xFF)")
    ap.add_argument("--vehicles-src", type=Path,
                    help="research/vehicles checkout 'src' folder providing master_rallye.dx")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()

    if a.output.exists():
        raise SystemExit(f"{a.output} already exists")
    a.output.mkdir(parents=True)
    exe = a.output / a.exe_name
    applied = patch_exe(a.retail_exe, exe, GHOST_TYPES[a.ghost_type], a.menu)
    if a.menu:
        if a.frontend_xml is None:
            raise SystemExit("--menu needs --frontend-xml (retail QuickModeSelect.xml)")
        sys.path.insert(0, str(Path(__file__).parent))
        import ghost3_frontend
        ghost3_frontend.main_args(a.frontend_xml, a.output / "DataScene" / "FrontendScreens" / "QuickModeSelect.xml")
        (a.output / "MRallyeExtras.ini").write_text(EXTRAS_INI, encoding="ascii", newline="\r\n")

    vehicles = a.output / "DataGx" / "Vehicles"
    cars = a.cars
    if cars == ["all"]:
        if a.alpha_mode != "retail-copy":
            raise SystemExit("--cars all is only supported with retail-copy")
        cars = sorted(d.name for d in a.alpha_source.iterdir()
                      if (d / "car.dx").exists() and (d / "wheel.dx").exists())
    for car in cars:
        if a.alpha_mode == "retail-copy":
            copy_retail_alpha(a.alpha_source / car, vehicles / f"{car}Alpha")
        else:
            if a.upgrader is None:
                raise SystemExit("demo-upgrade needs --upgrader")
            upgrade_alpha(a.upgrader, a.alpha_source / f"{car}Alpha", vehicles / f"{car}Alpha")
    translucency = {}
    if a.translucent:
        if a.vehicles_src is None:
            raise SystemExit("--translucent needs --vehicles-src")
        for car in cars:
            translucency[car] = make_translucent(vehicles / f"{car}Alpha", a.vehicles_src, a.alpha_scale)
    if a.ghosts:
        (a.output / "Ghosts").mkdir()
        for g in a.ghosts:
            shutil.copy2(g, a.output / "Ghosts" / g.name)

    manifest = {
        "retail_sha256": RETAIL_SHA256,
        "ghost_type": None if a.menu else a.ghost_type,
        "menu": a.menu,
        "patches": applied,
        "translucency": translucency,
        "files": {str(p.relative_to(a.output)).replace("\\", "/"): sha256(p)
                  for p in sorted(a.output.rglob("*")) if p.is_file()},
    }
    (a.output / "ghost1-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"kit: {a.output}\nexe sha256: {sha256(exe)}")


if __name__ == "__main__":
    main()
