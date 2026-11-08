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


def patches(ghost_type: int) -> list[dict]:
    return [
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_exe(src: Path, dst: Path, ghost_type: int) -> list[dict]:
    if sha256(src) != RETAIL_SHA256:
        raise SystemExit(f"{src}: not the pinned retail EXE ({RETAIL_SHA256})")
    data = bytearray(src.read_bytes())
    applied = []
    for p in patches(ghost_type):
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
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()

    if a.output.exists():
        raise SystemExit(f"{a.output} already exists")
    a.output.mkdir(parents=True)
    exe = a.output / a.exe_name
    applied = patch_exe(a.retail_exe, exe, GHOST_TYPES[a.ghost_type])

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
    if a.ghosts:
        (a.output / "Ghosts").mkdir()
        for g in a.ghosts:
            shutil.copy2(g, a.output / "Ghosts" / g.name)

    manifest = {
        "retail_sha256": RETAIL_SHA256,
        "ghost_type": a.ghost_type,
        "patches": applied,
        "files": {str(p.relative_to(a.output)).replace("\\", "/"): sha256(p)
                  for p in sorted(a.output.rglob("*")) if p.is_file()},
    }
    (a.output / "ghost1-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"kit: {a.output}\nexe sha256: {sha256(exe)}")


if __name__ == "__main__":
    main()
