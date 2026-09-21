"""Diagnostic OBJ fallback built on the reusable R1 model."""
from __future__ import annotations

import re
from pathlib import Path

from ..assets import AssetResolver
from ..dxt import PNG_ROWS_FLIP_VERTICAL, parse_dxt, write_png
from ..model import DxModel
from ..sidecar import SidecarModel, apply_material_candidates, normalize_texture_value


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value) or "unnamed"


def export_obj(
    model: DxModel,
    output_directory: Path,
    sidecar: SidecarModel | None = None,
    texture_directory: Path | None = None,
    flip_v: bool = False,
) -> tuple[Path, Path]:
    output = output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    apply_material_candidates(model.physical_draws, sidecar)
    resolver = AssetResolver((texture_directory or model.source_path.parent).resolve()) if (texture_directory or model.source_path) else None
    decoded: dict[str, str] = {}
    material_rows = []
    for draw in model.physical_draws:
        candidates = draw.material_candidates
        name = candidates[0].name if len(candidates) == 1 else f"draw_{draw.draw_index:03d}"
        material_name = f"{_safe(name)}_{draw.draw_index:03d}"
        primary = next((slot.value for slot in draw.texture_slots if slot.value.lower() != "null"), None)
        png_name = None
        if primary and resolver:
            source = resolver.resolve_texture(primary)
            if source:
                key = str(source.resolve()).lower()
                if key not in decoded:
                    png_name = f"{_safe(normalize_texture_value(primary))}.png"
                    write_png(
                        parse_dxt(source), output / png_name, row_policy=PNG_ROWS_FLIP_VERTICAL
                    )
                    decoded[key] = png_name
                png_name = decoded[key]
        material_rows.append((material_name, png_name))

    obj_path = output / "model.obj"
    mtl_path = output / "model.mtl"
    with mtl_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("# R1 diagnostic OBJ material library\n")
        for name, png_name in material_rows:
            stream.write(f"\nnewmtl {name}\nKd 1 1 1\n")
            if png_name:
                stream.write(f"map_Kd {png_name}\n")
    with obj_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("# R1 diagnostic OBJ export\nmtllib model.mtl\n")
        for x, y, z in model.vertices.positions:
            stream.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        if model.uv_sets:
            for u, v in model.uv_sets[0].values:
                stream.write(f"vt {u:.9g} {(1-v if flip_v else v):.9g}\n")
        for x, y, z in model.vertices.normals:
            stream.write(f"vn {x:.9g} {y:.9g} {z:.9g}\n")
        for draw, (material_name, _) in zip(model.physical_draws, material_rows):
            stream.write(f"\ng draw_{draw.draw_index:03d}\nusemtl {material_name}\n")
            indices = model.draw_global_indices(draw)
            for index in range(0, len(indices), 3):
                face = indices[index:index + 3]
                if model.uv_sets:
                    values = " ".join(f"{value+1}/{value+1}/{value+1}" for value in face)
                else:
                    values = " ".join(f"{value+1}//{value+1}" for value in face)
                stream.write(f"f {values}\n")
    return obj_path, mtl_path
