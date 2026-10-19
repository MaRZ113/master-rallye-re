"""Whole-course PS2 `.BSP` -> PC tag100 tree (W1 of the full PS2 course conversion).

The PS2 tree and the PC tree are the same kind of BSP (plane nodes: back = child = n.p + d < 0, front = sibling; leaves solid or empty). The PS2 file adds
payload leaves whose solid part is a convex polyhedron (solid where n.p + d <= -1e-4 for every plane of its run). This module rebuilds the PS2 tree as a
new PC tree:

  * a PS2 plane node becomes a PC plane node with the same float32 plane;
  * plain solid / empty leaves become PC solid / empty leaves;
  * a payload leaf becomes a chain of its run planes (front: empty leaf, back: next plane, last back: solid leaf); a run with no planes is solid.
    Run planes are moved by the PS2 epsilon (inset_d) so that thin cells do not keep a solid sheet the PS2 test does not have.

The walk carries the convex cell of every node (`bsp_region.ConvexCell`, universe cube cut by the path planes). It is used to drop planes that do not cut
their cell and to find a point on each plane for choosing its plane code. Geometry is exact against the PS2 BSP up to one float32 step of the inset plane.

Plane codes. The engine's contact code skips a plane whose code is negative as int32: the trace (PC 0x62f840, PS2 0x243718) ignores such a plane
and the nearest-plane fallback (PC 0x61fff0, PS2 0x237610) does not take it as the contact plane. PS2 tree planes with code 0xFFFFFFFF are splitters
of that kind and keep 0xFFFFFFFF (provenance `ps2_splitter`); with a valid code the fallback can pick such a plane under the ground and push the car
sideways (invisible one-sided wall, Turkey2 game test 2026-10-19). Every other plane gets a non-negative code. The code is the source triangle
ordinal of the PC collision source (R5T-F.2.1); its runtime use beyond "non-negative = contact" is not known. Choice per plane, with provenance
recorded:
  pc_same_plane  a retail PC plane with the same equation (|dn| <= 1e-3, |dd| <= 0.05) and a valid code exists: its code
  pc_ground_path the last near-horizontal valid code on the retail PC descent path at a point of the plane inside its cell (Tree.reference_code)
  default        the course default code (reference code at the centre of the PS2 ground)
A valid code is not a claim that the PC surface behind it is the right one; surface types are carried separately by tag1400.
"""
from __future__ import annotations

import collections
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'track-coll1a'))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
from bsp_region import ConvexCell, PS2_EPS  # noqa: E402
import tag100_tree as tt  # noqa: E402

UNIVERSE = 1.0e5
PS2_SPLITTER = 0xFFFFFFFF   # PS2 tree plane code of a splitter plane (no contact)


class PlaneCodes:
    """Code choice for new planes from the retail PC tree."""

    def __init__(self, pc_tree, default_point):
        self.pc = pc_tree
        self.by_key = collections.defaultdict(list)
        for i, pl in enumerate(pc_tree.plane):
            c = pc_tree.code[i]
            if pl is None or c is None or c >= 0x80000000:
                continue
            self.by_key[self._key(pl)].append((pl, c))
        self.default = pc_tree.reference_code(default_point)
        self.default_source = 'reference_code at the course centre'
        if self.default is None:
            # no near-horizontal valid plane on that path: the most frequent valid code of the near-horizontal retail planes
            freq = collections.Counter(c for pl, c in zip(pc_tree.plane, pc_tree.code)
                                       if pl is not None and c is not None and c < 0x80000000 and abs(pl[1]) > 0.8)
            if not freq:
                raise ValueError('the retail tree has no valid near-horizontal plane code')
            self.default = min(freq.items(), key=lambda kv: (-kv[1], kv[0]))[0]
            self.default_source = 'most frequent near-horizontal retail code'
        self.provenance = collections.Counter()

    @staticmethod
    def _key(pl):
        return (round(pl[0], 2), round(pl[1], 2), round(pl[2], 2), round(pl[3]))

    def choose(self, plane, point):
        best = None
        k = self._key(plane)
        for dk in (-1, 0, 1):     # neighbours: the rounding of d (and of the inset d) may fall on either side
            for cand, c in self.by_key.get((k[0], k[1], k[2], k[3] + dk), ()):
                if max(abs(cand[k] - plane[k]) for k in range(3)) <= 1e-3 and abs(cand[3] - plane[3]) <= 0.05:
                    if best is None or c < best:
                        best = c
        if best is not None:
            self.provenance['pc_same_plane'] += 1
            return best
        if point is not None:
            c = self.pc.reference_code(point)
            if c is not None:
                self.provenance['pc_ground_path'] += 1
                return c
        self.provenance['default'] += 1
        return self.default


def inset_d(d, eps=PS2_EPS):
    """Smallest float32 >= d + eps. The PS2 payload test is solid only where n.p + d <= -eps; a PC plane (n, d') with d' >= d + eps keeps the
    PC back side (n.p + d' < 0) inside the PS2 solid. The plane can only be stored in float32, so the inset is eps plus at most one float32 step."""
    x = d + eps
    r = struct.unpack('<f', struct.pack('<f', x))[0]
    if r < x:
        bits = struct.unpack('<I', struct.pack('<f', r))[0]
        bits = bits + 1 if r >= 0 else bits - 1
        r = struct.unpack('<f', struct.pack('<I', bits))[0]
    return r


def _face_point(cell, plane):
    """Centroid of the cell face lying in `plane` (the face the clip created), else the cell centroid."""
    for fp, poly in cell.faces:
        if all(abs(fp[k] - plane[k]) < 1e-9 for k in range(4)):
            return tuple(sum(p[k] for p in poly) / len(poly) for k in range(3))
    vs = cell.vertices()
    return tuple(sum(v[k] for v in vs) / len(vs) for k in range(3)) if vs else None


def _span(cell, plane):
    """(min, max) of n.p + d over the cell vertices."""
    n, d = plane[:3], plane[3]
    vals = [n[0] * v[0] + n[1] * v[1] + n[2] * v[2] + d for v in cell.vertices()]
    return min(vals), max(vals)


def _empty_tree(tail):
    t = tt.Tree.__new__(tt.Tree)
    t.header = [100, 0, 0, 0, 0, 0]
    t.tail = tail
    t.plane, t.code, t.f0, t.f1, t.child, t.sib = [], [], [], [], [], []
    return t


def convert(bsp, codes, tail=b'', prune=True, keep_splitters=True):
    """Returns (Tree, stats). The root of the PS2 tree becomes node 0. keep_splitters=False gives every plane a valid code (the build
    before 2026-10-19)."""
    tree = _empty_tree(tail)
    stats = collections.Counter()
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 200000))
    root_cell = ConvexCell.box((-UNIVERSE,) * 3, (UNIVERSE,) * 3)

    def leaf(f0):
        stats['leaf_solid' if f0 == tt.SOLID else 'leaf_empty'] += 1
        return tree.new_node(None, None, f0)

    def plane_node(pl, cell, ps2_code=None):
        node = tree.new_node(tuple(pl), None, 0)
        if keep_splitters and ps2_code == PS2_SPLITTER:
            tree.code[node] = PS2_SPLITTER
            codes.provenance['ps2_splitter'] += 1
        else:
            tree.code[node] = codes.choose(pl, _face_point(cell, pl) if cell is not None else None)
        stats['plane_nodes'] += 1
        return node

    def walk(idx, cell):
        n = bsp.nodes[idx]
        if n.plane is not None:
            nx, ny, nz, d = n.plane[:4]
            if prune:
                # decide by the signs of the cell vertices (exact), not by the volume of the clipped parts: thin cells are real
                lo, hi = _span(cell, (nx, ny, nz, d))
                if lo >= 0:
                    stats['pruned_planes'] += 1
                    return walk(n.sibling, cell)
                if hi < 0:
                    stats['pruned_planes'] += 1
                    return walk(n.child, cell)
                back = cell.clip((nx, ny, nz, d)) or cell
                front = cell.clip((-nx, -ny, -nz, -d)) or cell
            else:
                back = front = cell
            node = plane_node((nx, ny, nz, d), back, n.plane[4])
            c = walk(n.child, back)
            s = walk(n.sibling, front)
            tree.child[node], tree.sib[node] = c, s
            return node
        if n.payload is None:
            return leaf(tt.SOLID if n.field_0 == 0xFFFFFFFF else tt.EMPTY)
        stats['payload_leaves'] += 1
        start, count = n.payload[0] & 0xFFFFFF, n.payload[1] & 0xFF
        planes, cur = [], cell
        for nx, ny, nz, d, _c in bsp.plane_table[start:start + count]:
            if prune:
                di = inset_d(d)
                lo, hi = _span(cur, (nx, ny, nz, di))
                if lo >= 0:                       # no cell point strictly behind: no PS2 solid in this leaf
                    stats['payload_empty'] += 1
                    return leaf(tt.EMPTY)
                if hi < 0:                        # the whole cell is behind: the plane decides nothing here
                    stats['pruned_run_planes'] += 1
                    continue
                behind = cur.clip((nx, ny, nz, di)) or cur
                planes.append(((nx, ny, nz, di), behind))
                cur = behind
            else:
                planes.append(((nx, ny, nz, inset_d(d)), None))
        if not planes:
            return leaf(tt.SOLID)
        first = None
        prev = None
        for pl, c_cell in planes:
            node = plane_node(pl, c_cell)
            tree.sib[node] = leaf(tt.EMPTY)
            if prev is None:
                first = node
            else:
                tree.child[prev] = node
            prev = node
        tree.child[prev] = leaf(tt.SOLID)
        return first

    root = walk(0, root_cell)
    if root != 0:
        # the root of the PS2 tree was pruned away (cannot happen for a real course); move the subtree root to index 0 is not supported
        raise ValueError('converted root is not node 0')
    return tree, stats


def assemble_dx(retail_dx, tree_bytes_with_tail):
    """Course DX = retail render prefix (unchanged) + new tag100-starting suffix."""
    sys.path.insert(0, str(HERE.parent.parent / 'src'))
    from master_rallye.tag100_diff import extract_tag100_from_dx_bytes
    sl = extract_tag100_from_dx_bytes(retail_dx, 'retail')
    return retail_dx[:sl.tag_offset] + tree_bytes_with_tail, sl
