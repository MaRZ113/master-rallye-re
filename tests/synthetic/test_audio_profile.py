"""Generated audio fixtures only; no retail or GT recordings bundled."""
import copy,hashlib,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from master_rallye.addon_sdk.audio_profile import validate_profile,decode_pcm,canonical_wav,compile_audio,engine_resource
from master_rallye.addon_sdk.manifest import AddonValidationError
from tools.vehicle_audio_native import make_wrapper,append_audio

def fixture():
    values=[int(5000*((i%37)-18)/18) for i in range(16000)]
    raw=canonical_wav(values,32000)
    profile={'audio_profile_version':1,'policy':'native_custom_engine','physical_car_id':27,'stock_audio_profile_id':7,'namespace':'fixture_car',
        'engine':{'source_path':'engine.wav','source_sha256':hashlib.sha256(raw).hexdigest(),'trim_frames':[0,16000],'gain_db':0,'remove_dc':True,'crossfade_frames':64},'notes':'generated test audio'}
    return raw,profile

class AudioProfileTests(unittest.TestCase):
    def test_deterministic_canonical_mono_conversion(self):
        raw,p=fixture()
        with tempfile.TemporaryDirectory() as d:
            Path(d,'engine.wav').write_bytes(raw)
            files,a=compile_audio(p,d);again,b=compile_audio(copy.deepcopy(p),d)
            self.assertEqual(files,again);self.assertEqual(a,b)
            self.assertEqual(set(files),{'DataAudio/vehicles/sdk/fixture_car/engine.wav'})
            data=next(iter(files.values()));values,fmt=decode_pcm(data)
            self.assertEqual(fmt,{'sample_rate':48000,'channels':1,'bits_per_sample':16,'frames':23904})
            self.assertEqual(data[:36],canonical_wav(values)[:36]);self.assertFalse(a['runtime_qualified'])

    def test_malformed_profiles_fail_closed(self):
        _,p=fixture()
        changes=[('physical_car_id',7),('physical_car_id',True),('namespace','../rev9'),('stock_audio_profile_id',23),('stock_audio_profile_id',25),('audio_profile_version',True),('policy','fake_layers')]
        for k,v in changes:
            q=copy.deepcopy(p);q[k]=v
            with self.subTest(key=k,value=v),self.assertRaises(AddonValidationError):validate_profile(q)
        for k,v in [('source_path','../engine.wav'),('source_path','C:/engine.wav'),('source_path','a\\engine.wav'),('source_sha256','0'),('trim_frames',[0,True]),('gain_db',float('nan')),('remove_dc',1),('crossfade_frames',3000)]:
            q=copy.deepcopy(p);q['engine'][k]=v
            with self.subTest(key=k,value=v),self.assertRaises(AddonValidationError):validate_profile(q)
        q=copy.deepcopy(p);q['idle_layers']=['invented']
        with self.assertRaises(AddonValidationError):validate_profile(q)

    def test_pin_trim_silence_and_clipping_reject(self):
        raw,p=fixture()
        with tempfile.TemporaryDirectory() as d:
            Path(d,'engine.wav').write_bytes(raw)
            q=copy.deepcopy(p);q['engine']['source_sha256']='0'*64
            with self.assertRaisesRegex(AddonValidationError,'SHA256'):compile_audio(q,d)
            q=copy.deepcopy(p);q['engine']['trim_frames']=[0,17000]
            with self.assertRaisesRegex(AddonValidationError,'trim'):compile_audio(q,d)
            q=copy.deepcopy(p);q['engine']['trim_frames']=[0,2000];q['engine']['crossfade_frames']=0
            with self.assertRaisesRegex(AddonValidationError,'seconds'):compile_audio(q,d)
            silent=canonical_wav([0]*16000,32000);Path(d,'engine.wav').write_bytes(silent)
            q=copy.deepcopy(p);q['engine']['source_sha256']=hashlib.sha256(silent).hexdigest()
            with self.assertRaisesRegex(AddonValidationError,'silent'):compile_audio(q,d)
            loud=canonical_wav([30000,-30000]*8000,32000);Path(d,'engine.wav').write_bytes(loud)
            q['engine']['source_sha256']=hashlib.sha256(loud).hexdigest();q['engine']['gain_db']=12
            with self.assertRaisesRegex(AddonValidationError,'clips'):compile_audio(q,d)

    def test_riff_chunks_and_pcm_format_are_validated(self):
        raw,_=fixture()
        for bad in [b'no',raw[:-1],raw[:20]+struct.pack('<H',3)+raw[22:],raw[:22]+struct.pack('<H',3)+raw[24:]]:
            with self.assertRaises(AddonValidationError):decode_pcm(bad)
        # A metadata-bearing WAV is parsed by chunks and rebuilt to canonical44.
        extra=raw[:12]+b'JUNK'+struct.pack('<I',3)+b'abc\0'+raw[12:]
        extra=extra[:4]+struct.pack('<I',len(extra)-8)+extra[8:]
        self.assertEqual(decode_pcm(raw),decode_pcm(extra))
        dupe=raw+b'data'+struct.pack('<I',0);dupe=dupe[:4]+struct.pack('<I',len(dupe)-8)+dupe[8:]
        with self.assertRaisesRegex(AddonValidationError,'duplicate'):decode_pcm(dupe)

    def test_stereo_unsigned8_downmix(self):
        pcm=bytes([0,255,128,128])*3000
        raw=b'RIFF'+struct.pack('<I',36+len(pcm))+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,2,22050,44100,2,8)+b'data'+struct.pack('<I',len(pcm))+pcm
        values,fmt=decode_pcm(raw)
        self.assertEqual(values[:4],[-128,0,-128,0]);self.assertEqual(fmt['channels'],2)

    def test_resource_namespace_and_wrapper_are_independent(self):
        _,a=fixture();b=copy.deepcopy(a);b['physical_car_id']=28;b['namespace']='second_car'
        body=make_wrapper(0x10000000,[a,b]);self.assertIn(engine_resource(a).encode()+b'\0',body);self.assertIn(engine_resource(b).encode()+b'\0',body)
        self.assertEqual(body[:5],bytes.fromhex('9c60ff7654'))
        self.assertIn(bytes.fromhex('89442428'),body);self.assertIn(bytes.fromhex('619d'),body)
        with self.assertRaisesRegex(ValueError,'duplicate'):append_audio(b'',b'',b'',0x10000000,[a,a],65536)
        with self.assertRaisesRegex(ValueError,'unqualified'):append_audio(b'',b'',b'',0x10000000,[a],65536)
        self.assertEqual(append_audio(b'x',b'y',b'z',0x10000000,[],65536),(b'y',b'z',None))

    def test_link_and_junction_ancestors_reject_before_read(self):
        raw,p=fixture()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'fixture_root';child=root/'audio';child.mkdir(parents=True);(child/'engine.wav').write_bytes(raw)
            p['engine']['source_path']='audio/engine.wav'
            # Mock each OS link classification separately, including an ancestor
            # that would resolve inside the root (containment alone misses this).
            for linked in (root,child,child/'engine.wav'):
                with patch.object(Path,'is_symlink',lambda self:self==linked):
                    with self.assertRaisesRegex(AddonValidationError,'symbolic link or junction'):compile_audio(p,root)
                with patch.object(Path,'is_junction',lambda self:self==linked,create=True):
                    with self.assertRaisesRegex(AddonValidationError,'symbolic link or junction'):compile_audio(p,root)

if __name__=='__main__':unittest.main()
