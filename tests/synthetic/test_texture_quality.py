import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from master_rallye.addon_sdk.texture_quality import choose_limit, image_metrics, plan_textures
from master_rallye.dxt import parse_dxt_bytes
from tools.normalize_vehicle_texture_residency import normalize
from tests.synthetic.test_library import simple_record, synthetic_dx, footer56


class TextureQualityTests(unittest.TestCase):
    def fixture(self, root):
        points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
        raw=synthetic_dx(points,[0,1,2],[simple_record(0,2,0,3,('base','Null','Null'))],[(0,0,3)],trailing=footer56(points))
        for name in ('car.dx','complete.dx','wheel.dx'):(root/name).write_bytes(raw)
        tex=struct.pack('<5I',0xfeed,1,123,256,256)+bytes([20,30,40,255])*256**2
        (root/'base.dxt').write_bytes(tex)
        return tex

    def test_source_fidelity_is_byte_preserving_and_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'source';source.mkdir();self.fixture(source)
            normalize(source,root/'a',preset='source-fidelity')
            normalize(source,root/'b',preset='source-fidelity')
            for p in source.iterdir():
                self.assertEqual(p.read_bytes(),(root/'a'/p.name).read_bytes())
                self.assertEqual(p.read_bytes(),(root/'b'/p.name).read_bytes())

    def test_opt_in_reduction_preserves_dx_and_explains_decision(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'source';source.mkdir();self.fixture(source)
            report=normalize(source,root/'out',preset='performance')
            self.assertEqual(parse_dxt_bytes((root/'out/base.dxt').read_bytes()).width,128)
            self.assertEqual((source/'car.dx').read_bytes(),(root/'out/car.dx').read_bytes())
            self.assertTrue(report['quality_policy']['textures'][0]['reasons'])

    def test_protected_text_is_never_automatically_reduced(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);tex=self.fixture(root)
            profile={'version':1,'textures':{'base':{'role':'text','source_sha256':hashlib.sha256(tex).hexdigest()}}}
            self.assertEqual(plan_textures(root,preset='performance',profile=profile)['textures'][0]['factor'],1)
            profile['textures']['base']['source_sha256']='0'*64
            with self.assertRaises(ValueError):plan_textures(root,preset='balanced',profile=profile)

    def test_alpha_edges_are_protected_and_not_material_classification(self):
        tex=parse_dxt_bytes(struct.pack('<5I',0xfeed,1,0,2,2)+bytes([0,0,0,0,255,255,255,255])*2)
        metrics=image_metrics(tex)
        self.assertGreater(metrics['alpha_edge_fraction'],.005)
        self.assertIsNone(choose_limit('performance',metrics,{})[0])

    def test_nonfinite_geometry_cannot_drive_resolution_policy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);raw=bytearray((root/'car.dx').read_bytes());struct.pack_into('<f',raw,16,float('nan'));(root/'car.dx').write_bytes(raw)
            with self.assertRaises(Exception):plan_textures(root,preset='balanced')

    def test_invalid_settings_fail_closed(self):
        metrics={'alpha_edge_fraction':0.,'rgb_edge_fraction':0.}
        for bad in (True,float('nan'),-1,5):
            with self.assertRaises(ValueError):choose_limit('balanced',metrics,{},importance=bad)
        with self.assertRaises(ValueError):choose_limit('unknown',metrics,{})
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root)
            for malformed in ([],False,{'version':True,'textures':{}},{'version':1,'textures':{'base':[]}}):
                with self.assertRaises(ValueError):plan_textures(root,profile=malformed)
            with self.assertRaises(ValueError):plan_textures(root,profile={'version':1,'textures':{'missing':{}}})
            with self.assertRaises(ValueError):normalize(root,root/'out',128)
            with self.assertRaises(ValueError):normalize(root,root.parent/'unused',128,preset='balanced')
