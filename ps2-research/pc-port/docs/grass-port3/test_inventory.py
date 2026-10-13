"""Corpus-independent tests for GRASS3 metadata, exact tokens and provenance."""
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("grass3_inventory", HERE / "inventory.py")
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class SyntheticModel:
    materials = ["ground $detail(grass)", "ground $detail(shrubs)", "ground $detail(shrub)", "ground"]
    material_offsets = [100, 120, 140, 160]
    bindings = {0: 0, 1: 1, 2: 2, 3: 3}
    reverse = False

    def surface(self, _):
        points = ((0., 0., 0.), (0., 0., 1.), (1., 0., 0.))
        return tuple(reversed(points)) if self.reverse else points


class InventoryTests(unittest.TestCase):
    def test_exact_categories_and_singular_rejection(self):
        result = inventory.category_inventory(SyntheticModel())
        self.assertEqual(result["categories"]["grass"]["slope_eligible_float32"], 1)
        self.assertEqual(result["categories"]["shrubs"]["slope_eligible_float32"], 1)
        self.assertEqual(result["materials"][2]["detail_category"], "unrecognized")
        self.assertEqual(result["materials"][3]["detail_category"], "none")

    def test_original_winding_is_not_repaired(self):
        model = SyntheticModel()
        model.reverse = True
        result = inventory.category_inventory(model)
        self.assertTrue(all(c["slope_eligible_float32"] == 0 for c in result["categories"].values()))

    def test_binding_order_does_not_change_digest(self):
        a, b = SyntheticModel(), SyntheticModel()
        b.bindings = dict(reversed(list(a.bindings.items())))
        self.assertEqual(inventory.category_inventory(a), inventory.category_inventory(b))

    def test_material_identity_changes_source_digest(self):
        a, b = SyntheticModel(), SyntheticModel()
        b.materials = a.materials + [a.materials[0]]
        b.material_offsets = a.material_offsets + [180]
        b.bindings = dict(a.bindings, **{})
        b.bindings[0] = 4
        x, y = inventory.category_inventory(a), inventory.category_inventory(b)
        self.assertNotEqual(x["categories"]["grass"]["eligible_source_digest"],
                            y["categories"]["grass"]["eligible_source_digest"])

    def test_original_token_case_boundary(self):
        self.assertEqual(inventory.detail.directive_contract("x $detail(GRASS)")["detail_category"], "grass")
        self.assertEqual(inventory.detail.directive_contract("x $DETAIL(grass)")["detail_category"], "none")

    def test_all_course_inventory_has_source_provenance(self):
        result = json.loads((HERE / "course-inventory.json").read_text())
        self.assertEqual(result["summary"]["courses"], 36)
        self.assertEqual(len({row["course"] for row in result["courses"]}), 36)
        self.assertEqual(result["summary"]["grass_eligible_courses"], 36)
        self.assertEqual(result["summary"]["shrubs_eligible_courses"], 36)
        self.assertEqual(len(result["canonical_inputs"]), 4)
        for row in result["courses"]:
            self.assertEqual(len(row["psm_sha256"]), 64)
            self.assertEqual(row["representation"], "PS2_SPATIAL_TRIANGLE")
            self.assertEqual(row["runtime_visibility"], "UNKNOWN")

    def test_selected_assets_keep_course_and_category_separate(self):
        reports = [json.loads((HERE / name).read_text()) for name in ("france1-placement.json", "italys1-placement.json")]
        hashes = []
        for report in reports:
            for category in ("grass", "shrubs"):
                entry = report["categories"][category]
                self.assertLessEqual(entry["strict_matched_triangles"], entry["eligible_triangles"])
                self.assertLessEqual(entry["reconstructed_point_count"], 250000)
                self.assertEqual(entry["artifact"]["psm_sha256"], report["source_psm_sha256"])
                hashes.append(entry["artifact"]["sha256"])
        self.assertEqual(len(set(hashes)), 4)

    def test_scene_id_is_not_the_landscape_folder(self):
        result = json.loads((HERE / "course-admission-contract.json").read_text())
        italy = next(row for row in result["approved_candidates"] if row["landscape_id"] == "ITALY_S1")
        self.assertEqual(italy["native_certificate_id"], "RaceTest/ItalyS1")
        self.assertEqual(italy["pc_scene"], "DataScene/RaceTest/ItalyS1.xml")
        self.assertIn("RaceTest/Italy_S1", result["negative_controls"])


if __name__ == "__main__":
    unittest.main()
