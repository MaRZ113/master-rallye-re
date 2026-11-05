import hashlib,importlib.util,json,struct,unittest
from pathlib import Path
PORT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('vehicle_lighting_sdk',PORT/'tools/atmosphere_vehicle_lighting.py');sdk=importlib.util.module_from_spec(spec);spec.loader.exec_module(sdk)
class VehicleLightingSDK(unittest.TestCase):
    def test_opaque_contracts_do_not_relabel_glass_or_lamps(self):
        for p,s,part,role in [('body-tga','whitepaint-tga','car',1),('mastersticker243-tga','perspex-tga','car',3),('chair-tga','null','car',7),('driver-tga','null','car',8),('tread-tga','rubber-tga','wheel',9),('rim-tga','chrome-tga','wheel',10)]:
            self.assertEqual(sdk.role_for(p,s,part)[0],role)
        for p,s in [('glass-tga','perspex-tga'),('window-tga','whitepaint-tga'),('breaklightson-tga','chrome-tga'),('headlamp-tga','perspex-tga')]:self.assertEqual(sdk.role_for(p,s,'car')[0],0)
        self.assertEqual(sdk.role_for('body-tga','whitepaint-tga','car',False)[0],0)
    def test_number_panels_and_opaque_glazing_keep_transparent_and_lamp_exclusions(self):
        for name in ['mastersticker203-tga','customsticker-tga']:
            self.assertEqual(sdk.role_for(name,'perspex-tga','car')[0],3)
            self.assertEqual(sdk.role_for(name,'perspex-tga','car',False)[0],0)
        self.assertEqual(sdk.role_for('icewin-tga','glass-tga','car')[0],11)
        for name in ['icewin-tga','window-tga']:
            self.assertEqual(sdk.role_for(name,'glass-tga','car',False)[0],0)
        for name in ['inlights-tga','windscreen32-tga','windshield-tga','lampsticker-tga']:
            self.assertEqual(sdk.role_for(name,'glass-tga','car')[0],0)
    def test_blm3_scopes_resource_and_both_ps2_textures(self):
        rows={('custom','wheel','tread-tga','rubber-tga','a'*64,'b'*64,9),('custom','wheel','tread-tga','chrome-tga','a'*64,'c'*64,10)}
        b=sdk.encode(rows);self.assertEqual(struct.unpack_from('<4sII',b),(b'BLM3',3,2));self.assertEqual(len(b),76+2*390);self.assertEqual(b[12:76],hashlib.sha256(b[76:]).hexdigest().encode())
        with self.assertRaises(ValueError):sdk.encode({('../escape','wheel','tread-tga','rubber-tga','a'*64,'b'*64,9)})
    def test_native_binding_canonicalization_matches_runtime(self):
        for source,expected in [('CommonTextures\\BODY.TGA','body-tga'),('mr-ref-ab123-body-tga.dxt','body-tga'),('Rubber-tga.gxi','rubber-tga')]:self.assertEqual(sdk.canonical(source),expected)
