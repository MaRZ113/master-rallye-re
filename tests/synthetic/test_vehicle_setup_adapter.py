import copy
import json
from pathlib import Path
import struct
import unittest
from master_rallye.addon_sdk.setup_adapter import validate,number,header

ROOT=Path(__file__).resolve().parents[2]
PROFILE=json.loads((ROOT/'research/vehicles/vset1/retail-adapter.json').read_text())


def synthetic_image():
    data=bytearray(0x300000);data[:2]=b'MZ';struct.pack_into('<I',data,60,0x80)
    data[0x80:0x84]=b'PE\0\0';struct.pack_into('<HH',data,0x84,0x14c,1)
    struct.pack_into('<H',data,0x94,224);struct.pack_into('<H',data,0x98,0x10b)
    struct.pack_into('<I',data,0x80+52,0x400000)
    struct.pack_into('<4I',data,0x80+24+224+8,len(data),0,len(data),0)
    for item in PROFILE['apis'].values():
        at=number(item['va'])-0x400000;data[at:at+8]=bytes.fromhex(item['bytes'])
    m=PROFILE['menu']
    for role in ('tick','init'):struct.pack_into('<I',data,number(m['vtable'])-0x400000+m[role+'_offset'],number(m[role]))
    for item in PROFILE['publishers'].values():
        at=number(item['call']);data[at-0x400000:at-0x400000+5]=b'\xe8'+struct.pack('<i',number(item['target'])-at-5)
    return data


class SetupAdapterTests(unittest.TestCase):
    def test_synthetic_profile_and_cpp_share_addresses(self):
        self.assertEqual(validate(synthetic_image(),PROFILE)['tick_slot'],0x690b70)
        h=header(PROFILE);self.assertIn('menu_tick_slot=0x690b70',h);self.assertIn('menu_init_slot=0x690b74',h)

    def test_init_is_not_tick(self):
        wrong=copy.deepcopy(PROFILE);wrong['menu']['tick_offset']=20
        with self.assertRaisesRegex(ValueError,'vtable'):validate(synthetic_image(),wrong)

    def test_each_api_guard_rejects_changed_code(self):
        for name,item in PROFILE['apis'].items():
            data=synthetic_image();data[number(item['va'])-0x400000]^=1
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'preimage'):validate(data,PROFILE)

    def test_each_conflicting_writer_call_rejected(self):
        for item in PROFILE['publishers'].values():
            data=synthetic_image();data[number(item['call'])-0x400000+1]^=1
            with self.assertRaisesRegex(ValueError,'writer call'):validate(data,PROFILE)

    def test_unrelated_file_hash_is_not_an_allowlist(self):
        data=synthetic_image();data[0x5000]=0x91
        self.assertEqual(validate(data,PROFILE)['status'],'PASS_STATIC_ADAPTER')

    def test_actual_original_bytes_when_private_fixture_available(self):
        p=ROOT.parent/'corpora/retail/MRallye.exe'
        if not p.is_file():self.skipTest('Private original executable is not distributed')
        self.assertEqual(validate(p.read_bytes(),PROFILE)['status'],'PASS_STATIC_ADAPTER')


if __name__=='__main__':unittest.main()
