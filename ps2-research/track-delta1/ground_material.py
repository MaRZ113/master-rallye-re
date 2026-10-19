"""Ground material helpers (TRACK-GROUND1).

Native PC ground (course DX draw with texture tuple (base, 'Null', 'noise-tga')): stage 0 TEXTURE x DIFFUSE, stage 1 CURRENT x TEXTURE MODULATE2X with
noise-tga on the second UV set (research: pc-port/docs/ground-detail1). Generic DX models have one UV set and two unused texture slots.
`two_uv_noise_template()` builds an EXPERIMENTAL generic-DX template with a second UV array and slot 2 = noise-tga so that converted ground can carry a
noise UV; whether the engine then selects the noise stage for a model Egg is a HYPOTHESIS that only a runtime A/B can decide.
"""
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'src'))
from master_rallye.dx import parse_dx_bytes  # noqa: E402

NOISE_SLOT = b'noise-tga'


def two_uv_noise_template(template):
    """Template DX with slot 2 renamed to noise-tga and a duplicated UV array (uv count 2). Returns bytes; raises when the result does not parse."""
    m = parse_dx_bytes(template)
    draw = m.physical_draws[0]
    slot = draw.texture_slots[2]
    if slot.value != 'Null':
        raise ValueError('template slot 2 is not Null')
    data = bytearray(template)
    data[slot.length_offset:slot.data_offset + len(slot.raw)] = struct.pack('<I', len(NOISE_SLOT)) + NOISE_SLOT
    m2 = parse_dx_bytes(bytes(data))
    count_offset = m2.uv_count_offset
    uv = m2.uv_sets[0]
    size = len(uv.values) * 8
    block = bytes(data[uv.offset:uv.offset + size])
    out = bytearray(data[:uv.offset + size]) + block + bytes(data[uv.offset + size:])
    out[count_offset:count_offset + 4] = struct.pack('<I', 2)
    m3 = parse_dx_bytes(bytes(out))
    if len(m3.uv_sets) != 2 or m3.physical_draws[0].texture_tuple[2] != 'noise-tga':
        raise ValueError('2-UV template did not parse as expected')
    return bytes(out)
