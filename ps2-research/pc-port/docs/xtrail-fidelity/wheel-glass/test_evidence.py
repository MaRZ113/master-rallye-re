"""Corpus-independent checks of compact frozen Xtrail source evidence."""
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('xtrail_wheel_audit',HERE/'audit.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class XtrailEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((HERE/'source-evidence.json').read_text())
        cls.car,cls.wheel=cls.report['models']

    def test_glass_is_not_carshiny(self):
        cover=self.car['draws'][10]
        self.assertEqual(cover['triangles'],18)
        self.assertEqual(cover['categories'],{'GLASS_DISTINCT_FROM_BODY_ENVIRONMENT':18})
        binding=cover['bindings'][0]
        self.assertEqual(binding['mesh']['path'],'root.19')
        self.assertEqual(binding['mesh']['mode'],20)
        self.assertGreater(binding['uv_max_abs'],1.)
        # Source geometry places this in the front lamp region, distinct from
        # the front screen. Material names are not used as the spatial oracle.
        self.assertGreater(cover['bounds']['min'][2],1.9)
        self.assertLess(cover['bounds']['max'][1],.87)

    def test_decal_normals_and_uv_are_supported(self):
        draw=self.car['draws'][13]
        self.assertEqual(draw['geometry_sha256'],'e580100f2670ba7bd87589727e194026f3f28d9b54b42eda325d51e47aa136b3')
        self.assertEqual(draw['categories'],{'VERIFIED_ENVIRONMENT_MATERIAL_CURRENT_IDENTITY_REQUIRED':14})
        self.assertEqual(draw['bindings'][0]['uv_max_abs'],0.)
        normals=self.car['decal_normal_augmentation']
        self.assertEqual(normals['ambiguous_positions'],0)
        self.assertEqual(len(normals['entries']),20)
        self.assertEqual(len({r['pc_xyz_sha256'] for r in normals['entries']}),20)
        self.assertLess(normals['normal_max_abs_to_ps2'],2e-7)

    def test_wheel_rubber_negative_and_rim_separate(self):
        for di,count in ((0,72),(1,36),(2,54)):
            self.assertEqual(self.wheel['draws'][di]['categories'],{'KEEP_AUTHORED_RUBBER_MAP_NO_BODY_ENV_OVERRIDE':count})
        rim=self.wheel['draws'][3]
        self.assertEqual(rim['triangles'],90)
        self.assertEqual(rim['bindings'][0]['matched_source_faces'],90)
        self.assertEqual(rim['slots'][0],'xwheel-tga')
        self.assertEqual(rim['bindings'][0]['mesh']['slots'][0],'jumpwheel64-tga')
        self.assertGreater(rim['bindings'][0]['uv_max_abs'],.17)

    def test_mixed_body_flat_remains_separate(self):
        self.assertEqual(self.car['draws'][1]['source_ordered_runs'],[
            {'first_source_face':0,'source_faces':195,'category':'VERIFIED_ENVIRONMENT_MATERIAL_CURRENT_IDENTITY_REQUIRED'},
            {'first_source_face':195,'source_faces':14,'category':'FLAT_DISTINCT_FROM_BODY_ENVIRONMENT'}])
        self.assertEqual(audit.recommendation('carshiny','rubber-tga'),'KEEP_AUTHORED_RUBBER_MAP_NO_BODY_ENV_OVERRIDE')
        self.assertEqual(audit.recommendation(None,''),'UNKNOWN_KEEP_STOCK')

    def test_live_layout_is_not_live_geometry(self):
        self.assertEqual(len(self.report['live_layout_observations']),2)
        for file in self.report['live_layout_observations']:
            self.assertTrue(all(r['qualification']=='LAYOUT_CORRELATION_ONLY_NOT_RUNTIME_GEOMETRY_HASH' for r in file['records']))
            decal=next(r for r in file['records'] if r['arguments'][2:3]==[20] and r['arguments'][4]==14)
            self.assertEqual(decal['fvf'],0x142)
            self.assertEqual(decal['stream0']['stride'],24)
            self.assertEqual(decal['stages'][1]['1'],1)
            self.assertEqual(decal['native_states']['27'],0)
            cover=next(r for r in file['records'] if r['arguments'][2:3]==[22] and r['arguments'][4]==18)
            self.assertEqual(cover['fvf'],0x152)
            self.assertEqual(cover['stages'][1]['1'],18)

    def test_negative_corpus_source_uniqueness_bounded(self):
        self.assertEqual(self.report['negative_controls']['pc_files'],78)
        for hits in self.report['negative_controls']['exact_geometry_hits'].values():
            self.assertEqual(len(hits),1)
            self.assertTrue(hits[0]['path'].startswith('Xtrail/'))


if __name__=='__main__':unittest.main()
