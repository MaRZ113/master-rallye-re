import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

from master_rallye.addon_sdk import vehicle_setup as setup
from master_rallye.addon_sdk.setup_sources import ps2_model,transfer_rgb_rows
from master_rallye.addon_sdk.manifest import canonical_json


def tyre_xml():
    rows=[]
    for prefix, value in (('stock','1.0'),('gravel','2.0')):
        for i in range(5):
            for field in sorted(setup.TYRE_FIELDS):
                rows.append(f'<Value Name="Vehicles/Tyres/{prefix}{i}/{field}" Type="Float" Value="{value}"/>')
    return ('<Game><Broker>'+''.join(rows)+'</Broker></Game>').encode()


def manifest():
    raw=tyre_xml()
    source={'classification':'ORIGINAL','version':'synthetic fixture, not game evidence','sha256':setup.digest(raw)}
    return {'schema':setup.VERSION,'vehicle':{'id':'test-car','car_id':21,'geometry_sha256':'a'*64},
            'defaults':{'livery':'original','tyre':'stock'},
            'liveries':[{'id':key,'label':key,'source':source.copy(),'geometry_sha256':'a'*64,
                         'textures':[],'carsheet':None,'smallcarsheet':None}for key in ('original','alternate')],
            'tyres':[{'id':key,'label':key,'source':source.copy(),
                      'front':setup.tyre_table(raw,key),'rear':setup.tyre_table(raw,key)}for key in ('stock','gravel')],
            'scope':{'mode':'quick_race','participant':'human_player_1','application':'before_vehicle_creation'}}


def ps2_fixture():
    metadata=b'{}';mesh=struct.pack('<7I',0,1,0,0xffffffff,0xffffffff,0,3)
    # DWORD color has all one bits: never parse this as a float NaN.
    vertex=struct.pack('<6fI2f',0,0,0,0,1,0,0xffffffff,0,1)
    return struct.pack('<8s6I',b'PS2MDL02',2,len(metadata),1,1,3,1)+bytes(32)+metadata+mesh+vertex+struct.pack('<3I',0,0,0)+struct.pack('<3I',1,1,4)+bytes((1,2,3,255))


class VehicleSetupTests(unittest.TestCase):
    def test_complete_original_tables_only(self):
        m=manifest();self.assertTrue(setup.verify_tyre_sources(m,tyre_xml()))
        changed=copy.deepcopy(m);changed['tyres'][1]['front']['fields']['0/PeakMu']='3'
        changed['tyres'][1]['front']['table_sha256']=setup.digest(canonical_json(changed['tyres'][1]['front']['fields']))
        with self.assertRaisesRegex(ValueError,'differs from original'):setup.verify_tyre_sources(changed,tyre_xml())

    def test_partial_table_rejected(self):
        raw=tyre_xml().replace(b'<Value Name="Vehicles/Tyres/stock0/PeakMu" Type="Float" Value="1.0"/>',b'')
        with self.assertRaisesRegex(ValueError,'Incomplete'):setup.tyre_table(raw,'stock')

    def test_duplicate_table_field(self):
        raw=tyre_xml().replace(b'</Broker>',b'<Value Name="Vehicles/Tyres/stock0/PeakMu" Type="Float" Value="1.0"/></Broker>')
        with self.assertRaisesRegex(ValueError,'duplicate'):setup.tyre_table(raw,'stock')

    def test_no_entity_expansion(self):
        with self.assertRaises(ValueError):setup.tyre_table(b'<!DOCTYPE x><Game/>','stock')

    def test_geometry_change_blocks_texture_only_preset(self):
        m=manifest();m['liveries'][1]['geometry_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'incompatible'):setup.validate(m)

    def test_duplicate_preset_rejected(self):
        m=manifest();m['liveries'][1]['id']='original'
        with self.assertRaisesRegex(ValueError,'Duplicate preset'):setup.validate(m)

    def test_unknown_fields_and_bad_bool_car_id(self):
        for mutate in (lambda m:m.update(silently_apply=True),lambda m:m['vehicle'].update(car_id=True)):
            m=manifest();mutate(m)
            with self.assertRaises(ValueError):setup.validate(m)

    def test_removed_preset_requires_explicit_review(self):
        m=manifest();state=setup.selection(m,livery='alternate');m['liveries'].pop()
        with self.assertRaises(ValueError):setup.validate_selection(m,state)

    def test_renamed_contract_never_silently_migrates(self):
        m=manifest();state=setup.selection(m);m['liveries'][0]['label']='changed source'
        with self.assertRaisesRegex(ValueError,'explicit review'):setup.validate_selection(m,state)

    def test_persistence_uses_own_file_only(self):
        m=manifest();state=setup.selection(m,livery='alternate',tyre='gravel')
        with tempfile.TemporaryDirectory()as root:
            save=Path(root)/'PlayerState.xml';save.write_bytes(b'untouched championship')
            p=setup.save_selection(Path(root)/'setup',m,state)
            self.assertEqual(setup.decode_json(p.read_bytes()),state)
            self.assertEqual(save.read_bytes(),b'untouched championship')
            self.assertEqual(list(p.parent.iterdir()),[p])

    def test_livery_and_tyre_choices_independent(self):
        m=manifest();a=setup.selection(m,livery='alternate');b=setup.selection(m,tyre='gravel')
        self.assertEqual(a['tyre'],'stock');self.assertEqual(b['livery'],'original')

    def test_cancel_and_defaults_transaction(self):
        draft=setup.SetupDraft(manifest());draft.cycle('livery',1);draft.cycle('tyre',1);draft.cancel()
        self.assertEqual((draft.pending['livery'],draft.pending['tyre']),('original','stock'))
        draft.cycle('tyre',-1)
        with tempfile.TemporaryDirectory()as root:
            draft.confirm(root);draft.restore_defaults();draft.cancel()
            self.assertEqual(draft.pending['tyre'],'gravel')
            draft.restore_defaults();draft.confirm(root)
            self.assertEqual(draft.current['tyre'],'stock')

    def test_unknown_and_out_of_range_navigation(self):
        for field,step in (('gearbox',1),('livery',0),('tyre',True),('tyre',2)):
            with self.assertRaises(ValueError):setup.SetupDraft(manifest()).cycle(field,step)

    def test_scoped_precreation_plan_and_ai_exclusion(self):
        m=manifest();s=setup.selection(m)
        for mode,participant,car,initialized in ((2,1,21,False),(5,0,21,False),(2,0,20,False),(2,0,21,True)):
            self.assertIsNone(setup.precreation_plan(m,s,mode=mode,participant=participant,car_id=car,initialized=initialized,player_type=1,num_players=1,attract=False,replay=False))
        p=setup.precreation_plan(m,s,mode=2,participant=0,car_id=21,initialized=False,player_type=1,num_players=1,attract=False,replay=False)
        self.assertFalse(p['writes_shared_family']);self.assertEqual(p['native_application'],'NOT_QUALIFIED')

    def test_bool_participant_is_not_zero(self):
        m=manifest()
        with self.assertRaises(ValueError):setup.precreation_plan(m,setup.selection(m),mode=2,participant=False,car_id=21,initialized=False,player_type=1,num_players=1,attract=False,replay=False)

    def test_duplicate_json_and_nan(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}',b'x'*(setup.MAX_JSON+1)):
            with self.assertRaises(ValueError):setup.decode_json(raw)

    def test_resource_containment(self):
        for p in ('../foo','/foo','C:/foo','a\\b','a/./b','a//b','a/../b',''):
            with self.assertRaises(ValueError):setup.resource_path(p)

    def test_alpha_coverage_pin_is_real(self):
        m=manifest();raw=struct.pack('<5I',0xfeed,1,0,1,1)+bytes((255,0,255,0))
        binding={'material':'wheel','slot':0,'path':'wheel.dxt','sha256':setup.digest(raw),'alpha_sha256':setup.digest(bytes((255,)))}
        m['liveries'][0]['textures']=[binding];m['liveries'][1]['textures']=[binding]
        with tempfile.TemporaryDirectory()as root:
            (Path(root)/'wheel.dxt').write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'alpha'):setup.validate(m,root=root)
            binding['alpha_sha256']=setup.digest(bytes((0,)));setup.validate(m,root=root)

    def test_ps2_color_is_dword_not_nan_float(self):
        model=ps2_model(ps2_fixture());self.assertEqual(model['vertices'],1)

    def test_ps2_truncation_and_budgets(self):
        raw=ps2_fixture()
        for size in (0,63,65,len(raw)-1):
            with self.assertRaises(ValueError):ps2_model(raw[:size])
        bad=bytearray(raw);struct.pack_into('<I',bad,16,0xffffffff)
        with self.assertRaises(ValueError):ps2_model(bad)

    def test_ps2_bad_texture_and_vertex_indices(self):
        raw=ps2_fixture();at=66
        for offset in (at+8,at+28+36):
            bad=bytearray(raw);struct.pack_into('<I',bad,offset,17)
            with self.assertRaises(ValueError):ps2_model(bad)

    def test_determinism_and_source_immutability(self):
        m=manifest();before=canonical_json(m);raw=ps2_fixture()
        self.assertEqual(setup.selection(m),setup.selection(copy.deepcopy(m)))
        self.assertEqual(ps2_model(raw),ps2_model(raw))
        self.assertEqual(before,canonical_json(m));self.assertEqual(raw,ps2_fixture())

    def test_stock_can_preserve_native_unlisted_defaults(self):
        raw=tyre_xml().replace(b'</Broker>',b'<Value Name="Vehicles/Example/Suspension/Front/TyreType" Type="String" Value="FrontTest"/><Value Name="Vehicles/Example/Suspension/Rear/TyreType" Type="String" Value="RearTest"/></Broker>')
        m=manifest()
        for row in m['tyres']:
            row['source']['sha256']=setup.digest(raw)
            for axle in ('front','rear'):row[axle]=setup.tyre_table(raw,row[axle]['prefix'])
        for axle,prefix in (('front','FrontTest'),('rear','RearTest')):
            m['tyres'][0][axle]={'kind':'NATIVE_PASSTHROUGH','prefix':prefix,'source_sha256':setup.digest(raw),
                              'evidence_key':'Vehicles/Example/Suspension/'+axle.title()+'/TyreType'}
        self.assertTrue(setup.verify_tyre_sources(m,raw))
        m['tyres'][0]['front']['prefix']='harddirt'
        with self.assertRaisesRegex(ValueError,'differs from original'):setup.verify_tyre_sources(m,raw)

    def test_missing_secondary_stage_is_never_silent(self):
        m=manifest();binding={'material':'body','slot':1,'path':'secondary.dxt','sha256':'c'*64,'alpha_sha256':'d'*64}
        m['liveries'][0]['textures']=[binding]
        with self.assertRaisesRegex(ValueError,'secondary texture stage'):setup.validate(m)

    def test_rgb_transfer_preserves_every_alpha_value_and_sources(self):
        base=bytes((10,20,30,0,40,50,60,128,70,80,90,255,100,110,120,254))
        source=bytes((1,2,3,255,4,5,6,0,7,8,9,11,0,0,0,0))
        result=transfer_rgb_rows(base,source,2,2,flip_rows=True)
        self.assertEqual(result[3::4],base[3::4]);self.assertEqual(result[:3],source[8:11]);self.assertEqual(result[4:7],b'\0\0\0')
        self.assertEqual(base[0],10);self.assertEqual(source[0],1)
        for width,height in ((0,1),(1025,1),(True,4)):
            with self.assertRaises(ValueError):transfer_rgb_rows(base,source,width,height,flip_rows=True)

    def test_no_actor_zero_ai_or_attract_shortcut(self):
        m=manifest();state=setup.selection(m)
        options={'mode':2,'participant':0,'car_id':21,'initialized':False,'player_type':1,'num_players':1,'attract':False,'replay':False}
        for field,value in (('player_type',0),('num_players',2),('attract',True),('replay',True)):
            context={**options,field:value};self.assertIsNone(setup.precreation_plan(m,state,**context))


if __name__=='__main__':unittest.main()
