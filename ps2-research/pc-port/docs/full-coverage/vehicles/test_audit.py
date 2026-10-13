"""Synthetic algorithm controls and frozen compact corpus anchors."""
import unittest, json, struct
from pathlib import Path
import audit

class AuditTests(unittest.TestCase):
    def test_corner_permutations_and_winding(self):
        f=((0.,0.,0.),(1.,0.,0.),(0.,0.,1.))
        self.assertTrue(audit.matches((f[2],f[1],f[0]),audit.index_faces([f])))
    def test_close_stacked_surface_not_accepted(self):
        f=((0.,0.,0.),(1.,0.,0.),(0.,0.,1.))
        self.assertFalse(audit.matches(tuple((x,.002,z) for x,y,z in f),audit.index_faces([f])))
    def test_quantized_bin_boundary_not_false_negative(self):
        f=((.00099,0.,0.),(1.,0.,0.),(0.,0.,1.))
        g=((.00101,0.,0.),(1.,0.,0.),(0.,0.,1.))
        self.assertTrue(audit.matches(g,audit.index_faces([f])))
    def test_digest_preserves_duplicates(self):
        f=((0.,0.,0.),(1.,0.,0.),(0.,0.,1.))
        self.assertNotEqual(audit.geometry_signature([f]),audit.geometry_signature([f,f]))
        self.assertEqual(audit.geometry_signature([f]),audit.geometry_signature([tuple(reversed(f))]))
    def test_registry_previous_anchors(self):
        registry=json.loads((Path(__file__).parent/'registry-candidates.json').read_text())
        anchors={(x['vehicle'],x['draw_index']):x for x in registry}
        self.assertEqual(anchors['Tata',19]['geometry_sha256'],'f80ae53d8c8691ebb8387680b0555343e10100459949c56e3338c484b680e669')
        self.assertEqual(anchors['KiaSportage',14]['geometry_sha256'],'03f88e7a81ae783819b1ad64ac54284b0b330a4c488c851411aee0378706d729')
        for item in registry:
            with self.subTest(vehicle=item['vehicle'],record=item['draw_index']):
                self.assertEqual(item['ps2_binding']['pc_matching_faces'],item['triangles'])
                self.assertEqual(item['flags_hex'],'00000101')
                self.assertEqual(item['signature_owner_families'],[item['vehicle']])
                self.assertEqual(item['ps2_binding']['shader'],'carshiny')
                self.assertEqual(item['ps2_binding']['mesh_path'].count('.'),1)
    def test_full_family_inventory_and_explicit_blocks(self):
        report=json.loads((Path(__file__).parent/'vehicle-coverage.json').read_text())
        self.assertEqual(len(report['vehicles']),29)
        self.assertEqual(report['negative_controls']['files_scanned'],78)
        self.assertEqual(report['negative_controls']['unsupported'],[])
        self.assertEqual({x['ps2_family'] for x in report['vehicles'] if x['blockers']},{'MOONBUGGY','TANK','WOOLDAND'})
        registry=json.loads((Path(__file__).parent/'registry-candidates.json').read_text())
        self.assertNotIn('Forester',{x['vehicle'] for x in registry})
        self.assertNotIn('forklift',{x['vehicle'] for x in registry})

if __name__=='__main__':unittest.main()
