import copy,hashlib,json,struct,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class TomcatTests(unittest.TestCase):
    def test_historical_stats_are_not_physics_or_newrav_aliases(self):
        from master_rallye.addon_sdk.demo_restoration import validate_manifest
        catalog=json.loads((ROOT/'research/vehicles/sdk/restorations/frontend-stats.json').read_text())
        self.assertEqual(catalog['vehicles']['Tomcat']['pc841']['value'],[7,6,8,8])
        self.assertEqual(catalog['vehicles']['Forester']['pc931']['value'],[6,7,5,4])
        self.assertEqual(catalog['vehicles']['Rav4']['pc931']['status'],'UNKNOWN')
        self.assertEqual(catalog['vehicles']['Rav4Alpha']['pc841']['status'],'UNKNOWN')
        m=json.loads((ROOT/'research/vehicles/sdk/restorations/tomcat-841.json').read_text())
        validate_manifest(m);self.assertEqual(m['runtime']['physical_id'],32)
        bad=copy.deepcopy(m);bad['identity']['frontend']['stats'][0]=5
        with self.assertRaisesRegex(ValueError,'stats'):validate_manifest(bad)
        self.assertEqual(m['identity']['driver_assignment']['kind'],'REAL_FALLBACK')
        self.assertIsNone(m['identity']['driver']['value'])

    def test_frontend_rating_history_does_not_change_physics(self):
        from tests.synthetic.test_workshop_vehicle import project
        with tempfile.TemporaryDirectory()as folder:
            p,_=project(Path(folder));physics=(p.working/'physics-profile.json').read_bytes();old=p.vehicle_state()['frontend_stats']
            p.frontend_stats_update([7,6,8,8]);self.assertEqual(json.loads((p.working/'addon.json').read_text())['frontend']['stats'],[7,6,8,8])
            self.assertEqual(p.frontend_stats_inspect()['kind'],'CUSTOM')
            self.assertEqual((p.working/'physics-profile.json').read_bytes(),physics)
            p.undo();self.assertEqual(p.vehicle_state()['frontend_stats'],old)
            p.redo();self.assertEqual(p.vehicle_state()['frontend_stats'],[7,6,8,8])
            p.vehicle_reset('frontend_stats');self.assertEqual(p.vehicle_state()['frontend_stats'],old)
            for bad in ([True,6,8,8],[11,6,8,8],[1,2,3]):
                with self.assertRaises(ValueError):p.frontend_stats_update(bad)

    def test_cache_repair_requires_exact_source_and_output_pins(self):
        from tests.synthetic.test_heritage_source import fixture
        from master_rallye.dx import parse_dx_bytes
        from master_rallye.addon_sdk.heritage_source import repair_global_indices
        from master_rallye.addon_sdk.demo_restoration import qualify_rebaked_model
        from master_rallye.errors import MasterRallyeError
        source=bytearray(fixture());offset=parse_dx_bytes(source).global_index_table.data_offset
        struct.pack_into('<H',source,offset,2);source=bytes(source)
        with self.assertRaises((ValueError,MasterRallyeError)):qualify_rebaked_model(source,'fixture')
        fixed,_=repair_global_indices(source);sha=lambda b:hashlib.sha256(b).hexdigest()
        rule={'source_sha256':sha(source),'authoring_sha256':sha(fixed),'reason':'Synthetic known cache drift; no geometry changes'}
        result,report=qualify_rebaked_model(source,'fixture',rule)
        self.assertEqual(result,fixed);self.assertGreater(report['cache_positions_changed'],0)
        for field in ('source_sha256','authoring_sha256'):
            with self.assertRaises(ValueError):qualify_rebaked_model(source,'fixture',{**rule,field:'0'*64})

    def test_ui_highlights_are_view_dependent_and_material_scoped(self):
        from tools.generate_vehicle_ui_previews import icon_highlight
        from tools.vmesh_raster import Camera
        camera=Camera(138,10)
        self.assertEqual(icon_highlight((1,0,0),camera,False),(0.,0.,0.))
        self.assertEqual(icon_highlight((0,0,0),camera,True),(0.,0.,0.))
        first=icon_highlight((0,1,0),camera,True)
        self.assertNotEqual(first,icon_highlight((1,0,0),camera,True))
        self.assertTrue(all(0<=x<=85 for x in first))

    def test_v1_composition_remains_explicit_and_v2_keeps_coverage(self):
        from master_rallye.addon_sdk.ui_preview import compose_preview
        image=(10,10,bytes([80,100,120,255])*100)
        for role in ('vehicle_select_art','smallcarsheet'):
            a,old=compose_preview(image,role);b,new=compose_preview(image,role,style='mr-native-v2')
            self.assertEqual(a[3::4],b[3::4]);self.assertEqual(old['profile'],'mr-native-v1');self.assertEqual(new['profile'],'mr-native-v2')
            self.assertGreaterEqual(new['target_p90'],old['target_p90'])

    def test_v2_hud_has_its_own_three_quarter_camera(self):
        from tools.generate_vehicle_ui_previews import render_sources
        from tests.synthetic.test_heritage_source import fixture
        with tempfile.TemporaryDirectory()as folder:
            root=Path(folder);(root/'complete.dx').write_bytes(fixture())
            report=render_sources(root,root/'icons')
            hud=report['smallcarsheet'];menu=report['vehicle_select_art']
            self.assertEqual((hud['camera_azimuth'],hud['camera_elevation']),(130.,8.))
            self.assertNotEqual(hud['camera_azimuth'],menu['camera_azimuth'])
            self.assertEqual(hud['projection'],'orthographic')


if __name__=='__main__':unittest.main()
