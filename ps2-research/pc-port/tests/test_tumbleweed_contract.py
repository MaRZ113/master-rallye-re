"""Original-source conversion boundaries; synthetic hulls are not game assets."""
from __future__ import annotations

import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import unittest

PORT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_tumbleweed_contract",
                                             PORT / "tools/prepare_tumbleweed_contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
SDK = Path(os.environ.get("PS2_COURSE_SDK_ROOT", str(contract.DEFAULT_SDK)))
CORPUS = Path(os.environ.get("PS2_TUMBLEWEED_CORPUS", "D:/Game/Master Rallye PS2"))


def synthetic_tetrahedron():
    """Independent counted-wire fixture, not derived from original hull data."""
    vertices = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
    faces = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))
    edges = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))

    def geometry(points, triangles):
        data = struct.pack("<2i", len(points), len(triangles))
        data += b"".join(struct.pack("<3f", *p) for p in points)
        data += b"".join(struct.pack("<3i", *p) for p in triangles)
        return data

    rep = geometry(vertices, faces) + geometry(((.25, .25, .25),), ())
    rep += struct.pack("<5i", 4, 0, 1, 2, 3)
    rep += struct.pack("<i", len(edges)) + b"".join(struct.pack("<2i", *e) for e in edges)
    rep += struct.pack("<i", len(faces))
    for face in faces:
        rep += struct.pack("<4i", 3, *face) + struct.pack("<4i", 3, *face)
    for edge in edges:
        adjacent = tuple(i for i, face in enumerate(faces) if set(edge).issubset(face))
        rep += struct.pack("<2i", *adjacent)
    for face in faces:
        loop = tuple(i for i, edge in enumerate(edges) if set(edge).issubset(face))
        rep += struct.pack("<4i", 3, *loop)
    rep += struct.pack("<4f", .5, .5, .5, math.sqrt(3.) / 2.)
    return (struct.pack("<I", 101) + geometry(((.25, .25, .25),), ())
            + struct.pack("<f", 1.) + rep + rep)


class IdentityAndStorageTests(unittest.TestCase):
    def test_source_sha_is_required(self):
        contract.checked_identity(b"synthetic", contract.sha(b"synthetic"), "fixture")
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            contract.checked_identity(b"changed", contract.sha(b"synthetic"), "fixture")

    def test_raw_original_output_is_confined(self):
        allowed = PORT / ".assets/rigid/synthetic.tag101"
        self.assertEqual(contract.raw_output_path(allowed), allowed.resolve())
        for value in (PORT / "docs/rigid-port1/collision.bin", PORT / ".assets/rigid",
                      PORT / "../../modernization/renderer/collision.bin"):
            with self.subTest(path=str(value)), self.assertRaises(ValueError):
                contract.raw_output_path(value)


@unittest.skipUnless((SDK / "src/master_rallye/collision_writer.py").is_file(),
                     "Read-only Course SDK collision.py/collision_writer.py dependency unavailable")
class NativeWireTests(unittest.TestCase):
    def test_independent_synthetic_wire_roundtrip(self):
        raw = synthetic_tetrahedron()
        hull = contract.validate_native_wire(raw, SDK, contract.sha(raw))
        self.assertEqual(hull.representation_a.geometry_a.vertex_count, 4)
        self.assertEqual(hull.representation_b.geometry_a.triangle_count, 4)
        rows = contract.wire_accounting(hull)
        self.assertEqual(sum(row["bytes"] for row in rows), len(raw))
        self.assertEqual(rows[0], {"section": "dispatch_tag", "wire_offset": 0, "bytes": 4})
        self.assertEqual(rows[1]["wire_offset"], 4)

    def test_wrong_source_and_dispatch_fail_closed(self):
        raw = synthetic_tetrahedron()
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            contract.validate_native_wire(raw, SDK, "00" * 32)
        with self.assertRaisesRegex(ValueError, "dispatch word"):
            contract.validate_native_wire(struct.pack("<I", 100) + raw[4:], SDK)

    def test_unknown_trailer_and_duplicate_hull_fail_closed(self):
        raw = synthetic_tetrahedron()
        with self.assertRaisesRegex(ValueError, "entire bounded stream"):
            contract.validate_native_wire(raw + b"\xff\xff\xff\xff", SDK)
        with self.assertRaises(Exception) as caught:
            contract.validate_native_wire(raw + raw, SDK)
        self.assertIn("duplicate tag101", str(caught.exception))

    def test_truncated_and_negative_count_fail_closed(self):
        raw = synthetic_tetrahedron()
        with self.assertRaises(Exception) as caught:
            contract.validate_native_wire(raw[:-1], SDK)
        self.assertIn("need", str(caught.exception))
        changed = bytearray(raw)
        struct.pack_into("<i", changed, 4, -1)
        with self.assertRaises(Exception) as caught:
            contract.validate_native_wire(bytes(changed), SDK)
        self.assertIn("unreasonable count", str(caught.exception))

    def test_nonfinite_and_out_of_range_index_fail_closed(self):
        raw = synthetic_tetrahedron()
        changed = bytearray(raw)
        struct.pack_into("<f", changed, 12, float("nan"))
        with self.assertRaises(Exception) as caught:
            contract.validate_native_wire(bytes(changed), SDK)
        self.assertIn("non-finite", str(caught.exception))
        changed = bytearray(raw)
        # Independent fixture: outer/base/scalar = 28; rep-A counts/XYZ = 56.
        struct.pack_into("<i", changed, 84, 99)
        with self.assertRaises(Exception) as caught:
            contract.validate_native_wire(bytes(changed), SDK)
        self.assertIn("outside", str(caught.exception))


@unittest.skipUnless((CORPUS / "TNG.000").is_file()
                     and (SDK / "src/master_rallye/collision_writer.py").is_file(),
                     "Canonical private PS2 corpus and read-only Course SDK required")
class CanonicalSourceTests(unittest.TestCase):
    def test_original_source_and_native_wire_known_answers(self):
        report, raw = contract.prepare(CORPUS, SDK)
        self.assertEqual(report["scene"]["authored_record_count"], 6)
        self.assertEqual(report["selected_source"]["source_id"], contract.SOURCE_ID)
        self.assertEqual(report["selected_source"]["matrix_sha256"], contract.MATRIX_SHA)
        self.assertEqual(report["selected_source"]["resolved"]["mass"], 5.)
        self.assertEqual(report["selected_source"]["resolved"]["moi"], (2., 2., 2.))
        self.assertEqual(len(raw), 4612)
        self.assertEqual(contract.sha(raw), contract.TAG101_SHA)
        self.assertEqual(report["native_collision_wire"]["registration"].split(";")[0], "UNKNOWN")
        self.assertFalse(report["native_collision_wire"]["replacement_hay_hull"])
        self.assertEqual(report["runtime_validation"], "NOT_PERFORMED")
        self.assertEqual(report["model"]["visual"]["vertex_records"], 96)
        self.assertEqual(report["model"]["visual"]["nonsuppressed_nondegenerate_triangles"], 48)

    def test_compact_metadata_and_deterministic_output(self):
        left, left_wire = contract.prepare(CORPUS, SDK)
        right, right_wire = contract.prepare(CORPUS, SDK)
        self.assertEqual(left_wire, right_wire)
        self.assertEqual(json.dumps(left, sort_keys=True), json.dumps(right, sort_keys=True))
        self.assertNotIn('"vertices": [', json.dumps(left))
        self.assertNotIn('"triangles": [', json.dumps(left))


if __name__ == "__main__":
    unittest.main()
