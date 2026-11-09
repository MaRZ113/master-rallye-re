from __future__ import annotations
import copy
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tools')]
import build_runtime_launcher as launcher
from master_rallye.addon_sdk.capacity_profile import scenario


def fixture(count=128):
    distribution=(8,12,count-20)
    capacity=scenario(count,distribution)
    base=0x10000000
    data=bytearray(524288)
    descriptor=base+300000
    cursor=300044
    def emit(values):
        nonlocal cursor
        address=base+cursor
        struct.pack_into('<'+str(len(values))+'I', data,cursor,*values)
        cursor+=4*len(values)
        return address
    counts=emit([len(ids) for ids in capacity['classes'].values()])
    pointers_at=cursor; cursor+=12
    pointers=[]; reverse={}
    for cls, ids in enumerate(capacity['classes'].values()):
        pointers.append(emit(ids))
        reverse.update({i:(cls,n) for n,i in enumerate(ids)})
    struct.pack_into('<3I',data,pointers_at,*pointers)
    reverse_classes=emit([reverse[i][0] for i in range(count)])
    reverse_locals=emit([reverse[i][1] for i in range(count)])
    struct.pack_into('<4s10I',data,descriptor-base,b'MRVC',1,44,count,52,3,0x45a3c0,counts,base+pointers_at,reverse_classes,reverse_locals)
    profile={key:'a'*64 for key in ('addon_plan_sha256','native_patch_manifest_sha256','native_patch_operations_sha256','resource_manifest_sha256','resource_index_sha256','reconstructed_reference_file_sha256')}
    profile.update(retail_exe={'sha256':'a'*64},resource_count=1,profile='sdk-configurable-vehicle-registry',capacity_profile=capacity,
        vehicle_registry_descriptor=descriptor,sdk_roster_layout={'record_count':count,'addon_ids':list(range(26,count))},
        native_extension={'address':base,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'allocation_size':524288})
    return profile,bytes(data)


class CapacityLauncherTests(unittest.TestCase):
    def test_course_descriptor_shared_layout_and_inverse_maps(self):
        profile,data=fixture(35);data=bytearray(data);base=0x10000000;cursor=350000
        def emit(values):
            nonlocal cursor
            address=base+cursor;struct.pack_into('<'+str(len(values))+'I',data,cursor,*values);cursor+=4*len(values);return address
        groups=[list(range(10,13))+[40,39],list(range(13,16)),list(range(16,19)),list(range(19,22)),list(range(22,25)),list(range(25,36)),list(range(10)),list(range(36,39))]
        counts=emit([len(g) for g in groups]);ptrs=emit([emit(g) for g in groups])
        reverse={r:(g,p) for g,rows in enumerate(groups) for p,r in enumerate(rows)}
        rg=emit([reverse[i][0] for i in range(41)]);rl=emit([reverse[i][1] for i in range(41)])
        strings=[]
        for i in (39,40):
            raw=f'CourseRegistryV1/race-{i}'.encode()+b'\0';strings.append(base+cursor);data[cursor:cursor+len(raw)]=raw;cursor+=len(raw)
        cursor=(cursor+3)//4*4
        progress=emit([0]*39+strings)
        stages=emit([3,10,11,12,3,13,14,15,3,16,17,18,3,19,20,21,3,22,23,24,3,36,37,38])
        address=emit([int.from_bytes(b'MRCR','little'),1,64,41,44,35,1824,3628,0x45a3c0,counts,ptrs,rg,rl,progress,stages,6])
        profile.update(course_registry_descriptor=address,course_registry_layout={'race_count':41,'allocation_size':3628})
        fields=launcher._course_descriptor(profile,profile['native_extension'],bytes(data))
        self.assertEqual(fields[7],3628)
        for index in (3,5,6,7,9,10,11,12,14):
            bad=data.copy();struct.pack_into('<I',bad,address-base+4*index,0xffffffff)
            with self.assertRaises(launcher.LauncherBuildError):launcher._course_descriptor(profile,profile['native_extension'],bytes(bad))

    def test_generic_profile_accepts_numeric_boundaries(self):
        for count in (33,128,129,255,256,257,512):
            profile,data=fixture(count)
            header=launcher._header(profile,{'operations':[{}]},data).decode()
            self.assertIn('#define MR_VEHICLE_REGISTRY_DESCRIPTOR',header)
            self.assertIn(f'44u, {count}u, 52u',header)
    def test_bad_or_unaligned_budget_rejected(self):
        for allocation in (524287,1,0x70000000):
            profile,data=fixture(); profile['native_extension']['allocation_size']=allocation
            with self.assertRaises(launcher.LauncherBuildError): launcher._header(profile,{'operations':[{}]},data)
    def test_missing_extension_or_payload_rejected(self):
        profile,data=fixture()
        with self.assertRaises(launcher.LauncherBuildError): launcher._header(profile,{'operations':[{}]})
        profile.pop('native_extension')
        with self.assertRaises(launcher.LauncherBuildError): launcher._header(profile,{'operations':[{}]},data)
    def test_descriptor_and_mapping_mutations_rejected(self):
        profile,data=fixture()
        for offset in (4,12,16,24,28,40,44):
            changed=bytearray(data); changed[300000+offset]^=1
            profile['native_extension']['sha256']=hashlib.sha256(changed).hexdigest()
            with self.assertRaises(launcher.LauncherBuildError): launcher._header(profile,{'operations':[{}]},bytes(changed))
    def test_sdk33_order_and_range_are_mandatory(self):
        profile,data=fixture(); profile['capacity_profile']['classes']['T1'][0:2]=[1,0]
        with self.assertRaises(launcher.LauncherBuildError): launcher._header(profile,{'operations':[{}]},data)
    def test_stale_environment_is_filtered_in_child_only(self):
        source=(ROOT/'runtime_launcher/src/main.cpp').read_text()
        self.assertNotIn('SetEnvironmentVariable',source)
        self.assertIn('childEnvironment.data(), workingDirectory.c_str()',source)
        self.assertIn('name!=L"mr_vehicle_registry_descriptor"',source)
        self.assertIn('mode != L"--preflight-suspended"',source)
        self.assertIn('singleton!=0',source)

    def test_capacity_accepts_multiple_disjoint_data_pages(self):
        profile,data=fixture()
        profile['native_extension']['writable_ranges']=[{'offset':4096,'size':4096},{'offset':8192,'size':4096}]
        header=launcher._header(profile,{'operations':[{}]},data).decode()
        self.assertIn('#define MR_EXTENSION_RW_COUNT 2u',header)
        profile['native_extension']['writable_ranges'][1]['offset']=4096
        with self.assertRaises(launcher.LauncherBuildError): launcher._header(profile,{'operations':[{}]},data)


class NativeRosterStateTests(unittest.TestCase):
    def test_active_competition_requires_matching_dependency_baseline(self):
        with tempfile.TemporaryDirectory(prefix='mr-competition-') as directory:
            bundle=Path(directory);path=bundle/'PlayerState.xml'
            def run(active):
                raw=('<Game><Broker><Value Name="MasterRallye/GameSaved" Type="Bool" Value="'+str(active).lower()+'"/><Value Name="Frontend/QuickRace/Car0" Type="Int" Value="31"/></Broker></Game>').encode()
                path.write_bytes(raw)
                result=subprocess.run([str(self.exe),'--verify-competition-state',str(path),str(bundle)],capture_output=True,text=True)
                self.assertEqual(path.read_bytes(),raw)
                return result
            self.assertNotEqual(run(True).returncode,0)
            self.assertFalse((bundle/'competition-baseline.txt').exists())
            result=run(False);self.assertEqual(result.returncode,0,result.stderr)
            marker=bundle/'competition-baseline.txt';self.assertEqual([len(s) for s in marker.read_text().splitlines()],[64,64])
            # An imported active save cannot borrow a fresh package baseline.
            self.assertNotEqual(run(True).returncode,0)
            # Fixture for the association recorded after a verified owned game
            # exits normally; the test never runs or alters an installed game.
            contract=marker.read_text().splitlines()[0]
            marker.write_text(contract+'\n'+hashlib.sha256(path.read_bytes()).hexdigest()+'\n')
            self.assertEqual(run(True).returncode,0)
            marker.write_text('0'*64+'\n');self.assertNotEqual(run(True).returncode,0)
            self.assertEqual(marker.read_text(),'0'*64+'\n')

    @classmethod
    def setUpClass(cls):
        value=os.environ.get('MR_CAPACITY_TEST_LAUNCHER')
        if not value: raise unittest.SkipTest('set MR_CAPACITY_TEST_LAUNCHER to a capacity native launcher')
        cls.exe=Path(value)
    def invoke(self,xml,passed):
        raw=xml.encode() if isinstance(xml,str) else xml
        with tempfile.TemporaryDirectory(prefix='mr-roster-state-') as tmp:
            path=Path(tmp)/'PlayerState.xml';path.write_bytes(raw)
            result=subprocess.run([str(self.exe),'--verify-roster-state',str(path)],capture_output=True,text=True)
            self.assertEqual(path.read_bytes(),raw)
        self.assertEqual(result.returncode==0,passed,result.stdout+result.stderr)
        return result.stdout+result.stderr
    def test_native_good_ids_entities_and_active_campaign(self):
        self.invoke('<Game><Broker><Value Name="Frontend/QuickRace/Car0" Type="Int" Value="31"/><Value Name="MasterRallye/GameSaved" Type="Bool" Value="True"/><Value Name="Settings/Player1Name" Type="String" Value="A &amp; B &#x41;"/></Broker></Game>',True)
    def test_native_class_pairs_and_sentinel(self):
        self.invoke('<Game><Broker><Value Name="Frontend/QuickRace/Car0" Type="Int" Value="-1"/><Value Name="MasterRallye/Car0/CarID" Type="Int" Value="31"/><Value Name="MasterRallye/Car0/CarClass" Type="Int" Value="1"/></Broker></Game>',True)
        self.invoke('<Game><Broker><Value Name="MasterRallye/Car0/CarID" Type="Int" Value="31"/><Value Name="MasterRallye/Car0/CarClass" Type="Int" Value="0"/></Broker></Game>',False)
        self.invoke('<Game><Broker><Value Name="RallyeCup/PlayerT1Car0" Type="Int" Value="31"/></Broker></Game>',False)
    def test_native_unknown_unsupported_duplicate_and_bad_xml(self):
        snippets=['<Value Name="Frontend/QuickRace/Car0" Type="Int" Value="2147483647"/>',
            '<Value Name="Frontend/QuickRace/Car0" Type="Int" Value="-2"/>',
            '<Value Name="Frontend/QuickRace/Car2" Type="Int" Value="0"/>',
            '<Value Name="Frontend/QuickRace/Car0" Type="Float" Value="0"/>',
            '<Value Name="MasterRallye/VehicleClass" Type="Int" Value="3"/>',
            '<Value Name="X" Type="Int" Value="0"/><Value Name="x" Type="Int" Value="1"/>',
            '<Value Name="X" Name="Y" Type="Int" Value="0"/>',
            '<Value Name="X" Type="String" Value="&unknown;"/>']
        for snippet in snippets:
            with self.subTest(snippet=snippet): self.invoke('<Game><Broker>'+snippet+'</Broker></Game>',False)
        for xml in ['<!DOCTYPE Game><Game><Broker></Broker></Game>','<?xml version="1.0" encoding="UTF-16"?><Game><Broker></Broker></Game>','<Game><Broker></Game>','<Game><Broker/></Game>','<Game><Broker></Broker></Game><Game/>',b'<Game><Broker>\xff</Broker></Game>',b'<Game>\x00</Game>']:
            with self.subTest(xml=xml): self.invoke(xml,False)

if __name__=='__main__': unittest.main()
