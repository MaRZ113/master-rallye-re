"""Corpus-independent source metadata and synthetic admission boundary checks."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("frontend_identity_audit", HERE / "audit.py")
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.source = [{"source_id": "synthetic:" + str(n), "draw_index": n,
                        "vertices": vertices, "index_start": start,
                        "triangles": tris, "geometry_sha256": "synthetic" + str(n)}
                       for n, (vertices, start, tris) in enumerate([(4, 0, 2), (3, 6, 1)])]
        self.live = [{"args": [4, 999, d["vertices"], d["index_start"] + 42, d["triangles"]]}
                     for d in reversed(self.source)]

    def test_different_native_order_and_relative_indices(self):
        joined = A.layout_join(self.source, self.live)
        self.assertEqual(joined["status"], "COMPLETE_SET_LAYOUT_CORRELATION")
        self.assertEqual(joined["index_start_offset"], 42)
        self.assertEqual([p["source_draw"] for p in joined["matches"]], [0, 1])
        self.assertFalse(joined["suppression_authorized"])
        self.assertIn("mirror", joined["missing_link"])

    def test_partial_draw_set_rejected(self):
        self.assertEqual(A.layout_join(self.source, self.live[:1])["status"], "INCOMPLETE_DRAW_SET")

    def test_different_count_rejected(self):
        self.live[0]["args"][4] += 1
        self.assertEqual(A.layout_join(self.source, self.live)["status"], "LAYOUT_NOT_FOUND")

    def test_same_counts_wrong_index_range_rejected(self):
        self.live[0]["args"][3] += 3
        self.assertEqual(A.layout_join(self.source, self.live)["status"], "LAYOUT_NOT_FOUND")

    def test_duplicated_source_layout_not_used(self):
        self.source[1] = copy.deepcopy(self.source[0])
        self.live[1] = copy.deepcopy(self.live[0])
        self.assertEqual(A.layout_join(self.source, self.live)["status"], "LAYOUT_NOT_FOUND")

    def test_frontend_frame_context(self):
        begin = {"exe_sha256": A.EXE_SHA, "build": "PRISTINE_RETAIL", "frame": 7}
        epoch = {"frame": 7, "live_certificate_valid": False, "scene": {
            "read_complete": True, "countdown": 0, "requested_name": A.FRONTEND_SCENE,
            "committed_name": A.FRONTEND_SCENE,
            "job_source": "DataScene/FrontendScreens/VehicleSelect.xml"}}
        self.assertTrue(A.frontend_context(begin, epoch))
        for obj, key, wrong in [(begin, "frame", 8), (begin, "exe_sha256", "unknown"),
                                (epoch, "live_certificate_valid", True),
                                (epoch["scene"], "countdown", 1),
                                (epoch["scene"], "requested_name", "RaceTest/France1"),
                                (epoch["scene"], "committed_name", "FrontendScreens/MainMenu")]:
            before = obj[key]
            obj[key] = wrong
            self.assertFalse(A.frontend_context(begin, epoch))
            obj[key] = before


class FrozenMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((HERE / "source-and-live-evidence.json").read_text(encoding="utf8"))

    def test_resource_inventory_and_no_unknown_sources(self):
        inventory = self.evidence["source_inventory"]
        self.assertEqual(len(inventory["complete_resources"]), 26)
        self.assertEqual(inventory["dx_resources_scanned"], 78)
        self.assertEqual(inventory["unsupported_sources"], [])

    def test_all_forester_complete_groups_unique(self):
        candidate = next(s for s in self.evidence["source_inventory"]["complete_resources"]
                         if s["path"] == "Forester/complete.dx")
        self.assertEqual(candidate["sha256"], "a38566e0d653c586fc53594de2276e8c3f50d882126f26ee5792d74794cd3ca1")
        self.assertEqual(len(candidate["draws"]), 17)
        self.assertEqual(sum(d["triangles"] for d in candidate["draws"]), 2271)
        self.assertTrue(all(d["unique_to_complete_resource"] for d in candidate["draws"]))
        self.assertTrue(all(len(d["identical_source_owners"]) == 1 for d in candidate["draws"]))

    def test_rotation_and_generation_control(self):
        self.assertEqual([f["frame"] for f in self.evidence["frames"]], [1235, 2726])
        self.assertTrue(all(f["current_frontend_context"] for f in self.evidence["frames"]))
        self.assertTrue(self.evidence["same_resource_generations"])
        self.assertEqual(self.evidence["pose_changes"], {
            "world_changes": True, "view_unchanged": True, "projection_unchanged": True})
        self.assertTrue(all(not f["layout_join"]["suppression_authorized"]
                            for f in self.evidence["frames"]))

    def test_partial_side_not_promoted_to_whole_mesh(self):
        evidence = json.loads((HERE / "mesh-joins.json").read_text(encoding="utf8"))
        side = next(c for c in evidence["cases"] if c["pc_draw"] == 5)
        self.assertEqual((side["pc_faces"], side["ps2_faces"]), (400, 484))
        self.assertEqual((side["pc_to_ps2_exact_matches"], side["pc_to_ps2_modified_matches"]), (357, 364))
        self.assertLess(side["maximum_corner_error_among_matches"], .005)
        self.assertEqual(side["extra_faces_coplanar_overlap_other_pc_groups"], 1)
        self.assertEqual(side["extra_face_other_pc_groups"], ["9"])
        self.assertEqual(evidence["model_kind"], "COMPLETE_ONLY_NOT_CAR")

    def test_grille_shape_is_not_guessed_by_name(self):
        evidence = json.loads((HERE / "mesh-joins.json").read_text(encoding="utf8"))
        grille = next(c for c in evidence["cases"] if c["pc_draw"] == 1)
        self.assertEqual((grille["pc_to_ps2_exact_matches"], grille["pc_to_ps2_modified_matches"]), (0, 0))

    def test_original_native_byte_metadata(self):
        native = json.loads((HERE / "native-owner-evidence.json").read_text(encoding="utf8"))
        checked = json.loads((HERE / "native-byte-validation.json").read_text(encoding="utf8"))
        self.assertEqual(native["exe_sha256"], A.EXE_SHA)
        self.assertEqual(checked["instruction_windows_checked"], 31)
        self.assertEqual(checked["result"], "PASS")
        self.assertEqual(native["runtime_owner_validation"], "NOT_PERFORMED")
        self.assertEqual(checked["original_vtable_callback"]["target"], "0x44c4c0")


if __name__ == "__main__":
    unittest.main()
