"""Count underground-empty / above-ground-solid BSP leaves along a route.

usage: bsp_holes.py <dx> <racetest xml>
Leaf convention (cooked tag100): s = n.p + d; s <= 0 -> first child, else sibling;
leaf field_0 1 = empty, 0xFFFFFFFF = solid.
"""
import math
import sys
from pathlib import Path

sys.path[:0] = ["src", "tools"]
from master_rallye.course_atlas import read_marker_list  # noqa: E402
from master_rallye.course_tag100 import parse_course_tag100_bytes  # noqa: E402
from master_rallye.dx_course import parse_course_dx  # noqa: E402
import build_course_source as bcs  # noqa: E402


def load(dx):
    model = parse_course_dx(dx)
    tree = parse_course_tag100_bytes(model.collision.bsp.raw, dx.name, allow_trailing=True)
    return tree.nodes


def leaf(nodes, p):
    n = nodes[0]
    while n.optional_record is not None:
        a, b, c, d = n.optional_record.values
        n = nodes[n.first_child_index] if a * p[0] + b * p[1] + c * p[2] + d <= 0 else nodes[n.next_sibling_index]
    return n.field_0


def scan(dx, route, offsets=(-6, -3, 0, 3, 6), depth=0.7, lift=1.0):
    nodes = load(dx)
    land = bcs.land_database(dx.read_bytes())
    ground = bcs.ground_sampler([(r.float_prefix[0:3], r.float_prefix[3:6], r.float_prefix[6:9]) for r in land.records])
    holes, ceilings, total = [], [], 0
    for k, p in enumerate(route):
        q0, q1 = route[max(k - 1, 0)], route[min(k + 1, len(route) - 1)]
        fx, fz = q1[0] - q0[0], q1[2] - q0[2]
        length = math.hypot(fx, fz) or 1.0
        nx, nz = -fz / length, fx / length
        for off in offsets:
            x, z = p[0] + nx * off, p[2] + nz * off
            h = ground(x, z, p[1] + 50)
            if h is None:
                continue
            total += 1
            if leaf(nodes, (x, h - depth, z)) == 1:
                holes.append((k, off, round(x), round(h), round(z)))
            if leaf(nodes, (x, h + lift, z)) != 1:
                ceilings.append((k, off, round(x), round(h), round(z)))
    return total, holes, ceilings


if __name__ == "__main__":
    dx, xml = Path(sys.argv[1]), Path(sys.argv[2])
    route = read_marker_list(xml, "RaceLine")
    total, holes, ceilings = scan(dx, route)
    print(dx.name, "probes", total, "underground-empty", len(holes), "above-ground-solid", len(ceilings))
    print("holes", holes[:15])
    print("solid above", ceilings[:15])
