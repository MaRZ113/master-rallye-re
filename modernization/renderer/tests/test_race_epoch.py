from pathlib import Path
import json
import re
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from analyze_race_epoch import summarize, read_snapshots, MAX_LINE
from inspect_camera_scope import ROOT, SITES, A3D_SITES, epoch_observer_evidence


def record():
    return dict(type='race_epoch_snapshot', phase='R-CAM1-A3c', camera_writes_authorized=False,
                request_generation=2, successful_generation=2, jobs=[], events=[],
                course_identity_verified=False, installed=True, hook_ownership_intact=True)


class RaceEpochEvidenceTests(unittest.TestCase):
    def test_live_observer_does_not_claim_camera_scope_or_freecam(self):
        e = epoch_observer_evidence()
        self.assertTrue(e['implemented'])
        self.assertTrue(e['observation_only'])
        self.assertFalse(e['camera_writes_authorized'])
        self.assertEqual(e['runtime_status'], 'NOT_RUN')
        self.assertEqual(e['native_sites'], 10)

    def test_cpp_contexts_match_exact_image_inspector(self):
        # Independent verifier and production installer must pin identical caller context.
        rows = {va: signature for va, _, signature, _ in SITES + A3D_SITES}
        header = (ROOT / 'include/race_epoch.hpp').read_text()
        contexts = re.findall(r'\{(0x[0-9a-f]+),"[^"]+","([0-9a-f]+)"\}', header)
        self.assertEqual(len(contexts), 11)
        for va, signature in contexts:
            self.assertEqual(rows[int(va, 16)], signature)

    def test_inside_callback_is_an_observation_not_authorization(self):
        r = record()
        r['events'] = [dict(serial=1, event='execute_begin', job_lifetime=4),
                       dict(serial=2, event='owner_attach', job_lifetime=4, actor=99, owner_lifetime=7),
                       dict(serial=3, event='execute_return', job_lifetime=4)]
        s = summarize(r)
        self.assertEqual(s['owner_observations'][0]['relation'], 'inside_observed_callback')
        self.assertFalse(s['camera_writes_authorized'])
        self.assertEqual(s['status'], 'BLOCKED_ON_RACE_EPOCH_CORRELATION')

    def test_late_owner_and_missing_history_stay_unknown(self):
        r = record()
        r['events'] = [dict(serial=1, event='execute_begin', job_lifetime=4),
                       dict(serial=2, event='execute_return', job_lifetime=4),
                       dict(serial=3, event='owner_attach', job_lifetime=0)]
        self.assertEqual(summarize(r)['owner_observations'][0]['relation'], 'outside_or_missing_callback_history')
        r['events'] = [dict(serial=3, event='owner_attach', job_lifetime=4)]
        self.assertEqual(summarize(r)['owner_observations'][0]['relation'], 'outside_or_missing_callback_history')

    def test_invalid_serial_and_bounds_reject(self):
        for events in ([dict(serial=1), dict(serial=1)], [dict(serial=True)], [dict(serial=0)], [dict(serial=1)] * 129):
            r = record(); r['events'] = events
            with self.assertRaises(ValueError):
                summarize(r)
        r = record(); r['jobs'] = [{}] * 65
        with self.assertRaises(ValueError):
            summarize(r)

    def test_observer_record_cannot_claim_camera_writes(self):
        r = record(); r['camera_writes_authorized'] = True
        with self.assertRaisesRegex(ValueError, 'must not authorize'):
            summarize(r)

    def test_jsonl_uses_existing_f10_and_keeps_input_readonly(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'frame.jsonl'
            raw = (json.dumps(dict(type='frame_begin')) + '\n' + json.dumps(record()) + '\n').encode()
            p.write_bytes(raw)
            self.assertEqual(len(read_snapshots(p)), 1)
            self.assertEqual(p.read_bytes(), raw)
            p.write_text(json.dumps(dict(type='frame_summary')) + '\n')
            with self.assertRaisesRegex(ValueError, 'No race_epoch_snapshot'):
                read_snapshots(p)

    def test_line_limit_rejects_unbounded_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'frame.jsonl'; p.write_bytes(b' ' * (MAX_LINE + 1))
            with self.assertRaisesRegex(ValueError, 'exceeds 2 MiB'):
                read_snapshots(p)


if __name__ == '__main__':
    unittest.main()
