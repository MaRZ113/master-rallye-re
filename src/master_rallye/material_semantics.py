"""Vehicle draw material semantics from the traced DX loader and D3D8 shader path.

Unknown stage bindings and game-observed outcomes remain explicit null values.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
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
class MaterialSemantics:
    """Static DX-derived state; environment_mapping means feature capability.

    Runtime Reflections/DetailPasses settings can still suppress a shader stage.
    Null stage bindings are intentional when the exact resource-to-stage path is
    not established.
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

    @classmethod
    def from_draw(cls, draw: Any) -> "MaterialSemantics":
        alpha_enabled = bool(draw.flags_0x20[0])
        alpha_test = bool(draw.flags_0x20[1])
        alpha_mode = ("ALPHA_TEST" if alpha_test else "ALPHA_BLEND") if alpha_enabled else "OPAQUE"
        return cls(
            texture_slots=tuple(slot.value for slot in draw.texture_slots),
            serialized_draw_flags=draw.flags_0x20.hex(),
            serialized_texture_mask=draw.unknown_0x24,
            alpha_enabled=alpha_enabled,
            alpha_mode=alpha_mode,
            alpha_mode_confidence="CONFIRMED_BY_EXECUTABLE",
            environment_mapping=bool(draw.unknown_0x24 & 4),
            environment_mapping_confidence="CONFIRMED_BY_EXECUTABLE",
            texture_stage_mapping=None,
            texture_combine_operations=None,
            runtime_feature_mask=draw.unknown_0x24,
            runtime_shader_family=None,
            d3d8_render_states=(
                {"ALPHABLENDENABLE": True, "ALPHATESTENABLE": False,
                 "ZWRITEENABLE": False, "SRCBLEND": "SRCALPHA",
                 "DESTBLEND": "INVSRCALPHA"} if alpha_mode == "ALPHA_BLEND"
                else {"ALPHABLENDENABLE": False, "ALPHATESTENABLE": True,
                      "ZWRITEENABLE": True, "ALPHAFUNC": "GREATER",
                      "ALPHAREF": 128} if alpha_mode == "ALPHA_TEST"
                else {"ALPHABLENDENABLE": False, "ALPHATESTENABLE": False,
                      "ZWRITEENABLE": True}
            ),
            d3d8_texture_stage_states=None,
            unknown_fields={
                "unknown_0x14": draw.unknown_0x14,
                "unknown_0x18": draw.unknown_0x18,
                "unknown_0x1c_float": draw.unknown_0x1c_float,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["texture_slots"] = list(self.texture_slots)
        return value
