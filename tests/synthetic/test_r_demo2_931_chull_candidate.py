from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from tools.scanner.r_demo2_931_chull_candidate import build_candidate


def fixture(*, share_hull_vector_with_body: bool = False) -> bytes:
    record_count = 3
    vectors_a = [float(axis == (index % 3)) for index in range(9) for axis in range(3)]
    vector_a = struct.pack("<27f", *vectors_a)
    vector_b = b""
    vectors_c = b"".join(struct.pack("<3f", *point) for point in (
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        (3.0, 0.0, 0.0), (4.0, 0.0, 0.0), (3.0, 1.0, 0.0),
    ))
    body = (0, 1, 2) if share_hull_vector_with_body else (3, 4, 5)
    records = []
    for c_indices in (body, (0, 1, 2), (0, 2, 1)):
        records.append(struct.pack("<10I", 0xFFFFFFFF, 0xFFFFFFFF,
                                   0xFFFFFFFF, 0xFFFFFFFF, *c_indices, 0, 1, 2))
    record_stream = records[0] + b"\xff" * 12 + records[1] + b"\xff" * 12 + records[2]
    header = struct.pack("<8I", 0x20702, 0, 0, 0, record_count * 3, 0,
                         record_count, 6)
    return header + vector_a + vector_b + b"\xff" * 12 + record_stream + vectors_c + b"TAIL"


class Demo931ChullCandidateTests(unittest.TestCase):
    def _sidecar(self, root: Path) -> Path:
        sidecar = root / "Trooper.txt"
        sidecar.write_text(
            "Materials(Size 0)\n"
            "moMesh(Name [body] Index 0 Size 1)\n"
            "moMesh(Name [$chull(Trooper)] Index 1 Size 2)\n",
            encoding="latin-1",
        )
        return sidecar

    def test_candidate_edits_only_derived_hull_vector_c_x_words(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = fixture()
            sidecar = self._sidecar(root)
            candidate, report = build_candidate(source, sidecar)

        indices = report["chull"]["unique_vector_c_indices"]
        self.assertEqual(indices, [0, 1, 2])
        self.assertEqual(report["modified_vector_count"], 3)
        self.assertEqual(report["translation_source_xyz"], [0.1, 0.0, 0.0])
        self.assertTrue(report["non_target_bytes_identical"])
        self.assertEqual(len(candidate), len(source))
        changed = [i for i, (a, b) in enumerate(zip(source, candidate)) if a != b]
        approved = {offset for field in report["allowed_target_x_field_ranges_end_exclusive"]
                    for offset in range(field["start"], field["end_exclusive"])}
        self.assertTrue(changed)
        self.assertLessEqual(set(changed), approved)
        self.assertEqual(report["offsets"]["vector_c"], 32 + 9 * 12 + 12 + 3 * 52 - 12)
        self.assertEqual(report["masked_source_sha256"], report["masked_candidate_sha256"])

    def test_rejects_hull_vectors_shared_with_body(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sidecar = self._sidecar(root)
            with self.assertRaisesRegex(ValueError, "shared with other mesh"):
                build_candidate(fixture(share_hull_vector_with_body=True), sidecar)


if __name__ == "__main__":
    unittest.main()
