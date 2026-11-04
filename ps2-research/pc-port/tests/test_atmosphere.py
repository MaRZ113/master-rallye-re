import hashlib
import os
from pathlib import Path
import struct
import unittest

PORT=Path(__file__).resolve().parents[1]

class AtmosphereContracts(unittest.TestCase):
    def test_registry_has_six_complete_pairs(self):
        import re
        text=(PORT/'renderer/atmosphere_sky_registry.hpp').read_text()
        rows=re.findall(r'\{"([0-9a-f]{64})","([0-9a-f]{64})",(\d),(\d),256,256\}',text)
        self.assertEqual(len(rows),12)
        self.assertEqual({(int(p),int(l)) for _,_,p,l in rows},{(p,l) for p in range(6) for l in range(2)})

    def test_defaults_are_classic(self):
        import configparser
        c=configparser.ConfigParser();c.read(PORT/'Atmosphere.ini');c=c['Atmosphere']
        for key in ('Enabled','WorldLighting','LightProbe','Sun','SunFlare'):self.assertEqual(c[key],'0')
        self.assertEqual(c['SkyPreset'],'Auto');self.assertEqual(c['CustomSet'],'')

    @unittest.skipUnless(os.environ.get('MRR_ATMOSPHERE_EXE'),'NOT_PERFORMED: optional pristine PC executable')
    def test_original_binary_selector_contract(self):
        data=Path(os.environ['MRR_ATMOSPHERE_EXE']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4')
        pe=struct.unpack_from('<I',data,0x3c)[0];sections=struct.unpack_from('<H',data,pe+6)[0]
        opt=struct.unpack_from('<H',data,pe+20)[0];base=struct.unpack_from('<I',data,pe+24+28)[0]
        def read(va,n):
            rva=va-base
            for i in range(sections):
                o=pe+24+opt+i*40;virtual_size,start,size,raw=struct.unpack_from('<4I',data,o+8)
                if start<=rva and rva+n<=start+size:return data[raw+rva-start:raw+rva-start+n]
            raise ValueError(hex(va))
        self.assertEqual(base,0x400000)
        self.assertEqual(read(0x4b123c,5),bytes.fromhex('e81f550200'))
        self.assertEqual(0x4b123c+5+struct.unpack('<i',read(0x4b123d,4))[0],0x4d6760)
        self.assertEqual(read(0x4d6760,4),bytes.fromhex('8b442404')) # getter reads one stack argument
        self.assertEqual(read(0x4d6860,3),bytes.fromhex('c20400'))   # callee removes it
        self.assertEqual(read(0x4b125e,5),bytes.fromhex('e89d6d0200')) # replay-selected write follows hook
        self.assertEqual(read(0x4b1374,5),bytes.fromhex('e8e7530200')) # later layer reads Used natively
        self.assertEqual(read(0x4b13ae,8),bytes.fromhex('4783ff067c0233ff')) # six-preset cycle
        self.assertEqual(read(0x4ad931,5),bytes.fromhex('6844576e00'))
        self.assertEqual(read(0x6e5744,24),b'FrontEnd/Network/Browse\0')
        self.assertEqual(read(0x4ad94b,5),bytes.fromhex('e8d08b0200')) # native bool getter
        self.assertEqual(read(0x48e3aa,5),bytes.fromhex('e881f50100')) # producer reads that source
        self.assertEqual(read(0x48e3b2,13),bytes.fromhex('68f4156b0084c00f849e000000'))
        self.assertEqual(read(0x6b15f4,23),b'Race/NetworkSyncActive\0')
        self.assertEqual(read(0x48e3cc,2),bytes.fromhex('6a01')) # true publication
        self.assertEqual(read(0x48e3d6,5),bytes.fromhex('e8c5960400'))
        self.assertEqual(read(0x48e46a,1),bytes.fromhex('53')) # EBX=0 on false branch
        self.assertEqual(read(0x48e378,2),bytes.fromhex('33db'))
        self.assertEqual(read(0x48e473,5),bytes.fromhex('e828960400'))
        self.assertEqual(read(0x4dd983,6),bytes.fromhex('c70600000000')) # empty slot ID
        self.assertEqual(read(0x4dd9a5,7),bytes.fromhex('c7460400000000')) # null payload
        self.assertEqual(read(0x4dd9b1,7),bytes.fromhex('c746080c000000')) # native unconstructed tag 12
        self.assertEqual(read(0x4d660c,4),bytes.fromhex('8b0a8908')) # assign exact key ID
        self.assertEqual(read(0x4d6610,7),bytes.fromhex('8b480885c9750b')) # bool type check
        self.assertEqual(read(0x4d6622,8),bytes.fromhex('32c083c420c20400')) # native null -> false, RET4

if __name__=='__main__':unittest.main()
