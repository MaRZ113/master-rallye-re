"""Corpus-independent metadata and fail-closed frontend-context checks."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('xtrail_frontend_audit', HERE/'audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class ReadinessTests(unittest.TestCase):
    def test_source_identity_and_coverage(self):
        d = json.loads((HERE/'readiness.json').read_text())
        self.assertEqual(d['ps2']['sha256'], '30f976c4e4e371851e8ebd45dabc1db4ea6c676f9bf99684f70a9a2932096e38')
        self.assertEqual(d['pc']['sha256'], 'ce1694d24a09934cccc3163cfc3561c9308c2cac8d1a65443279c0eb00cda652')
        self.assertEqual(d['ps2']['source_triangles'], 4636)
        self.assertEqual(d['pc']['triangles'], 2487)
        self.assertEqual(len(d['pc']['draws']),24)
        self.assertTrue(all(x['unique_to_complete_resource'] for x in d['pc']['draws']))

    def test_registration_does_not_authorize_suppression(self):
        d = json.loads((HERE/'readiness.json').read_text())
        self.assertFalse(d['candidate_transform']['suppression_authorized'])
        self.assertFalse(d['candidate_transform']['independent_runtime_transform_proved'])
        self.assertTrue(all(r['identity_matches']==0 for r in d['comparison']['0.001']))
        self.assertTrue(all(r['candidate_translation_matches']==0 for r in d['comparison']['0.001']))
        self.assertEqual(d['current_frontend_owner_join'],'UNKNOWN')
        self.assertTrue(all(not r['xtrail_owner_verified'] for r in d['recent_log_inventory']))

    def test_transform_is_position_only_and_explicit(self):
        f = [((1.,2.,3.),(4.,5.,6.),(7.,8.,9.))]
        out = a.shift_faces(f, (0.,0.,-.25))
        self.assertEqual(out[0][0],(1.,2.,2.75))
        self.assertEqual(f[0][0],(1.,2.,3.))

    def test_frontend_context_fail_closed(self):
        row={'type':'race_epoch_snapshot','live_certificate_valid':False,
             'scene':{'read_complete':True,'countdown':0,
                      'requested_name':'FrontendScreens/VehicleSelect',
                      'committed_name':'FrontendScreens/VehicleSelect',
                      'job_source':'DataScene/FrontendScreens/VehicleSelect.xml'}}
        self.assertTrue(a.frontend_observation(row))
        for field,value in [('read_complete',False),('countdown',1),('committed_name','Hud/Hud0')]:
            wrong=copy.deepcopy(row);wrong['scene'][field]=value
            self.assertFalse(a.frontend_observation(wrong))
        wrong=copy.deepcopy(row);wrong['live_certificate_valid']=True
        self.assertFalse(a.frontend_observation(wrong))
        self.assertFalse(a.frontend_observation({}))


if __name__ == '__main__':
    unittest.main()
