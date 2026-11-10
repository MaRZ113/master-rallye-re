"""Exact collision for an edited Retail course: native object space grafted with the new ground.

``object_tree`` copies a Retail tag100 tree and keeps solid only the cells that
are object collision (solid convex cells standing above the ground with a face
towards empty space, see :func:`master_rallye.studio.collision.extract_native_solids`);
every other solid cell (the old ground) becomes empty.

``graft`` then pushes the new land polygons (edited terrain, Studio collision
objects, the map-edge closure) down that object tree. Object cells stay solid;
inside every empty cell the polygons that reach it are built into a local
solid-leaf tree, and a cell no polygon reaches takes the new ground tree's answer
at its centre. The result answers exactly ``native object OR new ground`` for
every point, so unchanged Retail objects keep their exact cooked shape and the
terrain may change topology freely.

The tag100 wire grammar needs solid leaves in back slots and empty leaves in
front slots; a leaf of the other kind is wrapped in a node whose plane sends
every point to one side.
"""
from __future__ import annotations

import hashlib
import math
import struct

from ..course_bsp import AXIS_CODE, Leaf, Node, build_solid_bsp
from .bsp_union import _split
from .collision import BOX_CODE, _box, _split_cell, classify

FAR = 1.0e9


def _always(solid: bool):
    # s = 0*x + 1*y + d: d = -FAR -> s <= 0 everywhere (back, solid); d = +FAR -> front (empty)
    return Node((0.0, 1.0, 0.0, -FAR if solid else FAR), AXIS_CODE, Leaf(True), Leaf(False))


def fix_slots(node, slot="root"):
    """Make every back-slot leaf solid and every front-slot leaf empty (wire grammar)."""
    if isinstance(node, Leaf):
        if slot == "back" and not node.solid:
            return _always(False)
        if slot == "front" and node.solid:
            return _always(True)
        if slot == "root":
            return _always(node.solid)
        return node
    stack = [node]
    while stack:
        n = stack.pop()
        for attr, side in (("back", "back"), ("front", "front")):
            child = getattr(n, attr)
            if isinstance(child, Leaf):
                setattr(n, attr, fix_slots(child, side))
            else:
                stack.append(child)
    return node


def object_tree(native_root, keep_leaf_ids: set):
    """Copy of the native tree in which only the leaves in ``keep_leaf_ids`` stay solid."""
    def copy(n):
        if isinstance(n, Leaf):
            return Leaf(n.solid and id(n) in keep_leaf_ids)
        return Node(n.plane, n.code, copy(n.back), copy(n.front))
    import sys
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 100000))
    try:
        return copy(native_root)
    finally:
        sys.setrecursionlimit(old)


def object_leaves(native_root, lo, hi, *, heights, ground_planes, min_lift=0.3, max_span=150.0):
    """ids of native solid leaves that are object collision (same rule as extract_native_solids)."""
    ground = set()
    for n0, n1, n2, d in ground_planes:
        if not any(math.isnan(v) for v in (n0, n1, n2, d)):
            ground.add((round(n0, 2), round(n1, 2), round(n2, 2), round(d, 1)))
            ground.add((round(-n0, 2), round(-n1, 2), round(-n2, 2), round(-d, 1)))
    keep = set()
    pad = 5.0
    stack = [(native_root, _box((lo[0] - pad, lo[1] - pad, lo[2] - pad), (hi[0] + pad, hi[1] + pad, hi[2] + pad)))]
    while stack:
        node, cell = stack.pop()
        if isinstance(node, Leaf):
            if not node.solid:
                continue
            pts = [p for face, _, _ in cell for p in face]
            span = max(max(p[k] for p in pts) - min(p[k] for p in pts) for k in (0, 2))
            if any(code == BOX_CODE for _, _, code in cell) or span > max_span:
                continue
            lift = max(((p[1] - g) for p in pts if (g := heights(p[0], p[2])) is not None), default=0.0)
            if lift < min_lift:
                continue
            for face, normal, code in cell:
                if code in (AXIS_CODE, BOX_CODE):
                    continue
                d = -(normal[0] * face[0][0] + normal[1] * face[0][1] + normal[2] * face[0][2])
                if any((round(normal[0], 2), round(normal[1], 2), round(normal[2], 2), round(d + dd, 1)) in ground
                       for dd in (0.0, 0.05, -0.05)):
                    continue
                cen = tuple(sum(p[k] for p in face) / len(face) for k in range(3))
                if not classify(native_root, tuple(cen[k] + 0.02 * normal[k] for k in range(3))):
                    keep.add(id(node))
                    break
            continue
        back, front = _split_cell(cell, node.plane, node.code)
        if back is not None:
            stack.append((node.back, back))
        if front is not None:
            stack.append((node.front, front))
    return keep


def graft(objects_root, polygons, ground_root, lo, hi, *, progress=None):
    """Union tree: ``objects_root`` solid cells OR the space below/inside ``polygons`` (judged by ``ground_root``)."""
    from ..course_bsp import Polygon
    pad = 5.0
    stats = {"empty_cells": 0, "grafted_cells": 0, "classified_cells": 0}

    def descend(node, polys, cell):
        if isinstance(node, Leaf):
            if node.solid:
                return Leaf(True)
            stats["empty_cells"] += 1
            if polys:
                stats["grafted_cells"] += 1
                return build_solid_bsp(polys)
            stats["classified_cells"] += 1
            pts = [p for face, _, _ in cell for p in face]
            centre = tuple(sum(p[k] for p in pts) / len(pts) for k in range(3))
            return Leaf(classify(ground_root, centre))
        back_polys, front_polys = [], []
        for poly in polys:
            b, f, kind = _split(poly.points, node.plane)
            if kind == 0:
                same = sum(node.plane[k] * poly.plane[k] for k in range(3)) > 0
                (front_polys if same else back_polys).append(poly)
                continue
            if b is not None:
                back_polys.append(Polygon(b, poly.plane, poly.code))
            if f is not None:
                front_polys.append(Polygon(f, poly.plane, poly.code))
        back_cell, front_cell = _split_cell(cell, node.plane, node.code)
        back = descend(node.back, back_polys, back_cell) if back_cell is not None else node.back
        front = descend(node.front, front_polys, front_cell) if front_cell is not None else node.front
        return Node(node.plane, node.code, back, front)

    import sys
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 200000))
    try:
        cell = _box((lo[0] - pad, lo[1] - pad, lo[2] - pad), (hi[0] + pad, hi[1] + pad, hi[2] + pad))
        tree = descend(objects_root, polygons, cell)
    finally:
        sys.setrecursionlimit(old)
    return fix_slots(tree), stats


def mesh_digest(mesh) -> str:
    h = hashlib.sha256()
    h.update(struct.pack(f"<{len(mesh.positions)}f", *mesh.positions))
    h.update(struct.pack(f"<{len(mesh.triangles)}I", *mesh.triangles))
    return h.hexdigest()
