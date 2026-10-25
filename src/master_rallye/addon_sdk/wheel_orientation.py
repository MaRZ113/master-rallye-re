"""Proper rotations between a source wheel's outward axis and MR's template.

Qualified stock Navara/Pajero wheel faces point toward local -X. Native race
instances own placement/spin/steering. Never correct orientation by shifting hubs
or applying a negative-determinant mirror to geometry without its winding.
"""
from dataclasses import replace
import math
from master_rallye.scene_dx_writer import ScenePart
from master_rallye.topology_writer import DrawGeometry


def orient_parts(parts: list[ScenePart], *, source_outward_x: int,
                 target_outward_x: int = -1) -> list[ScenePart]:
    if source_outward_x not in (-1,1) or target_outward_x not in (-1,1):
        raise ValueError('wheel outward direction must be signed X')
    if source_outward_x == target_outward_x:return list(parts)
    def turn(v):return (-v[0],v[1],-v[2])
    return [replace(p,geometry=DrawGeometry(tuple(replace(v,position=turn(v.position),normal=turn(v.normal))
        for v in p.geometry.vertices),p.geometry.triangles)) for p in parts]


def instance_angle(world_outward_x: int) -> float:
    if world_outward_x not in (-1,1):raise ValueError('wheel side must be signed X')
    return 0. if world_outward_x < 0 else math.pi
