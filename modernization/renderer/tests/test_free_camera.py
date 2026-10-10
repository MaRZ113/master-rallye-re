from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from analyze_race_epoch import reconcile_a3c, summarize
from inspect_camera_scope import inspect_a3d, A3D_SITES, verify_sites


class FreeCameraEvidenceTests(unittest.TestCase):
    def captures(self):
        return json.loads((ROOT / 'research/r-cam1-a3d/a3c-golden-excerpts.json').read_text())

    def test_real_first_capture_poison_did_not_prove_owner_absence(self):
        a = self.captures()['captures'][0]
        r = dict(a['snapshot'], events=a['selected_actual_events'])
        result = reconcile_a3c(r)
        self.assertEqual(result['first_false_poison_serial'], 4)
        self.assertTrue(result['request_inside_execution_observed'])
        self.assertEqual((result['owner_generation'], result['latest_scene_generation']), (7, 8))
        self.assertTrue(result['scene_request_after_owner_initialization'])
        self.assertEqual(result['native_owner_checks'], 'NOT_REACHED')
        self.assertFalse(result['successful_job_history_complete'])
        self.assertFalse(result['camera_writes_authorized'])
        self.assertEqual(a['sha256'], '7cff9e1c413a5f6fb6d09518b045ed19f67d887e5557d6fee44710a068ab46cd')

    def test_real_restart_capture_keeps_retirement_and_missing_success(self):
        b = self.captures()['captures'][1]
        r = dict(b['snapshot'], events=b['selected_actual_events'])
        result = reconcile_a3c(r)
        self.assertEqual((result['owner_generation'], result['latest_scene_generation'], result['owner_lifetime']), (19, 20, 3))
        self.assertTrue(result['scene_request_after_owner_initialization'])
        self.assertEqual(result['observed_retirements'], [47, 64, 65, 79])
        self.assertFalse(result['successful_job_history_complete'])
        self.assertFalse(summarize(r)['camera_writes_authorized'])
        self.assertEqual(b['sha256'], '87e546e6d74387a8a3582b7a6defc3dfc6a030494a21233456928a569e6b31e8')

    def test_golden_trace_has_no_fabricated_successful_callbacks(self):
        data = self.captures()
        self.assertEqual(data['session']['identity']['exe_sha256'], 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4')
        for capture in data['captures']:
            self.assertEqual(capture['snapshot']['successful_generation'], 0)
            self.assertTrue(all(e['event'] not in ('commit_return', 'execute_return') for e in capture['selected_actual_events']))

    def test_current_offline_diagnostic_does_not_grant_native_permission(self):
        r = dict(type='race_epoch_snapshot', phase='R-CAM1-A3d', camera_writes_authorized=False,
                 live_certificate_valid=True, free_camera=dict(active=True), events=[], jobs=[])
        result = summarize(r)
        self.assertEqual(result['status'], 'OFFLINE_DIAGNOSTIC_NOT_LIVE_CERTIFICATE')
        self.assertFalse(result['camera_writes_authorized'])
        self.assertTrue(result['free_camera']['active'])

    def test_a3e_summary_reports_live_certificate_without_claiming_flight(self):
        r = dict(type='race_epoch_snapshot', phase='R-CAM1-A3e', camera_writes_authorized=False,
                 live_certificate_valid=True, free_camera=dict(active=False), events=[], jobs=[],
                 root_job_success=dict(scene='RaceTest/France1', source='DataScene/RaceTest/France1.xml',
                                       flag21=1, flag22=1, commit_success=True, terminal=True),
                 hud_job_success=dict(scene='Hud/Hud0', flag21=1, flag22=0,
                                      commit_success=True, terminal=True),
                 input_observation=dict(toggle_key_vk=0x77, focused=True,
                                        toggle_pressed_while_focused=True, controller_toggle_edge=True))
        result = summarize(r)
        self.assertEqual(result['status'], 'LIVE_RACE_CERTIFIED_AWAITING_HUMAN_FLIGHT')
        self.assertFalse(result['camera_writes_authorized'])
        self.assertEqual(result['root_job_success']['flag22'], 1)
        self.assertEqual(result['hud_job_success']['flag22'], 0)
        self.assertTrue(result['input_observation']['controller_toggle_edge'])

    def test_first_flight_runtime_golden_keeps_root_hud_and_state_distinct(self):
        evidence = json.loads((ROOT / 'research/r-cam1-a3e/first-flight-capture-summary.json').read_text())
        self.assertEqual(evidence['target_exe_sha256'], 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4')
        root, hud = evidence['root_job'], evidence['hud_child_job']
        self.assertEqual((root['scene'], root['source'], root['flag21'], root['flag22']),
                         ('RaceTest/France1', 'DataScene/RaceTest/France1.xml', 1, 1))
        self.assertEqual((hud['scene'], hud['source'], hud['flag21'], hud['flag22'], hud['parent_job_lifetime']),
                         ('Hud/Hud0', 'DataScene/Hud/Hud0.xml', 1, 0, root['lifetime']))
        self.assertEqual(root['manager_scene_after_commit'], hud['manager_scene_after_commit'])
        self.assertEqual(evidence['typed_race_context']['Race/Car0/RaceState'], 0)
        self.assertEqual(evidence['observed_certificate']['live_certificate_reason'], 'supported_course_job_not_verified')
        self.assertFalse(evidence['interpretation']['flight_confirmed'])

    def test_current_inspector_still_rejects_unknown_binary(self):
        with self.assertRaisesRegex(ValueError, 'Not pristine retail'):
            inspect_a3d(b'unknown build')

    def test_new_native_context_guards_reject_each_mutation(self):
        class Image:
            image_base = 0x400000
            def offset(self, rva, n=1):
                return offsets[rva]
        offsets = {}
        blob = bytearray()
        for va, _, signature, _ in A3D_SITES:
            offsets[va - 0x400000] = len(blob)
            blob.extend(bytes.fromhex(signature))
        self.assertEqual(len(verify_sites(blob, Image(), A3D_SITES)), 3)
        for va, _, _, _ in A3D_SITES:
            bad = bytearray(blob)
            bad[offsets[va - 0x400000]] ^= 1
            with self.assertRaisesRegex(ValueError, 'Signature mismatch'):
                verify_sites(bad, Image(), A3D_SITES)

    def test_handoff_defaults_are_off_and_f10_is_reserved(self):
        import configparser
        ini = configparser.ConfigParser()
        ini.read(ROOT / 'MRRRenderer.ini.example')
        self.assertEqual(ini['FreeCamera']['Enabled'], '0')
        self.assertNotEqual(ini['FreeCamera']['ToggleKey'], 'F10')
        self.assertEqual(ini['FreeCamera']['AutoLevelHorizon'], '1')
        self.assertEqual(ini['FreeCamera']['HorizonLevelSeconds'], '0.30')
        first = configparser.ConfigParser()
        first.read(ROOT / 'docs/r-cam1-a3d/first-flight.ini')
        self.assertEqual(first['FreeCamera']['Enabled'], '1')
        self.assertEqual(first['FreeCamera']['ControlPreset'], '1')
        self.assertEqual(first['Trace']['Enabled'], '1')


if __name__ == '__main__':
    unittest.main()
