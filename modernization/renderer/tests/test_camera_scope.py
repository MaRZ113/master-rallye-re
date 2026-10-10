from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from inspect_camera_scope import ROOT, SITES, inspect, output_path, verify_sites, scope_evidence, race_evidence, epoch_observer_evidence


class SyntheticPE:
    image_base = 0x400000

    def __init__(self):
        self.offsets = {}
        self.blob = b''
        for va, _, signature, _ in SITES:
            self.offsets[va - self.image_base] = len(self.blob)
            self.blob += bytes.fromhex(signature)

    def offset(self, rva, n=1):
        return self.offsets[rva]


class CameraScopeTests(unittest.TestCase):
    def test_unknown_build_rejected_before_pe_read(self):
        with self.assertRaisesRegex(ValueError, 'Not pristine retail'):
            inspect(b'not a supported image')

    def test_return_and_late_camera_dependency_are_both_pinned(self):
        pe = SyntheticPE()
        rows = verify_sites(pe.blob, pe)
        by_role = {row['role']: row for row in rows}
        self.assertTrue(by_role['TraversalFullBody_RET8']['expected_bytes'].endswith('c20800'))
        late = by_role['PostTraversalCameraBuilderCall']
        self.assertEqual(late['va'], '0x0056E40A')
        self.assertEqual(late['rva'], '0x0016E40A')
        self.assertEqual(late['call_target'], '0x005614A0')
        self.assertEqual(by_role['RendererVtableFinalizeCamera']['expected_bytes'], '50e25600')
        self.assertEqual(by_role['ParticlesUseCurrentPose']['va'], '0x0056410E')
        self.assertEqual(by_role['ParticlesUseCurrentPose']['expected_bytes'], '81c388000000')
        self.assertEqual(by_role['ParticlesPassCurrentPoseToBillboardBuilder']['va'], '0x00564185')

    def test_every_anchor_rejects_mutation(self):
        pe = SyntheticPE()
        for va, _, _, _ in SITES:
            with self.subTest(va=hex(va)):
                bad = bytearray(pe.blob)
                bad[pe.offset(va - pe.image_base)] ^= 1
                with self.assertRaisesRegex(ValueError, 'Signature mismatch'):
                    verify_sites(bad, pe)

    def test_short_mapping_and_wrong_placement_rejected(self):
        pe = SyntheticPE()
        with self.assertRaisesRegex(ValueError, 'Signature mismatch'):
            verify_sites(pe.blob[:-1], pe)
        pe.image_base = 0x500000
        with self.assertRaisesRegex(ValueError, 'image base'):
            verify_sites(pe.blob, pe)

    def test_output_cannot_overwrite_binary_or_escape_renderer(self):
        for folder in ('research', '.analysis', 'scratch-camera'):
            self.assertEqual(output_path(ROOT / folder / 'scope.json'), ROOT / folder / 'scope.json')
        for path in (ROOT / 'MRallye.exe', ROOT.parent / 'scope.json', ROOT / 'research' / '..' / '..' / 'scope.json'):
            with self.subTest(path=str(path)), self.assertRaises(ValueError):
                output_path(path)

    def test_late_scope_candidates_do_not_certify_an_unimplemented_bridge(self):
        scope = scope_evidence()
        candidates = {row['va']: row for row in scope['candidates']}
        self.assertEqual(candidates['0x006532E2']['decision'], 'REJECTED')
        self.assertEqual(candidates['0x006532E9']['decision'], 'REJECTED')
        self.assertEqual(candidates['0x0065332C']['decision'], 'STATIC_NATIVE_ENDPOINT')
        self.assertFalse(scope['executable_mutation_approved'])
        self.assertFalse(scope['native_bridge_tested'])
        self.assertFalse(scope['completion_interception']['installed'])
        order = scope['order']
        for reader in ('traversal', 'finalize', 'particles_if_enabled', 'late_builder_if_debug', 'debug_if_enabled'):
            self.assertLess(order.index(reader), order.index('end'))
        self.assertLess(order.index('end'), order.index('message_pump'))
        self.assertIn('0x0056CE38', {reader['va'] for reader in scope['readers']})

    def test_owned_field_plan_excludes_native_viewport_and_snap_writes(self):
        # Checks the proposed ownership map, not a memory-write implementation.
        owned = set()
        for row in scope_evidence()['owned_field_candidates']:
            start = int(row['offset'], 16)
            region = set(range(start, start + row['size']))
            self.assertFalse(region & owned)
            owned |= region
        self.assertEqual(len(owned), 176)
        self.assertFalse(owned & set(range(0x78, 0x88)))
        self.assertFalse(owned & set(range(0xC8, 0xCC)))
        self.assertFalse(owned & set(range(8)))

    def test_new_call_contracts_are_pinned_independently(self):
        rows = {row['role']: row for row in verify_sites(SyntheticPE().blob, SyntheticPE())}
        self.assertEqual(rows['EndFrameVirtualCall']['expected_bytes'], 'ff5218')
        self.assertTrue(rows['SchedulerEpilogue_RET4']['expected_bytes'].endswith('c20400'))
        self.assertTrue(rows['EndFrameNormalEpilogue_RET0']['expected_bytes'].endswith('c3'))
        self.assertTrue(rows['EndFrameAlternateEpilogue_RET0']['expected_bytes'].endswith('c3'))
        self.assertEqual(rows['MainLoopSchedulerCall']['call_target'], '0x00653080')
        self.assertEqual(rows['EndFrameLateCameraBuilderCall']['call_target'], '0x005614A0')
        self.assertEqual(rows['DebugWorldCameraConsumer']['va'], '0x00589952')

    def test_relative_target_check_is_independent_of_signature_match(self):
        pe = SyntheticPE()
        sites = list(SITES)
        index = next(i for i, row in enumerate(sites) if row[1] == 'MainLoopSchedulerCall')
        va, role, signature, target = sites[index]
        sites[index] = (va, role, signature, target + 1)
        with self.assertRaisesRegex(ValueError, 'Relative CALL target mismatch'):
            verify_sites(pe.blob, pe, sites)

    def test_race_registry_evidence_never_promotes_stale_oracles_to_permission(self):
        gate = race_evidence()
        self.assertFalse(gate['validated'])
        self.assertFalse(gate['production_predicate_implemented'])
        self.assertFalse(gate['phase']['active_race_certificate'])
        self.assertEqual(gate['retirement']['mask'], 2)
        for oracle in ('gaLimitsAI vtable alone', 'RaceState == 2 alone',
                       'empty pending-job list alone', 'scene countdown == 0', 'BeenInRace'):
            self.assertIn(oracle, gate['rejected_oracles'])
        self.assertIn('failed same-scene request', gate['scene_jobs']['missing_fact'])

    def test_checked_in_map_matches_current_tool_and_keeps_implementation_absent(self):
        data = json.loads((ROOT / 'research/r-cam1-a3/camera-scope-map.json').read_text())
        self.assertEqual(data['schema_version'], 2)
        self.assertEqual(data['sites'], verify_sites(SyntheticPE().blob, SyntheticPE()))
        self.assertEqual(data['scope'], scope_evidence())
        self.assertEqual(data['race_gate'], race_evidence())
        self.assertEqual(data['status'], 'BLOCKED_ON_RACE_EPOCH_CORRELATION')
        self.assertEqual(data['race_epoch_observer'], epoch_observer_evidence())
        self.assertTrue(data['race_epoch_observer']['implemented'])
        self.assertTrue(data['race_epoch_observer']['observation_only'])
        self.assertFalse(data['race_epoch_observer']['camera_writes_authorized'])
        self.assertFalse(data['freecam']['implemented'])
        self.assertFalse(data['freecam']['camera_pose_writes'])
