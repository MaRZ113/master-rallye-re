"""Convert a PS2 GAME.XML vehicle descriptor (Vehicles2/<Car>, flat gaVehicleDescriptorXml) to the PC vehicles.xml
schema (Vehicles/<Family>/<Group>/<Key>), Roster V4 (docs/vehicle-manager/ROSTER_V4_PLAN.md, Forklift ID25).

The PC block of the target family is the template: every PC key keeps its type, attributes and order; a key the PS2
descriptor provides gets the PS2 value, a key it does not have (PC-only, e.g. TyreType, ToeVsLong) keeps the PC value
and is reported. Every PS2 key must be consumed, otherwise the conversion is refused.

--self-check maps every PS2 family that also exists in the retail PC vehicles.xml and reports how many values agree,
which proves the name mapping on cars both versions share before it is trusted for the Forklift.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

VALUE = re.compile(r'<Value Name="([^"]+)" Type="([^"]+)" Value="([^"]*)"')
SIDES = ("Front", "Rear")
SUSP_RENAMES = {"RollStiffness": "AuxRollStiffness", "ToeVsBounce": "ToeVsJounce", "CamberVsJounce": "CamverVsJounce",
                "SuspAppPointOffSetLat": "SuspAppPointOffsetLat", "SuspAppPointOffSetLong": "SuspAppPointOffsetLong",
                "SuspAppPointOffSetVert": "SuspAppPointOffsetVert"}


def ps2_descriptors(game_xml: str) -> dict[str, dict[str, tuple[str, str]]]:
    out, current = {}, None
    for line in game_xml.splitlines():
        m = VALUE.search(line)
        if not m:
            continue
        name, typ, value = m.groups()
        if name.startswith("Vehicles2/") and value == "gaVehicleDescriptorXml":
            current = out.setdefault(name.split("/", 1)[1], {})
        elif "XmlData" == typ:
            current = None
        elif current is not None:
            current[name] = (typ, value)
    return out


def pc_blocks(vehicles_xml: str) -> dict[str, list[tuple[str, str, str]]]:
    out = {}
    for line in vehicles_xml.splitlines():
        m = VALUE.search(line)
        if m and m.group(1).startswith("Vehicles/"):
            parts = m.group(1).split("/", 2)
            if len(parts) == 3:
                out.setdefault(parts[1], []).append((parts[2], m.group(2), m.group(3)))
    return out


def fmt(value: float, like: str) -> str:
    decimals = len(like.split(".")[1]) if "." in like else 0
    return f"{value:.{decimals}f}"


def pc_value(key: str, typ: str, like: str, ps2: dict[str, tuple[str, str]], used: set[str]):
    """PS2 value for one PC key in PC text form, or None if the PS2 descriptor has no such value."""
    def take(name):
        if name in ps2:
            used.add(name)
            return ps2[name][1]
        return None
    group, _, leaf = key.partition("/")
    if key == "Chassis/MomentOfInertia":
        parts = [take(n) for n in ("RgyrX", "RgyrY", "RgyrZ")]
    elif key == "Chassis/CentreOfGravity":
        parts = [take(n) for n in ("COGOffSetX", "COGOffsetY", "COGOffsetZ")]
    elif group == "Engine" and leaf.startswith("TorqueEntry") and leaf[11:].isdigit():
        i = leaf[11:]
        parts = [take("TorqueValue" + i), take("TorqueEntry" + i)]
    elif group == "Engine" and re.fullmatch(r"Gear\d+", leaf):
        parts = [take("GearRatio" + leaf[4:])]
    elif group == "Suspension":
        side, _, name = leaf.partition("/")
        source = next((p for p, pc in SUSP_RENAMES.items() if pc == name), name)
        parts = [take(side + source)]
    else:
        parts = [take(leaf)]
    if any(p is None for p in parts):
        return None
    if typ.startswith("Vector"):
        widths = [len(x.split(".")[1]) if "." in x else 0 for x in like.split()]
        return " ".join(f"{float(p):.{w}f}" for p, w in zip(parts, widths))
    if typ == "Float":
        return fmt(float(parts[0]), like)
    if typ == "Bool":
        return parts[0]
    if typ == "Int":
        return str(int(float(parts[0])))
    return parts[0]


def convert(ps2: dict[str, tuple[str, str]], template: list[tuple[str, str, str]]):
    used, values, kept = set(), [], []
    for key, typ, like in template:
        v = pc_value(key, typ, like, ps2, used)
        if v is None:
            kept.append(key)
            v = like
        values.append((key, typ, v))
    # Zero-filled array tails of the flat PS2 schema (TorqueValue/TorqueEntry/GearRatio/ChangeUp/DownRevs past the
    # counts) have no PC key; they must be zero, anything else is an unconsumed value.
    ignored = []
    for name, (typ, value) in ps2.items():
        if name in used:
            continue
        if re.fullmatch(r"(TorqueValue|TorqueEntry|GearRatio|ChangeUpRevs|ChangeDownRevs)\d+", name) and float(value) == 0.0:
            ignored.append(name)
            continue
        if name == "Bonnet Cam":                     # the PC schema has no bonnet camera value (not in DataGame)
            ignored.append(name)
            continue
        if re.search(r"DamageResetScore$", name) and float(value) == 0.0:
            ignored.append(name)
            continue
        raise ValueError(f"PS2 value without a PC key: {name}={value}")
    return values, kept, ignored


def self_check(ps2_all, pc_all):
    report = {}
    lower = {k.lower(): k for k in pc_all}
    for car, ps2 in sorted(ps2_all.items()):
        family = lower.get(car.lower())
        if not family:
            continue
        try:
            values, kept, _ = convert(ps2, pc_all[family])
        except ValueError as e:
            report[car] = {"error": str(e)}
            continue
        same = sum(1 for (k, t, v), (_, _, old) in zip(values, pc_all[family]) if v == old)
        differ = [k for (k, t, v), (_, _, old) in zip(values, pc_all[family]) if v != old]
        report[car] = {"pc_family": family, "keys": len(values), "equal": same, "kept_pc_only": len(kept), "differ": differ}
    return report


# Values the PC port changed identically for (almost) every car that exists on both platforms (see --self-check):
# HandBrakeTorque 2000 -> 4000 on 29/29 pairs, SuspAppPointOffsetVert 0.30/0.35 -> 0.50 on 27/31 pairs.
PC_PLATFORM = {"Chassis/HandBrakeTorque": lambda v: v * 2.0,
               "Suspension/Front/SuspAppPointOffsetVert": lambda v: 0.5 if v in (0.3, 0.35) else v,
               "Suspension/Rear/SuspAppPointOffsetVert": lambda v: 0.5 if v in (0.3, 0.35) else v}


def pc_platform(values):
    out = []
    for key, typ, value in values:
        if key in PC_PLATFORM:
            value = fmt(PC_PLATFORM[key](round(float(value), 4)), value)
        out.append((key, typ, value))
    return out


def apply(vehicles_xml: str, family: str, values) -> str:
    lookup = {f"Vehicles/{family}/{k}": v for k, _t, v in values}
    def sub(m):
        name = m.group(1)
        if name in lookup:
            return f'<Value Name="{name}" Type="{m.group(2)}" Value="{lookup.pop(name)}"'
        return m.group(0)
    out = VALUE.sub(sub, vehicles_xml)
    if lookup:
        raise ValueError(f"keys not written: {sorted(lookup)[:5]}")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--game-xml", type=Path, required=True, help="PS2 TNG/DATAGAME/GAME.XML")
    p.add_argument("--vehicles-xml", type=Path, required=True, help="PC DataGame/vehicles.xml (template and target)")
    p.add_argument("--ps2-car", help="PS2 descriptor name, e.g. Forklift")
    p.add_argument("--family", help="PC family block to replace, e.g. Forklift")
    p.add_argument("--output", type=Path, help="write the converted vehicles.xml here")
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--pc-platform", action="store_true", help="apply the PC port's uniform HandBrake/SuspApp changes")
    a = p.parse_args()
    ps2_all = ps2_descriptors(a.game_xml.read_text(encoding="latin-1"))
    text = a.vehicles_xml.read_bytes().decode("latin-1")
    pc_all = pc_blocks(text)
    if a.self_check:
        print(json.dumps(self_check(ps2_all, pc_all), indent=1))
    if a.ps2_car:
        values, kept, ignored = convert(ps2_all[a.ps2_car], pc_all[a.family])
        if a.pc_platform:
            values = pc_platform(values)
        changed = [(k, old, v) for (k, _t, v), (_k, _t2, old) in zip(values, pc_all[a.family]) if v != old]
        print(json.dumps({"ps2_car": a.ps2_car, "family": a.family, "changed": changed, "kept_pc_only": kept,
                          "ignored_zero_ps2": ignored}, indent=1))
        if a.output:
            a.output.write_bytes(apply(text, a.family, values).encode("latin-1"))
