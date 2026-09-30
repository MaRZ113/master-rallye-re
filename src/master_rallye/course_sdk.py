"""Read-only semantic Course SDK layered over the forensic format parsers.

This module composes existing resource readers. It does not write game data or
assign semantics to unresolved course structures.
"""
from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Iterable

from .course_gxm import CourseGxmModelV7, CourseGxmNode, CourseGxmPrefix, parse_course_gxm, parse_course_gxm_model_v7
from .course_source import CourseTxtDocument, parse_course_txt
from .course_xml import (
    CourseXmlAiComponent,
    CourseXmlDocument,
    CourseXmlEgg,
    CourseXmlMarker,
    CourseXmlMarkerList,
    parse_course_xml,
)
from .dx_course import CourseDxModel, parse_course_dx
from .hnt import HntDocument, parse_hnt, resolve_hnt_entries
from .sfl import SflField, parse_sfl


CONFIRMED_BY_RUNTIME_EDIT = "CONFIRMED_BY_RUNTIME_EDIT"
CONFIRMED_BY_EXECUTABLE = "CONFIRMED_BY_EXECUTABLE"
SUPPORTED_BY_SHARED_STRUCTURE = "SUPPORTED_BY_SHARED_STRUCTURE"
UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CourseMarkerArea:
    """Ordered source markers interpreted as one known course race-logic area."""

    source_list: CourseXmlMarkerList
    markers: tuple[CourseXmlMarker, ...]
    semantic_role: str
    semantic_rule_evidence: tuple[str, ...]
    record_evidence: tuple[str, ...] = ()

    @property
    def source_list_name(self) -> str | None:
        return self.source_list.name

    @property
    def source_xml_path(self) -> str:
        return self.source_list.xml_path

    @property
    def positions(self) -> tuple[tuple[float, float, float] | None, ...]:
        return tuple(marker.position for marker in self.markers)

    @property
    def directions(self) -> tuple[tuple[float, float, float] | None, ...]:
        return tuple(marker.direction for marker in self.markers)

    @property
    def centroid(self) -> tuple[float, float, float] | None:
        positions = self.positions
        if not positions or any(position is None for position in positions):
            return None
        valid = tuple(position for position in positions if position is not None)
        return tuple(mean(point[axis] for point in valid) for axis in range(3))  # type: ignore[return-value]

    @property
    def local_xz_bounds(self) -> tuple[float, float, float, float] | None:
        positions = self.positions
        if not positions or any(position is None for position in positions):
            return None
        valid = tuple(position for position in positions if position is not None)
        xs = tuple(point[0] for point in valid)
        zs = tuple(point[2] for point in valid)
        return min(xs), max(xs), min(zs), max(zs)


@dataclass(frozen=True)
class CourseStartArea(CourseMarkerArea):
    """StartArea frame; it does not contain inferred per-car slots."""


@dataclass(frozen=True)
class CourseFinishArea(CourseMarkerArea):
    """FinishArea contribution to race completion; not claimed exclusive."""


@dataclass(frozen=True)
class CourseVisualCheckpoint:
    source_egg: CourseXmlEgg
    position: tuple[float, float, float] | None
    semantic_rule_evidence: tuple[str, ...]
    record_evidence: tuple[str, ...] = ()

    @property
    def name(self) -> str | None:
        return self.source_egg.name

    @property
    def model_name(self) -> str | None:
        return self.source_egg.model_name

    @property
    def xml_path(self) -> str:
        return self.source_egg.xml_path


@dataclass(frozen=True)
class CourseSplitTime:
    split_id: int | None
    split_id_raw: str | None
    center: tuple[float, float, float] | None
    radius: float | None
    radius_raw: str | None
    extra_time: float | None
    extra_time_raw: str | None
    extra_time_semantics: str
    trigger_shape: str
    source_egg: CourseXmlEgg
    source_component: CourseXmlAiComponent
    companions: tuple[CourseVisualCheckpoint, ...]
    center_rule_evidence: tuple[str, ...]
    radius_rule_evidence: tuple[str, ...]
    companions_rule_evidence: tuple[str, ...]
    record_evidence: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()

    @property
    def egg_name(self) -> str | None:
        return self.source_egg.name

    @property
    def egg_xml_path(self) -> str:
        return self.source_egg.xml_path

    @property
    def egg_matrix(self):
        return self.source_egg.matrix("en3d Matrix")

    @property
    def trigger_complete(self) -> bool:
        return self.split_id is not None and self.center is not None and self.radius is not None and self.radius >= 0.0


@dataclass(frozen=True)
class CourseRaceLogic:
    source_document: CourseXmlDocument
    start_area: CourseStartArea | None
    finish_area: CourseFinishArea | None
    split_times: tuple[CourseSplitTime, ...]
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class CourseTag100Region:
    """Neutral public description of the course trailing tag-100 region."""

    present: bool
    tag_offset: int | None
    end_offset: int | None
    byte_size: int
    sha256: str | None
    boundary_status: str
    semantics: str = UNKNOWN


@dataclass(frozen=True)
class CourseRenderDraw:
    draw_index: int | None
    group_index: int | None
    record_path: str
    tag: int
    source_offset: int
    byte_size: int
    vertex_base: int
    local_vertex_max: int
    index_start: int
    index_count: int
    texture_slots: tuple[str, ...]


@dataclass(frozen=True)
class CourseRenderGroup:
    group_index: int
    root_record_path: str
    draw_indices: tuple[int, ...]


@dataclass(frozen=True)
class CourseRenderResource:
    """Public course render view with tag100 separated from collision naming."""

    source: str
    revision: int
    vertex_count: int
    triangle_count: int
    draw_count: int
    positions: tuple[tuple[float, float, float], ...]
    normals: tuple[tuple[float, float, float], ...]
    colors: bytes
    uv_sets: tuple[object, ...]
    local_indices: tuple[int, ...]
    draw_groups: tuple[CourseRenderGroup, ...]
    draw_records: tuple[CourseRenderDraw, ...]
    tag100: CourseTag100Region
    validation_passed: bool
    validation_errors: tuple[str, ...]
    validation_warnings: tuple[str, ...]
    _parsed_model: CourseDxModel = field(repr=False, compare=False)


@dataclass(frozen=True)
class CourseDependency:
    keyword: str
    referenced_value: str
    raw_line: str
    line_number: int
    status: str
    resolved_relative_path: str | None
    ambiguity_candidates: tuple[str, ...]


@dataclass(frozen=True)
class CourseDependencies:
    source: Path | None
    entries: tuple[CourseDependency, ...]
    unparsed_lines: tuple[tuple[int, str], ...] = ()


@dataclass(frozen=True)
class CourseSpatialField:
    source: str
    width: int
    height: int
    header: object
    payload_offset: int
    payload_size: int
    value_min: int | None
    value_max: int | None
    distinct_value_count: int
    value_counts: tuple[tuple[int, int], ...]
    _parsed_field: SflField = field(repr=False, compare=False)
    semantics: str = UNKNOWN


@dataclass(frozen=True)
class CourseSourceMesh:
    """Read-only source moMesh triangle span; name semantics remain unassigned."""

    literal_name: str
    hierarchy_path: tuple[str, ...]
    source_ordinal: int
    source_index: int
    source_size: int
    triangle_start: int
    triangle_count: int
    position_indices: tuple[int, ...]
    unique_position_indices: tuple[int, ...]
    bounds: tuple[tuple[float, float, float], tuple[float, float, float]] | None
    source_evidence: tuple[str, ...]
    gameplay_role: str = UNKNOWN


@dataclass(frozen=True)
class CourseResourcePaths:
    identity: str
    search_roots: tuple[Path, ...]
    render_dx: Path | None
    race_test_xml: Path | None
    hnt: Path | None
    sfl: Path | None
    source_txt: Path | None
    source_gxm: Path | None
    candidates: tuple[tuple[str, tuple[Path, ...]], ...]
    diagnostics: tuple[str, ...] = ()

    def candidate_paths(self, kind: str) -> tuple[Path, ...]:
        return next((paths for name, paths in self.candidates if name == kind), ())


@dataclass(frozen=True)
class CourseProject:
    """Partial, read-only composition of available course resources."""

    identity: str
    source_context: Path | None
    resources: CourseResourcePaths
    render: CourseRenderResource | None = None
    race_logic: CourseRaceLogic | None = None
    dependencies: CourseDependencies | None = None
    sfl: CourseSpatialField | None = None
    source_txt: CourseTxtDocument | None = None
    source_gxm: CourseGxmPrefix | None = None
    source_geometry: CourseGxmModelV7 | None = None
    source_meshes: tuple[CourseSourceMesh, ...] = ()
    diagnostics: tuple[str, ...] = ()


_RESOURCE_SUFFIXES = {
    "render_dx": ".dx",
    "race_test_xml": ".xml",
    "hnt": ".hnt",
    "sfl": ".sfl",
    "source_txt": ".txt",
    "source_gxm": ".gxm",
}
_IGNORED_DIRS = {".git", "__pycache__", ".research-output", "cache", "temp"}


def _iter_files(root: Path) -> tuple[Path, ...]:
    found: list[Path] = []
    for directory, names, filenames in os.walk(root):
        names[:] = sorted((name for name in names if name.casefold() not in _IGNORED_DIRS), key=str.casefold)
        for filename in filenames:
            if Path(filename).suffix.casefold() in set(_RESOURCE_SUFFIXES.values()):
                found.append(Path(directory) / filename)
    return tuple(sorted(found, key=lambda item: item.as_posix().casefold()))


def _find_data_gx_root(selected_dx: Path | None, roots: tuple[Path, ...]) -> Path | None:
    if selected_dx is not None:
        for candidate in selected_dx.resolve().parents:
            if candidate.name.casefold() == "datagx":
                return candidate
    for root in roots:
        candidates = (root, *tuple(root.parents)[:3])
        for candidate in candidates:
            if candidate.name.casefold() == "datagx":
                return candidate
            if candidate.is_dir():
                try:
                    child = next((item for item in candidate.iterdir()
                                  if item.is_dir() and item.name.casefold() == "datagx"), None)
                except OSError:
                    child = None
                if child is not None:
                    return child
    return None


def _hnts_linking_dx(files: tuple[Path, ...], selected_dx: Path, data_gx_root: Path | None) -> tuple[Path, ...]:
    """Return HNTs whose exact Model path resolves to the selected DX."""
    if data_gx_root is None:
        return ()
    try:
        selected_relative = selected_dx.resolve().relative_to(data_gx_root.resolve()).as_posix().casefold()
    except ValueError:
        return ()
    linked: set[Path] = set()
    for hnt_path in files:
        if hnt_path.suffix.casefold() != ".hnt":
            continue
        try:
            document = parse_hnt(hnt_path)
        except (OSError, UnicodeError):
            continue
        for entry in document.entries_of("Model"):
            reference = entry.value.replace("\\", "/").strip("/")
            parts = reference.split("/")
            if not reference or any(part in {".", ".."} for part in parts):
                continue
            if not Path(parts[-1]).suffix:
                reference += ".dx"
            if reference.casefold() == selected_relative:
                linked.add(hnt_path)
                break
    return tuple(sorted(linked, key=lambda item: item.as_posix().casefold()))


def discover_course_resources(
    path: Path,
    *,
    search_roots: Iterable[Path] = (),
) -> CourseResourcePaths:
    """Find exact-stem package resources; preserve ambiguity instead of guessing.

    A file argument pins that resource. Directory scans are limited to the
    provided directory and explicitly supplied search roots.
    """
    supplied = Path(path).expanduser().resolve()
    if not supplied.exists():
        raise FileNotFoundError(supplied)
    is_file = supplied.is_file()
    root = supplied.parent if is_file else supplied
    roots: list[Path] = []
    for candidate in (root, *tuple(Path(item).expanduser().resolve() for item in search_roots)):
        if candidate.is_dir() and candidate not in roots:
            roots.append(candidate)
    files = tuple(sorted({item for search_root in roots for item in _iter_files(search_root)},
                         key=lambda item: item.as_posix().casefold()))

    forced: dict[str, Path] = {}
    if is_file:
        suffix = supplied.suffix.casefold()
        for kind, expected_suffix in _RESOURCE_SUFFIXES.items():
            if suffix == expected_suffix:
                forced[kind] = supplied
                break

    if is_file and supplied.suffix.casefold() == ".dx":
        stem = supplied.stem
        parent = supplied.parent.name
        identity = stem if parent.casefold().endswith(stem.casefold()) else parent
    elif is_file:
        identity = supplied.stem
    else:
        identity = supplied.name
    identity_keys = {identity.casefold()}
    if "render_dx" in forced:
        identity_keys.add(supplied.stem.casefold())

    candidate_map: dict[str, tuple[Path, ...]] = {}
    selected: dict[str, Path | None] = {}
    diagnostics: list[str] = []
    for kind, suffix in _RESOURCE_SUFFIXES.items():
        if kind in forced:
            matches = (forced[kind],)
            selected[kind] = forced[kind]
        else:
            matches = tuple(
                item for item in files
                if item.suffix.casefold() == suffix and item.stem.casefold() in identity_keys
            )
            selected[kind] = matches[0] if len(matches) == 1 else None
            if len(matches) > 1:
                diagnostics.append(f"ambiguous {kind}: " + ", ".join(str(item) for item in matches))
        candidate_map[kind] = matches

    # A package directory may contain one main model whose filename is a
    # source-side name such as track01. Accept it only when selection is unique.
    if "render_dx" not in forced and selected["render_dx"] is None and not candidate_map["render_dx"]:
        dx_files = tuple(item for item in files if item.suffix.casefold() == ".dx")
        candidate_map["render_dx"] = dx_files
        explicit_course_directory = (not is_file) or any(
            search_root.name.casefold() in identity_keys for search_root in roots
        )
        if len(dx_files) == 1 and explicit_course_directory:
            selected["render_dx"] = dx_files[0]
        elif len(dx_files) > 1:
            diagnostics.append("ambiguous render_dx: " + ", ".join(str(item) for item in dx_files))
        elif len(dx_files) == 1:
            diagnostics.append(
                f"render_dx not selected: {dx_files[0]} is the only candidate but no course-folder or exact-stem relation identifies it"
            )

    # HNT Model paths provide an exact relationship when the course folder,
    # model, and RaceTest names differ (for example Italy_M1 / italy_m1 /
    # italyM1). Never fall back to a fuzzy basename match.
    association_stem = None
    selected_dx = selected["render_dx"]
    if selected_dx is not None and "hnt" not in forced:
        linked_hnts = _hnts_linking_dx(files, selected_dx, _find_data_gx_root(selected_dx, tuple(roots)))
        if len(linked_hnts) == 1:
            selected["hnt"] = linked_hnts[0]
            candidate_map["hnt"] = linked_hnts
            association_stem = linked_hnts[0].stem.casefold()
        elif len(linked_hnts) > 1:
            selected["hnt"] = None
            candidate_map["hnt"] = linked_hnts
            diagnostics.append("ambiguous HNT Model links for selected DX: "
                               + ", ".join(str(item) for item in linked_hnts))

    if association_stem is not None:
        for kind in ("race_test_xml", "sfl"):
            if kind in forced:
                continue
            matches = tuple(
                item for item in files
                if item.suffix.casefold() == _RESOURCE_SUFFIXES[kind]
                and item.stem.casefold() == association_stem
            )
            candidate_map[kind] = matches
            selected[kind] = matches[0] if len(matches) == 1 else None
            if len(matches) > 1:
                diagnostics.append(f"ambiguous {kind} for HNT Model link {linked_hnts[0].name}: "
                                   + ", ".join(str(item) for item in matches))

    # TXT/GXM sidecars are sometimes named after the model rather than the
    # course folder (for example Italy1/track01.dx + track01.txt). Once the
    # model is selected unambiguously, its exact stem is a safe additional key.
    selected_dx = selected["render_dx"]
    if selected_dx is not None:
        model_stem = selected_dx.stem.casefold()
        for kind in ("source_txt", "source_gxm"):
            if kind in forced or candidate_map[kind]:
                continue
            matches = tuple(
                item for item in files
                if item.suffix.casefold() == _RESOURCE_SUFFIXES[kind]
                and item.stem.casefold() == model_stem
            )
            candidate_map[kind] = matches
            if len(matches) == 1:
                selected[kind] = matches[0]
            elif len(matches) > 1:
                diagnostics.append(f"ambiguous {kind} for selected model stem {selected_dx.stem}: "
                                   + ", ".join(str(item) for item in matches))

    resource_candidates = tuple((kind, candidate_map[kind]) for kind in _RESOURCE_SUFFIXES)
    return CourseResourcePaths(
        identity=identity,
        search_roots=tuple(roots),
        render_dx=selected["render_dx"],
        race_test_xml=selected["race_test_xml"],
        hnt=selected["hnt"],
        sfl=selected["sfl"],
        source_txt=selected["source_txt"],
        source_gxm=selected["source_gxm"],
        candidates=resource_candidates,
        diagnostics=tuple(diagnostics),
    )


def _number(raw: str | None, field_name: str, issues: list[str]) -> float | None:
    if raw is None:
        issues.append(f"{field_name} missing")
        return None
    try:
        value = float(raw.strip())
    except (TypeError, ValueError):
        issues.append(f"{field_name} is not numeric: {raw!r}")
        return None
    if not math.isfinite(value):
        issues.append(f"{field_name} is not finite: {raw!r}")
        return None
    return value


def _split_id(raw: str | None, issues: list[str]) -> int | None:
    if raw is None:
        issues.append("Split Time ID missing")
        return None
    try:
        value = float(raw.strip())
    except ValueError:
        issues.append(f"Split Time ID is not numeric: {raw!r}")
        return None
    if not math.isfinite(value) or not value.is_integer():
        issues.append(f"Split Time ID is not a finite integer: {raw!r}")
        return None
    return int(value)


def _matrix_position(egg: CourseXmlEgg, issues: list[str]) -> tuple[float, float, float] | None:
    matrix = egg.matrix("en3d Matrix")
    if matrix is None:
        issues.append("en3d Matrix missing")
        return None
    if matrix.position is None:
        issues.append("en3d Matrix Row3 missing or invalid")
        return None
    return matrix.position


def _exact_visual_companions(
    document: CourseXmlDocument,
    egg: CourseXmlEgg,
) -> tuple[CourseVisualCheckpoint, ...]:
    if not egg.name:
        return ()
    pattern = re.compile(re.escape(egg.name) + r"-(\d+)$", re.IGNORECASE)
    companions = []
    for candidate in document.eggs:
        if candidate.ordinal == egg.ordinal or candidate.list_ordinal != egg.list_ordinal:
            continue
        if not candidate.name or not pattern.fullmatch(candidate.name):
            continue
        position = candidate.matrix("en3d Matrix")
        companions.append(CourseVisualCheckpoint(
            source_egg=candidate,
            position=position.position if position is not None else None,
            semantic_rule_evidence=(SUPPORTED_BY_SHARED_STRUCTURE,),
        ))
    return tuple(companions)


def build_course_race_logic(
    document: CourseXmlDocument,
) -> CourseRaceLogic:
    """Interpret proven RaceTest fields while preserving their raw XML nodes."""
    diagnostics: list[str] = []

    def area(name: str, cls, role: str, evidence: tuple[str, ...]):
        matches = tuple(item for item in document.marker_lists if item.name == name)
        if len(matches) > 1:
            diagnostics.append(f"multiple MarkerLists named {name}; semantic area is ambiguous")
            return None
        if not matches:
            return None
        marker_list = matches[0]
        return cls(marker_list, marker_list.markers, role, evidence)

    start_area = area(
        "StartArea", CourseStartArea,
        "geometric frame used for physical start-grid placement and heading",
        (CONFIRMED_BY_RUNTIME_EDIT,),
    )
    finish_area = area(
        "FinishArea", CourseFinishArea,
        "contributes to race-completion trigger region; not asserted exclusive",
        (CONFIRMED_BY_RUNTIME_EDIT,),
    )

    splits: list[CourseSplitTime] = []
    for egg in document.split_time_eggs:
        component = egg.split_time_component
        if component is None:
            continue
        values = {item.name: item for item in component.values}
        issues: list[str] = []
        split_id_raw = values.get("Split Time ID").value if values.get("Split Time ID") else None
        radius_raw = values.get("Radius").value if values.get("Radius") else None
        extra_time_raw = values.get("ExtraTime").value if values.get("ExtraTime") else None
        split_id = _split_id(split_id_raw, issues)
        radius = _number(radius_raw, "Radius", issues)
        extra_time = _number(extra_time_raw, "ExtraTime", issues)
        center = _matrix_position(egg, issues)
        companions = _exact_visual_companions(document, egg)
        splits.append(CourseSplitTime(
            split_id=split_id,
            split_id_raw=split_id_raw,
            center=center,
            radius=radius,
            radius_raw=radius_raw,
            extra_time=extra_time,
            extra_time_raw=extra_time_raw,
            extra_time_semantics=UNKNOWN,
            trigger_shape="sphere",
            source_egg=egg,
            source_component=component,
            companions=companions,
            center_rule_evidence=(CONFIRMED_BY_EXECUTABLE, SUPPORTED_BY_SHARED_STRUCTURE),
            radius_rule_evidence=(CONFIRMED_BY_EXECUTABLE, SUPPORTED_BY_SHARED_STRUCTURE),
            companions_rule_evidence=(SUPPORTED_BY_SHARED_STRUCTURE,),
            record_evidence=(),
            issues=tuple(issues),
        ))

    return CourseRaceLogic(
        source_document=document,
        start_area=start_area,
        finish_area=finish_area,
        split_times=tuple(splits),
        diagnostics=tuple(diagnostics),
    )


def _render_resource(model: CourseDxModel) -> CourseRenderResource:
    section = model.collision.bsp
    tag100 = CourseTag100Region(
        present=section is not None,
        tag_offset=section.tag_offset if section else None,
        end_offset=section.end_offset if section else None,
        byte_size=len(section.raw) if section else 0,
        sha256=section.sha256 if section else None,
        boundary_status=section.status if section else "not-present",
    )
    records = tuple(CourseRenderDraw(
        draw_index=item.draw_index,
        group_index=item.top_level_index,
        record_path=item.record_path,
        tag=item.tag,
        source_offset=item.offset,
        byte_size=item.size,
        vertex_base=item.vertex_base,
        local_vertex_max=item.local_vertex_max,
        index_start=item.index_start,
        index_count=item.index_count,
        texture_slots=item.texture_tuple,
    ) for item in model.physical_draws)
    groups = tuple(CourseRenderGroup(
        group_index=group.top_level_index,
        root_record_path=group.root.record_path,
        draw_indices=tuple(group.draw_indices),
    ) for group in model.draw_groups)
    return CourseRenderResource(
        source=model.source,
        revision=model.word_0x04,
        vertex_count=model.vertex_count,
        triangle_count=model.triangle_count,
        draw_count=len(model.physical_draws),
        positions=model.vertices.positions,
        normals=model.vertices.normals,
        colors=model.vertices.colors,
        uv_sets=tuple(model.uv_sets),
        local_indices=model.local_indices,
        draw_groups=groups,
        draw_records=records,
        tag100=tag100,
        validation_passed=model.course_render_validated,
        validation_errors=tuple(model.diagnostics.errors),
        validation_warnings=tuple(model.diagnostics.warnings),
        _parsed_model=model,
    )


def _course_dependencies(document: HntDocument, path: Path, data_gx_root: Path) -> CourseDependencies:
    resolutions = resolve_hnt_entries(document, data_gx_root)
    return CourseDependencies(
        source=path,
        entries=tuple(CourseDependency(
            keyword=item.entry.keyword,
            referenced_value=item.entry.value,
            raw_line=item.entry.raw_line,
            line_number=item.entry.line_number,
            status=item.status,
            resolved_relative_path=item.resolved_path,
            ambiguity_candidates=item.candidates,
        ) for item in resolutions),
        unparsed_lines=document.unparsed_lines,
    )


def _data_gx_root(resources: CourseResourcePaths) -> Path:
    found = _find_data_gx_root(resources.render_dx, resources.search_roots)
    if found is not None:
        return found
    return resources.search_roots[0] if resources.search_roots else Path.cwd()


def _course_source_meshes(model: CourseGxmModelV7) -> tuple[CourseSourceMesh, ...]:
    nodes = {node.ordinal: node for node in model.object_table.nodes}

    def path_for(node: CourseGxmNode) -> tuple[str, ...]:
        path = [node.name]
        parent_id = node.parent_id
        visited = {node.ordinal}
        while parent_id is not None and parent_id in nodes and parent_id not in visited:
            parent = nodes[parent_id]
            path.append(parent.name)
            visited.add(parent_id)
            parent_id = parent.parent_id
        return tuple(reversed(path))

    meshes = []
    for node in model.object_table.nodes:
        if node.class_name.casefold() != "momesh" or node.mesh_index is None or node.mesh_size is None:
            continue
        model.mesh_triangle_indices(node)
        position_indices = model.mesh_position_indices(node)
        unique_indices = tuple(sorted(set(position_indices)))
        points = tuple(model.position(index) for index in unique_indices)
        bounds = None
        if points:
            bounds = (
                tuple(min(point[axis] for point in points) for axis in range(3)),
                tuple(max(point[axis] for point in points) for axis in range(3)),
            )
        meshes.append(CourseSourceMesh(
            literal_name=node.name,
            hierarchy_path=path_for(node),
            source_ordinal=node.ordinal,
            source_index=node.mesh_index,
            source_size=node.mesh_size,
            triangle_start=node.mesh_index,
            triangle_count=node.mesh_size,
            position_indices=position_indices,
            unique_position_indices=unique_indices,
            bounds=bounds,
            source_evidence=("CONFIRMED_BY_BINARY_STRUCTURE", "CONFIRMED_BY_EXECUTABLE"),
        ))
    return tuple(meshes)


def load_course_project(
    path: Path,
    *,
    search_roots: Iterable[Path] = (),
) -> CourseProject:
    """Discover and parse available resources into a partial CourseProject.

    An ambiguous resource kind is left absent and reported in diagnostics. A
    parse failure for one optional resource does not discard successfully
    parsed siblings.
    """
    resources = discover_course_resources(path, search_roots=search_roots)
    diagnostics = list(resources.diagnostics)
    render = race_logic = dependencies = spatial_field = source_txt = source_gxm = source_geometry = None
    source_meshes: tuple[CourseSourceMesh, ...] = ()

    if resources.render_dx is not None:
        try:
            render = _render_resource(parse_course_dx(resources.render_dx))
        except Exception as error:
            diagnostics.append(f"course DX parse failed ({resources.render_dx}): {error}")
    if resources.race_test_xml is not None:
        try:
            document = parse_course_xml(resources.race_test_xml)
            race_logic = build_course_race_logic(document)
            diagnostics.extend(race_logic.diagnostics)
        except Exception as error:
            diagnostics.append(f"RaceTest XML parse failed ({resources.race_test_xml}): {error}")
    if resources.hnt is not None:
        try:
            parsed_hnt = parse_hnt(resources.hnt)
            dependencies = _course_dependencies(parsed_hnt, resources.hnt, _data_gx_root(resources))
        except Exception as error:
            diagnostics.append(f"HNT parse/resolution failed ({resources.hnt}): {error}")
    if resources.sfl is not None:
        try:
            parsed_sfl = parse_sfl(resources.sfl)
            spatial_field = CourseSpatialField(
                source=parsed_sfl.source,
                width=parsed_sfl.header.width,
                height=parsed_sfl.header.height,
                header=parsed_sfl.header,
                payload_offset=parsed_sfl.payload_offset,
                payload_size=len(parsed_sfl.payload),
                value_min=parsed_sfl.value_min,
                value_max=parsed_sfl.value_max,
                distinct_value_count=parsed_sfl.distinct_value_count,
                value_counts=parsed_sfl.value_counts,
                _parsed_field=parsed_sfl,
            )
        except Exception as error:
            diagnostics.append(f"SFL parse failed ({resources.sfl}): {error}")
    if resources.source_txt is not None:
        try:
            source_txt = parse_course_txt(resources.source_txt)
        except Exception as error:
            diagnostics.append(f"course TXT parse failed ({resources.source_txt}): {error}")
    if resources.source_gxm is not None:
        try:
            source_gxm = parse_course_gxm(resources.source_gxm)
            if source_gxm.header_words[0] & 0xFF == 0x02 and (source_gxm.header_words[0] >> 8) & 0xFF == 7:
                if source_txt is None:
                    raise ValueError("version-7 source topology requires the paired course TXT")
                source_geometry = parse_course_gxm_model_v7(resources.source_gxm, source_txt)
                source_meshes = _course_source_meshes(source_geometry)
                if source_geometry.validation.mesh_span_gaps:
                    diagnostics.append(f"course GXM mesh spans have gaps: {source_geometry.validation.mesh_span_gaps[:4]}")
                if source_geometry.validation.mesh_span_overlaps:
                    diagnostics.append(f"course GXM mesh spans overlap: {source_geometry.validation.mesh_span_overlaps[:4]}")
        except Exception as error:
            diagnostics.append(f"course GXM parse failed ({resources.source_gxm}): {error}")

    return CourseProject(
        identity=resources.identity,
        source_context=resources.search_roots[0] if resources.search_roots else None,
        resources=resources,
        render=render,
        race_logic=race_logic,
        dependencies=dependencies,
        sfl=spatial_field,
        source_txt=source_txt,
        source_gxm=source_gxm,
        source_geometry=source_geometry,
        source_meshes=source_meshes,
        diagnostics=tuple(diagnostics),
    )
