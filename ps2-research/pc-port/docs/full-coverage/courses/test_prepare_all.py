"""Synthetic exact-source admission checks; contains no original geometry."""
import unittest
import json
from pathlib import Path
import prepare_all as source

class ExactAdmission(unittest.TestCase):
    def setUp(self):
        self.face=((0.,0.,0.),(1.,0.,0.),(0.,0.,1.))
    def test_winding_and_order(self):
        self.assertEqual(source.exact_matches([(7,self.face)],[tuple(reversed(self.face))]),[7])
    def test_parallel_surface_rejected(self):
        shifted=tuple((x,y+.01,z) for x,y,z in self.face)
        self.assertEqual(source.exact_matches([(7,self.face)],[shifted]),[])
    def test_tolerance_is_bounded(self):
        self.assertEqual(source.exact_matches([(1,self.face)],[tuple((x,y+.0009,z) for x,y,z in self.face)]),[1])
        self.assertEqual(source.exact_matches([(1,self.face)],[tuple((x,y+.0011,z) for x,y,z in self.face)]),[])
    def test_degenerate_source_rejected(self):
        zero=((0.,0.,0.),)*3
        self.assertEqual(source.exact_matches([(1,zero)],[zero]),[])
    def test_no_crossed_triangulation_guess(self):
        other=((0.,0.,0.),(1.,0.,0.),(1.,0.,1.))
        self.assertEqual(source.exact_matches([(1,self.face)],[other]),[])
    def test_duplicate_target_not_duplicate_source(self):
        self.assertEqual(source.exact_matches([(4,self.face)],[self.face,self.face]),[4])
    def test_complete_registry_distinct_original_ownership(self):
        registry=json.loads((Path(__file__).parent/'coverage-registry.json').read_text())
        self.assertEqual(len(registry['courses']),36)
        self.assertEqual(len({row['native_certificate_id'].lower() for row in registry['courses']}),36)
        names=[]
        for row in registry['courses']:
            self.assertEqual(row['status'],'VERIFIED_PAIR')
            self.assertEqual(set(row['categories']),{'grass','shrubs'})
            self.assertEqual(row['alignment']['transform'],'IDENTITY_IN_SOURCE_FRAME; NO_FIT')
            for item in row['categories'].values():
                self.assertEqual(item['status'],'VERIFIED_PRIVATE_ASSET')
                self.assertLessEqual(item['point_count'],300000)
                self.assertEqual(item['artifact']['psm_sha256'],row['psm_sha256'])
                self.assertEqual(item['artifact']['pc_dx_sha256'],row['pc_dx_sha256'])
                names.append(item['filename'].lower())
        self.assertEqual(len(set(names)),72)
    def test_existing_assets_frozen_regression(self):
        registry=json.loads((Path(__file__).parent/'coverage-registry.json').read_text())
        expected={'FRANCE1':('354cb84c7238e8a1a4959c95fc7e265587f32a3f26dcb29b98aa818c1096f961','69e64191810c4f3ce5b9b06862e9afe8d4ea2a69940ee7d4449cb71430fc2802'),
                  'ITALY_S1':('e764d52060bc87c797e43459d743ec3dc6a4cd1aff67f239a62c59e82863c1ae','e2d08cfc56f7f3ea8e91b5225ba1b4a228ec40062b361c697426694c0f88234d'),
                  'TURKEY3':('6af6393c444a485b2c648c2a6973a91bd5783db3c0f90269a0d653b2f089cfad','688947a32776ffab67c553b4adc95e4597c399f2d70ece37534fd682044752b4')}
        for row in registry['courses']:
            if row['course'] in expected:
                self.assertEqual(tuple(row['categories'][c]['artifact']['sha256'] for c in ('grass','shrubs')),expected[row['course']])

if __name__=='__main__':unittest.main()
