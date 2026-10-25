"""Conservative inline DX slot rebinding; no texture or topology mutation.

Qualified subset: diffuse slot 0, same ASCII encoded length, existing FEED
textures with identical dimensions, format and alpha. Other layouts fail closed.
"""
import re
from .dx import parse_dx_bytes
from .dxt import parse_dxt_bytes


def binding_patch(raw, draw_id, slot_id, target, texture_provider):
    model = parse_dx_bytes(raw)
    if not model.diagnostics.validated:
        raise ValueError('Invalid source DX')
    if slot_id != 0 or type(slot_id) is not int:
        raise ValueError('Only diffuse slot 0 is qualified; environment/effect slots are read-only')
    if not isinstance(target, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', target) or target.casefold() == 'null':
        raise ValueError('Target must be a local existing texture stem')
    draw = next((d for d in model.physical_draws if d.draw_index == draw_id), None)
    if draw is None:
        raise ValueError('Unknown physical draw ID')
    slot = draw.texture_slots[slot_id]
    if not slot.value or slot.value.casefold() == 'null':
        raise ValueError('Cannot enable a previously absent texture')
    encoded = target.encode('ascii')
    if len(encoded) != len(slot.raw):
        raise ValueError('This qualified writer requires the same encoded name length')
    start, end = slot.data_offset, slot.data_offset + len(slot.raw)
    for other in model.physical_draws:
        for descriptor in other.texture_slots:
            if other.draw_index == draw_id and descriptor.slot == slot_id:
                continue
            if max(start, descriptor.length_offset) < min(end, descriptor.data_offset + len(descriptor.raw)):
                raise ValueError('Shared or aliased native slot descriptor: assignment rejected')
    old, new = (parse_dxt_bytes(texture_provider(name)) for name in (slot.value, target))
    if (old.width, old.height, old.word_0x04) != (new.width, new.height, new.word_0x04):
        raise ValueError('Texture dimensions/native format must match')
    if old.bgra[3::4] != new.bgra[3::4]:
        raise ValueError('Texture alpha ownership differs; glass/decal/effect rebinding is not qualified')
    output = raw[:start] + encoded + raw[end:]
    after = parse_dx_bytes(output)
    if not after.diagnostics.validated or after.vertices != model.vertices:
        raise ValueError('Rebinding changed model structure')
    return output
