"""Original generated tones only. No MR/GT sound fixtures."""
import copy,json,tempfile,unittest
from pathlib import Path
from master_rallye.workshop.service import WorkshopProject
from master_rallye.workshop.audio import LAYERS,sha
from master_rallye.addon_sdk.audio_profile import RESPONSE_BOUNDS,canonical_wav
from tests.synthetic.test_audio_profile import fixture
from tests.synthetic.test_workshop import family

def project(root,name='p',car=28):
    raw,profile=fixture();profile['physical_car_id']=car;profile['namespace']='fixture_'+name
    r=root/name;family(r/'geometry');author=r/'author';author.mkdir()
    (author/'engine.wav').write_bytes(raw)
    for layer,bounds in RESPONSE_BOUNDS.items():
        response={k:(a+b)/2 for k,(a,b) in bounds.items()};response['mute_neutral']=False
        profile[layer]={'source':copy.deepcopy(profile['engine']),'response':response,'provenance':'Generated original test tone'}
    (author/'audio-profile.json').write_text(json.dumps(profile))
    (author/'addon.json').write_text(json.dumps({'addon_id':name,'audio':{'stock_audio_profile_id':7}}))
    (author/'vehicle-project.json').write_text(json.dumps({'vehicle_name':'geometry','source_vehicle_dir':str(r/'geometry'),'resources':{},'texture_edits':{},'texture_replacements':{}}))
    return WorkshopProject.create(author,r/'workshop')

class WorkshopAudioTests(unittest.TestCase):
    def test_visual_version_inherits_named_audio_without_losing_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);parent=project(root);child=project(root,'child',29)
            default=child.audio_compile()[0]
            source=copy.deepcopy(parent.audio_state()['profile']['engine']);source['gain_db']=-8
            parent.audio_update('engine',source=source);parent.audio_save_preset('version preset')
            child.audio_inherit(parent)
            self.assertIn('version preset',child.audio_state()['presets'])
            self.assertEqual(child.audio_state()['profile']['physical_car_id'],29)
            child.audio_reset();self.assertEqual(child.audio_compile()[0],default)

    def test_existing_style_sibling_presets_are_visible_and_explicitly_loaded(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);parent=project(root);child=project(root,'child')
            child.data['identity']=parent.data['identity'];child.save()
            parent.data['style_versions']={'Source Fidelity':str(parent.root),'Classic MR Style':str(child.root)}
            child.data['style_versions']=copy.deepcopy(parent.data['style_versions']);child.save();parent.save()
            parent.audio_save_preset('saved audio');before=child.audio_state()['profile']
            self.assertIn('saved audio (Source Fidelity)',child.audio_available_presets())
            self.assertEqual(child.audio_state()['profile'],before)
            child.audio_load_preset('saved audio (Source Fidelity)')
            self.assertIn('saved audio',child.audio_state()['presets'])
            self.assertEqual(child.audio_state()['profile']['namespace'],'fixture_child')

    def test_continuous_audition_spool_bov_and_muting(self):
        from vehicle_audio_layers import mix_sequence
        with tempfile.TemporaryDirectory() as td:
            p=project(Path(td));state=p.audio_state();response=copy.deepcopy(state['profile']['bov_release']['response'])
            response.update(boost_threshold=.2,release_rate_threshold=1,min_rpm=1500,retrigger_seconds=.5)
            p.audio_update('bov_release',response=response);resources,report=p.audio_compile()
            engine=canonical_wav([0]*96000)
            controls=[{'rpm':4000,'load':1.,'gear':2},{'rpm':4000,'load':0.,'gear':2}]
            raw,mixes=mix_sequence(engine,resources,report,controls,{k:True for k in LAYERS})
            self.assertEqual(sum(len(m['bov_events']) for m in mixes),1)
            silence,none=mix_sequence(engine,resources,report,controls,{k:False for k in LAYERS})
            self.assertFalse(any(silence[44:]));self.assertNotEqual(raw,silence)

    def test_independent_layers_history_presets_reopen_restore(self):
        with tempfile.TemporaryDirectory() as td:
            p=project(Path(td));before,report=p.audio_compile();geometry={f:f.read_bytes() for f in p.assets.iterdir()}
            state=p.audio_state();source=copy.deepcopy(state['profile']['transmission_whine']['source']);source['gain_db']=-8
            p.audio_update('transmission_whine',source=source)
            after,_=p.audio_compile();changes=[k for k in before if before[k]!=after[k]]
            self.assertEqual(changes,[report['transmission_whine']['resource_path']]);p.audio_save_preset('quiet')
            q=WorkshopProject(p.root);self.assertEqual(q.audio_compile()[0],after)
            q.audio_reset('transmission_whine');self.assertEqual(q.audio_compile()[0],before)
            q.undo();self.assertEqual(q.audio_compile()[0],after);q.redo();self.assertEqual(q.audio_compile()[0],before)
            q.audio_load_preset('quiet');self.assertEqual(q.audio_compile()[0],after)
            q.restore();self.assertEqual(q.audio_compile()[0],before)
            self.assertEqual(geometry,{f:f.read_bytes() for f in p.assets.iterdir()})

    def test_import_pin_unchanged_original_and_cross_addon_rebinding(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=project(root);donor=project(root,'donor',29)
            raw=canonical_wav([i%1000 for i in range(12000)])
            wav=root/'own.wav';wav.write_bytes(raw);donor.audio_import('bov_release',wav)
            self.assertEqual(wav.read_bytes(),raw);donor.audio_save_preset('local')
            p.audio_transfer(donor,'local');state=p.audio_state()
            self.assertEqual(state['profile']['physical_car_id'],28);self.assertEqual(state['profile']['namespace'],'fixture_p')
            self.assertEqual(state['profile']['bov_release']['source']['source_sha256'],sha(raw));self.assertTrue(p.audio_compile()[0])
            wav.unlink();self.assertTrue(p.audio_compile()[0]) # pinned project copy survives moved external source
            pin=p.root/'audio-sources'/(sha(raw)+'.wav');pin.unlink()
            with self.assertRaisesRegex(ValueError,'missing'):p.audio_compile()

    def test_invalid_edits_are_atomic_and_schema_bounds_shared(self):
        with tempfile.TemporaryDirectory() as td:
            p=project(Path(td));state=p.audio_state();count=len(p.data['history']);before=p.audio_compile()[0]
            for layer in LAYERS[1:]:
                for key,(low,high) in RESPONSE_BOUNDS[layer].items():
                    response=copy.deepcopy(state['profile'][layer]['response']);response[key]=high+1
                    with self.subTest(layer=layer,key=key),self.assertRaises(ValueError):p.audio_update(layer,response=response)
            with self.assertRaisesRegex(ValueError,'audition-only'):p.audio_update('engine',enabled=False)
            source=copy.deepcopy(state['profile']['engine']);source['source_path']='../bad.wav'
            with self.assertRaises(ValueError):p.audio_update('engine',source=source)
            self.assertEqual(len(p.data['history']),count);self.assertEqual(p.audio_compile()[0],before)

    def test_disable_retains_response_and_source_restore_tuning(self):
        with tempfile.TemporaryDirectory() as td:
            p=project(Path(td));before=p.audio_compile()[0];original=p.audio_state()['profile']
            p.audio_update('turbo_spool',enabled=False);self.assertEqual(len(p.audio_compile()[0]),4)
            self.assertEqual(p.audio_effective()['turbo_spool']['response']['gain'],0)
            self.assertEqual(p.audio_effective()['turbo_spool']['response']['spool_up_seconds'],original['turbo_spool']['response']['spool_up_seconds'])
            self.assertIn('turbo_spool',p.audio_state()['profile']);p.audio_update('turbo_spool',enabled=True)
            self.assertEqual(p.audio_compile()[0],before)
            p.audio_update('engine',stock_profile=3);p.audio_reset('engine')
            self.assertEqual(p.audio_state()['profile'],original)
            self.assertEqual(json.loads((p.working/'addon.json').read_text())['audio']['stock_audio_profile_id'],7)

    def test_hash_clipping_unknown_and_stock_rejection(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);p=project(r);state=p.audio_state()
            raw=canonical_wav([32000 if i%2 else -32000 for i in range(10000)]);wav=r/'clipped.wav';wav.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'clips'):p.audio_import('engine',wav,gain_db=12)
            self.assertEqual(p.audio_state(),state)
            with self.assertRaises(ValueError):p.audio_update('unknown')
            family(r/'plain');q=WorkshopProject.create(r/'plain',r/'plain-project')
            with self.assertRaisesRegex(ValueError,'addon'):q.audio_state()
            baseline=p.root/'audio-baseline.json';baseline.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'baseline changed'):p.audio_reset()
