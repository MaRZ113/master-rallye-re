"""Frontend model frame: put the wheels of complete.dx on Y = 0.

Retail complete.dx (the Vehicle Select / Quick Race showroom model) is the car.dx body raised so that the lowest wheel
point is at Y = 0 (megane: car.dx min Y -0.246, complete.dx min Y 0.001 with the body raised 0.461 m; same for Forester,
Jump, Kangoo, Navara, WildCat). The Evo 2 and GT imports already follow this. Imports that wrote complete.dx in the
car.dx frame (RCX set 1-2: wheels down to -0.34 m) sit visibly low in the frontend (owner, 2026-11-16).

lift_complete_dx() shifts every render vertex by -min(Y) and recomputes the marker-1339 bounds exactly like
scene_dx_writer.write_scene_dx(); collision bytes are kept.
"""
from __future__ import annotations
import struct
from .dx import parse_dx_bytes
from .bounds import compute_bounds1339, replace_bounds1339

GROUND_TOLERANCE = 0.005          # metres; retail complete.dx minima are within +-0.005 of zero


def lift_complete_dx(raw: bytes) -> tuple[bytes, float]:
    model = parse_dx_bytes(raw)
    if not model.diagnostics.validated:
        raise ValueError('complete.dx does not validate')
    vd = model.vertices
    count = len(vd.positions)
    low = min(p[1] for p in vd.positions)
    if abs(low) <= GROUND_TOLERANCE:
        return raw, 0.0
    dy = -low
    out = bytearray(raw)
    at = vd.position_offset
    for i in range(count):
        o = at + 12 * i + 4
        (y,) = struct.unpack_from('<f', out, o)
        struct.pack_into('<f', out, o, y + dy)
    model2 = parse_dx_bytes(bytes(out))
    bounds = compute_bounds1339(model2.vertices.positions, model2.collision.convex_hull, offset=model2.collision.unparsed_offset)
    result = replace_bounds1339(bytes(out), bounds, footer_offset=model2.collision.unparsed_offset)
    after = parse_dx_bytes(result)
    if not after.diagnostics.validated or len(after.physical_draws) != len(model.physical_draws):
        raise ValueError('lifted complete.dx does not validate')
    if result[after.trailing.offset:after.collision.unparsed_offset] != raw[model.trailing.offset:model.collision.unparsed_offset]:
        raise ValueError('collision bytes changed')
    if abs(min(p[1] for p in after.vertices.positions)) > GROUND_TOLERANCE:
        raise ValueError('lift did not reach the ground plane')
    return result, dy
