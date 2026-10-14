import json
from pathlib import Path
import unittest

HERE = Path(__file__).parent


class SourceCoverageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((HERE/'source-coverage.json').read_text())
        cls.additions = json.loads((HERE/'registry-additions.json').read_text())

    def test_complete_root_face_or_surface_coverage(self):
        self.assertEqual(len(self.additions), 29)
        for row in self.additions:
            with self.subTest(vehicle=row['vehicle'], draw=row['draw_index']):
                self.assertEqual(row['pc_faces_matching_root_carshiny_union']+row['root_surface_equivalent_faces'],
                                 row['nondegenerate_triangles'])
                self.assertEqual(row['triangles'], row['nondegenerate_triangles']+row['diagnostic_degenerate_triangles'])
                self.assertTrue(all(m['path'].count('.') == 1 and m['contract']['mode'] == 3
                                    and not m['contract']['rubber_substring_preserved'] for m in row['ps2_bindings']))

    def test_texture_independent_paint_and_degenerate_witnesses(self):
        bykey = {(r['vehicle'], r['draw_index']): r for r in self.additions}
        self.assertIn('OLD_EXACT_TEXTURE_PREFILTER', bykey['ChevyBlazer',4]['omission_reasons'])
        self.assertEqual(bykey['Tata',12]['diagnostic_degenerate_triangles'], 2)
        self.assertEqual(bykey['Tata',12]['nondegenerate_triangles'], 110)
        self.assertIn('OLD_SLOT1_EXCLUSION', bykey['Kamaz',6]['omission_reasons'])

    def test_retail_family_uniqueness(self):
        self.assertEqual(self.report['negative_controls']['retail_dx_files'], 78)
        self.assertEqual(self.report['negative_controls']['unsupported'], [])
        for row in self.additions+self.report['vertex_material_candidates']:
            self.assertTrue(row['unique_vehicle_family'])
            self.assertEqual(row['signature_owner_families'], [row['vehicle']])

    def test_vertex_material_join_not_promoted_to_face_equivalence(self):
        rows = self.report['vertex_material_candidates']
        self.assertEqual({(r['vehicle'],r['draw_index']) for r in rows},
                         {('Jump',1),('Jump',2),('Bruno',5),('IceCream',4)})
        for row in rows:
            match = row['root_material_vertex_agreement']
            self.assertEqual(match['matching_positions'], match['pc_unique_nondegenerate_positions'])
            self.assertLess(row['pc_faces_matching_root_carshiny_union']+row['root_surface_equivalent_faces'],
                            row['nondegenerate_triangles'])
            self.assertEqual(row['geometric_relation'], 'SOURCE_VERTEX_MATERIAL_JOIN_TOPOLOGY_DIFFERENT')

    def test_partial_panels_and_helmets_fail_closed(self):
        accepted = {(r['vehicle'],r['draw_index']) for r in self.additions}
        self.assertNotIn(('LandCruiser',8), accepted)
        self.assertNotIn(('LandCruiser',9), accepted)
        self.assertNotIn(('Navara',3), accepted)
        for v in self.report['vehicles']:
            for row in v['draws']:
                if 'helmet' in row['texture_slots'][0]:
                    self.assertEqual(row['root_material_vertex_agreement']['matching_positions'], 0)
                    self.assertNotIn((row['vehicle'],row['draw_index']),accepted)


if __name__ == '__main__': unittest.main()
