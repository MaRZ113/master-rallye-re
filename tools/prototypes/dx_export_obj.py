#!/usr/bin/env python3
"""Experimental Master Rallye DX to OBJ/MTL proof exporter.

This is deliberately an R0.5 diagnostic, not a production converter. It uses
only the parsed draw table and preserves every embedded texture slot in JSON.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from dx_mesh_probe import DxParseError, parse_dx
from dxt_decode import parse_dxt, write_png


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return value or "unnamed"


def resolve_texture(directory: Path, stem: str) -> Path | None:
    wanted = f"{stem}.dxt".lower()
    return next((p for p in directory.iterdir() if p.is_file() and p.name.lower() == wanted), None)


def export_obj(source: Path, output: Path, texture_directory: Path, flip_v: bool) -> dict:
    result, arrays = parse_dx(source)
    if not arrays["uv_sets"]:
        raise DxParseError("OBJ proof requires at least one UV set")
    output.mkdir(parents=True, exist_ok=True)
    base = safe_name(source.stem)
    obj_path = output / f"{base}.obj"
    mtl_path = output / f"{base}.mtl"
    diagnostics_path = output / f"{base}-export-proof.json"
    records = result["sections"]["draw_table"]["records"]

    used_material_names = set()
    material_rows = []
    decoded = {}
    for record in records:
        candidates = record["material_candidates"]
        candidate_name = candidates[0]["name"] if len(candidates) == 1 else f"draw_{record['draw_index']:03d}"
        material_name = safe_name(candidate_name)
        if material_name in used_material_names:
            material_name = f"{material_name}_{record['draw_index']:03d}"
        used_material_names.add(material_name)
        slots = [entry["text"] for entry in record["texture_slots"]]
        primary = next((value for value in slots if value.lower() != "null"), None)
        png_name = None
        if primary:
            texture_path = resolve_texture(texture_directory, primary)
            if texture_path is None:
                raise FileNotFoundError(f"texture resource not found for {primary!r} in {texture_directory}")
            if primary.lower() not in decoded:
                header, pixels = parse_dxt(texture_path)
                png_path = output / f"{safe_name(primary)}.png"
                write_png(
                    png_path, header["width"], header["height"], pixels, "bgra", "flip-vertical"
                )
                decoded[primary.lower()] = {"source": texture_path.name, "output": png_path.name, "header": header}
            png_name = decoded[primary.lower()]["output"]
        record["export_material"] = material_name
        material_rows.append({
            "draw_index": record["draw_index"],
            "material": material_name,
            "material_candidates": candidates,
            "all_texture_slots": slots,
            "primary_texture": primary,
            "decoded_png": png_name,
        })

    with mtl_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("# Experimental R0.5 proof; only the first non-Null texture is used.\n")
        for row in material_rows:
            stream.write(f"\nnewmtl {row['material']}\nKd 1.0 1.0 1.0\nKa 0.0 0.0 0.0\n")
            if row["decoded_png"]:
                stream.write(f"map_Kd {row['decoded_png']}\n")

    uv_set = arrays["uv_sets"][0]
    indices = arrays["global_indices"]
    with obj_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("# Experimental Master Rallye R0.5 mesh proof\n")
        stream.write(f"mtllib {mtl_path.name}\n")
        for x, y, z in arrays["positions"]:
            stream.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for u, v in uv_set:
            stream.write(f"vt {u:.9g} {(1.0-v if flip_v else v):.9g}\n")
        for x, y, z in arrays["normals"]:
            stream.write(f"vn {x:.9g} {y:.9g} {z:.9g}\n")
        for record, row in zip(records, material_rows):
            stream.write(f"\ng draw_{record['draw_index']:03d}\nusemtl {row['material']}\n")
            start = record["index_start"]
            end = start + record["index_count"]
            for offset in range(start, end, 3):
                face = indices[offset:offset + 3]
                stream.write("f " + " ".join(f"{index+1}/{index+1}/{index+1}" for index in face) + "\n")

    diagnostics = {
        "schema_version": 1,
        "status": "experimental-r0.5-proof",
        "source_name": source.name,
        "vertex_count": result["header"]["vertex_count"],
        "triangle_count": result["sections"]["indices"]["triangle_count"],
        "draw_count": len(records),
        "index_rule": "expanded triangle = (local[1]+base, local[0]+base, local[2]+base)",
        "uv_set": 0,
        "uv_mode": "flip-v" if flip_v else "direct-v",
        "uv_orientation_status": "HIGH_FOR_GLTF_FLIP_V_AFTER_PNG_ROW_CORRECTION",
        "texture_raster_row_policy": "flip-vertical",
        "materials": material_rows,
        "decoded_textures": decoded,
        "outputs": {"obj": obj_path.name, "mtl": mtl_path.name},
    }
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return diagnostics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--texture-directory", type=Path)
    parser.add_argument("--flip-v", action="store_true")
    args = parser.parse_args()
    texture_directory = (args.texture_directory or args.input.parent).resolve()
    diagnostics = export_obj(args.input.resolve(), args.output.resolve(), texture_directory, args.flip_v)
    print(f"exported {diagnostics['vertex_count']} vertices, {diagnostics['triangle_count']} triangles, {diagnostics['draw_count']} draw groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
