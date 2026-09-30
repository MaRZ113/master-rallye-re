"""Read-only course GXM readers: bounded prefix and loader-guided v7 geometry."""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path

from .errors import BoundsError, FormatError
from .course_source import CourseTxtDocument, CourseTxtNode


HEADER_SIZE = 32
OPAQUE_RECORD_STRIDE = 16
MAX_OPAQUE_RECORDS = 4_000_000
GXM_MODEL_CLASS = 0x02
GXM_MODEL_VERSION_7 = 0x07
GXM_TRIANGLE_STRIDE_V7 = 52
GXM_TRIANGLE_U32_COUNT_V7 = 13
UINT32_SENTINEL = 0xFFFFFFFF


@dataclass(frozen=True)
class CourseGxmPrefix:
    source: str
    byte_size: int
    header_words: tuple[int, int, int, int, int, int, int, int]
    record_count: int
    record_stride: int
    record_offset: int
    record_end: int
    opaque_records: bytes
    opaque_tail: bytes


@dataclass(frozen=True)
class CourseGxmNode:
    ordinal: int
    class_name: str
    name: str
    parent_id: int | None
    class_code: int | None
    flags: int | None
    record_control_u16: int
    child_count: int
    mesh_index: int | None
    mesh_size: int | None
    record_offset: int
    record_size: int


@dataclass(frozen=True)
class CourseGxmObjectTable:
    source: str
    table_offset: int
    table_size: int
    nodes: tuple[CourseGxmNode, ...]
    root_name: str
    txt_crosscheck: str


@dataclass(frozen=True)
class CourseGxmFloat3Pool:
    """Header-bounded float3 bank; its point semantics remain corpus inference."""

    source: str
    offset: int
    count: int
    byte_size: int
    raw: bytes
    points: tuple[tuple[float, float, float], ...]


@dataclass(frozen=True)
class CourseGxmBank:
    name: str
    offset: int
    count: int
    stride: int | None
    raw: bytes

    @property
    def end(self) -> int:
        return self.offset + len(self.raw)


@dataclass(frozen=True)
class CourseGxmTriangleV7:
    color_indices: tuple[int, int, int]
    material_index: int
    texcoord_indices: tuple[int, int, int]
    position_indices: tuple[int, int, int]
    normal_indices: tuple[int, int, int]


@dataclass(frozen=True)
class CourseGxmV7Validation:
    triangle_count: int
    domains: tuple[tuple[str, dict], ...]
    mesh_count: int
    mesh_span_gaps: tuple[tuple[int, int], ...]
    mesh_span_overlaps: tuple[tuple[int, int], ...]
    max_mesh_end: int

    def domain(self, name: str) -> dict:
        return dict(self.domains)[name]

    @property
    def passed(self) -> bool:
        return all(domain["out_of_range_count"] == 0 for _, domain in self.domains)

    @property
    def mesh_spans_cover_bank(self) -> bool:
        return not self.mesh_span_gaps and not self.mesh_span_overlaps and self.max_mesh_end == self.triangle_count


@dataclass(frozen=True)
class CourseGxmModelV7:
    """Loader-guided, read-only version-7 moModel geometry.

    The large attribute banks remain raw bytes; records are decoded on demand.
    Material records are deliberately retained as one bounded opaque block.
    """

    source: str
    byte_size: int
    object_class: int
    version: int
    child_count: int
    counts: tuple[int, int, int, int, int, int, int]
    colors: CourseGxmBank
    materials: CourseGxmBank
    normals: CourseGxmBank
    texcoords: CourseGxmBank
    triangles: CourseGxmBank
    positions: CourseGxmBank
    object_table: CourseGxmObjectTable
    validation: CourseGxmV7Validation

    def triangle(self, index: int) -> CourseGxmTriangleV7:
        if not 0 <= index < self.triangles.count:
            raise IndexError(index)
        values = struct.unpack_from("<13I", self.triangles.raw, index * GXM_TRIANGLE_STRIDE_V7)
        return CourseGxmTriangleV7(
            tuple(values[0:3]), values[3], tuple(values[4:7]),
            tuple(values[7:10]), tuple(values[10:13]),
        )

    def position(self, index: int) -> tuple[float, float, float]:
        return _float3_at(self.positions, index)

    def normal(self, index: int) -> tuple[float, float, float]:
        return _float3_at(self.normals, index)

    def texcoord(self, index: int) -> tuple[float, float, float]:
        return _float3_at(self.texcoords, index)

    def color(self, index: int) -> tuple[float, float, float, float]:
        if not 0 <= index < self.colors.count:
            raise IndexError(index)
        return struct.unpack_from("<4f", self.colors.raw, index * 16)

    def find_mesh(self, name: str) -> CourseGxmNode:
        matches = tuple(
            node for node in self.object_table.nodes
            if node.class_name.casefold() == "momesh" and node.name == name
        )
        if len(matches) != 1:
            raise KeyError(f"expected one moMesh named {name!r}, found {len(matches)}")
        return matches[0]

    def mesh_triangle_indices(self, node: CourseGxmNode) -> range:
        if node.class_name.casefold() != "momesh" or node.mesh_index is None or node.mesh_size is None:
            raise FormatError(f"node {node.name!r} is not a bounded moMesh")
        end = node.mesh_index + node.mesh_size
        if node.mesh_index < 0 or node.mesh_size < 0 or end > self.triangles.count:
            raise BoundsError(f"moMesh {node.name!r} triangle range [{node.mesh_index}, {end}) exceeds bank")
        return range(node.mesh_index, end)

    def mesh_position_indices(self, node: CourseGxmNode) -> tuple[int, ...]:
        return tuple(
            position_index
            for triangle_index in self.mesh_triangle_indices(node)
            for position_index in self.triangle(triangle_index).position_indices
        )


def _float3_at(bank: CourseGxmBank, index: int) -> tuple[float, float, float]:
    if not 0 <= index < bank.count:
        raise IndexError(index)
    return struct.unpack_from("<3f", bank.raw, index * 12)


def parse_course_gxm_bytes(data: bytes, source: str = "<bytes>") -> CourseGxmPrefix:
    """Parse the fixed header and bounded opaque bank found in old course GXM.

    Header word 2 is used as a count of 16-byte records for this boundary probe.
    No position, transform, node, or helper semantics are assigned here.
    """
    if len(data) < HEADER_SIZE:
        raise BoundsError(f"course GXM header in {source}: need {HEADER_SIZE} bytes, have {len(data)}")
    header = struct.unpack_from("<8I", data, 0)
    record_count = header[2]
    if record_count > MAX_OPAQUE_RECORDS:
        raise FormatError(
            f"course GXM record count {record_count} in {source} exceeds {MAX_OPAQUE_RECORDS}"
        )
    record_offset = HEADER_SIZE
    record_end = record_offset + record_count * OPAQUE_RECORD_STRIDE
    if record_end > len(data):
        raise BoundsError(
            f"course GXM opaque bank in {source}: count {record_count} at 0x{record_offset:X} "
            f"requires end 0x{record_end:X}, file has {len(data)} bytes"
        )
    return CourseGxmPrefix(
        source=source,
        byte_size=len(data),
        header_words=tuple(header),
        record_count=record_count,
        record_stride=OPAQUE_RECORD_STRIDE,
        record_offset=record_offset,
        record_end=record_end,
        opaque_records=data[record_offset:record_end],
        opaque_tail=data[record_end:],
    )


def parse_course_gxm(path: Path) -> CourseGxmPrefix:
    resolved = path.resolve()
    return parse_course_gxm_bytes(resolved.read_bytes(), resolved.name)


def _expected_table_size(nodes: tuple[CourseTxtNode, ...]) -> int:
    if not nodes:
        raise FormatError("course TXT has no nodes; cannot bound the GXM object table")
    root = nodes[0]
    if root.class_name.casefold() != "momodel" or root.parent_id is not None:
        raise FormatError("course TXT root is not a parentless moModel node")
    size = 2 + len(root.name.encode("latin-1"))
    for node in nodes[1:]:
        encoded_name_size = len(node.name.encode("latin-1"))
        if node.class_name.casefold() == "momesh":
            size += 4 + 8 + 2 + encoded_name_size
        elif node.class_name.casefold() == "mounknown":
            size += 4 + 2 + encoded_name_size
        else:
            raise FormatError(f"unsupported course TXT node class {node.class_name!r}")
    return size


def _expected_direct_child_counts(nodes: tuple[CourseTxtNode, ...]) -> dict[int, int]:
    counts = {node.node_id: 0 for node in nodes}
    for node in nodes:
        if node.parent_id is not None:
            if node.parent_id not in counts:
                raise FormatError(f"course TXT node {node.node_id} has missing parent {node.parent_id}")
            counts[node.parent_id] += 1
    return counts


def parse_course_gxm_object_table_bytes(
    data: bytes,
    txt_document: CourseTxtDocument,
    source: str = "<bytes>",
) -> CourseGxmObjectTable:
    """Parse the exact trailing node records, cross-checked against the paired TXT.

    The paired TXT inventory supplies the expected sequence and therefore an
    exact table boundary. The parser validates every length, class, name,
    child count, and mesh span; it does not search for names in the GXM bytes.
    Current evidence covers old 8.4.1 France1 and Italy1 source pairs only.
    """
    if txt_document.unparsed_node_lines:
        line, text = txt_document.unparsed_node_lines[0]
        raise FormatError(f"paired course TXT has unparsed node at line {line}: {text!r}")
    nodes = txt_document.nodes
    expected_size = _expected_table_size(nodes)
    table_offset = len(data) - expected_size
    header = parse_course_gxm_bytes(data, source)
    if table_offset < header.record_end:
        raise BoundsError(
            f"course GXM object table in {source} overlaps the bounded header bank: "
            f"table starts 0x{table_offset:X}, bank ends 0x{header.record_end:X}"
        )

    offset = table_offset
    root = nodes[0]
    if offset + 2 > len(data):
        raise BoundsError(f"course GXM root name length in {source} is truncated")
    root_length = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    root_end = offset + root_length
    if root_end > len(data):
        raise BoundsError(f"course GXM root name in {source} is truncated")
    root_name = data[offset:root_end].decode("latin-1")
    offset = root_end
    if root_name != root.name:
        raise FormatError(
            f"course GXM root name {root_name!r} in {source} differs from paired TXT {root.name!r}"
        )
    parsed = [CourseGxmNode(
        ordinal=root.node_id,
        class_name=root.class_name,
        name=root_name,
        parent_id=None,
        class_code=None,
        flags=None,
        record_control_u16=0,
        child_count=sum(1 for node in nodes if node.parent_id == root.node_id),
        mesh_index=None,
        mesh_size=None,
        record_offset=table_offset,
        record_size=offset - table_offset,
    )]
    child_counts = _expected_direct_child_counts(nodes)

    for expected in nodes[1:]:
        start = offset
        if offset + 4 > len(data):
            raise BoundsError(f"course GXM node header {expected.node_id} in {source} is truncated")
        class_code, flags, record_control = struct.unpack_from("<BBH", data, offset)
        offset += 4
        class_name = expected.class_name.casefold()
        expected_code = 1 if class_name == "momesh" else 3
        if class_code != expected_code:
            raise FormatError(
                f"course GXM node {expected.node_id} {expected.name!r} in {source}: "
                f"class code {class_code} differs from paired TXT class {expected.class_name}"
            )
        if flags != 1:
            raise FormatError(
                f"course GXM node {expected.node_id} {expected.name!r} in {source}: "
                f"unobserved node flags {flags}"
            )

        mesh_index = mesh_size = None
        if class_name == "momesh":
            if offset + 8 > len(data):
                raise BoundsError(f"course GXM mesh span for {expected.name!r} in {source} is truncated")
            mesh_index, mesh_size = struct.unpack_from("<II", data, offset)
            offset += 8
            if (mesh_index, mesh_size) != (expected.mesh_index, expected.mesh_size):
                raise FormatError(
                    f"course GXM mesh span for {expected.name!r} in {source} is "
                    f"({mesh_index}, {mesh_size}), paired TXT says ({expected.mesh_index}, {expected.mesh_size})"
                )
        elif record_control != child_counts[expected.node_id]:
            raise FormatError(
                f"course GXM node {expected.name!r} in {source} declares {record_control} children, "
                f"paired TXT hierarchy has {child_counts[expected.node_id]}"
            )

        if offset + 2 > len(data):
            raise BoundsError(f"course GXM node name length for {expected.name!r} in {source} is truncated")
        name_length = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        name_end = offset + name_length
        if name_end > len(data):
            raise BoundsError(f"course GXM node name for {expected.name!r} in {source} is truncated")
        name = data[offset:name_end].decode("latin-1")
        offset = name_end
        if name != expected.name:
            raise FormatError(
                f"course GXM node name {name!r} at ordinal {expected.node_id} in {source} "
                f"differs from paired TXT {expected.name!r}"
            )
        parsed.append(CourseGxmNode(
            ordinal=expected.node_id,
            class_name=expected.class_name,
            name=name,
            parent_id=expected.parent_id,
            class_code=class_code,
            flags=flags,
            record_control_u16=record_control,
            child_count=child_counts[expected.node_id],
            mesh_index=mesh_index,
            mesh_size=mesh_size,
            record_offset=start,
            record_size=offset - start,
        ))

    if offset != len(data):
        raise FormatError(
            f"course GXM node table in {source} consumed through 0x{offset:X}, "
            f"file ends at 0x{len(data):X}"
        )
    return CourseGxmObjectTable(
        source,
        table_offset,
        len(data) - table_offset,
        tuple(parsed),
        root_name,
        "exact names, node classes, hierarchy child counts, and mesh spans match paired TXT",
    )


def parse_course_gxm_float3_pool_bytes(
    data: bytes,
    object_table: CourseGxmObjectTable,
    source: str = "<bytes>",
) -> CourseGxmFloat3Pool:
    """Read the final header-counted float3 bank before an exact node table.

    The current France1, Italy1, and Boinds source/cooked comparisons support
    interpreting this bank as course points. This parser preserves the raw
    values and does not associate them with individual node mesh spans.
    """
    header = parse_course_gxm_bytes(data, source)
    if object_table.table_offset < header.record_end:
        raise BoundsError(f"course GXM object table in {source} overlaps the header bank")
    if object_table.table_offset + object_table.table_size != len(data):
        raise FormatError(f"course GXM object table boundary does not match {source} length")
    count = header.header_words[7]
    byte_size = count * 12
    offset = object_table.table_offset - byte_size
    if offset < header.record_end:
        raise BoundsError(
            f"course GXM float3 pool in {source}: count {count} at 0x{offset:X} overlaps "
            f"the bounded header bank ending at 0x{header.record_end:X}"
        )
    raw = data[offset:object_table.table_offset]
    if len(raw) != byte_size:
        raise BoundsError(
            f"course GXM float3 pool in {source}: expected {byte_size} bytes, got {len(raw)}"
        )
    points = tuple(struct.iter_unpack("<3f", raw))
    for index, point in enumerate(points):
        if not all(math.isfinite(value) for value in point):
            raise FormatError(f"course GXM float3 pool in {source} has non-finite point at index {index}")
    return CourseGxmFloat3Pool(source, offset, count, byte_size, raw, points)


def _make_bank(data: bytes, name: str, start: int, count: int, stride: int, source: str) -> CourseGxmBank:
    if count < 0 or count > MAX_OPAQUE_RECORDS:
        raise FormatError(f"course GXM {name} count {count} in {source} is outside supported bounds")
    size = count * stride
    end = start + size
    if start < 0 or end < start or end > len(data):
        raise BoundsError(
            f"course GXM {name} bank in {source}: [{start:#x}, {end:#x}) exceeds file size {len(data):#x}"
        )
    return CourseGxmBank(name, start, count, stride, data[start:end])


def _index_domain(values, count: int, allow_sentinel: bool) -> dict:
    minimum = None
    maximum = None
    sentinels = 0
    out_of_range = 0
    valid_count = 0
    for value in values:
        if value == UINT32_SENTINEL and allow_sentinel:
            sentinels += 1
            continue
        valid_count += 1
        minimum = value if minimum is None else min(minimum, value)
        maximum = value if maximum is None else max(maximum, value)
        if value >= count:
            out_of_range += 1
    return {
        "pool_count": count,
        "reference_count": valid_count + sentinels,
        "valid_reference_count": valid_count,
        "sentinel_count": sentinels,
        "min": minimum,
        "max": maximum,
        "out_of_range_count": out_of_range,
        "sentinel_allowed": allow_sentinel,
    }


def validate_course_gxm_model_v7(model: CourseGxmModelV7) -> CourseGxmV7Validation:
    """Validate each independent index domain and all TXT-backed mesh spans."""
    color_refs: list[int] = []
    material_refs: list[int] = []
    texcoord_refs: list[int] = []
    position_refs: list[int] = []
    normal_refs: list[int] = []
    for offset in range(0, len(model.triangles.raw), GXM_TRIANGLE_STRIDE_V7):
        values = struct.unpack_from("<13I", model.triangles.raw, offset)
        color_refs.extend(values[0:3])
        material_refs.append(values[3])
        texcoord_refs.extend(values[4:7])
        position_refs.extend(values[7:10])
        normal_refs.extend(values[10:13])
    domains = (
        ("color", _index_domain(color_refs, model.colors.count, True)),
        ("material", _index_domain(material_refs, model.materials.count, True)),
        ("texcoord", _index_domain(texcoord_refs, model.texcoords.count, True)),
        ("position", _index_domain(position_refs, model.positions.count, False)),
        ("normal", _index_domain(normal_refs, model.normals.count, False)),
    )
    spans = sorted(
        (node.mesh_index, node.mesh_index + node.mesh_size, node.name)
        for node in model.object_table.nodes
        if node.class_name.casefold() == "momesh"
        and node.mesh_index is not None and node.mesh_size is not None
    )
    gaps: list[tuple[int, int]] = []
    overlaps: list[tuple[int, int]] = []
    cursor = 0
    max_end = 0
    for start, end, _name in spans:
        max_end = max(max_end, end)
        if start > cursor:
            gaps.append((cursor, start))
        elif start < cursor:
            overlaps.append((start, min(cursor, end)))
        cursor = max(cursor, end)
    if cursor < model.triangles.count:
        gaps.append((cursor, model.triangles.count))
    return CourseGxmV7Validation(
        triangle_count=model.triangles.count,
        domains=domains,
        mesh_count=len(spans),
        mesh_span_gaps=tuple(gaps),
        mesh_span_overlaps=tuple(overlaps),
        max_mesh_end=max_end,
    )


def parse_course_gxm_model_v7_bytes(
    data: bytes,
    txt_document: CourseTxtDocument,
    source: str = "<bytes>",
) -> CourseGxmModelV7:
    """Decode the observed version-7 moModel pools without writing or guessing.

    Fixed-bank boundaries are derived from the TXT-validated trailing node
    table, the final position count, and loader-confirmed record strides. The
    intervening material block remains raw bytes.
    """
    prefix = parse_course_gxm_bytes(data, source)
    packed = prefix.header_words[0]
    object_class = packed & 0xFF
    version = (packed >> 8) & 0xFF
    child_count = (packed >> 16) & 0xFFFF
    if object_class != GXM_MODEL_CLASS:
        raise FormatError(f"course GXM {source} has object class 0x{object_class:02X}, expected moModel 0x02")
    if version != GXM_MODEL_VERSION_7:
        raise FormatError(f"course GXM {source} has moModel version {version}; only version 7 is decoded")

    word2, word3, word4, word5, word6, word7 = prefix.header_words[2:8]
    object_table = parse_course_gxm_object_table_bytes(data, txt_document, source)
    model_children = sum(1 for node in txt_document.nodes if node.parent_id == txt_document.nodes[0].node_id)
    if child_count != model_children:
        raise FormatError(
            f"course GXM {source} model child count {child_count} differs from paired TXT root children {model_children}"
        )
    for node in object_table.nodes:
        if node.class_name.casefold() == "momesh" and node.mesh_index is not None and node.mesh_size is not None:
            mesh_end = node.mesh_index + node.mesh_size
            if node.mesh_index < 0 or node.mesh_size < 0 or mesh_end > word6:
                raise BoundsError(
                    f"course GXM {source} moMesh {node.name!r} span "
                    f"[{node.mesh_index}, {mesh_end}) exceeds triangle count {word6}"
                )
    position_start = object_table.table_offset - word7 * 12
    triangle_start = position_start - word6 * GXM_TRIANGLE_STRIDE_V7
    texcoord_start = triangle_start - word5 * 12
    normal_start = texcoord_start - word4 * 12
    colors_start = HEADER_SIZE
    colors_end = colors_start + word2 * 16
    if normal_start < colors_end:
        raise BoundsError(
            f"course GXM {source} version-7 fixed banks overlap: colors end {colors_end:#x}, "
            f"normal bank starts {normal_start:#x}"
        )

    colors = _make_bank(data, "color-like float4", colors_start, word2, 16, source)
    # The material count is not a byte count; preserve its independently
    # bounded variable-length region and its material cardinality separately.
    materials = CourseGxmBank("raw material block", colors_end, word3, None, data[colors_end:normal_start])
    normals = _make_bank(data, "normal float3", normal_start, word4, 12, source)
    texcoords = _make_bank(data, "texcoord-like float3", texcoord_start, word5, 12, source)
    triangles = _make_bank(data, "triangle records", triangle_start, word6, GXM_TRIANGLE_STRIDE_V7, source)
    positions = _make_bank(data, "source position float3", position_start, word7, 12, source)
    banks = (colors, normals, texcoords, positions)
    for bank in banks:
        for index, point in enumerate(struct.iter_unpack("<4f" if bank.stride == 16 else "<3f", bank.raw)):
            if not all(math.isfinite(value) for value in point):
                raise FormatError(f"course GXM {source} {bank.name} has non-finite record at index {index}")

    model = CourseGxmModelV7(
        source=source,
        byte_size=len(data),
        object_class=object_class,
        version=version,
        child_count=child_count,
        counts=prefix.header_words[1:8],
        colors=colors,
        materials=materials,
        normals=normals,
        texcoords=texcoords,
        triangles=triangles,
        positions=positions,
        object_table=object_table,
        validation=CourseGxmV7Validation(0, (), 0, (), (), 0),
    )
    validation = validate_course_gxm_model_v7(model)
    invalid = tuple(
        f"{name} has {domain['out_of_range_count']} out-of-range references"
        for name, domain in validation.domains
        if domain["out_of_range_count"]
    )
    if invalid:
        raise FormatError(f"course GXM {source} invalid version-7 indices: " + "; ".join(invalid))
    return CourseGxmModelV7(
        source=model.source,
        byte_size=model.byte_size,
        object_class=model.object_class,
        version=model.version,
        child_count=model.child_count,
        counts=model.counts,
        colors=model.colors,
        materials=model.materials,
        normals=model.normals,
        texcoords=model.texcoords,
        triangles=model.triangles,
        positions=model.positions,
        object_table=model.object_table,
        validation=validation,
    )


def parse_course_gxm_model_v7(
    path: Path,
    txt_document: CourseTxtDocument | None = None,
) -> CourseGxmModelV7:
    resolved = path.resolve()
    if txt_document is None:
        txt_path = resolved.with_suffix(".txt")
        if not txt_path.is_file():
            raise FileNotFoundError(f"paired course TXT not found for {resolved}")
        txt_document = parse_course_txt(txt_path)
    return parse_course_gxm_model_v7_bytes(resolved.read_bytes(), txt_document, resolved.name)
