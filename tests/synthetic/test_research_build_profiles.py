"""Synthetic profile gates/oracles; no retail bytes or live process required."""
import copy
import contextlib
import io
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import research_build_profiles as b
import r_ai1_observe as adapter


def fixture():
    data=bytearray(0x2000)
    data[:2]=b'MZ';struct.pack_into('<I',data,0x3c,0x80);data[0x80:0x84]=b'PE\0\0'
    struct.pack_into('<HHI',data,0x84,0x14c,1,12345)
    struct.pack_into('<H',data,0x94,0xe0)
    struct.pack_into('<H',data,0x98,0x10b)
    for offset,value in ((0xa8,0x1000),(0xb4,0x400000),(0xd0,0x3000)):
        struct.pack_into('<I',data,offset,value)
    at=0x178;data[at:at+8]=b'.text\0\0\0'
    struct.pack_into('<IIII',data,at+8,0x1000,0x1000,0x1000,0x1000)
    struct.pack_into('<I',data,at+36,0x60000020)
    data[0x1000:0x1010]=bytes(range(16))
    data=bytes(data);pe=b.pe_layout(data)
    canonical=dict(retail_pe=pe,anchors=[dict(name='test_anchor',va=0x401000,length=16,
            sha256=b.digest(data[0x1000:0x1010]),section='.text',semantics='Synthetic anchor')],
            profiles=[dict(profile='fixture',sha256=b.digest(data),size=len(data),pe=pe)])
    return data,canonical


def capability_fixture():
    """Three-section retail-shaped PE with independently fingerprinted Broker anchors."""
    data=bytearray(0x5000)
    data[:2]=b'MZ';struct.pack_into('<I',data,0x3c,0x80);data[0x80:0x84]=b'PE\0\0'
    struct.pack_into('<HHI',data,0x84,0x14c,3,12345)
    struct.pack_into('<H',data,0x94,0xe0);struct.pack_into('<H',data,0x98,0x10b)
    for offset,value in ((0xa8,0x1000),(0xb4,0x400000),(0xd0,0x5000)):
        struct.pack_into('<I',data,offset,value)
    sections=[('.text',0x2000,0x1000,0x2000,0x1000,0x60000020),
              ('.rdata',0x1000,0x3000,0x1000,0x3000,0x40000040),
              ('.data',0x1000,0x4000,0x1000,0x4000,0xC0000040)]
    at=0x178
    for name,vs,rva,size,raw,flags in sections:
        data[at:at+8]=name.encode().ljust(8,b'\0')
        struct.pack_into('<IIII',data,at+8,vs,rva,size,raw);struct.pack_into('<I',data,at+36,flags)
        at+=40
    for offset in range(0x1000,0x1180,0x10):
        data[offset:offset+16]=bytes((offset+i)&0xff for i in range(16))
    data[0x3000:0x3010]=bytes(range(16))
    data[0x4000:0x4008]=bytes(8)
    image=bytes(data);pe=b.pe_layout(image)
    specs=[('resource_file_open',0x401100,16,'.text'),
           ('broker_editor_dump_route',0x401040,16,'.text'),
           ('broker_singleton_accessor',0x401080,16,'.text'),
           ('debug_logger',0x401000,16,'.text'),
           ('native_dump_walker',0x4010C0,16,'.text'),
           ('main_loop',0x401140,16,'.text'),
           ('debug_sink_vtable',0x403000,16,'.rdata'),
           ('debug_sink_global',0x404000,4,'.data'),
           ('broker_manager_global',0x404004,4,'.data'),
           ('loading_legacy_failure',0x401180,16,'.text')]
    anchors=[]
    for name,va,length,section in specs:
        raw,actual,offset=b.window(image,pe,va,length)
        anchors.append(dict(name=name,va=va,length=length,sha256=b.digest(raw),section=section,
                            semantics='synthetic capability anchor'))
    canonical={'retail_pe':pe,'anchors':anchors,'profiles':[],
               'families':{'retail-broker-v1':{'pe_reference':'retail_pe',
                  'anchor_names':[row['name'] for row in anchors],
                  'observatory_layout_profile':'fixture'}}}
    return image,canonical


def snapshot(profile='retail-merc-id26',ids=(26,1,2,3)):
    p=next(r for r in b.definitions()['profiles'] if r['profile']==profile)
    vals={'Race/NumCars':4,'Race/NumPlayers':1,'Race/NumNetworkPlayers':0,'Race/Type':2,
          'Race/AttractMode':False,'Race/PlaybackReplay':False}
    for n,id in enumerate(ids):
        record=b.vehicle(profile,id)
        vals.update({f'Race/Car{n}/{key}':value for key,value in
                     dict(CarID=id,CarClass=record['class'],CarType=record['CarType'],
                          WheelType=record['WheelType'],PlayerType=1 if n==0 else 2,DriverID=30 if n==0 else n).items()})
        vals[f'Vehicles/Car{n}/Exists']=1;vals[f'Physics/Car{n}/Exists']=1
    return dict(kind='master-rallye-broker-dump-snapshot',schema_version=1,
                source=dict(image_sha256=p['sha256'],image_size=p['size'],build_profile=profile,
                            freshness='post_baseline_complete_dump_proven',broker_dump_variant='native_stock',label='merc-id26-race'),
                entries=[dict(path=k,value=v) for k,v in vals.items()])


class ProfileAudit(unittest.TestCase):
    def test_exact_registered_fixture(self):
        data,defs=fixture()
        with patch.object(b,'definitions',return_value=defs):self.assertEqual(b.identify(data)['profile'],'fixture')

    def test_unknown_hash_rejected(self):
        data,defs=fixture();wrong=data[:-1]+b'X'
        with patch.object(b,'definitions',return_value=defs):
            with self.assertRaises(ValueError):b.identify(wrong)
    def test_one_byte_change_does_not_gain_trust(self):
        data,defs=fixture();wrong=data[:-1]+b'X'
        with patch.object(b,'definitions',return_value=defs):
            audit=b.audit_build(wrong)
        self.assertTrue(audit['anchor_compatible']);self.assertIsNone(audit['exact_registered_profile'])
        self.assertFalse(audit['automatic_trust'])
    def test_corrupted_anchor_incompatible(self):
        data,defs=fixture();wrong=bytearray(data);wrong[0x1004]^=1
        with patch.object(b,'definitions',return_value=defs):self.assertFalse(b.audit_build(bytes(wrong))['anchor_compatible'])

    def test_only_exact_approved_loading_anchor_variant_is_compatible(self):
        data,defs=fixture();anchor=defs['anchors'][0]
        anchor['name']='loading_legacy_failure'
        patched=bytearray(data);patched[0x1004:0x1009]=bytes.fromhex('e9d8ffffff')
        anchor['approved_variants']=[dict(id='r-ai2-loading-false-trigger-neutralization-v1',
            sha256=b.digest(patched[0x1000:0x1010]))]
        with patch.object(b,'definitions',return_value=defs):
            accepted=b.audit_build(bytes(patched))
            self.assertTrue(accepted['anchor_compatible'])
            self.assertEqual(accepted['anchors'][0]['matched_variant'],
                             'r-ai2-loading-false-trigger-neutralization-v1')
            self.assertFalse(accepted['capabilities']['legacy_loading_attract_present'])
            self.assertTrue(accepted['capabilities']['legacy_loading_attract_neutralized'])
            changed=bytearray(patched);changed[0x100f]^=1
            rejected=b.audit_build(bytes(changed))
            self.assertFalse(rejected['anchor_compatible'])
            stock=bytearray(data);stock_audit=b.audit_build(bytes(stock))
            self.assertNotEqual(b._audit_fingerprint(accepted),b._audit_fingerprint(stock_audit))
            relabeled=dict(accepted);relabeled['anchors']=[dict(row) for row in accepted['anchors']]
            relabeled['anchors'][0]['matched_variant']='different-approved-variant'
            self.assertNotEqual(b._audit_fingerprint(accepted),b._audit_fingerprint(relabeled))
    def test_registered_identity_does_not_skip_anchors(self):
        data,defs=fixture();defs['anchors'][0]['sha256']='0'*64
        with patch.object(b,'definitions',return_value=defs):
            with self.assertRaises(ValueError):b.identify(data)
    def test_relocated_section_incompatible(self):
        data,defs=fixture();wrong=bytearray(data);struct.pack_into('<I',wrong,0x184,0x2000)
        with patch.object(b,'definitions',return_value=defs):self.assertFalse(b.audit_build(bytes(wrong))['anchor_compatible'])
    def test_pe_file_extent_bounds(self):
        data,_=fixture();wrong=bytearray(data);struct.pack_into('<I',wrong,0x188,0xffffff)
        with self.assertRaises(ValueError):b.pe_layout(wrong)
    def test_missing_pe_rejected(self):
        with self.assertRaises(ValueError):b.pe_layout(bytes(512))
    def test_profile_pins_are_distinct(self):
        p=b.definitions()['profiles'];self.assertEqual({x['sha256'] for x in p},{b.PRISTINE_SHA256,b.MERC_SHA256})
        self.assertEqual(len({x['profile'] for x in p}),2)
    def test_profile_lookup_is_deterministic(self):
        self.assertEqual(b.definitions(),b.definitions())
    def test_merc_capabilities_stock_unsafe(self):
        p=next(x for x in b.definitions()['profiles'] if x['sha256']==b.MERC_SHA256)
        self.assertFalse(p['native_dump_post_results_safe']);self.assertTrue(p['legacy_loading_attract_present'])
        self.assertTrue(p['capabilities']['open_broker_editor'])
        self.assertEqual(p['vehicle_registry_profile'],'merc-id26')

    def test_critical_anchor_mutation_refuses_unknown_build(self):
        data,defs=capability_fixture()
        anchor=next(row for row in defs['anchors'] if row['name']=='resource_file_open')
        _raw,_section,offset=b.window(data,b.pe_layout(data),anchor['va'],anchor['length'])
        mutated=bytearray(data);mutated[offset]^=1
        with patch.object(b,'definitions',return_value=defs):
            audit=b.audit_build(bytes(mutated))
            self.assertFalse(audit['anchor_compatible'])
            with self.assertRaises(ValueError) as ctx:
                b.resolve_build(bytes(mutated),write_local_profile=False)
        message=str(ctx.exception)
        self.assertIn('structural family/Broker-core audit',message)
        self.assertIn(anchor['name'],message)

    def test_unrelated_anchor_does_not_disable_broker_read_or_native_dump(self):
        data,defs=capability_fixture();changed=bytearray(data);changed[0x1180]^=0x7f
        with patch.object(b,'definitions',return_value=defs):
            audit=b.audit_build(bytes(changed))
            self.assertFalse(audit['anchor_compatible'])
            self.assertTrue(audit['capability_compatible'])
            self.assertTrue(audit['capabilities']['broker_read'])
            self.assertFalse(audit['capabilities']['open_broker_editor'])
            self.assertTrue(audit['capabilities']['native_dump'])
            self.assertEqual(audit['capabilities']['post_results_native_dump_safe'],False)

    def test_walker_failure_keeps_passive_reader_but_disables_native_dump(self):
        data,defs=capability_fixture();changed=bytearray(data);changed[0x10C2]^=1
        with patch.object(b,'definitions',return_value=defs):
            audit=b.audit_build(bytes(changed))
            self.assertTrue(audit['capabilities']['broker_read'])
            self.assertFalse(audit['capabilities']['open_broker_editor'])
            self.assertFalse(audit['capabilities']['native_dump'])
            self.assertFalse(audit['capabilities']['active_race_native_dump_safe'])
            self.assertIsNone(audit['capabilities']['post_results_native_dump_safe'])
            self.assertEqual(audit['capabilities']['broker_dump_variant'],'unknown')

    def test_exact_hardened_walker_variant_alone_enables_results_dump_safety(self):
        data,defs=capability_fixture()
        walker=next(row for row in defs['anchors'] if row['name']=='native_dump_walker')
        patched=bytearray(data);patched[0x10C0:0x10C8]=bytes.fromhex('e97dc20800909090')
        expected=bytes(patched[0x10C0:0x10D0])
        walker['approved_variants']=[dict(id='native-hardened-r-ai1-v1',sha256=b.digest(expected))]
        with patch.object(b,'definitions',return_value=defs):
            accepted=b.audit_build(bytes(patched))
            self.assertTrue(accepted['capabilities']['native_dump'])
            self.assertTrue(accepted['capabilities']['hardened_dump'])
            self.assertTrue(accepted['capabilities']['post_results_native_dump_safe'])
            self.assertEqual(accepted['capabilities']['broker_dump_variant'],'native_hardened')
            changed=bytearray(patched);changed[0x10CF]^=1
            rejected=b.audit_build(bytes(changed))
            self.assertFalse(rejected['capabilities']['native_dump'])
            self.assertIsNone(rejected['capabilities']['post_results_native_dump_safe'])

    def test_allow_degraded_requires_broker_core_and_cache_is_reaudited(self):
        data,defs=capability_fixture();changed=bytearray(data);changed[0x1180]^=0x7f
        with tempfile.TemporaryDirectory() as td, patch.object(b,'definitions',return_value=defs):
            with self.assertRaisesRegex(ValueError,'structural family/Broker-core'):
                b.resolve_build(bytes(changed),cache_root=Path(td)/'build-profiles')
            first=b.resolve_build(bytes(changed),cache_root=Path(td)/'build-profiles',allow_degraded=True)
            self.assertEqual(first['status'],'CAPABILITY_COMPATIBLE')
            self.assertEqual(first['profile_origin'],'locally_audited')
            self.assertEqual(first['schema_version'],b.PROFILE_SCHEMA_VERSION)
            second=b.resolve_build(bytes(changed),cache_root=Path(td)/'build-profiles',allow_degraded=True)
            self.assertTrue(second['cache_reused'])
            broken=bytearray(changed);broken[0x1001]^=1
            with self.assertRaisesRegex(ValueError,'structural family/Broker-core'):
                b.resolve_build(bytes(broken),cache_root=Path(td)/'build-profiles',allow_degraded=True)

    def test_schema_one_local_cache_is_reaudited_and_migrated(self):
        data,defs=capability_fixture();changed=bytearray(data);changed[0x1180]^=0x7f
        with tempfile.TemporaryDirectory() as td, patch.object(b,'definitions',return_value=defs):
            cache=Path(td)/'build-profiles'
            first=b.resolve_build(bytes(changed),cache_root=cache,allow_degraded=True)
            cache_path=Path(first['local_profile_cache'])
            old=json.loads(cache_path.read_text(encoding='utf-8'))
            old['schema_version']=1
            cache_path.write_text(json.dumps(old),encoding='utf-8')
            refreshed=b.resolve_build(bytes(changed),cache_root=cache,allow_degraded=True)
            self.assertFalse(refreshed['cache_reused'])
            migrated=json.loads(cache_path.read_text(encoding='utf-8'))
            self.assertEqual(migrated['schema_version'],b.PROFILE_SCHEMA_VERSION)
            self.assertEqual(migrated['audit_version'],b.AUDIT_VERSION)


class RegistryOracle(unittest.TestCase):
    def test_merc_forward26(self):self.assertEqual(b.absolute_id('retail-merc-id26',0,7),26)
    def test_merc_reverse26(self):
        v=b.vehicle('retail-merc-id26',26);self.assertEqual((v['class'],v['local_index']),(0,7))
        self.assertEqual((v['CarType'],v['WheelType']),('Mercedes','Mercedes'))
    def test_id25_preserved(self):
        v=b.vehicle('retail-merc-id26',25);self.assertEqual((v['class'],v['local_index'],v['CarType']),(2,11,'Trooper'))
    def test_pristine26_invalid(self):
        with self.assertRaises(ValueError):b.vehicle('retail-pristine',26)
    def test_pristine25_not_named(self):
        with self.assertRaises(ValueError):b.vehicle('retail-pristine',25)
    def test_pristine_local7_not_valid_T1(self):
        with self.assertRaises(ValueError):b.absolute_id('retail-pristine',0,7)
    def test_neighbors_stock_unchanged(self):
        for id in range(25):self.assertEqual(b.vehicle('retail-pristine',id),b.vehicle('retail-merc-id26',id))
    def test_all_merc_roundtrips(self):
        for id in range(27):
            v=b.vehicle('retail-merc-id26',id);self.assertEqual(b.absolute_id('retail-merc-id26',v['class'],v['local_index']),id)
    def test_invalid_ids_rejected(self):
        for id in (-1,27,True,'26'):
            with self.assertRaises(ValueError):b.vehicle('retail-merc-id26',id)
    def test_unknown_profile_rejected(self):
        with self.assertRaises(ValueError):b.vehicle('retail-derived-untrusted',26)
    def test_future_entries_are_data_driven(self):
        v=b.registry('retail-merc-id26');v[40]=dict(id=40,**{'class':1},local_index=7)
        with patch.object(b,'registry',return_value=v):self.assertEqual(b.absolute_id('retail-merc-id26',1,7),40)


class RuntimeOracle(unittest.TestCase):
    def test_merc26_matches_state_only(self):
        r=b.check_vehicle(snapshot(),'retail-merc-id26',0,26)
        self.assertEqual(r['status'],'BROKER_STATE_MATCH_ONLY');self.assertFalse(r['runtime_full_pass'])
    def test_stock_under_merc_valid(self):self.assertEqual(b.check_vehicle(snapshot(ids=(0,1,2,3)),'retail-merc-id26',0,0)['participant']['id'],0)
    def test_stock_under_pristine_valid(self):self.assertEqual(b.check_vehicle(snapshot('retail-pristine',(0,1,2,3)),'retail-pristine',0)['participant']['id'],0)
    def test_pristine26_rejected_even_with_spoofed_metadata(self):
        d=snapshot();p=next(x for x in b.definitions()['profiles'] if x['profile']=='retail-pristine')
        d['source'].update(image_sha256=p['sha256'],build_profile=p['profile'])
        with self.assertRaises(ValueError):b.check_vehicle(d,'retail-pristine',0)
    def test_wrong_capture_hash(self):
        d=snapshot();d['source']['image_sha256']='0'*64
        with self.assertRaises(ValueError):b.check_vehicle(d,'retail-merc-id26',0)
    def test_wrong_registry_class(self):
        d=snapshot();next(e for e in d['entries'] if e['path']=='Race/Car0/CarClass')['value']=2
        with self.assertRaises(ValueError):b.check_vehicle(d,'retail-merc-id26',0)
    def test_alias_family_rejected(self):
        d=snapshot();next(e for e in d['entries'] if e['path']=='Race/Car0/CarType')['value']='Landcruiser'
        with self.assertRaises(ValueError):b.check_vehicle(d,'retail-merc-id26',0)
    def test_results_label_rejected(self):
        d=snapshot();d['source']['label']='merc-results'
        with self.assertRaises(ValueError):b.check_vehicle(d,'retail-merc-id26',0)
    def test_attract_rejected(self):
        d=snapshot();next(e for e in d['entries'] if e['path']=='Race/AttractMode')['value']=True
        with self.assertRaises(ValueError):b.check_vehicle(d,'retail-merc-id26',0)
    def test_missing_physics_rejected(self):
        d=snapshot();d['entries']=[e for e in d['entries'] if e['path']!='Physics/Car0/Exists']
        with self.assertRaises(ValueError):b.check_vehicle(d,'retail-merc-id26',0)
    def test_profile_size_gate(self):
        d=snapshot();d['source']['image_size']+=1
        with self.assertRaises(ValueError):b.check_vehicle(d,'retail-merc-id26',0)
    def test_duplicate_vehicle_rejected(self):
        with self.assertRaises(ValueError):b.check_vehicle(snapshot(ids=(26,1,1,3)),'retail-merc-id26',0)
    def test_inactive_slot_rejected(self):
        with self.assertRaises(ValueError):b.check_vehicle(snapshot(),'retail-merc-id26',4)


class AuditedAdapter(unittest.TestCase):
    def test_unknown_hash_rejected_before_external_import(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'MRallye_merc.exe';p.write_bytes(b'MZ unknown')
            with self.assertRaises(ValueError):adapter.load_profile(Path(td),p)
    def test_unknown_implementation_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            for name in adapter.OBSERVATORY_FILES:(Path(td)/name).write_text('untrusted')
            with self.assertRaises(ValueError):adapter.verify_distribution(Path(td))
    def test_only_audited_basename_comparisons_change(self):
        src='def names(a,b):\n return a.casefold()=="mrallye.exe", b.casefold()!="mrallye.exe"\n'
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'synthetic_names.py').write_text(src)
            fixture_hash=b.digest((Path(td)/'synthetic_names.py').read_bytes())
            with patch.dict(adapter.OBSERVATORY_FILES,{'synthetic_names.py':fixture_hash}):
                module=adapter._research_module(Path(td),'synthetic_names')
            try:
                self.assertEqual(module.names('MRallye_merc.exe','MRallye.exe'),(True,False))
                self.assertEqual(module.names('MRallye_mercv2.exe','MRallye_mercv2.exe'),(True,False))
                self.assertEqual(module.names('unknown.exe','unknown.exe'),(False,True))
                self.assertEqual((Path(td)/'synthetic_names.py').read_text(),src)
            finally:sys.modules.pop('synthetic_names',None)
    def test_changed_basename_filter_shape_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'synthetic_names.py').write_text('def names(a):\n return a.casefold()=="mrallye.exe"\n')
            source=(Path(td)/'synthetic_names.py').read_bytes()
            with patch.dict(adapter.OBSERVATORY_FILES,{'synthetic_names.py':b.digest(source)}):
                with self.assertRaises(ValueError):adapter._research_module(Path(td),'synthetic_names')


if __name__=='__main__':unittest.main()
