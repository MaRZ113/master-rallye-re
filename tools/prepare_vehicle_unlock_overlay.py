#!/usr/bin/env python3
"""Build the exact retail Vehicle Select T1_Car8 locked-state overlay.

The source T1_Car4 / physical ID3 widget is cloned so its native disabler and
button-unlocker controls remain present. Only the ID26 normal frame and the
new slot's X position are changed. Source XML and retail assets are read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


SOURCE_SCENE_SHA256 = "ec7fd6372fe5008b1039eb8e09890ef3b37396dad1581568af439cbb611b58e1"
SOURCE_SCENE_REPO_PATH = "corpora/retail/Data.sma_unpacked/DataScene/FrontendScreens/VehicleSelect.xml"
TEMPLATE_WIDGET = "T1_Car4"
TARGET_WIDGET = "T1_Car8"
EXPECTED_UNLOCK_PATH = "Progress/UnlockedCars/T1CupCar1"
EXPECTED_CHEAT_PATHS = (
    "Progress/Cheats/UnlockCars",
    "Progress/Cheats/UnlockAll",
)
NORMAL_FRAME = 3
LOCKED_FRAME = 15
TARGET_X_ID = 7
TARGET_XPOS_PATH = "Frontend/VehicleSelect/Button7XPos"


class OverlayError(ValueError):
    """Raised when the source scene or locked-slot template is not exact."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_research_output(path: Path) -> bool:
    return any(part.casefold() in {"research-output", ".research-output"} for part in path.parts)


def _parse_xml(text: str) -> ET.Element:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise OverlayError(f"invalid Vehicle Select XML: {exc}") from exc
    if root.tag != "Scene":
        raise OverlayError(f"expected Scene root, got {root.tag!r}")
    return root


def _cars_list(root: ET.Element) -> ET.Element:
    matches = [node for node in root.findall("./EggLists_Version4/List")
               if node.get("Name") == "cars"]
    if len(matches) != 1:
        raise OverlayError("expected exactly one direct Vehicle Select cars list")
    return matches[0]


def _egg_span(text: str, name: str) -> tuple[int, int]:
    pattern = re.compile(r'<Egg\b(?=[^>]*\bName\s*=\s*["\']' + re.escape(name) + r'["\'])[^>]*>')
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise OverlayError(f"expected exactly one raw XML Egg named {name!r}")
    opening = matches[0]
    token_pattern = re.compile(r"<(\/?)Egg\b[^>]*>")
    depth = 0
    closing_end: int | None = None
    for token in token_pattern.finditer(text, opening.start()):
        depth += -1 if token.group(1) else 1
        if depth == 0:
            closing_end = token.end()
            break
    if closing_end is None:
        raise OverlayError(f"unterminated Egg block {name!r}")
    line_start = max(text.rfind("\n", 0, opening.start()), text.rfind("\r", 0, opening.start())) + 1
    return line_start, closing_end


def _direct_value(parent: ET.Element, name: str) -> ET.Element:
    matches = [value for value in parent.findall("./Value") if value.get("Name") == name]
    if len(matches) != 1:
        raise OverlayError(f"expected one {name!r} value")
    return matches[0]


def _ai_node(egg: ET.Element, ai_no: str, expected_name: str) -> tuple[ET.Element, ET.Element]:
    matches = [node for node in egg.findall("./AI_List/AI") if node.get("No") == ai_no]
    if len(matches) != 1:
        raise OverlayError(f"{egg.get('Name')} must have one AI No={ai_no}")
    node = matches[0]
    names = [value.get("Value") for value in node.findall("./Value")
             if value.get("Name") == "AI Name"]
    if names != [expected_name]:
        raise OverlayError(f"{egg.get('Name')} AI {ai_no} must be {expected_name}")
    body = node.find("./" + expected_name)
    if body is None:
        raise OverlayError(f"{expected_name} parameter block is missing")
    return node, body


def _body_values(body: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for value in body.findall("./Value"):
        name = value.get("Name")
        if not isinstance(name, str) or name in values:
            raise OverlayError("AI parameter block has a missing or duplicate value name")
        values[name] = value.get("Value", "")
    return values


def _validate_stock_locked_template(text: str) -> None:
    root = _parse_xml(text)
    group = _cars_list(root)
    widgets = [node.get("Name") for node in group.findall("./Egg")
               if re.fullmatch(r"T1_Car[1-9][0-9]*", node.get("Name", ""))]
    if widgets != [f"T1_Car{i}" for i in range(1, 8)]:
        raise OverlayError("retail T1 widget list must contain exactly T1_Car1 through T1_Car7")
    template_matches = [node for node in group.findall("./Egg") if node.get("Name") == TEMPLATE_WIDGET]
    if len(template_matches) != 1:
        raise OverlayError("locked-capable stock T1_Car4 template is missing or ambiguous")
    template = template_matches[0]

    disabler_node, disabler = _ai_node(template, "0", "gaFrontendDisablerAI")
    disabler_values = _body_values(disabler)
    if (disabler_values.get("Broker Value1*") != EXPECTED_UNLOCK_PATH
            or disabler_values.get("Broker Value2*") != EXPECTED_CHEAT_PATHS[0]
            or disabler_values.get("Broker Value3*") != EXPECTED_CHEAT_PATHS[1]
            or disabler_values.get("True Value") != "27"
            or disabler_values.get("False Value") != str(LOCKED_FRAME)):
        raise OverlayError("stock ID3 disabler does not match the audited T1CupCar1 / frame-15 gate")
    _ = disabler_node

    _button_node, button = _ai_node(template, "2", "gaFrontendXYButtonAI")
    button_values = _body_values(button)
    if (button_values.get("Button ID") != "1" or button_values.get("X ID") != "3"
            or button_values.get("Y ID") != "0"
            or button_values.get("XPos*") != "Frontend/VehicleSelect/Button3XPos"
            or button_values.get("Enabled") != "True"):
        raise OverlayError("stock ID3 XY button does not match the audited slot control")

    _unlock_node, unlocker = _ai_node(template, "3", "gaFrontendButtonUnlockerAI")
    unlock_values = _body_values(unlocker)
    if (unlock_values.get("Unlock 1*") != EXPECTED_UNLOCK_PATH
            or unlock_values.get("1 OR 2") != "True"
            or unlock_values.get("Unlock 2*") != EXPECTED_CHEAT_PATHS[0]
            or unlock_values.get("Control AI ID") != "2"
            or unlock_values.get("1?2 OR 3") != "True"
            or unlock_values.get("Unlock 3*") != EXPECTED_CHEAT_PATHS[1]):
        raise OverlayError("stock ID3 unlocker is not the audited native OR gate for XY AI 2")


def _replace_value(snippet: str, name: str, replacement: str) -> str:
    pattern = re.compile(r'(<Value\s+Name="' + re.escape(name)
                         + r'"[^>]*\bValue=")[^"]*(")')
    result, count = pattern.subn(lambda match: match.group(1) + replacement + match.group(2), snippet)
    if count != 1:
        raise OverlayError(f"expected one raw {name!r} value while cloning {TEMPLATE_WIDGET}, found {count}")
    return result


def _validate_generated_slot(text: str) -> None:
    root = _parse_xml(text)
    group = _cars_list(root)
    widgets = [node for node in group.findall("./Egg") if node.get("Name", "").startswith("T1_Car")]
    names = [node.get("Name") for node in widgets]
    if names.count(TARGET_WIDGET) != 1 or names.index(TARGET_WIDGET) != names.index("T1_Car7") + 1:
        raise OverlayError("generated T1_Car8 is missing, duplicated, or not appended after T1_Car7")
    slot = next(node for node in widgets if node.get("Name") == TARGET_WIDGET)
    if _direct_value(slot, "en2d Image Bank Index").get("Value") != str(NORMAL_FRAME):
        raise OverlayError("ID26 slot default art must be the audited Mercedes frame 3")
    _node, disabler = _ai_node(slot, "0", "gaFrontendDisablerAI")
    disabler_values = _body_values(disabler)
    if (disabler_values.get("Broker Value1*") != EXPECTED_UNLOCK_PATH
            or disabler_values.get("Broker Value2*") != EXPECTED_CHEAT_PATHS[0]
            or disabler_values.get("Broker Value3*") != EXPECTED_CHEAT_PATHS[1]
            or disabler_values.get("True Value") != str(NORMAL_FRAME)
            or disabler_values.get("False Value") != str(LOCKED_FRAME)):
        raise OverlayError("generated ID26 slot does not switch between frame 3 and stock locked frame 15")
    _node, button = _ai_node(slot, "2", "gaFrontendXYButtonAI")
    button_values = _body_values(button)
    if (button_values.get("Button ID") != "1" or button_values.get("X ID") != str(TARGET_X_ID)
            or button_values.get("Y ID") != "0"
            or button_values.get("XPos*") != TARGET_XPOS_PATH):
        raise OverlayError("generated ID26 XY button does not target T1 local7 / Button7XPos")
    _node, unlocker = _ai_node(slot, "3", "gaFrontendButtonUnlockerAI")
    unlock_values = _body_values(unlocker)
    if (unlock_values.get("Unlock 1*") != EXPECTED_UNLOCK_PATH
            or unlock_values.get("Unlock 2*") != EXPECTED_CHEAT_PATHS[0]
            or unlock_values.get("Unlock 3*") != EXPECTED_CHEAT_PATHS[1]
            or unlock_values.get("Control AI ID") != "2"
            or unlock_values.get("1 OR 2") != "True"
            or unlock_values.get("1?2 OR 3") != "True"):
        raise OverlayError("generated ID26 XY button lost the stock ID3 unlock/disable gate")


def build_overlay_bytes(source_bytes: bytes, *, expected_source_sha256: str = SOURCE_SCENE_SHA256
                        ) -> tuple[bytes, dict[str, Any]]:
    actual_sha = sha256_bytes(source_bytes)
    if actual_sha != expected_source_sha256.lower():
        raise OverlayError(f"unsupported Vehicle Select source SHA256: {actual_sha}")
    bom = source_bytes.startswith(b"\xef\xbb\xbf")
    try:
        source_text = source_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise OverlayError("Vehicle Select source is not UTF-8") from exc
    _validate_stock_locked_template(source_text)
    root = _parse_xml(source_text)
    group = _cars_list(root)
    if any(node.get("Name") == TARGET_WIDGET for node in root.iter("Egg")):
        raise OverlayError("T1_Car8 already exists in source; refusing a duplicate slot")

    template_start, template_end = _egg_span(source_text, TEMPLATE_WIDGET)
    clone = source_text[template_start:template_end]
    if clone.count(f'<Egg Name="{TEMPLATE_WIDGET}">') != 1:
        raise OverlayError("stock T1_Car4 raw opening tag changed")
    clone = clone.replace(f'<Egg Name="{TEMPLATE_WIDGET}">', f'<Egg Name="{TARGET_WIDGET}">', 1)
    clone = _replace_value(clone, "en2d Image Bank Index", str(NORMAL_FRAME))
    clone = _replace_value(clone, "True Value", str(NORMAL_FRAME))
    clone = _replace_value(clone, "X ID", str(TARGET_X_ID))
    clone = _replace_value(clone, "XPos*", TARGET_XPOS_PATH)

    last_start, last_end = _egg_span(source_text, "T1_Car7")
    _ = last_start
    newline = "\r\n" if "\r\n" in source_text else "\n"
    if source_text[last_end:last_end + len(newline)] != newline:
        raise OverlayError("could not identify the retail line ending after T1_Car7")
    inserted = clone + newline
    insert_at = last_end + len(newline)
    output_text = source_text[:insert_at] + inserted + source_text[insert_at:]
    _validate_generated_slot(output_text)
    restored = output_text[:insert_at] + output_text[insert_at + len(inserted):]
    if restored != source_text:
        raise OverlayError("internal audit failed: source XML changed outside the appended T1_Car8 block")

    output_bytes = (b"\xef\xbb\xbf" if bom else b"") + output_text.encode("utf-8")
    manifest = {
        "schema_version": 1,
        "phase": "R5V-G.1 locked-state integration correction",
        "status": "READY_FOR_HUMAN_RUNTIME",
        "source_sha256": actual_sha,
        "output_sha256": sha256_bytes(output_bytes),
        "change": {
            "widget": TARGET_WIDGET,
            "physical_vehicle_id": 26,
            "class": "T1",
            "class_local_index": 7,
            "raw_template": TEMPLATE_WIDGET,
            "default_image_frame": NORMAL_FRAME,
            "unlocked_image_frame": NORMAL_FRAME,
            "locked_image_frame": LOCKED_FRAME,
            "unlock_paths": [EXPECTED_UNLOCK_PATH, *EXPECTED_CHEAT_PATHS],
            "unlock_operator": "(T1CupCar1 OR UnlockCars) OR UnlockAll",
            "xy_button": {"button_id": 1, "x_id": TARGET_X_ID, "y_id": 0,
                           "xpos_path": TARGET_XPOS_PATH},
            "unlocker_controls_ai_id": 2,
            "asset_changes": [],
        },
        "audit": {
            "exact_source_sha_required": True,
            "source_mutated": False,
            "only_appended_slot_changed": True,
            "stock_disabler_retained": True,
            "stock_button_unlocker_retained": True,
            "physical_vehicle_id_rewritten": False,
        },
        "evidence_limit": (
            "The XML carries the same stock gate and locked-frame behavior as ID3; "
            "human UI interaction is still required to confirm visible art and blocked commit."
        ),
    }
    return output_bytes, manifest


def _repo_relative(path: Path) -> str:
    root = Path(__file__).resolve().parents[1]
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError as exc:
        raise OverlayError("generated output must remain inside this checkout") from exc


def generate_overlay(source: Path, output: Path, manifest_path: Path, *, verify_existing: bool = False
                     ) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    manifest_path = manifest_path.resolve(strict=False)
    if source == output or output == manifest_path:
        raise OverlayError("source, overlay, and manifest paths must be distinct")
    if not _is_research_output(output):
        raise OverlayError("overlay output must be inside research-output")
    if not _is_research_output(manifest_path):
        raise OverlayError("manifest output must be inside research-output")

    source_bytes = source.read_bytes()
    output_bytes, base_manifest = build_overlay_bytes(source_bytes)
    manifest = {
        **base_manifest,
        "source_path": SOURCE_SCENE_REPO_PATH,
        "output_path": _repo_relative(output),
        "manifest_path": _repo_relative(manifest_path),
    }
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    already_present = output.is_file() and manifest_path.is_file()
    if verify_existing:
        if not output.is_file() or output.read_bytes() != output_bytes:
            raise OverlayError("existing overlay differs from deterministic clean-source rebuild")
        if not manifest_path.is_file() or manifest_path.read_bytes() != manifest_bytes:
            raise OverlayError("existing overlay manifest differs from deterministic rebuild")
        status = "VERIFIED_EXISTING"
    else:
        for path, contents in ((output, output_bytes), (manifest_path, manifest_bytes)):
            if path.exists():
                if not path.is_file() or path.read_bytes() != contents:
                    raise OverlayError(f"refusing to overwrite different generated output: {path}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)
        status = "ALREADY_PRESENT" if already_present else "GENERATED"
    return {"status": status, "source_sha256": base_manifest["source_sha256"],
            "output_sha256": base_manifest["output_sha256"],
            "source_path": manifest["source_path"], "output_path": manifest["output_path"],
            "manifest_path": manifest["manifest_path"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=Path(__file__).resolve().parents[2] / SOURCE_SCENE_REPO_PATH)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = generate_overlay(args.source, args.output, args.manifest,
                                  verify_existing=args.verify_existing)
    except (OSError, UnicodeError, json.JSONDecodeError, OverlayError) as exc:
        parser.exit(2, f"Vehicle Select unlock overlay refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
