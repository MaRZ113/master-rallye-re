"""Source-only optional project audio ownership tests."""
import json,tempfile,unittest
from pathlib import Path
from test_audio_profile import fixture
from master_rallye.addon_sdk.project import _audio_artifacts
from master_rallye.addon_sdk.manifest import AddonValidationError

class AudioIntegrationTests(unittest.TestCase):
    def test_preview_whine_is_additive_and_neutral_mutes_it(self):
        from tools.vehicle_audio_preview import add_whine_preview
        from tools.vehicle_whine_audition import synthesize_loop,DEFAULT_RESPONSE
        from master_rallye.addon_sdk.audio_profile import canonical_wav
        engine=canonical_wav([123]*48000);source=synthesize_loop()
        mixed,report=add_whine_preview(engine,source,DEFAULT_RESPONSE,4000,1.,2)
        self.assertNotEqual(mixed,engine);self.assertEqual(report['clipped_samples'],0)
        muted,_=add_whine_preview(engine,source,DEFAULT_RESPONSE,4000,1.,1)
        self.assertEqual(muted,engine)
    def test_preview_uses_current_physics_rev_limit(self):
        from tools.preview_vehicle import audio_rev_limit
        self.assertEqual(audio_rev_limit({'Engine/RevLimit':{'value':'6500.00000'}}),6500)
        self.assertEqual(audio_rev_limit({'Engine/RevLimit':{'value':'6500'}},7000),7000)
        self.assertEqual(audio_rev_limit(),7000)
        with self.assertRaises(ValueError):audio_rev_limit(override=float('nan'))

    def test_optional_sidecar_has_no_effect_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(_audio_artifacts(Path(d),{},27),({},None))

    def test_resolved_carid_and_stock_tuning_are_required(self):
        raw,p=fixture();addon={'audio':{'stock_audio_profile_id':7}}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'engine.wav').write_bytes(raw);(root/'audio-profile.json').write_text(json.dumps(p))
            files,report=_audio_artifacts(root,addon,27)
            self.assertEqual(set(files),{'audio-profile.json','DataAudio/vehicles/sdk/fixture_car/engine.wav'})
            self.assertEqual(report['audio_profile'],p)
            with self.assertRaisesRegex(AddonValidationError,'resolved CarID'):_audio_artifacts(root,addon,28)
            with self.assertRaisesRegex(AddonValidationError,'stock tuning'):_audio_artifacts(root,{'audio':{'stock_audio_profile_id':0}},27)

if __name__=='__main__':unittest.main()
