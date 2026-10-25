import copy,json,math,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.ui_preview import compose_preview,PROFILES
from master_rallye.addon_sdk.ui_assets import alpha_bounds,build_ui_assets
from master_rallye.addon_sdk.manifest import AddonValidationError
from tests.synthetic import test_addon_ui_assets as fixtures
from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels
from vmesh_raster import Camera,_project
from generate_vehicle_ui_previews import frame_camera

class PreviewTests(unittest.TestCase):
    def image(self,w=40,h=20):return (w,h,bytes((35,65,110,255))*w*h)

    def test_two_roles_have_separate_grounding_and_scale(self):
        for role in PROFILES:
            out,r=compose_preview(self.image(),role);w,h=PROFILES[role]['size'];bounds=alpha_bounds((w,h,out))
            self.assertEqual(bounds[3],PROFILES[role]['baseline']);self.assertEqual(r['profile'],'mr-native-v1')
            self.assertGreaterEqual(r['exposure'],.8);self.assertLessEqual(r['exposure'],1.6)
            self.assertTrue(any(a==0 for a in out[3::4]));self.assertTrue(any(a==255 for a in out[3::4]))

    def test_tone_is_bounded_and_role_specific(self):
        _,select=compose_preview(self.image(),'vehicle_select_art');_,small=compose_preview(self.image(),'smallcarsheet')
        self.assertGreaterEqual(small['exposure'],select['exposure'])
        self.assertEqual(PROFILES['smallcarsheet']['camera'],(-90.,0.))

    def test_unknown_blank_or_oversized_input_rejected(self):
        for image,role in ((self.image(),'missing'),((2,2,bytes(16)),'smallcarsheet'),((5000,1,bytes(20000)),'smallcarsheet')):
            with self.assertRaises(AddonValidationError):compose_preview(image,role)

    def test_pipeline_opt_in_and_legacy_compatibility(self):
        with tempfile.TemporaryDirectory() as temp:
            root,addon,sma,cfg=fixtures.UiAssetTests().fixture(Path(temp));legacy,old=build_ui_assets(root,addon,sma)
            for role in cfg['icons']:cfg['icons'][role]['presentation']='mr-native-v1'
            (root/'ui-assets.json').write_text(json.dumps(cfg));assets,report=build_ui_assets(root,addon,sma)
            for role,r in report['roles'].items():
                self.assertEqual(r['presentation']['profile'],'mr-native-v1');self.assertEqual(assets[r['bank_path']],legacy[r['bank_path']])
                tex=parse_dxt_bytes(assets[r['frame_path']]);bounds=alpha_bounds((tex.width,tex.height,decode_rgba_pixels(tex)))
                self.assertEqual(bounds[3],PROFILES[role]['baseline'])
            cfg['icons']['smallcarsheet']['presentation']='unknown';(root/'ui-assets.json').write_text(json.dumps(cfg))
            with self.assertRaises(AddonValidationError):build_ui_assets(root,addon,sma)

    def test_optional_perspective_preserves_old_camera_and_near_far_size(self):
        old=Camera(0,0,10,(0,0,0));perspective=Camera(0,0,10,(0,0,0),10)
        self.assertEqual(_project((1,0,0),old,0,0),(-10.,0.,0.))
        near=_project((1,0,-5),perspective,0,0);far=_project((1,0,5),perspective,0,0)
        self.assertAlmostEqual(near[0]/far[0],3.)
        with self.assertRaises(ValueError):_project((0,0,-10),perspective,0,0)

    def test_perspective_source_framing_keeps_every_point_inside_guard(self):
        points=[(-2,0,-2),(2,0,-2),(-2,1,2),(2,1,2),(-3,-1,-3)]
        camera=Camera(138,10,1,(0,0,0),7)
        b=frame_camera(points,camera,512,320)
        self.assertGreaterEqual(b[0],12-1e-6);self.assertGreaterEqual(b[1],12-1e-6)
        self.assertLessEqual(b[2],500+1e-6);self.assertLessEqual(b[3],308+1e-6)
        self.assertNotEqual(camera.offset,(0,0))
        with self.assertRaises(ValueError):frame_camera([(0,0,0)],camera,512,320)

if __name__=='__main__':unittest.main()
