"""Minimal glTF 2.0 exporter for parsed Master Rallye vehicle models."""
from __future__ import annotations

import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..assets import AssetResolver
from ..dxt import PNG_ROWS_FLIP_VERTICAL, has_transparency, parse_dxt, write_png
from ..errors import ExportError
from ..model import DrawRecord, DxModel
from ..sidecar import SidecarModel, apply_material_candidates, normalize_texture_value


@dataclass(frozen=True)
class GltfExportResult:
    gltf_path: Path
    bin_path: Path
    metadata_path: Path
    texture_count: int
    primitive_count: int
    warnings: tuple[str, ...]


class BufferBuilder:
    def __init__(self):
        self.data = bytearray()
        self.views: list[dict[str, Any]] = []
        self.accessors: list[dict[str, Any]] = []

    def add_view(self, payload: bytes, target: int | None = None) -> int:
        while len(self.data) % 4:
            self.data.append(0)
        offset = len(self.data)
        self.data.extend(payload)
        view: dict[str, Any] = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
        if target is not None:
            view["target"] = target
        self.views.append(view)
        return len(self.views) - 1

    def add_accessor(
        self,
        payload: bytes,
        component_type: int,
        count: int,
        accessor_type: str,
        target: int | None = None,
        normalized: bool = False,
        minimum: list[float] | None = None,
        maximum: list[float] | None = None,
    ) -> int:
        view = self.add_view(payload, target)
        accessor: dict[str, Any] = {
            "bufferView": view,
            "byteOffset": 0,
            "componentType": component_type,
            "count": count,
            "type": accessor_type,
        }
        if normalized:
            accessor["normalized"] = True
        if minimum is not None:
            accessor["min"] = minimum
        if maximum is not None:
            accessor["max"] = maximum
        self.accessors.append(accessor)
        return len(self.accessors) - 1


def _safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return value or "unnamed"


def _pack_float_vectors(values: tuple[tuple[float, ...], ...]) -> bytes:
    if not values:
        return b""
    width = len(values[0])
    flattened = (component for value in values for component in value)
    return struct.pack(f"<{len(values) * width}f", *flattened)


def transform_uv_values(
    values: tuple[tuple[float, float], ...],
    flip_v: bool,
) -> tuple[tuple[float, float], ...]:
    """Apply only the requested coordinate-space V transform."""
    return tuple((u, 1.0 - v if flip_v else v) for u, v in values)


def _draw_metadata(draw: DrawRecord, group_label: str | None) -> dict[str, Any]:
    return {
        "record_path": draw.record_path,
        "record_tag": draw.tag,
        "record_offset": f"0x{draw.offset:X}",
        "core_offset": f"0x{draw.core_offset:X}",
        "top_level_index": draw.top_level_index,
        "group_label": group_label,
        "control_words": list(draw.control_words),
        "declared_child_count": draw.declared_child_count,
        "vertex_base": draw.vertex_base,
        "local_vertex_max": draw.local_vertex_max,
        "index_start": draw.index_start,
        "index_count": draw.index_count,
        "unknown_0x14": draw.unknown_0x14,
        "unknown_0x18": draw.unknown_0x18,
        "unknown_0x1C_float": draw.unknown_0x1c_float,
        "flags_0x20": draw.flags_0x20.hex(" "),
        "unknown_0x24": draw.unknown_0x24,
        "texture_slots": [slot.value for slot in draw.texture_slots],
        "material_candidates": [
            {"number": candidate.number, "name": candidate.name}
            for candidate in draw.material_candidates
        ],
    }


def export_gltf(
    model: DxModel,
    output_directory: Path,
    sidecar: SidecarModel | None = None,
    texture_directory: Path | None = None,
    flip_v: bool = False,
    strict: bool = False,
) -> GltfExportResult:
    output = output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    texture_output = output / "textures"
    apply_material_candidates(model.physical_draws, sidecar)
    resolver = AssetResolver((texture_directory or model.source_path.parent).resolve()) if (texture_directory or model.source_path) else None
    warnings = list(model.diagnostics.warnings)

    builder = BufferBuilder()
    positions = model.vertices.positions
    normals = model.vertices.normals
    position_min = [min(value[axis] for value in positions) for axis in range(3)]
    position_max = [max(value[axis] for value in positions) for axis in range(3)]
    position_accessor = builder.add_accessor(
        _pack_float_vectors(positions), 5126, len(positions), "VEC3", 34962,
        minimum=position_min, maximum=position_max,
    )
    normal_accessor = builder.add_accessor(
        _pack_float_vectors(normals), 5126, len(normals), "VEC3", 34962
    )
    uv_accessor: int | None = None
    if model.uv_sets:
        uv_values = transform_uv_values(model.uv_sets[0].values, flip_v)
        uv_accessor = builder.add_accessor(
            _pack_float_vectors(uv_values), 5126, len(uv_values), "VEC2", 34962
        )
    color_accessor = builder.add_accessor(
        model.vertices.colors, 5121, model.vertex_count, "VEC4", 34962, normalized=True
    )

    images: list[dict[str, Any]] = []
    textures: list[dict[str, Any]] = []
    decoded: dict[str, tuple[int, bool, str]] = {}
    materials: list[dict[str, Any]] = []
    primitives: list[dict[str, Any]] = []
    material_metadata: list[dict[str, Any]] = []

    group_labels = {
        group.top_level_index: group.root.group_label for group in model.draw_groups
    }
    for draw in model.physical_draws:
        draw_index = draw.draw_index if draw.draw_index is not None else len(primitives)
        candidates = draw.material_candidates
        material_name = candidates[0].name if len(candidates) == 1 else f"draw_{draw_index:03d}"
        metadata = _draw_metadata(draw, group_labels.get(draw.top_level_index))
        primary = next((slot.value for slot in draw.texture_slots if slot.value.lower() != "null"), None)
        material: dict[str, Any] = {
            "name": _safe_name(material_name),
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 1.0,
            },
            "extras": {"master_rallye": metadata},
        }
        decoded_png: str | None = None
        if primary and resolver is not None and uv_accessor is not None:
            source = resolver.resolve_texture(primary)
            if source is None:
                message = f"draw {draw_index}: texture {primary!r} was not found"
                if strict:
                    raise ExportError(message)
                warnings.append(message)
            else:
                cache_key = str(source.resolve()).lower()
                if cache_key not in decoded:
                    texture = parse_dxt(source)
                    png_name = f"{_safe_name(normalize_texture_value(primary))}.png"
                    png_path = texture_output / png_name
                    write_png(texture, png_path, row_policy=PNG_ROWS_FLIP_VERTICAL)
                    image_index = len(images)
                    images.append({"uri": f"textures/{png_name}", "name": source.name})
                    textures.append({"sampler": 0, "source": image_index, "name": normalize_texture_value(primary)})
                    decoded[cache_key] = (len(textures) - 1, has_transparency(texture), png_name)
                texture_index, transparent, decoded_png = decoded[cache_key]
                material["pbrMetallicRoughness"]["baseColorTexture"] = {
                    "index": texture_index,
                    "texCoord": 0,
                }
                if transparent:
                    material["alphaMode"] = "BLEND"
                    material["doubleSided"] = True
        elif primary and uv_accessor is None:
            warnings.append(f"draw {draw_index}: texture retained as metadata because UV set 0 is absent")
        material_index = len(materials)
        materials.append(material)

        draw_indices = model.draw_global_indices(draw)
        if len(draw_indices) != draw.index_count:
            raise ExportError(f"draw {draw_index}: incomplete triangle reconstruction")
        if draw_indices and max(draw_indices) >= model.vertex_count:
            raise ExportError(f"draw {draw_index}: index exceeds vertex array")
        index_payload = struct.pack(f"<{len(draw_indices)}I", *draw_indices) if draw_indices else b""
        index_accessor = builder.add_accessor(
            index_payload, 5125, len(draw_indices), "SCALAR", 34963,
            minimum=[min(draw_indices)] if draw_indices else [0],
            maximum=[max(draw_indices)] if draw_indices else [0],
        )
        attributes = {
            "POSITION": position_accessor,
            "NORMAL": normal_accessor,
            "COLOR_0": color_accessor,
        }
        if uv_accessor is not None:
            attributes["TEXCOORD_0"] = uv_accessor
        primitives.append({
            "attributes": attributes,
            "indices": index_accessor,
            "material": material_index,
            "mode": 4,
            "extras": {"master_rallye": metadata},
        })
        material_metadata.append({
            "draw_index": draw_index,
            "preview_material_name": material["name"],
            "primary_preview_slot": primary,
            "decoded_png": decoded_png,
            **metadata,
        })

    bin_name = "model.bin"
    gltf: dict[str, Any] = {
        "asset": {
            "version": "2.0",
            "generator": "master-rallye-re R1 research exporter",
            "extras": {
                "master_rallye": {
                    "source_name": model.source,
                    "uv_mode": "flip-v" if flip_v else "direct-v",
                    "uv_orientation_status": "HIGH_FOR_GLTF_FLIP_V_AFTER_PNG_ROW_CORRECTION",
                    "uv_orientation_evidence": "upright asymmetric Astero PNGs plus direct-v versus flip-v vehicle comparison",
                    "texture_raster_row_policy": "flip-vertical",
                    "material_policy": "first non-Null slot used provisionally as baseColorTexture",
                }
            },
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": Path(model.source).stem}],
        "meshes": [{
            "name": Path(model.source).stem,
            "primitives": primitives,
            "extras": {
                "master_rallye": {
                    "declared_top_level_record_count": model.declared_top_level_record_count,
                    "reconstructed_root_count": len(model.draw_groups),
                    "groups": [
                        {
                            "top_level_index": group.top_level_index,
                            "record_path": group.root.record_path,
                            "label": group.root.group_label,
                            "draw_indices": group.draw_indices,
                        }
                        for group in model.draw_groups
                    ],
                }
            },
        }],
        "buffers": [{"uri": bin_name, "byteLength": len(builder.data)}],
        "bufferViews": builder.views,
        "accessors": builder.accessors,
        "materials": materials,
    }
    if images:
        gltf["samplers"] = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]
        gltf["images"] = images
        gltf["textures"] = textures

    gltf_path = output / "model.gltf"
    bin_path = output / bin_name
    metadata_path = output / "metadata.json"
    bin_path.write_bytes(builder.data)
    gltf_path.write_text(json.dumps(gltf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    metadata = {
        "schema_version": 1,
        "status": "R1 experimental extraction",
        "source_name": model.source,
        "model_summary": model.to_summary(),
        "uv_mode": "flip-v" if flip_v else "direct-v",
        "uv_orientation_status": "HIGH_FOR_GLTF_FLIP_V_AFTER_PNG_ROW_CORRECTION",
        "uv_orientation_evidence": "upright asymmetric Astero PNGs plus direct-v versus flip-v vehicle comparison",
        "texture_raster_row_policy": "flip-vertical",
        "materials": material_metadata,
        "warnings": warnings,
        "outputs": {
            "gltf": gltf_path.name,
            "binary": bin_path.name,
            "texture_directory": "textures",
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return GltfExportResult(
        gltf_path,
        bin_path,
        metadata_path,
        len(decoded),
        len(primitives),
        tuple(warnings),
    )
