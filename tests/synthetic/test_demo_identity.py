"""Historical identity, exact retail clone and bounded original table regressions."""
import copy,struct,unittest,xml.etree.ElementTree as ET
from master_rallye.addon_sdk.demo_identity import localized_tables,localized_value,ps2_registration,selected_identity
from master_rallye.addon_sdk.demo_restoration import restoration_physics,verify_retail_clone
from master_rallye.addon_sdk.physics_profile import compile_family
from tests.synthetic.test_physics_profile import fixture


def elf():
    raw=bytearray(4096);raw[:6]=b'\x7fELF\x01\x01';struct.pack_into('<I',raw,28,52);struct.pack_into('<2H',raw,42,32,1)
    struct.pack_into('<8I',raw,52,1,0,0x100000,0,len(raw),len(raw),7,4);return raw


class DemoIdentityTests(unittest.TestCase):
    def test_interior_string_pointers_and_conflicting_tables_are_not_lost(self):
        raw=elf();raw[2048:2064]=b'TOYOTA FORESTER\0\0'
        for off,cat,index,ptr in [(1024,52,8,0x100807),(1036,57,8,0x100800)]:struct.pack_into('<3I',raw,off,cat,index,ptr)
        rows=localized_tables(raw);self.assertEqual(localized_value(rows,52,8)['value'],'FORESTER')
        struct.pack_into('<3I',raw,1048,52,8,0x100800)
        self.assertEqual(localized_value(localized_tables(raw),52,8)['status'],'UNKNOWN')
        self.assertEqual(localized_value(rows,57,13)['status'],'UNKNOWN')

    def test_retired_family_does_not_inherit_later_pickup_identity(self):
        original={'value':None,'status':'UNKNOWN','evidence':'No original registration'}
        identity={'driver':original,'frontend':{'combined':'DEMO SUV'}}
        fallback={'value':'VERIFIED DRIVER','kind':'REAL_FALLBACK','credentials':'1999 manufacturer event','sources':[{'url':'https://example.org/original-event-report'}]}
        identity['driver_assignment']=fallback;before=copy.deepcopy(identity)
        selected=selected_identity(identity,[.25,.55,.85,1])
        self.assertEqual(selected['driver']['kind'],'REAL_FALLBACK');self.assertIsNone(selected['driver']['original']['value']);self.assertEqual(identity,before)
        identity['driver']={'value':'RECOVERED ORIGINAL','status':'PROVEN'}
        self.assertEqual(selected_identity(identity,[1,0,0,1])['driver']['value'],'RECOVERED ORIGINAL')
        self.assertEqual(selected_identity(identity,[1,0,0,1])['driver']['kind'],'ORIGINAL')
        self.assertEqual(identity['driver_assignment'],fallback)
        identity['driver']['status']='INFERRED'
        with self.assertRaisesRegex(ValueError,'Unproven original'):selected_identity(identity,[1,0,0,1])
        identity['driver']['status']='PROVEN'
        del fallback['sources']
        with self.assertRaises(ValueError):selected_identity(identity,[1,0,0,1])

    def test_marker_is_explicit_and_cannot_be_nan_or_implicitly_original(self):
        identity={'driver':{'value':None},'frontend':{'combined':'SUV'}}
        self.assertEqual(selected_identity(identity,[0,0,1,1])['race_marker']['status'],'UNKNOWN')
        identity['race_marker']={'value':[0,float('nan'),1,1],'status':'PROVEN'}
        with self.assertRaises(ValueError):selected_identity(identity,[0,0,1,1])

    def test_retail_mode_never_applies_historical_wheelbase_or_torque(self):
        members,profile=fixture();source=b'<Game><Value Name="Vehicles/Old/Dimensions/WheelBase" Value="2.4"/><Value Name="Vehicles/Old/Engine/TorqueEntry7" Value=".9 99"/></Game>'
        policy={'mode':'retail','input':'old','source_family':'Old','donor_family':'Navara','require_exact_clone':True,'reason':'Owner selected complete retail physics'}
        p,r=restoration_physics(policy,profile,{'old':source},members,runtime_family='AddonOne')
        self.assertEqual(p['overrides'],{});self.assertFalse(r['inactive_historical_evidence']['applied']);self.assertEqual(r['inactive_historical_evidence']['row_count'],2)
        for name,raw in members.items():
            output,_=compile_family(raw,p,donor_family='Navara',runtime_family='AddonOne',source_label=name)
            rows=lambda b,prefix:{v.get('Name')[len(prefix):]:{k:w for k,w in v.attrib.items()if k!='Name'}for v in ET.fromstring(b).iter('Value')if v.get('Name','').startswith(prefix)}
            self.assertEqual(rows(raw,'Vehicles/Navara/'),rows(output,'Vehicles/AddonOne/'))
        compiled={n:compile_family(raw,p,donor_family='Navara',runtime_family='AddonOne',source_label=n)[0]for n,raw in members.items()}
        self.assertEqual(len(verify_retail_clone(members,compiled,donor_family='Navara',runtime_family='AddonOne')),2)
        corrupted=copy.deepcopy(compiled);corrupted['DataGame/vehicles.xml']=corrupted['DataGame/vehicles.xml'].replace(b'Name="Vehicles/AddonOne/Dimensions/WheelBase" Type="Float" Value="1"',b'Name="Vehicles/AddonOne/Dimensions/WheelBase" Type="Float" Value="2.4"')
        with self.assertRaisesRegex(ValueError,'Compiled retail clone differs'):verify_retail_clone(members,corrupted,donor_family='Navara',runtime_family='AddonOne')
        bad=copy.deepcopy(profile);bad['overrides']={'DataGame/vehicles.xml':{'Dimensions/WheelBase':2.4}}
        with self.assertRaisesRegex(ValueError,'Exact retail clone'):restoration_physics(policy,bad,{'old':source},members,runtime_family='AddonOne')
        bad=copy.deepcopy(profile);bad['ride_height_reference_m']={'Front':-.1,'Rear':-.1}
        with self.assertRaisesRegex(ValueError,'Exact retail clone'):restoration_physics(policy,bad,{'old':source},members,runtime_family='AddonOne')
        self.assertEqual(source,b'<Game><Value Name="Vehicles/Old/Dimensions/WheelBase" Value="2.4"/><Value Name="Vehicles/Old/Engine/TorqueEntry7" Value=".9 99"/></Game>')

    def test_r5900_static_marker_inputs_must_all_be_known(self):
        raw=elf();raw[2048:2055]=b'Family\0'
        imm=lambda op,rs,rt,value:(op<<26)|(rs<<21)|(rt<<16)|(value&65535)
        words=[imm(15,0,5,0x10),imm(13,5,5,0x800),(3<<26)|(0x100400>>2),0,
               imm(15,0,1,0x3f80),(17<<26)|(4<<21)|(1<<16),imm(9,29,16,32),imm(43,29,16,8),
               *[imm(57,16,0,i*4)for i in range(4)],imm(9,0,5,0),(3<<26)|(0x100500>>2),0]
        for i,word in enumerate(words):struct.pack_into('<I',raw,256+i*4,word)
        args=dict(begin=0x100100,end=0x100100+len(words)*4,string_call=0x100400,record_call=0x100500)
        self.assertEqual(ps2_registration(raw,**args)[0]['rgba'],[1,1,1,1])
        struct.pack_into('<I',raw,256+11*4,0) # missing alpha store
        with self.assertRaisesRegex(ValueError,'Unknown original marker'):ps2_registration(raw,**args)
        struct.pack_into('<I',raw,256+11*4,0xffffffff)
        with self.assertRaisesRegex(ValueError,'Unsupported R5900'):ps2_registration(raw,**args)


if __name__=='__main__':unittest.main()
