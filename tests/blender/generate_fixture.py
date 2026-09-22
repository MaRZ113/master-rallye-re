#!/usr/bin/env python3
"""Generate non-copyrighted grouped DX/DXT/TXT fixtures for Blender tests."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

DX_MAGIC = 0x0000D00D
DXT_MAGIC = 0x0000FEED

POSITIONS = (
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0),
    (0.0, 1.0, 0.0),
)
UVS = (
    (0.0, 0.0),
    (1.0, 0.0),
    (1.0, 1.0),
    (0.0, 1.0),
)
MAIN_NORMALS = (
    (0.0, 0.0, 2.0),
    (0.0, 0.0, 0.5),
    (0.0, 0.0, 1.0),
    (0.0, 0.0, 3.0),
)
FALLBACK_NORMALS = (
    (0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0),
    (float("nan"), 0.0, 1.0),
    (0.0, 0.0, 1.0),
)


def draw_core(base, local_max, index_start, index_count, texture):
    payload = bytearray(struct.pack(
        "<7If4BI",
        2,
        base,
        local_max,
        index_start,
        index_count,
        1,
        0,
        1.0,
        0,
        0,
        0,
        1,
        5,
    ))
    payload += struct.pack("<I", 2)
    for value in (texture, "Null"):
        encoded = value.encode("ascii")
        payload += struct.pack("<I", len(encoded)) + encoded
    payload += struct.pack("<I", 0)
    return bytes(payload)


def grouped_records(textures=("synthetic-top-tga", "synthetic-bottom-tga")):
    label = b"synthetic_group"
    parent = (
        struct.pack("<2I", 7, len(label))
        + label
        + struct.pack("<5I", 2, 2, 8, 99, 1)
        + draw_core(0, 2, 0, 3, textures[0])
    )
    child = (
        struct.pack("<3I", 8, 2, 1)
        + draw_core(0, 3, 3, 3, textures[1])
    )
    return parent + child


def build_dx(normals=MAIN_NORMALS, textures=("synthetic-top-tga", "synthetic-bottom-tga")):
    colors = bytes((
        255, 0, 0, 255,
        0, 255, 0, 255,
        0, 0, 255, 255,
        255, 255, 0, 255,
    ))
    # Two triangles share vertices 0 and 2, exercising repeated corner use.
    local = (0, 1, 2, 0, 2, 3)
    global_indices = (1, 0, 2, 2, 0, 3)
    blob = bytearray(struct.pack("<4I", DX_MAGIC, 135, 1337, len(POSITIONS)))
    for value in POSITIONS:
        blob += struct.pack("<3f", *value)
    for value in normals:
        blob += struct.pack("<3f", *value)
    blob += colors
    blob += struct.pack("<I", 1)
    for value in UVS:
        blob += struct.pack("<2f", *value)
    blob += struct.pack("<I", len(local)) + struct.pack("<6H", *local)
    blob += struct.pack("<2I", 1, 1) + grouped_records(textures)
    blob += (
        struct.pack("<2I", 1, len(global_indices))
        + struct.pack("<6I", *global_indices)
    )
    return bytes(blob)


def build_dxt(top_rgba, bottom_rgba):
    # Stored DXT row zero is visual bottom; PNG presentation must reverse rows.
    def bgra(row):
        payload = bytearray()
        for red, green, blue, alpha in row:
            payload += bytes((blue, green, red, alpha))
        return payload

    stored = bgra(bottom_rgba) + bgra(top_rgba)
    return struct.pack("<5I", DXT_MAGIC, 1, 0x12345678, 2, 2) + stored


def signed_bits(values):
    return [
        [struct.unpack("<i", struct.pack("<f", component))[0] for component in value]
        for value in values
    ]


def generate(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    (output / "synthetic.dx").write_bytes(build_dx())
    # A second top-level resource makes folder import exercise multiple DX files.
    (output / "synthetic-secondary.dx").write_bytes(build_dx())
    (output / "synthetic.txt").write_text(
        "Materials(Size 2)\n"
        "Material number [ 0] has name [SyntheticTop]\n"
        "Texture [ 0] HasAlpha [No] UsesAlpha [Yes] IsNoise [No] Name[Synthetic-Top.tga]\n"
        "Material number [ 1] has name [SyntheticBottom]\n"
        "Texture [ 0] HasAlpha [Yes] UsesAlpha [No] IsNoise [Yes] Name[Synthetic-Bottom.tga]\n"
        "moMesh(Name [synthetic_group] Index 0 Size 2)\n",
        encoding="latin-1",
    )
    opaque = 255
    (output / "synthetic-top-tga.dxt").write_bytes(build_dxt(
        ((255, 0, 0, opaque), (0, 255, 0, opaque)),
        ((0, 0, 255, opaque), (255, 255, 0, opaque)),
    ))
    (output / "synthetic-bottom-tga.dxt").write_bytes(build_dxt(
        ((255, 0, 255, opaque), (0, 255, 255, opaque)),
        ((32, 64, 96, 128), (224, 192, 160, opaque)),
    ))

    fallback = output / "fallback"
    fallback.mkdir(exist_ok=True)
    (fallback / "synthetic-fallback.dx").write_bytes(build_dx(FALLBACK_NORMALS))

    warning_cache = output / "warning-cache"
    warning_cache.mkdir(exist_ok=True)
    (warning_cache / "a-missing.dx").write_bytes(build_dx(
        textures=("missing-only-here-tga", "synthetic-bottom-tga"),
    ))
    (warning_cache / "b-clean.dx").write_bytes(build_dx())
    for texture_name in ("synthetic-top-tga.dxt", "synthetic-bottom-tga.dxt"):
        (warning_cache / texture_name).write_bytes((output / texture_name).read_bytes())

    expected = {
        "vertex_count": 4,
        "triangle_count": 2,
        "draw_count": 2,
        "record_tags": [7, 8],
        "group_count": 1,
        "material_count": 2,
        "uv_set_count": 1,
        "uvs": UVS,
        "source_normal_bits": signed_bits(MAIN_NORMALS),
        "fallback_source_normal_bits": signed_bits(FALLBACK_NORMALS),
    }
    (output / "expected.json").write_text(
        json.dumps(expected, indent=2) + "\n",
        encoding="utf-8",
    )
    return expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
