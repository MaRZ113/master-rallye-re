"""Landscape-count bisection after E1.1 (diag1..5 all loaded; InvFrance with 5 crashed).

Stock FranceM scene plus additional France stage models, identity matrices:

* InvDiag6: 3 landscapes (FranceM, FranceS1, FranceS2)
* InvDiag7: 4 (+ FranceW)
* InvDiag8: 5 (+ France1)
* InvDiag9: 6 (+ France2)
* MRallye_diag8_laa.exe: InvDiag8 with IMAGE_FILE_LARGE_ADDRESS_AWARE set (4 GB
  user space on 64-bit Windows) to separate address-space exhaustion from a
  hard landscape limit.
"""
from __future__ import annotations

import copy
import hashlib
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETAIL = ROOT.parent / "corpora/retail/Data.sma_unpacked/DataScene/RaceTest"
OUT = ROOT / "research-output/invitation_concept/diag2"
EXTRA = (("FranceS1", "course\\france_s1\\frances1"), ("FranceS2", "course\\france_s2\\frances2"),
         ("FranceW", "course\\france_w\\francew"), ("France1", "course\\france1\\france1"),
         ("France2", "course\\france2\\france2"))


def hnt(name: str) -> bytes:
    return next(p for p in RETAIL.glob("*.hnt") if p.stem.lower() == name.lower()).read_bytes()


def main() -> int:
    scenes = OUT / "DataScene/RaceTest"
    exe_dir = OUT / "exe"
    scenes.mkdir(parents=True, exist_ok=True)
    exe_dir.mkdir(parents=True, exist_ok=True)
    for number, extra_count in ((6, 2), (7, 3), (8, 4), (9, 5)):
        root = ET.fromstring((RETAIL / "FranceM.xml").read_bytes())
        lst = next(l for l in root.iter("List") if l.get("Name") == "landscape")
        prototype = lst.find("Egg")
        manifest = hnt("FranceM")
        for stem, model in EXTRA[:extra_count]:
            egg = copy.deepcopy(prototype)
            egg.find("Value[@Name='en3d Model Name']").set("Value", model)
            lst.append(egg)
            manifest += hnt(stem)
        (scenes / f"InvDiag{number}.xml").write_bytes(ET.tostring(root, encoding="unicode").encode("utf-8"))
        (scenes / f"InvDiag{number}.hnt").write_bytes(manifest)
        target = exe_dir / f"MRallye_diag{number}.exe"
        subprocess.run([sys.executable, str(ROOT / "tools/patch_invitation_entries.py"), str(ROOT.parent / "MRallye.exe"),
                        str(target), "--names", f"InvDiag{number},InvTurkey,InvItaly"], check=True, capture_output=True)
        print(target.name, "->", 1 + extra_count, "landscapes")
    data = bytearray((exe_dir / "MRallye_diag8.exe").read_bytes())
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    characteristics = struct.unpack_from("<H", data, pe + 22)[0]
    struct.pack_into("<H", data, pe + 22, characteristics | 0x20)
    (exe_dir / "MRallye_diag8_laa.exe").write_bytes(data)
    print("MRallye_diag8_laa.exe -> 5 landscapes, LAA", hashlib.sha256(data).hexdigest()[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
