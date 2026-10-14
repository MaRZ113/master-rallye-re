"""Frozen metadata audit checks; no proprietary assets or game dependency."""
import hashlib
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]

class DeploymentInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((HERE / "deployment-inventory.json").read_text())
        cls.registry_path = PORT / "docs/full-coverage/courses/coverage-registry.json"
        cls.registry = json.loads(cls.registry_path.read_text())

    def test_complete_verified_snapshot_matches_registry(self):
        expected = {(row["course"], kind): value for row in self.registry["courses"] for kind, value in row["categories"].items()}
        observed = {(row["course"], row["category"]): row for row in self.data["rows"]}
        self.assertEqual(set(observed), set(expected))
        self.assertEqual(len(observed), 72)
        self.assertEqual(len({row["filename"] for row in observed.values()}), 72)
        self.assertEqual(hashlib.sha256(self.registry_path.read_bytes()).hexdigest(), self.data["source_registry_sha256"])
        for key, row in observed.items():
            self.assertEqual(row["expected_sha256"], expected[key]["artifact"]["sha256"])
            self.assertEqual(row["filename"], expected[key]["filename"])
            self.assertEqual(row["local_status"], "VERIFIED")
            self.assertEqual(row["point_count"], expected[key]["point_count"])

    def test_only_existing_three_courses_deployed_in_snapshot(self):
        installed = [row for row in self.data["rows"] if row["deployed_status"] == "VERIFIED"]
        self.assertEqual(len(installed), 6)
        self.assertEqual({row["course"] for row in installed}, {"TURKEY3", "FRANCE1", "ITALY_S1"})
        self.assertEqual(sum(row["deployed_status"] == "MISSING" for row in self.data["rows"]), 66)
        self.assertEqual(self.data["local_verified_count"], 72)
        self.assertEqual(self.data["deployed_verified_count"], 6)
        self.assertFalse(self.data["automatic_deployment"])

if __name__ == "__main__":
    unittest.main()
