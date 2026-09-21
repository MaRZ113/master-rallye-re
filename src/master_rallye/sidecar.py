"""Parser and normalized ordered texture-tuple matching for DX TXT sidecars."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import DrawRecord, MaterialCandidate

MATERIAL_RE = re.compile(r"Material number \[\s*(\d+)\] has name \[(.*?)\]")
TEXTURE_RE = re.compile(r"Texture \[\s*(\d+)\].*?Name\[([^\]]+\.tga)\]", re.I)
MESH_RE = re.compile(r"moMesh\(Name \[(.*?)\] Index (\d+) Size (\d+)\)")
MATERIAL_COUNT_RE = re.compile(r"Materials\(Size\s+(\d+)\)")


@dataclass(frozen=True)
class SidecarTexture:
    slot: int
    source_tga: str
    resource_stem: str


@dataclass
class SidecarMaterial:
    number: int
    name: str
    textures: list[SidecarTexture] = field(default_factory=list)


@dataclass(frozen=True)
class SidecarMesh:
    name: str
    index: int
    size: int


@dataclass
class SidecarModel:
    source: str
    declared_material_count: int | None
    materials: list[SidecarMaterial]
    meshes: list[SidecarMesh]

    @property
    def mesh_span(self) -> int:
        return max((mesh.index + mesh.size for mesh in self.meshes), default=0)


def normalize_texture_value(value: str) -> str:
    if value.strip().lower() == "null":
        return "null"
    name = Path(value.replace("\\", "/")).name
    stem = Path(name).stem.lower()
    return stem if stem.endswith("-tga") else f"{stem}-tga"


def parse_sidecar(path: Path) -> SidecarModel:
    text = path.read_text(encoding="latin-1")
    materials: list[SidecarMaterial] = []
    current: SidecarMaterial | None = None
    for line in text.splitlines():
        material_match = MATERIAL_RE.search(line)
        if material_match:
            current = SidecarMaterial(int(material_match.group(1)), material_match.group(2))
            materials.append(current)
            continue
        texture_match = TEXTURE_RE.search(line)
        if texture_match and current is not None:
            source_tga = Path(texture_match.group(2).replace("\\", "/")).name
            current.textures.append(SidecarTexture(
                int(texture_match.group(1)), source_tga, normalize_texture_value(source_tga)
            ))
    count_match = MATERIAL_COUNT_RE.search(text)
    meshes = [SidecarMesh(match.group(1), int(match.group(2)), int(match.group(3))) for match in MESH_RE.finditer(text)]
    return SidecarModel(
        source=path.name,
        declared_material_count=int(count_match.group(1)) if count_match else None,
        materials=materials,
        meshes=meshes,
    )


def normalized_material_tuple(material: SidecarMaterial, width: int) -> tuple[str, ...] | None:
    values = tuple(texture.resource_stem for texture in material.textures)
    if len(values) > width:
        return None
    return values + ("null",) * (width - len(values))


def match_materials(draw: DrawRecord, sidecar: SidecarModel | None) -> list[MaterialCandidate]:
    if sidecar is None:
        return []
    actual = tuple(normalize_texture_value(slot.value) for slot in draw.texture_slots)
    return [
        MaterialCandidate(material.number, material.name)
        for material in sidecar.materials
        if normalized_material_tuple(material, len(actual)) == actual
    ]


def apply_material_candidates(draws: list[DrawRecord], sidecar: SidecarModel | None) -> None:
    for draw in draws:
        draw.material_candidates = match_materials(draw, sidecar)
