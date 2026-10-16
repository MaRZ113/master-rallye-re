import collections
import unittest
import generate_fleet_probe_registry as g

class FleetProbeRegistryTests(unittest.TestCase):
    def test_exact_family_coverage_and_exclusion(self):
        rows = g.profiles()
        self.assertEqual(len({r['family'] for r in rows}), 25)
        self.assertNotIn('forklift', {r['family'].lower() for r in rows})
        self.assertEqual(len(rows), 774)

    def test_every_profile_retains_original_source_identity(self):
        import json
        rows = g.profiles()
        source = json.loads(g.SOURCE.read_text())['fleet']
        expected = {(f['pc_family'], d['record_path']): d for f in source if f.get('pc_family') and f['pc_family'].lower() != 'forklift' for d in f['draws']}
        self.assertEqual(len(rows), len(expected))
        for row in rows:
            original = expected[(row['family'], row['record_path'])]
            self.assertEqual((row['vertices'], row['faces'], row['geometry_sha256']),
                             (original['vertices'], original['faces'], original['geometry_sha256']))
            self.assertEqual(row['source_path'], row['family'] + '/car.dx')
            self.assertRegex(row['geometry_sha256'], r'^[0-9a-f]{64}$')

    def test_family_uniqueness_does_not_hide_shared_geometry(self):
        rows = g.profiles()
        owners = collections.defaultdict(set)
        for row in rows:
            owners[row['geometry_sha256']].add(row['family'])
        for row in rows:
            self.assertEqual(row['unique_across_families'], len(owners[row['geometry_sha256']]) == 1)

    def test_generated_header_is_exact_and_deterministic(self):
        rows = g.profiles()
        self.assertEqual(g.render(rows), g.render(g.profiles()))
        self.assertEqual((g.HERE / 'fleet_probe_registry.hpp').read_text(), g.render(rows))
        self.assertIn('NOT A REPLACEMENT OR OWNER CERTIFICATE', g.render(rows))

if __name__ == '__main__':
    unittest.main()
