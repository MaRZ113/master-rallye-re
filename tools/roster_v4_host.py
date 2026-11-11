"""Roster V4 candidate host: Forklift from PS2, PS2 models for Forklift/ForesterSTI, DEMO model variants.

Derives a fresh sibling host from an owner-tested one (default host-roster-fix-03) without touching it. The native
roster transaction (roster.mrvr) is unchanged; everything here is resource data the VehicleRoster overlay serves:

  * Forklift (ID25): car.dx with the PS2 CAR.PSM tag-101 hull (tools/ps2_collision_hull.py) and the Vehicles/Forklift
    physics block converted from PS2 GAME.XML Vehicles2/Forklift (tools/ps2_vehicle_physics.py --pc-platform);
  * PS2 fleet assets FORKLIFT-CAR-FLEET, FORESTER-CAR-FLEET, FORESTER-COMPLETE-FLEET (tools/ps2_fleet_new_families.py)
    for the renderer built with the matching registry rows;
  * DEMO variants (MODEL = PS2 / PC / DEMO): one resource folder per variant, a physics + modifications block cloned
    from the base family (owner rule: the DEMO model keeps the family's physics), and active/variants.ini with the
    Demo display names, read by the dinput8 Extra Options module.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT.parent
VEH = GAME / "master-rallye-re-vehicles/.research-output/vehicles/auto-import"
# base family block in vehicles.xml, variant folder, variant source folder, Demo names (manufacturer, model)
VARIANTS = [
    ("megane", "Megane", "Heritage841megane", VEH / "demo841/megane-build/DataGx/Vehicles/Heritage841megane",
     "SCHLESSER", "MEGANE 2001", "PC Demo 8.4.1 megane; both Demo catalogs name it SCHLESSER MEGANE 2001"),
    ("LandCruiser", "Landcruiser", "Heritage841LandCruiser", VEH / "demo841/LandCruiser-build/DataGx/Vehicles/Heritage841LandCruiser",
     "TOYOTA", "LANDCRUISER", "PC Demo 8.4.1 TOYOTA LANDCRUISER (retail: TOMMEK DIRTBEAST)"),
    ("Tata", "Tata", "HeritageTata", VEH / "heritage-auto-features/demo-9.3.1-Tata/assets/source/Trooper",
     "TATA", "SAFARI", "PC Demo 9.3.1 Tata, rev131->135 Heritage Garage set; TATA SAFARI in both catalogs"),
    ("NewRav", "Newrav", "HeritageNewRav", None,
     "TOYOTA", "RAV4 PICKUP", "PC Demo 9.3.1 NewRav (former ID34 HeritageNewRav); Demo model label RAV4 PICKUP"),
]
VALUE = re.compile(r'(<Value Name=")Vehicles/([^/"]+)/([^"]+)(")')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clone_blocks(text: str, base: str, variant: str) -> tuple[str, int]:
    """Append (or replace) Vehicles/<variant>/... as a copy of Vehicles/<base>/... lines (CRLF kept)."""
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    kept = [l for l in lines if f'Name="Vehicles/{variant}/' not in l]
    clones = [l.replace(f'Name="Vehicles/{base}/', f'Name="Vehicles/{variant}/', 1) for l in kept
              if f'Name="Vehicles/{base}/' in l]
    if not clones:
        raise ValueError(f"no Vehicles/{base}/ block")
    last = max(i for i, l in enumerate(kept) if f'Name="Vehicles/{base}/' in l)
    return eol.join(kept[:last + 1] + clones + kept[last + 1:]), len(clones)


def copy_host(source: Path, output: Path):
    for p in source.rglob("*"):
        rel = p.relative_to(source)
        dst = output / rel
        if p.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        elif rel.as_posix() == "Data.sma":
            os.link(p, dst)
        elif rel.parts[0] in ("provenance",) or p.suffix == ".log":
            continue
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)


def build(a):
    source, output = a.source_host.resolve(), a.output_host.resolve()
    if output.exists():
        raise ValueError("output host must be fresh")
    copy_host(source, output)
    active = output / "MRMods/Vehicles/active"
    res = active / "resources"
    report = {"schema": "mr-roster-v4-host/1", "source_host": str(source), "changes": []}
    def put(rel: str, data: bytes, why: str):
        path = res / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        report["changes"].append({"path": rel, "sha256": sha(data), "bytes": len(data), "why": why})

    # 1. Forklift collision + physics
    put("DataGx/Vehicles/forklift/car.dx", a.forklift_car.read_bytes(), "PS2 FORKLIFT CAR.PSM tag101 hull; visual bytes unchanged")
    vehicles = a.forklift_vehicles.read_bytes().decode("latin-1")
    mods = (res / "DataGame/Modifications.xml").read_bytes().decode("latin-1")
    # 2. DEMO variants
    ini = ["; Roster V4 DEMO model variants (MODEL = PS2 / PC / DEMO), read by dinput8 Extra Options.",
           "; Base = registry folder of the family; Folder = variant resource folder (physics cloned from Base)."]
    for i, (base, block, folder, src, maker, model, why) in enumerate(VARIANTS):
        vehicles, n = clone_blocks(vehicles, block, folder)
        mods, m = clone_blocks(mods, block, folder)
        if src is not None:
            files = sorted(p for p in src.iterdir() if p.is_file() and p.suffix.lower() in (".dx", ".dxt"))
            for p in files:
                put(f"DataGx/Vehicles/{folder}/{p.name.lower()}", p.read_bytes(), f"DEMO {base}: {why}")
        elif not (res / "DataGx/Vehicles" / folder / "car.dx").is_file():
            raise ValueError(f"{folder} resources missing in the source roster")
        ini += [f"[Variant{i}]", f"Base={base}", f"Folder={folder}", f"Manufacturer={maker}", f"Model={model}", f"; {why}",
                f"; physics: {n} vehicles.xml values and {m} Modifications.xml values cloned from Vehicles/{block}"]
    put("DataGame/vehicles.xml", vehicles.encode("latin-1"), "Forklift PS2 physics + DEMO variant physics clones")
    put("DataGame/Modifications.xml", mods.encode("latin-1"), "DEMO variant modification clones")
    (active / "variants.ini").write_bytes(("\r\n".join(ini) + "\r\n").encode("ascii"))
    # 3. PS2 fleet assets + binaries
    for name in ("FORKLIFT-CAR-FLEET.ps2model", "FORESTER-CAR-FLEET.ps2model", "FORESTER-COMPLETE-FLEET.ps2model"):
        shutil.copyfile(a.ps2_assets / name, output / "PS2Vehicles" / name)
        report["changes"].append({"path": "PS2Vehicles/" + name, "sha256": sha((output / "PS2Vehicles" / name).read_bytes())})
    for name, src in (("d3d8.dll", a.renderer), ("dinput8.dll", a.loader)):
        if src:
            shutil.copyfile(src, output / name)
            report["changes"].append({"path": name, "sha256": sha((output / name).read_bytes())})
    # 4. loader profile: roster.mrvr v1 -> v2 with the MRLP section (roster-independent dinput8)
    if a.addon_plan:
        from roster_loader_profile import build_profile, to_v2
        roster = (active / "roster.mrvr").read_bytes()
        profile, summary = build_profile(roster, a.retail.read_bytes(), (output / "MRallyeRandomizerRuntime.dll").read_bytes(),
                                         json.loads(a.addon_plan.read_text()))
        (active / "roster.mrvr").write_bytes(to_v2(roster, profile))
        report["loader_profile"] = summary
    # 5. catalog: resource list follows the overlay
    catalog = json.loads((active / "catalog.json").read_text(encoding="utf-8"))
    catalog["label"] = "Roster V4 - Forklift PS2, PS2 models, DEMO variants"
    catalog["resources"] = [{"path": p.relative_to(res).as_posix(), "sha256": sha(p.read_bytes()), "size": p.stat().st_size}
                            for p in sorted(res.rglob("*")) if p.is_file()]
    catalog["variants"] = [{"base": v[0], "folder": v[2], "manufacturer": v[4], "model": v[5]} for v in VARIANTS]
    catalog["active_derivation"] = {"tool": "tools/roster_v4_host.py", "source_host": str(source), "native_transaction_unchanged": True,
                                    "roster_format": "MRVR v2 (MRLP loader profile)" if a.addon_plan else "MRVR v1"}
    catalog["roster_mrvr_sha256"] = sha((active / "roster.mrvr").read_bytes())
    (active / "catalog.json").write_text(json.dumps(catalog, indent=1) + "\n", encoding="utf-8")
    (output / "roster-v4-host.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    launcher = output.parent / ("Launch-" + output.name.removeprefix("host-") + ".cmd")
    launcher.write_text('@echo off\npushd "%~dp0' + output.name + '"\nif errorlevel 1 exit /b 1\nstart "" "MRallye.exe"\npopd\n', encoding="ascii")
    return {"output": str(output), "changes": len(report["changes"]), "launcher": str(launcher)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source-host", type=Path, required=True)
    p.add_argument("--output-host", type=Path, required=True)
    p.add_argument("--forklift-car", type=Path, required=True)
    p.add_argument("--forklift-vehicles", type=Path, required=True, help="vehicles.xml with the converted Forklift block")
    p.add_argument("--ps2-assets", type=Path, required=True)
    p.add_argument("--renderer", type=Path)
    p.add_argument("--loader", type=Path)
    p.add_argument("--addon-plan", type=Path, help="V-CAP addon-plan.json: write roster.mrvr v2 with the MRLP loader profile")
    p.add_argument("--retail", type=Path, default=GAME / "corpora/retail/MRallye.exe")
    print(json.dumps(build(p.parse_args()), indent=1))
