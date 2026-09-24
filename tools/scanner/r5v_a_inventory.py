"""Read-only vehicle evidence inventory for the local PC builds.

Only metadata is written. Original game files are never copied or changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


COMMON = {"Tyres", "Custom"}


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def xml_values(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    root = ET.parse(path).getroot()
    return [element.attrib for element in root.iter("Value") if "Name" in element.attrib]


def physics_sections(path: Path) -> list[dict]:
    sections: dict[str, dict] = {}
    for value in xml_values(path):
        parts = value["Name"].split("/")
        if len(parts) < 3 or parts[0] != "Vehicles" or parts[1] in COMMON:
            continue
        section = sections.setdefault(parts[1], {"name": parts[1], "value_count": 0, "fields": []})
        section["value_count"] += 1
        section["fields"].append("/".join(parts[2:]))
    for section in sections.values():
        section["fields"] = sorted(set(section["fields"]))
    return list(sections.values())


def folders(path: Path) -> list[dict]:
    if not path.is_dir():
        return []
    result = []
    for folder in sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name.casefold()):
        files = sorted((p for p in folder.iterdir() if p.is_file()), key=lambda p: p.name.casefold())
        result.append({
            "name": folder.name,
            "files": [{"name": p.name, "size": p.stat().st_size, "sha256": sha256(p)} for p in files],
            "dx_roles": {role: (folder / role).is_file() for role in ("car.dx", "complete.dx", "wheel.dx")},
            "dxt_count": sum(p.suffix.casefold() == ".dxt" for p in files),
        })
    return result


def exe_strings(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    data = path.read_bytes()
    return [{"offset": f"0x{m.start():08X}", "text": m.group().decode("ascii")}
            for m in re.finditer(rb"[ -~]{4,}", data)]


def named_values(root: Path, relative: str, pattern: str) -> list[dict]:
    path = root / relative
    if not path.is_file():
        path = root / "Data.sma_unpacked" / relative
    return [{"name": v["Name"], "value": v.get("Value"),
             "save_player_state": v.get("SavePlayerState")}
            for v in xml_values(path) if re.search(pattern, v["Name"], re.I)]


def inventory(root: Path, label: str) -> dict:
    game = root / "DataGame"
    if not (game / "vehicles.xml").is_file():
        game = root / "Data.sma_unpacked" / "DataGame"
    gx = root / "DataGx" / "Vehicles"
    if not gx.is_dir():
        gx = root / "Data.sma_unpacked" / "DataGx" / "Vehicles"
    scene = root / "DataScene"
    if not scene.is_dir():
        scene = root / "Data.sma_unpacked" / "DataScene"
    car_name_refs = []
    if scene.is_dir():
        for xml in scene.rglob("*.xml"):
            try:
                values = xml_values(xml)
            except ET.ParseError:
                continue
            for value in values:
                if value["Name"] == "Car Name":
                    car_name_refs.append({"path": xml.relative_to(scene).as_posix(), "name": value.get("Value")})
    exe = root / "MRallye.exe"
    archive = root / "Data.sma"
    strings = exe_strings(exe)
    return {
        "build": label,
        "source_note": "External local game corpus; no binary or asset content copied",
        "hashes": {"MRallye.exe": sha256(exe), "Data.sma": sha256(archive),
                   "vehicles.xml": sha256(game / "vehicles.xml")},
        "physics_sections_xml_order_not_registry_order": physics_sections(game / "vehicles.xml"),
        "vehicle_folders_not_registry_order": folders(gx),
        "frontend_state": named_values(root, "DataGame/frontend.xml", r"Car\d|Vehicle|CurrentClass"),
        "scene_car_name_refs": car_name_refs,
        "progress_unlocks": named_values(root, "DataGame/Progress.xml", r"UnlockedCars|UnlockCars"),
        "cup_car_state": named_values(root, "DataGame/RallyeCup.xml", r"Car"),
        "master_car_state": named_values(root, "DataGame/MasterRallye.xml", r"Car"),
        "exe_vehicle_anchor_strings": [s for s in strings if re.search(
            r"(?i)forklift|vehicles/|VehicleSelect|CarModelDataFile|Car%d|CarID %d", s["text"])],
        "exe_ascii_string_count": len(strings),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("label")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = inventory(args.source, args.label)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.label}: {len(result['physics_sections_xml_order_not_registry_order'])} physics sections, "
          f"{len(result['vehicle_folders_not_registry_order'])} asset folders")


if __name__ == "__main__":
    main()
