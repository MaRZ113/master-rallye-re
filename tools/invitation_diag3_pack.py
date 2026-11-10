"""Landscape count vs. texture count (after diag6..9 all crashed, LAA included).

* InvDiag10 (T1): stock FranceM with the FranceM landscape egg three times:
  three landscapes, 99 HNT textures.
* InvDiag11 (T2): stock TurkeyM plus the Turkey1 model: two landscapes,
  254 HNT textures (plus the scene's own sky/checkpoint/car textures).

diag1 (2 landscapes, 177 textures) loaded; diag6 (3 landscapes, 274 textures)
crashed. T1 isolates the landscape count, T2 the texture count.
"""
from __future__ import annotations

import copy
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETAIL = ROOT.parent / "corpora/retail/Data.sma_unpacked/DataScene/RaceTest"
OUT = ROOT / "research-output/invitation_concept/diag3"


def hnt(name: str) -> bytes:
    return next(p for p in RETAIL.glob("*.hnt") if p.stem.lower() == name.lower()).read_bytes()


def scene(base: str, extra_models: list[str]) -> bytes:
    root = ET.fromstring((RETAIL / f"{base}.xml").read_bytes())
    lst = next(l for l in root.iter("List") if l.get("Name") == "landscape")
    for model in extra_models:
        egg = copy.deepcopy(lst.find("Egg"))
        egg.find("Value[@Name='en3d Model Name']").set("Value", model)
        lst.append(egg)
    return ET.tostring(root, encoding="unicode").encode("utf-8")


def main() -> int:
    scenes, exe_dir = OUT / "DataScene/RaceTest", OUT / "exe"
    scenes.mkdir(parents=True, exist_ok=True)
    exe_dir.mkdir(parents=True, exist_ok=True)
    cases = {
        10: (scene("FranceM", ["course\\france_m\\francem"] * 2), hnt("FranceM")),
        11: (scene("TurkeyM", ["course\\turkey1\\turkey1"]), hnt("TurkeyM") + hnt("Turkey1")),
    }
    for number, (xml, manifest) in cases.items():
        (scenes / f"InvDiag{number}.xml").write_bytes(xml)
        (scenes / f"InvDiag{number}.hnt").write_bytes(manifest)
        subprocess.run([sys.executable, str(ROOT / "tools/patch_invitation_entries.py"), str(ROOT.parent / "MRallye.exe"),
                        str(exe_dir / f"MRallye_diag{number}.exe"), "--names", f"InvDiag{number},InvTurkey,InvItaly"],
                       check=True, capture_output=True)
        print(f"MRallye_diag{number}.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
