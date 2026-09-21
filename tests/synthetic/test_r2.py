from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
for path in (SRC, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.coords import (
    AUTHORING_SCALE,
    BLENDER_PREVIEW_UV_POLICY,
    GLTF_PREVIEW_UV_POLICY,
    analyze_normals,
    blender_position_to_source,
    expand_corner_normals,
    geometry_fingerprint,
    normal_to_authoring,
    position_to_authoring,
    position_to_blender,
    prepare_display_normals,
    transform_uv_values,
    triangles_from_indices,
)
from build_blender_addon import build


class CoordinatePolicyTests(unittest.TestCase):
    def test_native_position_normal_scale_and_winding_are_preserved(self):
        self.assertEqual(AUTHORING_SCALE, 1.0)
        self.assertEqual(position_to_authoring((1, -2, 3.5)), (1.0, -2.0, 3.5))
        self.assertEqual(normal_to_authoring((0, 0, 1)), (0.0, 0.0, 1.0))
        self.assertEqual(position_to_blender((1, 2, 3)), (1.0, -3.0, 2.0))
        self.assertEqual(
            blender_position_to_source((1, -3, 2)),
            (1.0, 2.0, 3.0),
        )
        self.assertEqual(
            triangles_from_indices((1, 0, 2, 4, 3, 5)),
            ((1, 0, 2), (4, 3, 5)),
        )

    def test_blender_and_gltf_uv_policies_are_independent(self):
        self.assertEqual(GLTF_PREVIEW_UV_POLICY, "flip-v")
        self.assertEqual(BLENDER_PREVIEW_UV_POLICY, "direct-v")
        values = ((0.125, 0.2), (0.875, 0.7))
        self.assertEqual(transform_uv_values(values, False), values)
        flipped = transform_uv_values(values, True)
        self.assertEqual(flipped[0][0], values[0][0])
        self.assertAlmostEqual(flipped[0][1], 0.8)
        self.assertEqual(flipped[1][0], values[1][0])
        self.assertAlmostEqual(flipped[1][1], 0.3)

    def test_geometry_fingerprint_detects_coordinate_and_topology_changes(self):
        positions = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
        triangles = ((1, 0, 2),)
        source = geometry_fingerprint(positions, triangles)
        self.assertEqual(source, geometry_fingerprint(positions, triangles))
        self.assertNotEqual(
            source,
            geometry_fingerprint(((0, 0, 0), (2, 0, 0), (0, 1, 0)), triangles),
        )
        self.assertNotEqual(
            source,
            geometry_fingerprint(positions, ((0, 1, 2),)),
        )


class NormalPolicyTests(unittest.TestCase):
    def test_non_unit_normals_are_normalized_only_for_display(self):
        source = ((0.0, 0.0, 2.0), (0.0, 3.0, 0.0))
        display, diagnostics, reason = prepare_display_normals(source, 2)
        self.assertIsNone(reason)
        self.assertEqual(source[0], (0.0, 0.0, 2.0))
        self.assertAlmostEqual(diagnostics.min_magnitude, 2.0)
        self.assertAlmostEqual(diagnostics.max_magnitude, 3.0)
        self.assertTrue(all(math.isclose(sum(c * c for c in value), 1.0) for value in display))

    def test_per_corner_candidate_expands_shared_vertices(self):
        display, diagnostics, reason = prepare_display_normals(
            ((0.0, 0.0, 2.0),) * 4,
            4,
        )
        self.assertIsNone(reason)
        self.assertEqual(diagnostics.count, 4)
        corners = expand_corner_normals(display, (0, 1, 2, 0, 2, 3))
        self.assertEqual(len(corners), 6)
        self.assertEqual(corners[0], corners[3])
        self.assertEqual(corners[2], corners[4])
        with self.assertRaises(ValueError):
            expand_corner_normals(display, (4,))

    def test_zero_length_normal_uses_fallback(self):
        display, diagnostics, reason = prepare_display_normals(
            ((0.0, 0.0, 0.0),),
            1,
        )
        self.assertIsNone(display)
        self.assertEqual(diagnostics.near_zero_count, 1)
        self.assertIn("zero/near-zero", reason)

    def test_non_finite_normal_uses_fallback(self):
        values = ((float("nan"), 0.0, 1.0), (0.0, float("inf"), 1.0))
        display, diagnostics, reason = prepare_display_normals(values, 2)
        self.assertIsNone(display)
        self.assertEqual(diagnostics.non_finite_count, 2)
        self.assertIn("non-finite", reason)
        self.assertEqual(analyze_normals(values).count, 2)

    def test_normal_count_mismatch_uses_fallback(self):
        display, diagnostics, reason = prepare_display_normals(
            ((0.0, 0.0, 1.0),),
            2,
        )
        self.assertIsNone(display)
        self.assertEqual(diagnostics.count, 1)
        self.assertIn("differs from vertex count", reason)


class BlenderAddonBuildTests(unittest.TestCase):
    def test_build_contains_addon_and_vendored_canonical_library_only(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "addon.zip"
            result = build(output, ROOT)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                manifest = json.loads(
                    archive.read("master_rallye_io/build_manifest.json")
                )
        self.assertEqual(result["addon_module"], "master_rallye_io")
        self.assertEqual(manifest["source_of_truth"], "src/master_rallye")
        self.assertIn("master_rallye_io/__init__.py", names)
        self.assertIn("master_rallye_io/vendor/master_rallye/dx.py", names)
        self.assertFalse(any(name.startswith("master_rallye/") for name in names))
        forbidden = (".dx", ".dxt", ".png", ".blend", ".gltf", ".bin", ".pyc")
        self.assertFalse(any(name.lower().endswith(forbidden) for name in names))
        self.assertFalse(any("__pycache__" in name for name in names))


if __name__ == "__main__":
    unittest.main()
