from pathlib import Path
import hashlib,json,unittest
PORT=Path(__file__).resolve().parents[1]
class LampEvidence(unittest.TestCase):
 def test_complete_lamp_hash_multiset(self):
  d=json.loads((PORT/'docs/xtrail-brake-followup/lamp-partition.json').read_text());mapping=d['face_hash_policy'];self.assertEqual(sum(r['multiplicity'] for r in mapping.values()),58);self.assertEqual(sum(r['multiplicity'] for r in mapping.values() if not r['shiny']),22);self.assertEqual(hashlib.sha256(''.join(h*r['multiplicity'] for h,r in sorted(mapping.items())).encode()).hexdigest(),'7f46a206c472a37c9cb951f0f110f63bb6742ce57466d4adea1ec8896854784e')
 def test_glow_source_uniqueness(self):
  d=json.loads((PORT/'docs/xtrail-brake-followup/glow-source.json').read_text());self.assertEqual(d['negative_search']['files'],78);self.assertEqual(d['negative_search']['hits'],[{'file':'Terrano\\car.dx','record':31}]);self.assertEqual(d['negative_search']['errors'],[]);self.assertEqual((d['vertices'],d['triangles']),(20,20))
 def test_frontend_source_only(self):
  d=json.loads((PORT/'docs/xtrail-fidelity/frontend/readiness.json').read_text());self.assertEqual(len(d['pc']['draws']),24);self.assertTrue(all(r['unique_to_complete_resource'] for r in d['pc']['draws']));self.assertTrue(all(r['runtime_identity_status']=='CURRENT_UPLOAD_MIRROR_DIGEST_REQUIRED' for r in d['pc']['draws']))
if __name__=='__main__':unittest.main()
