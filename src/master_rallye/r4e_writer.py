"""Conservative R4E same-topology DX attribute and fixed material-state patches."""
from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .dx import parse_dx_bytes
from .dx_writer import ByteRange, audit_binary_diff, patch_dx_positions
from .errors import DxWriteError

R4F_REQUIRED = "REQUIRES_R4F_TOPOLOGY_WRITER"
CATEGORIES = {
    "NO_CHANGE", "TEXTURE_CONTENT_ONLY", "POSITION_ONLY",
    "SAME_TOPOLOGY_GEOMETRY_ATTRIBUTES", "SAFE_MATERIAL_STATE_CHANGE",
    "COLLISION_TRANSLATION", "MULTIPLE_SAFE_CHANGES", "TOPOLOGY_CHANGED",
    "UNSUPPORTED",
}


@dataclass(frozen=True)
class FieldChange:
    field: str
    identity: int
    offset: int
    old_hex: str
    new_hex: str

    def to_dict(self):
        return vars(self).copy()


@dataclass(frozen=True)
class AttributePatch:
    data: bytes
    source_sha256: str
    output_sha256: str
    changes: tuple[FieldChange, ...]
    diff: object
    classification: str
    collision_sha256: str | None
    topology_sha256: str

    def to_dict(self):
        return {
            "source_sha256": self.source_sha256,
            "output_sha256": self.output_sha256,
            "classification": self.classification,
            "changes": [change.to_dict() for change in self.changes],
            "diff": self.diff.to_dict(),
            "collision_sha256": self.collision_sha256,
            "topology_sha256": self.topology_sha256,
        }


def aggregate_corners(
    loop_vertex_ids: Sequence[int],
    loop_values: Sequence[Sequence[float]],
    source_values: Sequence[Sequence[float]],
    *,
    field: str,
    tolerance: float = 1.0e-6,
) -> tuple[tuple[float, ...], ...]:
    """Map Blender corner values to source vertices; never average a new seam."""
    if len(loop_vertex_ids) != len(loop_values):
        raise DxWriteError(f"{field}: loop/value count mismatch")
    if not math.isfinite(tolerance) or tolerance < 0:
        raise DxWriteError("invalid corner tolerance")
    output = [tuple(float(x) for x in value) for value in source_values]
    seen = {}
    for vertex_id, value in zip(loop_vertex_ids, loop_values):
        index = int(vertex_id)
        if not 0 <= index < len(output):
            raise DxWriteError(f"{field}: source vertex ID {index} out of range")
        candidate = tuple(float(x) for x in value)
        if len(candidate) != len(output[index]) or not all(math.isfinite(x) for x in candidate):
            raise DxWriteError(f"{field}: invalid corner value at vertex {index}")
        first = seen.get(index)
        if first is not None and any(abs(a-b) > tolerance for a,b in zip(first,candidate)):
            raise DxWriteError(f"{R4F_REQUIRED}: {field} corner divergence at source vertex {index}")
        seen[index] = candidate
    for index, value in seen.items():
        output[index] = value
    return tuple(output)


def classify_edit(
    *,
    topology_valid: bool = True,
    position=False, normal=False, uv=False, color=False,
    material=False, texture=False, collision=False, unsupported=False,
) -> str:
    if not topology_valid:
        return "TOPOLOGY_CHANGED"
    if unsupported:
        return "UNSUPPORTED"
    families = sum(bool(x) for x in (position, normal, uv, color, material, texture, collision))
    if families == 0:
        return "NO_CHANGE"
    if families > 1:
        return "MULTIPLE_SAFE_CHANGES"
    if texture:
        return "TEXTURE_CONTENT_ONLY"
    if position:
        return "POSITION_ONLY"
    if normal or uv or color:
        return "SAME_TOPOLOGY_GEOMETRY_ATTRIBUTES"
    if material:
        return "SAFE_MATERIAL_STATE_CHANGE"
    return "COLLISION_TRANSLATION"


def _pack_floats(value, width, label):
    candidate = tuple(float(x) for x in value)
    if len(candidate) != width or not all(math.isfinite(x) for x in candidate):
        raise DxWriteError(f"{label}: expected {width} finite values")
    try:
        return struct.pack("<" + "f"*width, *candidate)
    except (OverflowError, struct.error) as error:
        raise DxWriteError(f"{label}: float32 overflow") from error


def _topology_signature(model):
    digest = hashlib.sha256()
    digest.update(struct.pack("<2I", model.vertex_count, len(model.local_indices)))
    digest.update(struct.pack("<" + "H"*len(model.local_indices), *model.local_indices))
    for draw in model.physical_draws:
        digest.update(struct.pack("<5I", draw.vertex_base, draw.local_vertex_max, draw.index_start, draw.index_count, draw.tag))
        digest.update(draw.record_path.encode("ascii"))
    if model.global_index_table:
        for value in model.global_index_table.indices:
            digest.update(struct.pack("<I", value))
    return digest.hexdigest()


def patch_dx_attributes(
    template: bytes,
    *,
    positions=None,
    normals=None,
    uv_sets=None,
    colors=None,
    material_alpha: dict[int, bool] | None = None,
    material_env: dict[int, bool] | None = None,
    source="<template>",
    safe_bounds=True,
) -> AttributePatch:
    original = parse_dx_bytes(template, source=source)
    if not original.diagnostics.validated:
        raise DxWriteError("source DX geometry is not validated")
    work = bytearray(template)
    changes = []
    ranges = []

    def patch(field, identity, offset, encoded):
        old = template[offset:offset+len(encoded)]
        if len(old) != len(encoded):
            raise DxWriteError(f"{field}: patch outside template")
        if old == encoded:
            return
        work[offset:offset+len(encoded)] = encoded
        changes.append(FieldChange(field, identity, offset, old.hex(), encoded.hex()))
        ranges.append(ByteRange(offset, offset+len(encoded)))

    if positions is not None:
        position_result = patch_dx_positions(template, positions, source=source, safe_bounds=safe_bounds)
        for change in position_result.changes:
            offset = change.source_offset
            patch("position", change.vertex_index, offset, position_result.data[offset:offset+12])
    if normals is not None:
        normals = tuple(normals)
        if len(normals) != original.vertex_count:
            raise DxWriteError("normal count differs from source vertex count")
        for index, value in enumerate(normals):
            if value is None:
                continue
            patch("normal", index, original.vertices.normal_offset+index*12, _pack_floats(value,3,f"normal {index}"))
    if uv_sets is not None:
        uv_sets = tuple(tuple(values) for values in uv_sets)
        if len(uv_sets) != len(original.uv_sets):
            raise DxWriteError("UV set count differs from source")
        for set_index, (incoming, source_set) in enumerate(zip(uv_sets, original.uv_sets)):
            if len(incoming) != original.vertex_count:
                raise DxWriteError(f"UV{set_index}: vertex count differs")
            for index, value in enumerate(incoming):
                patch(f"UV{set_index}", index, source_set.offset+index*8, _pack_floats(value,2,f"UV{set_index} vertex {index}"))
    if colors is not None:
        if isinstance(colors, (bytes,bytearray)):
            raw = bytes(colors)
        else:
            rows = tuple(colors)
            if len(rows) != original.vertex_count:
                raise DxWriteError("color count differs")
            try:
                raw = bytes(component for row in rows for component in row)
            except (ValueError, TypeError) as error:
                raise DxWriteError("color channels must be raw byte values") from error
            if len(raw) != original.vertex_count*4:
                raise DxWriteError("each source color must have four raw channels")
        if len(raw) != len(original.vertices.colors):
            raise DxWriteError("color byte count differs")
        for index in range(original.vertex_count):
            patch("vertex_color_raw",index,original.vertices.color_offset+index*4,raw[index*4:index*4+4])
    draws = original.physical_draws
    for draw_id, enabled in (material_alpha or {}).items():
        if type(enabled) is not bool or not 0 <= draw_id < len(draws):
            raise DxWriteError("invalid alpha edit")
        draw = draws[draw_id]
        if draw.draw_index != draw_id or draw.tag not in (2, 7, 8):
            raise DxWriteError("alpha edit requires a physical vehicle draw identity")
        if draw.flags_0x20[1] != 0:
            raise DxWriteError("alpha-test material is experimental and cannot be edited here")
        patch("material_alpha_enable",draw_id,draw.core_offset+0x20,bytes([int(enabled)]))
    for draw_id, enabled in (material_env or {}).items():
        if type(enabled) is not bool or not 0 <= draw_id < len(draws):
            raise DxWriteError("invalid environment edit")
        draw=draws[draw_id]
        if draw.draw_index != draw_id or draw.tag not in (2, 7, 8):
            raise DxWriteError("environment edit requires a physical vehicle draw")
        if len(draw.texture_slots)<2 or draw.texture_slots[1].value.casefold()=="null":
            raise DxWriteError("cannot enable environment feature without existing slot-1 helper")
        if draw.unknown_0x24 & ~7:
            raise DxWriteError("unrecognized feature-mask bits: preserve without editing")
        new_mask = (draw.unknown_0x24 | 4) if enabled else (draw.unknown_0x24 & ~4)
        patch("material_env_bit",draw_id,draw.core_offset+0x24,struct.pack("<I",new_mask))
    output=bytes(work)
    diff=audit_binary_diff(template,output,ranges)
    if not diff.valid:
        raise DxWriteError("unauthorized byte difference")
    parsed=parse_dx_bytes(output,source=f"{source} patched")
    if not parsed.diagnostics.validated or parsed.diagnostics.warnings != original.diagnostics.warnings:
        raise DxWriteError("reparse validation changed")
    if _topology_signature(parsed)!=_topology_signature(original):
        raise DxWriteError(f"{R4F_REQUIRED}: render topology changed")
    if output[original.collision.offset:original.collision.end_offset] != template[original.collision.offset:original.collision.end_offset]:
        raise DxWriteError("collision bytes changed")
    if parsed.trailing.data != original.trailing.data:
        raise DxWriteError("trailing bytes changed")
    if positions is None and parsed.vertices.positions != original.vertices.positions:
        raise DxWriteError("unexpected position edit")
    if normals is None and parsed.vertices.normals != original.vertices.normals:
        raise DxWriteError("unexpected normal edit")
    if uv_sets is None and [x.values for x in parsed.uv_sets] != [x.values for x in original.uv_sets]:
        raise DxWriteError("unexpected UV edit")
    if colors is None and parsed.vertices.colors != original.vertices.colors:
        raise DxWriteError("unexpected color edit")
    old_draws=original.physical_draws
    for idx,(before,after) in enumerate(zip(old_draws,parsed.physical_draws)):
        if before.texture_tuple != after.texture_tuple or before.flags_0x20[1:] != after.flags_0x20[1:] or before.unknown_0x14 != after.unknown_0x14 or before.unknown_0x18 != after.unknown_0x18:
            raise DxWriteError(f"unknown draw field changed at {idx}")
        if idx not in (material_alpha or {}) and before.flags_0x20 != after.flags_0x20:
            raise DxWriteError(f"unexpected material flags at {idx}")
        if idx not in (material_env or {}) and before.unknown_0x24 != after.unknown_0x24:
            raise DxWriteError(f"unexpected material feature mask at {idx}")
    field_set={x.field for x in changes}
    classification=classify_edit(
        position="position" in field_set, normal="normal" in field_set,
        uv=any(x.startswith("UV") for x in field_set),
        color="vertex_color_raw" in field_set,
        material=any(x.startswith("material_") for x in field_set),
    )
    collision_hash=hashlib.sha256(template[original.collision.offset:original.collision.end_offset]).hexdigest()
    return AttributePatch(output,hashlib.sha256(template).hexdigest(),hashlib.sha256(output).hexdigest(),tuple(changes),diff,classification,collision_hash,_topology_signature(original))


def write_dx_attributes(source_path: Path, output_path: Path, *, expected_source_sha256: str, **changes):
    source_path=Path(source_path).resolve()
    output_path=Path(output_path).resolve()
    if source_path==output_path:
        raise DxWriteError("refusing to overwrite source DX")
    data=source_path.read_bytes()
    if hashlib.sha256(data).hexdigest().casefold()!=expected_source_sha256.casefold():
        raise DxWriteError("source template SHA-256 mismatch")
    patch=patch_dx_attributes(data,source=str(source_path),**changes)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_bytes(patch.data)
    return patch
