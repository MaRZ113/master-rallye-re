"""Join verified EXE constructor records with XML and asset metadata."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

BASE = Path("research/r5v_a")
FILES = {
    "september": BASE / "demo-september-registry.json",
    "november": BASE / "demo-november-registry.json",
    "final": BASE / "final-vehicle-registry.json",
}


def cstring(data: bytes, va: int) -> str:
    offset = va - 0x400000
    end = data.index(0, offset)
    return data[offset:end].decode("ascii")


def final_display_names(exe: Path) -> list[str]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4":
        raise ValueError("Final EXE hash does not match the verified build")
    base = 0x6B99E8
    names = [cstring(data, struct.unpack_from("<I", data, base - 0x400000 + i * 12)[0])
             for i in range(26)]
    assert names[23:26] == ["PRIVATEER ICE CREAM VAN", "STEEL MONKEYS UFO",
                            "STEEL MONKEYS FORKLIFT"]
    return names


def augment(path: Path, display: list[str] | None) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    folders = {x["name"].casefold(): x for x in data["vehicle_folders_not_registry_order"]}
    physics = {x["name"].casefold(): x for x in data["physics_sections_xml_order_not_registry_order"]}
    records = []
    for record in sorted(data["executable_registry"]["records"], key=lambda x: x["index"]):
        name = record["name"]
        key = name.casefold() if name else None
        folder = folders.get(key) if key else None
        section = physics.get(key) if key else None
        index = record["index"]
        numeric = record["raw_numeric_arguments_push_order"]
        refs = sorted({x["path"] for x in data["scene_car_name_refs"]
                       if name and (x["name"] or "").casefold() == key})
        records.append({
            "registry_index": index,
            "internal_name": name,
            "display_name": display[index] if display else None,
            "display_name_evidence": "localized 12-byte table order, cross-checked at indices 23-25"
                                     if display else None,
            "folder": f"DataGx/Vehicles/{folder['name']}" if folder else None,
            "class_id": numeric[-2] if len(numeric) >= 2 else None,
            "numeric_id": numeric[-1] if numeric else None,
            "secondary_numeric_field_uninterpreted": numeric[0] if numeric else None,
            "resource_id": None,
            "physics_section": section["name"] if section else None,
            "physics_value_count": section["value_count"] if section else 0,
            "dx_roles": folder["dx_roles"] if folder else None,
            "dxt_count": folder["dxt_count"] if folder else 0,
            "unlock_state": None,
            "scene_car_name_references": refs,
            "frontend_references": [],
            "ai_references": refs,
            "missing_folder": folder is None,
            "missing_physics": section is None,
            "name_status": record["name_status"],
        })
    data["canonical_registry"] = records
    named = [item for item in records if item["internal_name"]]
    data["registry_summary"] = {
        "named_vehicle_count": len(named),
        "first_named_index": min((item["registry_index"] for item in named), default=None),
        "last_named_index": max((item["registry_index"] for item in named), default=None),
        "record_capacity": data["executable_registry"]["array_capacity"],
        "unresolved_name_indices": data["executable_registry"]["unresolved_name_indices"],
    }
    registered = {x["internal_name"].casefold() for x in records if x["internal_name"]}
    data["unregistered_asset_folders"] = [
        x["name"] for x in data["vehicle_folders_not_registry_order"]
        if x["name"].casefold() not in registered]
    data["unregistered_physics_sections"] = [
        x["name"] for x in data["physics_sections_xml_order_not_registry_order"]
        if x["name"].casefold() not in registered]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(data["build"], len(records), len(data["unregistered_asset_folders"]),
          len(data["unregistered_physics_sections"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("final_exe", type=Path)
    args = parser.parse_args()
    display = final_display_names(args.final_exe)
    for build, path in FILES.items():
        augment(path, display if build == "final" else None)


if __name__ == "__main__":
    main()