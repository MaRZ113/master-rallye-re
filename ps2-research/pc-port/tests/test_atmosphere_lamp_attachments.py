import hashlib,importlib.util,math,struct,tempfile,unittest
from pathlib import Path
PORT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lamp_attachments',PORT/'tools/atmosphere_lamp_attachments.py');sdk=importlib.util.module_from_spec(spec);spec.loader.exec_module(sdk)

class AttachmentAuthoring(unittest.TestCase):
    def test_uv_signature_preserves_expansion_order_and_normalizes_zero(self):
        self.assertEqual(sdk.uv_bytes([(0.,-0.),(.5,1.)]),struct.pack('<4f',0.,0.,.5,1.))
        self.assertNotEqual(sdk.sha(sdk.uv_bytes([(0.,0.),(1.,1.)])),sdk.sha(sdk.uv_bytes([(1.,1.),(0.,0.)])))
        with self.assertRaises(ValueError):sdk.uv_bytes([(math.nan,0.)])

    def test_raw_and_opaque_texture_identities(self):
        self.assertEqual(len(sdk.texture_identities(b'\x01\x02\x03\xff')),1)
        raw=b'\x01\x02\x03\x00';self.assertEqual(set(sdk.texture_identities(raw)),{sdk.sha(raw),sdk.sha(raw[:3]+b'\xff')})
        with self.assertRaises(ValueError):sdk.texture_identities(b'bad')

    def test_switch_visibility_and_glow_exclusion_are_generic(self):
        class Draw:
            def __init__(self,path,texture):self.record_path=path;self.texture_tuple=(texture,)
        self.assertEqual(sdk.switch_role(Draw('9.2','paint-tga'),['9']),'off')
        self.assertEqual(sdk.switch_role(Draw('9','breaklightson-tga'),['9']),'on')
        self.assertIsNone(sdk.switch_role(Draw('9.1','breaklightsonglow-tga'),['9']))
        self.assertEqual(sdk.switch_role(Draw('90','paint-tga'),['9']),'main')

    def test_real_off_and_on_paths_required_without_synthesizing_visibility(self):
        on=dict(record='on',role='on',anchor={'distance':.001})
        with self.assertRaises(ValueError):sdk.select_modes([on])
        main=dict(record='passive',role='main',anchor={'distance':.001})
        selected=sdk.select_modes([on,main]);self.assertEqual(next(c for c in selected if c['record']=='passive')['modes'],['off','on'])

    def test_panel_proximity_is_not_triangle_identity(self):
        lens=[(0.,0.,1.),(1.,0.,1.),(0.,1.,1.)]
        self.assertEqual(sdk.triangle_key(lens),sdk.triangle_key(lens[::-1]))
        self.assertNotEqual(sdk.triangle_key(lens),sdk.triangle_key([(x,y,z+.001) for x,y,z in lens]))

    def test_sidecar_exact_rig_payload_hashes_dedup_and_invalid_anchor(self):
        rig=b'car Synthetic\n';row=('Synthetic',0,'a'*64,'b'*64,3,0,.2,.3,.5,.01,1,.001)
        data=sdk.encode_rows(rig,[row,row]);header,payload=data.split(b'\n',1)
        self.assertEqual(header.split(),[b'LPA1',hashlib.sha256(rig).hexdigest().encode(),hashlib.sha256(payload).hexdigest().encode()])
        self.assertEqual(len(payload.splitlines()),1)
        for bad in [row[:5]+(1,)+row[6:],row[:6]+(.2,.3,.8)+row[9:]]:
            with self.assertRaises(ValueError):sdk.encode_rows(rig,[bad])

    @unittest.skipUnless(Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvarsall.bat').is_file(),'MSVC x86 authoring oracle unavailable')
    def test_current_cpp_oracle_binds_and_tracks_local_damage_rejects_missing_surface(self):
        with tempfile.TemporaryDirectory() as name:
            output=Path(name);exe=sdk.compile_probe(output,Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'))
            positions=[(0.,0.,2.),(1.,0.,2.),(0.,1.,2.)]
            cases=[dict(positions=positions,point=dict(kind=0,position=(.2,.2,z))) for z in (2.03,3.)]
            valid,missing=sdk.run_probe(exe,cases,output/'fixture.txt')
            self.assertIsNone(missing);self.assertEqual(valid['triangle'],0);self.assertAlmostEqual(valid['offset'],.03,places=5)
            self.assertTrue(valid['collapsed_rejected']);self.assertLess(valid['damage_error'],1e-5)

if __name__=='__main__':unittest.main()
