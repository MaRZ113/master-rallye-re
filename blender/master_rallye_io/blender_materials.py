"""Conservative Blender preview materials backed by the R1 DXT decoder."""
from __future__ import annotations

import hashlib
import re
import tempfile
from pathlib import Path

import bpy

from .library import (
    AssetResolver,
    PNG_ROWS_FLIP_VERTICAL,
    has_transparency,
    normalize_texture_value,
    parse_dxt,
    write_png,
)


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()) or "unnamed"


class PreviewMaterialCache:
    """Reuse visual materials while draw-specific evidence remains on the object."""

    def __init__(self, texture_directory: Path, load_textures: bool = True, cache_directory: Path | None = None):
        self.texture_directory = texture_directory.resolve()
        self.load_textures = load_textures
        self.resolver = AssetResolver(self.texture_directory)
        self.cache_directory = (
            cache_directory
            or Path(tempfile.gettempdir()) / "master-rallye-re" / "blender-textures"
        )
        self.materials = {}
        self.images = {}
        self.warnings = []

    def _decode_image(self, source: Path):
        key = str(source.resolve()).casefold()
        if key in self.images:
            return self.images[key]
        texture = parse_dxt(source)
        stat = source.stat()
        identity = f"{key}|{stat.st_size}|{stat.st_mtime_ns}".encode("utf-8")
        suffix = hashlib.sha256(identity).hexdigest()[:16]
        png_path = self.cache_directory / f"{_safe(source.stem)}-{suffix}.png"
        if not png_path.exists():
            png_path.parent.mkdir(parents=True, exist_ok=True)
            write_png(texture, png_path, row_policy=PNG_ROWS_FLIP_VERTICAL)
        image = bpy.data.images.load(str(png_path), check_existing=True)
        image.name = f"MR {source.stem}"
        image.alpha_mode = "STRAIGHT"
        image["mr_dxt_source"] = str(source.resolve())
        image["mr_png_row_policy"] = PNG_ROWS_FLIP_VERTICAL
        self.images[key] = (image, has_transparency(texture))
        return self.images[key]

    def material_for_draw(self, draw):
        primary = next(
            (slot.value for slot in draw.texture_slots if slot.value.casefold() != "null"),
            None,
        )
        source = self.resolver.resolve_texture(primary) if primary and self.load_textures else None
        if primary and self.load_textures and source is None:
            self.warnings.append(f"draw {draw.draw_index}: missing texture {primary!r}")

        image = None
        transparent = False
        if source is not None:
            image, transparent = self._decode_image(source)
        key = (str(source.resolve()).casefold() if source else None, transparent)
        if key in self.materials:
            return self.materials[key]

        label = normalize_texture_value(primary) if primary else "neutral"
        material = bpy.data.materials.new(name=f"MR Preview - {_safe(label)}")
        material.use_nodes = True
        material.diffuse_color = (1.0, 1.0, 1.0, 1.0)
        material["mr_preview_semantics"] = "PROVISIONAL_FIRST_NON_NULL_SLOT"
        material["mr_primary_texture_slot"] = primary or "Null"
        material["mr_runtime_blending_known"] = False
        nodes = material.node_tree.nodes
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
        if image is not None:
            image_node = nodes.new("ShaderNodeTexImage")
            image_node.image = image
            image_node.interpolation = "Linear"
            material.node_tree.links.new(image_node.outputs["Color"], shader.inputs["Base Color"])
            material.node_tree.links.new(image_node.outputs["Alpha"], shader.inputs["Alpha"])
            material["mr_dxt_source"] = str(source.resolve())
            material["mr_png_row_policy"] = PNG_ROWS_FLIP_VERTICAL
        if transparent:
            if hasattr(material, "surface_render_method"):
                material.surface_render_method = "DITHERED"
            elif hasattr(material, "blend_method"):
                material.blend_method = "BLEND"
            material.use_transparency_overlap = False
            material["mr_alpha_preview"] = "PROVISIONAL_DECODED_ALPHA"
        self.materials[key] = material
        return material
