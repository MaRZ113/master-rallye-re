"""Cell-restricted graft of the PS2 solid into a PC tag100 tree (TRACK-COLL1A, default method).

The first method (`bsp_region.transplant_brush`: carve the box, then fill every PS2 polytope with the brush API) is exact but allocates a chain per
fragmented PC leaf: on Turkey3 rank 1 it adds 134k nodes (+26 percent). This method walks the PC tree with the cell of every node instead:

  * cell does not touch the box      -> untouched
  * cell lies inside the box         -> the whole subtree is replaced by the PS2 BSP restricted to that cell (`build_content`)
  * leaf cell straddles the box      -> chain of the box faces that cut the cell: outside keeps the old leaf class, inside gets the PS2 content
                                        restricted to the cell and the box
  * plane node whose cell straddles  -> kept, its children are handled recursively

Only links of nodes whose cell touches the box change. Replaced subtrees remain in memory as unreachable nodes and are not serialized.
All new nodes are created with Tree.new_node; plane equations are the PS2 float32 planes or the box walls; every new plane carries a valid
(non-negative) plane code taken from the PC descent path.
"""
from __future__ import annotations

import sys

import bsp_region as br
from bsp_region import ConvexCell, Snapshot, box_halfspaces, solid_volumes, PS2_EPS, MIN_VOLUME
import tag100_tree as tt

UNIVERSE = 1.0e5


def _contained(cell, lo, hi, tol=1e-6):
    return all(lo[k] - tol <= v[k] <= hi[k] + tol for v in cell.vertices() for k in range(3))


def _leaf(tree, f0):
    return tree.new_node(None, None, f0)


def build_content(tree, bsp, idx, cell, code):
    """New subtree describing the PS2 solid/empty inside `cell`. PS2 orientation is kept: front (n.p + d >= 0, the sibling link) is the empty side."""
    n = bsp.nodes[idx]
    if n.plane is not None:
        nx, ny, nz, d = n.plane[:4]
        back = cell.clip((nx, ny, nz, d))
        front = cell.clip((-nx, -ny, -nz, -d))
        if front is None and back is None:
            return _leaf(tree, tt.EMPTY)
        if front is None:
            return build_content(tree, bsp, n.child, back, code)
        if back is None:
            return build_content(tree, bsp, n.sibling, front, code)
        node = tree.new_node((nx, ny, nz, d), code, 0)
        tree.child[node] = build_content(tree, bsp, n.child, back, code)
        tree.sib[node] = build_content(tree, bsp, n.sibling, front, code)
        return node
    if n.payload is None:
        return _leaf(tree, tt.SOLID if n.field_0 == 0xFFFFFFFF else tt.EMPTY)
    start, count = n.payload[0] & 0xFFFFFF, n.payload[1] & 0xFF
    planes, cur = [], cell
    for nx, ny, nz, d, _c in bsp.plane_table[start:start + count]:
        behind = cur.clip((nx, ny, nz, d + PS2_EPS))
        if behind is None:
            return _leaf(tree, tt.EMPTY)
        if cur.clip((-nx, -ny, -nz, -d - PS2_EPS)) is None:
            continue                      # the whole cell is already behind this plane
        planes.append((nx, ny, nz, d))
        cur = behind
    if cur.volume() < MIN_VOLUME:
        return _leaf(tree, tt.EMPTY)
    top = _leaf(tree, tt.SOLID)
    for pl in reversed(planes):
        node = tree.new_node(pl, code, 0)
        tree.child[node], tree.sib[node] = top, _leaf(tree, tt.EMPTY)
        top = node
    return top


def reachable_nodes(tree):
    n, st = 0, [0]
    while st:
        j = st.pop()
        n += 1
        if tree.plane[j] is not None:
            st += [tree.child[j], tree.sib[j]]
    return n


def transplant(tree, bsp, box_lo, box_hi, code=None):
    """Replace the PC collision inside the box by the PS2 solid. Mutates `tree`; on any failure the tree is restored and the exception raised."""
    snap = Snapshot(tree)
    n0 = len(tree.plane)
    reach0 = reachable_nodes(tree)
    stats = {'grafted_subtrees': 0, 'straddling_leaves': 0, 'box_planes_emitted': 0, 'plane_nodes_visited': 0}
    box_planes = [(*n, d) for n, d in box_halfspaces(box_lo, box_hi)]
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 100000))
    try:
        if code is None:
            mid = tuple((box_lo[k] + box_hi[k]) / 2 for k in range(3))
            code = tree.reference_code(mid)
            if code is None:
                raise ValueError('no valid plane code on the PC descent path at the region centre')
        if code >= 0x80000000:
            raise ValueError('plane code must be a non-negative int32')

        def local_code(cell):
            vs = cell.vertices()
            pt = tuple(sum(v[k] for v in vs) / len(vs) for k in range(3))
            c = tree.reference_code(pt)
            return code if c is None else c

        def walk(i, full, boxed):
            if _contained(full, box_lo, box_hi):
                stats['grafted_subtrees'] += 1
                return build_content(tree, bsp, 0, boxed, local_code(boxed))
            if tree.plane[i] is not None:
                stats['plane_nodes_visited'] += 1
                nx, ny, nz, d = tree.plane[i][:4]
                for side in ('child', 'sib'):
                    sign = 1 if side == 'child' else -1
                    pl = (sign * nx, sign * ny, sign * nz, sign * d)
                    f, b = full.clip(pl), boxed.clip(pl)
                    if f is None or b is None:
                        continue
                    old = tree.child[i] if side == 'child' else tree.sib[i]
                    new = walk(old, f, b)
                    if new != old:
                        if side == 'child':
                            tree.child[i] = new
                        else:
                            tree.sib[i] = new
                return i
            stats['straddling_leaves'] += 1
            cl = local_code(boxed)
            top = build_content(tree, bsp, 0, boxed, cl)
            emitted = [pl for pl in box_planes if full.clip((-pl[0], -pl[1], -pl[2], -pl[3])) is not None]
            for pl in reversed(emitted):
                node = tree.new_node(pl, cl, 0)
                tree.child[node], tree.sib[node] = top, _leaf(tree, tree.f0[i])
                top = node
            stats['box_planes_emitted'] += len(emitted)
            return top

        universe = ConvexCell.box((-UNIVERSE,) * 3, (UNIVERSE,) * 3)
        boxed = universe
        for pl in box_planes:
            boxed = boxed.clip(pl)
        if tree.plane[0] is None or _contained(universe, box_lo, box_hi):
            raise ValueError('the tree root is a leaf or the region covers the universe')
        if walk(0, universe, boxed) != 0:
            raise ValueError('replacing the root is not supported')
        if not tree.counts_ok():
            raise ValueError('tag100 count invariants failed')
    except Exception:
        snap.restore(tree)
        raise
    cells, ps2_stats = solid_volumes(bsp, box_lo, box_hi)
    reach1 = reachable_nodes(tree)
    return {'method': 'graft', 'code': code, 'ps2_polytopes': len(cells), 'ps2_stats': ps2_stats, 'graft': stats,
            'nodes_reachable_before': reach0, 'nodes_reachable_after': reach1, 'nodes_net_change': reach1 - reach0,
            'nodes_allocated': len(tree.plane) - n0, 'polytope_volume': round(sum(c.volume() for c in cells), 3)}
