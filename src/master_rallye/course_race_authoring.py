"""Allowlist-constrained, source-preserving RaceTest logic authoring.

Only runtime-confirmed RaceTest fields are editable here. XML is patched at the
source attribute spans, so comments, whitespace, unknown nodes, and unrelated
source bytes are retained exactly. This module intentionally has no DX/GXM or
physical-course writer.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.parsers import expat

from .course_sdk import CourseRaceLogic, CourseSplitTime, build_course_race_logic
from .course_xml import CourseXmlDocument, parse_course_xml_bytes
from .errors import FormatError


SCHEMA = "master-rallye-race-logic-edit-v1"
_FLOAT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


@dataclass(frozen=True)
class RaceLogicAreaStatus:
    name: str
    present: bool
    supported: bool
    marker_count: int
    source_xml_path: str | None
    positions: tuple[tuple[float, float, float] | None, ...]
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class RaceLogicSplitStatus:
    identity: str
    egg_name: str | None
    split_id: int | None
    center: tuple[float, float, float] | None
    radius: float | None
    extra_time_raw: str | None
    source_xml_path: str
    supported: bool
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class RaceLogicExportReport:
    course_identity: str
    source_xml: str
    source_sha256: str
    exported_sha256: str
    changed_semantic_paths: tuple[str, ...]
    changes: tuple[dict[str, Any], ...]
    unknown_content_preserved: bool
    warnings: tuple[str, ...]
    schema: str = SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "course_identity": self.course_identity,
            "source_xml": self.source_xml,
            "source_xml_sha256": self.source_sha256,
            "exported_xml_sha256": self.exported_sha256,
            "changed_semantic_paths": list(self.changed_semantic_paths),
            "changes": list(self.changes),
            "unknown_content_preserved": self.unknown_content_preserved,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class _StartTag:
    name: str
    start: int
    end: int
    attributes: dict[str, tuple[int, int, int]]  # name -> (value start, value end, quote byte)


@dataclass
class _BoundField:
    element: ET.Element
    locator: tuple[int, ...]
    attribute: str
    mode: str
    path: str
    original_raw: str
    original_value: Any


@dataclass
class _Mutation:
    field: _BoundField
    new_raw: str
    new_value: Any


def _xml_parser() -> ET.XMLParser:
    return ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True))


def _parse_tree(data: bytes, source: str) -> ET.Element:
    try:
        return ET.fromstring(data, parser=_xml_parser())
    except ET.ParseError as error:
        raise FormatError(f"invalid RaceTest XML in {source}: {error}") from error


def _locator_index(root: ET.Element) -> dict[int, tuple[int, ...]]:
    result: dict[int, tuple[int, ...]] = {id(root): ()}

    def visit(parent: ET.Element, path: tuple[int, ...]) -> None:
        for index, child in enumerate(list(parent)):
            child_path = path + (index,)
            result[id(child)] = child_path
            visit(child, child_path)

    visit(root, ())
    return result


def _at_locator(root: ET.Element, locator: tuple[int, ...]) -> ET.Element:
    element = root
    for index in locator:
        children = list(element)
        if index < 0 or index >= len(children):
            raise ValueError(f"RaceTest XML structure changed at child path {locator!r}")
        element = children[index]
    return element


def _float_tuple(raw: str | None, count: int, what: str) -> tuple[float, ...]:
    if raw is None:
        raise ValueError(f"{what} is missing")
    parts = raw.split()
    if len(parts) != count or any(not _FLOAT.fullmatch(part) for part in parts):
        raise ValueError(f"{what} must contain {count} finite numbers")
    values = tuple(float(part) for part in parts)
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{what} contains a non-finite number")
    return values


def _format_float(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("RaceTest authoring values must be finite")
    return format(float(value), ".9g")


def _direct_values(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(element) if child.tag == "Value" and child.get("Name") == name]


def _same3(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    return len(left) == len(right) == 3 and all(a == b for a, b in zip(left, right))


def _read_start_tag_end(data: bytes, start: int) -> int:
    quote = 0
    for index in range(start + 1, len(data)):
        byte = data[index]
        if quote:
            if byte == quote:
                quote = 0
        elif byte in (ord("'"), ord('"')):
            quote = byte
        elif byte == ord(">"):
            return index + 1
    raise ValueError(f"unterminated XML start tag at byte {start}")


def _parse_start_tag_attributes(data: bytes, start: int, end: int) -> dict[str, tuple[int, int, int]]:
    index = start + 1
    while index < end and data[index] not in b" \t\r\n/>":
        index += 1  # element name
    attributes: dict[str, tuple[int, int, int]] = {}
    while index < end:
        while index < end and data[index] in b" \t\r\n":
            index += 1
        if index >= end or data[index] in b"/>":
            break
        name_start = index
        while index < end and data[index] not in b" \t\r\n=/>":
            index += 1
        name = data[name_start:index].decode("ascii", errors="strict")
        while index < end and data[index] in b" \t\r\n":
            index += 1
        if index >= end or data[index] != ord("="):
            raise ValueError(f"malformed XML attribute in start tag at byte {start}")
        index += 1
        while index < end and data[index] in b" \t\r\n":
            index += 1
        if index >= end or data[index] not in (ord("'"), ord('"')):
            raise ValueError(f"unquoted XML attribute in start tag at byte {start}")
        quote = data[index]
        index += 1
        value_start = index
        while index < end and data[index] != quote:
            index += 1
        if index >= end:
            raise ValueError(f"unterminated XML attribute in start tag at byte {start}")
        attributes[name] = (value_start, index, quote)
        index += 1
    return attributes


def _source_start_tags(data: bytes) -> dict[tuple[int, ...], _StartTag]:
    """Map XML element child-index paths to exact source opening-tag spans."""
    tags: dict[tuple[int, ...], _StartTag] = {}
    parser = expat.ParserCreate()
    stack: list[tuple[int, ...]] = []
    child_counts: list[int] = []

    def start(name: str, _attributes: dict[str, str]) -> None:
        offset = parser.CurrentByteIndex
        if stack:
            child_index = child_counts[-1]
            child_counts[-1] += 1
            locator = stack[-1] + (child_index,)
        else:
            locator = ()
        end = _read_start_tag_end(data, offset)
        tags[locator] = _StartTag(
            name=name,
            start=offset,
            end=end,
            attributes=_parse_start_tag_attributes(data, offset, end),
        )
        stack.append(locator)
        child_counts.append(0)

    def end(_name: str) -> None:
        stack.pop()
        child_counts.pop()

    def child_node(*_args: Any) -> None:
        if stack:
            child_counts[-1] += 1

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CommentHandler = child_node
    parser.ProcessingInstructionHandler = child_node
    try:
        parser.Parse(data, True)
    except expat.ExpatError as error:
        raise FormatError(f"invalid RaceTest XML for source-span scan: {error}") from error
    return tags


def _xml_attr_replace(value: str, quote: int) -> bytes:
    escaped = value.replace("&", "&amp;").replace("<", "&lt;")
    if quote == ord('"'):
        escaped = escaped.replace('"', "&quot;")
    else:
        escaped = escaped.replace("'", "&apos;")
    try:
        return escaped.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("RaceTest allowlisted fields must serialize as ASCII numeric values") from error


def _tree_projection(root: ET.Element, masks: dict[tuple[int, ...], dict[str, str]]) -> tuple[Any, ...]:
    def tag_name(element: ET.Element) -> str:
        if isinstance(element.tag, str):
            return element.tag
        if element.tag is ET.Comment:
            return "#comment"
        if element.tag is ET.ProcessingInstruction:
            return "#processing-instruction"
        return repr(element.tag)

    def visit(element: ET.Element, locator: tuple[int, ...]) -> tuple[Any, ...]:
        attributes = list(element.attrib.items())
        modes = masks.get(locator, {})
        for index, (name, value) in enumerate(attributes):
            mode = modes.get(name)
            if mode == "attribute":
                attributes[index] = (name, "<allowlisted-value>")
            elif mode == "row3-xyz":
                parts = value.split()
                if len(parts) != 4:
                    raise ValueError(f"matrix Row3 at {locator!r} no longer has four components")
                attributes[index] = (name, "<allowlisted-x> <allowlisted-y> <allowlisted-z> " + parts[3])
        children = tuple(visit(child, locator + (index,)) for index, child in enumerate(list(element)))
        return (tag_name(element), tuple(attributes), element.text, element.tail, children)

    return visit(root, ())


def _semantic_guard(
    original: bytes,
    output: bytes,
    masks: dict[tuple[int, ...], dict[str, str]],
) -> bool:
    before = _parse_tree(original, "<original>")
    after = _parse_tree(output, "<export>")
    return _tree_projection(before, masks) == _tree_projection(after, masks)


class CourseRaceLogicAuthoring:
    """A bounded edit transaction over one original RaceTest XML document."""

    def __init__(self, data: bytes, source: str = "<bytes>") -> None:
        self.source = str(source)
        self.course_identity = Path(source).stem if source not in {"", "<bytes>"} else "course"
        self._source = bytes(data)
        self.source_sha256 = hashlib.sha256(self._source).hexdigest()
        self.document: CourseXmlDocument = parse_course_xml_bytes(self._source, source)
        self.race_logic: CourseRaceLogic = build_course_race_logic(self.document)
        self._root = _parse_tree(self._source, source)
        self._locators = _locator_index(self._root)
        self._pending: dict[tuple[tuple[int, ...], str], _Mutation] = {}
        self._area_bindings: dict[str, list[_BoundField]] = {}
        self._split_bindings: dict[str, dict[str, _BoundField]] = {}
        self._area_status: dict[str, RaceLogicAreaStatus] = {}
        self._split_status: list[RaceLogicSplitStatus] = []
        self._lexical_editable = not self._source.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff", b"\xff\xfe\x00\x00"))
        self._build_area_bindings()
        self._build_split_bindings()

    @classmethod
    def from_path(cls, path: Path) -> "CourseRaceLogicAuthoring":
        resolved = Path(path).expanduser().resolve()
        return cls(resolved.read_bytes(), str(resolved))

    @property
    def area_status(self) -> tuple[RaceLogicAreaStatus, ...]:
        return tuple(self._area_status[name] for name in ("StartArea", "FinishArea"))

    @property
    def split_status(self) -> tuple[RaceLogicSplitStatus, ...]:
        return tuple(self._split_status)

    @property
    def mutation_count(self) -> int:
        return len(self._pending)

    def _direct_root_children(self, tag: str) -> list[ET.Element]:
        return [child for child in list(self._root) if child.tag == tag]

    def _build_area_bindings(self) -> None:
        marker_containers = self._direct_root_children("MarkerLists")
        for name in ("StartArea", "FinishArea"):
            semantic = self.race_logic.start_area if name == "StartArea" else self.race_logic.finish_area
            issues: list[str] = []
            bindings: list[_BoundField] = []
            positions: tuple[tuple[float, float, float] | None, ...] = ()
            matches = [item for item in self.document.marker_lists if item.name == name]
            present = bool(matches)
            if len(marker_containers) != 1:
                issues.append(f"expected one root MarkerLists container; found {len(marker_containers)}")
            elif len(matches) != 1 or semantic is None:
                issues.append(f"expected one MarkerLists/List named {name}; found {len(matches)}")
            else:
                container = marker_containers[0]
                list_elements = [child for child in list(container) if isinstance(child.tag, str)]
                marker_list = matches[0]
                if (marker_list.ordinal >= len(list_elements)
                        or list_elements[marker_list.ordinal].tag != "List"
                        or list_elements[marker_list.ordinal].get("Name") != name):
                    issues.append("MarkerLists source ordering does not map unambiguously to the semantic list")
                else:
                    list_element = list_elements[marker_list.ordinal]
                    marker_elements = [child for child in list(list_element) if child.tag == "Marker"]
                    if len(marker_elements) != len(marker_list.markers):
                        issues.append("nested or non-direct Marker elements make source ordering ambiguous")
                    if len(marker_elements) != 4:
                        issues.append(f"authoring requires exactly four ordered markers; found {len(marker_elements)}")
                    marker_positions = []
                    for index, marker_element in enumerate(marker_elements):
                        values = _direct_values(marker_element, "Marker Pos")
                        marker = marker_list.markers[index] if index < len(marker_list.markers) else None
                        if len(values) != 1 or values[0].get("Type") != "Vector3" or "Value" not in values[0].attrib:
                            issues.append(f"Marker {index} must have one direct Vector3 Marker Pos value")
                            marker_positions.append(None)
                            continue
                        try:
                            parsed = _float_tuple(values[0].get("Value"), 3, f"{name} Marker {index} Pos")
                        except ValueError as error:
                            issues.append(str(error))
                            marker_positions.append(None)
                            continue
                        position = tuple(parsed)
                        marker_positions.append(position)
                        if marker is None or marker.index_in_list != index or marker.position != position:
                            issues.append(f"Marker {index} does not match the canonical Course SDK projection")
                            continue
                        element = values[0]
                        bindings.append(_BoundField(
                            element=element,
                            locator=self._locators[id(element)],
                            attribute="Value",
                            mode="attribute",
                            path=f"/MarkerLists/{name}/Marker[{index}]/Value[@Name='Marker Pos']/@Value",
                            original_raw=element.get("Value", ""),
                            original_value=position,
                        ))
                    positions = tuple(marker_positions)
            supported = not issues and len(bindings) == 4
            if not supported:
                bindings = []
            self._area_bindings[name] = bindings
            path = semantic.source_xml_path if semantic is not None else None
            self._area_status[name] = RaceLogicAreaStatus(
                name=name,
                present=present,
                supported=supported,
                marker_count=len(matches[0].markers) if len(matches) == 1 else 0,
                source_xml_path=path,
                positions=positions,
                issues=tuple(issues),
            )

    def _build_split_bindings(self) -> None:
        containers = self._direct_root_children("EggLists_Version4")
        seen_ids: set[str] = set()
        for split in self.race_logic.split_times:
            issues: list[str] = []
            fields: dict[str, _BoundField] = {}
            identity = (
                f"list[{split.source_egg.list_ordinal}]/egg[{split.source_egg.index_in_list}]"
                f"/{split.source_egg.name or '<unnamed>'}/component[{split.source_component.ai_no or '?'}]"
            )
            if identity in seen_ids:
                issues.append("duplicate structural split identity")
            seen_ids.add(identity)
            egg_element: ET.Element | None = None
            if len(containers) != 1:
                issues.append(f"expected one root EggLists_Version4 container; found {len(containers)}")
            elif split.source_egg.list_ordinal is None:
                issues.append("split Egg has no unambiguous source list ordinal")
            else:
                lists = [child for child in list(containers[0]) if isinstance(child.tag, str)]
                list_ordinal = split.source_egg.list_ordinal
                if list_ordinal >= len(lists):
                    issues.append("split Egg list ordinal is outside the source container")
                elif lists[list_ordinal].tag != "List":
                    issues.append("split Egg parent is not a structurally identified List element")
                else:
                    eggs = list(lists[list_ordinal].iter("Egg"))
                    if split.source_egg.index_in_list >= len(eggs):
                        issues.append("split Egg index is outside its source list")
                    else:
                        egg_element = eggs[split.source_egg.index_in_list]
                        if egg_element.get("Name") != split.source_egg.name:
                            issues.append("split Egg literal name does not match the Course SDK projection")

            component_element: ET.Element | None = None
            matrix_element: ET.Element | None = None
            if egg_element is not None:
                components = [
                    component
                    for ai in egg_element.iter("AI")
                    for component in list(ai)
                    if component.tag == "gaRaceSplitTimeAI"
                ]
                if len(components) != 1:
                    issues.append(f"expected one gaRaceSplitTimeAI component under the main Egg; found {len(components)}")
                else:
                    component_element = components[0]
                matrices = [
                    child for child in list(egg_element)
                    if child.tag == "Value" and child.get("Name") == "en3d Matrix" and child.get("Type") == "Matrix"
                ]
                if len(matrices) != 1:
                    issues.append(f"expected one direct en3d Matrix value; found {len(matrices)}")
                else:
                    matrix_element = matrices[0]
                    try:
                        row = _float_tuple(matrix_element.get("Row3"), 4, f"{identity} en3d Matrix Row3")
                    except ValueError as error:
                        issues.append(str(error))
                    else:
                        fields["center"] = _BoundField(
                            matrix_element, self._locators[id(matrix_element)], "Row3", "row3-xyz",
                            f"{split.source_egg.xml_path}/Value[@Name='en3d Matrix']/@Row3[XYZ]",
                            matrix_element.get("Row3", ""), tuple(row[:3]),
                        )
                        if split.center != tuple(row[:3]):
                            issues.append("Egg Row3 center does not match the Course SDK projection")
            if component_element is not None:
                for key, xml_name, type_name, parser in (
                    ("id", "Split Time ID", "Int", lambda raw: int(raw.strip())),
                    ("radius", "Radius", "Float", lambda raw: float(raw.strip())),
                ):
                    values = _direct_values(component_element, xml_name)
                    if len(values) != 1 or values[0].get("Type") != type_name or "Value" not in values[0].attrib:
                        issues.append(f"{identity} requires one direct {type_name} {xml_name} property")
                        continue
                    element = values[0]
                    try:
                        value = parser(element.get("Value", ""))
                    except (ValueError, OverflowError):
                        issues.append(f"{identity} {xml_name} is not a valid {type_name}")
                        continue
                    if isinstance(value, float) and not math.isfinite(value):
                        issues.append(f"{identity} {xml_name} is non-finite")
                        continue
                    if key == "id" and (split.split_id is None or int(value) != split.split_id):
                        issues.append(f"{identity} ID does not match the Course SDK projection")
                    if key == "radius" and (split.radius is None or float(value) != split.radius or value <= 0):
                        issues.append(f"{identity} Radius is incomplete, differs from the projection, or is not positive")
                    fields[key] = _BoundField(
                        element, self._locators[id(element)], "Value", "attribute",
                        f"{split.source_component.xml_path}/Value[@Name={xml_name!r}]/@Value",
                        element.get("Value", ""), value,
                    )
            supported = not issues and set(fields) == {"center", "id", "radius"}
            if supported:
                self._split_bindings[identity] = fields
            self._split_status.append(RaceLogicSplitStatus(
                identity=identity,
                egg_name=split.egg_name,
                split_id=split.split_id,
                center=split.center,
                radius=split.radius,
                extra_time_raw=split.extra_time_raw,
                source_xml_path=split.egg_xml_path,
                supported=supported,
                issues=tuple(issues),
            ))

    def _set_field(self, field: _BoundField, new_raw: str, new_value: Any) -> None:
        key = (field.locator, field.attribute)
        if new_raw == field.original_raw:
            field.element.set(field.attribute, field.original_raw)
            self._pending.pop(key, None)
            return
        field.element.set(field.attribute, new_raw)
        self._pending[key] = _Mutation(field=field, new_raw=new_raw, new_value=new_value)

    @staticmethod
    def _validate_position(position) -> tuple[float, float, float]:
        if len(position) != 3:
            raise ValueError("RaceTest positions must contain exactly three coordinates")
        values = tuple(float(item) for item in position)
        if not all(math.isfinite(item) for item in values):
            raise ValueError("RaceTest positions must be finite")
        return values  # type: ignore[return-value]

    def set_start_marker(self, index: int, runtime_position) -> None:
        self._set_area_marker("StartArea", index, runtime_position)

    def set_finish_marker(self, index: int, runtime_position) -> None:
        self._set_area_marker("FinishArea", index, runtime_position)

    def _set_area_marker(self, name: str, index: int, runtime_position) -> None:
        status = self._area_status[name]
        if not status.supported:
            raise ValueError(f"{name} authoring is refused: " + "; ".join(status.issues or ("unsupported structure",)))
        if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index >= 4:
            raise ValueError(f"{name} marker index must be 0..3")
        position = self._validate_position(runtime_position)
        field = self._area_bindings[name][index]
        if position == field.original_value:
            self._set_field(field, field.original_raw, position)
            return
        raw = " ".join(_format_float(item) for item in position)
        self._set_field(field, raw, position)

    def _split_fields(self, identity: str) -> dict[str, _BoundField]:
        fields = self._split_bindings.get(identity)
        if fields is None:
            status = next((item for item in self._split_status if item.identity == identity), None)
            details = "; ".join(status.issues) if status else "identity not found"
            raise ValueError(f"SplitTime authoring is refused for {identity!r}: {details}")
        return fields

    def set_split_center(self, source_identity: str, runtime_position) -> None:
        position = self._validate_position(runtime_position)
        field = self._split_fields(source_identity)["center"]
        _float_tuple(field.original_raw, 4, "split matrix Row3")
        original_w = field.original_raw.split()[3]
        if position == field.original_value:
            self._set_field(field, field.original_raw, position)
            return
        raw = " ".join((*(_format_float(item) for item in position), original_w))
        self._set_field(field, raw, position)

    def set_split_radius(self, source_identity: str, radius: float) -> None:
        value = float(radius)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError("SplitTime Radius must be a finite value greater than zero")
        field = self._split_fields(source_identity)["radius"]
        if value == field.original_value:
            self._set_field(field, field.original_raw, value)
            return
        self._set_field(field, _format_float(value), value)

    def set_split_id(self, source_identity: str, split_id: int) -> None:
        if isinstance(split_id, bool) or not isinstance(split_id, int):
            raise ValueError("Split Time ID must be an integer")
        field = self._split_fields(source_identity)["id"]
        if split_id == field.original_value:
            self._set_field(field, field.original_raw, split_id)
            return
        self._set_field(field, str(split_id), split_id)

    def validation_warnings(self) -> tuple[str, ...]:
        warnings: list[str] = []
        for name in ("StartArea", "FinishArea"):
            status = self._area_status[name]
            fields = self._area_bindings[name]
            if not status.supported:
                if status.present:
                    warnings.append(f"{name} is read-only: " + "; ".join(status.issues))
                continue
            points = [tuple(float(value) for value in field.element.get("Value", "").split()) for field in fields]
            if any(len(point) != 3 for point in points):
                continue
            if any(math.dist(a, b) < 1e-5 for i, a in enumerate(points) for b in points[i + 1:]):
                warnings.append(f"{name} contains coincident or nearly coincident markers")
            xz = [(point[0], point[2]) for point in points]
            area = abs(sum(xz[i][0] * xz[(i + 1) % 4][1] - xz[(i + 1) % 4][0] * xz[i][1] for i in range(4))) * 0.5
            if area < 1e-4:
                warnings.append(f"{name} has nearly zero projected X/Z area")
            if _segment_intersects(xz[0], xz[1], xz[2], xz[3]) or _segment_intersects(xz[1], xz[2], xz[3], xz[0]):
                warnings.append(f"{name} projected X/Z perimeter self-crosses; marker order was preserved")
            xs, ys, zs = [p[0] for p in points], [p[1] for p in points], [p[2] for p in points]
            if max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) > 100000:
                warnings.append(f"{name} extent exceeds 100000 runtime units; inspect this unusually large edit")
        ids: dict[int, list[str]] = {}
        for status in self._split_status:
            fields = self._split_bindings.get(status.identity)
            if not fields:
                if status.issues:
                    warnings.append(f"{status.identity} is read-only: " + "; ".join(status.issues))
                continue
            split_id = int(fields["id"].element.get("Value", "0"))
            ids.setdefault(split_id, []).append(status.identity)
            radius = float(fields["radius"].element.get("Value", "0"))
            if radius > 10000:
                warnings.append(f"{status.identity} Radius exceeds 10000 units; no hard game limit is asserted")
        for split_id, identities in ids.items():
            if len(identities) > 1:
                warnings.append(f"duplicate Split Time ID {split_id}: " + ", ".join(identities))
        return tuple(warnings)

    def export(self, additional_warnings=()) -> tuple[bytes, RaceLogicExportReport]:
        output = self._source
        masks: dict[tuple[int, ...], dict[str, str]] = {}
        if self._pending:
            if not self._lexical_editable:
                raise ValueError("editing UTF-16/UTF-32 XML is refused; no-op export remains byte-identical")
            tags = _source_start_tags(self._source)
            replacements: list[tuple[int, int, bytes]] = []
            for mutation in self._pending.values():
                field = mutation.field
                tag = tags.get(field.locator)
                if tag is None or tag.name != str(field.element.tag):
                    raise ValueError(f"source-span lookup failed for allowlisted field {field.path}")
                attribute = tag.attributes.get(field.attribute)
                if attribute is None:
                    raise ValueError(f"source attribute not found for allowlisted field {field.path}")
                value_start, value_end, quote = attribute
                replacements.append((value_start, value_end, _xml_attr_replace(mutation.new_raw, quote)))
                masks.setdefault(field.locator, {})[field.attribute] = field.mode
            for start, end, replacement in sorted(replacements, reverse=True):
                output = output[:start] + replacement + output[end:]
            if not _semantic_guard(self._source, output, masks):
                raise ValueError("RaceTest export semantic diff guard rejected a non-allowlisted XML change")

        ordered = sorted(
            self._pending.values(),
            key=lambda item: self._locators[id(item.field.element)],
        )
        changes = tuple({
            "path": mutation.field.path,
            "old": mutation.field.original_value,
            "new": mutation.new_value,
        } for mutation in ordered)
        report = RaceLogicExportReport(
            course_identity=self.course_identity,
            source_xml=self.source,
            source_sha256=self.source_sha256,
            exported_sha256=hashlib.sha256(output).hexdigest(),
            changed_semantic_paths=tuple(item["path"] for item in changes),
            changes=changes,
            unknown_content_preserved=True,
            warnings=tuple(self.validation_warnings()) + tuple(str(item) for item in additional_warnings),
        )
        return output, report

    def write_export(self, output_path: Path, *, additional_warnings=()) -> RaceLogicExportReport:
        output = Path(output_path).expanduser().resolve()
        if self.source not in {"", "<bytes>"} and output == Path(self.source).expanduser().resolve():
            raise ValueError("RaceTest export cannot overwrite its source XML")
        manifest_path = output.with_name(output.name + ".mr-race-edit.json")
        if output.exists() or manifest_path.exists():
            raise FileExistsError("output XML or edit manifest already exists; choose a new output path")
        xml_bytes, report = self.export(additional_warnings=additional_warnings)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = report.to_dict()
        with output.open("xb") as stream:
            stream.write(xml_bytes)
        try:
            with manifest_path.open("xb") as stream:
                stream.write((json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        except Exception:
            output.unlink(missing_ok=True)
            raise
        return report


def _segment_intersects(a, b, c, d) -> bool:
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    ab_c, ab_d = orient(a, b, c), orient(a, b, d)
    cd_a, cd_b = orient(c, d, a), orient(c, d, b)
    return ab_c * ab_d < 0 and cd_a * cd_b < 0


def load_course_race_logic_authoring(path: Path) -> CourseRaceLogicAuthoring:
    return CourseRaceLogicAuthoring.from_path(path)
