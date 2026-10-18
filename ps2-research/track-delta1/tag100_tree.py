"""In-memory editable PC course tag100 BSP with an exact serializer (batch brush fill / carve).

See tag100_patch.py for the wire grammar. The whole tree is loaded into parallel lists, edited, and written back in one pass; header words are
recounted from the structure (w0 = leaves in child links, w1 = leaves in sibling links, w2 = w3 = plane nodes). `serialize()` of an unedited tree
reproduces the parsed bytes exactly (tested on retail Turkey3).

Orientation rule used by the brush operations (retail convention): a plane normal points from the solid side to the empty side.
  fill  (target EMPTY leaves -> inside SOLID): planes are the outward normals of the brush, inside = back link.
  carve (target SOLID leaves -> inside EMPTY): planes are the inward normals of the brush, inside = front link.
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


def polytope(halfspaces, eps=1e-5):
    """Vertices and non-redundant half-spaces of {p : n.p + d <= 0 for every (n, d)}; ([], []) when empty or degenerate."""
    hs = [(tuple(h[0]), h[1]) if len(h) == 2 else (tuple(h[:3]), h[3]) for h in halfspaces]
    verts = []
    for (a, da), (b, db), (c, dc) in itertools.combinations(hs, 3):
        # solve [a;b;c] p = -[da;db;dc]
        det = (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]))
        if abs(det) < 1e-9:
            continue
        rhs = (-da, -db, -dc)

        def cramer(col):
            m = [list(a), list(b), list(c)]
            for r in range(3):
                m[r][col] = rhs[r]
            return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                    + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
        p = (cramer(0) / det, cramer(1) / det, cramer(2) / det)
        if all(n[0] * p[0] + n[1] * p[1] + n[2] * p[2] + d <= eps for n, d in hs):
            verts.append(p)
    uniq = []
    for p in verts:
        if not any(abs(p[0] - q[0]) < 1e-4 and abs(p[1] - q[1]) < 1e-4 and abs(p[2] - q[2]) < 1e-4 for q in uniq):
            uniq.append(p)
    if len(uniq) < 4:
        return [], []
    kept = []
    for n, d in hs:
        on = [p for p in uniq if abs(n[0] * p[0] + n[1] * p[1] + n[2] * p[2] + d) < 1e-3]
        if len(on) >= 3 and not any(max(abs(n[i] - k[0][i]) for i in range(3)) < 1e-6 and abs(d - k[1]) < 1e-5 for k in kept):
            kept.append((n, d))
    # a flat polytope (all vertices coplanar) has no volume
    if len(kept) < 4:
        return [], []
    return uniq, kept


class Tree:
    def __init__(self, raw):
        parsed = parse_course_tag100_bytes(raw, 'tag100', allow_trailing=True)
        self.header = parsed.header_words
        self.tail = raw[parsed.consumed_size:]
        self.plane, self.code, self.f0, self.f1, self.child, self.sib = [], [], [], [], [], []
        for n in parsed.nodes:
            if n.list_offset is not None:
                raise ValueError('tag100 list blocks are not supported')
            self.plane.append(n.optional_record.values if n.optional_record else None)
            self.code.append(n.optional_record.code if n.optional_record else None)
            self.f0.append(n.field_0)
            self.f1.append(n.field_1)
            self.child.append(n.first_child_index)
            self.sib.append(n.next_sibling_index)

    def new_node(self, plane, code, f0):
        self.plane.append(plane)
        self.code.append(code)
        self.f0.append(f0)
        self.f1.append(0)
        self.child.append(None)
        self.sib.append(None)
        return len(self.plane) - 1

    def serialize(self):
        out = bytearray(b'')
        stack = [('n', 0)]
        counts = [0, 0, 0]  # child leaves, sibling leaves, plane nodes
        body = bytearray()
        # first pass in the same order to recount; emit directly
        while stack:
            kind, v = stack.pop()
            if kind == 'b':
                body += v
                continue
            i = v
            if self.plane[i] is None:
                body += struct.pack('<2I4B', self.f0[i], self.f1[i], 0, 0, 0, 0)
            else:
                counts[2] += 1
                body += struct.pack('<2IB4fIBB', self.f0[i], self.f1[i], 1, *self.plane[i], self.code[i], 0, 1)
                c, s = self.child[i], self.sib[i]
                sel_c = 1 if self.plane[c] is None else 0
                sel_s = 1 if self.plane[s] is None else 0
                counts[0] += sel_c
                counts[1] += sel_s
                # order: child selector, child subtree, has_sibling, sibling selector, sibling subtree
                stack.append(('n', s))
                stack.append(('b', bytes([1, sel_s])))
                stack.append(('n', c))
                stack.append(('b', bytes([sel_c])))
        w4 = self.header[4]
        head = struct.pack('<6I', 100, counts[0], counts[1], counts[2], counts[2], w4)
        return bytes(head) + bytes(body) + self.tail

    def classify(self, p):
        i = 0
        while self.plane[i] is not None:
            nx, ny, nz, d = self.plane[i][:4]
            i = self.sib[i] if nx * p[0] + ny * p[1] + nz * p[2] + d >= 0 else self.child[i]
        return i

    def find_leaves(self, verts, target):
        """Leaves with field_0 == target whose cell overlaps the convex hull of verts: [(leaf, parent, 'child' | 'sib')]."""
        found, stack = [], [(0, verts)]
        while stack:
            i, vs = stack.pop()
            nx, ny, nz, d = self.plane[i][:4]
            s = [nx * x + ny * y + nz * z + d for x, y, z in vs]
            sides = []
            if min(s) >= -EPS:
                sides.append(('sib', self.sib[i]))
            elif max(s) <= EPS:
                sides.append(('child', self.child[i]))
            else:
                sides += [('sib', self.sib[i]), ('child', self.child[i])]
            for kind, t in sides:
                if self.plane[t] is not None:
                    stack.append((t, vs))
                elif self.f0[t] == target:
                    found.append((t, i, kind))
        return found

    def _chain(self, planes, code, inside_front, inside, outside):
        """Build the plane chain; returns the index of its first node. `planes` are oriented (normal toward the empty side)."""
        nodes = [self.new_node(tuple(p), code, 0) for p in planes]
        for k, node in enumerate(nodes):
            inner = nodes[k + 1] if k + 1 < len(nodes) else self.new_node(None, None, inside)
            outer = self.new_node(None, None, outside)
            if inside_front:
                self.sib[node], self.child[node] = inner, outer
            else:
                self.child[node], self.sib[node] = inner, outer
        return nodes[0]

    def apply_brush(self, halfspaces, code, mode):
        """mode 'fill': inside becomes SOLID (target EMPTY leaves); 'carve': inside becomes EMPTY (target SOLID leaves).

        `halfspaces` are outward half-spaces (n.p + d <= 0 inside). Returns the number of leaves replaced."""
        verts, kept = polytope(halfspaces)
        return self.apply_prepared(verts, kept, code, mode)

    def apply_prepared(self, verts, kept, code, mode):
        """Same as apply_brush with the polytope already computed (kept = [((nx, ny, nz), d)] outward half-spaces)."""
        if not verts:
            return 0
        target, inside, outside = (EMPTY, SOLID, EMPTY) if mode == 'fill' else (SOLID, EMPTY, SOLID)
        if mode == 'fill':
            planes = [(*n, d) for n, d in kept]
        else:
            planes = [(-n[0], -n[1], -n[2], -d) for n, d in kept]
        leaves = self.find_leaves(verts, target)
        for leaf, parent, kind in leaves:
            first = self._chain(planes, code, mode == 'carve', inside, outside)
            if kind == 'child':
                self.child[parent] = first
            else:
                self.sib[parent] = first
        return len(leaves)

    def reference_code(self, point):
        """Valid (non-negative int32) plane code on the descent path to `point`, preferring near-horizontal planes."""
        best, i = None, 0
        while self.plane[i] is not None:
            p = self.plane[i]
            if self.code[i] < 0x80000000 and abs(p[1]) > 0.8:
                best = self.code[i]
            i = self.sib[i] if p[0] * point[0] + p[1] * point[1] + p[2] * point[2] + p[3] >= 0 else self.child[i]
        return best

    def counts_ok(self):
        raw = self.serialize()
        parsed = parse_course_tag100_bytes(raw, 'check', allow_trailing=True)
        return all(parsed.count_invariants().values())
