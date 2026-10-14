"""Exact post-tree tag102 adapter; reuse the proven visual reader unchanged.

0x38fac0 dispatches102 to0x3947b0, reading two float32 values, then resumes
top-level tag reading. This is a cylinder auxiliary, not a visual node or LOD.
No original input is edited. A private four-byte normalization view lets the
existing strict tree parser finish; the returned Scene retains original bytes.
"""
from pathlib import Path
import math
import struct
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'ps2-research/tools'))
import reflection_runtime as r
import tngtool as t
import water_runtime as w


def failure_boundary(error):
    trace = error.__traceback__
    while trace:
        if trace.tb_frame.f_code.co_name == 'decode_scene':
            return trace.tb_frame.f_locals.get('end')
        trace = trace.tb_next
    return None


def decode_complete(payload):
    """Return (Scene, trailer metadata), failing closed outside proved layouts.

    Tag101 trees remain accepted through the existing reader; their complete
    collision trailer is opaque. Selected standalone sentinel requires exact
    EOF. New tag102 support accepts exactly two finite source floats followed
    by the original -1 sentinel at EOF; no other record is skipped.
    """
    try:
        scene = r.decode_vehicle(payload)
        return scene, {'tag': 101, 'offset': scene.end,
            'kind': 'CONVEX_AUXILIARY_TRAILER_NOT_DECODED',
            'unparsed_bytes': len(payload) - scene.end - 4}
    except t.FormatError as error:
        at = failure_boundary(error)
        if at is None or at + 4 > len(payload):
            raise
        tag = struct.unpack_from('<I', payload, at)[0]
        if tag == 0xffffffff and at + 4 == len(payload):
            scene = w.decode_scene(payload, {7:r._named_node, 8:r._indexed_node},
                                   terminator=0xffffffff)
            return scene, {'tag': tag, 'offset': at, 'kind': 'EXACT_EOF_SENTINEL'}
        if tag != 102:
            raise
        if len(payload) - at != 16 or struct.unpack_from('<I', payload, at+12)[0] != 0xffffffff:
            raise t.FormatError('Tag102 requires two floats and exact EOF sentinel') from error
        values = struct.unpack_from('<2f', payload, at+4)
        if not all(math.isfinite(v) for v in values):
            raise t.FormatError('Non-finite tag102 cylinder parameters') from error
        # The visual subtree has already ended at at, independently of tag102.
        # Only its delimiter changes in this temporary host parsing view.
        view = payload[:at] + struct.pack('<I',101) + payload[at+4:]
        scene = r.decode_vehicle(view)
        if scene.end != at:
            raise t.FormatError('Tag102 normalization altered tree boundary')
        scene.payload = payload
        return scene, {'tag':102, 'offset':at,
            'kind':'POST_TREE_WHEEL_CYLINDER_AUXILIARY',
            'values': list(values), 'value_fields':['cylinder+0x14','cylinder+0x18'],
            'consumer':'0x003947b0', 'visual_owner':'0x003900f0 -> 0x00391d38',
            'sentinel_offset':at+12, 'unparsed_bytes':0,
            'runtime_rule':'Model+0x38 assigned only when model name contains wheel; otherwise destroy cylinder',
            'not_used_for_visual_geometry':True}
