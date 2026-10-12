import importlib.util
from pathlib import Path
import unittest


path = Path(__file__).resolve().parents[1] / "tools" / "analyze_physics_commit.py"
spec = importlib.util.spec_from_file_location("physics_commit_analysis", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def capture():
    return [
        {"type": "physics_probe_setup", "installed": True, "exact_retail_build": True},
        {"type": "physics_probe_summary", "patch_restored": True,
         "counts": {"flag_rises_observed": 1, "flag_clears_observed": 1,
                    "flag_set_consumer_calls": 1},
         "clear_writer_capture": {"policy": "transition_priority_v1",
                                  "all_sampled_store_transitions_retained": True,
                                  "transition_overflow": 0, "diagnostic_overflow": 100}},
        {"type": "physics_probe_clear_writer_event", "writer": "recovery_mode0",
         "store_va": "0x004CD1A1", "apply_flag_before": 1, "native_store_value": 0,
         "owner_known": True, "owner_links_current": True, "player_type": 1,
         "controller": "C", "backing": "P", "thread_id": 1, "qpc": 20,
         "last_flagged_consumer_thread": 1, "last_flagged_consumer_qpc": 10,
         "interval_flagged_consumer_calls": 1, "consumer_in_progress": False,
         "store_completion_observed": False},
        {"type": "physics_probe_event", "event": "controller_transform_consumer",
         "before": {"controller": "C", "backing": "P", "thread_id": 1, "qpc": 30,
                    "apply_flag_P_plus_0x33": 0}},
    ]


class PhysicsCommitAnalysis(unittest.TestCase):
    def test_correlated_clear_is_session_evidence_not_teleport_authorization(self):
        result = module.analyze_session(capture())
        self.assertEqual(result["status"], "STOCK_CLEAR_ATTRIBUTION_CAPTURED")
        self.assertFalse(result["one_shot_guaranteed"])
        self.assertFalse(result["teleport_authorized_by_this_report"])
        self.assertFalse(result["clear_candidates"][0]["store_completion_observed"])

    def test_legacy_saturated_capture_does_not_prove_writer(self):
        result = module.analyze_session([
            {"type": "physics_probe_summary", "counts": {
                "clear_writer_events": 32, "clear_writer_events_dropped": 465,
                "flag_set_consumer_calls": 1}},
            *[{"type": "physics_probe_clear_writer_event", "apply_flag_before": 0,
               "native_store_value": 0} for _ in range(32)],
        ])
        self.assertTrue(result["legacy_capture"])
        self.assertTrue(result["capture_loss_or_overlap"])
        self.assertEqual(result["clear_candidates"], [])
        self.assertEqual(result["status"], "NEEDS_CLEAR_ATTRIBUTION_CAPTURE")

    def test_critical_overflow_requires_retest(self):
        rows = capture()
        rows[1]["clear_writer_capture"]["transition_overflow"] = 1
        result = module.analyze_session(rows)
        self.assertEqual(result["status"], "NEEDS_CLEAR_ATTRIBUTION_CAPTURE")

    def test_stale_owner_ai_other_thread_or_no_later_clear_fail_closed(self):
        for key, value in (("owner_links_current", False), ("player_type", 2),
                           ("last_flagged_consumer_thread", 2),
                           ("consumer_in_progress", True)):
            with self.subTest(key=key):
                rows = capture()
                rows[2][key] = value
                self.assertEqual(module.analyze_session(rows)["status"],
                                 "NEEDS_CLEAR_ATTRIBUTION_CAPTURE")
        self.assertEqual(module.analyze_session(capture()[:-1])["status"],
                         "NEEDS_CLEAR_ATTRIBUTION_CAPTURE")

    def test_missing_setup_failed_install_or_failed_restoration(self):
        for index, key in ((0, "installed"), (0, "exact_retail_build"), (1, "patch_restored")):
            rows = capture()
            rows[index][key] = False
            self.assertEqual(module.analyze_session(rows)["status"],
                             "NEEDS_CLEAR_ATTRIBUTION_CAPTURE")
        self.assertEqual(module.analyze_session([])["status"], "NEEDS_CLEAR_ATTRIBUTION_CAPTURE")


if __name__ == "__main__":
    unittest.main()
