from pathlib import Path
import unittest,json,hashlib,struct,re
HERE=Path(__file__).resolve().parent
class LampTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((HERE/'source-registry.json').read_text());cls.rows=cls.data['families']
 def test_complete_source_coverage(self):
  self.assertEqual(len(self.rows),25);self.assertEqual(len({f['family'] for f in self.rows}),25)
  for f in self.rows:
   self.assertEqual(len(f['on']),1);self.assertEqual(len(f['glow']),1)
   for kind,mode in [('on',1),('glow',14)]:
    p=f[kind][0];self.assertEqual(p['status'],'SOURCE_ADMITTED');self.assertEqual(p['mode'],mode);self.assertEqual(len(p['source_uv_index_topology']),64)
 def test_exact_source_colors_and_ordered_slots(self):
  for f in self.rows:
   on=f['on'][0];glow=f['glow'][0]
   self.assertEqual(on['resources'][0]['slot'],0);self.assertEqual(on['ordered_slots'][0]['slot'],0)
   self.assertEqual(on['resources'][0]['sha256'],'fd4c121f962ef4e9ee7491666c71b65db008d6ca276d9188881c0b35c7846131')
   self.assertEqual(glow['resources'][0]['sha256'],'b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09')
 def test_off_boundaries_and_geometry_differences(self):
  blocked={f['family'] for f in self.rows if f['off_status']!='SOURCE_ADMITTED'}
  self.assertEqual(blocked,{'Bruno','Jump','Mattserati','Ufo'})
  self.assertGreater(next(f for f in self.rows if f['family']=='Jump')['on'][0]['max_source_xyz_difference'],.001)
  self.assertGreater(next(f for f in self.rows if f['family']=='Mattserati')['on'][0]['max_source_xyz_difference'],.001)
 def test_cpp_unique_exact_registry(self):
  header=(HERE/'fleet_on_registry_draft.hpp').read_text();self.assertEqual(header.count(' {"'),25)
  self.assertEqual(len({f['on'][0]['positionUv'] for f in self.rows}),25)
 def test_compact_fixtures_positive_negative(self):
  m=json.loads((HERE/'fixture-manifest.json').read_text());p=HERE.parents[2]/'.assets/vehicles'/Path(m['path']).name
  if not p.exists():self.skipTest('Original corpus fixture intentionally not shipped')
  raw=p.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),m['sha256']);self.assertEqual(raw[:8],b'PS2LMP01')
  profiles={f['on'][0]['positionUv']:f['family'] for f in self.rows};at=12;count=struct.unpack_from('<I',raw,8)[0];positives=0
  for case in m['cases']:
   kind,n,t,stride=struct.unpack_from('<4I',raw,at);at+=16;self.assertEqual(stride,20)
   vb=raw[at:at+n*20];at+=n*20;indices=struct.unpack_from('<%dI'%(t*3),raw,at);at+=t*12
   sha=hashlib.sha256(b''.join(sorted(vb[i*20:(i+1)*20] for i in indices))).hexdigest()
   if kind==1:self.assertEqual(profiles.get(sha),case['family']);positives+=1
   else:self.assertNotIn(sha,profiles)
  self.assertEqual(positives,25);self.assertEqual(count,774);self.assertEqual(at,len(raw))
if __name__=='__main__':unittest.main()
