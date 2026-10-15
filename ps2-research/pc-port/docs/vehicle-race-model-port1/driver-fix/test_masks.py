import hashlib,json,struct,unittest
from pathlib import Path
H=Path(__file__).resolve().parent
class DriverMasks(unittest.TestCase):
 def test_partition(self):
  m=json.loads((H/'driver-masks.json').read_text())
  self.assertEqual(m['private_asset_sha256'],'a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac')
  self.assertEqual(m['ps2_source_sha256'],'af57572e92ce47d810666779fb60c8c178f1979feb203416131a3acc81449326')
  for r,drop,keep in [('0',348,221),('7',48,6)]:
   row=m['roots'][r];self.assertEqual(len(row['excluded_faces']),drop);self.assertEqual(len(row['kept_faces']),keep)
   self.assertFalse(set(row['excluded_faces'])&set(row['kept_faces']))
   self.assertEqual(sorted(row['excluded_faces']+row['kept_faces']),list(range(row['source_face_count'])))
 def test_component_certificate(self):
  m=json.loads((H/'driver-masks.json').read_text());c=json.loads((H/'components.json').read_text())
  for r,row in m['roots'].items():
   chosen=[x for x in c[r]['components']if x['seed_face']in row['component_seeds']]
   self.assertEqual(sorted(i for x in chosen for i in x['faces']),row['excluded_faces'])
   self.assertEqual([x['index_sha256']for x in chosen],row['component_hashes'])
 def test_steering_and_seats_retained(self):
  m=json.loads((H/'driver-masks.json').read_text());c=json.loads((H/'components.json').read_text())
  steer=next(x for x in c['0']['components']if x['seed_face']==25)
  seats=next(x for x in c['7']['components']if x['seed_face']==0)
  self.assertTrue(set(steer['faces'])<=set(m['roots']['0']['kept_faces']))
  self.assertTrue(set(seats['faces'])<=set(m['roots']['7']['kept_faces']))
if __name__=='__main__':unittest.main()
