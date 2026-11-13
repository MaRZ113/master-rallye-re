"""Read a native car.dx into the meshes brake-lamp authoring needs (SDK required on sys.path).

Selection follows the native state switch: every ungrouped draw, the first case of every
state group, and for the ``blight`` group the ON case (case 2), which carries the OFF lamp
glass plus the ON layers. Lamp ON layers are recognised by their native material role
(``breaklightson``/``breaklightsonglow`` textures); the OFF glass by the ``blight`` case 1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import struct

import numpy as np

from .geometry import Mesh, merge

ON_CORE_TEXTURE = 'breaklightson-tga'
ON_GLOW_TEXTURE = 'breaklightsonglow-tga'


@dataclass
class DrawInfo:
    index: int
    texture: str
    case: tuple | None
    alpha: bool
    mesh: Mesh
    vertex_count: int
    triangle_count: int
    role: str  # body | off_glass | off_glass_on | on_core | on_glow | hidden_state


@dataclass
class CarModel:
    family: str
    sha256: str
    draws: list = field(default_factory=list)

    def role(self, *roles):
        return [d for d in self.draws if d.role in roles]

    def mesh(self, *roles) -> Mesh:
        return merge(d.mesh for d in self.role(*roles))

    def occluders(self) -> Mesh:
        """Opaque surfaces drawn while braking: body and any OFF glass the ON case keeps under the ON layers."""
        return merge(d.mesh for d in self.draws if d.role in ('body', 'off_glass_on') and not d.alpha)


def face_ids(positions, triangles):
    """Stable face IDs: sha256 of the three corner positions (float32 bits, sorted), the renderer's face hash.

    Independent of draw order, vertex order and winding, so a lens selection survives re-export.
    """
    out = []
    for t in triangles:
        pts = sorted(tuple(struct.unpack('<I', struct.pack('<f', 0.0 if v == 0 else float(v)))[0] for v in positions[i]) for i in t)
        out.append(hashlib.sha256(b''.join(struct.pack('<3I', *p) for p in pts)).hexdigest()[:16])
    return out


def load(raw: bytes, family: str) -> CarModel:
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.topology_writer import source_geometry
    from master_rallye.preview_scene import logical_cases
    m = parse_dx_bytes(raw)
    geometry = source_geometry(m)
    cases, _ = logical_cases(m)
    # Group labels: a tag-7 draw opens a group; logical_cases gives (group ordinal, case).
    labels = {}
    for d in m.physical_draws:
        if d.tag == 7 and cases.get(d.draw_index):
            labels[cases[d.draw_index][0]] = d.group_label
    car = CarModel(family, hashlib.sha256(raw).hexdigest())
    for d in m.physical_draws:
        g = geometry[d.draw_index]
        mesh = Mesh.of([v.position for v in g.vertices], g.triangles)
        case = cases.get(d.draw_index)
        texture = d.texture_tuple[0]
        label = labels.get(case[0]) if case else None
        if texture == ON_CORE_TEXTURE or texture == ON_GLOW_TEXTURE:
            role = 'on_core' if texture == ON_CORE_TEXTURE else 'on_glow'
            if case and case[1] != 2:
                role = 'hidden_state'
        elif case is None:
            role = 'body'
        elif label == 'blight':
            # case 1 = the OFF lamp (lens reference); non-lamp draws of case 2 stay drawn while braking.
            role = 'off_glass' if case[1] == 1 else 'off_glass_on'
        else:
            role = 'body' if case[1] == 1 else 'hidden_state'
        car.draws.append(DrawInfo(d.draw_index, texture, case, bool(d.flags_0x20[0]), mesh,
                                  d.local_vertex_max + 1, d.triangle_count, role))
    return car
