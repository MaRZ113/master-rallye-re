"""Version-7 course GXM writer and paired TXT sidecar (R5T-INV E2).

Layout (inverse of ``course_gxm.parse_course_gxm_model_v7``):

* header: eight u32 words. Word 0 packs class 0x02, version 7 and the model's
  direct child count; words 1..7 are 0, colour count, material count, normal
  count, texcoord count, triangle count, position count;
* colour float4 bank; material records (u16 name, u8 slot count, per slot three
  control bytes ``(present, HasAlpha, UsesAlpha)`` and a u16 reference);
  normal, texcoord and position float3 banks; 52-byte triangle records
  ``colour[3] material texcoord[3] position[3] normal[3]`` (0xFFFFFFFF = none);
* node table in depth-first order: root ``u16 name``; then per node
  ``u8 class (1 mesh, 3 group) u8 1 u16 child count``, meshes add
  ``u32 first triangle, u32 triangle count``, then a u16 name.

Coordinates are source space: compiled DX = ``(x, z, -y)`` of the source;
normals follow the same transform; texcoords carry a third component (0.5 in
the AI_Track source); vertex colours are float RGBA (DX stores bytes BGRA).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Sequence

SENTINEL = 0xFFFFFFFF
Vec3 = tuple[float, float, float]
Vec4 = tuple[float, float, float, float]


@dataclass
class GxmTextureSlot:
    reference: str = "Null"
    has_alpha: bool = False
    uses_alpha: bool = False
    is_noise: bool = False

    @property
    def present(self) -> bool:
        return self.reference != "Null"

    def control(self) -> bytes:
        return bytes((int(self.present), int(self.has_alpha), int(self.uses_alpha))) if self.present else bytes(3)


@dataclass
class GxmMaterial:
    name: str
    slots: list[GxmTextureSlot] = field(default_factory=lambda: [GxmTextureSlot(), GxmTextureSlot(), GxmTextureSlot()])


@dataclass
class GxmMesh:
    name: str
    first: int = 0
    count: int = 0
    children: list = field(default_factory=list)  # rare: a mesh node may parent other nodes


@dataclass
class GxmGroup:
    name: str
    children: list = field(default_factory=list)


@dataclass
class GxmCorner:
    position: Vec3
    normal: Vec3
    texcoord: tuple[float, float, float] | None
    color: Vec4 | None


def _u16_string(text: str) -> bytes:
    raw = text.encode("latin-1")
    if len(raw) > 0xFFFF:
        raise ValueError("GXM string longer than 65535 bytes")
    return struct.pack("<H", len(raw)) + raw


def encode_materials(materials: Sequence[GxmMaterial]) -> bytes:
    out = bytearray()
    for material in materials:
        out += _u16_string(material.name)
        out.append(len(material.slots))
        for slot in material.slots:
            out += slot.control() + _u16_string(slot.reference)
    return bytes(out)


def decode_materials(raw: bytes, count: int) -> list[GxmMaterial]:
    """Parse a material block into editable records (inverse of encode_materials)."""
    materials, offset = [], 0
    for _ in range(count):
        length = struct.unpack_from("<H", raw, offset)[0]
        name = raw[offset + 2:offset + 2 + length].decode("latin-1")
        offset += 2 + length
        slot_count = raw[offset]
        offset += 1
        slots = []
        for _ in range(slot_count):
            present, has_alpha, uses_alpha = raw[offset:offset + 3]
            offset += 3
            length = struct.unpack_from("<H", raw, offset)[0]
            reference = raw[offset + 2:offset + 2 + length].decode("latin-1")
            offset += 2 + length
            slot = GxmTextureSlot(reference, bool(has_alpha), bool(uses_alpha))
            if slot.control() != bytes((present, has_alpha, uses_alpha)):
                raise ValueError(f"unrepresentable slot control {present, has_alpha, uses_alpha} in {name!r}")
            slots.append(slot)
        materials.append(GxmMaterial(name, slots))
    if offset != len(raw):
        raise ValueError(f"material block has {len(raw) - offset} trailing bytes")
    return materials


def _walk(node, depth=0):
    yield node, depth
    for child in node.children:
            yield from _walk(child, depth + 1)


def encode_node_table(root_name: str, children: Sequence) -> bytes:
    out = bytearray(_u16_string(root_name))
    for top in children:
        for node, _ in _walk(top):
            if isinstance(node, GxmMesh):
                out += struct.pack("<BBHII", 1, 1, len(node.children), node.first, node.count)
            else:
                out += struct.pack("<BBH", 3, 1, len(node.children))
            out += _u16_string(node.name)
    return bytes(out)


def encode_gxm_v7(
    *,
    colors: Sequence[Vec4],
    materials: Sequence[GxmMaterial],
    normals: Sequence[Vec3],
    texcoords: Sequence[tuple[float, float, float]],
    triangles: Sequence[tuple[int, ...]],
    positions: Sequence[Vec3],
    root_name: str,
    children: Sequence,
    header_word1: int = 0,
    material_block: bytes | None = None,
) -> bytes:
    """Serialise explicit banks. ``material_block`` keeps an original block verbatim."""
    header = struct.pack(
        "<8I",
        0x02 | (7 << 8) | (len(children) << 16),
        header_word1, len(colors), len(materials), len(normals), len(texcoords), len(triangles), len(positions),
    )
    body = bytearray(header)
    body += b"".join(struct.pack("<4f", *c) for c in colors)
    body += material_block if material_block is not None else encode_materials(materials)
    body += b"".join(struct.pack("<3f", *n) for n in normals)
    body += b"".join(struct.pack("<3f", *t) for t in texcoords)
    body += b"".join(struct.pack("<13I", *t) for t in triangles)
    body += b"".join(struct.pack("<3f", *p) for p in positions)
    body += encode_node_table(root_name, children)
    return bytes(body)


def encode_txt(root_name: str, materials: Sequence[GxmMaterial], children: Sequence) -> str:
    """TXT sidecar in the exporter's syntax (parseable by ``course_source``)."""
    lines = [f"moModel(Name [{root_name}])", f"  Materials(Size {len(materials)})", "  {"]
    for index, material in enumerate(materials):
        lines.append(f"    Material number [{index:2d}] has name [{material.name}]")
        for slot_index, slot in enumerate(material.slots):
            if slot.present:
                lines.append(
                    f"      Texture [{slot_index:2d}] HasAlpha [{'Yes' if slot.has_alpha else 'No'}] "
                    f"UsesAlpha [{'Yes' if slot.uses_alpha else 'No'}] IsNoise [{'Yes' if slot.is_noise else 'No'}] "
                    f"Name[{slot.reference}]")
    lines += ["  }", "{"]

    def emit(node, depth):
        pad = "  " * depth
        if isinstance(node, GxmMesh):
            lines.append(f"{pad}moMesh(Name [{node.name}] Index {node.first} Size {node.count})")
        else:
            lines.append(f"{pad}moUnknown(Name [{node.name}])")
        if node.children:
            lines.append(f"{pad}{{")
            for child in node.children:
                emit(child, depth + 1)
            lines.append(f"{pad}}}")

    for top in children:
        emit(top, 1)
    lines += ["}", "Start of warnings:", "End of warnings:"]
    return "\r\n".join(lines) + "\r\n"


class GxmBuilder:
    """Accumulate meshes of corners into deduplicated v7 banks."""

    def __init__(self) -> None:
        self.colors: list[Vec4] = []
        self.normals: list[Vec3] = []
        self.texcoords: list[tuple[float, float, float]] = []
        self.positions: list[Vec3] = []
        self.triangles: list[tuple[int, ...]] = []
        self._index: dict[tuple, int] = {}

    def _ref(self, bank: list, kind: str, value) -> int:
        if value is None:
            return SENTINEL
        key = (kind, value)
        found = self._index.get(key)
        if found is None:
            found = len(bank)
            bank.append(value)
            self._index[key] = found
        return found

    def add_triangle(self, material: int, corners: Sequence[GxmCorner]) -> None:
        cols = [self._ref(self.colors, "c", c.color) for c in corners]
        tcs = [self._ref(self.texcoords, "t", c.texcoord) for c in corners]
        pos = [self._ref(self.positions, "p", c.position) for c in corners]
        nrm = [self._ref(self.normals, "n", c.normal) for c in corners]
        self.triangles.append((*cols, material, *tcs, *pos, *nrm))

    def mesh(self, name: str, triangles: Sequence[tuple[int, Sequence[GxmCorner]]]) -> GxmMesh:
        first = len(self.triangles)
        for material, corners in triangles:
            self.add_triangle(material, corners)
        return GxmMesh(name, first, len(self.triangles) - first)

    def encode(self, materials: Sequence[GxmMaterial], root_name: str, children: Sequence) -> tuple[bytes, str]:
        data = encode_gxm_v7(colors=self.colors, materials=materials, normals=self.normals,
                             texcoords=self.texcoords, triangles=self.triangles, positions=self.positions,
                             root_name=root_name, children=children)
        return data, encode_txt(root_name, materials, children)
