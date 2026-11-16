"""Rally Championship Xtreme (PC) stage reader: <stage>.map world mesh and config.cfg race data.

.map (QTree version 11, loader Rally.exe 0x419F80 / 0x41A330):
  header u32 version 11, u32 node count, ..., u32 @24 total index count, u32 @32 vertex count,
  u32 @40 group count; bbox (6 f32) @0x40; identity matrix @0x58.
  mesh leaves: 0x80-byte header (u32 index count, u32 ?, u32 face count, u32 first group,
  u32 group count, u32, u32, u32 stored vertex count, u32 index count, ...; bbox; 4x4 matrix) followed by >= 4 words 0xFFFFFFFF, u16 indices (leaf-local),
  32-byte vertices (world xyz f32, u32 colour, uv f32 x2, 2 x f32 0), then per-leaf extra arrays.
  group table near the end: u32 count, 57-byte records (same layout as QTO groups: u32 0, u32 texture
  index (-1 = untextured), u32 second texture index (render flag 0x8: the group blends texture -> texture2 by the
  vertex colour alpha, 0 = texture, 255 = texture2), u32 render flags, u8 surface, u32 global first index, u32 index
  count, u32 triangle count, 7 x u32), then u32 texture count and 0x104-byte texture names.
  surface = index into the Rally.exe surface table (36-byte records, "Tarmac" record at file 0xB32F8):
  SURFACES below.
config.cfg: "TCFG", u32 4, u32 n, chunks (tag, u32 size, data): ENVO, MESH, INSU, CAMP, SPLN (name[256],
  2 x u32, then segments: u32 type, u32 0, 3 x (xyz f32, 3 f32)), STRT (name[256], u32, 4x4 matrix),
  CHKP (records: name[256], u32, post A xyz, post B xyz), CSND, TANM.
"""
from __future__ import annotations
import struct
from dataclasses import dataclass, field

BLEND_FLAG = 0x8                # group render flag: texture -> texture2 blend by vertex alpha (Clashin Darroch: 1027 groups)
SURFACES = ['Unknown', 'No Drive', 'Tarmac', 'Gravel', 'Mud', 'Snow', 'Water', 'Dust', 'Grass', 'Rough', 'Ice',
            'Cattle Grid', 'THS', 'Soft grass', 'NO_COLLIDE', 'Rough grass', 'Rough gravel', 'Rough tarmac', 'Rock',
            'Fence', 'Forest', 'Bushy', 'Wood', 'Metal', 'Corona']


@dataclass
class Group:
    texture: int
    flags: int
    surface: int
    first: int
    count: int
    texture2: int = -1          # flag 0x8 groups: second texture, blended by vertex alpha (0 = texture, 255 = texture2)


@dataclass
class Leaf:
    index_base: int          # global index position of this leaf's first index
    group_first: int         # leaf header word 3: first record of its groups in the group table
    group_count: int         # leaf header word 4
    indices: list
    vertices: list           # (x, y, z, colour u32, u, v)


@dataclass
class StageMap:
    bbox: tuple
    leaves: list
    groups: list
    textures: list

    def triangles(self):
        """Yield (group, (v0, v1, v2)) for every triangle; vertices are leaf vertex tuples.
        Group first is a global index position (leaves own groups[first:first+count]); indices are leaf-local vertex numbers."""
        for leaf in self.leaves:
            for g in self.groups[leaf.group_first:leaf.group_first + leaf.group_count]:
                off = g.first - leaf.index_base          # group first = global index position
                if off < 0 or off + g.count > len(leaf.indices):
                    raise ValueError('group outside its leaf')
                for k in range(off, off + g.count, 3):
                    a, b, c = leaf.indices[k:k + 3]
                    yield g, (leaf.vertices[a], leaf.vertices[b], leaf.vertices[c])


def read_map(b: bytes) -> StageMap:
    version = struct.unpack_from('<I', b, 0)[0]
    if version != 11:
        raise ValueError('QTree version %d' % version)
    n_index, n_vertex, n_group = (struct.unpack_from('<I', b, o)[0] for o in (24, 32, 40))
    bbox = struct.unpack_from('<6f', b, 0x40)
    leaves, i, base = [], 0, 0
    while base < n_index:
        i = b.find(b'\xff' * 16, i)
        if i < 0:
            break
        j = i + 16
        while b[j:j + 4] == b'\xff' * 4:
            j += 4
        ni, _nv, _nf, gfirst, gcount, _a, _b, nv = struct.unpack_from('<8I', b, i - 0x80)   # word 7 = stored vertices
        idx = list(struct.unpack_from('<%dH' % ni, b, j))
        vs = j + ni * 2
        verts = [struct.unpack_from('<3fI2f', b, vs + k * 32) for k in range(nv)]
        leaves.append(Leaf(base, gfirst, gcount, idx, verts))
        base += ni
        i = vs + nv * 32
    if base != n_index:
        raise ValueError('leaf indices %d != header %d' % (base, n_index))
    # group table: the u32 count n_group sits right before it, after the last leaf
    key = struct.pack('<I', n_group)
    gpos = b.find(key, i)
    while gpos >= 0:
        if gpos + 4 + n_group * 57 <= len(b) and \
                sum(struct.unpack_from('<I', b, gpos + 4 + k * 57 + 21)[0] for k in range(n_group)) == n_index:
            break
        gpos = b.find(key, gpos + 1)
    if gpos < 0:
        raise ValueError('group table not found')
    groups = []
    for k in range(n_group):
        p = gpos + 4 + k * 57
        tex, tex2, flags = struct.unpack_from('<3I', b, p + 4)
        first, count = struct.unpack_from('<2I', b, p + 17)
        groups.append(Group(-1 if tex == 0xFFFFFFFF else tex, flags, b[p + 16], first, count,
                            tex2 if flags & BLEND_FLAG and tex2 != 0xFFFFFFFF else -1))
    p = gpos + 4 + n_group * 57
    n_tex = struct.unpack_from('<I', b, p)[0]; p += 4
    textures = []
    for _ in range(n_tex):
        textures.append(b[p:b.index(b'\0', p)].decode('latin1')); p += 0x104
    return StageMap(bbox, leaves, groups, textures)


@dataclass
class StageConfig:
    splines: dict = field(default_factory=dict)       # name -> [(x, y, z)]
    start: tuple | None = None                         # (position xyz, 4x4 matrix)
    checkpoints: list = field(default_factory=list)    # (name, post A, post B)
    chunks: dict = field(default_factory=dict)


def read_config(b: bytes) -> StageConfig:
    if b[:4] != b'TCFG':
        raise ValueError('not a TCFG config')
    cfg = StageConfig(); p = 12
    while p + 8 <= len(b):
        tag = b[p:p + 4].decode('latin1'); size = struct.unpack_from('<I', b, p + 4)[0]
        d = b[p + 8:p + 8 + size]
        cfg.chunks.setdefault(tag, []).append(d)
        if tag == 'SPLN':
            name = d[:256].split(b'\0')[0].decode('latin1'); pts = []; q = 264   # name[256] + 2 x u32
            while q + 8 + 72 <= len(d):
                kind = struct.unpack_from('<I', d, q)[0]
                if kind not in (1, 2, 3):
                    break
                for k in range(3):
                    pts.append(struct.unpack_from('<3f', d, q + 8 + k * 24))
                q += 8 + 72
            cfg.splines[name] = pts
        elif tag == 'STRT':
            m = struct.unpack_from('<16f', d, 260)                 # name[256] + u32
            cfg.start = ((m[12], m[13], m[14]), m)
        elif tag == 'CHKP':
            for q in range(0, len(d) - 283, 284):
                name = d[q:q + 256].split(b'\0')[0].decode('latin1')
                a = struct.unpack_from('<3f', d, q + 260); c = struct.unpack_from('<3f', d, q + 272)
                cfg.checkpoints.append((name, a, c))
        p += 8 + size
    return cfg
