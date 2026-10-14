"""Current source-authority fix; no screenshot or source match is live parity."""
import json
from pathlib import Path
import unittest

PORT=Path(__file__).resolve().parents[1]


class CoverageFix(unittest.TestCase):
    def test_previous_source_records_are_preserved(self):
        prior=json.loads((PORT/'docs/full-coverage/vehicles/registry-candidates.json').read_text())
        current=json.loads((PORT/'docs/reflection-coverage-fix/active-registry.json').read_text())
        self.assertEqual(current['previous_count'],174)
        self.assertEqual(current['added_count'],38)
        self.assertEqual(len(current['entries']),212)
        byhash={row['geometry_sha256']:row for row in current['entries']}
        for row in prior:
            self.assertEqual(byhash[row['geometry_sha256']],row)

    def test_all_active_digests_are_unique_and_header_pinned(self):
        current=json.loads((PORT/'docs/reflection-coverage-fix/active-registry.json').read_text())
        header=(PORT/'renderer/reflection_pilot.hpp').read_text()
        self.assertEqual(len({r['geometry_sha256'] for r in current['entries']}),212)
        for row in current['entries']:
            with self.subTest(vehicle=row['vehicle'],source=row['draw_index']):
                self.assertTrue(row['unique_vehicle_family'])
                self.assertIn(row['geometry_sha256'],header)
        for digest in current['unsupported_alpha_candidates']:
            self.assertNotIn(digest,header)

    def test_source_material_context_keeps_exact_hash_and_state_gates(self):
        h=(PORT/'renderer/reflection_pilot.hpp').read_text()
        c=(PORT/'renderer/reflection_pilot.cpp').read_text()
        integration=(PORT/'renderer/reflection_native_integration.hpp').read_text()
        self.assertIn('reflection_material_exclusion(draw)',h)
        self.assertIn('affected_source_material_vehicle(material->vehicle)',c)
        self.assertIn('mode_value()==4',integration)
        self.assertIn('tracked_world.known',integration)
        self.assertIn('std::memcmp(&native_world,&tracked_world.value',integration)
        self.assertIn('hash==candidate.geometry_sha',c)
        for gate in ('live_race_owner_unverified','native_material_stage_mismatch',
                     'missing_current_upload_or_resource_identity','native_state_unknown_or_diverged'):
            self.assertIn(gate,c)


if __name__=='__main__':unittest.main()
