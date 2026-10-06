"""Conservative Blender preview materials backed by the R1 DXT decoder."""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path

import bpy

from .library import (
    AssetResolver,
    MaterialSemantics,
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

    def __init__(self, texture_directory: Path, load_textures: bool = True,
                 cache_directory: Path | None = None, *, reflections: bool = True):
        self.texture_directory = texture_directory.resolve()
        self.load_textures = load_textures
        self.reflections = reflections
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
        image["mr_dxt_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        image["mr_png_row_policy"] = PNG_ROWS_FLIP_VERTICAL
        self.images[key] = (image, has_transparency(texture))
        return self.images[key]

    def material_for_draw(self, draw, *, resource_kind="vehicle"):
        if resource_kind != "vehicle":
            return self._material_for_unscoped_draw(draw)
        semantics = MaterialSemantics.from_draw(draw, reflections=self.reflections)
        slots = semantics.texture_slots
        base_name = slots[0] if slots else "Null"
        helper_name = slots[1] if len(slots) > 1 else "Null"
        bindings = semantics.texture_stage_mapping
        sources = []
        for index, name in enumerate((base_name, helper_name)):
            bound = bindings[f"slot{index}"].bound
            source = self.resolver.resolve_texture(name) if bound and self.load_textures else None
            if bound and self.load_textures and source is None:
                self.warnings.append(f"draw {draw.draw_index}: missing texture in slot{index}: {name!r}")
            sources.append(source)
        key = ("R_MAT1", tuple(str(p.resolve()).casefold() if p else None for p in sources),
               slots, draw.flags_0x20, draw.unknown_0x24, draw.unknown_0x18, self.reflections)
        if key in self.materials:
            return self.materials[key]
        material = bpy.data.materials.new(name=f"MR Preview - {_safe(normalize_texture_value(base_name))}")
        material.use_nodes = True
        material.diffuse_color = (1, 1, 1, 1)
        material["mr_preview_semantics"] = "R_MAT1_RUNTIME_STAGES_V3"
        material["mr_texture_slots_json"] = json.dumps(slots)
        material["mr_serialized_flags_0x20_hex"] = draw.flags_0x20.hex()
        material["mr_serialized_texture_mask"] = draw.unknown_0x24
        material["mr_primary_texture_slot"] = base_name
        material["mr_preview_source_slot"] = 0 if bindings["slot0"].bound else -1
        material["mr_environment_helper"] = helper_name
        material["mr_runtime_alpha_enabled"] = semantics.alpha_enabled
        material["mr_runtime_alpha_test"] = semantics.alpha_mode == "ALPHA_TEST"
        material["mr_runtime_blending_known"] = semantics.classification == "CLASSIFIED"
        material["mr_runtime_alpha_mode"] = semantics.alpha_mode
        material["mr_runtime_environment_enabled"] = semantics.environment_mapping
        material["mr_preview_reflections_enabled"] = self.reflections
        material["mr_runtime_shader_family"] = semantics.runtime_shader_family or "UNKNOWN"
        material["mr_environment_confidence"] = bindings["slot1"].confidence
        material["mr_material_semantics_json"] = json.dumps(semantics.to_dict(), separators=(",", ":"))
        material["mr_preview_confidence"] = "APPROXIMATE" if semantics.classification == "CLASSIFIED" else "UNKNOWN"
        notes = ["PRINCIPLED_LIGHTING_DIFFERS_FROM_D3D8", "BLENDER_DISPLAY_NORMALS",
                 "CAMERA_COORDINATE_CONVENTION_APPROXIMATION", "COMPOSITE_RUNTIME_SORT_NOT_REPRODUCED",
                 "INSTANCE_Z_STATE_OVERRIDES_NOT_REPRODUCED"]
        if not self.load_textures:
            notes.append("TEXTURES_NOT_LOADED")
        elif any(bindings[f"slot{i}"].bound and sources[i] is None for i in (0, 1)):
            notes.append("MISSING_TEXTURE")
        if semantics.unknown_reasons:
            notes.extend(semantics.unknown_reasons)
            self.warnings.append(f"draw {draw.draw_index}: material UNKNOWN: {', '.join(semantics.unknown_reasons)}")
        material["mr_preview_approximation_notes_json"] = json.dumps(notes)
        nodes, links = material.node_tree.nodes, material.node_tree.links
        nodes.clear()

        def node(kind, name):
            item = nodes.new(kind)
            item.name = name
            item.label = name
            return item

        output = node("ShaderNodeOutputMaterial", "MR Preview Output")
        shader = node("ShaderNodeBsdfPrincipled", "MR Preview Surface")
        links.new(shader.outputs["BSDF"], output.inputs["Surface"])
        color = node("ShaderNodeRGB", "MR Default Diffuse")
        color.outputs[0].default_value = (1, 1, 1, 1)
        alpha = node("ShaderNodeValue", "MR Default Alpha")
        alpha.outputs[0].default_value = 1
        base_color, base_alpha = color.outputs[0], alpha.outputs[0]
        if semantics.vertex_diffuse_enabled:
            diffuse = node("ShaderNodeVertexColor", "MR Source Vertex Diffuse")
            diffuse.layer_name = "MR Vertex Color"
            base_color, base_alpha = diffuse.outputs["Color"], diffuse.outputs["Alpha"]
        transparent = False
        base_source, env_source = sources
        if base_source is not None and semantics.classification == "CLASSIFIED":
            image, transparent = self._decode_image(base_source)
            texture = node("ShaderNodeTexImage", "MR Slot 0 Base")
            texture.image = image
            texture.interpolation = "Linear"
            if semantics.source_uv_enabled:
                uv = node("ShaderNodeUVMap", "MR Source UV 0")
                uv.uv_map = "MR UV 0"
                links.new(uv.outputs["UV"], texture.inputs["Vector"])
            else:
                zero = node("ShaderNodeCombineXYZ", "MR No Source UV")
                links.new(zero.outputs[0], texture.inputs["Vector"])
            combine = node("ShaderNodeMixRGB", "MR Stage 0 Modulate Diffuse")
            combine.blend_type = "MULTIPLY"
            combine.inputs[0].default_value = 1
            links.new(texture.outputs["Color"], combine.inputs[1])
            links.new(base_color, combine.inputs[2])
            base_color = combine.outputs[0]
            multiply = node("ShaderNodeMath", "MR Stage 0 Alpha")
            multiply.operation = "MULTIPLY"
            links.new(texture.outputs["Alpha"], multiply.inputs[0])
            links.new(base_alpha, multiply.inputs[1])
            base_alpha = multiply.outputs[0]
            material["mr_dxt_source"] = str(base_source.resolve())
            material["mr_dxt_sha256"] = image.get("mr_dxt_sha256")
            material["mr_png_row_policy"] = PNG_ROWS_FLIP_VERTICAL
        links.new(base_color, shader.inputs["Base Color"])
        show_env = (semantics.classification == "CLASSIFIED" and env_source is not None
                    and semantics.null_slot_behavior["stage1_effective"])
        material["mr_secondary_stage_preview"] = (
            "APPROXIMATE_ENV_NORMALS" if show_env else
            "BOUND_ENV_SUPPRESSED_NULL_BASE" if bindings["slot1"].bound and not bindings["slot0"].bound else "NOT_SHOWN")
        if show_env:
            env_image, _ = self._decode_image(env_source)
            env_texture = node("ShaderNodeTexImage", "MR Slot 1 Environment")
            env_texture.image = env_image
            env_texture.interpolation = "Linear"
            geometry = node("ShaderNodeNewGeometry", "MR Display Normal")
            camera = node("ShaderNodeVectorTransform", "MR Camera Space Normal Approximation")
            camera.vector_type = "NORMAL"
            camera.convert_from, camera.convert_to = "WORLD", "CAMERA"
            links.new(geometry.outputs["Normal"], camera.inputs["Vector"])
            scale = node("ShaderNodeVectorMath", "MR Env Normal Scale")
            scale.operation = "SCALE"
            scale.inputs["Scale"].default_value = 0.5
            links.new(camera.outputs["Vector"], scale.inputs[0])
            bias = node("ShaderNodeVectorMath", "MR Env Coordinate Bias")
            bias.operation = "ADD"
            bias.inputs[1].default_value = (0.5, 0.5, 0)
            links.new(scale.outputs["Vector"], bias.inputs[0])
            links.new(bias.outputs["Vector"], env_texture.inputs["Vector"])
            term = node("ShaderNodeMixRGB", "MR Environment Color Times Current Alpha")
            term.blend_type = "MULTIPLY"
            term.inputs[0].default_value = 1
            links.new(env_texture.outputs["Color"], term.inputs[1])
            links.new(base_alpha, term.inputs[2])
            # A separate unlit contribution approximates CURRENT + A*ENV.
            # It is not physical emission or an additive framebuffer blend.
            links.new(term.outputs[0], shader.inputs["Emission Color"])
            shader.inputs["Emission Strength"].default_value = 1
            multiply = node("ShaderNodeMath", "MR Stage 1 Alpha")
            multiply.operation = "MULTIPLY"
            links.new(base_alpha, multiply.inputs[0])
            links.new(env_texture.outputs["Alpha"], multiply.inputs[1])
            base_alpha = multiply.outputs[0]
        material["mr_dxt_has_nonopaque_alpha"] = transparent
        if semantics.alpha_enabled:
            if semantics.alpha_mode == "ALPHA_TEST":
                clip = node("ShaderNodeMath", "MR Alpha Greater Than 128")
                clip.operation = "GREATER_THAN"
                clip.inputs[1].default_value = 128 / 255
                links.new(base_alpha, clip.inputs[0])
                base_alpha = clip.outputs[0]
            links.new(base_alpha, shader.inputs["Alpha"])
            if hasattr(material, "surface_render_method"):
                material.surface_render_method = "DITHERED"
            elif hasattr(material, "blend_method"):
                material.blend_method = "CLIP" if semantics.alpha_mode == "ALPHA_TEST" else "BLEND"
                if hasattr(material, "alpha_threshold"):
                    material.alpha_threshold = 128 / 255
            if hasattr(material, "use_transparency_overlap"):
                material.use_transparency_overlap = True
            material["mr_alpha_preview"] = "ALPHATEST_APPROXIMATION" if semantics.alpha_mode == "ALPHA_TEST" else "ALPHABLEND_APPROXIMATION"
        else:
            material["mr_alpha_preview"] = "OPAQUE_FLAGS_IGNORE_TEXTURE_ALPHA"
        self.materials[key] = material
        return material

    def _material_for_unscoped_draw(self, draw):
        primary = next(
            (slot.value for slot in draw.texture_slots if slot.value.casefold() != "null"),
            None,
        )
        source = self.resolver.resolve_texture(primary) if primary and self.load_textures else None
        if primary and self.load_textures and source is None:
            self.warnings.append(f"draw {draw.draw_index}: missing texture {primary!r}")

        helper_name = draw.texture_slots[1].value if len(draw.texture_slots)>1 else "Null"
        helper_source = self.resolver.resolve_texture(helper_name) if self.load_textures and helper_name.casefold()!="null" else None
        show_helper = bool(helper_source and draw.unknown_0x24 & 4 and helper_name.casefold() in {"whitepaint-tga", "chrome-tga"})
        image = None
        transparent = False
        if source is not None:
            image, transparent = self._decode_image(source)
        # Serialized byte order was traced through the executable loader:
        # flag byte 0 -> runtime +0x22, byte 1 -> +0x23.
        alpha_enabled = bool(draw.flags_0x20[0])
        alpha_test = bool(draw.flags_0x20[1])
        slots = tuple(slot.value for slot in draw.texture_slots)
        key = (str(source.resolve()).casefold() if source else None,
               slots, draw.flags_0x20, draw.unknown_0x24)
        if key in self.materials:
            return self.materials[key]

        label = normalize_texture_value(primary) if primary else "neutral"
        material = bpy.data.materials.new(name=f"MR Preview - {_safe(label)}")
        material.use_nodes = True
        material.diffuse_color = (1.0, 1.0, 1.0, 1.0)
        material["mr_preview_semantics"] = "R4D1_PRIMARY_SLOT_ALPHA_ONLY"
        material["mr_texture_slots_json"] = json.dumps(slots)
        material["mr_serialized_flags_0x20_hex"] = draw.flags_0x20.hex()
        material["mr_serialized_texture_mask"] = draw.unknown_0x24
        material["mr_runtime_alpha_enabled"] = alpha_enabled
        material["mr_runtime_alpha_test"] = alpha_test
        material["mr_secondary_stage_preview"] = (
            "APPROXIMATE_ENV_NORMALS" if show_helper
            else "NOT_SHOWN"
        )
        material["mr_environment_helper"] = helper_name
        material["mr_environment_confidence"] = (
            "CONFIRMED_BY_RUNTIME_M1_M3" if helper_name.casefold() in
            {"whitepaint-tga", "chrome-tga"} else "CONFIRMED_BY_EXECUTABLE_PATH"
        )
        material["mr_primary_texture_slot"] = primary or "Null"
        material["mr_runtime_blending_known"] = True
        material["mr_preview_source_slot"] = next(
            (slot.slot for slot in draw.texture_slots if slot.value.casefold() != "null"), -1
        )
        nodes = material.node_tree.nodes
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
        if image is not None:
            image_node = nodes.new("ShaderNodeTexImage")
            image_node.image = image
            image_node.interpolation = "Linear"
            base_color = image_node.outputs["Color"]
            if show_helper:
                helper_image,_ = self._decode_image(helper_source)
                helper_node=nodes.new("ShaderNodeTexImage")
                helper_node.image=helper_image
                coordinates=nodes.new("ShaderNodeTexCoord")
                material.node_tree.links.new(coordinates.outputs["Normal"],helper_node.inputs["Vector"])
                combine=nodes.new("ShaderNodeMixRGB")
                combine.blend_type="ADD"
                combine.inputs[0].default_value=(0.55 if "chrome" in helper_name.casefold() else 0.25)
                material.node_tree.links.new(base_color,combine.inputs[1])
                material.node_tree.links.new(helper_node.outputs["Color"],combine.inputs[2])
                base_color=combine.outputs["Color"]
            material.node_tree.links.new(base_color, shader.inputs["Base Color"])
            if alpha_enabled:
                material.node_tree.links.new(image_node.outputs["Alpha"], shader.inputs["Alpha"])
            material["mr_dxt_source"] = str(source.resolve())
            material["mr_dxt_sha256"] = image.get("mr_dxt_sha256")
            material["mr_png_row_policy"] = PNG_ROWS_FLIP_VERTICAL
        if alpha_enabled:
            if alpha_test and hasattr(material, "blend_method"):
                material.blend_method = "CLIP"
                if hasattr(material, "alpha_threshold"):
                    material.alpha_threshold = 128 / 255
            elif hasattr(material, "surface_render_method"):
                material.surface_render_method = "DITHERED"
            elif hasattr(material, "blend_method"):
                material.blend_method = "BLEND"
            material.use_transparency_overlap = False
            material["mr_alpha_preview"] = (
                "ALPHATEST_APPROXIMATION" if alpha_test else "ALPHABLEND_APPROXIMATION"
            )
            material["mr_dxt_has_nonopaque_alpha"] = transparent
        self.materials[key] = material
        return material
