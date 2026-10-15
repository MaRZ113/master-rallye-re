import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fleet_convert', HERE / 'convert_fleet_complete.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class FleetInventory(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((HERE / 'coverage.json').read_text())['fleet']
        self.profiles = json.loads((HERE / 'frontend-profiles.json').read_text())

    def test_all_original_sources_and_alias(self):
        self.assertEqual(len(self.rows), 29)
        by = {x['ps2_family']: x for x in self.rows}
        self.assertEqual(by['WOOLDAND']['pc_family'], 'Forester')
        self.assertIsNone(by['FORESTER']['pc_family'])
        self.assertEqual(sum(x['pc_family'] is not None for x in self.rows), 26)
        for row in self.rows:
            self.assertEqual(set(row['models']), {'CAR', 'COMPLETE'})
            self.assertEqual(row['models']['COMPLETE']['wrappers'], [])

    def test_exact_admitted_material_profiles(self):
        self.assertEqual(len(self.profiles['profiles']), 20)
        rejected = {x['family'] for x in self.profiles['rejected']}
        self.assertEqual(rejected, {'FORESTER', 'MOONBUGGY', 'TANK', 'MATTSERATI', 'SIMMBUGGHINI', 'UFO', 'WOOLDAND', 'KIASPORTAGE', 'TATA'})
        self.assertEqual(max(x['ps2_meshes'] for x in self.profiles['profiles']), 24)
        self.assertEqual(max(len(x['pc_sources']) for x in self.profiles['profiles']), 26)
        for p in self.profiles['profiles']:
            self.assertTrue(any(x['unique_family_in_all_paired_complete_sources'] for x in p['pc_sources']))
            self.assertTrue(all(x['vertices'] > 0 and x['index_count'] == x['faces'] * 3 for x in p['pc_sources']))

    def test_generated_registry_exact(self):
        header = (HERE / 'frontend_fleet_registry.hpp').read_text()
        for p in self.profiles['profiles']:
            self.assertIn(p['sha256'], header)
            self.assertIn(p['filename'], header)
            for s in p['pc_sources']:
                self.assertIn(s['geometry_sha256'], header)

    def test_source_driven_secondary_selection(self):
        for p in self.profiles['profiles']:
            self.assertEqual(len(p['mesh_secondary_kinds']), p['ps2_meshes'])
            for m in p['mesh_secondary_kinds']:
                if m['mixed_reflection']:
                    self.assertEqual(m['mode'], 3)
                    self.assertEqual(m['effective_secondary'], 'CommonTextures\\rendertarget64x64')
                if 'rubber' in m['authored_secondary'].lower():
                    self.assertFalse(m['mixed_reflection'])

    def test_private_assets_if_present(self):
        for p in self.profiles['profiles']:
            file = c.PORT / '.assets/vehicles' / p['filename']
            if not file.exists():
                self.skipTest('Original-derived private fleet assets intentionally excluded from handoff')
            data = file.read_bytes()
            self.assertEqual(c.c.sha(data), p['sha256'])
            self.assertEqual(len(data), p['bytes'])
            magic, version, meta_size, meshes, vertices, indices, textures, digest = c.c.HEADER.unpack_from(data)
            self.assertEqual((magic, version, meshes, vertices, indices, textures),
                             (c.c.MAGIC, 2, p['ps2_meshes'], p['vertices'], p['indices'], p['textures']))
            self.assertEqual(digest.hex(), p['source_sha256'])
            for i in range(meshes):
                mesh = c.c.MESH.unpack_from(data, c.c.HEADER.size + meta_size + i * c.c.MESH.size)
                self.assertNotEqual(mesh[2], c.c.NONE)

    def test_explicit_shader_missing_primary_fails_closed(self):
        for family, node in [('KIASPORTAGE', 379852), ('TATA', 349913)]:
            file = c.PORT / '.assets/vehicles' / (family + '-COMPLETE.ps2vehicle')
            if not file.exists():
                self.skipTest('Private original-derived inputs excluded from handoff')
            row = next(x for x in self.rows if x['ps2_family'] == family)
            with self.assertRaisesRegex(ValueError, 'Missing primary for explicit shader: node ' + str(node)):
                c.convert(file.read_bytes(), row, b'')


if __name__ == '__main__':
    unittest.main()
