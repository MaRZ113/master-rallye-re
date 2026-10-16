from pathlib import Path
import importlib.util,json,unittest
PORT=Path(__file__).resolve().parents[1]

class XtrailFocusedEvidenceTests(unittest.TestCase):
    def test_actual_prior_partition_runtime_not_screenshot_guess(self):
        d=json.loads((PORT/'docs/xtrail-fidelity/runtime-ab-evidence.json').read_text())
        active=d['sessions']['race_model_1']
        events=[e for e in active['events'] if e['type']=='ps2_vehicle_material_partition']
        self.assertEqual(len(events),1)
        e=events[0];self.assertEqual(e['native_subdraws'],2)
        self.assertEqual([r['triangles'] for r in e['runs']],[195,14])
        self.assertEqual([r['override_applied'] for r in e['runs']],[True,False])
        self.assertFalse(e['state_restore_pending']);self.assertEqual(e['hresult'],0)
        self.assertEqual(d['new_dll_runtime'],'NOT_PERFORMED')

    def test_decal_headlights_and_wheel_source_separation(self):
        d=json.loads((PORT/'docs/xtrail-fidelity/wheel-glass/source-evidence.json').read_text())
        car,wheel=d['models']
        self.assertEqual(car['draws'][13]['categories'],{'VERIFIED_ENVIRONMENT_MATERIAL_CURRENT_IDENTITY_REQUIRED':14})
        self.assertEqual(car['draws'][10]['categories'],{'GLASS_DISTINCT_FROM_BODY_ENVIRONMENT':18})
        self.assertEqual(sum(r['triangles'] for r in wheel['draws']),252)
        self.assertEqual(car['decal_normal_augmentation']['ambiguous_positions'],0)
        self.assertEqual(len(car['decal_normal_augmentation']['entries']),20)

    def test_default_and_no_new_texture(self):
        config=(PORT/'PS2Port.ini.example').read_text()
        self.assertIn('RaceFleet=0',config)
        d=json.loads((PORT/'docs/xtrail-fidelity/runtime-ab-evidence.json').read_text())
        self.assertEqual(len(d['supplied_images']),4)
        self.assertEqual(set(x['grade'] for x in d['supplied_images']),{'USER_RUNTIME_OBSERVATION'})

if __name__=='__main__':unittest.main()
