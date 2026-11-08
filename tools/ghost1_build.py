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
    "6083ec0889eb6a016a3ee86a0000006a10e80e39f3ff83c40485c0744a89c331c9890b894b04894b08894b0c"
    "6a006a3fe8440000006a016a3fe83b0000006a026a3fe8320000006800e868008d4c2404e89b21e4ff538d44"
    "240450e8d0aae4ff89c1e889a4e4ff83c408618d4c241468a8686b00e9c0bbdeff83ec04e8df78dfff8b10ff"
    "74240cff74240c89c1ff520c508d4c2404e8a62de4ff8d0c24516a01ff730889d9e8f696d7ffff3424e8be67"
    "f2ff83c408c20800e843fce1ff83f801753283ec046850e868008d4c2404e81d21e4ff8d042450e854aae4ff"
    "89c1e8ed82e4ff83c40485c0b8010000007405b804000000c3515383ec0431db837c2410047547c744241001"
    "000000436830e868008d4c2404e8d620e4ff8d042450e80daae4ff89c1e8a682e4ff5068b4586e008d4c2408"
    "e8b720e4ff8d44240450e8eda9e4ff89c1e8269be4ff6850e868008d4c2404e89820e4ff538d44240450e8cd"
    "a9e4ff89c1e8069be4ff83c4045b59e95cfbe1ff515383ec046850e868008d4c2404e86920e4ff8d042450e8"
    "a0a9e4ff89c1e83982e4ff31db85c00f95c368d41d6b008d4c2404e84420e4ff538d44240450e879a9e4ff89"
    "c1e85295e4ff68bc1d6b008d4c2404e82420e4ff538d44240450e859a9e4ff89c1e83295e4ff83c4045b59e9"
    "78fbe1ff"
)
MENU_ENTRY = {"modes": 0x68E390, "init": 0x68E448, "accept": 0x68E485, "start": 0x68E504}
MENU_STRINGS = [
    (0x68E800, "Frontend/QuickModeSelect/GhostList"),
    (0x68E830, "Frontend/QuickModeSelect/Ghost"),
    (0x68E850, "Frontend/QuickRace/GhostMode"),
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
         "why": "Quick Race setup: GhostPlayback / Car0 RecordSpline from GhostMode"},
    ]
    for va, text in MENU_STRINGS:
        raw = text.encode("ascii") + bytes(1)
        out.append({"va": va, "old": "00" * len(raw), "new": raw.hex(), "why": f"string {text}"})
    return out


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
    for p in patches(ghost_type, menu):
        off = p["file_offset"] if "file_offset" in p else p["va"] - IMAGE_BASE
        old, new = bytes.fromhex(p["old"]), bytes.fromhex(p["new"])
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
