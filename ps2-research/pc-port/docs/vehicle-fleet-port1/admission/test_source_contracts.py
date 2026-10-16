"""Independent source-only invariants; these do not grant runtime admission."""
import json
import hashlib
from pathlib import Path
import unittest

PORT = Path(__file__).resolve().parents[3]
SOURCE = PORT / 'docs/vehicle-continuity2/fleet-car'


class AdmissionSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((SOURCE / 'race-profiles.json').read_text())['profiles']
        cls.contracts = {p['pc_family']: p for p in json.loads(
            (SOURCE / 'fleet-car-contracts.json').read_text())['fleet'] if p.get('pc_family')}

    def test_exactly_playable_twenty_five(self):
        self.assertEqual(len(self.profiles), 25)
        self.assertEqual(len({p['family'] for p in self.profiles}), 25)
        self.assertNotIn('forklift', {p['family'].lower() for p in self.profiles})

    def test_every_source_partition_complete_disjoint(self):
        for p in self.profiles:
            with self.subTest(p['family']):
                c = self.contracts[p['family']]
                selected = {r['record_path'] for r in p['pc_sources']}
                excluded = {r['record_path'] for r in p['excluded_conditional_native_sources']}
                self.assertFalse(selected & excluded)
                self.assertEqual(selected | excluded, {r['record_path'] for r in c['native_sources']})
                self.assertEqual(selected, set(c['native_suppression_record_paths']))
                self.assertFalse(p['includes_conditional_geometry'])
                self.assertFalse(p['includes_independent_wheels'])
                self.assertTrue(p['includes_static_crew'])

    def test_no_conditional_or_ambiguous_suppression(self):
        for p in self.profiles:
            for r in p['pc_sources']:
                with self.subTest(family=p['family'], record=r['record_path']):
                    self.assertTrue(r['whole_chassis_suppress_candidate'])
                    self.assertFalse(r['source_conditional_face_hits'])
                    self.assertFalse(r['original_source_glow_or_on_guard'])
                    self.assertTrue(r['unique_family_in_paired_car_corpus'])
                    for key in ('geometry_sha256', 'ordered_position_sha256',
                                'uv_topology_sha256', 'native_uv_winding_sha256'):
                        self.assertEqual(len(r[key]), 64)

    def test_material_modes_explicit(self):
        for p in self.profiles:
            self.assertFalse(self.contracts[p['family']]['material_blocks'])
            self.assertLessEqual({m['mode'] for m in p['mesh_secondary_kinds']}, {0, 1, 2, 3, 5, 20})
        by_family = {p['family']: p for p in self.profiles}
        self.assertIn(5, {m['mode'] for m in by_family['Forester']['mesh_secondary_kinds']})
        for family in ('Mattserati', 'Simmbugghini'):
            self.assertIn(2, {m['mode'] for m in by_family[family]['mesh_secondary_kinds']})

    def test_original_world_setter_zero_branch(self):
        here = Path(__file__).resolve().parent
        evidence = json.loads((here / 'world-setter-evidence.json').read_text())
        self.assertEqual(evidence['subject']['digest']['sha256'],
                         'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4')
        assembly = evidence['assembly']
        for instruction in ('0x561b03: TEST EDI, EDI',
                            '0x561b05: JZ 0x00561b10',
                            '0x561b17: DEC EAX',
                            '0x561b18: JZ 0x00561beb',
                            '0x561b1e: DEC EAX',
                            '0x561b1f: JNZ 0x00561d46',
                            '0x561dd2: PUSH 0x100',
                            '0x561dda: CALL dword ptr [EAX + 0x94]'):
            self.assertIn(instruction, assembly)
        windows = json.loads((here / 'world-original-windows.json').read_text())
        self.assertEqual(windows['exe_sha256'], evidence['subject']['digest']['sha256'])
        for window in windows['windows']:
            raw = bytes.fromhex(window['bytes_hex'])
            self.assertEqual(len(raw), int(window['end_exclusive'], 16) - int(window['va'], 16))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), window['sha256'])

    def test_original_two_pass_queue(self):
        here = Path(__file__).resolve().parent
        evidence = json.loads((here / 'queue-two-pass-evidence.json').read_text())
        assembly = evidence['assembly']
        for instruction in ('0x562831: MOV EAX, dword ptr [EBX + 0x24]',
                            '0x562843: MOV ECX, dword ptr [EDI + 0x8]',
                            '0x562886: ADD EBP, 0x18',
                            '0x5628b2: MOV ECX, dword ptr [EAX + 0x8]',
                            '0x5628bc: CALL 0x00576970',
                            '0x56290e: MOV EAX, dword ptr [EBX + 0x34]',
                            '0x56291d: MOV ECX, dword ptr [EBX + 0x38]',
                            '0x56295c: ADD EDI, 0x18',
                            '0x5629df: MOV ECX, dword ptr [EAX + 0x8]',
                            '0x5629e9: CALL 0x00576970'):
            self.assertIn(instruction, assembly)
        windows = json.loads((here / 'queue-original-windows.json').read_text())
        self.assertEqual(windows['exe_sha256'], evidence['subject']['digest']['sha256'])
        for window in windows['windows']:
            raw = bytes.fromhex(window['bytes_hex'])
            self.assertEqual(len(raw), int(window['end_exclusive'], 16) - int(window['va'], 16))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), window['sha256'])


if __name__ == '__main__':
    unittest.main()
