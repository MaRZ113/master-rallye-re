import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from test_visual_fitment import fixture
from master_rallye.addon_sdk.project import _apply_visual_fitment
from master_rallye.addon_sdk.manifest import AddonValidationError


class VisualFitmentIntegrationTests(unittest.TestCase):
    def test_absent_profile_has_no_side_effect(self):
        with tempfile.TemporaryDirectory() as td:
            raw,_=fixture();out,report=_apply_visual_fitment(Path(td),{'car.dx':raw})
            self.assertEqual(out,{'car.dx':raw});self.assertIsNone(report)

    def test_role_scoping_preserves_menu_and_output_hash(self):
        raw,definition=fixture()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p={'profile_version':1,'roles':{'car.dx':definition},'provenance':'synthetic separate visual path'}
            (root/'visual-fitment.json').write_text(json.dumps(p))
            out,report=_apply_visual_fitment(root,{'car.dx':raw,'complete.dx':raw})
            self.assertNotEqual(out['car.dx'],raw);self.assertEqual(out['complete.dx'],raw)
            self.assertEqual(report['roles']['car.dx']['output_sha256'],hashlib.sha256(out['car.dx']).hexdigest())
            p['roles']['wheel.dx']=copy.deepcopy(definition);(root/'visual-fitment.json').write_text(json.dumps(p))
            with self.assertRaises(AddonValidationError):_apply_visual_fitment(root,{'car.dx':raw})

    def test_unbound_or_reapplied_source_fails_closed(self):
        raw,definition=fixture()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'visual-fitment.json').write_text(json.dumps({'profile_version':1,'roles':{'car.dx':definition},'provenance':'synthetic'}))
            out,_=_apply_visual_fitment(root,{'car.dx':raw})
            with self.assertRaises(AddonValidationError):_apply_visual_fitment(root,out)
    def test_case_aliases_cannot_register_two_mechanical_families(self):
        from tools.vehicle_mechanics_native import append_mechanics
        def profile(name):return {'runtime_family':name,'resource_keys':['vehicles/'+name+'/mechanics'+str(i) for i in range(4)]}
        with self.assertRaisesRegex(ValueError,'duplicate'):
            append_mechanics(b'',b'',b'',0x10000000,[profile('Fixture'),profile('fixture')],65536)


if __name__=='__main__':unittest.main()
