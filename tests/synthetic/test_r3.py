from __future__ import annotations

import hashlib
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "src", ROOT / "tests" / "blender"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from generate_fixture import POSITIONS, build_dx
from master_rallye.authoring import (
    INVALID_PROVENANCE,
    POSITIONS_ONLY_CHANGED,
    SOURCE_IDENTICAL,
    UNSUPPORTED_TOPOLOGY_CHANGED,
    provenance_fingerprint,
    validate_authoring_state,
)
from master_rallye.coords import (
    blender_position_to_source,
    position_to_blender,
)
from master_rallye.dx import parse_dx_bytes
from master_rallye.dx_writer import (
    audit_binary_diff,
    patch_dx_positions,
    write_dx_positions,
)
from master_rallye.errors import DxWriteError


class DxWriterTests(unittest.TestCase):
    def setUp(self):
        self.template = build_dx()
        self.model = parse_dx_bytes(self.template)

    def test_zero_edit_is_byte_identical(self):
        result = patch_dx_positions(self.template, self.model.vertices.positions)
        self.assertTrue(result.byte_identical)
        self.assertEqual(result.data, self.template)
        self.assertEqual(result.diff.changed_byte_count, 0)
        self.assertEqual(result.changes, ())

    def test_single_and_multiple_position_changes_are_confined(self):
        positions = list(self.model.vertices.positions)
        positions[0] = (0.125, 0.0, 0.0)
        one = patch_dx_positions(self.template, positions)
        self.assertEqual([item.vertex_index for item in one.changes], [0])
        self.assertTrue(one.diff.valid)
        start = self.model.vertices.position_offset
        self.assertTrue(
            all(start <= item.start and item.end <= start + 12 for item in one.diff.changed_ranges)
        )
        positions[1] = (0.875, 0.125, 0.0)
        two = patch_dx_positions(self.template, positions)
        self.assertEqual([item.vertex_index for item in two.changes], [0, 1])
        self.assertTrue(two.output_model.diagnostics.validated)
        self.assertEqual(two.output_model.local_indices, self.model.local_indices)

    def test_external_change_is_detected(self):
        changed = bytearray(self.template)
        changed[self.model.vertices.normal_offset] ^= 1
        audit = audit_binary_diff(
            self.template,
            bytes(changed),
            ((self.model.vertices.position_offset, self.model.vertices.position_buffer_end),),
        )
        self.assertFalse(audit.valid)
        self.assertEqual(audit.unexpected_ranges[0].start, self.model.vertices.normal_offset)

    def test_invalid_positions_and_count_are_rejected(self):
        with self.assertRaisesRegex(DxWriteError, "position count"):
            patch_dx_positions(self.template, self.model.vertices.positions[:-1])
        values = list(self.model.vertices.positions)
        values[0] = (math.nan, 0.0, 0.0)
        with self.assertRaisesRegex(DxWriteError, "non-finite"):
            patch_dx_positions(self.template, values)

    def test_safe_bounds_rejects_outside_edit(self):
        values = list(self.model.vertices.positions)
        values[0] = (-0.01, 0.0, 0.0)
        with self.assertRaisesRegex(DxWriteError, "outside original AABB"):
            patch_dx_positions(self.template, values)
        unrestricted = patch_dx_positions(
            self.template,
            values,
            safe_bounds=False,
        )
        self.assertEqual(len(unrestricted.changes), 1)

    def test_source_hash_and_overwrite_safety(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.dx"
            output = Path(directory) / "output.dx"
            source.write_bytes(self.template)
            digest = hashlib.sha256(self.template).hexdigest()
            with self.assertRaisesRegex(DxWriteError, "overwrite"):
                write_dx_positions(
                    source,
                    source,
                    self.model.vertices.positions,
                    expected_source_sha256=digest,
                )
            with self.assertRaisesRegex(DxWriteError, "SHA-256 mismatch"):
                write_dx_positions(
                    source,
                    output,
                    self.model.vertices.positions,
                    expected_source_sha256="0" * 64,
                )
            result = write_dx_positions(
                source,
                output,
                self.model.vertices.positions,
                expected_source_sha256=digest,
            )
            self.assertTrue(result.byte_identical)
            self.assertEqual(output.read_bytes(), self.template)

    def test_coordinate_inverse_round_trip(self):
        for source in (
            (0.0, 0.0, 0.0),
            (1.25, -2.5, 3.75),
            (-4.0, 5.5, -6.25),
            (-0.0, 0.0, -0.0),
        ):
            self.assertEqual(
                blender_position_to_source(position_to_blender(source)),
                tuple(float(value) for value in source),
            )


class AuthoringProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.positions = tuple(position_to_blender(value) for value in POSITIONS)
        self.faces = ((1, 0, 2), (2, 0, 3))
        self.source_vertex_ids = (0, 1, 2, 3)
        self.source_triangle_ids = (0, 1)
        self.draw_ids = (0, 1)
        self.group_ids = (0, 0)
        self.expected_geometry = self._geometry_fingerprint()
        self.expected_provenance = provenance_fingerprint(
            self.faces,
            self.source_vertex_ids,
            self.source_triangle_ids,
            self.draw_ids,
            self.group_ids,
        )

    def _geometry_fingerprint(self):
        from master_rallye.coords import geometry_fingerprint
        return geometry_fingerprint(self.positions, self.faces)

    def validate(self, **overrides):
        values = {
            "positions": self.positions,
            "faces": self.faces,
            "source_vertex_ids": self.source_vertex_ids,
            "source_vertex_valid": (True,) * 4,
            "source_triangle_ids": self.source_triangle_ids,
            "draw_ids": self.draw_ids,
            "group_ids": self.group_ids,
            "expected_vertex_count": 4,
            "expected_face_count": 2,
            "expected_geometry_fingerprint": self.expected_geometry,
            "expected_provenance_fingerprint": self.expected_provenance,
        }
        values.update(overrides)
        return validate_authoring_state(**values)

    def test_identical_and_positions_only_status(self):
        self.assertEqual(self.validate().status, SOURCE_IDENTICAL)
        changed = list(self.positions)
        changed[0] = (0.125, changed[0][1], changed[0][2])
        result = self.validate(positions=changed)
        self.assertEqual(result.status, POSITIONS_ONLY_CHANGED)
        self.assertTrue(result.exportable)

    def test_duplicate_missing_and_invalid_source_ids_are_rejected(self):
        duplicate = self.validate(source_vertex_ids=(0, 0, 2, 3))
        self.assertEqual(duplicate.status, INVALID_PROVENANCE)
        self.assertTrue(any("duplicate" in error for error in duplicate.errors))
        invalid = self.validate(source_vertex_valid=(True, False, True, True))
        self.assertEqual(invalid.status, INVALID_PROVENANCE)

    def test_topology_face_count_and_draw_changes_are_rejected(self):
        topology = self.validate(faces=((0, 1, 2), (2, 0, 3)))
        self.assertEqual(topology.status, UNSUPPORTED_TOPOLOGY_CHANGED)
        face_count = self.validate(
            faces=self.faces[:1],
            source_triangle_ids=(0,),
            draw_ids=(0,),
            group_ids=(0,),
        )
        self.assertEqual(face_count.status, UNSUPPORTED_TOPOLOGY_CHANGED)
        draw = self.validate(draw_ids=(1, 1))
        self.assertEqual(draw.status, UNSUPPORTED_TOPOLOGY_CHANGED)


if __name__ == "__main__":
    unittest.main()
