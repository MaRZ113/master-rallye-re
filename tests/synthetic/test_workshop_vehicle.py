"""Generated Broker/geometry fixtures; no game assets required."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tests.synthetic.test_workshop import family
from tests.synthetic.test_physics_profile import fixture
from master_rallye.workshop.service import WorkshopProject
from master_rallye.addon_sdk.project import _default_manifest
from master_rallye.workshop.vehicle_authoring import field_info

def project(root):
    raw,profile=fixture();family(root/'Navara');author=root/'author';author.mkdir()
    addon=_default_manifest('Mitsubishi Test','T2','AddonOne','Navara')
    (author/'addon.json').write_text(json.dumps(addon))
    (author/'vehicle-project.json').write_text(json.dumps({'vehicle_name':'Navara','source_vehicle_dir':str(root/'Navara'),'resources':{},'texture_edits':{},'texture_replacements':{}}))
    (author/'physics-profile.json').write_text(json.dumps(profile))
    p=WorkshopProject.create(author,root/'workshop');p.data['car_id']=28;p.save();return p,raw

class VehicleWorkshopTests(unittest.TestCase):
    def test_physics_typed_validation_history_audio_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            p,members=project(Path(td));p.vehicle_state();before=(p.working/'addon.json').read_bytes();geometry={x:x.read_bytes() for x in p.assets.iterdir()}
            with patch.object(WorkshopProject,'_retail_members',return_value=members):
                compiled=p.physics_compile()[0];p.physics_update('DataGame/vehicles.xml','Chassis/TotalMass',1200.)
                self.assertNotEqual(p.physics_compile()[0],compiled)
                p.undo();self.assertEqual(p.physics_compile()[0],compiled);p.redo();self.assertEqual(p.vehicle_state()['physics']['overrides']['DataGame/vehicles.xml']['Chassis/TotalMass'],1200.)
                q=WorkshopProject(p.root);self.assertEqual(q.physics_compile()[0],p.physics_compile()[0]);q.vehicle_reset('physics');self.assertEqual(q.physics_compile()[0],compiled)
                with self.assertRaises(ValueError):p.physics_update('DataGame/vehicles.xml','Engine/Gears',5)
                state=p.vehicle_state()
                for value in (-1,0,float('nan'),1.):
                    with self.assertRaises(ValueError):p.physics_update('DataGame/vehicles.xml','Chassis/TotalMass',value)
                self.assertEqual(p.vehicle_state(),state)
            self.assertEqual(before,(p.working/'addon.json').read_bytes());self.assertEqual(geometry,{x:x.read_bytes() for x in p.assets.iterdir()})

    def test_display_identity_preserves_internal_fields(self):
        with tempfile.TemporaryDirectory() as td:
            p,_=project(Path(td));original=json.loads((p.working/'addon.json').read_text());fields=p.vehicle_state()['details'];fields.update(model='EVO IV STUDIO',combined='MITSUBISHI EVO IV STUDIO',display_name='EVO IV STUDIO')
            p.details_update(fields);after=json.loads((p.working/'addon.json').read_text())
            for key in ('identity','physical_id','addon_id','assets','audio'):self.assertEqual(after[key],original[key])
            self.assertEqual(after['frontend']['model'],fields['model']);p.undo();self.assertEqual(json.loads((p.working/'addon.json').read_text()),original)
            for value in ('bad\0name','bad\nname','Мицубиси','x'*97):
                wrong=copy.deepcopy(fields);wrong['combined']=value
                with self.assertRaises(ValueError):p.details_update(wrong)

    def test_aliases_metadata_only_search_reopen_restore_and_source_drift(self):
        with tempfile.TemporaryDirectory() as td:
            p,_=project(Path(td));before={x:x.read_bytes() for x in p.assets.iterdir()};p.alias_update('base-tga.dxt','Body Paint')
            self.assertEqual(p.texture_search('body')[0]['name'],'base-tga.dxt');self.assertEqual(p.texture_search('base-tga')[0]['alias'],'Body Paint')
            q=WorkshopProject(p.root);self.assertEqual(q.texture_search('paint')[0]['name'],'base-tga.dxt');q.undo();self.assertEqual(q.texture_search('paint'),[]);q.redo();self.assertTrue(q.texture_search('paint'));q.restore();self.assertFalse(q.vehicle_state()['aliases'])
            self.assertEqual(before,{x:x.read_bytes() for x in p.assets.iterdir()})
            with self.assertRaises(ValueError):q.alias_update('../bad.dxt','Alias')
            baseline=q.root/'author-baseline/addon.json';baseline.write_text('{}')
            with self.assertRaisesRegex(ValueError,'baseline changed'):q.vehicle_state()

    def test_new_visual_version_keeps_only_compatible_aliases(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p,_=project(root/'one');q,_=project(root/'two');p.alias_update('base-tga.dxt','Glass')
            result=q.vehicle_inherit(p);self.assertEqual(result['applied'],['base-tga.dxt']);self.assertEqual(q.texture_search('glass')[0]['name'],'base-tga.dxt')
            q.data['inputs']['base-tga.dxt']='0'*64;result=q.vehicle_inherit(p);self.assertTrue(result['conflicts'])

    def test_camera_target_hash_and_source_guard(self):
        with tempfile.TemporaryDirectory() as td:
            p,_=project(Path(td));p.vehicle_state()
            info={'car_id':28,'family':'AddonOne','source_model_sha256':'f'*64,'original':{'half_length_m':3,'height_m':2}}
            with patch.object(p,'camera_inspect',return_value=info),patch.object(p,'camera_source',return_value=b'not a source'):
                with self.assertRaisesRegex(ValueError,'target'):p.camera_update(2.,1.5,27)
                with self.assertRaisesRegex(ValueError,'hash'):p.camera_update(2.,1.5,28)
            self.assertIsNone(p.vehicle_state()['camera'])

    def test_visual_version_seed_does_not_bake_authored_defaults(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p,members=project(root/'one');original=p.vehicle_state()
            with patch.object(WorkshopProject,'_retail_members',return_value=members):p.physics_update('DataGame/vehicles.xml','Chassis/TotalMass',1200.)
            fields=copy.deepcopy(original['details']);fields['model']='AUTHORED';p.details_update(fields)
            author=root/'new-author';shutil.copytree(p.working,author);p.vehicle_restore_author_baseline(author)
            self.assertEqual(json.loads((author/'physics-profile.json').read_text()),original['physics'])
            self.assertEqual(json.loads((author/'addon.json').read_text())['frontend']['model'],original['details']['model'])
            self.assertNotEqual(p.vehicle_state()['physics'],original['physics'])

    def test_art_apply_rejects_foreign_or_stale_sources_atomically(self):
        with tempfile.TemporaryDirectory() as td:
            p,_=project(Path(td));before=p.vehicle_state()
            addon=json.loads((p.working/'addon.json').read_text());addon['frontend']['vehicle_select_art']={'policy':'project_frame'};(p.working/'addon.json').write_text(json.dumps(addon))
            with self.assertRaisesRegex(ValueError,'source changed'):
                p.art_apply({'vehicle_select_art':{'source_model':'complete.dx','render_input_sha256':{}}})
            self.assertEqual(p.vehicle_state(),before)
            with self.assertRaisesRegex(ValueError,'source changed'):
                p.art_apply({'vehicle_select_art':{'source_model':'../../external.dx','render_input_sha256':p.art_input_pins()}})

    def test_qualified_units_not_unverified_claims(self):
        self.assertEqual(field_info('Dimensions/WheelBase','Float','DataGame/vehicles.xml')['units'],'m')
        self.assertFalse(field_info('DamageParams/MaxDamage','Float','DataGame/vehicles.xml')['editable'])
        self.assertFalse(field_info('Engine/TorqueEntries','Int','DataGame/vehicles.xml')['editable'])
        self.assertIn('native units',field_info('Steering/Unknown','Float','DataGame/vehicles.xml')['units'])
