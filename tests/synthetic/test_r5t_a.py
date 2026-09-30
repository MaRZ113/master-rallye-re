from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.dx import MAGIC, parse_dx_common_prefix
from master_rallye.dx_course import parse_course_dx_bytes
from master_rallye.errors import BoundsError, FormatError
from master_rallye.course_metadata import mark_course_metadata
from master_rallye.hnt import parse_hnt_bytes, resolve_hnt_entries
from master_rallye.sfl import parse_sfl_bytes


def course_record(base=0, index_start=0):
    textures = ("track-tga", "Null")
    record = bytearray(struct.pack(
        "<7If4BI", 2, base, 2, index_start, 3, 1, 0, 1.0, 0, 0, 0, 1, 5
    ))
    record += struct.pack("<I", len(textures))
    for texture in textures:
        value = texture.encode("ascii")
        record += struct.pack("<I", len(value)) + value
    record += struct.pack("<I", 0)
    return bytes(record)


def synthetic_course_dx():
    positions = (
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        (2.0, 0.0, 0.0), (3.0, 0.0, 0.0), (2.0, 1.0, 0.0),
    )
    blob = bytearray(struct.pack("<4I", MAGIC, 135, 1337, len(positions)))
    for point in positions:
        blob += struct.pack("<3f", *point)
    for _ in positions:
        blob += struct.pack("<3f", 0.0, 0.0, 1.0)
    blob += bytes((10, 20, 30, 255)) * len(positions)
    blob += struct.pack("<I", 1)
    for uv in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (0.0, 1.0)):
        blob += struct.pack("<2f", *uv)
    blob += struct.pack("<I6H", 6, 0, 1, 2, 0, 1, 2)
    blob += struct.pack("<3I", 1, 1, 4)
    blob += struct.pack("<3I", 8, 9, 1)
    first_draw = course_record()
    tag5 = struct.pack("<I4fI", 5, 12.0, -3.5, 8.25, 4.0, 1) + first_draw
    blob += tag5
    blob += struct.pack("<2I", 1, 1)
    blob += course_record(base=3, index_start=3)
    blob += struct.pack("<I", 100) + b"synthetic BSP bytes"
    return bytes(blob)


class R5TCourseDxTests(unittest.TestCase):
    def setUp(self):
        self.data = synthetic_course_dx()

    def test_shared_prefix_and_course_draw_parse(self):
        prefix = parse_dx_common_prefix(self.data)
        model = parse_course_dx_bytes(self.data)
        self.assertEqual(prefix.word_0x04, 135)
        self.assertEqual(prefix.local_indices, (0, 1, 2, 0, 1, 2))
        self.assertEqual(len(model.physical_draws), 2)
        self.assertEqual(model.physical_draws[0].texture_tuple, ("track-tga", "Null"))
        self.assertTrue(model.course_render_validated)
        self.assertEqual(len(model.course_batches), 1)
        self.assertEqual(model.course_batches[0].record_count, 1)
        tag5_container = next(
            record for group in model.draw_groups for record in group.root.flattened()
            if record.tag == 5
        )
        self.assertEqual(tag5_container.opaque_prefix, struct.pack("<4fI", 12.0, -3.5, 8.25, 4.0, 1))
        self.assertEqual(model.collision.tag_ids, (100,))
        self.assertEqual(model.collision.bsp.tag_offset, model.trailing.offset)

    def test_revision_and_wrapper_fail_closed(self):
        old_revision = bytearray(self.data)
        struct.pack_into("<I", old_revision, 4, 131)
        with self.assertRaisesRegex(FormatError, "not the observed revision 135"):
            parse_course_dx_bytes(bytes(old_revision))

        bad_wrapper = bytearray(self.data)
        prefix = parse_dx_common_prefix(self.data)
        struct.pack_into("<I", bad_wrapper, prefix.draw_table_offset, 2)
        with self.assertRaisesRegex(FormatError, "unsupported course root preamble"):
            parse_course_dx_bytes(bytes(bad_wrapper))

    def test_truncated_common_and_auxiliary_sections_fail(self):
        parsed = parse_course_dx_bytes(self.data)
        with self.assertRaises(BoundsError):
            parse_course_dx_bytes(self.data[:parsed.trailing.offset - 1])
        bad_count = bytearray(self.data)
        struct.pack_into("<I", bad_count, parsed.course_batches[0].offset + 4, 100)
        with self.assertRaises(FormatError):
            parse_course_dx_bytes(bytes(bad_count))

    def test_course_metadata_retains_unknown_sections_and_blocks_authoring(self):
        model = parse_course_dx_bytes(self.data)
        metadata = mark_course_metadata({"round_trip": {"writer_available": True}}, model)
        self.assertFalse(metadata["round_trip"]["writer_available"])
        self.assertTrue(metadata["round_trip"]["read_only"])
        self.assertEqual(len(metadata["course"]["draw_batches"]), 1)
        opaque = metadata["course"]["opaque_course_data"]
        self.assertEqual(opaque["tag100"]["boundary_status"], "raw-length-unresolved")
        self.assertEqual(opaque["tag100"]["semantics"], "UNKNOWN")
        self.assertEqual(opaque["trailing_tag_ids"], [100])
        self.assertNotIn("collision", opaque)

class R5THntTests(unittest.TestCase):
    def test_parses_exact_records_and_resolves_without_basename_guessing(self):
        document = parse_hnt_bytes(
            b"Model [course\\italy1\\track01]\r\n"
            b"Texture [course\\italy1\\track-tga]\n"
            b"Mystery [course\\italy1\\unknown]\n"
            b"not a record\n",
            "Italy1.hnt",
        )
        self.assertEqual([entry.keyword for entry in document.entries], ["Model", "Texture"])
        self.assertEqual(document.unparsed_lines, ((3, "Mystery [course\\italy1\\unknown]"), (4, "not a record")))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            model = root / "Course" / "Italy1" / "track01.dx"
            texture = root / "Course" / "Italy1" / "track-tga.dxt"
            unrelated = root / "Other" / "track01.dx"
            for path in (model, texture, unrelated):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic")
            resolutions = resolve_hnt_entries(document, root)
        self.assertEqual([item.status for item in resolutions], ["resolved", "resolved"])
        self.assertTrue(resolutions[0].resolved_path.casefold().endswith("course/italy1/track01.dx"))


class R5TSflTests(unittest.TestCase):
    def test_exact_header_payload_and_malformed_sizes(self):
        data = struct.pack("<fIIff", 3.0, 3, 2, -10.5, 4.25) + bytes(range(6))
        field = parse_sfl_bytes(data)
        self.assertEqual((field.header.width, field.header.height), (3, 2))
        self.assertEqual(field.payload, bytes(range(6)))
        self.assertEqual(field.distinct_value_count, 6)
        with self.assertRaises(BoundsError):
            parse_sfl_bytes(data[:-1])
        with self.assertRaises(FormatError):
            parse_sfl_bytes(data + b"x")


if __name__ == "__main__":
    unittest.main()
