"""Writer for the render section of a revision-135 course DX (W2 of the PS2 course conversion).

Layout (see docs/formats/dx-common.md and dx-course.md):
  header        u32 0xD00D, u32 135, u32 word_0x08, u32 vertex count
  arrays        positions (3 f32), normals (3 f32), colours (4 bytes), u32 UV set count + sets (2 f32), u32 index count + u16 local indices
  root envelope u32 1, u32 root count, root records (retail: one tag-4 wrapper without children)
  batches       repeated (u32 1, u32 count, records); a record is a draw (tag 2) or a container (tag 1: child count; tag 4: three words, the
                third is the child count; tag 5: four f32 + child count; tag 6: four f32 + child count), containers are followed by their children
  suffix        tag100 tree, tag1339, tag1400, tag1500 (written by the caller, kept as bytes here)
A draw is the 40-byte core (tag 2, vertex base, inclusive local vertex maximum, index start, index count, two unknown words, an unknown f32,
four flag bytes, a feature word), the texture slots (u32 count, length-prefixed names) and a zero terminator.

Unknown fields are carried as raw bytes. `from_bytes` + `serialize` reproduces every retail course DX byte for byte (tests). Edits are
made on the dataclasses; `serialize` recounts child counts and index/vertex ranges are validated, but container contents (tag-5 spheres,
tag-6 planes) and the tag1339/tag1500 sections that depend on geometry are the caller's responsibility (see `ps2-research/track-render1`).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

from .dx_course import parse_course_dx_bytes
from .errors import DxWriteError

CONTAINER_TAGS = {1, 4, 5, 6}


@dataclass
class Draw:
    vertex_base: int
    local_vertex_max: int
    index_start: int
    index_count: int
    unknown_0x14: int
    unknown_0x18: int
    raw_0x1c: bytes
    flags_0x20: bytes
    unknown_0x24: int
    slots: list[bytes]
    tag: int = 2

    @property
    def texture_tuple(self):
        return tuple(s.decode('ascii') for s in self.slots)


@dataclass
class Container:
    tag: int
    prefix: bytes                     # bytes after the tag, child count included (rewritten on serialize)
    children: list = field(default_factory=list)


@dataclass
class CourseRender:
    word_0x04: int
    word_0x08: int
    positions: list
    normals: list
    colors: bytearray
    uv_sets: list
    indices: list
    roots: list
    batches: list                     # list of lists of records
    suffix: bytes

    @classmethod
    def from_bytes(cls, data: bytes, source: str = '<bytes>') -> 'CourseRender':
        m = parse_course_dx_bytes(data, source)

        def conv(rec):
            if rec.tag in CONTAINER_TAGS and rec.opaque_prefix is not None and rec.index_count == 0:
                return Container(rec.tag, bytes(rec.opaque_prefix), [conv(c) for c in rec.children])
            if rec.tag != 2:
                raise DxWriteError(f'course draw tag {rec.tag} is not supported by the writer')
            core = data[rec.core_offset:rec.core_offset + 40]
            return Draw(rec.vertex_base, rec.local_vertex_max, rec.index_start, rec.index_count, rec.unknown_0x14, rec.unknown_0x18,
                        core[0x1C:0x20], core[0x20:0x24], rec.unknown_0x24, [s.raw for s in rec.texture_slots])

        end = m.trailing.offset
        return cls(m.word_0x04, m.word_0x08, list(m.vertices.positions), list(m.vertices.normals), bytearray(m.vertices.colors),
                   [list(u.values) for u in m.uv_sets], list(m.local_indices), [conv(r) for r in m.course_root_records],
                   [[conv(r) for r in b.records] for b in m.course_batches], data[end:])

    # ------------------------------------------------------------------ writing
    def _record(self, rec, out):
        if isinstance(rec, Container):
            prefix = bytearray(rec.prefix)
            n = len(rec.children)
            if rec.tag == 1:
                prefix[0:4] = struct.pack('<I', n)
            elif rec.tag == 4:
                prefix[8:12] = struct.pack('<I', n)
            else:
                prefix[16:20] = struct.pack('<I', n)
            out += struct.pack('<I', rec.tag) + prefix
            for c in rec.children:
                self._record(c, out)
            return
        d = rec
        out += struct.pack('<7I', 2, d.vertex_base, d.local_vertex_max, d.index_start, d.index_count, d.unknown_0x14, d.unknown_0x18)
        out += d.raw_0x1c + d.flags_0x20 + struct.pack('<I', d.unknown_0x24)
        out += struct.pack('<I', len(d.slots))
        for s in d.slots:
            out += struct.pack('<I', len(s)) + s
        out += struct.pack('<I', 0)

    def draws(self):
        def walk(r):
            if isinstance(r, Container):
                for c in r.children:
                    yield from walk(c)
            else:
                yield r
        for r in self.roots:
            yield from walk(r)
        for b in self.batches:
            for r in b:
                yield from walk(r)

    def validate(self):
        n = len(self.positions)
        if not (len(self.normals) == n and len(self.colors) == 4 * n and all(len(u) == n for u in self.uv_sets)):
            raise DxWriteError('vertex arrays have different lengths')
        if n > 0xFFFFFFFF or len(self.indices) > 0xFFFFFFFF:
            raise DxWriteError('too many vertices or indices')
        covered = bytearray(len(self.indices))
        for d in self.draws():
            if d.index_count % 3 or d.index_start + d.index_count > len(self.indices):
                raise DxWriteError('draw index range outside the index array')
            for k in range(d.index_start, d.index_start + d.index_count):
                li = self.indices[k]
                if li > d.local_vertex_max or d.vertex_base + li >= n:
                    raise DxWriteError('local index outside its draw vertex range')
                if covered[k]:
                    raise DxWriteError('index ranges of two draws overlap')
                covered[k] = 1
        if not all(covered):
            raise DxWriteError('index array has entries no draw uses')

    def serialize(self, validate=True) -> bytes:
        if validate:
            self.validate()
        n = len(self.positions)
        out = bytearray(struct.pack('<4I', 0xD00D, self.word_0x04, self.word_0x08, n))
        out += b''.join(struct.pack('<3f', *p) for p in self.positions)
        out += b''.join(struct.pack('<3f', *p) for p in self.normals)
        out += bytes(self.colors)
        out += struct.pack('<I', len(self.uv_sets))
        for uv in self.uv_sets:
            out += b''.join(struct.pack('<2f', *t) for t in uv)
        out += struct.pack('<I', len(self.indices)) + struct.pack(f'<{len(self.indices)}H', *self.indices)
        out += struct.pack('<2I', 1, len(self.roots))
        for r in self.roots:
            self._record(r, out)
        for b in self.batches:
            out += struct.pack('<2I', 1, len(b))
            for r in b:
                self._record(r, out)
        return bytes(out) + self.suffix
