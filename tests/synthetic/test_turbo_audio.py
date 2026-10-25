import copy,hashlib,tempfile,unittest
from pathlib import Path
from test_audio_profile import fixture
from master_rallye.addon_sdk.audio_profile import compile_audio,audio_resource_hashes,validate_profile
from master_rallye.addon_sdk.manifest import AddonValidationError
from master_rallye.addon_sdk.audio_response import SpoolState,step
from tools.vehicle_audio_layers import DEFAULT_SPOOL,mix_layers
from tools.vehicle_turbo_source import synthesize_spool,synthesize_bov

BOV={'release_rate_threshold':3.,'boost_threshold':.45,'gain':.45,'pitch_variation':.08,'retrigger_seconds':.5,'release_decay_seconds':.2,'min_rpm':2000}

def profile():
    engine,p=fixture();sources={'engine.wav':engine}
    for name,wav,response in [('turbo_spool',synthesize_spool(),DEFAULT_SPOOL),('bov_release',synthesize_bov(),BOV)]:
        sources[name+'.wav']=wav
        p[name]={'source':{'source_path':name+'.wav','source_sha256':hashlib.sha256(wav).hexdigest(),'trim_frames':[0,(len(wav)-44)//2],'gain_db':0,'remove_dc':False,'crossfade_frames':0},'response':copy.deepcopy(response),'provenance':'authored synthetic test'}
    return p,sources

class TurboAudioTests(unittest.TestCase):
    def test_explicit_neutral_policy_preserves_loaded_release_guards(self):
        sp=copy.deepcopy(DEFAULT_SPOOL);sp['mute_neutral']=False
        bv=copy.deepcopy(BOV);bv['mute_neutral']=False
        s=SpoolState()
        for _ in range(200):self.assertIsNone(step(s,4000,1,1,.01,sp,bv)['bov'])
        self.assertGreater(s.pressure,.9)
        self.assertIsNotNone(step(s,4000,0,1,.01,sp,bv)['bov'])
        for _ in range(100):self.assertIsNone(step(s,4000,0,1,.01,sp,bv)['bov'])
        for rpm,pressure in ((800,1),(4000,0)):
            s=SpoolState(pressure=pressure,previous_load=1)
            self.assertIsNone(step(s,rpm,0,1,.01,sp,bv)['bov'])
        p,_=profile();p['bov_release']['response']['mute_neutral']=False;validate_profile(p)
        p['bov_release']['response']['mute_neutral']=1
        with self.assertRaises(AddonValidationError):validate_profile(p)

    def test_optional_layer_guards_and_resource_ownership(self):
        p,_=profile()
        for layer,key,value in [('turbo_spool','load_threshold',1),('turbo_spool','spool_up_seconds',0),('turbo_spool','mute_neutral',1),('bov_release','release_rate_threshold',0),('bov_release','boost_threshold',float('nan')),('bov_release','gain',2),('bov_release','pitch_variation',.5),('bov_release','retrigger_seconds',0),('bov_release','release_decay_seconds',0),('bov_release','min_rpm',0)]:
            q=copy.deepcopy(p);q[layer]['response'][key]=value
            with self.subTest(layer=layer,key=key),self.assertRaises(AddonValidationError):validate_profile(q)
        for layer in ('turbo_spool','bov_release'):
            q=copy.deepcopy(p);q[layer]['source']['source_path']='../foreign.wav'
            with self.assertRaises(AddonValidationError):validate_profile(q)

    def test_optional_resources_and_legacy_engine_are_independent(self):
        p,inputs=profile()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name,wav in inputs.items():(root/name).write_bytes(wav)
            resources,report=compile_audio(p,root);self.assertEqual(len(resources),3);self.assertEqual(len(audio_resource_hashes(report)),3)
            legacy={k:v for k,v in p.items() if k not in ('turbo_spool','bov_release')}
            old,_=compile_audio(legacy,root)
            for name,wav in old.items():self.assertEqual(resources[name],wav)
            for absent in ('turbo_spool','bov_release'):
                q=copy.deepcopy(p);del q[absent];self.assertEqual(len(compile_audio(q,root)[0]),2)

    def test_release_requires_accumulation_rpm_and_no_spam(self):
        s=SpoolState()
        for _ in range(200):self.assertIsNone(step(s,4000,1.,2,.01,DEFAULT_SPOOL,BOV)['bov'])
        c=step(s,4000,0.,2,.01,DEFAULT_SPOOL,BOV);self.assertIsNotNone(c['bov'])
        for i in range(40):self.assertIsNone(step(s,4000,float(i%2),2,.01,DEFAULT_SPOOL,BOV)['bov'])
        self.assertEqual(s.events,1)
        for rpm,gear,finished in [(800,2,False),(4000,1,False),(4000,2,True)]:
            s=SpoolState(pressure=1,previous_load=1)
            self.assertIsNone(step(s,rpm,0.,gear,.01,DEFAULT_SPOOL,BOV,finished=finished)['bov'])
        s=SpoolState(previous_load=1)
        self.assertIsNone(step(s,4000,0,2,.01,DEFAULT_SPOOL,BOV)['bov'])

    def test_preview_bov_solo_uses_trigger_and_produces_audio(self):
        p,inputs=profile()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name,wav in inputs.items():(root/name).write_bytes(wav)
            resources,report=compile_audio(p,root)
            from master_rallye.addon_sdk.audio_profile import canonical_wav,decode_pcm
            output,diagnostic=mix_layers(canonical_wav([0]*48000),resources,report,4000,1.,2,{'engine':False,'bov_release':True},lift=True)
            self.assertEqual(len(diagnostic['bov_events']),1);self.assertGreater(max(map(abs,decode_pcm(output)[0])),0)
            self.assertEqual(diagnostic['clipped_samples'],0)

    def test_shift_alone_and_slow_release_do_not_trigger_bov(self):
        s=SpoolState(pressure=1,previous_load=1)
        for gear in (2,3,4,3,2):self.assertIsNone(step(s,4000,1,gear,.01,DEFAULT_SPOOL,BOV)['bov'])
        for i in range(100):self.assertIsNone(step(s,4000,1-(i+1)/100,2,.01,DEFAULT_SPOOL,BOV)['bov'])
        self.assertEqual(s.events,0)
