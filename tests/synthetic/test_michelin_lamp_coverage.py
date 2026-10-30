"""Source-free reproductions of incomplete lamp UV selection and ownership."""
import copy
import math
import unittest
from master_rallye.material_derivation import polygon_pixels
from master_rallye.michelin_lamp_coverage import (
    CONTOURS, LEFT_CONTOUR, SCENE_SHA256, rav4_coverage, uv_coverage,
)


class MichelinLampCoverageTests(unittest.TestCase):
    def test_old_rectangle_truncates_red_lens_inner_edge(self):
        pixels = polygon_pixels(CONTOURS,256,128)
        old_rect = lambda x,y: (43<=x<57 or 198<=x<212) and 55<=y<80
        missed = {i for i in pixels if not old_rect(i%256,i//256)}
        self.assertGreater(len(missed),0)
        self.assertIn(74*256+59,pixels)
        self.assertFalse(old_rect(59,74))
        self.assertIn(74*256+196,pixels)
        self.assertFalse(old_rect(196,74))

    def test_no_amber_pale_inset_emblem_or_bumper_coverage(self):
        pixels = polygon_pixels(CONTOURS,256,128)
        for x,y in [(50,59),(55,67),(128,70),(46,98),(205,59),(200,67),(208,98)]:
            self.assertNotIn(y*256+x,pixels)
        self.assertEqual(len(pixels),336)
        self.assertEqual({y for y in range(128) if any(i//256==y for i in pixels)},set(range(63,77)))

    def test_both_lenses_have_symmetric_pixel_coverage(self):
        pixels = polygon_pixels(CONTOURS,256,128)
        self.assertEqual({(i//256)*256+255-i%256 for i in pixels},pixels)

    def test_whole_triangle_selection_is_not_a_lens_mask(self):
        # A synthetic painted triangle contains a small lamp island. Ownership
        # must retain only the explicit island, not unlight the complete face.
        mesh = {'uvs':[[0,0],[1,0],[0,1]],'triangles':[[0,1,2]]}
        pixels = polygon_pixels([((1,1),(3,1),(3,3),(1,3))],8,8)
        report = uv_coverage(mesh,pixels,8,8,filter_radius=0)
        self.assertEqual(report['source_face_ids'],[0])
        self.assertEqual(report['lit_pixel_count'],4)
        self.assertLess(report['lit_pixel_count'],8*8//2)

    def test_missing_face_is_a_failure_not_partial_pass(self):
        mesh = {'uvs':[[0,0],[1,0],[0,1]],'triangles':[[0,1,2]]}
        with self.assertRaisesRegex(ValueError,'outside original source faces'):
            uv_coverage(mesh,{7*8+7},8,8)

    def test_uv_index_and_nonfinite_rejected(self):
        mesh = {'uvs':[[0,0],[1,0],[0,1]],'triangles':[[0,1,3]]}
        with self.assertRaisesRegex(ValueError,'UV index'):
            uv_coverage(mesh,{9},8,8)
        mesh['triangles']=[[0,1,2]];mesh['uvs'][0][0]=math.nan
        with self.assertRaisesRegex(ValueError,'UV values'):
            uv_coverage(mesh,{9},8,8)

    def test_filter_support_adds_adjacent_face_without_enlarging_lit_mask(self):
        mesh = {'uvs':[[0,0],[1,0],[0,1],[1,1]],'triangles':[[0,1,2],[1,3,2]]}
        pixels = {3*8+3}
        tight = uv_coverage(mesh,pixels,8,8,filter_radius=0)
        filtered = uv_coverage(mesh,pixels,8,8,filter_radius=1)
        self.assertEqual(tight['source_face_ids'],[0])
        self.assertEqual(filtered['source_face_ids'],[0,1])
        self.assertEqual(tight['lit_pixel_count'],filtered['lit_pixel_count'])

    def test_determinism_and_no_mutation(self):
        mesh = {'uvs':[[0,0],[1,0],[0,1],[1,1]],'triangles':[[0,1,2],[1,3,2]]}
        before=copy.deepcopy(mesh);pixels={9,10,17,18}
        self.assertEqual(uv_coverage(mesh,pixels,8,8),uv_coverage(mesh,pixels,8,8))
        self.assertEqual(mesh,before)

    def test_excessive_work_and_allocation_are_rejected(self):
        mesh = {'uvs':[[0,0],[1,0],[0,1]],'triangles':[[0,1,2]]*4096}
        with self.assertRaisesRegex(ValueError,'work budget'):
            uv_coverage(mesh,set(range(4096)),128,128)
        with self.assertRaisesRegex(ValueError,'allocation budget'):
            uv_coverage(mesh,list(range(65537)),512,512)

    def test_wrong_vehicle_cannot_reuse_toyota_recipe(self):
        with self.assertRaisesRegex(ValueError,'exact accepted source scene'):
            rav4_coverage({'source':{'catalog':'Car06A.PDO'}},SCENE_SHA256)
        with self.assertRaisesRegex(ValueError,'exact accepted source scene'):
            rav4_coverage({'source':{'catalog':'Car25A.PDO'}},'0'*64)


if __name__ == '__main__':
    unittest.main()
