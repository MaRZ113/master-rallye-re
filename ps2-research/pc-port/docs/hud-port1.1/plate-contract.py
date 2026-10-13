"""Bounded original UI source decoding; no renderer or process mutation."""
import math
import struct

EXE_SHA = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
SPEED_DIAL_VTABLE = 0x690F38
CHECKPOINT = 0x56D65D

def bounded_span(begin, end, stride, maximum):
    if begin < 0x10000 or end < begin or end > 0x7FFFFFFF:
        raise ValueError('invalid original vector span')
    size = end - begin
    if size % stride or size // stride > maximum:
        raise ValueError('unaligned or excessive original vector span')
    return size // stride

def decode_triangle(payload):
    if len(payload) != 0x34:
        raise ValueError('original triangle must contain 52 bytes')
    texture_id = struct.unpack_from('<I', payload)[0]
    uv = struct.unpack_from('<6f', payload, 4)
    xy = struct.unpack_from('<6i', payload, 0x1C)
    if not all(math.isfinite(v) for v in uv):
        raise ValueError('non-finite original UV')
    return {'texture_resource_id': texture_id,
            'uv': [list(uv[n:n+2]) for n in (0,2,4)],
            'source_xy': [list(xy[n:n+2]) for n in (0,2,4)]}

def original_vertices(triangle, row_xyz, z_value):
    if not all(math.isfinite(v) for v in (*row_xyz, z_value)):
        raise ValueError('non-finite original placement')
    return [[float(x) + row_xyz[0] - .5, row_xyz[1] + .5 - float(y), z_value]
            for x, y in triangle['source_xy']]

def qualify(registers, owner, packet, ai_vtable, key_values, selected_index,
            selected_subimage, bank_begin, bank_end, triangle_begin, triangle_end):
    if registers['eip'] != CHECKPOINT or ai_vtable != SPEED_DIAL_VTABLE:
        raise ValueError('wrong original consumer or class')
    if not owner or not packet or key_values != [0] or selected_index < 0:
        raise ValueError('ambiguous owner or non-plate selection')
    count = bounded_span(bank_begin, bank_end, 0x10, 64)
    if selected_index >= count or selected_subimage != bank_begin + selected_index * 0x10:
        raise ValueError('key-to-subimage correspondence missing')
    bounded_span(triangle_begin, triangle_end, 0x34, 2)
    if registers['esi'] != triangle_begin:
        raise ValueError('checkpoint is not first original plate triangle')
    return {'source_mapping': 'CLASS_PACKET_KEY0_SUBIMAGE_CONFIRMED_AT_DECLARED_PAUSE',
            'replacement_authorized': False}
