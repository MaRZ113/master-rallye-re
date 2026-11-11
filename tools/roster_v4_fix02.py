"""Roster V4 fix 02 (owner test 2026-11-11) applied to a Vehicle Manager store (manager/base + manager/packages).

* DEMO variants stood 0.38..0.51 m too low in Vehicle Select: their complete.dx is lifted so the lowest vertex is at
  y = 0, like every other SDK car (tools/roster_v4.py lift_complete).
* Broken glass showed the red windscreen strip: tools/vehicle_glass_band_fix.py on every generated cracked texture
  (base resources and packages).
* DEMO artwork: the LandCruiser and NewRav variants get their Demo Vehicle Select CarSheet and race small icon
  (PC Demo 8.4.1 carsheet frame 3 = TOYOTA LANDCRUISER, 9.3.1 carsheet frame 17 / smallcarsheet 17 = RAV4 PICKUP;
  8.4.1 has no small icon bank, so the LandCruiser small icon is its CarSheet contained in the small frame).
* ForesterSTI lit tail lights use the PS2 art on the Demo model's lamp geometry (ps2_brake_textures).
Run `vehicle_manager.py apply` afterwards. Idempotent: lifting an already lifted model and band-fixing a fixed texture
change nothing.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from roster_v4 import lift_complete           # noqa: E402
from vehicle_glass_band_fix import fix_dxt, fix_tree, NAMES   # noqa: E402

DEMO = Path(__file__).resolve().parents[2] / "corpora"
ART = {
    "landcruiser-demo.mrcar": {"carsheet": DEMO / "demo-8.4.1/DataGx/Frontend/VehicleSelect/carsheet_003_000.dxt",
                               "smallcarsheet": DEMO / "demo-8.4.1/DataGx/Frontend/VehicleSelect/carsheet_003_000.dxt"},
    "newrav-demo.mrcar": {"carsheet": DEMO / "demo-9.3.1/DataGx/Frontend/VehicleSelect/carsheet_017_000.dxt",
                          "smallcarsheet": DEMO / "demo-9.3.1/DataGx/Frontend/RaceResults/smallcarsheet_017_000.dxt"},
}


def sha(b): return hashlib.sha256(b).hexdigest()


def ps2_brake_textures(base_res: Path) -> dict:
    """ForesterSTI lit tail lights: the PS2 FORESTER art (COMMONTEXTURES BREAKLIGHTSON / BREAKLIGHTSONGLOW) on the
    Demo model's own lamp geometry, which covers the lamp more precisely than the PS2 CAR. RGB from PS2 (resized to
    the PC texture), alpha from the PC texture so the native blending is unchanged."""
    import importlib.util
    root = HERE.parent
    sys.path[:0] = [str(root / "ps2-research/tools"), str(root.parent / "master-rallye-re-vehicles/src")]
    import tngtool as t
    spec = importlib.util.spec_from_file_location("cc", root / "ps2-research/pc-port/docs/vehicle-model-port2/assets/convert_complete.py")
    c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
    from master_rallye.dxt import parse_dxt_bytes, decode_rgba_pixels, encode_dxt_pixels
    from PIL import Image
    ps2 = Path("D:/Game/Master Rallye PS2")
    archive, _ = t.load_pak(ps2 / "TNG.PAK")
    entries = {t.logical_path(e["path"]).upper(): e for e in archive["entries"] if e["kind"] == "file"}
    out = {}
    for pc_name, ps2_name in (("breaklightson-tga", "BREAKLIGHTSON-TGA"), ("breaklightsonglow-tga", "BREAKLIGHTSONGLOW-TGA")):
        raw, _ = t.read_payload(entries[t.logical_path("\\TNG\\DATAPSM\\COMMONTEXTURES\\" + ps2_name + ".GXI").upper()], ps2 / "TNG.000")
        info, px = c.texture(raw)
        rgb = bytearray()
        for i in range(0, len(px), 4):
            rgb += bytes((px[i + 2], px[i + 1], px[i], 255))
        src = Image.frombytes("RGBA", (info["width"], info["height"]), bytes(rgb)).transpose(Image.FLIP_TOP_BOTTOM)
        path = base_res / "DataGx/Vehicles/ForesterSTI" / (pc_name + ".dxt")
        tmpl = parse_dxt_bytes(path.read_bytes())
        pc = decode_rgba_pixels(tmpl)
        src = src.resize((tmpl.width, tmpl.height), Image.BILINEAR).tobytes()
        rgba = bytearray(src)
        rgba[3::4] = pc[3::4]
        data = encode_dxt_pixels(tmpl, bytes(rgba), tmpl.width, tmpl.height)
        path.write_bytes(data)
        out[pc_name] = {"from": ps2_name, "size": [tmpl.width, tmpl.height], "sha256": sha(data)}
    return out


def fix_package(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        manifest = json.loads(z.read("manifest.json"))
        files = {n: z.read(n) for n in z.namelist() if n != "manifest.json"}
    report = {}
    for item in manifest["files"]:
        key, leaf = "files/" + item["path"], item["path"].rsplit("/", 1)[-1].lower()
        data = files[key]
        if leaf == "complete.dx":
            data, lift = lift_complete(data)
            report["complete_lift_m"] = round(lift, 4)
        elif leaf in NAMES:
            fixed, info = fix_dxt(data)
            data = fixed or data
            report[leaf] = info.get("band_rows", 0)
        files[key] = data
        item["sha256"] = sha(data)
    for role, src in ART.get(path.name, {}).items():
        data = src.read_bytes()
        name = f"art/{role}.dxt"
        files[name] = data
        manifest.setdefault("art", {})[role] = {"path": name, "sha256": sha(data), "source": str(src)}
        report[role] = src.name
    tmp = path.with_suffix(".mrcar.new")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in sorted(files.items()):
            z.writestr(n, d)
        z.writestr("manifest.json", json.dumps(manifest, indent=1))
    tmp.replace(path)
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--game", type=Path, required=True)
    a = p.parse_args()
    root = a.game / "MRMods/Vehicles/manager"
    out = {"base": fix_tree(root / "base/resources"), "foresterSTI_brake": ps2_brake_textures(root / "base/resources"),
           "packages": {pk.name: fix_package(pk) for pk in sorted((root / "packages").glob("*.mrcar"))}}
    print(json.dumps(out, indent=1))
