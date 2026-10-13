"""Read-only HUD-PORT0 source/capture audit; no HUD implementation or export.

Run with the existing Rabbitizer R5900 venv. Original payloads remain in memory;
the report stores paths, hashes, small authored facts and bounded ISA probes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

REPOSITORY = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY / "ps2-research/tools"))
from psbtool import parse_psb, parse_gxi
import tngtool

ELF_SHA = "b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2"
PC_SHA = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
BANKS = ("HUD-TEMPLATE", "NEWHUD", "HUD-DAMAGE", "PACENOTES")
KEYS = {"en2d Model Name", "en2d Image Bank Index", "en2d Matrix", "en2d Visible"}
ELEMENTS = {"SpeedDial", "SpeedNeedle", "SpeedVelocity", "SpeedGear", "GPSBackground",
            "GPSNeedle", "Map", "GameRank", "GameTimer", "ProgressBar", "PauseMenuChooser",
            "PauseMenuTiles", "ConfirmMenuTiles"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def input_fact(path):
    return {"path": str(path), "size": path.stat().st_size,
            "sha256": tngtool.file_hash(path)}


def scene_facts(data):
    result = []
    for egg in ET.fromstring(data).findall(".//Egg"):
        name = egg.get("Name", "")
        if name not in ELEMENTS and not name.startswith("Car0_Damage_"):
            continue
        properties = {v.get("Name"): v.get("Value", v.get("Row3"))
                      for v in egg.findall("Value") if v.get("Name") in KEYS}
        owners = []
        for ai in egg.findall("./AI_List/AI"):
            values = {v.get("Name"): v.get("Value") for v in ai.findall(".//Value")}
            if values.get("AI Name") not in (None, "Null"):
                owners.append(values)
        result.append({"name": name, "properties": properties, "owners": owners,
                       "evidence_grade": "CONFIRMED_BY_BYTES", "runtime_selection": "UNKNOWN"})
    return result


def frame_fact(path):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    header = next(r for r in rows if r.get("type") == "frame_begin")
    if header["exe_sha256"] != PC_SHA:
        raise ValueError("capture is not the verified PC retail executable")
    ui = [r for r in rows if r.get("type") == "draw"
          and r.get("caller", {}).get("return_rva") == 0x16d7c4]
    probe = header.get("ui_margins", {}).get("ui_ownership_probe", {})
    state_keys = [7, 14, 15, 27, 19, 20, 22]
    variants = Counter(tuple(r["state"]["render_states"].get(str(k))
                             for k in state_keys) for r in ui)
    return {"file": path.name, "sha256": sha(path.read_bytes()),
            "frame": header["frame"], "proxy_sha256": header["proxy_sha256"],
            "exe_sha256": header["exe_sha256"], "ui_draws": len(ui),
            "native_forwarded_draws": sum(bool(r["forwarded"]) for r in ui),
            "proxy_result_counts": dict(Counter(str(r["result"]) for r in ui)),
            "hud_preference_hidden": header.get("hud_hide", {}).get("requested_hidden"),
            "hud_context": header.get("hud_hide", {}).get("current_ui_context"),
            "ownership": {k: probe.get(k) for k in ["records", "identity_count", "complete",
                         "coverage_status", "owner_mapping_status", "owner_name_mapping_enabled"]},
            "render_state_key_order": state_keys,
            "tracked_render_state_variants": [{"values": list(k), "draws": n}
                for k, n in sorted(variants.items())],
            "texture_stage0_variants": [{"values": list(k), "draws": n}
                for k, n in sorted(Counter(tuple(r["state"]["texture_stage_states"][0].get(str(k))
                for k in [1, 2, 3, 4, 5, 6, 11]) for r in ui).items())],
            "texture_stage0_key_order": [1, 2, 3, 4, 5, 6, 11],
            "evidence_grade": "CONFIRMED_BY_RUNTIME",
            "limitation": "proxy native forwarding/state tracking; no per-widget semantic owner or pixel attribution"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ps2", type=Path, required=True)
    parser.add_argument("--pc-retail", type=Path, required=True)
    parser.add_argument("--course-sdk", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Pin all canonical sources; verify the large archive once, not per resource.
    canonical = {name: input_fact(args.ps2 / name)
                 for name in ["SLES_509.06", "SYSTEM.CNF", "TNG.PAK", "TNG.000"]}
    previous = json.loads((REPOSITORY / "ps2-research/ui/input-provenance.json").read_text())["inputs"]
    for name, fact in canonical.items():
        if (fact["sha256"], fact["size"]) != (previous[name]["sha256"], previous[name]["size"]):
            raise ValueError(f"canonical input drift: {name}")
    manifest, _ = tngtool.load_pak(args.ps2 / "TNG.PAK")
    by_path = {entry["path"].upper(): entry for entry in manifest["entries"]}

    def payload(path):
        return tngtool.read_payload(by_path[path.upper()], args.ps2 / "TNG.000")

    banks = []
    selected_textures = set()
    for name in BANKS:
        data, provenance = payload("\\TNG\\DATAPSM\\HUD\\" + name + ".PSB")
        parsed = parse_psb(data)
        banks.append({"path": provenance["path"], "size": len(data), "sha256": sha(data),
                      "image_count": len(parsed["images"]),
                      "triangle_count": sum(i["triangle_count"] for i in parsed["images"]),
                      "evidence_grade": "CONFIRMED_BY_BYTES"})
        images = parsed["images"][:3] if name in ["HUD-TEMPLATE", "NEWHUD"] else parsed["images"][:5]
        for image in images:
            for triangle in image["triangles"]:
                resource = triangle["texture_name"]
                if resource != "Null":
                    selected_textures.add("\\TNG\\DATAPSM\\HUD\\" + resource + ".GXI")
    textures = []
    for path in sorted(selected_textures):
        data, provenance = payload(path)
        gxi = parse_gxi(data)
        textures.append({"path": provenance["path"], "size": len(data), "sha256": sha(data),
                         "width": gxi["width"], "height": gxi["height"],
                         "alpha_min": gxi["alpha_min"], "alpha_max": gxi["alpha_max"],
                         "alpha_unique_count": gxi["alpha_unique_count"],
                         "rgba_interpretation": "UI1 visually corroborated; not GS upload parity",
                         "evidence_grade": "CONFIRMED_BY_BYTES"})
    ps2_scene, provenance = payload("\\TNG\\DATASCENE\\HUD\\HUD0.XML")
    pause_bank, pause_provenance = payload("\\TNG\\DATAPSM\\FRONTEND\\NEW\\TILES\\TEXTBOXALPHA.PSB")
    pause_parsed = parse_psb(pause_bank)
    pause_gxi, pause_texture_provenance = payload("\\TNG\\DATAPSM\\FRONTEND\\NEW\\TILES\\TEXTBOXALPHA_000.GXI")
    pause_texture = parse_gxi(pause_gxi)
    pc_scene = args.pc_retail / "DataScene/Hud/Hud0.xml"
    pc_bank = args.pc_retail / "DataGx/Hud/hud-template.dxb"
    sys.path.insert(0, str(args.course_sdk / "src"))
    from master_rallye.dxt import parse_dxt
    pc_textures = []
    for name in ["hud-template_000_000.dxt", "hud-template_002_000.dxt",
                 "hud-damage_001_000.dxt", "newhud_028_000.dxt"]:
        path = args.pc_retail / "DataGx/Hud" / name
        texture = parse_dxt(path)
        alpha = texture.bgra[3::4]
        pc_textures.append(dict(input_fact(path), width=texture.width, height=texture.height,
            stored_channels="BGRA", alpha_min=min(alpha), alpha_max=max(alpha),
            alpha_unique_count=len(set(alpha)), row_orientation="not validated as runtime sampling",
            evidence_grade="CONFIRMED_BY_BYTES"))
    try:
        parse_psb(pc_bank.read_bytes())
        pc_bank_result = "unexpectedly_accepted"
    except ValueError as error:
        pc_bank_result = f"{type(error).__name__}: {error}"
    import rabbitizer
    data = (args.ps2 / "SLES_509.06").read_bytes()
    phoff = struct.unpack_from("<I", data, 28)[0]
    phsize, phcount = struct.unpack_from("<HH", data, 42)
    segments = [struct.unpack_from("<8I", data, phoff + i * phsize) for i in range(phcount)]

    def word(va):
        matches = [s for s in segments if s[0] == 1 and s[2] <= va and va + 4 <= s[2] + s[4]]
        if len(matches) != 1:
            raise ValueError("ambiguous ELF VA mapping")
        s = matches[0]
        return struct.unpack_from("<I", data, s[1] + va - s[2])[0]

    probes = []
    for va, target in [(0x00330334, 0x00337a98), (0x003303f4, 0x00337a98),
                       (0x00342ba0, 0x003cb2d0), (0x003cbb80, 0x003cb2d0),
                       (0x00319308, 0x00318bd8), (0x0031a4ac, 0x00318bd8)]:
        value = word(va)
        decoded_target = ((va + 4) & 0xf0000000) | ((value & 0x03ffffff) << 2)
        if value >> 26 != 3 or decoded_target != target:
            raise ValueError(f"UI2 direct JAL oracle differs at {va:x}")
        instruction = rabbitizer.Instruction(value, va, rabbitizer.InstrCategory.R5900)
        if not instruction.isValid():
            raise ValueError("invalid R5900 instruction")
        probes.append({"va": f"0x{va:08x}", "word": f"0x{value:08x}",
                       "target": f"0x{target:08x}", "r5900": instruction.disassemble()})
    # A bounded architecture check; its presence does not close sprite/video composition.
    for va in range(0x003cb2d0, 0x003cb30c, 4):
        value = word(va)
        instruction = rabbitizer.Instruction(value, va, rabbitizer.InstrCategory.R5900)
        if not instruction.isValid():
            raise ValueError(f"invalid matrix probe at {va:x}")
        probes.append({"va": f"0x{va:08x}", "word": f"0x{value:08x}",
                       "r5900": instruction.disassemble()})
    result = {"schema_version": 1, "phase": "HUD-PORT0", "implementation": "NOT_PERFORMED",
              "canonical_inputs": canonical,
              "renderer_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip(),
              "renderer_tree": subprocess.check_output(["git", "rev-parse", "HEAD:modernization/renderer"], cwd=REPOSITORY, text=True).strip(),
              "ps2_banks": banks, "selected_ps2_textures": textures,
              "ps2_hud0": {"path": provenance["path"], "sha256": sha(ps2_scene), "size": len(ps2_scene),
                           "elements": scene_facts(ps2_scene)},
              "ps2_pause_panel": {"path": pause_provenance["path"], "sha256": sha(pause_bank),
                  "images": len(pause_parsed["images"]), "texture": {"path": pause_texture_provenance["path"],
                  "sha256": sha(pause_gxi), "width": pause_texture["width"], "height": pause_texture["height"],
                  "alpha_min": pause_texture["alpha_min"], "alpha_max": pause_texture["alpha_max"]},
                  "runtime_selection": "UNKNOWN", "evidence_grade": "CONFIRMED_BY_BYTES"},
              "pc_hud0": dict(input_fact(pc_scene), elements=scene_facts(pc_scene.read_bytes())),
              "pc_dxb": dict(input_fact(pc_bank), ps2_parser_admission=pc_bank_result,
                             header_u32=list(struct.unpack_from("<3I", pc_bank.read_bytes()))),
              "selected_pc_textures": pc_textures,
              "readonly_course_sdk": {"path": str(args.course_sdk), "head":
                  subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.course_sdk, text=True).strip()},
              "rabbitizer_version": importlib.metadata.version("rabbitizer"),
              "r5900_probes": probes,
              "r5900_scope": "original direct-call edges and bounded matrix words; no full sprite owner/math revalidation",
              "frames": [frame_fact(args.logs / name) for name in ["frame-10916-d1-00002579.jsonl",
                                                                    "frame-42216-d1-00026331.jsonl"]]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"banks": len(banks), "textures": len(textures), "r5900_words": len(probes),
                      "frames": len(result["frames"]), "output_sha256": sha(args.output.read_bytes())}))


if __name__ == "__main__":
    main()
