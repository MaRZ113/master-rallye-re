import copy
import json
from pathlib import Path
import unittest

import build_runtime_launcher as launcher
import sdk_capacity_native as native

ROOT=Path(__file__).resolve().parents[2]


class CapacityTests(unittest.TestCase):
    def test_audio_lookup_chains_parent_once_without_getter_reentry(self):
        class Code:
            def __init__(self):self.calls=[];self.blocks=[];self.jumps=[]
            def label(self,name):pass
            def emit(self,data):self.blocks.append(data)
            def call(self,target):self.calls.append(target)
            def jne(self,label):pass
            def jump(self,target):self.jumps.append(target)
        rows=json.loads((ROOT/'research/vehicles/scale1/probe-30-rows.json').read_text())
        code=Code();native.emit_audio_lookup(code,rows,0x12345678)
        self.assertEqual(code.calls,[0x12345678]);self.assertEqual(code.jumps,[])
        self.assertEqual(code.blocks[0],bytes.fromhex('ff742404'))
        self.assertEqual(code.blocks[-1],bytes.fromhex('c20400'))
    def test_probe_rows_use_the_shared_manifest_schema(self):
        rows=json.loads((ROOT/'research/vehicles/scale1/probe-30-rows.json').read_text())
        native.validate_rows(rows)
        for key,value in [('physical_id',True),('class_local_index',False),
                          ('race_colour_rgba_f32le_hex','00')]:
            changed=copy.deepcopy(rows);changed[0][key]=value
            with self.assertRaises((ValueError,RuntimeError)):native.validate_rows(changed)
        changed=copy.deepcopy(rows)
        changed[0]['assets']['model_package_root']='DataGx/Vehicles/Wrong'
        with self.assertRaises((ValueError,RuntimeError)):native.validate_rows(changed)
        with self.assertRaises(ValueError):native.validate_rows(rows+rows)

    def test_private_extension_trust_header_bounds(self):
        profile={k:'a'*64 for k in ('addon_plan_sha256','native_patch_manifest_sha256',
            'native_patch_operations_sha256','resource_manifest_sha256','resource_index_sha256',
            'reconstructed_reference_file_sha256')}
        profile.update(retail_exe={'sha256':'b'*64},resource_count=1)
        old=launcher._header(profile,{'operations':[{}]})
        self.assertNotIn(b'MR_EXTENSION_',old)
        extension={'address':0x10000000,'size':1341,'sha256':'c'*64,'allocation_size':65536}
        profile['native_extension']=extension
        self.assertIn(b'#define MR_EXTENSION_SIZE 1341u',launcher._header(profile,{'operations':[{}]}))
        for key,value in [('address',0x10001000),('size',0),('size',65537),('size',True),
                          ('allocation_size',4096),('sha256','C'*64),('sha256','bad')]:
            bad=copy.deepcopy(profile);bad['native_extension'][key]=value
            with self.assertRaises(launcher.LauncherBuildError):launcher._header(bad,{'operations':[{}]})


if __name__=='__main__':unittest.main()
