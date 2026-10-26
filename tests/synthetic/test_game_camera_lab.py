import json,tempfile,unittest,struct
from pathlib import Path
from tests.synthetic.test_workshop_vehicle import project
from master_rallye.workshop.service import WorkshopProject
from master_rallye.workshop.race_marker import normalized_rgb,colour_info,tinted_marker
from master_rallye.game_camera import follow_preset,static_pose
from master_rallye.camera_preview import camera_guides


class MarkerTests(unittest.TestCase):
    def test_marker_persists_history_without_other_identity_or_resource_edits(self):
        with tempfile.TemporaryDirectory()as td:
            p,_=project(Path(td));before=json.loads((p.working/'addon.json').read_text());state=p.vehicle_state();assets={f.name:f.read_bytes()for f in p.assets.iterdir()if f.is_file()}
            info=p.marker_update('#20D9E8');self.assertEqual(info['car_id'],28)
            addon=json.loads((p.working/'addon.json').read_text());expected=dict(before);expected['race_colour_rgba']=[32/255,217/255,232/255,before['race_colour_rgba'][3]];self.assertEqual(addon,expected)
            self.assertEqual(info['current']['f32le_hex'],struct.pack('<4f',*expected['race_colour_rgba']).hex())
            reopened=WorkshopProject(p.root);self.assertEqual(reopened.marker_inspect(),info);p.undo();self.assertEqual(p.vehicle_state(),state);p.redo();self.assertEqual(p.marker_inspect(),info)
            p.vehicle_reset('race_marker');self.assertEqual((p.working/'addon.json').read_bytes(),(p.root/'author-baseline/addon.json').read_bytes());self.assertEqual({f.name:f.read_bytes()for f in p.assets.iterdir()if f.is_file()},assets)

    def test_bad_colour_and_display_only_tint(self):
        from PIL import Image
        for value in ('123456','#zz0000',[True,0,0],[0,1,float('nan')],[0,2,0]):
            with self.assertRaises(ValueError):normalized_rgb(value)
        im=Image.new('RGBA',(2,1),(255,128,64,63));out=tinted_marker(im,[.5,1,0,1]);self.assertEqual(out.getpixel((0,0)),(128,128,0,63));self.assertEqual(im.getpixel((0,0)),(255,128,64,63))

    def test_static_pose_uses_separate_source_distances_and_extents(self):
        p={'Dist Front':14.,'Dist Back':3.5,'Dist Up':.65,'FOV':90.}
        a=static_pose({'half_length_m':2.25,'height_m':1.5},p)
        self.assertEqual(a['target'],[0.,0.,14.]);self.assertEqual(a['eye'],[0.,2.15,-5.75])
        b=static_pose({'half_length_m':2.25,'height_m':1.5},p,[3,2,-4],90)
        self.assertAlmostEqual(b['eye'][0],-2.75);self.assertAlmostEqual(b['eye'][1],4.15);self.assertAlmostEqual(b['target'][0],17)
        debug={k:{field:a[field]for field in ('eye','target','source_fov_degrees')}for k in ('original','modified')};self.assertTrue(camera_guides(debug))
        debug['original']['eye']=[float('nan'),0,0]
        with self.assertRaises(ValueError):camera_guides(debug)

    def test_camera_setup_refuses_unsupported_layout_and_inputs(self):
        with self.assertRaises(ValueError):follow_preset(b'<Game/>')
        with self.assertRaises(ValueError):follow_preset(b'<Game/>',3)
        with self.assertRaises(ValueError):static_pose({'half_length_m':-1,'height_m':1},{})
        with self.assertRaises(ValueError):static_pose({'half_length_m':1,'height_m':1},{'Dist Front':1,'Dist Back':1,'Dist Up':1,'FOV':True})

    def test_camera_original_reset_removes_only_this_roster_override(self):
        with tempfile.TemporaryDirectory()as td:
            p,_=project(Path(td));p.vehicle_state();own=Path(td)/'own.json';other=Path(td)/'other.json'
            own.write_text(json.dumps({'car_id':28}));other.write_text(json.dumps({'car_id':29}))
            roster={'camera_profiles':[str(own),str(other)]};p.camera_build_roster(roster,Path(td),Path(td))
            self.assertEqual(roster['camera_profiles'],[str(other)])


if __name__=='__main__':unittest.main()
