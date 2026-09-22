from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from master_rallye.roles import (
    _select_structural_sidecar,
    classify_mesh_name,
    multiset_similarity,
)


class VehicleRoleAnalysisTests(unittest.TestCase):
    def test_literal_mesh_evidence_classification_is_conservative(self):
        self.assertEqual(classify_mesh_name("driver01"), ("crew",))
        self.assertEqual(classify_mesh_name("screenfrontb"), ("glass",))
        self.assertEqual(classify_mesh_name("$chull(Astero)"), ("collision_hull_named",))
        self.assertEqual(classify_mesh_name("wheel $cylinder_0.766_0.39"), ("wheel",))
        self.assertEqual(classify_mesh_name("hub 03"), ("hub",))
        self.assertNotIn("wheel", classify_mesh_name("wheelarches"))
        self.assertNotIn("wheel", classify_mesh_name("steeringwheel"))
        self.assertNotIn("wheel", classify_mesh_name("wheelspare $rubber"))

    def test_multiset_similarity_requires_multiplicity(self):
        exact = Counter({(1.0, 2.0, 3.0): 2, (2.0, 2.0, 2.0): 1})
        same = Counter({(2.0, 2.0, 2.0): 1, (1.0, 2.0, 3.0): 2})
        missing = Counter({(1.0, 2.0, 3.0): 1, (2.0, 2.0, 2.0): 1})
        self.assertEqual(multiset_similarity(exact, same), 1.0)
        self.assertLess(multiset_similarity(exact, missing), 1.0)

    def test_structural_sidecar_prefers_exact_then_closest_mesh_span(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            exact_path = directory / "car.txt"
            exact_path.write_text(
                "Materials(Size 0)\nmoMesh(Name [body] Index 0 Size 10)\n",
                encoding="latin-1",
            )
            model = SimpleNamespace(triangle_count=10)
            selected, path, reason = _select_structural_sidecar(
                directory / "car.dx", model, None, None
            )
            self.assertEqual(path, exact_path)
            self.assertEqual(reason, "exact-stem")
            self.assertEqual(selected.mesh_span, 10)

            exact_path.unlink()
            (directory / "complete.txt").write_text(
                "Materials(Size 0)\nmoMesh(Name [body] Index 0 Size 40)\n",
                encoding="latin-1",
            )
            candidate_path = directory / "VehicleWheel.txt"
            candidate_path.write_text(
                "Materials(Size 0)\nmoMesh(Name [wheel] Index 0 Size 10)\n",
                encoding="latin-1",
            )
            selected, path, reason = _select_structural_sidecar(
                directory / "wheel.dx", model, None, None
            )
            self.assertEqual(path, candidate_path)
            self.assertEqual(reason, "closest-mesh-span")
            self.assertEqual(selected.mesh_span, 10)


if __name__ == "__main__":
    unittest.main()
