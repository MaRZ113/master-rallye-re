from __future__ import annotations

import hashlib
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for item in (ROOT, ROOT / "src", ROOT / "tools", ROOT / "tests" / "synthetic"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

import r5t_f1_tag100_swap as swap  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402
from master_rallye.errors import FormatError  # noqa: E402
from test_r5t_a import synthetic_course_dx  # noqa: E402


def fixture_dx(*, prefix_extension: bytes = b"", tag_payload: bytes = b"synthetic BSP bytes", revision: int = 135) -> bytes:
    source = synthetic_course_dx()
    parsed = parse_course_dx_bytes(source)
    prefix = source[:parsed.collision.bsp.tag_offset]
    result = bytearray(prefix + prefix_extension + struct.pack("<I", 100) + tag_payload)
    struct.pack_into("<I", result, 4, revision)
    return bytes(result)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class R5TF1Tag100SwapTests(unittest.TestCase):
    def setUp(self):
        self.baseline = fixture_dx()
        self.modified = fixture_dx(
            prefix_extension=struct.pack("<2I", 1, 0),
            tag_payload=b"modified synthetic tag100 with unequal length",
        )
        self.baseline_regions = swap.parse_regions(self.baseline, "baseline")
        self.modified_regions = swap.parse_regions(self.modified, "modified")

    def build(self, baseline: bytes | None = None, modified: bytes | None = None, **overrides):
        return swap.build_reciprocal_bytes(
            self.baseline if baseline is None else baseline,
            self.modified if modified is None else modified,
            expected_baseline_tag_sha256=overrides.get(
                "expected_baseline_tag_sha256", digest(self.baseline_regions.tag100)
            ),
            expected_modified_tag_sha256=overrides.get(
                "expected_modified_tag_sha256", digest(self.modified_regions.tag100)
            ),
            expected_baseline_dx_sha256=overrides.get("expected_baseline_dx_sha256"),
            expected_modified_dx_sha256=overrides.get("expected_modified_dx_sha256"),
        )

    def test_parser_derived_tag100_split_boundary(self):
        parsed = parse_course_dx_bytes(self.baseline)
        regions = swap.parse_regions(self.baseline, "fixture")

        self.assertEqual(regions.tag_offset, parsed.collision.bsp.tag_offset)
        self.assertEqual(regions.tag_end, len(self.baseline))
        self.assertEqual(regions.prefix, self.baseline[:regions.tag_offset])
        self.assertEqual(regions.tag100, self.baseline[regions.tag_offset:])

    def test_reciprocal_hybrids_use_selected_prefix_donors(self):
        regions, hybrids = self.build()

        self.assertEqual(hybrids["hybrid-a"][:], regions["baseline"].prefix + regions["modified"].tag100)
        self.assertEqual(hybrids["hybrid-b"][:], regions["modified"].prefix + regions["baseline"].tag100)

    def test_reciprocal_hybrids_preserve_tag100_donor_bytes(self):
        regions, hybrids = self.build()

        self.assertEqual(swap.parse_regions(hybrids["hybrid-a"], "A").tag100, regions["modified"].tag100)
        self.assertEqual(swap.parse_regions(hybrids["hybrid-b"], "B").tag100, regions["baseline"].tag100)

    def test_unequal_tag100_sizes_are_supported(self):
        _, hybrids = self.build()

        self.assertNotEqual(len(self.baseline_regions.tag100), len(self.modified_regions.tag100))
        self.assertEqual(
            len(swap.parse_regions(hybrids["hybrid-a"], "A").tag100),
            len(self.modified_regions.tag100),
        )
        self.assertEqual(
            len(swap.parse_regions(hybrids["hybrid-b"], "B").tag100),
            len(self.baseline_regions.tag100),
        )

    def test_unequal_prefix_sizes_are_supported(self):
        regions, _ = self.build()

        self.assertNotEqual(len(regions["baseline"].prefix), len(regions["modified"].prefix))
        self.assertEqual(regions["baseline"].tag_offset, len(regions["baseline"].prefix))
        self.assertEqual(regions["modified"].tag_offset, len(regions["modified"].prefix))

    def test_hybrid_total_size_is_sum_of_selected_regions(self):
        regions, hybrids = self.build()

        self.assertEqual(
            len(hybrids["hybrid-a"]),
            len(regions["baseline"].prefix) + len(regions["modified"].tag100),
        )
        self.assertEqual(
            len(hybrids["hybrid-b"]),
            len(regions["modified"].prefix) + len(regions["baseline"].tag100),
        )

    def test_expected_tag100_hashes_are_enforced(self):
        regions, _ = self.build()

        self.assertEqual(digest(regions["baseline"].tag100), digest(self.baseline_regions.tag100))
        self.assertEqual(digest(regions["modified"].tag100), digest(self.modified_regions.tag100))

    def test_wrong_donor_tag100_hash_is_refused(self):
        with self.assertRaisesRegex(ValueError, "tag100 SHA-256"):
            self.build(expected_baseline_tag_sha256="0" * 64)

    def test_wrong_donor_full_dx_hash_is_refused(self):
        with self.assertRaisesRegex(ValueError, "donor DX SHA-256"):
            self.build(expected_modified_dx_sha256="0" * 64)

    def test_missing_tag100_is_refused(self):
        missing = self.baseline_regions.prefix + b"NOPE" + b"opaque tail"
        with self.assertRaisesRegex(ValueError, "did not find trailing tag100"):
            swap.parse_regions(missing, "missing-tag")

    def test_unsupported_revision_is_refused_by_course_parser(self):
        unsupported = fixture_dx(revision=131)

        with self.assertRaisesRegex(FormatError, "not the observed revision 135"):
            swap.parse_regions(unsupported, "revision-131")

    def test_literal_swap_is_parser_validated_as_synthetic_rev135_course(self):
        _, hybrids = self.build()

        for name, data in hybrids.items():
            model = parse_course_dx_bytes(data, name)
            self.assertEqual(model.word_0x04, 135)
            self.assertTrue(model.course_render_validated)
            self.assertEqual(model.collision.errors, ())
            self.assertEqual(model.collision.unparsed_data, b"")
            self.assertIsNotNone(model.collision.bsp)

    def test_tool_does_not_expose_a_course_dx_writer(self):
        self.assertTrue(swap.__doc__.startswith("R5T-F.1 research-only"))
        self.assertFalse(hasattr(swap, "write_course_dx"))
        self.assertFalse(hasattr(swap, "serialize_course_dx"))


if __name__ == "__main__":
    unittest.main()
