#!/usr/bin/env python3
"""Create a fail-closed, scene-only Vehicle Select icon overlay.

The tool appends the next class-local ``Tn_CarN`` scene object using a
same-class, non-unlock-gated template. It does not modify an executable,
Data.sma, source scene, or image asset. Output is restricted to a
``research-output`` tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


DXT_MAGIC = 0x0000FEED


class OverlayError(ValueError):
    """Raised when an overlay request is inconsistent or unsafe."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _scene_tree(scene_text: str) -> ET.Element:
    try:
        root = ET.fromstring(scene_text)
    except ET.ParseError as exc:
        raise OverlayError(f"invalid scene XML: {exc}") from exc
    if root.tag != "Scene":
        raise OverlayError(f"expected Scene root, got {root.tag!r}")
    return root


def _vehicle_select_list(root: ET.Element) -> ET.Element:
    lists = [
        node for node in root.findall("./EggLists_Version4/List")
        if node.get("Name") == "cars"
    ]
    if len(lists) != 1:
        raise OverlayError("expected exactly one cars list in EggLists_Version4")
    # Retail Tn_CarN icon widgets are direct children of this sibling list.
    return lists[0]


def _widget_name(class_name: str, local_index: int) -> str:
    return f"{class_name}_Car{local_index + 1}"


def _class_widgets(group: ET.Element, class_name: str) -> list[tuple[int, ET.Element]]:
    found: list[tuple[int, ET.Element]] = []
    pattern = re.compile(re.escape(class_name) + r"_Car([1-9][0-9]*)\Z")
    for child in group.findall("./Egg"):
        match = pattern.fullmatch(child.get("Name", ""))
        if match:
            found.append((int(match.group(1)), child))
    found.sort(key=lambda item: item[0])
    indices = [number for number, _ in found]
    if indices and indices != list(range(1, len(indices) + 1)):
        raise OverlayError(f"{class_name} widget numbering has gaps: {indices}")
    return found


def _value_node(node: ET.Element, name: str) -> ET.Element:
    values = [value for value in node.findall("./Value") if value.get("Name") == name]
    if len(values) != 1:
        raise OverlayError(
            f"{node.get('Name', 'scene node')} must have exactly one {name!r} value"
        )
    return values[0]


def _xy_button_ai(node: ET.Element) -> ET.Element:
    matches: list[ET.Element] = []
    for ai in node.findall("./AI_List/AI"):
        name_values = [
            value for value in ai.findall("./Value")
            if value.get("Name") == "AI Name" and value.get("Value") == "gaFrontendXYButtonAI"
        ]
        if name_values:
            body = ai.find("./gaFrontendXYButtonAI")
            if body is None:
                raise OverlayError("gaFrontendXYButtonAI has no parameter block")
            matches.append(body)
    if len(matches) != 1:
        raise OverlayError(f"{node.get('Name')} must have exactly one XY button AI")
    return matches[0]


def _egg_span(scene_text: str, name: str) -> tuple[int, int]:
    escaped = re.escape(name)
    open_tag = re.compile(r'<Egg\b(?=[^>]*\bName\s*=\s*["\']' + escaped + r'["\'])[^>]*>')
    matches = list(open_tag.finditer(scene_text))
    if len(matches) != 1:
        raise OverlayError(f"expected one raw XML Egg block named {name!r}")
    match = matches[0]
    token_re = re.compile(r"<(\/?)Egg\b[^>]*>")
    depth = 0
    close_end: int | None = None
    for token in token_re.finditer(scene_text, match.start()):
        if token.group(1):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            close_end = token.end()
            break
    if close_end is None:
        raise OverlayError(f"unterminated Egg block named {name!r}")
    line_start = max(scene_text.rfind("\n", 0, match.start()), scene_text.rfind("\r", 0, match.start())) + 1
    return line_start, close_end


def _replace_value(snippet: str, name: str, value: str) -> str:
    escaped = re.escape(name)
    pattern = re.compile(
        r'(<Value\s+Name="' + escaped + r'"[^>]*\bValue=")[^"]*(")'
    )
    result, count = pattern.subn(lambda match: match.group(1) + value + match.group(2), snippet)
    if count != 1:
        raise OverlayError(f"expected one raw XML value for {name!r}, found {count}")
    return result


def _validate_dxt(path: Path) -> str:
    if not path.is_file():
        raise OverlayError(f"indexed icon frame does not exist: {path}")
    data = path.read_bytes()
    if len(data) < 20:
        raise OverlayError(f"indexed icon frame is shorter than its DXT header: {path}")
    magic, _word4, _word8, width, height = struct.unpack_from("<5I", data)
    if magic != DXT_MAGIC or width <= 0 or height <= 0:
        raise OverlayError(f"invalid DXT image header: {path}")
    if len(data) != 20 + width * height * 4:
        raise OverlayError(f"DXT payload size disagrees with {width}x{height}: {path}")
    return sha256_bytes(data)


def _replace_scene_value(snippet: str, name: str, value: str) -> str:
    return _replace_value(snippet, name, value)


def generate_overlay(
    source_scene: Path,
    output_scene: Path,
    asset_root: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Generate validated XML using a JSON icon-slot manifest."""
    source_scene = source_scene.resolve()
    output_scene = output_scene.resolve()
    asset_root = asset_root.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 2:
        raise OverlayError("unsupported icon manifest schema_version")
    if not source_scene.is_file():
        raise OverlayError(f"source scene not found: {source_scene}")
    if source_scene == output_scene:
        raise OverlayError("output must not overwrite the source scene")
    if "research-output" not in {part.lower() for part in output_scene.parts}:
        raise OverlayError("output scene must be inside a research-output directory")

    source_bytes = source_scene.read_bytes()
    actual_source_sha = sha256_bytes(source_bytes)
    expected_source_sha = str(manifest.get("source_scene_sha256", "")).upper()
    if actual_source_sha != expected_source_sha:
        raise OverlayError(
            f"source scene SHA-256 mismatch: expected {expected_source_sha}, got {actual_source_sha}"
        )
    bom = source_bytes.startswith(b"\xef\xbb\xbf")
    try:
        source_text = source_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise OverlayError("source scene is not UTF-8") from exc
    root = _scene_tree(source_text)
    group = _vehicle_select_list(root)

    bank = manifest.get("image_bank", {})
    bank_name = str(bank.get("scene_name", ""))
    container_name = str(bank.get("container", ""))
    frame_pattern = str(bank.get("frame_pattern", ""))
    frame_count = bank.get("frame_count")
    file_type = str(bank.get("file_type", ""))
    if not bank_name or not container_name or "{index" not in frame_pattern:
        raise OverlayError("manifest image_bank must define scene_name, container, and frame_pattern")
    if not isinstance(frame_count, int) or frame_count <= 0:
        raise OverlayError("manifest image_bank.frame_count must be a positive integer")
    if not (asset_root / container_name).is_file():
        raise OverlayError(f"image-bank container does not exist: {asset_root / container_name}")

    class_mappings = manifest.get("class_mappings")
    if not isinstance(class_mappings, dict) or not class_mappings:
        raise OverlayError("manifest class_mappings must be a non-empty object")
    positions = manifest.get("layout_position_properties")
    if not isinstance(positions, list) or not positions or not all(
        isinstance(value, str) and value for value in positions
    ):
        raise OverlayError("manifest layout_position_properties must list supported position keys")
    slots = manifest.get("slots")
    if not isinstance(slots, list) or not slots:
        raise OverlayError("manifest slots must be a non-empty array")

    text = source_text
    inserted_chunks: list[str] = []
    additions: list[dict[str, Any]] = []
    seen_vehicle_ids: set[int] = set()
    for slot in slots:
        if not isinstance(slot, dict):
            raise OverlayError("each slot manifest entry must be an object")
        class_name = slot.get("class")
        if not isinstance(class_name, str):
            raise OverlayError(f"unsupported vehicle class: {class_name!r}")
        mapping = class_mappings.get(class_name)
        if not isinstance(mapping, dict):
            raise OverlayError(f"unsupported vehicle class: {class_name!r}")
        base_id = mapping.get("vehicle_id_base")
        row_id = mapping.get("row_id")
        if not isinstance(base_id, int) or base_id < 0 or not isinstance(row_id, int) or row_id < 0:
            raise OverlayError(f"{class_name} mapping needs non-negative vehicle_id_base and row_id")
        local_index = slot.get("local_index")
        vehicle_id = slot.get("vehicle_id")
        frame_index = slot.get("frame_index")
        template_name = str(slot.get("template_widget", ""))
        if not isinstance(local_index, int) or local_index < 0:
            raise OverlayError("local_index must be a non-negative integer")
        if local_index >= len(positions):
            raise OverlayError(
                f"local index {local_index} has no verified layout position in this profile; add a position key only after proving the runtime supports it"
            )
        if not isinstance(vehicle_id, int) or vehicle_id != base_id + local_index:
            raise OverlayError("vehicle_id does not match the supported class-base/local-index mapping")
        if vehicle_id in seen_vehicle_ids:
            raise OverlayError(f"multiple slots map to vehicle ID {vehicle_id}")
        seen_vehicle_ids.add(vehicle_id)
        if not isinstance(frame_index, int) or not 0 <= frame_index < frame_count:
            raise OverlayError(f"frame_index must be in 0..{frame_count - 1}")
        if not template_name.startswith(class_name + "_Car"):
            raise OverlayError("template_widget must belong to the same vehicle class")

        current_root = _scene_tree(text)
        current_group = _vehicle_select_list(current_root)
        all_named = [node for node in current_root.iter("Egg") if node.get("Name")]
        target_name = _widget_name(class_name, local_index)
        if any(node.get("Name") == target_name for node in all_named):
            raise OverlayError(f"target scene object already exists: {target_name}")
        siblings = _class_widgets(current_group, class_name)
        if not siblings or local_index != len(siblings):
            raise OverlayError(
                f"slot must append the next {class_name} widget: expected local index {len(siblings)}, got {local_index}"
            )
        by_name = {node.get("Name"): node for _, node in siblings}
        template = by_name.get(template_name)
        if template is None:
            raise OverlayError(f"template widget not found in scene: {template_name}")
        en2d_model = _value_node(template, "en2d Model Name").get("Value", "")
        en2d_file_type = _value_node(template, "en2d FileType").get("Value", "")
        if en2d_model.casefold() != bank_name.casefold() or en2d_file_type != file_type:
            raise OverlayError("template image bank/file type disagrees with manifest")
        _value_node(template, "en2d Image Bank Index")
        xy_ai = _xy_button_ai(template)
        button_id = _value_node(xy_ai, "Button ID").get("Value")
        y_id = _value_node(xy_ai, "Y ID").get("Value")
        if button_id != "1" or y_id != str(row_id):
            raise OverlayError("template does not match the proven vehicle-button/class-row pattern")
        ai_names = [
            value.get("Value", "")
            for ai in template.findall("./AI_List/AI")
            for value in ai.findall("./Value")
            if value.get("Name") == "AI Name"
        ]
        unsupported = {"gaFrontendDisablerAI", "gaFrontendButtonUnlockerAI"}.intersection(ai_names)
        if unsupported:
            raise OverlayError(
                "template contains lock/unlock behavior; this tool requires a separately proven per-slot unlock policy"
            )

        dxt_name = frame_pattern.format(index=frame_index)
        dxt_path = (asset_root / dxt_name).resolve()
        if not dxt_path.is_relative_to(asset_root):
            raise OverlayError("frame_pattern resolves outside the asset root")
        frame_sha256 = _validate_dxt(dxt_path)

        template_start, template_end = _egg_span(text, template_name)
        clone = text[template_start:template_end]
        original_open = f'<Egg Name="{template_name}">'
        if clone.count(original_open) != 1:
            raise OverlayError("template raw XML opening tag changed or is ambiguous")
        clone = clone.replace(original_open, f'<Egg Name="{target_name}">', 1)
        clone = _replace_scene_value(clone, "en2d Image Bank Index", str(frame_index))
        clone = _replace_scene_value(clone, "X ID", str(local_index))
        position_property = positions[local_index]
        clone = _replace_scene_value(clone, "XPos*", position_property)

        last_name = siblings[-1][1].get("Name", "")
        _last_start, last_end = _egg_span(text, last_name)
        newline = "\r\n" if "\r\n" in text else "\n"
        if text[last_end:last_end + len(newline)] != newline:
            raise OverlayError("could not find the expected line ending after the last class widget")
        insert_at = last_end + len(newline)
        inserted = clone + newline
        text = text[:insert_at] + inserted + text[insert_at:]
        inserted_chunks.append(inserted)
        additions.append(
            {
                "widget": target_name,
                "class": class_name,
                "local_index": local_index,
                "vehicle_id": vehicle_id,
                "template_widget": template_name,
                "frame_index": frame_index,
                "frame_sha256": frame_sha256,
                "image_bank": bank_name,
                "position_property": position_property,
            }
        )

    _scene_tree(text)
    # Prove the only textual changes are the exact appended XML nodes.
    restored = text
    for inserted in reversed(inserted_chunks):
        if restored.count(inserted) != 1:
            raise OverlayError("internal audit failed: generated XML addition is not unique")
        restored = restored.replace(inserted, "", 1)
    if restored != source_text:
        raise OverlayError("internal audit failed: source XML changed outside appended scene nodes")

    output_bytes = (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")
    existed = output_scene.exists()
    if existed:
        if output_scene.read_bytes() != output_bytes:
            raise OverlayError(f"refusing to overwrite a different generated output: {output_scene}")
    else:
        output_scene.parent.mkdir(parents=True, exist_ok=True)
        output_scene.write_bytes(output_bytes)
    return {
        "status": "ALREADY_PRESENT" if existed else "GENERATED",
        "source_scene": str(source_scene),
        "source_sha256": actual_source_sha,
        "output_scene": str(output_scene),
        "output_sha256": sha256_bytes(output_bytes),
        "image_container": str(asset_root / container_name),
        "additions": additions,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-scene", type=Path, required=True)
    parser.add_argument("--output-scene", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = generate_overlay(args.source_scene, args.output_scene, args.asset_root, args.manifest)
    except (OSError, json.JSONDecodeError, OverlayError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
