"""Generated whine fixtures; native replay is an explicitly local diagnostic."""
import copy,hashlib,math,tempfile,unittest
from pathlib import Path
from master_rallye.addon_sdk.audio_profile import compile_audio,validate_profile,whine_resource,audio_resource_hashes
from master_rallye.addon_sdk.manifest import AddonValidationError
from tools.vehicle_whine_native import append_whine,make_payload,response_values
from tools.vehicle_whine_audition import DEFAULT_RESPONSE,synthesize_loop,audition_whine
from tests.synthetic.test_audio_profile import fixture


def whine_fixture():
    raw,p=fixture();whine=synthesize_loop()
    p['transmission_whine']={'source':{'source_path':'whine.wav','source_sha256':hashlib.sha256(whine).hexdigest(),'trim_frames':[0,48000],'gain_db':0,'remove_dc':False,'crossfade_frames':0},'response':copy.deepcopy(DEFAULT_RESPONSE),'provenance':'Generated synthetic fixture, not game audio.'}
    return raw,whine,p


class WhineTests(unittest.TestCase):
    def test_additive_resource_keeps_exact_engine_pcm(self):
        engine,whine,p=whine_fixture();legacy=copy.deepcopy(p);del legacy['transmission_whine']
        with tempfile.TemporaryDirectory() as d:
            Path(d,'engine.wav').write_bytes(engine);Path(d,'whine.wav').write_bytes(whine)
            original,old_report=compile_audio(legacy,d);combined,report=compile_audio(p,d)
            for path,raw in original.items():self.assertEqual(combined[path],raw)
            self.assertEqual(report['engine_sha256'],old_report['engine_sha256'])
            self.assertEqual(len(combined),2);self.assertEqual(combined['DataAudio/'+whine_resource(p)+'.wav'],whine)
            self.assertFalse(report['transmission_whine']['runtime_qualified'])
            self.assertEqual(audio_resource_hashes(report),{k:hashlib.sha256(v).hexdigest() for k,v in combined.items()})
            bad=copy.deepcopy(report);bad['transmission_whine']['resource_path']='DataAudio/vehicles/rev9.wav'
            with self.assertRaises(AddonValidationError):audio_resource_hashes(bad)
            bad=copy.deepcopy(report);bad['resource_path']='DataAudio/vehicles/rev9.wav'
            with self.assertRaises(AddonValidationError):audio_resource_hashes(bad)
            bad=copy.deepcopy(old_report);bad['transmission_whine']=report['transmission_whine']
            with self.assertRaises(AddonValidationError):audio_resource_hashes(bad)

    def test_whine_guards_are_strict_and_legacy_optional(self):
        _,_,p=whine_fixture()
        for key,value in [('reference_rpm',float('nan')),('pitch_max',4),('gain_drive',2),('fade_in_rpm',0),('mute_neutral',1)]:
            q=copy.deepcopy(p);q['transmission_whine']['response'][key]=value
            with self.subTest(key=key),self.assertRaises(AddonValidationError):validate_profile(q)
        for key,value in [('source_path','../engine.wav'),('source_sha256','a'),('trim_frames',[0,True])]:
            q=copy.deepcopy(p);q['transmission_whine']['source'][key]=value
            with self.subTest(key=key),self.assertRaises(AddonValidationError):validate_profile(q)
        self.assertEqual(append_whine(b'x',b'y',b'z',0x10000000,[],65536),(b'y',b'z',None))
        q=copy.deepcopy(p);del q['transmission_whine'];self.assertEqual(append_whine(b'x',b'y',b'z',0x10000000,[q],65536),(b'y',b'z',None))
        with self.assertRaisesRegex(ValueError,'unqualified'):append_whine(b'x',b'y',b'z',0x10000000,[p],65536)
        with self.assertRaisesRegex(ValueError,'duplicate'):append_whine(b'x',b'y',b'z',0x10000000,[p,p],65536)

    def test_controls_speed_signed_load_neutral_and_finish(self):
        r=DEFAULT_RESPONSE
        self.assertEqual(response_values(r,0,500,500,2)['gain'],0)
        self.assertAlmostEqual(response_values(r,4000,500,500,2)['gain'],r['gain_drive'])
        self.assertAlmostEqual(response_values(r,4000,-500,500,2)['gain'],r['gain_coast'])
        self.assertEqual(response_values(r,4000,500,500,1)['gain'],0)
        self.assertEqual(response_values(r,4000,500,500,2,finished=True)['gain'],0)
        self.assertEqual(response_values(r,30000,500,500,2)['pitch'],r['pitch_max'])
        self.assertEqual(response_values(r,float('nan'),500,500,2)['gain'],0)

    def test_deterministic_private_source_and_preview(self):
        a=synthesize_loop();self.assertEqual(a,synthesize_loop())
        wav,report=audition_whine(a,DEFAULT_RESPONSE,[1000,4000,6000],[1,0,-1],[2,2,2],.02)
        self.assertEqual(len(wav),44+3*960*2);self.assertGreater(report['segments'][1]['rms_pcm16'],0)
        muted,_=audition_whine(a,DEFAULT_RESPONSE,[4000],[1],[1],.02)
        self.assertEqual(set(muted[44:]),{0})
        _,_,p=whine_fixture();blob,entries=make_payload(0x10000000,[p]);self.assertEqual(set(entries),{'construct','publish','update','destroy','map','cursor','voices'})
        self.assertIn(b'vehicles/sdk/fixture_car/transmission_whine\0',blob)
        self.assertEqual(entries['cursor'] % 4096,0)
        self.assertEqual(entries['map'],entries['cursor']+4)
        self.assertEqual(len(blob),entries['cursor']-0x10000000+4096)
        self.assertEqual(blob[-4096:],b'\0'*4096)
        # Prefix offset must not defeat absolute page alignment.
        shifted,shifted_entries=make_payload(0x10012340,[p])
        self.assertEqual(shifted_entries['cursor'] % 4096,0)
        self.assertEqual(0x10012340+len(shifted),shifted_entries['cursor']+4096)


if __name__=='__main__':unittest.main()
