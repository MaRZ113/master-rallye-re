"""Vehicle draw material semantics from the traced DX loader and D3D8 shader path.

Read-only projection, never a writer input. Evidence: research/r-mat1/.
Shader setup writes are distinguished from subsequent instance overrides.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def texture_presence_mask(slots: tuple[str, ...] | list[str], flag_byte_2: int) -> int:
    if len(slots) != 3:
        raise ValueError("observed vehicle draw has exactly three texture slots")
    if not 0 <= flag_byte_2 <= 255:
        raise ValueError("flag byte must be unsigned")
    present = lambda value: value.strip().casefold() != "null"
    return (int(present(slots[0])) | (2 if flag_byte_2 else 0)
            | (4 if present(slots[1]) else 0))


@dataclass(frozen=True)
class MaterialTextureStageSemantics:
    serialized_slot: int
    runtime_handle_offset: str
    d3d_stage: int | None
    role: str
    bound: bool | None
    confidence: str = "CONFIRMED_BY_EXE"


@dataclass(frozen=True)
class MaterialSemantics:
    """Static DX-derived state; environment_mapping means feature capability.

    Runtime Reflections/DetailPasses settings can still suppress a shader stage.
    The default projection assumes Reflections ON. An explicit OFF projection
    retains raw slots and mask while suppressing the environment stage.
    """
    texture_slots: tuple[str, ...]
    serialized_draw_flags: str
    serialized_texture_mask: int
    alpha_enabled: bool | None
    alpha_mode: str
    alpha_mode_confidence: str
    environment_mapping: bool | None
    environment_mapping_confidence: str
    texture_stage_mapping: dict[str, Any] | None
    texture_combine_operations: dict[str, Any] | None
    runtime_feature_mask: int | None
    runtime_shader_family: str | None
    d3d8_render_states: dict[str, Any] | None
    d3d8_texture_stage_states: dict[str, Any] | None
    unknown_fields: dict[str, Any]
    feature_semantics: dict[str, Any] = field(default_factory=dict)
    runtime_flag_semantics: dict[str, Any] = field(default_factory=dict)
    render_state_scope: dict[str, Any] = field(default_factory=dict)
    null_slot_behavior: dict[str, Any] = field(default_factory=dict)
    runtime_shader_family_reflections_off: str | None = None
    vertex_diffuse_enabled: bool = False
    source_uv_enabled: bool = False
    reflections_enabled: bool = True
    classification: str = "UNKNOWN"
    unknown_reasons: tuple[str, ...] = ()

    @classmethod
    def from_draw(cls, draw: Any, *, reflections: bool = True) -> "MaterialSemantics":
        if len(draw.flags_0x20) != 4:
            raise ValueError("material requires four serialized flag bytes")
        alpha_enabled = bool(draw.flags_0x20[0])
        alpha_test = bool(draw.flags_0x20[1])
        alpha_mode = ("ALPHA_TEST" if alpha_test else "ALPHA_BLEND") if alpha_enabled else "OPAQUE"
        slots = tuple(slot.value for slot in draw.texture_slots)
        slot = lambda index: slots[index] if index < len(slots) else "Null"
        present = lambda index: slot(index).strip().casefold() != "null"
        mask = draw.unknown_0x24
        env = bool(mask & 4)
        stage0_bound = bool(mask & 1) and present(0)
        stage1_bound = env and reflections and present(1)
        reasons = []
        if mask & ~7:
            reasons.append("FEATURES_OUTSIDE_RETAIL_VEHICLE_MASK_0x07")
        if not mask & 3:
            reasons.append("NO_OBSERVED_BASE_FAMILY_SELECTOR")
        if len(slots) > 3 or present(2):
            reasons.append("SLOT2_USE_OUTSIDE_OBSERVED_VEHICLE_CORPUS")
        if draw.unknown_0x18:
            reasons.append("OPTIONAL_RUNTIME_VARIANT_OBJECT")
        suffix = "_alpha" if alpha_mode == "ALPHA_BLEND" else "_alphatest" if alpha_mode == "ALPHA_TEST" else ""
        family_off = "shader/base" + suffix if not reasons else None
        family = "shader/base" + ("_env" if env and reflections else "") + suffix if not reasons else None
        states = None
        if family:
            states = {"LIGHTING": False, "ZENABLE": True,
                      "ZWRITEENABLE": True if env and reflections else alpha_mode != "ALPHA_BLEND",
                      "ALPHABLENDENABLE": alpha_mode == "ALPHA_BLEND",
                      "SRCBLEND": "SRCALPHA", "DESTBLEND": "INVSRCALPHA",
                      "ALPHATESTENABLE": True if alpha_mode == "ALPHA_TEST" else
                          False if alpha_mode == "ALPHA_BLEND" and not (env and reflections) else None}
            if alpha_mode == "ALPHA_TEST":
                states.update(ALPHAFUNC="GREATER", ALPHAREF=128)
        stage0 = {"COLOROP": "MODULATE", "COLORARG1": "TEXTURE", "COLORARG2": "DIFFUSE",
                  "ALPHAOP": "MODULATE", "ALPHAARG1": "TEXTURE", "ALPHAARG2": "DIFFUSE",
                  "TEXCOORDINDEX": 0, "TEXTURETRANSFORMFLAGS": "DISABLE"}
        stage1 = ({"COLOROP": "MODULATEALPHA_ADDCOLOR", "COLORARG1": "CURRENT", "COLORARG2": "TEXTURE",
                   "ALPHAOP": "MODULATE", "ALPHAARG1": "CURRENT", "ALPHAARG2": "TEXTURE",
                   "TEXCOORDINDEX": 0x10000, "COORDINATE_GENERATION": "CAMERASPACENORMAL",
                   "TEXTURETRANSFORMFLAGS": "COUNT2", "TEXTURE_TRANSFORM": "NORMAL_XY_SCALE_0.5_BIAS_0.5"}
                  if env and reflections else {"COLOROP": "DISABLE", "ALPHAOP": "DISABLE"})
        return cls(
            texture_slots=tuple(slot.value for slot in draw.texture_slots),
            serialized_draw_flags=draw.flags_0x20.hex(),
            serialized_texture_mask=draw.unknown_0x24,
            alpha_enabled=alpha_enabled,
            alpha_mode=alpha_mode,
            alpha_mode_confidence="CONFIRMED_BY_EXECUTABLE",
            environment_mapping=bool(draw.unknown_0x24 & 4),
            environment_mapping_confidence="CONFIRMED_BY_EXECUTABLE",
            texture_stage_mapping={
                "slot0": MaterialTextureStageSemantics(0, "+0x38", 0 if family else None, "BASE",
                    stage0_bound if family else None, "CONFIRMED_BY_EXE" if family else "UNKNOWN"),
                "slot1": MaterialTextureStageSemantics(1, "+0x3C", 1 if family else None, "ENVIRONMENT",
                    stage1_bound if family else None, "CONFIRMED_BY_EXE" if family else "UNKNOWN"),
                "slot2": MaterialTextureStageSemantics(2, "+0x40", None,
                    "UNUSED_IN_OBSERVED_VEHICLES" if family else "UNKNOWN",
                    False if family else None, "CONFIRMED_BY_CORPUS" if family else "UNKNOWN"),
            },
            texture_combine_operations={"stage0_rgb": "texture0.rgb * diffuse.rgb",
                                        "stage0_alpha": "texture0.a * diffuse.a",
                                        "stage1_rgb": "current.rgb + current.a * texture1.rgb" if env and reflections else None,
                                        "stage1_alpha": "current.a * texture1.a" if env and reflections else None,
                                        "confidence": "CONFIRMED_BY_EXE"} if family else None,
            runtime_feature_mask=draw.unknown_0x24,
            runtime_shader_family=family,
            d3d8_render_states=states,
            d3d8_texture_stage_states={"stage0": stage0, "stage1": stage1} if family else None,
            unknown_fields={
                "unknown_0x14": draw.unknown_0x14,
                "unknown_0x18": draw.unknown_0x18,
                "unknown_0x1c_float": draw.unknown_0x1c_float,
            },
            feature_semantics={
                "0x01": {"enabled": bool(mask & 1), "role": "BASE_TEXTURE_HANDLE_GATE", "confidence": "CONFIRMED_BY_EXE"},
                "0x02": {"enabled": bool(mask & 2), "role": "BASE_FAMILY_SELECTOR", "confidence": "CONFIRMED_BY_EXE",
                         "byte2_correlation": "CONFIRMED_BY_CORPUS; not a second texture stage"},
                "0x04": {"enabled": env, "role": "ENVIRONMENT_WITH_REFLECTIONS_GATE", "confidence": "CONFIRMED_BY_EXE"},
            },
            runtime_flag_semantics={
                "byte0": {"offset": "+0x22", "role": "ALPHA_FAMILY_ENABLE", "confidence": "CONFIRMED_BY_EXE"},
                "byte1": {"offset": "+0x23", "role": "ALPHA_TEST_SELECTOR", "confidence": "CONFIRMED_BY_EXE"},
                "byte2": {"offset": "+0x20", "role": "PASS_VERTEX_DIFFUSE_ENABLE", "confidence": "CONFIRMED_BY_EXE",
                          "condition": "pass_flags & 1", "fvf_bit": 0x40},
                "byte3": {"offset": "+0x21", "role": "PASS_SOURCE_UV_ENABLE", "confidence": "CONFIRMED_BY_EXE", "components": 2},
            },
            render_state_scope={"scope": "EXPLICIT_SHADER_SETUP_WRITES", "confidence": "CONFIRMED_BY_EXE",
                                "unwritten_state_value": None,
                                "draw_overrides": {"ZENABLE": "instance+0xA8", "ZWRITEENABLE": "instance+0xA9"},
                                "evidence": "005867A0/00586150 -> 00576970"},
            null_slot_behavior={"promotion": False if family else None,
                                "binding_confidence": "CONFIRMED_BY_EXE" if family else "UNKNOWN",
                                "stage0_null": not stage0_bound,
                                "stage1_effective": stage1_bound and stage0_bound if family else None,
                                "cascade_rule": "NULL_TEXTURE_ARG1_TERMINATES_STAGES",
                                "cascade_confidence": "HIGH_CONFIDENCE_INFERENCE" if family else "UNKNOWN"},
            runtime_shader_family_reflections_off=family_off,
            vertex_diffuse_enabled=bool(draw.flags_0x20[2]), source_uv_enabled=bool(draw.flags_0x20[3]),
            reflections_enabled=reflections, classification="UNKNOWN" if reasons else "CLASSIFIED",
            unknown_reasons=tuple(reasons),
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["texture_slots"] = list(self.texture_slots)
        value["unknown_reasons"] = list(self.unknown_reasons)
        return value
