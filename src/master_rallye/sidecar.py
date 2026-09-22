"""TXT sidecars, ordered texture matching, and evidence-scored discovery."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import DrawRecord, DxModel, MaterialCandidate

MATERIAL_RE = re.compile(r"Material number \[\s*(\d+)\] has name \[(.*?)\]")
TEXTURE_RE = re.compile(r"Texture \[\s*(\d+)\](.*?)Name\[([^\]]+)\]", re.I)
FLAG_RE = re.compile(r"(HasAlpha|UsesAlpha|IsNoise) \[(Yes|No)\]", re.I)
MESH_RE = re.compile(r"moMesh\(Name \[(.*?)\] Index (\d+) Size (\d+)\)")
MATERIAL_COUNT_RE = re.compile(r"Materials\(Size\s+(\d+)\)")


@dataclass(frozen=True)
class SidecarTexture:
    slot: int
    source_tga: str
    resource_stem: str
    has_alpha: bool | None = None
    uses_alpha: bool | None = None
    is_noise: bool | None = None


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


@dataclass(frozen=True)
class SidecarCandidateScore:
    path: Path
    score: int
    matched_draws: int
    unique_matches: int
    ambiguous_matches: int
    unmatched_draws: int
    mesh_span_compatible: bool
    exact_stem: bool
    name_hint: bool
    malformed: bool
    error: str | None = None


@dataclass
class SidecarResolution:
    selected_path: Path | None
    sidecar: SidecarModel | None
    score: int | None
    ambiguous: bool
    candidates: list[SidecarCandidateScore]


def _optional_bool(flags: dict[str, str], name: str) -> bool | None:
    value = flags.get(name.lower())
    return None if value is None else value.lower() == "yes"


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
            source_tga = Path(texture_match.group(3).replace("\\", "/")).name
            flags = {
                match.group(1).lower(): match.group(2)
                for match in FLAG_RE.finditer(texture_match.group(2))
            }
            current.textures.append(SidecarTexture(
                slot=int(texture_match.group(1)),
                source_tga=source_tga,
                resource_stem=normalize_texture_value(source_tga),
                has_alpha=_optional_bool(flags, "HasAlpha"),
                uses_alpha=_optional_bool(flags, "UsesAlpha"),
                is_noise=_optional_bool(flags, "IsNoise"),
            ))
    count_match = MATERIAL_COUNT_RE.search(text)
    meshes = [
        SidecarMesh(match.group(1), int(match.group(2)), int(match.group(3)))
        for match in MESH_RE.finditer(text)
    ]
    return SidecarModel(
        source=path.name,
        declared_material_count=int(count_match.group(1)) if count_match else None,
        materials=materials,
        meshes=meshes,
    )


def normalized_material_tuple(material: SidecarMaterial, width: int) -> tuple[str, ...] | None:
    ordered = sorted(material.textures, key=lambda texture: texture.slot)
    values = tuple(texture.resource_stem for texture in ordered)
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


def _score_candidate(model: DxModel, path: Path, sidecar: SidecarModel) -> SidecarCandidateScore:
    matches = [match_materials(draw, sidecar) for draw in model.physical_draws]
    matched = sum(bool(items) for items in matches)
    unique = sum(len(items) == 1 for items in matches)
    ambiguous = sum(len(items) > 1 for items in matches)
    unmatched = len(matches) - matched
    mesh_compatible = bool(sidecar.meshes) and sidecar.mesh_span == model.triangle_count
    exact = path.stem.casefold() == Path(model.source).stem.casefold()
    source_name = Path(model.source).stem.casefold()
    hint = source_name in path.stem.casefold() or path.stem.casefold() in source_name
    malformed = (
        not sidecar.materials
        and not sidecar.meshes
        and sidecar.declared_material_count is None
    )
    score = (
        matched * 100
        + unique * 20
        - ambiguous * 3
        - unmatched * 10
        + (15 if mesh_compatible else 0)
        + (5 if exact else 0)
        + (1 if hint else 0)
        - (1000 if malformed else 0)
    )
    return SidecarCandidateScore(
        path=path,
        score=score,
        matched_draws=matched,
        unique_matches=unique,
        ambiguous_matches=ambiguous,
        unmatched_draws=unmatched,
        mesh_span_compatible=mesh_compatible,
        exact_stem=exact,
        name_hint=hint,
        malformed=malformed,
    )


def resolve_sidecar(model: DxModel, directory: Path) -> SidecarResolution:
    candidates: list[SidecarCandidateScore] = []
    parsed: dict[Path, SidecarModel] = {}
    for path in sorted(directory.glob("*.txt"), key=lambda item: item.name.casefold()):
        try:
            sidecar = parse_sidecar(path)
            parsed[path] = sidecar
            candidates.append(_score_candidate(model, path, sidecar))
        except (OSError, ValueError) as error:
            candidates.append(SidecarCandidateScore(
                path=path,
                score=-10000,
                matched_draws=0,
                unique_matches=0,
                ambiguous_matches=0,
                unmatched_draws=len(model.physical_draws),
                mesh_span_compatible=False,
                exact_stem=path.stem.casefold() == Path(model.source).stem.casefold(),
                name_hint=False,
                malformed=True,
                error=str(error),
            ))
    if not candidates:
        return SidecarResolution(None, None, None, False, [])
    ranked = sorted(candidates, key=lambda item: (-item.score, item.path.name.casefold()))
    best = ranked[0]
    tied = [candidate for candidate in ranked if candidate.score == best.score]
    if best.malformed or len(tied) != 1:
        return SidecarResolution(None, None, best.score, len(tied) > 1, ranked)
    return SidecarResolution(best.path, parsed[best.path], best.score, False, ranked)
