import copy
import unittest

from master_rallye.addon_sdk.roster_layout import resolve_layout,BASE
from tools.roster_scene_layout import reorder_scene
from tools.prepare_sdk_capacity_probe import scene_append


def rows():
    return [{'physical_id':i,'vehicle_class':c,'class_local_index':n,
             'frontend':{'vehicle_select_art':{'frame':i+100}}}
            for i,c,n in [(28,'T2',8),(29,'T2',9),(30,'T2',10),(31,'T2',11),(32,'T3',12)]]


def order():
    return {'T1':BASE['T1'][:], 'T2':[7,8,30,9,10,11,12,31,13,27,28,29],
            'T3':[14,32]+list(range(15,26))}


class RosterLayoutTests(unittest.TestCase):
    def test_order_does_not_renumber_participants_or_reservations(self):
        source=rows();before=copy.deepcopy(source);layout=resolve_layout(source,order())
        self.assertEqual(source,before)
        self.assertEqual(layout['physical_id_to_class_local']['30'],{'vehicle_class':'T2','class_local_index':2})
        self.assertEqual(layout['physical_id_to_class_local']['31']['class_local_index'],7)
        self.assertEqual(layout['physical_id_to_class_local']['32']['class_local_index'],1)
        self.assertEqual(layout['canonical']['T3'][-1],32)
        self.assertEqual([len(v)for v in layout['class_to_physical_ids'].values()],[8,12,13])

    def test_invalid_orders_fail_before_native_output(self):
        for mutate in (lambda o:o['T2'].append(30),lambda o:o['T3'].remove(32),
                       lambda o:o['T1'].__setitem__(0,True),
                       lambda o:o['T2'].__setitem__(0,32),lambda o:o.update(T4=[])):
            candidate=order();mutate(candidate)
            with self.assertRaises(ValueError):resolve_layout(rows(),candidate)
        bad=rows();bad[-1]['class_local_index']=1
        with self.assertRaises(ValueError):resolve_layout(bad,order())

    def test_widget_13_and_physical_art_ownership(self):
        # Distinct frame IDs reveal the previous failure class: moving the
        # native map while leaving menu art attached to its former local slot.
        text='<Scene>\n'
        for cls,ids in BASE.items():
            for n,physical in enumerate(ids):
                text+=f'<Egg Name="{cls}_Car{n+1}">\n'
                for key,value in [('en2d Image Bank Index',physical+100),('True Value',physical+100),
                                  ('X ID',n),('Y ID',{'T1':0,'T2':1,'T3':2}[cls]),('XPos*',f'Frontend/VehicleSelect/Button{n}XPos')]:
                    text+=f'<Value Name="{key}" Value="{value}"/>\n'
                text+='</Egg>\n'
        raw=(text+'</Scene>').encode();appended=scene_append(raw,rows())
        transformed=reorder_scene(appended,resolve_layout(rows(),order()))
        import xml.etree.ElementTree as ET
        tree=ET.fromstring(transformed)
        for cls,ids in order().items():
            for n,physical in enumerate(ids):
                egg=next(e for e in tree.iter('Egg')if e.get('Name')==f'{cls}_Car{n+1}')
                values={v.get('Name'):v.get('Value')for v in egg}
                self.assertEqual(values['en2d Image Bank Index'],str(physical+100))
                self.assertEqual(values['X ID'],str(n))
                self.assertEqual(values['Y ID'],str({'T1':0,'T2':1,'T3':2}[cls]))
                self.assertEqual(values['XPos*'],f'Frontend/VehicleSelect/Button{n}XPos')
        self.assertIn(b'T3_Car13',transformed)
        self.assertEqual(reorder_scene(appended,resolve_layout(rows(),order())),transformed)

    def test_33_requires_separate_explicit_profile(self):
        from tools.build_sdk_roster import derive
        with self.assertRaisesRegex(ValueError,'selection_order'):
            derive({'sdk_roster_version':1,'base_runtime':'absent','projects':[{}]*5,'experimental_record_count':33})

    def test_save_migration_is_not_silently_authorized(self):
        from master_rallye.addon_sdk.roster_layout import validate_trial_save
        raw=b'<Game><Broker><Value Name="MasterRallye/GameSaved" Value="False"/><Value Name="MasterRallye/Car0/CarID" Value="31"/></Broker></Game>'
        self.assertTrue(validate_trial_save(raw)['original_bytes_preserved'])
        self.assertIn(b'Value="31"',raw)
        with self.assertRaisesRegex(ValueError,'Active championship'):
            validate_trial_save(raw.replace(b'False',b'True'))
        with self.assertRaises(ValueError):validate_trial_save(b'<!DOCTYPE Game><Game/>')

    def test_storage_extension_is_scoped_to_33_record_profile(self):
        from tools.build_runtime_launcher import _header,LauncherBuildError
        profile={k:'a'*64 for k in ('addon_plan_sha256','native_patch_manifest_sha256',
            'native_patch_operations_sha256','resource_manifest_sha256','resource_index_sha256','reconstructed_reference_file_sha256')}
        profile.update(profile='sdk-multi-addon-roster-experimental-33',retail_exe={'sha256':'a'*64},resource_count=1,
            sdk_roster_layout={'record_count':33,'addon_ids':list(range(26,33))},
            native_extension={'address':0x10000000,'size':300000,'allocation_size':524288,'sha256':'a'*64})
        self.assertIn(b'MR_EXTENSION_ALLOCATION_SIZE 524288u',_header(profile,{'operations':[{}]}))
        for mutate in (lambda p:p.update(profile='sdk-multi-addon-roster-experimental-32'),
                       lambda p:p['sdk_roster_layout'].update(record_count=34),
                       lambda p:p['native_extension'].update(size=524289)):
            bad=copy.deepcopy(profile);mutate(bad)
            with self.assertRaises(LauncherBuildError):_header(bad,{'operations':[{}]})

    def test_workshop_configuration_is_copy_on_write(self):
        import json,tempfile
        from pathlib import Path
        from master_rallye.workshop.service import WorkshopProject
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'old';source.mkdir();(root/'retail.sma').write_bytes(b'fixture')
            entries=[]
            for i in range(28,32):
                author=root/str(i);author.mkdir()
                (author/'addon.json').write_text(json.dumps({'addon_id':str(i),'vehicle_class':'T2',
                    'ai_eligibility':{'quick_race':{'enabled':True}}}))
                entries.append({'physical_id':i,'project':str(author),'build':'fixture'})
            config={'projects':entries};raw=json.dumps(config).encode();(source/'roster-config.json').write_bytes(raw)
            p=WorkshopProject.__new__(WorkshopProject);p.root=root/'workshop'
            p.data={'kind':'addon','identity':'31','build_settings':{'roster_candidate':str(source),'retail_sma':str(root/'retail.sma'),'retail_root':str(root)}}
            p.save=lambda:None
            selected=order();selected['T3']=BASE['T3'][:]
            p.configure_roster(selected)
            self.assertEqual((source/'roster-config.json').read_bytes(),raw)
            self.assertNotEqual(p.data['build_settings']['roster_candidate'],str(source))
            self.assertEqual(p.roster_configuration()['selection_order'],selected)
            self.assertEqual(p.data['car_id'],31)
            p.configure_roster(None)
            private=Path(p.data['build_settings']['roster_candidate'])/'roster-config.json'
            self.assertNotIn('selection_order',json.loads(private.read_text()))
            with self.assertRaisesRegex(ValueError,'AI'):
                p.configure_roster(selected,{'31':'T3'})


if __name__=='__main__':unittest.main()
