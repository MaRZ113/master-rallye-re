"""Headless Workbench previews of a vehicle family (car.dx + wheels, complete.dx) - private, diagnostic only.

``--mode texture`` shows the textures the DX files reference; ``--mode role`` colours each draw (draw-index
palette) which makes shell/glass/interior separation visible.  Requires Blender on PATH or ``--blender``.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.export.obj import export_obj  # noqa: E402
import vmesh_diagnose as diag  # noqa: E402

VIEWS = {"side": (90, 0, 0.62), "q34": (145, 12, 0.62), "front34": (35, 14, 0.62), "top": (90, 89, 0.62)}
DEFAULT_PALETTE = {0: [0.9, 0.5, 0.1], 3: [0.1, 0.3, 0.9], 9: [0.1, 0.1, 0.1], 24: [0.2, 0.9, 0.2], 25: [0.9, 0.9, 0.2]}


def _shift(src: Path, dst: Path, delta) -> None:
    lines = []
    for line in src.read_text().splitlines():
        if line.startswith("v "):
            x, y, z = map(float, line.split()[1:4])
            line = "v %f %f %f" % (x + delta[0], y + delta[1], z + delta[2])
        lines.append(line)
    dst.write_text("\n".join(lines))
    shutil.copy(src.with_suffix(".mtl"), dst.with_suffix(".mtl"))


def render(family: Path, donor: Path, out: Path, mode: str, views: list[str], blender: str,
           colors: dict | None = None, hide: list[int] | None = None, which=("race", "complete")) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    dcar = parse_dx_bytes((donor / "car.dx").read_bytes())
    dcomp = parse_dx_bytes((donor / "complete.dx").read_bytes())
    dy = diag.frame_offset(dcar, dcomp)["dy"]
    hubs = diag.donor_hubs_complete(dcomp)
    objs = {}
    for name in ("complete", "car", "wheel"):
        path = family / f"{name}.dx"
        model = parse_dx_bytes(path.read_bytes(), source=str(path), source_path=path)
        target = out / f"obj_{name}"
        export_obj(model, target, None, family)
        objs[name] = target / "model.obj"
    wheels = []
    for i, (x, y, z) in enumerate(hubs):
        t = out / f"w{i}.obj"
        _shift(objs["wheel"], t, (x, y - dy, z))
        wheels.append(str(t))
    made = []
    sets = {"race": [str(objs["car"])] + wheels, "complete": [str(objs["complete"])]}
    for label in which:
        cfg = {"objs": sets[label], "mode": mode, "out": str(out / label),
               "views": {v: VIEWS[v] for v in views}, "colors": colors or DEFAULT_PALETTE, "hide": hide or []}
        subprocess.run([blender, "-b", "--python", str(Path(__file__).with_name("_vmesh_blender_render.py")), "--",
                        json.dumps(cfg)], check=True, capture_output=True)
        made += [out / f"{label}_{v}.png" for v in views]
    return made


def contact_sheet(images: list[Path], out: Path, cols: int, blender: str) -> Path:
    """Tile ``images`` row-major (``cols`` per row) into one PNG using Blender's image API."""
    subprocess.run([blender, "-b", "--python", str(Path(__file__).with_name("_vmesh_blender_sheet.py")), "--",
                    str(out), str(cols)] + [str(i) for i in images], check=True, capture_output=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family-dir", required=True, type=Path)
    ap.add_argument("--donor-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--mode", choices=("texture", "role"), default="texture")
    ap.add_argument("--views", default="side,q34")
    ap.add_argument("--hide", default="", help="comma list of draw indices to drop (role/texture mode)")
    ap.add_argument("--blender", default="blender")
    args = ap.parse_args()
    hide = [int(x) for x in args.hide.split(",") if x]
    for p in render(args.family_dir.resolve(), args.donor_dir, args.out.resolve(), args.mode, args.views.split(","),
                    args.blender, hide=hide):
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
