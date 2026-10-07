#!/usr/bin/env python3
"""Append the bounded R5V-I.0 T2_Car8 slot to the qualified G.1 overlay.

The retail scene and qualified G.1 generator are hash-pinned inputs. This
builder clones the stock locked T2_Car4 control, changes only the appended
slot's frame and position, and leaves all previous Vehicle Select XML bytes
untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

try:
    import prepare_vehicle_unlock_overlay as g1
except ImportError:  # pragma: no cover - package-style imports for tests
    from tools import prepare_vehicle_unlock_overlay as g1


SOURCE_SCENE_REPO_PATH = "corpora/retail/Data.sma_unpacked/DataScene/FrontendScreens/VehicleSelect.xml"
SOURCE_SCENE_SHA256 = g1.SOURCE_SCENE_SHA256
G1_OVERLAY_SHA256 = "6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d"
TEMPLATE_WIDGET = "T2_Car4"
LAST_STOCK_WIDGET = "T2_Car7"
TARGET_WIDGET = "T2_Car8"
UNLOCK_PATH = "Progress/UnlockedCars/T2CupCar1"
CHEAT_PATHS = ("Progress/Cheats/UnlockCars", "Progress/Cheats/UnlockAll")
DONOR_FRAME = 23  # audited stock T2/Navara Vehicle Select carsheet frame
LOCKED_FRAME = 15
TARGET_X_ID = 7
TARGET_Y_ID = 1
TARGET_XPOS_PATH = "Frontend/VehicleSelect/Button7XPos"


class OverlayError(ValueError):
    """Raised when a source scene or generated slot differs from the audit."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_t2_template(text: str) -> None:
    root = g1._parse_xml(text)
    group = g1._cars_list(root)
    widgets = [node.get("Name") for node in group.findall("./Egg")
               if node.get("Name", "").startswith("T2_Car")]
    expected_names = [f"T2_Car{i}" for i in range(1, 8)]
    if widgets != expected_names:
        raise OverlayError("retail T2 widget list must contain exactly T2_Car1 through T2_Car7")
    template_matches = [node for node in group.findall("./Egg")
                        if node.get("Name") == TEMPLATE_WIDGET]
    if len(template_matches) != 1:
        raise OverlayError("stock locked T2_Car4 template is missing or ambiguous")
    template = template_matches[0]

    _node, disabler = g1._ai_node(template, "0", "gaFrontendDisablerAI")
    disabler_values = g1._body_values(disabler)
    if (disabler_values.get("Broker Value1*") != UNLOCK_PATH
            or disabler_values.get("Broker Value2*") != CHEAT_PATHS[0]
            or disabler_values.get("Broker Value3*") != CHEAT_PATHS[1]
            or disabler_values.get("True Value") != "12"
            or disabler_values.get("False Value") != str(LOCKED_FRAME)):
        raise OverlayError("stock T2_Car4 is not the audited T2CupCar1 / locked-frame gate")

    _node, button = g1._ai_node(template, "2", "gaFrontendXYButtonAI")
    button_values = g1._body_values(button)
    if (button_values.get("Button ID") != "1" or button_values.get("X ID") != "3"
            or button_values.get("Y ID") != str(TARGET_Y_ID)
            or button_values.get("XPos*") != "Frontend/VehicleSelect/Button3XPos"
            or button_values.get("Enabled") != "True"):
        raise OverlayError("stock T2_Car4 XY button differs from the audited slot control")

    _node, unlocker = g1._ai_node(template, "3", "gaFrontendButtonUnlockerAI")
    unlock_values = g1._body_values(unlocker)
    if (unlock_values.get("Unlock 1*") != UNLOCK_PATH
            or unlock_values.get("1 OR 2") != "True"
            or unlock_values.get("Unlock 2*") != CHEAT_PATHS[0]
            or unlock_values.get("Control AI ID") != "2"
            or unlock_values.get("1?2 OR 3") != "True"
            or unlock_values.get("Unlock 3*") != CHEAT_PATHS[1]):
        raise OverlayError("stock T2_Car4 unlocker is not the audited native OR gate")


def _validate_generated_slot(text: str) -> None:
    root = g1._parse_xml(text)
    group = g1._cars_list(root)
    widgets = [node for node in group.findall("./Egg")
               if node.get("Name", "").startswith("T2_Car")]
    names = [node.get("Name") for node in widgets]
    if (names != [*(f"T2_Car{i}" for i in range(1, 8)), TARGET_WIDGET]
            or names.count(TARGET_WIDGET) != 1):
        raise OverlayError("generated T2_Car8 is missing, duplicated, or not appended after T2_Car7")
    slot = widgets[-1]
    if g1._direct_value(slot, "en2d Image Bank Index").get("Value") != str(DONOR_FRAME):
        raise OverlayError("ID27 diagnostic art must use the audited stock Navara frame 23")

    _node, disabler = g1._ai_node(slot, "0", "gaFrontendDisablerAI")
    disabler_values = g1._body_values(disabler)
    if (disabler_values.get("Broker Value1*") != UNLOCK_PATH
            or disabler_values.get("Broker Value2*") != CHEAT_PATHS[0]
            or disabler_values.get("Broker Value3*") != CHEAT_PATHS[1]
            or disabler_values.get("True Value") != str(DONOR_FRAME)
            or disabler_values.get("False Value") != str(LOCKED_FRAME)):
        raise OverlayError("generated ID27 slot lost its T2CupCar1 locked-frame control")

    _node, button = g1._ai_node(slot, "2", "gaFrontendXYButtonAI")
    button_values = g1._body_values(button)
    if (button_values.get("Button ID") != "1"
            or button_values.get("X ID") != str(TARGET_X_ID)
            or button_values.get("Y ID") != str(TARGET_Y_ID)
            or button_values.get("XPos*") != TARGET_XPOS_PATH
            or button_values.get("Enabled") != "True"):
        raise OverlayError("generated ID27 XY button does not target T2 local7 / Button7XPos")

    _node, unlocker = g1._ai_node(slot, "3", "gaFrontendButtonUnlockerAI")
    unlock_values = g1._body_values(unlocker)
    if (unlock_values.get("Unlock 1*") != UNLOCK_PATH
            or unlock_values.get("Unlock 2*") != CHEAT_PATHS[0]
            or unlock_values.get("Unlock 3*") != CHEAT_PATHS[1]
            or unlock_values.get("Control AI ID") != "2"
            or unlock_values.get("1 OR 2") != "True"
            or unlock_values.get("1?2 OR 3") != "True"):
        raise OverlayError("generated ID27 slot does not preserve the stock T2 unlock/disable gate")


def build_overlay_bytes(source_bytes: bytes, *,
                        expected_source_sha256: str = SOURCE_SCENE_SHA256
                        ) -> tuple[bytes, dict[str, Any]]:
    actual_source_sha = sha256_bytes(source_bytes)
    if actual_source_sha != expected_source_sha256.lower():
        raise OverlayError(f"unsupported Vehicle Select source SHA256: {actual_source_sha}")
    try:
        source_text = source_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise OverlayError("Vehicle Select source is not UTF-8") from exc

    _validate_t2_template(source_text)
    root = g1._parse_xml(source_text)
    if any(node.get("Name") == TARGET_WIDGET for node in root.iter("Egg")):
        raise OverlayError("T2_Car8 already exists in source; refusing a duplicate slot")

    g1_overlay_bytes, g1_manifest = g1.build_overlay_bytes(
        source_bytes, expected_source_sha256=expected_source_sha256)
    if expected_source_sha256.lower() == SOURCE_SCENE_SHA256:
        if g1_manifest["output_sha256"] != G1_OVERLAY_SHA256:
            raise OverlayError("qualified G.1 overlay hash differs from its pinned output")
    bom = g1_overlay_bytes.startswith(b"\xef\xbb\xbf")
    try:
        base_text = g1_overlay_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:  # pragma: no cover - builder validates source encoding
        raise OverlayError("G.1 overlay is not UTF-8") from exc

    base_root = g1._parse_xml(base_text)
    group = g1._cars_list(base_root)
    if any(node.get("Name") == TARGET_WIDGET for node in base_root.iter("Egg")):
        raise OverlayError("T2_Car8 already exists in the G.1 base overlay")
    _validate_t2_template(base_text)

    template_start, template_end = g1._egg_span(base_text, TEMPLATE_WIDGET)
    clone = base_text[template_start:template_end]
    open_tag = f'<Egg Name="{TEMPLATE_WIDGET}">'
    if clone.count(open_tag) != 1:
        raise OverlayError("stock T2_Car4 raw opening tag changed")
    clone = clone.replace(open_tag, f'<Egg Name="{TARGET_WIDGET}">', 1)
    for key, value in (
        ("en2d Image Bank Index", str(DONOR_FRAME)),
        ("True Value", str(DONOR_FRAME)),
        ("X ID", str(TARGET_X_ID)),
        ("XPos*", TARGET_XPOS_PATH),
    ):
        clone = g1._replace_value(clone, key, value)

    last_start, last_end = g1._egg_span(base_text, LAST_STOCK_WIDGET)
    _ = last_start
    newline = "\r\n" if "\r\n" in base_text else "\n"
    if base_text[last_end:last_end + len(newline)] != newline:
        raise OverlayError("could not identify the line ending after T2_Car7")
    inserted = clone + newline
    insert_at = last_end + len(newline)
    output_text = base_text[:insert_at] + inserted + base_text[insert_at:]
    _validate_generated_slot(output_text)
    restored = output_text[:insert_at] + output_text[insert_at + len(inserted):]
    if restored != base_text:
        raise OverlayError("internal audit failed: G.1 overlay changed outside appended T2_Car8")

    output_bytes = (b"\xef\xbb\xbf" if bom else b"") + output_text.encode("utf-8")
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R5V-I.0 two-addon-slot / T2 local7 diagnostic overlay",
        "status": "READY_FOR_HUMAN_RUNTIME",
        "source_path": SOURCE_SCENE_REPO_PATH,
        "source_sha256": actual_source_sha,
        "g1_overlay_sha256": sha256_bytes(g1_overlay_bytes),
        "output_sha256": sha256_bytes(output_bytes),
        "change": {
            "widget": TARGET_WIDGET,
            "physical_vehicle_id": 27,
            "class": "T2",
            "class_local_index": 7,
            "raw_template": TEMPLATE_WIDGET,
            "donor_art": "stock physical ID7/Navara carsheet frame 23; diagnostic only",
            "default_image_frame": DONOR_FRAME,
            "unlocked_image_frame": DONOR_FRAME,
            "locked_image_frame": LOCKED_FRAME,
            "unlock_paths": [UNLOCK_PATH, *CHEAT_PATHS],
            "unlock_operator": "(T2CupCar1 OR UnlockCars) OR UnlockAll",
            "xy_button": {
                "button_id": 1, "x_id": TARGET_X_ID, "y_id": TARGET_Y_ID,
                "xpos_path": TARGET_XPOS_PATH,
            },
            "unlocker_controls_ai_id": 2,
            "physical_car_id_rewritten": False,
        },
        "audit": {
            "exact_retail_source_sha_required": True,
            "qualified_g1_overlay_preserved": True,
            "only_t2_car8_appended_after_g1_overlay": True,
            "stock_t2_disabler_retained": True,
            "stock_t2_button_unlocker_retained": True,
            "t2_class_reachability_changed": False,
            "physical_id27_is_real_independent_vehicle": False,
        },
        "evidence_limit": (
            "This is a slot-architecture overlay using donor Navara frontend art. "
            "Human UI and race checks are still required; it is not a real second-vehicle qualification."
        ),
    }
    return output_bytes, manifest


def generate_overlay(source: Path, output: Path, manifest_path: Path, *,
                     verify_existing: bool = False) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    manifest_path = manifest_path.resolve(strict=False)
    if source == output or output == manifest_path:
        raise OverlayError("source, overlay, and manifest paths must be distinct")
    if not g1._is_research_output(output) or not g1._is_research_output(manifest_path):
        raise OverlayError("overlay and manifest outputs must be inside research-output")
    output_bytes, base = build_overlay_bytes(source.read_bytes())
    root = Path(__file__).resolve().parents[1]
    try:
        output_name = output.relative_to(root).as_posix()
        manifest_name = manifest_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise OverlayError("generated output must remain inside this checkout") from exc
    manifest = {**base, "output_path": output_name, "manifest_path": manifest_name}
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if verify_existing:
        if not output.is_file() or output.read_bytes() != output_bytes:
            raise OverlayError("existing overlay differs from deterministic source rebuild")
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
        status = "GENERATED"
    return {
        "status": status,
        "source_sha256": base["source_sha256"],
        "g1_overlay_sha256": base["g1_overlay_sha256"],
        "output_sha256": base["output_sha256"],
        "output_path": output_name,
        "manifest_path": manifest_name,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=Path(__file__).resolve().parents[1] / SOURCE_SCENE_REPO_PATH)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = generate_overlay(args.source, args.output, args.manifest,
                                  verify_existing=args.verify_existing)
    except (OSError, UnicodeError, json.JSONDecodeError, OverlayError,
            g1.OverlayError) as exc:
        parser.exit(2, f"R5V-I.0 Vehicle Select overlay refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
