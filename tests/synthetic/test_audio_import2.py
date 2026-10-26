"""Generated source tones and minimal banks only; optional codecs tested on Windows."""
import copy,json,math,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tests.synthetic.test_workshop_audio import project
from tests.synthetic.test_gt_sound_lab import fixture as gt_fixture
from tests.synthetic.test_gt4_audio_extract import bank as engn
from master_rallye.workshop.service import WorkshopProject
from master_rallye.workshop.audio_import import decode_media,wav_loop
from master_rallye.addon_sdk.audio_profile import canonical_wav
from master_rallye.addon_sdk.gt_audio_source import GTSourceAdapter
from gt4_audio_extract import pcm_wav

def tone(root):
    path=root/'own.wav';path.write_bytes(canonical_wav([round(5000*math.sin(i*.1)) for i in range(24000)]));return path

class AudioImportTests(unittest.TestCase):
    def test_review_is_separate_and_each_assignment_is_independent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=project(root);source=tone(root);original=source.read_bytes();baseline=p.audio_compile()[0]
            for layer in ('engine','transmission_whine','turbo_spool','bov_release'):
                before=p.audio_state();review=p.audio_prepare_import(source,gain_db=-6,crossfade=40);self.assertEqual(p.audio_state(),before)
                p.audio_apply_import(review,layer);compiled,report=p.audio_compile();changed=[k for k in baseline if baseline[k]!=compiled[k]]
                self.assertEqual(changed,[report['resource_path'] if layer=='engine' else report[layer]['resource_path']]);self.assertEqual(source.read_bytes(),original)
                p.audio_save_preset(layer);q=WorkshopProject(p.root);self.assertIn(layer,q.audio_state()['presets']);q.audio_reset();q.undo();self.assertEqual(q.audio_compile()[0],compiled)
                q.audio_reset();p=q

    def test_review_hashes_foreign_input_and_clipping_reject(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=project(root);q=project(root,'other');review=p.audio_prepare_import(tone(root));state=p.audio_state()
            with self.assertRaisesRegex(ValueError,'another project'):q.audio_apply_import(review,'engine')
            (Path(review['preview_root'])/'converted.wav').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'bytes changed'):p.audio_apply_import(review,'engine')
            self.assertEqual(p.audio_state(),state)
            loud=root/'loud.wav';loud.write_bytes(canonical_wav([30000,-30000]*12000))
            with self.assertRaisesRegex(ValueError,'clips'):p.audio_prepare_import(loud,gain_db=12)

    def test_source_loop_metadata_trim_and_one_shot_does_not_loop(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=project(root);path=root/'loop.wav';path.write_bytes(pcm_wav([500,-500]*6000,24000,(100,10000)))
            self.assertEqual(wav_loop(path.read_bytes(),12000)['frames'],[100,10000])
            review=p.audio_prepare_import(path,use_source_loop=True);self.assertEqual(review['source']['trim_frames'],[100,10000])
            p.audio_apply_import(review,'bov_release');self.assertEqual(p.audio_inspect()['layers']['bov_release']['playback'],'one-shot')

    def test_ordinary_import_without_gt_or_external_decoder(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path=tone(root)
            with patch('master_rallye.workshop.audio_import.shutil.which',return_value=None):self.assertEqual(decode_media(path)[2]['decoder'],'existing SDK RIFF PCM')
            wrong=root/'bad.flac';wrong.write_bytes(b'bad source'*10)
            with patch('master_rallye.workshop.audio_import.shutil.which',return_value=None),self.assertRaisesRegex(ValueError,'ffmpeg'):decode_media(wrong)

    def test_disabled_layer_can_receive_source_without_being_enabled(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=project(root);p.audio_update('bov_release',enabled=False);review=p.audio_prepare_import(tone(root));p.audio_apply_import(review,'bov_release')
            self.assertFalse(p.audio_state()['enabled']['bov_release']);self.assertIsNone(p.audio_inspect()['layers']['bov_release']['compiled'])
            p.audio_update('bov_release',enabled=True);self.assertEqual(p.audio_compile()[1]['bov_release']['sha256'],review['native_sha256'])

    def test_identical_pcm_keeps_distinct_layer_origins_and_presets(self):
        from master_rallye.workshop.audio import sha
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=project(root);path=tone(root)
            base={'adapter_schema':'gt-sound-bank-lab/1','game':'gt4','wav_sha256':sha(path.read_bytes()),'authentic_effect_identity':None,'selected_entry':{'entry_id':'0'}}
            for layer,bank in [('engine','carsound/engine/1'),('turbo_spool','carsound/turbo0/1')]:
                evidence={**base,'bank_id':bank};review=p.audio_prepare_import(path,source_evidence=evidence);p.audio_apply_import(review,layer)
            self.assertEqual(p.audio_inspect()['layers']['engine']['provenance']['gt_source']['bank_id'],'carsound/engine/1')
            self.assertEqual(p.audio_inspect()['layers']['turbo_spool']['provenance']['gt_source']['bank_id'],'carsound/turbo0/1')
            source=copy.deepcopy(p.audio_state()['profile']['engine']);source['gain_db']=-8;p.audio_update('engine',source=source)
            self.assertEqual(p.audio_inspect()['layers']['engine']['provenance']['gt_source']['bank_id'],'carsound/engine/1')
            p.audio_save_preset('origins');p.audio_reset();p.audio_load_preset('origins');self.assertEqual(len(p.audio_state()['imports'][sha(path.read_bytes())]['origins']),2)
            p.audio_assign('bov_release','engine');self.assertEqual(p.audio_inspect()['layers']['bov_release']['provenance']['gt_source']['bank_id'],'carsound/engine/1')
            digest=sha(path.read_bytes());self.assertTrue(p.audio_catalog()[digest]['name'].startswith('Shared PCM'));p.audio_assign('bov_release',digest);self.assertIsNone(p.audio_inspect()['layers']['bov_release']['provenance']['gt_source'])

class GTAdapterTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'gt/source';gt_fixture(source);bank=source/'carsound/turbo3/9876';bank.write_bytes(engn());return source,bank

    def test_live_association_shared_samples_and_private_export(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source,bank=self.fixture(root);a=GTSourceAdapter({'game':'gt4','source':str(source)});v=a.find_vehicle('testmodel');self.assertEqual(v['sound_id'],9876)
            report=a.inspect('carsound/turbo3/9876');entry=report['entries'][0];original=bank.read_bytes();out=root/'private/test.wav'
            evidence=a.export('carsound/turbo3/9876',entry['entry_id'],out,expected_bank_sha256=report['sha256']);self.assertEqual(bank.read_bytes(),original);self.assertIsNone(evidence['authentic_effect_identity']);self.assertIn('decoded bank',evidence['offset_semantics'])
            with self.assertRaisesRegex(ValueError,'outside original'):a.export('carsound/turbo3/9876',entry['entry_id'],source/'bad.wav')
            with self.assertRaises(ValueError):a.inspect('../../bank')
            with self.assertRaises(ValueError):a.find_vehicle('sb0097')

    def test_catalog_drift_and_reviewed_bank_hash_reject(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source,bank=self.fixture(root);a=GTSourceAdapter({'game':'gt4','source':str(source)});catalog=copy.deepcopy(a.catalog);catalog['vehicles'][0]['sound_id']=1;path=root/'catalog.json';path.write_text(json.dumps(catalog))
            other=GTSourceAdapter({'game':'gt4','source':str(source),'catalog':str(path)})
            with self.assertRaisesRegex(ValueError,'association changed'):other.find_vehicle('testmodel')
            report=a.inspect('carsound/turbo3/9876')
            with self.assertRaisesRegex(ValueError,'Bank changed'):a.export('carsound/turbo3/9876','0',root/'out.wav',expected_bank_sha256='0'*64)
            with self.assertRaisesRegex(ValueError,'CORE'):a.export('carsound/turbo3/9876','0',root/'native.wav',rate_mode='native')

    def test_gt3_no_short_code_inference_and_missing_native_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);volume=root/'source.vol';volume.write_bytes(b'fixture');catalog={'schema':'gt-sound-bank-lab/1','game':'gt3','vehicles':[{'vehicle_id':'exact_car','sound_id':2,'banks':[]}],'banks':[],'boundary':'test'};path=root/'catalog.json';path.write_text(json.dumps(catalog));a=GTSourceAdapter({'game':'gt3','source':str(volume),'catalog':str(path)})
            with self.assertRaisesRegex(ValueError,'short mesh'):a.find_vehicle('sb0097')
            with self.assertRaisesRegex(ValueError,'CORE'):a.events()
