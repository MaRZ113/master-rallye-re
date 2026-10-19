from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src", Path(__file__).resolve().parent):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.course_render_writer import Container, CourseRender, Draw  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402
from master_rallye.errors import DxWriteError  # noqa: E402
from test_r5t_a import synthetic_course_dx  # noqa: E402


class CourseRenderWriterTests(unittest.TestCase):
    def setUp(self):
        self.data = synthetic_course_dx()

    def test_round_trip_is_byte_identical(self):
        self.assertEqual(CourseRender.from_bytes(self.data).serialize(), self.data)

    def test_container_child_count_is_recounted(self):
        r = CourseRender.from_bytes(self.data)
        sphere = r.roots[0].children[0] if r.roots[0].children else None
        # the synthetic file has the tag-4 root with one tag-5 child holding the first draw
        self.assertIsInstance(r.roots[0], Container)
        self.assertEqual(r.roots[0].tag, 4)
        self.assertIsInstance(sphere, Container)
        self.assertEqual(sphere.tag, 5)
        moved = r.batches[0].pop()
        sphere.children.append(moved)
        out = r.serialize()
        m = parse_course_dx_bytes(out)
        self.assertTrue(m.course_render_validated)
        tag5 = next(rec for g in m.draw_groups for rec in g.root.flattened() if rec.tag == 5)
        self.assertEqual(tag5.declared_child_count, 2)
        self.assertEqual(struct.unpack_from('<I', tag5.opaque_prefix, 16)[0], 2)

    def test_new_geometry_round_trips_through_the_parser(self):
        r = CourseRender.from_bytes(self.data)
        base = len(r.positions)
        r.positions += [(5.0, 0.0, 0.0), (6.0, 0.0, 0.0), (5.0, 1.0, 0.0)]
        r.normals += [(0.0, 0.0, 1.0)] * 3
        r.colors += bytes((1, 2, 3, 255)) * 3
        r.uv_sets[0] += [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        start = len(r.indices)
        r.indices += [0, 1, 2]
        r.batches[0].append(Draw(base, 2, start, 3, 1, 0, struct.pack('<f', 1.0), bytes.fromhex('00000101'), 3, [b'new-tga', b'Null']))
        m = parse_course_dx_bytes(r.serialize())
        self.assertTrue(m.course_render_validated)
        self.assertEqual(len(m.physical_draws), 3)
        self.assertEqual(m.physical_draws[-1].texture_tuple, ('new-tga', 'Null'))

    def test_validation_rejects_bad_ranges(self):
        r = CourseRender.from_bytes(self.data)
        r.indices.append(0)                      # an index no draw uses
        with self.assertRaises(DxWriteError):
            r.serialize()
        r = CourseRender.from_bytes(self.data)
        d = next(r.draws())
        d.local_vertex_max = 0                   # local index 1 and 2 now outside the draw range
        with self.assertRaises(DxWriteError):
            r.serialize()
        r = CourseRender.from_bytes(self.data)
        r.normals.pop()
        with self.assertRaises(DxWriteError):
            r.serialize()


if __name__ == "__main__":
    unittest.main()
