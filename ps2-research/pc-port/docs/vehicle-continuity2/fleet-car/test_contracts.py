from pathlib import Path
import hashlib
import json
import struct
import unittest

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
REPORT = json.loads((HERE / 'fleet-car-contracts.json').read_text())
FLEET = {r['ps2_family']: r for r in REPORT['fleet']}


class FleetCarContracts(unittest.TestCase):
    def test_fleet_identity_and_exclusions(self):
        self.assertEqual(len(FLEET), 29)
        self.assertEqual(sum('prototype' in r for r in FLEET.values()), 25)
        self.assertEqual(FLEET['FORESTER']['decision'], 'NO_PC_COUNTERPART')
        self.assertEqual(FLEET['WOOLDAND']['pc_family'], 'Forester')
        self.assertEqual(FLEET['FORKLIFT']['decision'], 'EXCLUDED_FORKLIFT')
        self.assertTrue(all(not r['enabled'] for r in FLEET.values()))

    def test_suppression_is_exact_and_excludes_conditional_siblings(self):
        xtrail = FLEET['XTRAIL']
        self.assertEqual(len(xtrail['native_suppression_record_paths']), 23)
        self.assertNotIn('24', xtrail['native_suppression_record_paths'])
        self.assertIn('24', xtrail['native_conditional_record_paths'])
        self.assertEqual(xtrail['private_unconditional_faces'], 1980)
        for family in FLEET.values():
            if 'prototype' not in family:
                continue
            mask = int(family['native_suppression_physical_record_mask_hex'], 16)
            for i, source in enumerate(family['native_sources']):
                accepted = bool(mask & (1 << i))
                self.assertEqual(accepted, source['whole_chassis_suppress_candidate'])
                self.assertEqual(len(source['geometry_sha256']), 64)
                self.assertEqual(len(source['native_uv_winding_sha256']), 64)
                if accepted:
                    self.assertEqual(source['source_conditional_face_hits'], 0)
                    self.assertFalse(source['original_source_glow_or_on_guard'])
                    self.assertEqual(source['tag'], 2)
                    self.assertNotIn('.', source['record_path'])

    def test_private_prototypes_preserve_pinned_sources(self):
        for family in FLEET.values():
            if 'prototype' not in family:
                continue
            prototype = family['prototype']
            self.assertFalse(prototype['unresolved_textures'])
            self.assertEqual(prototype['source_sha256'], family['source_ps2_car_sha256'])
            path = PORT / '.assets/vehicles' / prototype['filename']
            if path.exists():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), prototype['sha256'])

    def test_unknown_shader_keeps_generic_source_semantics(self):
        wood = next(m for m in FLEET['WOOLDAND']['source_roots'] if m['path'] == 'root.10')
        self.assertEqual((wood['mode'], wood['mixed_reflection']), (3, False))
        ufo = next(m for m in FLEET['UFO']['source_roots'] if m['path'] == 'root.3')
        self.assertEqual((ufo['mode'], ufo['mixed_reflection']), (3, False))
        ice = next(m for m in FLEET['ICECREAM']['source_roots'] if m['path'] == 'root.3')
        self.assertEqual((ice['mode'], ice['mixed_reflection']), (3, True))
        self.assertEqual(ice['primary_default_resource'], '\\TNG\\DEFAULT.GXI')

    def test_runtime_candidates_are_full_car_with_static_crew_only(self):
        profiles = json.loads((HERE / 'race-profiles.json').read_text())
        self.assertEqual(len(profiles['profiles']), 25)
        self.assertFalse(profiles['rejected'])
        for profile in profiles['profiles']:
            self.assertFalse(profile['enabled'])
            self.assertTrue(profile['includes_static_crew'])
            self.assertFalse(profile['includes_conditional_geometry'])
            self.assertFalse(profile['includes_independent_wheels'])
            self.assertEqual(profile['indices'] // 3,
                             FLEET[profile['ps2_family']]['private_unconditional_faces'])
            path = PORT / '.assets/vehicles' / profile['filename']
            if not path.exists():
                continue
            data = path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), profile['sha256'])
            magic, version, text_size, meshes, vertices, indices, textures, digest = struct.unpack_from('<8s6I32s', data)
            self.assertEqual((magic, version), (b'PS2MDL02', 2))
            self.assertEqual(digest.hex(), profile['original_ps2_source_sha256'])
            meta = json.loads(data[64:64 + text_size])
            self.assertEqual(len(meta['meshes']), meshes)
            self.assertTrue(all(m['path'].count('.') == 1 for m in meta['meshes']))
            self.assertEqual(sum(m['index_count'] for m in meta['meshes']), indices)
            self.assertEqual((vertices, textures), (profile['vertices'], profile['textures']))

    def test_independent_wheels_are_not_assumed_four_record(self):
        self.assertEqual(len(FLEET['XTRAIL']['wheel_contract']['native_sources']), 4)
        self.assertEqual(len(FLEET['TERRANO']['wheel_contract']['native_sources']), 5)
        self.assertEqual(FLEET['UFO']['wheel_contract']['status'],
                         'MISSING_EXPLICIT_SOURCE_OR_NATIVE_WHEEL_RESOURCE')


if __name__ == '__main__':
    unittest.main()
