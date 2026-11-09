"""Identity and resource growth contracts independent of game installations."""
import copy
import struct
import unittest
from pathlib import Path
import tempfile
import hashlib
import json
from master_rallye.addon_sdk.roster_identity import catalog,identity_digest,preserve_reservations
from master_rallye.addon_sdk.ui_assets import parse_bank,append_frame


def bank(count):
    records=[]
    for i in range(count):
        name=f'carsheet_{i:03d}_000'.encode()
        records.append(struct.pack('<I',2)+(bytes(48)+struct.pack('<I',len(name))+name)*2)
    return struct.pack('<3I',0xf001,125,count)+b''.join(struct.pack('<2I',i,i) for i in range(count))+struct.pack('<I',count)+b''.join(records)


class IdentityReservations(unittest.TestCase):
    def test_same_roster_competition_is_validation_not_migration(self):
        from master_rallye.addon_sdk.roster_identity import preflight_player_state
        current=catalog([{'physical_id':256,'family':'HighIdFamily','vehicle_class':'T2'}])
        raw=b'<Game><Broker><Value Name="MasterRallye/GameSaved" Type="Bool" Value="True"/><Value Name="MasterRallye/PlayerT2Car0" Type="Int" Value="256"/></Broker></Game>'
        self.assertEqual(preflight_player_state(raw,current,current)['status'],'PASS_IDENTITY_MAPPING_ONLY')
        for name in ('Frontend/QuickRace/Car2','MasterRallye/PlayerT4Car0','MasterRallye/Car6/CarID'):
            xml=('<Game><Broker><Value Name="'+name+'" Type="Int" Value="256"/></Broker></Game>').encode()
            with self.assertRaisesRegex(ValueError,'Unsupported'):preflight_player_state(xml,current,current)

    def setUp(self):
        self.old=catalog([{'physical_id':33,'family':'NativeFamily','vehicle_class':'T2','retired':True}])
        self.new=copy.deepcopy(self.old);self.new['entries'][0]['retired']=False
        self.migration={'schema':'mr-roster-reactivation/1','previous_identity_sha256':identity_digest(self.old),'reactivate':[33],'reason':'Explicit recovery of the same family, not ID reuse'}

    def test_tombstone_cannot_reactivate_implicitly(self):
        with self.assertRaisesRegex(ValueError,'explicit reactivation'):preserve_reservations(self.old,self.new)
        preserve_reservations(self.old,self.old)
        preserve_reservations(self.old,self.new,migration=self.migration)

    def test_migration_is_exact_and_cannot_rebind(self):
        for key,value in [('reactivate',[]),('reactivate',[33,33]),('reactivate',[True]),('reason',''),('previous_identity_sha256','0'*64)]:
            migration={**self.migration,key:value}
            with self.assertRaises(ValueError):preserve_reservations(self.old,self.new,migration=migration)
        for key,value in [('family','OtherFamily'),('vehicle_class','T3')]:
            new=copy.deepcopy(self.new);new['entries'][0][key]=value
            with self.assertRaisesRegex(ValueError,'rebound'):preserve_reservations(self.old,new,migration=self.migration)


class ArtworkBanks(unittest.TestCase):
    def test_count_growth_is_bounded_by_input_not128(self):
        for n in (127,128,255,256,512):
            original=bank(n);result,name=append_frame(original,0)
            parsed=parse_bank(result)
            self.assertEqual(parsed['count'],n+1)
            self.assertEqual(parsed['records'][:-1],parse_bank(original)['records'])
            self.assertEqual(parsed['names'][-1],name)
        raw=bytearray(bank(1));struct.pack_into('<I',raw,8,0xffffffff)
        with self.assertRaises(ValueError):parse_bank(bytes(raw))

    def test_four_digit_names_rewrite_counted_lengths(self):
        original=bank(1000);result,name=append_frame(original,23)
        self.assertEqual(name,'carsheet_1000_000')
        self.assertEqual(parse_bank(result)['count'],1001)
        self.assertEqual(parse_bank(result)['records'][:-1],parse_bank(original)['records'])


class NativeSceneGrowth(unittest.TestCase):
    def test_more_than_thirteen_widgets_keep_native_ownership(self):
        from master_rallye.addon_sdk.capacity_profile import scenario,SDK33
        from prepare_sdk_capacity_probe import scene_append
        from roster_scene_layout import reorder_scene
        import prepare_vehicle_unlock_overlay as g
        root=Path(__file__).resolve().parents[2]
        path=root.parent/'master-rallye-re-vehicles/.research-output/vehicles/extra-set2/extra-set2-03/runtime/resource-root/DataScene/FrontendScreens/VehicleSelect.xml'
        if not path.exists():self.skipTest('Local accepted SDK33 scene unavailable')
        original=path.read_bytes();p=scenario(64,(8,43,13));canonical=copy.deepcopy(SDK33)
        rows=[]
        for i in range(33,64):
            local=len(canonical['T2']);canonical['T2'].append(i)
            rows.append({'vehicle_class':'T2','class_local_index':local,'frontend':{'vehicle_select_art':{'frame':i+6}}})
        result=reorder_scene(scene_append(original,rows),{'canonical':canonical,'class_to_physical_ids':p['classes']}).decode('utf-8-sig')
        self.assertEqual(result.count('<Egg Name="T2_Car'),43)
        a,b=g._egg_span(result,'T2_Car43')
        self.assertIn('Frontend/VehicleSelect/Button42XPos',result[a:b])
        old=original.decode('utf-8-sig')
        for name in ('T1_Car1','T1_Car8','T3_Car1','T3_Car13'):
            a,b=g._egg_span(old,name);c,d=g._egg_span(result,name)
            self.assertEqual(old[a:b],result[c:d])


class RegistryResourceVerification(unittest.TestCase):
    def test_hash_file_set_and_private_state_exceptions(self):
        from build_vehicle_registry import verify_bundle
        with tempfile.TemporaryDirectory() as directory:
            bundle=Path(directory);root=bundle/'resource-root';(root/'DataGame').mkdir(parents=True)
            model=root/'model.dx';model.write_bytes(b'fixture model')
            row={'path':'model.dx','size':13,'sha256':hashlib.sha256(model.read_bytes()).hexdigest()}
            raw=json.dumps({'resources':[row]}).encode();(bundle/'resource-manifest.json').write_bytes(raw)
            ctx={'files':{'resource-manifest.json':raw}}
            self.assertEqual(verify_bundle(bundle,ctx)['resource_count'],1)
            (root/'DataGame/PlayerState.xml').write_text('mutable state checked separately by native launcher')
            self.assertEqual(verify_bundle(bundle,ctx)['resource_count'],1)
            model.write_bytes(b'changed model')
            with self.assertRaisesRegex(ValueError,'Resource changed'):verify_bundle(bundle,ctx)
            model.write_bytes(b'fixture model');extra=root/'extra';extra.write_bytes(b'X')
            with self.assertRaisesRegex(ValueError,'Unlisted'):verify_bundle(bundle,ctx)
            extra.unlink();model.unlink()
            with self.assertRaisesRegex(ValueError,'set changed'):verify_bundle(bundle,ctx)


if __name__=='__main__':unittest.main()
