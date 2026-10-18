"""Point classification and vertical ray queries on a PS2 BSP (ps2_bsp.Bsp) or a PC tag100 tree.

Both trees use plane records (nx, ny, nz, d) with the plane n.p + d = 0. A plane node has two links, `child` and
`sibling` in the parser's naming. Which one is the front half-space is a parameter (`child_is_front`) until the
loader semantics are pinned down by the ground test in `bsp_orientation.py`.
"""
from __future__ import annotations


def classify(nodes, p, child_is_front=True, root=0):
    """Return the leaf node containing point p."""
    n = nodes[root]
    x, y, z = p
    while n.plane is not None:
        nx, ny, nz, d = n.plane[:4]
        front = nx * x + ny * y + nz * z + d >= 0
        nxt = n.child if (front == child_is_front) else n.sibling
        if nxt is None:
            return n
        n = nodes[nxt]
    return n


def leaf_class(node):
    """Raw leaf descriptor: (field_0, has_payload)."""
    return (node.field_0, node.payload is not None)


def vertical_transitions(nodes, x, z, y_top, y_bottom, step, child_is_front=True):
    """Walk down a vertical line in fixed steps and report where the leaf descriptor changes.

    Returns [(y_before, y_after, descriptor_before, descriptor_after)]. Resolution is `step`; a refinement by
    bisection is applied to each transition.
    """
    out = []
    prev = leaf_class(classify(nodes, (x, y_top, z), child_is_front))
    y = y_top
    while y > y_bottom:
        y2 = max(y - step, y_bottom)
        cur = leaf_class(classify(nodes, (x, y2, z), child_is_front))
        if cur != prev:
            lo, hi = y2, y  # bisection on the transition
            for _ in range(24):
                mid = (lo + hi) / 2
                if leaf_class(classify(nodes, (x, mid, z), child_is_front)) == prev:
                    hi = mid
                else:
                    lo = mid
            out.append((hi, lo, prev, cur))
            prev = cur
        y = y2
    return out


def ps2_segment_leaves(nodes, a, b, root=0):
    """Leaves crossed by segment a->b in order, as (node, t0, t1) with t in [0, 1]. Front half-space = `sibling`.

    Used for polygon hits: a payload plane crossing the segment inside [t0, t1] hits that leaf's polygon.
    """
    out = []
    stack = [(root, 0.0, 1.0)]
    while stack:
        idx, t0, t1 = stack.pop()
        n = nodes[idx]
        if n.plane is None:
            out.append((n, t0, t1))
            continue
        nx, ny, nz, d = n.plane[:4]
        p0 = tuple(a[i] + (b[i] - a[i]) * t0 for i in range(3))
        p1 = tuple(a[i] + (b[i] - a[i]) * t1 for i in range(3))
        s0 = nx * p0[0] + ny * p0[1] + nz * p0[2] + d
        s1 = nx * p1[0] + ny * p1[1] + nz * p1[2] + d
        front, back = n.sibling, n.child
        if s0 >= 0 and s1 >= 0:
            stack.append((front, t0, t1))
        elif s0 < 0 and s1 < 0:
            stack.append((back, t0, t1))
        else:
            tm = t0 + (t1 - t0) * (s0 / (s0 - s1))
            first, second = (front, back) if s0 >= 0 else (back, front)
            stack.append((second, tm, t1))   # popped last
            stack.append((first, t0, tm))
    return out


def ps2_ray_hits(bsp, a, b, eps=1e-4):
    """Polygon hits of segment a->b against payload planes of the leaves it crosses: [(t, code, normal)]."""
    hits = []
    plane_table = bsp.plane_table
    for leaf, t0, t1 in ps2_segment_leaves(bsp.nodes, a, b):
        if leaf.payload is None:
            continue
        start, count = leaf.payload[0] & 0xffffff, leaf.payload[1] & 0xff
        for nx, ny, nz, d, code in plane_table[start:start + count]:
            s0 = nx * a[0] + ny * a[1] + nz * a[2] + d
            s1 = nx * b[0] + ny * b[1] + nz * b[2] + d
            if s0 == s1:
                continue
            t = s0 / (s0 - s1)
            if t0 - eps <= t <= t1 + eps:
                hits.append((t, code, (nx, ny, nz)))
    hits.sort()
    return hits


def ps2_first_contact(bsp, a, b):
    """First contact along a->b: entry into a solid leaf (field_0 == -1) or a payload polygon hit.

    Returns (t, kind, code) with kind 'solid' or 'polygon', or None.
    """
    best = None
    for leaf, t0, _t1 in ps2_segment_leaves(bsp.nodes, a, b):
        if leaf.payload is None and leaf.field_0 == 0xffffffff:
            if best is None or t0 < best[0]:
                best = (t0, 'solid', None)
            break  # leaves come in ray order, so the first solid leaf is the earliest solid entry
    hits = ps2_ray_hits(bsp, a, b)
    if hits and (best is None or hits[0][0] < best[0]):
        best = (hits[0][0], 'polygon', hits[0][1])
    return best


PS2_EPS = 9.999999747378752e-05  # float at VA 0x4264a0 in SLES_509.06


def ps2_leaf_is_solid(bsp, leaf, p):
    """Solidity of point p inside a leaf, from the leaf-class vtable methods (ELF 0x2378a8, 0x236070, 0x236518).

    - empty leaf class (field_0 == +1): 0;  solid leaf class (field_0 == -1): 1;
    - payload leaf: 1 if its run has no planes, else 1 only when p is strictly behind every plane (n.p + d <= -eps).
    """
    if leaf.payload is None:
        return leaf.field_0 == 0xffffffff
    start, count = leaf.payload[0] & 0xffffff, leaf.payload[1] & 0xff
    if count == 0:
        return True
    for nx, ny, nz, d, _code in bsp.plane_table[start:start + count]:
        if nx * p[0] + ny * p[1] + nz * p[2] + d > -PS2_EPS:
            return False
    return True


def ps2_is_solid(bsp, p):
    return ps2_leaf_is_solid(bsp, classify(bsp.nodes, p, False), p)


def ps2_first_solid_t(bsp, a, b):
    """Smallest t in [0, 1] along a->b at which the point is solid, exact per leaf (polyhedron clipped to the leaf segment)."""
    for leaf, t0, t1 in ps2_segment_leaves(bsp.nodes, a, b):
        if leaf.payload is None:
            if leaf.field_0 == 0xffffffff:
                return t0
            continue
        start, count = leaf.payload[0] & 0xffffff, leaf.payload[1] & 0xff
        lo, hi = t0, t1
        for nx, ny, nz, d, _code in bsp.plane_table[start:start + count]:
            s0 = nx * a[0] + ny * a[1] + nz * a[2] + d
            s1 = nx * b[0] + ny * b[1] + nz * b[2] + d
            ds = s1 - s0                      # require s0 + t*ds <= -eps
            rhs = -PS2_EPS - s0
            if abs(ds) < 1e-12:
                if rhs < 0:
                    lo, hi = 1.0, 0.0
                    break
                continue
            t = rhs / ds
            if ds > 0:
                hi = min(hi, t)
            else:
                lo = max(lo, t)
            if lo > hi:
                break
        if lo <= hi:
            return lo
    return None
