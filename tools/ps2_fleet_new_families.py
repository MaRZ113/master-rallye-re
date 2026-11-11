"""PS2 race (CAR) fleet profiles for the Roster V4 families that the original fleet port left out.

Roster V4 (docs/vehicle-manager/ROSTER_V4_PLAN.md): MODEL = PS2 must show the original PS2 model for
  * Forklift    (ID25, PC folder `forklift`)    <- PS2 VEHICLES\\FORKLIFT\\CAR.PSM  (excluded by the fleet port on request)
  * ForesterSTI (ID30, PC folder `ForesterSTI`) <- PS2 VEHICLES\\FORESTER\\CAR.PSM  (had no PC counterpart before V4;
                                                   WOOLDAND stays the PS2 model of the retail PC Forester)
The conversion is the accepted VEHICLE-CONTINUITY2 one (docs/vehicle-continuity2/fleet-car/prepare_contracts.py and
convert_runtime.py, imported unchanged): whole unconditional PS2 CAR roots replace the whole unconditional PC chassis
set; conditional PC records (brake lamps, state alternatives) and wheels stay native; no damage transfer is granted
(no family damage profile = stock damage fallback in the renderer). New profiles are APPENDED after the 25 existing
ones so every index-keyed renderer table (lamps, wheels, damage) keeps its meaning.

Outputs: <PORT>/.assets/vehicles/<FAMILY>-CAR-FLEET.ps2model and a JSON report with the generated registry rows.
"""
from __future__ import annotations
import argparse, collections, hashlib, importlib.util, json, sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PORT = BASE / "ps2-research/pc-port"
DOCS = PORT / "docs/vehicle-continuity2/fleet-car"
PS2 = Path("D:/Game/Master Rallye PS2")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V4_FAMILIES = ("FORKLIFT", "FORESTER")


def strip_v4(text: str, families=V4_FAMILIES) -> str:
    """Registry text without the rows this tool (and ps2_fleet_damage_new.py) add: every top-level array whose name
    contains FORKLIFT / FORESTER (header through its closing "};") and every profile entry naming them."""
    keep, skipping = [], False
    for line in text.split("\n"):
        if skipping:
            skipping = line.strip() != "};"
            continue
        named = any(f"{f}[]" in line or f" {f}_" in line or f"Source{f}[" in line or f"{f}[" in line for f in families)
        if line.startswith("inline constexpr") and named:
            skipping = not line.rstrip().endswith("};")
            continue
        if line.startswith(" {\"") or line.startswith("{\""):
            if any(f'","{f}",' in line for f in families):
                continue
        keep.append(line)
    return "\n".join(keep)


def contract(pc, entries, t, family, pc_family, pc_car: Path):
    key = t.logical_path("\\TNG\\DATAPSM\\VEHICLES\\" + family + "\\CAR.PSM").upper()
    raw, provenance = t.read_payload(entries[key], PS2 / "TNG.000")
    scene = pc.r.decode_vehicle(raw)
    model = pc.parse_dx(pc_car)
    records = [pc.pc_record(model, d) for d in model.physical_draws]
    # Lit brake geometry is drawn only while braking (owner test 2026-11-11: ForesterSTI records 18/19, textures
    # breaklightson/breaklightsonglow, kept the certificate from ever completing). Like the accepted families'
    # native_glow_or_on_texture proof, such records stay native and are never part of the suppressed chassis.
    for rec in records:
        if any(str(t).lower().startswith(("breaklightson", "brakeon", "brakelighton")) for t in rec["ordered_texture_slots"]):
            rec["whole_chassis_suppress_candidate"] = False
            rec["admission"] = "KEEP_NATIVE_CONDITIONAL_GLOW_OR_ON_SOURCE_BOUNDARY"
    roots = [pc.mesh_row(scene, m) for m in scene.meshes]
    body = [m for m in roots if not m["conditional"]]
    blocks = [dict(path=m["path"], mode=m["mode"]) for m in body if m["mode"] not in (0, 1, 2, 3, 5, 20, 21)]
    if blocks:
        raise ValueError(f"{family}: unsupported unconditional material modes {blocks}")
    row = dict(ps2_family=family, pc_family=pc_family, enabled=False,
               source_ps2_car_sha256=pc.sha(raw), source_pc_car_sha256=pc.sha(pc_car.read_bytes()),
               source_ps2_vertices=scene.vertex_count,
               original_pc_top_level_record_count=model.declared_top_level_record_count,
               native_sources=records, source_roots=roots,
               native_suppression_record_paths=[d["record_path"] for d in records if d["whole_chassis_suppress_candidate"]],
               private_unconditional_root_paths=[m["path"] for m in body],
               private_unconditional_faces=sum(m["faces"] for m in body),
               source_conditional_root_paths=[m["path"] for m in roots if m["conditional"]],
               native_conditional_record_paths=[d["record_path"] for d in records if not d["whole_chassis_suppress_candidate"]])
    row["prototype"] = pc.prepare_source(raw, provenance, scene, family, key, entries)
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--forklift-car", type=Path, required=True, help="PC forklift/car.dx (visual part decides the draw identities)")
    ap.add_argument("--forester-car", type=Path, required=True, help="PC ForesterSTI/car.dx of the installed roster")
    ap.add_argument("--forester-complete", type=Path, help="PC ForesterSTI/complete.dx (menu profile)")
    ap.add_argument("--report", type=Path, required=True)
    a = ap.parse_args()
    pc = load("fleet_prepare_contracts", DOCS / "prepare_contracts.py")
    rt = load("fleet_convert_runtime", DOCS / "convert_runtime.py")
    t = pc.t
    pc.r.w.verify_inputs(PS2)
    archive, _ = t.load_pak(PS2 / "TNG.PAK")
    entries = {t.logical_path(e["path"]).upper(): e for e in archive["entries"] if e["kind"] == "file"}
    default = (PORT / ".assets/vehicles/XTRAIL-default.gxi").read_bytes()
    if rt.c.sha(default) != rt.c.DEFAULT_SHA:
        raise ValueError("Original DEFAULT.GXI changed")
    # Uniqueness against the 25 accepted families (their PC draw identities are in the shipped registry).
    existing = strip_v4((PORT / "renderer/race_fleet_registry.hpp").read_text())
    out = []
    for family, pc_family, car in (("FORKLIFT", "forklift", a.forklift_car), ("FORESTER", "ForesterSTI", a.forester_car)):
        row = contract(pc, entries, t, family, pc_family, car)
        data, profile = rt.convert(row, default)
        path = rt.c.private_output(PORT / ".assets/vehicles" / profile["filename"])
        path.write_bytes(data)
        for src in profile["pc_sources"]:
            src["unique_family_in_paired_car_corpus"] = src["geometry_sha256"] not in existing and \
                sum(s["geometry_sha256"] == src["geometry_sha256"] for s in profile["pc_sources"]) == 1
        ident = profile["ps2_family"]
        lines = ["inline constexpr FleetRaceSource kRaceFleetSource" + ident + "[]={"]
        for src in profile["pc_sources"]:
            lines.append(' {"%s","%s","%s","%s",%du,%du,%s},' % (src["geometry_sha256"], src["ordered_position_sha256"],
                         src["uv_topology_sha256"], src["native_uv_winding_sha256"], src["vertices"], src["faces"],
                         "true" if src["unique_family_in_paired_car_corpus"] else "false"))
        lines.append("};")
        for field, key in (("Mixed", "mixed_reflection"), ("WrapU", "primary_u_wrap")):
            lines.append("inline constexpr bool kRaceFleet" + field + ident + "[]={" +
                         ",".join("true" if m[key] else "false" for m in profile["mesh_secondary_kinds"]) + "};")
        entry = ' {"%s","%s","%s","%s",%du,%du,%du,%du,%du,%du,%du,kRaceFleetSource%s,kRaceFleetMixed%s,kRaceFleetWrapU%s},' % (
            profile["family"], ident, profile["filename"], profile["sha256"], profile["bytes"], profile["vertices"],
            profile["indices"], profile["textures"], profile["ps2_meshes"], len(profile["pc_sources"]),
            profile["native_root_count_candidate"], ident, ident, ident)
        out.append(dict(family=pc_family, ps2_family=family, pc_car=str(car), profile=profile,
                        pc_sources=len(profile["pc_sources"]), unique_sources=sum(s["unique_family_in_paired_car_corpus"] for s in profile["pc_sources"]),
                        suppressed=row["native_suppression_record_paths"], kept_native=row["native_conditional_record_paths"],
                        source_conditional_roots=row["source_conditional_root_paths"], header_arrays=lines, header_entry=entry))
        print(family, profile["ps2_meshes"], profile["indices"] // 3, len(profile["pc_sources"]), profile["sha256"], flush=True)
    complete = complete_profile(pc, a.forester_complete, default) if a.forester_complete else None
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(dict(schema="mr-roster-v4-fleet/1", families=out, frontend=complete), indent=1) + "\n")


def complete_profile(pc, pc_complete: Path, default: bytes):
    """Menu (COMPLETE) profile FORESTER -> ForesterSTI with the accepted CONTINUITY2 frontend converter. Forklift needs
    none: its retail COMPLETE profile is already in frontend_fleet_registry.hpp and its complete.dx is unchanged."""
    models = load("prepare_vehicle_models", PORT / "tools/prepare_vehicle_models.py")
    front = load("frontend_continuity2", PORT / "docs/vehicle-continuity2/frontend/convert_complete_continuity2.py")
    models.prepare(PS2, ["FORESTER"], replace_verified=True)
    original = json.loads((PORT / "docs/vehicle-crew-port1/fleet/coverage.json").read_text())
    row = next(r for r in original["fleet"] if r["ps2_family"] == "FORESTER")
    native = pc.parse_dx(pc_complete)
    draws = [pc.pc_record(native, d) for d in native.physical_draws]
    row = dict(row, pc_family="ForesterSTI")
    row["models"] = dict(row["models"])
    row["models"]["COMPLETE"] = dict(row["models"]["COMPLETE"], pc_compiled_source=dict(
        path=str(pc_complete), sha256=pc.sha(pc_complete.read_bytes()), draws=draws))
    data = (PORT / ".assets/vehicles/FORESTER-COMPLETE.ps2vehicle").read_bytes()
    binary, profile = front.convert(data, row, default)
    profile["filename"] = "FORESTER-COMPLETE-FLEET.ps2model"
    path = front.c.private_output(PORT / ".assets/vehicles" / profile["filename"])
    path.write_bytes(binary)
    existing = strip_v4((PORT / "renderer/frontend_fleet_registry.hpp").read_text(), ("FORESTER",))
    unique = [d["geometry_sha256"] not in existing for d in profile["pc_sources"]]
    lines = ["inline constexpr FrontendSource kFleetSourcesFORESTER[]={"] + \
            [' {"%s",%d,%d},' % (d["geometry_sha256"], d["vertices"], d["faces"]) for d in profile["pc_sources"]] + ["};",
            "inline constexpr bool kFleetUniqueFORESTER[]={" + ",".join("true" if u else "false" for u in unique) + "};",
            "inline constexpr bool kFleetMixedReflectionFORESTER[]={" + ",".join("true" if m["mixed_reflection"] else "false" for m in profile["mesh_secondary_kinds"]) + "};"]
    entry = ' {"%s","%s","%s","%s",%d,%d,%d,%d,%d,%d,kFleetSourcesFORESTER,kFleetUniqueFORESTER,kFleetMixedReflectionFORESTER},' % (
        profile["family"], profile["ps2_family"], profile["filename"], profile["sha256"], profile["bytes"], profile["vertices"],
        profile["indices"], profile["textures"], profile["ps2_meshes"], len(profile["pc_sources"]))
    print("FORESTER COMPLETE", profile["ps2_meshes"], profile["indices"] // 3, len(profile["pc_sources"]), sum(unique), profile["sha256"], flush=True)
    return dict(family="ForesterSTI", ps2_family="FORESTER", pc_complete=str(pc_complete), sha256=profile["sha256"],
                pc_sources=len(profile["pc_sources"]), unique_sources=sum(unique), header_arrays=lines, header_entry=entry)



def apply_registries(report_path: Path):
    """Append the generated rows to the renderer registries (idempotent: refuses if already present)."""
    report = json.loads(report_path.read_text())
    race = PORT / "renderer/race_fleet_registry.hpp"
    text = strip_v4(race.read_text())
    marker = "inline constexpr FleetRaceProfile kRaceFleetProfiles[]={"
    for fam in report["families"]:
        if "kRaceFleetSource" + fam["ps2_family"] + "[]" in text:
            raise ValueError(f"{fam['ps2_family']} already in {race.name}")
        text = text.replace(marker, "\n".join(fam["header_arrays"]) + "\n" + marker)
        head, tail = text.split(marker)
        end = tail.index("\n};")
        text = head + marker + tail[:end] + "\n" + fam["header_entry"] + tail[end:]
    race.write_text(text)
    front = report.get("frontend")
    if front:
        path = PORT / "renderer/frontend_fleet_registry.hpp"
        text = strip_v4(path.read_text(), ("FORESTER",))
        marker = "inline constexpr FleetProfile kFrontendFleetProfiles[]={"
        if "kFleetSourcesFORESTER[]" in text:
            raise ValueError("FORESTER already in frontend registry")
        text = text.replace(marker, "\n".join(front["header_arrays"]) + "\n" + marker)
        head, tail = text.split(marker)
        end = tail.index("\n};")
        path.write_text(head + marker + tail[:end] + "\n" + front["header_entry"] + tail[end:])


if __name__ == "__main__":
    if sys.argv[1:2] == ["--apply"]:
        apply_registries(Path(sys.argv[2]))
    else:
        main()
