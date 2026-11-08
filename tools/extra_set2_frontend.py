#!/usr/bin/env python3
"""EXTRA-SET2 native frontend pages, derived from the retail scene XML.

* VehicleSetup3.xml (GENERAL): the four rows move up 50 px apart and a fifth TYRE TYPE row
  (native text table 7/8, cloned from the GEARBOX GearType multistate) is added as button 6.
* VehicleSelect.xml: a MODEL row (button 3, cloned from the Class multistate) below the car
  carousel; the car name block moves down 25 px to make room.

VehicleSetup4.xml (GEARBOX) is not produced: the stock page is used unchanged.
Inputs are only read; outputs go to a new directory.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

SCREENS = "DataScene/FrontendScreens"


def value(parent, name, text):
    v = parent.find(f"Value[@Name='{name}']")
    if v is None:
        v = ET.SubElement(parent, "Value", Name=name, Type="Int" if isinstance(text, int) else "String", Value=str(text))
    else:
        v.set("Value", str(text))


def row3(egg):
    m = egg.find("Value[@Name='en2d Matrix']")
    x, y = m.get("Row3").split()[:2]
    return float(x), float(y)


def move(egg, x=None, y=None):
    m = egg.find("Value[@Name='en2d Matrix']")
    ox, oy = row3(egg)
    m.set("Row3", f"{ox if x is None else x:.2f} {oy if y is None else y:.2f} 0.00 1.00")


def section_of(root, egg_name):
    for s in root.iter("List"):
        if s.find(f"Egg[@Name='{egg_name}']") is not None:
            return s
    raise ValueError(f"egg {egg_name} missing")


def control(egg, ai):
    found = egg.find(f".//{ai}")
    if found is None:
        raise ValueError(f"{egg.get('Name')}: {ai} missing")
    return found


def general_page(general: bytes, gearbox: bytes) -> bytes:
    root = ET.fromstring(general)
    gear = ET.fromstring(gearbox)
    s = section_of(root, "BrakeBias")
    eggs = {e.get("Name"): e for e in s.findall("Egg")}
    g = {e.get("Name"): e for e in section_of(gear, "GearType").findall("Egg")}
    need = {"BrakeBias", "CentreLSD", "FrontLSD", "RearLSD", "ScreenType", "DescriptionText1", "DescriptionText2"}
    if not need <= eggs.keys() or not {"GearType", "GearTypeText", "GearLeftArrow", "GearRightArrow"} <= g.keys():
        raise ValueError("unsupported GENERAL/GEARBOX layout")
    if any(control(eggs[n], "gaFrontendStandardButtonAI").find("Value[@Name='Button ID']").get("Value") != str(i)
           for i, n in enumerate(("BrakeBias", "CentreLSD", "FrontLSD", "RearLSD"), 2)):
        raise ValueError("unexpected GENERAL button IDs")
    # Rows keep their stock components; every egg of a row moves with it.
    rows = {"BrakeBias": ("Slider", "Text", "Front", "Rear", 1), "CentreLSD": ("Slider", "Text", 2),
            "FrontLSD": ("Slider", "Text", 3), "RearLSD": ("Slider", "Text", 4)}
    targets = {"BrakeBias": 318.0, "CentreLSD": 268.0, "FrontLSD": 218.0, "RearLSD": 168.0}
    for name, parts in rows.items():
        dy = targets[name] - row3(eggs[name])[1]
        members = [name] + [name + p for p in parts if isinstance(p, str)]
        members += [f"SliderBar{parts[-1]}", f"SliderDots{parts[-1]}"]
        for m in members:
            if m in eggs:
                move(eggs[m], y=row3(eggs[m])[1] + dy)
    for name, y in (("DescriptionText1", 78.0), ("DescriptionText2", 60.0)):
        move(eggs[name], y=y)
    # Navigation 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 1.
    for egg in s.findall("Egg"):
        for c in egg.iter():
            b = c.find("Value[@Name='Button ID']")
            if b is None:
                continue
            if b.get("Value") == "5":
                value(c, "Down Path", 6)
            if b.get("Value") == "1":
                value(c, "Up Path", 6)
    y = 118.0
    tyre = copy.deepcopy(g["GearType"])
    tyre.set("Name", "ExtraTyreType")
    move(tyre, 40.0, y)
    label = control(tyre, "enUITextButtonAI")
    value(label, "Text*", "Null"), value(label, "Text ID#", 7), value(label, "Text ID Index#", 8), value(label, "Text String", "Null")
    m = control(tyre, "gaFrontendMultistateAI")
    for n, v in (("Button ID", 6), ("Up Path", 5), ("Down Path", 1), ("StringList*", "Frontend/ExtraOptions/TireList"),
                 ("Value*", "Frontend/ExtraOptions/Tire"), ("CurrentText*", "Frontend/ExtraOptions/TireText")):
        value(m, n, v)
    text = copy.deepcopy(g["GearTypeText"])
    text.set("Name", "ExtraTyreTypeText")
    move(text, 355.0, y + 8)
    value(control(text, "enUITextButtonAI"), "Text*", "Frontend/ExtraOptions/TireText")
    s.extend([tyre, text])
    for side, x in (("Left", 339.0), ("Right", 591.0)):
        arrow = copy.deepcopy(g[f"Gear{side}Arrow"])
        arrow.set("Name", f"ExtraTyreType{side}Arrow")
        move(arrow, x, y + 10)
        value(control(arrow, "gaFrontendArrowAI"), "Arrow Status*", f"Frontend/ExtraOptions/Tire{side}Arrow")
        s.append(arrow)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8") + b"\n"


def select_page(original: bytes) -> bytes:
    root = ET.fromstring(original)
    s = section_of(root, "Class")
    eggs = {e.get("Name"): e for e in s.findall("Egg")}
    if not {"Class", "SelectCar", "ModeText", "ModeLeftArrow", "ModeRightArrow"} <= eggs.keys():
        raise ValueError("unsupported Vehicle Select layout")
    info = {e.get("Name"): e for e in section_of(root, "ManufacturerName").findall("Egg")}
    for name in ("ManufacturerName", "CarName"):
        move(info[name], y=row3(info[name])[1] - 25)
    value(control(eggs["Class"], "gaFrontendMultistateAI"), "Up Path", 3)
    value(control(eggs["SelectCar"], "gaFrontendStandardButtonAI"), "Down Path", 3)
    y = 275.0
    look = copy.deepcopy(eggs["Class"])
    look.set("Name", "ExtraModel")
    move(look, y=y)
    label = control(look, "enUITextButtonAI")
    value(label, "Text*", "Null"), value(label, "Text ID#", 0), value(label, "Text ID Index#", 0), value(label, "Text String", "MODEL")
    m = control(look, "gaFrontendMultistateAI")
    for n, v in (("Button ID", 3), ("Up Path", 2), ("Down Path", 1), ("StringList*", "Frontend/ExtraOptions/PaintList"),
                 ("Value*", "Frontend/ExtraOptions/Paint"), ("CurrentText*", "Frontend/ExtraOptions/PaintText")):
        value(m, n, v)
    text = copy.deepcopy(eggs["ModeText"])
    text.set("Name", "ExtraModelText")
    move(text, y=y + 6)
    value(control(text, "enUITextButtonAI"), "Text*", "Frontend/ExtraOptions/PaintText")
    s.extend([look, text])
    for side in ("Left", "Right"):
        arrow = copy.deepcopy(eggs[f"Mode{side}Arrow"])
        arrow.set("Name", f"ExtraModel{side}Arrow")
        move(arrow, y=y + 9)
        value(control(arrow, "gaFrontendArrowAI"), "Arrow Status*", f"Frontend/ExtraOptions/Paint{side}Arrow")
        s.append(arrow)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8") + b"\n"


def build(stock: Path, base: Path | None = None) -> dict[str, bytes]:
    """`base` (e.g. an SDK bundle resource root) wins over stock: SDK33 ships its own
    VehicleSelect.xml with extra car buttons/icons, which must be extended, not replaced."""
    def page(name: str) -> bytes:
        for root in ([base] if base else []) + [stock]:
            path = root / SCREENS / name
            if path.is_file():
                return path.read_bytes()
        raise FileNotFoundError(name)
    return {f"{SCREENS}/VehicleSetup3.xml": general_page(page("VehicleSetup3.xml"), page("VehicleSetup4.xml")),
            f"{SCREENS}/VehicleSelect.xml": select_page(page("VehicleSelect.xml"))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stock", type=Path, required=True, help="unpacked retail Data.sma root")
    ap.add_argument("--base", type=Path, help="resource root whose pages override stock (SDK bundle)")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise SystemExit(f"{a.output} already exists")
    pages = build(a.stock, a.base)
    report = {}
    for rel, raw in pages.items():
        out = a.output / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        report[rel] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
