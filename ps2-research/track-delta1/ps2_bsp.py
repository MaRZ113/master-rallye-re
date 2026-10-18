"""Reader for the PS2 course `.BSP` file, written from the original loader.

Derived from SLES_509.06 (read-only Ghidra EER decompilation, see T2-BSP-RECON.md):
  * 003944e8  opens `<course path without extension>.bsp` and stores the object at owner+4 -> +0x30
  * 003b6cd8  top-level reader: six u32 header words, then the tree (003b6ef8), then a plane table (003b6e10)
  * 003b6ef8  recursive node reader; 003b7278 plane record (3 f32 + f32 + u32); 003b7310 8-byte node payload;
              003b7460 one boolean byte
Fields whose meaning is unknown are kept raw.
"""
from __future__ import annotations

import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Node:
    index: int
    depth: int
    offset: int
    field_0: int
    field_1: int
    plane: tuple | None          # (nx, ny, nz, d, code)
    payload: tuple | None        # (u32 word0, u32 word1) from 003b7310
    child_select: tuple | None   # two booleans read after the child flag
    sibling_select: tuple | None
    child: int | None = None
    sibling: int | None = None


@dataclass
class Bsp:
    header: tuple                # six u32 words
    nodes: list = field(default_factory=list)
    plane_table: list = field(default_factory=list)   # (nx, ny, nz, d, code)
    tree_end: int = 0
    size: int = 0


class _R:
    def __init__(self, data):
        self.d, self.o = data, 0

    def u32(self):
        v = struct.unpack_from('<I', self.d, self.o)[0]
        self.o += 4
        return v

    def flag(self):
        v = self.d[self.o]
        self.o += 1
        return v != 0

    def plane(self):
        v = struct.unpack_from('<4fI', self.d, self.o)
        self.o += 20
        return v


def parse(data: bytes, max_nodes: int = 5_000_000) -> Bsp:
    r = _R(data)
    header = tuple(r.u32() for _ in range(6))
    bsp = Bsp(header=header, size=len(data))
    # Iterative form of the loader's recursion: child subtree first, then the sibling flag.
    pending = ('root', None, 0)
    waiting = []
    while pending is not None or waiting:
        if pending is None:
            parent = waiting.pop()
            if r.flag():
                sel = (r.flag(), r.flag())
                bsp.nodes[parent].sibling_select = sel
                pending = ('sibling', parent, bsp.nodes[parent].depth)
            continue
        kind, parent, depth = pending
        pending = None
        if len(bsp.nodes) >= max_nodes:
            raise ValueError('node limit')
        idx = len(bsp.nodes)
        off = r.o
        f0, f1 = r.u32(), r.u32()
        plane = r.plane() if r.flag() else None
        payload = (r.u32(), r.u32()) if r.flag() else None
        node = Node(idx, depth, off, f0, f1, plane, payload, None, None)
        bsp.nodes.append(node)
        if kind == 'child':
            bsp.nodes[parent].child = idx
        elif kind == 'sibling':
            bsp.nodes[parent].sibling = idx
        if r.flag():
            node.child_select = (r.flag(), r.flag())
            waiting.append(idx)
            pending = ('child', idx, depth + 1)
        else:
            if r.flag():
                node.sibling_select = (r.flag(), r.flag())
                pending = ('sibling', idx, depth)
    bsp.tree_end = r.o
    count = header[5]
    bsp.plane_table = [r.plane() for _ in range(count)]
    return bsp


def summary(bsp: Bsp) -> dict:
    with_plane = sum(n.plane is not None for n in bsp.nodes)
    with_payload = sum(n.payload is not None for n in bsp.nodes)
    consumed = bsp.tree_end + 20 * len(bsp.plane_table)
    return {'header': list(bsp.header), 'nodes': len(bsp.nodes), 'nodes_with_plane': with_plane,
            'nodes_with_payload': with_payload, 'max_depth': max(n.depth for n in bsp.nodes),
            'tree_end': bsp.tree_end, 'plane_table': len(bsp.plane_table), 'consumed': consumed,
            'file_size': bsp.size, 'trailing': bsp.size - consumed}


if __name__ == '__main__':
    import json
    print(json.dumps(summary(parse(Path(sys.argv[1]).read_bytes())), indent=1))
