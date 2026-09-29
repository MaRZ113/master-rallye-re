"""Read-only, hierarchy-preserving extraction of RaceTest XML course data."""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .errors import FormatError


FLOAT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
RECORD_TAGS = {"Marker", "gaRaceSplitTimeAI", "gaRacePostFirstSplitTimeAI", "gaLimitBuilderAI"}


@dataclass(frozen=True)
class CourseXmlValue:
    name: str
    type_name: str
    value: str
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class CourseXmlRecord:
    tag: str
    ordinal: int
    attributes: tuple[tuple[str, str], ...]
    values: tuple[CourseXmlValue, ...]
    xml_path: str = ""
    marker_list_name: str | None = None
    egg_list_name: str | None = None
    egg_name: str | None = None
    ai_no: str | None = None

    def value(self, name: str) -> CourseXmlValue | None:
        return next((item for item in self.values if item.name == name), None)


@dataclass(frozen=True)
class CourseXmlNode:
    """Generic XML tree node retaining unknown tags, attributes, and ordering."""

    tag: str
    ordinal: int
    xml_path: str
    attributes: tuple[tuple[str, str], ...]
    text: str
    children: tuple[CourseXmlNode, ...]

    def attribute(self, name: str) -> str | None:
        return dict(self.attributes).get(name)


@dataclass(frozen=True)
class CourseXmlMatrix:
    name: str
    type_name: str
    attributes: tuple[tuple[str, str], ...]
    rows: tuple[tuple[float, float, float, float] | None, ...]
    issues: tuple[str, ...] = ()

    def row(self, index: int) -> tuple[float, float, float, float] | None:
        return self.rows[index] if 0 <= index < len(self.rows) else None

    @property
    def position(self) -> tuple[float, float, float] | None:
        row = self.row(3)
        return row[:3] if row is not None else None


@dataclass(frozen=True)
class CourseXmlAiComponent:
    tag: str
    ai_no: str | None
    ai_name: str | None
    attributes: tuple[tuple[str, str], ...]
    values: tuple[CourseXmlValue, ...]
    xml_path: str

    def value(self, name: str) -> CourseXmlValue | None:
        return next((item for item in self.values if item.name == name), None)


@dataclass(frozen=True)
class CourseXmlAiObject:
    ordinal: int
    ai_no: str | None
    ai_name: str | None
    attributes: tuple[tuple[str, str], ...]
    values: tuple[CourseXmlValue, ...]
    components: tuple[CourseXmlAiComponent, ...]
    xml_path: str


@dataclass(frozen=True)
class CourseXmlEgg:
    ordinal: int
    list_name: str | None
    list_ordinal: int | None
    index_in_list: int
    name: str | None
    attributes: tuple[tuple[str, str], ...]
    values: tuple[CourseXmlValue, ...]
    model_name: str | None
    matrices: tuple[CourseXmlMatrix, ...]
    ai_objects: tuple[CourseXmlAiObject, ...]
    xml_path: str

    def matrix(self, name: str = "en3d Matrix") -> CourseXmlMatrix | None:
        return next((item for item in self.matrices if item.name == name), None)

    def components(self, tag: str | None = None) -> tuple[CourseXmlAiComponent, ...]:
        found = tuple(component for ai in self.ai_objects for component in ai.components)
        return found if tag is None else tuple(item for item in found if item.tag == tag)

    @property
    def split_time_component(self) -> CourseXmlAiComponent | None:
        return next((item for item in self.components("gaRaceSplitTimeAI")), None)


@dataclass(frozen=True)
class CourseXmlMarker:
    ordinal: int
    marker_no: str | None
    marker_type: str | None
    position: tuple[float, float, float] | None
    direction: tuple[float, float, float] | None
    raw_position: str | None
    raw_direction: str | None
    record: CourseXmlRecord
    issues: tuple[str, ...]
    marker_list_name: str | None = None
    marker_list_ordinal: int | None = None
    index_in_list: int = 0


@dataclass(frozen=True)
class CourseXmlMarkerList:
    ordinal: int
    name: str | None
    attributes: tuple[tuple[str, str], ...]
    markers: tuple[CourseXmlMarker, ...]
    xml_path: str


@dataclass(frozen=True)
class CourseXmlDocument:
    source: str
    root_tag: str
    records: tuple[CourseXmlRecord, ...]
    markers: tuple[CourseXmlMarker, ...]
    root: CourseXmlNode
    marker_lists: tuple[CourseXmlMarkerList, ...]
    eggs: tuple[CourseXmlEgg, ...]

    @property
    def split_time_records(self) -> tuple[CourseXmlRecord, ...]:
        return tuple(item for item in self.records if item.tag == "gaRaceSplitTimeAI")

    @property
    def limit_builder_records(self) -> tuple[CourseXmlRecord, ...]:
        return tuple(item for item in self.records if item.tag == "gaLimitBuilderAI")

    @property
    def split_time_eggs(self) -> tuple[CourseXmlEgg, ...]:
        return tuple(item for item in self.eggs if item.split_time_component is not None)

    def marker_list(self, name: str) -> CourseXmlMarkerList | None:
        return next((item for item in self.marker_lists if item.name == name), None)


def _attributes(element: ET.Element) -> tuple[tuple[str, str], ...]:
    return tuple((str(key), str(value)) for key, value in element.attrib.items())


def _element_label(element: ET.Element, sibling_index: int) -> str:
    tag = str(element.tag)
    identity = element.attrib.get("Name") or element.attrib.get("No")
    if identity is not None:
        return f"{tag}[@Name={identity!r}]" if "Name" in element.attrib else f"{tag}[@No={identity!r}]"
    return f"{tag}[{sibling_index}]"


def _build_tree(element: ET.Element, ordinal: list[int], path: str) -> CourseXmlNode:
    node_ordinal = ordinal[0]
    ordinal[0] += 1
    same_tag_seen: dict[str, int] = {}
    children = []
    for child in list(element):
        tag = str(child.tag)
        index = same_tag_seen.get(tag, 0)
        same_tag_seen[tag] = index + 1
        child_path = f"{path}/{_element_label(child, index)}"
        children.append(_build_tree(child, ordinal, child_path))
    return CourseXmlNode(
        tag=str(element.tag),
        ordinal=node_ordinal,
        xml_path=path,
        attributes=_attributes(element),
        text=(element.text or "").strip(),
        children=tuple(children),
    )


def _vector3(value: str, source: str, field_name: str) -> tuple[float, float, float]:
    parts = value.split()
    if len(parts) != 3 or not all(FLOAT_RE.fullmatch(part) for part in parts):
        raise FormatError(f"invalid Vector3 {field_name!r} in {source}: {value!r}")
    result = tuple(float(part) for part in parts)
    if not all(math.isfinite(part) for part in result):
        raise FormatError(f"non-finite Vector3 {field_name!r} in {source}: {value!r}")
    return result  # type: ignore[return-value]


def _values(element: ET.Element) -> tuple[CourseXmlValue, ...]:
    return tuple(
        CourseXmlValue(
            name=child.attrib.get("Name", ""),
            type_name=child.attrib.get("Type", ""),
            value=child.attrib.get("Value", ""),
            attributes=_attributes(child),
        )
        for child in list(element)
        if str(child.tag) == "Value"
    )


def _matrix(element: ET.Element, source: str, egg_name: str) -> CourseXmlMatrix:
    rows: list[tuple[float, float, float, float] | None] = []
    issues: list[str] = []
    for index in range(4):
        raw = element.attrib.get(f"Row{index}")
        if raw is None:
            rows.append(None)
            continue
        parts = raw.split()
        try:
            if len(parts) != 4 or not all(FLOAT_RE.fullmatch(part) for part in parts):
                raise ValueError("expected four float components")
            values = tuple(float(part) for part in parts)
            if not all(math.isfinite(value) for value in values):
                raise ValueError("non-finite matrix component")
            rows.append(values)  # type: ignore[arg-type]
        except ValueError as error:
            rows.append(None)
            issues.append(f"{egg_name} {element.attrib.get('Name', 'Matrix')} Row{index}: {error} ({raw!r})")
    return CourseXmlMatrix(
        name=element.attrib.get("Name", ""),
        type_name=element.attrib.get("Type", ""),
        attributes=_attributes(element),
        rows=tuple(rows),
        issues=tuple(issues),
    )


def _marker(
    element: ET.Element,
    ordinal: int,
    list_name: str | None,
    list_ordinal: int | None,
    list_index: int,
    xml_path: str,
    source: str,
    record_ordinal: int,
) -> tuple[CourseXmlMarker, CourseXmlRecord]:
    values = _values(element)
    record = CourseXmlRecord(
        tag=str(element.tag),
        ordinal=record_ordinal,
        attributes=_attributes(element),
        values=values,
        xml_path=xml_path,
        marker_list_name=list_name,
    )
    value_map = {item.name: item for item in values}
    marker_type = value_map.get("Marker Type")
    position_value = value_map.get("Marker Pos")
    direction_value = value_map.get("Marker Dir")
    issues: list[str] = []
    position = direction = None
    if position_value is None:
        issues.append("Marker Pos value missing")
    elif position_value.type_name != "Vector3":
        issues.append(f"Marker Pos type is {position_value.type_name!r}, not 'Vector3'")
    else:
        try:
            position = _vector3(position_value.value, source, "Marker Pos")
        except FormatError as error:
            issues.append(str(error))
    if direction_value is None:
        issues.append("Marker Dir value missing")
    elif direction_value.type_name != "Vector3":
        issues.append(f"Marker Dir type is {direction_value.type_name!r}, not 'Vector3'")
    else:
        try:
            direction = _vector3(direction_value.value, source, "Marker Dir")
        except FormatError as error:
            issues.append(str(error))
    return (
        CourseXmlMarker(
            ordinal=ordinal,
            marker_no=dict(record.attributes).get("No"),
            marker_type=marker_type.value if marker_type else None,
            position=position,
            direction=direction,
            raw_position=position_value.value if position_value else None,
            raw_direction=direction_value.value if direction_value else None,
            record=record,
            issues=tuple(issues),
            marker_list_name=list_name,
            marker_list_ordinal=list_ordinal,
            index_in_list=list_index,
        ),
        record,
    )


def _egg(
    element: ET.Element,
    ordinal: int,
    list_name: str | None,
    list_ordinal: int | None,
    index: int,
    xml_path: str,
    source: str,
) -> CourseXmlEgg:
    name = element.attrib.get("Name")
    matrices = tuple(
        _matrix(child, source, name or f"Egg {ordinal}")
        for child in element.iter("Value")
        if child.attrib.get("Type") == "Matrix"
    )
    direct_values = _values(element)
    model = next(
        (item.value for item in direct_values if item.name in {"en3d Model Name", "Model Name", "Model"}),
        None,
    )
    ai_objects: list[CourseXmlAiObject] = []
    for ai_ordinal, ai in enumerate(element.iter("AI")):
        ai_values = _values(ai)
        ai_name_value = next((item for item in ai_values if item.name == "AI Name"), None)
        ai_name = ai_name_value.value if ai_name_value else None
        components = []
        for component_index, component in enumerate(list(ai)):
            if str(component.tag) == "Value":
                continue
            component_path = f"{xml_path}/AI[@No={ai.attrib.get('No', str(ai_ordinal))!r}]/{component.tag}[{component_index}]"
            components.append(CourseXmlAiComponent(
                tag=str(component.tag),
                ai_no=ai.attrib.get("No"),
                ai_name=ai_name,
                attributes=_attributes(component),
                values=_values(component),
                xml_path=component_path,
            ))
        ai_objects.append(CourseXmlAiObject(
            ordinal=ai_ordinal,
            ai_no=ai.attrib.get("No"),
            ai_name=ai_name,
            attributes=_attributes(ai),
            values=ai_values,
            components=tuple(components),
            xml_path=f"{xml_path}/AI[@No={ai.attrib.get('No', str(ai_ordinal))!r}]",
        ))
    return CourseXmlEgg(
        ordinal=ordinal,
        list_name=list_name,
        list_ordinal=list_ordinal,
        index_in_list=index,
        name=name,
        attributes=_attributes(element),
        values=direct_values,
        model_name=model,
        matrices=matrices,
        ai_objects=tuple(ai_objects),
        xml_path=xml_path,
    )


def parse_course_xml_bytes(data: bytes, source: str = "<bytes>") -> CourseXmlDocument:
    """Parse RaceTest XML without assigning unobserved gameplay meanings.

    The complete element hierarchy, ordering, and attributes are retained in
    ``root``. Typed projections expose MarkerLists, Egg lists, matrix rows, and
    AI component values while preserving the older flat ``markers`` view.
    """
    try:
        root_element = ET.fromstring(data)
    except ET.ParseError as error:
        raise FormatError(f"invalid course XML in {source}: {error}") from error

    root = _build_tree(root_element, [0], f"/{root_element.tag}")
    records: list[CourseXmlRecord] = []
    markers: list[CourseXmlMarker] = []
    marker_lists: list[CourseXmlMarkerList] = []
    eggs: list[CourseXmlEgg] = []
    marker_list_container = next((item for item in list(root_element) if str(item.tag) == "MarkerLists"), None)
    marker_list_ordinals = {
        id(child): index for index, child in enumerate(list(marker_list_container))
    } if marker_list_container is not None else {}

    record_ordinal = 0
    marker_ordinal = 0

    def collect_records(
        element: ET.Element,
        path: str,
        marker_list_name: str | None = None,
        marker_list_ordinal: int | None = None,
        egg_list_name: str | None = None,
        egg_name: str | None = None,
        ai_no: str | None = None,
        inside_marker_lists: bool = False,
        inside_egg_lists: bool = False,
    ) -> None:
        nonlocal record_ordinal, marker_ordinal
        tag = str(element.tag)
        attrs = element.attrib
        inside_marker_lists = inside_marker_lists or tag == "MarkerLists"
        inside_egg_lists = inside_egg_lists or tag == "EggLists_Version4"
        if tag == "List" and inside_marker_lists:
            marker_list_name = attrs.get("Name")
            marker_list_ordinal = marker_list_ordinals.get(id(element))
        if tag == "List" and inside_egg_lists:
            egg_list_name = attrs.get("Name")
        if tag == "Egg":
            egg_name = attrs.get("Name")
        if tag == "AI":
            ai_no = attrs.get("No")

        if tag in RECORD_TAGS:
            values = _values(element)
            record = CourseXmlRecord(
                tag=tag,
                ordinal=record_ordinal,
                attributes=_attributes(element),
                values=values,
                xml_path=path,
                marker_list_name=marker_list_name if inside_marker_lists else None,
                egg_list_name=egg_list_name if inside_egg_lists else None,
                egg_name=egg_name if inside_egg_lists else None,
                ai_no=ai_no if inside_egg_lists else None,
            )
            records.append(record)
            if tag == "Marker":
                list_index = (
                    sum(1 for item in markers if item.marker_list_ordinal == marker_list_ordinal)
                    if marker_list_ordinal is not None else 0
                )
                marker, marker_record = _marker(
                    element, marker_ordinal, marker_list_name if inside_marker_lists else None,
                    marker_list_ordinal if inside_marker_lists else None, list_index, path, source, record_ordinal,
                )
                # Use the same enriched record object for both projections.
                marker = CourseXmlMarker(**{**marker.__dict__, "record": record})
                markers.append(marker)
                marker_ordinal += 1
            record_ordinal += 1

        same_tag_seen: dict[str, int] = {}
        for child in list(element):
            child_tag = str(child.tag)
            child_index = same_tag_seen.get(child_tag, 0)
            same_tag_seen[child_tag] = child_index + 1
            collect_records(child, f"{path}/{_element_label(child, child_index)}", marker_list_name,
                            marker_list_ordinal,
                            egg_list_name, egg_name, ai_no, inside_marker_lists, inside_egg_lists)

    collect_records(root_element, f"/{root_element.tag}")

    marker_container = next((child for child in list(root_element) if str(child.tag) == "MarkerLists"), None)
    if marker_container is not None:
        seen: dict[str, int] = {}
        for list_ordinal, marker_list in enumerate(list(marker_container)):
            tag = str(marker_list.tag)
            same_index = seen.get(tag, 0)
            seen[tag] = same_index + 1
            list_name = marker_list.attrib.get("Name")
            path = f"/{root_element.tag}/MarkerLists/{_element_label(marker_list, same_index)}"
            list_markers = tuple(item for item in markers if item.marker_list_ordinal == list_ordinal)
            marker_lists.append(CourseXmlMarkerList(
                ordinal=list_ordinal,
                name=list_name,
                attributes=_attributes(marker_list),
                markers=list_markers,
                xml_path=path,
            ))

    egg_container = next((child for child in list(root_element) if str(child.tag) == "EggLists_Version4"), None)
    if egg_container is not None:
        egg_ordinal = 0
        list_seen: dict[str, int] = {}
        for list_ordinal, egg_list in enumerate(list(egg_container)):
            tag = str(egg_list.tag)
            same_index = list_seen.get(tag, 0)
            list_seen[tag] = same_index + 1
            list_name = egg_list.attrib.get("Name")
            list_path = f"/{root_element.tag}/EggLists_Version4/{_element_label(egg_list, same_index)}"
            egg_index = 0
            egg_seen: dict[str, int] = {}
            for element in egg_list.iter("Egg"):
                # Only consider each nested Egg once; this remains safe if an
                # Egg contains another Egg in an unusual future file.
                egg_tag_index = egg_seen.get("Egg", 0)
                egg_seen["Egg"] = egg_tag_index + 1
                egg_path = f"{list_path}/{_element_label(element, egg_tag_index)}"
                eggs.append(_egg(element, egg_ordinal, list_name, list_ordinal, egg_index, egg_path, source))
                egg_ordinal += 1
                egg_index += 1

    return CourseXmlDocument(
        source=str(source), root_tag=str(root_element.tag), records=tuple(records),
        markers=tuple(markers), root=root, marker_lists=tuple(marker_lists), eggs=tuple(eggs),
    )


def parse_course_xml(path: Path) -> CourseXmlDocument:
    resolved = path.resolve()
    return parse_course_xml_bytes(resolved.read_bytes(), resolved.name)
