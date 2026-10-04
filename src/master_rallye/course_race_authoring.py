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


SCHEMA = "master-rallye-race-logic-edit-v2"
_FLOAT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
G1_MARKER_LISTS = (
    "RaceLine",
    "LeftInnerLimit",
    "LeftOuterLimit",
    "RightInnerLimit",
    "RightOuterLimit",
)
_G1_EVIDENCE = {
    "RaceLine": "CONFIRMED_BY_RUNTIME_EDIT: edited samples changed local race progression",
    "LeftInnerLimit": "EXECUTABLE_CONFIRMED; first direct visual probe inconclusive",
    "LeftOuterLimit": "CONFIRMED_BY_RUNTIME_STATE_DIFF: edited boundary changed local LimitState and recovery onset",
    "RightInnerLimit": "EXECUTABLE_CONFIRMED; no direct mutation runtime test",
    "RightOuterLimit": "EXECUTABLE_CONFIRMED; no direct mutation runtime test",
}


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
class RaceLogicVisualCompanionStatus:
    split_identity: str
    source_identity: str
    split_name: str | None
    egg_name: str | None
    position: tuple[float, float, float] | None
    source_xml_path: str
    supported: bool
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class RaceLogicMarkerListStatus:
    name: str
    present: bool
    supported: bool
    marker_count: int
    source_list_ordinal: int | None
    source_xml_path: str | None
    positions: tuple[tuple[float, float, float] | None, ...]
    directions: tuple[tuple[float, float, float] | None, ...]
    evidence_status: str
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
    marker_list_invariants: tuple[dict[str, Any], ...] = ()
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
            "marker_list_invariants": list(self.marker_list_invariants),
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
    semantic_role: str
    marker_list_name: str | None = None
    marker_index: int | None = None


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
    # repr(float) is the shortest decimal that round-trips to the exact Python
    # float. A fixed significant-digit budget truncated large world positions
    # (for example -2469.939355 to -2469.93935) and could change a runtime
    # probe's authored coordinate.
    formatted = repr(float(value))
    return formatted[:-2] if formatted.endswith(".0") else formatted


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
            elif mode == "vector3":
                parts = value.split()
                if len(parts) != 3:
                    raise ValueError(f"Vector3 attribute at {locator!r} no longer has three components")
                attributes[index] = (name, "<allowlisted-x> <allowlisted-y> <allowlisted-z>")
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


def _nearest_route_measure(point, route_positions):
    """Return nearest source-order RaceLine progress and signed X/Z offset."""
    if len(route_positions) < 2:
        return 0.0, 0.0
    lengths = [
        math.dist((a[0], a[2]), (b[0], b[2]))
        for a, b in zip(route_positions, route_positions[1:])
    ]
    total = sum(lengths)
    if total <= 1.0e-9:
        return 0.0, 0.0
    best = None
    traversed = 0.0
    for start, end, length in zip(route_positions, route_positions[1:], lengths):
        dx, dz = end[0] - start[0], end[2] - start[2]
        length_sq = dx * dx + dz * dz
        if length_sq <= 1.0e-12:
            traversed += length
            continue
        amount = max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[2] - start[2]) * dz) / length_sq))
        nearest_x, nearest_z = start[0] + amount * dx, start[2] + amount * dz
        offset_x, offset_z = point[0] - nearest_x, point[2] - nearest_z
        distance = math.hypot(offset_x, offset_z)
        signed_distance = (dx * offset_z - dz * offset_x) / math.sqrt(length_sq)
        progress = (traversed + amount * length) / total
        candidate = (distance, progress, signed_distance)
        if best is None or candidate[0] < best[0]:
            best = candidate
        traversed += length
    return (best[1], best[2]) if best is not None else (0.0, 0.0)


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
        self._visual_companion_bindings: dict[str, _BoundField] = {}
        self._marker_list_bindings: dict[str, list[_BoundField]] = {}
        self._area_status: dict[str, RaceLogicAreaStatus] = {}
        self._split_status: list[RaceLogicSplitStatus] = []
        self._visual_companion_status: list[RaceLogicVisualCompanionStatus] = []
        self._marker_list_status: dict[str, RaceLogicMarkerListStatus] = {}
        self._lexical_editable = not self._source.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff", b"\xff\xfe\x00\x00"))
        self._build_area_bindings()
        self._build_marker_list_bindings()
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
    def visual_companion_status(self) -> tuple[RaceLogicVisualCompanionStatus, ...]:
        return tuple(self._visual_companion_status)

    @property
    def marker_list_status(self) -> tuple[RaceLogicMarkerListStatus, ...]:
        return tuple(self._marker_list_status[name] for name in G1_MARKER_LISTS)

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
                            semantic_role=(
                                "race.start.marker_position" if name == "StartArea"
                                else "race.finish.marker_position"
                            ),
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

    def _build_marker_list_bindings(self) -> None:
        """Bind only the existing G1 Marker Pos values by literal list and ordinal."""
        containers = self._direct_root_children("MarkerLists")
        for name in G1_MARKER_LISTS:
            matches = [item for item in self.document.marker_lists if item.name == name]
            issues: list[str] = []
            positions: list[tuple[float, float, float] | None] = []
            directions: list[tuple[float, float, float] | None] = []
            bindings: list[_BoundField] = []
            if len(containers) != 1:
                issues.append(f"expected one root MarkerLists container; found {len(containers)}")
            elif len(matches) != 1:
                if matches:
                    issues.append(f"expected one MarkerLists/List named {name}; found {len(matches)}")
            else:
                marker_list = matches[0]
                list_elements = [child for child in list(containers[0]) if isinstance(child.tag, str)]
                ordinal = marker_list.ordinal
                if ordinal < 0 or ordinal >= len(list_elements):
                    issues.append("MarkerLists ordinal is outside the source container")
                elif list_elements[ordinal].tag != "List" or list_elements[ordinal].get("Name") != name:
                    issues.append("MarkerLists source ordering does not map unambiguously to the named list")
                else:
                    list_element = list_elements[ordinal]
                    marker_elements = [child for child in list(list_element) if child.tag == "Marker"]
                    if len(marker_elements) != len(marker_list.markers):
                        issues.append("nested or non-direct Marker elements make source order ambiguous")
                    for index, marker_element in enumerate(marker_elements):
                        marker = marker_list.markers[index] if index < len(marker_list.markers) else None
                        values = _direct_values(marker_element, "Marker Pos")
                        direction_values = _direct_values(marker_element, "Marker Dir")
                        position = None
                        direction = None
                        if (len(values) != 1 or values[0].get("Type") != "Vector3"
                                or "Value" not in values[0].attrib):
                            issues.append(f"Marker {index} must have one direct Vector3 Marker Pos value")
                        else:
                            try:
                                position = self._validate_position(_float_tuple(
                                    values[0].get("Value"), 3, f"{name} Marker {index} Pos"
                                ))
                            except ValueError as error:
                                issues.append(str(error))
                            else:
                                if marker is None or marker.index_in_list != index or marker.position != position:
                                    issues.append(f"Marker {index} does not match the canonical Course XML projection")
                                else:
                                    bindings.append(_BoundField(
                                        element=values[0],
                                        locator=self._locators[id(values[0])],
                                        attribute="Value",
                                        mode="vector3",
                                        path=(f"/MarkerLists/{name}/Marker[{index}]"
                                              "/Value[@Name='Marker Pos']/@Value"),
                                        original_raw=values[0].get("Value", ""),
                                        original_value=position,
                                        semantic_role=self._marker_semantic_role(name),
                                        marker_list_name=name,
                                        marker_index=index,
                                    ))
                        if len(direction_values) == 1 and direction_values[0].get("Type") == "Vector3":
                            try:
                                direction = self._validate_position(_float_tuple(
                                    direction_values[0].get("Value"), 3, f"{name} Marker {index} Dir"
                                ))
                            except ValueError as error:
                                issues.append(str(error))
                        elif direction_values:
                            issues.append(f"Marker {index} has ambiguous Marker Dir fields")
                        positions.append(position)
                        directions.append(direction)
                        if marker is None or marker.index_in_list != index:
                            issues.append(f"Marker {index} does not preserve the canonical source ordinal")
                    if not marker_elements:
                        issues.append("marker list is empty; no existing positions can be authored")
            supported = not issues and bool(matches) and len(bindings) == len(matches[0].markers)
            if not supported:
                bindings = []
            self._marker_list_bindings[name] = bindings
            match = matches[0] if len(matches) == 1 else None
            self._marker_list_status[name] = RaceLogicMarkerListStatus(
                name=name,
                present=bool(matches),
                supported=supported,
                marker_count=len(match.markers) if match else 0,
                source_list_ordinal=match.ordinal if match else None,
                source_xml_path=match.xml_path if match else None,
                positions=tuple(positions),
                directions=tuple(directions),
                evidence_status=_G1_EVIDENCE[name],
                issues=tuple(issues),
            )

    @staticmethod
    def _marker_semantic_role(name: str) -> str:
        if name == "RaceLine":
            return "race.route.raceline.marker_position"
        side = "left" if name.startswith("Left") else "right"
        kind = "inner" if "Inner" in name else "outer"
        return f"race.limit.{side}_{kind}.marker_position"

    def _current_marker_positions(self, name: str) -> tuple[tuple[float, float, float] | None, ...]:
        status = self._marker_list_status[name]
        fields = {field.marker_index: field for field in self._marker_list_bindings.get(name, ())}
        values = []
        for index, original in enumerate(status.positions):
            field = fields.get(index)
            pending = self._pending.get((field.locator, field.attribute)) if field is not None else None
            values.append(pending.new_value if pending is not None else original)
        return tuple(values)

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
            source_lists: list[ET.Element] = []
            if len(containers) != 1:
                issues.append(f"expected one root EggLists_Version4 container; found {len(containers)}")
            elif split.source_egg.list_ordinal is None:
                issues.append("split Egg has no unambiguous source list ordinal")
            else:
                lists = [child for child in list(containers[0]) if isinstance(child.tag, str)]
                source_lists = lists
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
                            "race.split.trigger_center",
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
                    if key == "id" and not (-(2 ** 31) <= int(value) <= 2 ** 31 - 1):
                        issues.append(f"{identity} Split Time ID is outside the signed 32-bit range")
                    if key == "radius" and (split.radius is None or float(value) != split.radius or value <= 0):
                        issues.append(f"{identity} Radius is incomplete, differs from the projection, or is not positive")
                    fields[key] = _BoundField(
                        element, self._locators[id(element)], "Value", "attribute",
                        f"{split.source_component.xml_path}/Value[@Name={xml_name!r}]/@Value",
                        element.get("Value", ""), value,
                        "race.split.id" if key == "id" else "race.split.radius",
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
            self._bind_visual_companions(split, identity, source_lists)

    @staticmethod
    def _egg_source_identity(egg) -> str:
        return f"list[{egg.list_ordinal}]/egg[{egg.index_in_list}]/{egg.name or '<unnamed>'}"

    def _bind_visual_companions(self, split, split_identity: str, source_lists: list[ET.Element]) -> None:
        seen: set[str] = set()
        for companion in split.companions:
            egg = companion.source_egg
            source_identity = self._egg_source_identity(egg)
            issues: list[str] = []
            element: ET.Element | None = None
            if not source_lists:
                issues.append("expected one root EggLists_Version4 container and an unambiguous source list")
            elif egg.list_ordinal is None or egg.list_ordinal < 0 or egg.list_ordinal >= len(source_lists):
                issues.append("visual companion has no valid source Egg list ordinal")
            else:
                source_list = source_lists[egg.list_ordinal]
                if source_list.tag != "List" or source_list.get("Name") != egg.list_name:
                    issues.append("visual companion source list identity does not match")
                else:
                    eggs = list(source_list.iter("Egg"))
                    if egg.index_in_list < 0 or egg.index_in_list >= len(eggs):
                        issues.append("visual companion Egg index is outside its source list")
                    else:
                        element = eggs[egg.index_in_list]
                        if element.get("Name") != egg.name:
                            issues.append("visual companion literal Egg name does not match the Course SDK projection")
            if source_identity in seen:
                issues.append("duplicate visual companion source identity")
            seen.add(source_identity)
            if element is not None:
                matrices = [
                    child for child in list(element)
                    if child.tag == "Value" and child.get("Name") == "en3d Matrix" and child.get("Type") == "Matrix"
                ]
                if len(matrices) != 1:
                    issues.append(f"expected one direct en3d Matrix value; found {len(matrices)}")
                else:
                    matrix = matrices[0]
                    try:
                        row = _float_tuple(matrix.get("Row3"), 4, f"{source_identity} en3d Matrix Row3")
                    except ValueError as error:
                        issues.append(str(error))
                    else:
                        position = tuple(row[:3])
                        if companion.position != position:
                            issues.append("visual companion Row3 position does not match the Course SDK projection")
                        if not issues:
                            field = _BoundField(
                                element=matrix,
                                locator=self._locators[id(matrix)],
                                attribute="Row3",
                                mode="row3-xyz",
                                path=f"{egg.xml_path}/Value[@Name='en3d Matrix']/@Row3[XYZ]",
                                original_raw=matrix.get("Row3", ""),
                                original_value=position,
                                semantic_role="race.split.visual_companion_position",
                            )
                            if source_identity not in self._visual_companion_bindings:
                                self._visual_companion_bindings[source_identity] = field
            self._visual_companion_status.append(RaceLogicVisualCompanionStatus(
                split_identity=split_identity,
                source_identity=source_identity,
                split_name=split.egg_name,
                egg_name=egg.name,
                position=companion.position,
                source_xml_path=egg.xml_path,
                supported=not issues and source_identity in self._visual_companion_bindings,
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

    def set_split_visual_companion_position(
        self, split_identity: str, companion_identity: str, runtime_position
    ) -> None:
        position = self._validate_position(runtime_position)
        status = next(
            (item for item in self._visual_companion_status if item.source_identity == companion_identity),
            None,
        )
        if status is None or status.split_identity != split_identity or not status.supported:
            details = "; ".join(status.issues) if status else "source identity not found"
            raise ValueError(f"Split visual companion authoring is refused for {companion_identity!r}: {details}")
        field = self._visual_companion_bindings[companion_identity]
        _float_tuple(field.original_raw, 4, "visual companion matrix Row3")
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
        if not -(2 ** 31) <= split_id <= 2 ** 31 - 1:
            raise ValueError("Split Time ID must fit a signed 32-bit integer")
        field = self._split_fields(source_identity)["id"]
        if split_id == field.original_value:
            self._set_field(field, field.original_raw, split_id)
            return
        self._set_field(field, str(split_id), split_id)

    def set_marker_position(self, list_name: str, index: int, runtime_position) -> None:
        """Move one existing RaceLine/Limit marker without changing list topology."""
        if list_name not in G1_MARKER_LISTS:
            raise ValueError(f"G1.1 marker position authoring does not support {list_name!r}")
        status = self._marker_list_status[list_name]
        if not status.supported:
            raise ValueError(
                f"{list_name} authoring is refused: "
                + "; ".join(status.issues or ("unsupported structure",))
            )
        if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index >= status.marker_count:
            raise ValueError(f"{list_name} marker index must be 0..{status.marker_count - 1}")
        position = self._validate_position(runtime_position)
        field = self._marker_list_bindings[list_name][index]
        if field.marker_index != index or field.marker_list_name != list_name:
            raise ValueError(f"{list_name} marker source ordinal does not map unambiguously")
        if position == field.original_value:
            self._set_field(field, field.original_raw, position)
            return
        # G1's fixed runtime probes serialize Marker Pos as six decimal places;
        # use the same bounded coordinate precision so the stable authoring
        # path can reproduce those verified candidates byte-for-byte.
        self._set_field(field, " ".join(f"{item:.6f}" for item in position), position)

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
        for status in self._visual_companion_status:
            if not status.supported and status.issues:
                warnings.append(f"{status.source_identity} visual companion is read-only: " + "; ".join(status.issues))
        warnings.extend(self._marker_geometry_warnings())
        return tuple(warnings)

    def _marker_geometry_warnings(self) -> tuple[str, ...]:
        warnings: list[str] = []
        for name in G1_MARKER_LISTS:
            status = self._marker_list_status[name]
            if not status.supported:
                if status.present and status.issues:
                    warnings.append(f"{name} is read-only: " + "; ".join(status.issues))
                continue
            fields = self._marker_list_bindings[name]
            edited = {
                field.marker_index for field in fields
                if (field.locator, field.attribute) in self._pending
            }
            if not edited:
                continue
            original = status.positions
            current = self._current_marker_positions(name)
            if any(point is None for point in original) or any(point is None for point in current):
                continue
            baseline = [math.dist(original[i], original[i + 1]) for i in range(len(original) - 1)]
            current_spacings = [math.dist(current[i], current[i + 1]) for i in range(len(current) - 1)]
            positive_baseline = [value for value in baseline if value > 1.0e-6]
            reference = sorted(positive_baseline)[len(positive_baseline) // 2] if positive_baseline else None
            warned_gap = False
            warned_zero = False
            for edge, distance in enumerate(current_spacings):
                if not ({edge, edge + 1} & edited):
                    continue
                if distance < 1.0e-3 and not warned_zero:
                    warnings.append(f"{name} has a near-zero consecutive marker gap at {edge}/{edge + 1}; order was preserved")
                    warned_zero = True
                if reference is not None and distance > max(reference * 5.0, 1.0) and not warned_gap:
                    warnings.append(
                        f"{name} has a large consecutive gap at {edge}/{edge + 1} "
                        f"({distance:.3g}; baseline median {reference:.3g}); inspect source-order sampling"
                    )
                    warned_gap = True
            for index in sorted(edited):
                adjacent = [current_spacings[edge] for edge in (index - 1, index)
                            if 0 <= edge < len(current_spacings) and current_spacings[edge] > 1.0e-6]
                if len(adjacent) == 2 and max(adjacent) / min(adjacent) > 4.0:
                    warnings.append(
                        f"{name} marker {index} creates an extreme neighboring spacing ratio "
                        f"({max(adjacent) / min(adjacent):.3g}); no automatic resampling was applied"
                    )
                if 0 < index < len(current) - 1:
                    before = tuple(current[index][axis] - current[index - 1][axis] for axis in range(3))
                    after = tuple(current[index + 1][axis] - current[index][axis] for axis in range(3))
                    before_len, after_len = math.sqrt(sum(v * v for v in before)), math.sqrt(sum(v * v for v in after))
                    if before_len > 1.0e-6 and after_len > 1.0e-6:
                        cosine = sum(a * b for a, b in zip(before, after)) / (before_len * after_len)
                        if cosine < -0.85:
                            warnings.append(
                                f"{name} marker {index} creates a severe local backtracking candidate "
                                "in source order; inspect the route/corridor"
                            )
            if name != "RaceLine":
                warnings.extend(self._limit_corridor_warnings(name, current, edited))
        return tuple(dict.fromkeys(warnings))

    def _limit_corridor_warnings(self, name, positions, edited_indices) -> tuple[str, ...]:
        """Warn when edited limits cross a stable baseline side/order relationship."""
        route_status = self._marker_list_status["RaceLine"]
        if not route_status.supported or any(item is None for item in route_status.positions):
            return ()
        route = self._current_marker_positions("RaceLine")
        if any(item is None for item in route):
            return ()
        baseline_signs = []
        for point in self._marker_list_status[name].positions:
            progress, signed = _nearest_route_measure(point, route_status.positions)
            if abs(signed) > 1.0e-3:
                baseline_signs.append(1 if signed > 0 else -1)
        # Confidence is based on this limit list's own population.  A much
        # denser RaceLine must not disable diagnostics for a valid shorter
        # corridor list.
        limit_status = self._marker_list_status[name]
        if len(baseline_signs) < max(3, limit_status.marker_count // 4):
            return ()
        expected_sign = 1 if sum(baseline_signs) >= 0 else -1
        warnings = []
        for index in sorted(edited_indices):
            progress, signed = _nearest_route_measure(positions[index], route)
            if abs(signed) > 1.0 and (1 if signed > 0 else -1) != expected_sign:
                warnings.append(
                    f"{name} marker {index} crosses the list's baseline RaceLine-side polarity "
                    f"near progress {progress:.3f}; review intended corridor placement"
                )
        if name.endswith("OuterLimit"):
            inner_name = name.replace("OuterLimit", "InnerLimit")
            inner_status = self._marker_list_status[inner_name]
            inner_positions = self._current_marker_positions(inner_name) if inner_status.supported else ()
            valid_inner = [(point, _nearest_route_measure(point, route)[0]) for point in inner_positions if point is not None]
            for index in sorted(edited_indices):
                point_progress, outer_signed = _nearest_route_measure(positions[index], route)
                if not valid_inner:
                    break
                nearest_inner, inner_progress = min(valid_inner, key=lambda item: abs(item[1] - point_progress))
                _progress, inner_signed = _nearest_route_measure(nearest_inner, route)
                inner_distance = abs(inner_signed)
                if abs(point_progress - inner_progress) > 0.05:
                    continue
                if abs(outer_signed) + 0.5 < inner_distance:
                    warnings.append(
                        f"{name} marker {index} is closer to RaceLine than the nearest-progress {inner_name} sample; "
                        "check inner/outer ordering"
                    )
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
        changes = tuple(self._change_record(mutation) for mutation in ordered)
        marker_list_invariants = tuple({
            "marker_list": name,
            "source_marker_count": status.marker_count,
            "output_marker_count": status.marker_count,
            "marker_count_unchanged": True,
            "source_order_unchanged": True,
        } for name in G1_MARKER_LISTS if (status := self._marker_list_status[name]).present)
        report = RaceLogicExportReport(
            course_identity=self.course_identity,
            source_xml=self.source,
            source_sha256=self.source_sha256,
            exported_sha256=hashlib.sha256(output).hexdigest(),
            changed_semantic_paths=tuple(item["path"] for item in changes),
            changes=changes,
            unknown_content_preserved=True,
            warnings=tuple(self.validation_warnings()) + tuple(str(item) for item in additional_warnings),
            marker_list_invariants=marker_list_invariants,
        )
        return output, report

    @staticmethod
    def _change_record(mutation: _Mutation) -> dict[str, Any]:
        field = mutation.field
        change: dict[str, Any] = {
            "path": field.path,
            "semantic_role": field.semantic_role,
            "old": field.original_value,
            "new": mutation.new_value,
        }
        if field.marker_list_name is not None:
            change["marker_list"] = field.marker_list_name
            change["marker_index"] = field.marker_index
            change["delta"] = [
                float(new) - float(old)
                for old, new in zip(field.original_value, mutation.new_value)
            ]
        return change

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
