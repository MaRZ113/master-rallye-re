"""Read-only extraction of explicitly stored RaceTest XML course records."""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .errors import FormatError


FLOAT_RE = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
)
RECORD_TAGS = {"Marker", "gaRaceSplitTimeAI", "gaRacePostFirstSplitTimeAI", "gaLimitBuilderAI"}


@dataclass(frozen=True)
class CourseXmlValue:
    name: str
    type_name: str
    value: str


@dataclass(frozen=True)
class CourseXmlRecord:
    tag: str
    ordinal: int
    attributes: tuple[tuple[str, str], ...]
    values: tuple[CourseXmlValue, ...]

    def value(self, name: str) -> CourseXmlValue | None:
        return next((item for item in self.values if item.name == name), None)


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


@dataclass(frozen=True)
class CourseXmlDocument:
    source: str
    root_tag: str
    records: tuple[CourseXmlRecord, ...]
    markers: tuple[CourseXmlMarker, ...]

    @property
    def split_time_records(self) -> tuple[CourseXmlRecord, ...]:
        return tuple(item for item in self.records if item.tag == "gaRaceSplitTimeAI")

    @property
    def limit_builder_records(self) -> tuple[CourseXmlRecord, ...]:
        return tuple(item for item in self.records if item.tag == "gaLimitBuilderAI")


def _vector3(value: str, source: str, field_name: str) -> tuple[float, float, float]:
    parts = value.split()
    if len(parts) != 3 or not all(FLOAT_RE.fullmatch(part) for part in parts):
        raise FormatError(f"invalid Vector3 {field_name!r} in {source}: {value!r}")
    result = tuple(float(part) for part in parts)
    if not all(math.isfinite(part) for part in result):
        raise FormatError(f"non-finite Vector3 {field_name!r} in {source}: {value!r}")
    return result  # type: ignore[return-value]


def parse_course_xml_bytes(data: bytes, source: str = "<bytes>") -> CourseXmlDocument:
    """Retain named XML values and parse only explicit marker Vector3 fields.

    Names such as ``Marker``, ``gaRaceSplitTimeAI`` and ``gaLimitBuilderAI``
    are recorded as XML identifiers. This parser does not assign gameplay
    semantics to those records.
    """
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise FormatError(f"invalid course XML in {source}: {error}") from error

    records: list[CourseXmlRecord] = []
    markers: list[CourseXmlMarker] = []
    marker_ordinal = 0
    for element in root.iter():
        tag = str(element.tag)
        if tag not in RECORD_TAGS:
            continue
        values = tuple(
            CourseXmlValue(
                name=child.attrib.get("Name", ""),
                type_name=child.attrib.get("Type", ""),
                value=child.attrib.get("Value", ""),
            )
            for child in list(element)
            if str(child.tag) == "Value"
        )
        record = CourseXmlRecord(
            tag=tag,
            ordinal=len(records),
            attributes=tuple(sorted((str(key), str(value)) for key, value in element.attrib.items())),
            values=values,
        )
        records.append(record)
        if tag != "Marker":
            continue

        marker_type = record.value("Marker Type")
        position_value = record.value("Marker Pos")
        direction_value = record.value("Marker Dir")
        issues: list[str] = []
        position = None
        direction = None
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

        marker_no = dict(record.attributes).get("No")
        markers.append(CourseXmlMarker(
            ordinal=marker_ordinal,
            marker_no=marker_no,
            marker_type=marker_type.value if marker_type else None,
            position=position,
            direction=direction,
            raw_position=position_value.value if position_value else None,
            raw_direction=direction_value.value if direction_value else None,
            record=record,
            issues=tuple(issues),
        ))
        marker_ordinal += 1

    return CourseXmlDocument(str(source), str(root.tag), tuple(records), tuple(markers))


def parse_course_xml(path: Path) -> CourseXmlDocument:
    resolved = path.resolve()
    return parse_course_xml_bytes(resolved.read_bytes(), resolved.name)
