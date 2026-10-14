"""Report invariants; byte-derived displacement is not runtime or UV parity."""
import json
from pathlib import Path
import unittest

HERE = Path(__file__).parent


class ModifiedMaterialEvidence(unittest.TestCase):
    def test_eight_body_relations_have_one_source_and_bounded_residual(self):
        report = json.loads((HERE/'modified-material-correspondence.json').read_text())
        rows = [r for r in report['entries'] if f"{r['vehicle']}:{r['draw_index']}" not in report['excluded_non_body_records']]
        expected = {('Forester',10),('Forester',12),('Forester',14),('Navara',3),
                    ('Navara',4),('Patrol',1),('Patrol',2),('Kamaz',13)}
        self.assertEqual({(r['vehicle'],r['draw_index']) for r in rows}, expected)
        for row in rows:
            with self.subTest(vehicle=row['vehicle'],draw=row['draw_index']):
                self.assertEqual(row['tolerance'],.005)
                self.assertGreater(row['binding']['max_error'],.001)
                self.assertLessEqual(row['binding']['max_error'],.005)
                self.assertIn('$shader(carshiny)',row['binding']['material'])
                # Original PC draws retain three/one degenerate records in
                # Navara3/4; only nondegenerate faces establish surface mapping.
                degenerates={('Navara',3):3,('Navara',4):1}
                self.assertEqual(row['binding']['matching_pc_faces'],
                    row['triangles']-degenerates.get((row['vehicle'],row['draw_index']),0))
                self.assertEqual(row['signature_owner_families'],[row['vehicle']])
                self.assertEqual(row['material_relation'],'SINGLE_PS2_CARSHINY_MATERIAL_CORRESPONDENCE')
                self.assertEqual(row['geometry_relation'],'GEOMETRY_MODIFIED_SMALL_LOCAL_DISPLACEMENT')

    def test_active_registry_excludes_nonbody_and_preserves_uv_qualification(self):
        report=json.loads((HERE/'modified-material-correspondence.json').read_text())
        registry=json.loads((HERE/'active-registry.json').read_text())
        active={r['geometry_sha256']:r for r in registry['entries']}
        differing_uv=0
        for row in report['entries']:
            if f"{row['vehicle']}:{row['draw_index']}" in report['excluded_non_body_records']:
                self.assertNotIn(row['geometry_sha256'],active)
                continue
            self.assertEqual(active[row['geometry_sha256']],row)
            differing_uv+=not row['independent_uv_check']['complete']
        self.assertGreater(differing_uv,0)

    def test_forester_correct_source_not_same_named_ps2_family(self):
        report=json.loads((HERE/'modified-material-correspondence.json').read_text())
        for row in report['entries']:
            if row['vehicle']=='Forester':
                self.assertEqual(row['ps2_resource'],'/TNG/DATAPSM/VEHICLES/WOOLDAND/CAR.PSM')
                self.assertEqual(row['ps2_source_sha256'],'93a2bd9e9ee884ac32a6d7af4b320212156e853fd85b02bc01bdcc783d0d533d')


if __name__=='__main__':unittest.main()
