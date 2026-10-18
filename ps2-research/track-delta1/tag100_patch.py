"""Insert a convex solid brush into a PC course tag100 BSP (the collision tree at the end of the course DX).

Wire grammar (course_tag100.py, retail rev 135), one record per node, written depth first:
  node = u32 field_0, u32 field_1, u8 has_plane [plane: 4 float nx ny nz d + u32 code], u8 has_list [list],
         u8 has_child [u8 selector, back subtree], u8 has_sibling [u8 selector, front subtree]
A plane node carries both links (child = back half-space n.p + d < 0, sibling = front half-space n.p + d >= 0, T2 results), a leaf has neither.
Selector 1 marks a terminal leaf (pool8_child / pool8_sibling), 0 a plane node (pool36). field_0 = 0xFFFFFFFF is a solid leaf, 1 an empty leaf,
plane nodes use field_0 = field_1 = 0. A leaf record is 12 bytes (fields + four zero flag bytes).
Header words: w0 = back leaves (child links), w1 = front leaves (sibling links), w2 = w3 = plane nodes, w4 = list items.

Brush insertion (standard BSP): every empty leaf whose cell overlaps the brush is replaced by a chain of the brush planes; for the plane h_i
(outward normal) the front link is a new empty leaf and the back link is h_{i+1}, the last back link is a solid leaf. Outside the brush
nothing changes, inside the brush every overlapped cell becomes solid. Per replaced leaf: front-link leaf w0 +1, w1 +(k-1);
back-link leaf w0 +0, w1 +k; both w2 = w3 +k.
"""
import itertools
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'src'))
from master_rallye.course_tag100 import parse_course_tag100_bytes  # noqa: E402

SOLID, EMPTY = 0xFFFFFFFF, 1
EPS = 1e-4
LEAF_SIZE = 12


def hull_planes(points, eps=1e-4):
    """Outward planes (nx, ny, nz, d) with n.p + d <= 0 for every point; coplanar faces are merged."""
    pts = sorted({tuple(round(c, 5) for c in p) for p in points})
    planes = []
    for a, b, c in itertools.combinations(pts, 3):
        ux, uy, uz = (b[i] - a[i] for i in range(3))
        vx, vy, vz = (c[i] - a[i] for i in range(3))
        n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        ln = sum(x * x for x in n) ** .5
        if ln < 1e-9:
            continue
        n = tuple(x / ln for x in n)
        d = -sum(n[i] * a[i] for i in range(3))
        side = [sum(n[i] * p[i] for i in range(3)) + d for p in pts]
        if all(s <= eps for s in side):
            pass
        elif all(s >= -eps for s in side):
            n = tuple(-x for x in n)
            d = -d
        else:
            continue
        if not any(max(abs(n[i] - q[i]) for i in range(3)) < 1e-4 and abs(d - q[3]) < 1e-3 for q in planes):
            planes.append((*n, d))
    return planes


def leaf_bytes(field_0):
    return struct.pack('<2I4B', field_0, 0, 0, 0, 0, 0)


def subtree(planes, code=0xFFFFFFFF):
    """Serialized replacement for one empty leaf."""
    def node(i):
        last = i + 1 == len(planes)
        # fields, has_plane = 1, plane, has_list = 0, has_child = 1
        head = struct.pack('<2IB4fIBB', 0, 0, 1, *planes[i], code, 0, 1)
        back = leaf_bytes(SOLID) if last else node(i + 1)
        # child selector, back subtree, has_sibling = 1, sibling selector 1 (terminal leaf), empty front leaf
        return head + bytes([1 if last else 0]) + back + bytes([1, 1]) + leaf_bytes(EMPTY)
    return node(0)


def to_nodes(raw):
    parsed = parse_course_tag100_bytes(raw, 'tag100', allow_trailing=True)
    nodes = []
    for n in parsed.nodes:
        class N:
            pass
        o = N()
        o.plane = n.optional_record.values if n.optional_record else None
        o.code = n.optional_record.code if n.optional_record else None
        o.child, o.sibling, o.field_0, o.offset = n.first_child_index, n.next_sibling_index, n.field_0, n.offset
        nodes.append(o)
    return nodes, parsed


def classify(nodes, p):
    n = nodes[0]
    while n.plane is not None:
        nx, ny, nz, d = n.plane[:4]
        n = nodes[n.sibling if nx * p[0] + ny * p[1] + nz * p[2] + d >= 0 else n.child]
    return n


def reference_code(nodes, point):
    """Valid (non-negative as int32) plane code on the descent path to `point`, preferring near-horizontal planes (ground).

    The engine's contact code (0x006363C0) rejects a hit whose plane code is negative (0xFFFFFFFF = splitter without surface),
    so brush planes need a real code; the surface of the ground below the object is the natural choice.
    """
    best = None
    n = nodes[0]
    while n.plane is not None:
        code = n.code
        if code is not None and code < 0x80000000 and abs(n.plane[1]) > 0.8:
            best = code
        nx, ny, nz, d = n.plane[:4]
        n = nodes[n.sibling if nx * point[0] + ny * point[1] + nz * point[2] + d >= 0 else n.child]
    return best


def find_leaves(nodes, verts):
    """Empty leaves whose cell overlaps the convex hull given by its vertices: [(node index, 'front' | 'back')]."""
    found, stack = [], [(0, verts)]
    while stack:
        i, vs = stack.pop()
        n = nodes[i]
        s = [n.plane[0] * x + n.plane[1] * y + n.plane[2] * z + n.plane[3] for x, y, z in vs]
        sides = []
        if min(s) >= -EPS:
            sides.append(('front', n.sibling))
        elif max(s) <= EPS:
            sides.append(('back', n.child))
        else:
            sides += [('front', n.sibling), ('back', n.child)]
        for kind, target in sides:
            if nodes[target].plane is not None:
                stack.append((target, vs))
            elif nodes[target].field_0 == EMPTY:
                found.append((target, kind))
    return found


def insert_brush(raw, verts, planes=None, code=0xFFFFFFFF):
    """Return (new tag100 bytes, report)."""
    nodes, parsed = to_nodes(raw)
    tail = raw[parsed.consumed_size:]  # data that follows the tree in the same suffix is carried over unchanged
    raw = raw[:parsed.consumed_size]
    planes = planes or hull_planes(verts)
    leaves = sorted(set(find_leaves(nodes, verts)), key=lambda t: nodes[t[0]].offset)
    out = bytearray(raw)
    k = len(planes)
    empty = leaf_bytes(EMPTY)
    h = list(parsed.header_words)
    for i, kind in reversed(leaves):
        off = nodes[i].offset
        if bytes(raw[off:off + LEAF_SIZE]) != empty or bytes(raw[off - 2:off]) != bytes([1, 1]):
            raise ValueError(f'leaf {i} at 0x{off:X} is not a plain empty leaf: {raw[off - 2:off + LEAF_SIZE].hex()}')
        out[off - 1] = 0  # the link now points at a plane node (pool36) instead of a terminal leaf
        out[off:off + LEAF_SIZE] = subtree(planes, code)
        h[0] += 1 if kind == 'front' else 0
        h[1] += (k - 1) if kind == 'front' else k
        h[2] += k
        h[3] += k
    out[4:24] = struct.pack('<5I', *h)
    report = {'planes': k, 'leaves_replaced': len(leaves), 'header_before': list(parsed.header_words), 'header_after': h,
              'bytes_added': len(out) - len(raw), 'tree_bytes': len(raw), 'tail_bytes_carried': len(tail)}
    return bytes(out) + tail, report
