import hashlib,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from master_rallye.preview_scene import stage_vehicle,logical_cases
from tests.synthetic.test_library import simple_record,synthetic_dx,footer56,tag7_record,tag8_record
from master_rallye.dx import parse_dx_bytes

class PreviewTests(unittest.TestCase):
    def fixture(self,root):
        points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
        record=bytearray(simple_record(0,2,0,3,('base-tga','Null','Null')));record[32:36]=bytes([0,0,1,1]);struct.pack_into('<I',record,36,3)
        (root/'part.dx').write_bytes(synthetic_dx(points,[0,1,2],[record],[(0,0,3)],trailing=footer56(points)))
        pixels=bytes([7,11,23,128,29,31,37,255,41,43,47,0,53,59,61,64])
        (root/'base-tga.dxt').write_bytes(struct.pack('<5I',0xfeed,1,0,2,2)+pixels)
        return pixels
    def test_raw_dxt_to_gpu_rows_and_determinism(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pixels=self.fixture(root);out=root/'scene.mrpv';r=stage_vehicle(root/'part.dx',out);first=out.read_bytes()
            self.assertIn(pixels,first);self.assertNotIn(pixels[8:]+pixels[:8],first)
            self.assertEqual(r['draws'],1);self.assertEqual(r['textures'],1)
            self.assertEqual(r['native_texture_residency']['family_cache_bytes'],16)
            self.assertFalse(r['native_texture_residency']['warning'])
            stage_vehicle(root/'part.dx',out);self.assertEqual(first,out.read_bytes())
    def test_native_budget_warning_does_not_hide_diagnostic_geometry(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root)
            with patch('master_rallye.preview_scene.DEFAULT_VEHICLE_TEXTURE_BUDGET',8):
                r=stage_vehicle(root/'part.dx',root/'s.mrpv')
            self.assertTrue(r['native_texture_residency']['warning']);self.assertEqual(r['draws'],1)
    def test_missing_texture_fails_without_poisoning_previous_scene(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);out=root/'scene.mrpv';out.write_bytes(b'previous');(root/'base-tga.dxt').unlink()
            with self.assertRaises(ValueError):stage_vehicle(root/'part.dx',out)
            self.assertEqual(out.read_bytes(),b'previous')
    def test_no_alpha_inference_from_texture_pixels(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);r=stage_vehicle(root/'part.dx',root/'s.mrpv')
            self.assertEqual(r['sources'][0]['materials'][0]['alpha_mode'],'OPAQUE')
    def test_switch_case_is_control_index_not_material_count(self):
        points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
        core=simple_record(0,2,0,3,('Null','Null','Null'));other=simple_record(0,2,3,3,('Null','Null','Null'))
        raw=synthetic_dx(points,[0,1,2]*2,[tag7_record('screenrear',core,1,controls=(2,2,8,2)),tag8_record(other,controls=(1,1))],[(0,0,3),(0,3,3)],declared_count=1)
        cases,warnings=logical_cases(parse_dx_bytes(raw));self.assertEqual(cases,{0:(2,2),1:(2,1)});self.assertTrue(warnings)
    def test_profile_requires_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);p=root/'profile.json';p.write_text(json.dumps({'race_wheel_instances':[{'translation':[0,0,0],'rotation_y':0}]}))
            with self.assertRaises(ValueError):stage_vehicle(root/'part.dx',root/'s.mrpv',profile=p)
    def test_generated_profile_is_discovered_beside_dx(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root)
            (root/'preview-profile.json').write_text(json.dumps({'provenance':'own synthetic rest-pose profile','race_wheel_instances':[]}))
            r=stage_vehicle(root/'part.dx',root/'s.mrpv')
            self.assertEqual(r['profile']['provenance'],'own synthetic rest-pose profile')
    def test_source_pinned_mechanical_markers_do_not_edit_dx(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);(root/'part.dx').rename(root/'car.dx')
            before=(root/'car.dx').read_bytes()
            definition={'profile_version':1,'source_sha256':hashlib.sha256(before).hexdigest(),
                'provenance':'synthetic mechanical diagnostic','groups':[{'name':'test','draw_indices':[0],
                'source_hub_m':[0,0,0],'target_hub_m':[0,.05,.1],'provenance':'test only'}]}
            p=root/'profile.json';p.write_text(json.dumps({'mechanical_debug':definition}))
            r=stage_vehicle(root/'car.dx',root/'s.mrpv',profile=p)
            self.assertEqual(r['draws'],3);self.assertIn('mechanical_debug',r)
            self.assertIn(b'diagnostic:mechanical:test:target_hub_m',(root/'s.mrpv').read_bytes())
            self.assertEqual(before,(root/'car.dx').read_bytes())
            definition['source_sha256']='0'*64;p.write_text(json.dumps({'mechanical_debug':definition}))
            with self.assertRaises(ValueError):stage_vehicle(root/'car.dx',root/'s.mrpv',profile=p)
    def test_auxiliary_model_uses_explicit_wheel_pose_in_race_only(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);(root/'part.dx').rename(root/'car.dx')
            (root/'aux.dx').write_bytes((root/'car.dx').read_bytes())
            p=root/'profile.json';p.write_text(json.dumps({'provenance':'own qualified pose',
                'race_wheel_instances':[{'translation':[2,3,4],'rotation_y':0}],
                'attached_models':[{'resource':'aux.dx','wheel_index':0}]}))
            r=stage_vehicle(root/'car.dx',root/'s.mrpv',profile=p)
            self.assertEqual(r['draws'],2);self.assertEqual(r['sources'][1]['model'],4)
            self.assertIn(struct.pack('<3f',2,3,4),(root/'s.mrpv').read_bytes())
            config=json.loads(p.read_text());config['attached_models'][0]['resource']='../aux.dx';p.write_text(json.dumps(config))
            with self.assertRaises(ValueError):stage_vehicle(root/'car.dx',root/'s.mrpv',profile=p)

if __name__=='__main__':unittest.main()
