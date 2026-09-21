from __future__ import annotations

import json
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
    blender_position_to_source,
    geometry_fingerprint,
    normal_to_authoring,
    position_to_authoring,
    position_to_blender,
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
        self.assertEqual(blender_position_to_source((1, -3, 2)), (1.0, 2.0, 3.0))
        self.assertEqual(triangles_from_indices((1, 0, 2, 4, 3, 5)), ((1, 0, 2), (4, 3, 5)))

    def test_uv_transform_is_only_v_flip(self):
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
        self.assertNotEqual(source, geometry_fingerprint(((0, 0, 0), (2, 0, 0), (0, 1, 0)), triangles))
        self.assertNotEqual(source, geometry_fingerprint(positions, ((0, 1, 2),)))


class BlenderAddonBuildTests(unittest.TestCase):
    def test_build_contains_addon_and_vendored_canonical_library_only(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "addon.zip"
            result = build(output, ROOT)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                manifest = json.loads(archive.read("master_rallye_io/build_manifest.json"))
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
