from pathlib import Path
import json,unittest
HERE=Path(__file__).resolve().parent
class FleetOff(unittest.TestCase):
 def setUp(self):self.rows=json.loads((HERE/'source-registry.json').read_text())['families']
 def test_exact_original_guards(self):
  admitted=[f for f in self.rows if f['status']=='SOURCE_ADMITTED'];self.assertEqual(len(admitted),21)
  for f in admitted:
   p=f['profile'];self.assertLessEqual(p['max_position_error'],.001);self.assertLessEqual(p['max_uv_error'],.000001);self.assertTrue(p['runtime_guard_exact']);self.assertEqual(len(p['geometry']),64);self.assertEqual(len(p['positionUv']),64)
 def test_on_glow_other_not_same_identity(self):
  for f in self.rows:
   if 'profile' not in f:continue
   p=f['profile'];self.assertFalse(any(p['geometry']==n['geometry'] and p['positionUv']==n['positionUv'] for n in f['negative_sources']))
 def test_existing_profiles_retained(self):
  fs={f['family']:f for f in self.rows};self.assertEqual(fs['KiaSportage']['profile']['positionUv'],'559102637af617f9ccbe2c9c6025d5c07189bf580d046a436c7b30317abd2edb');self.assertEqual(fs['Xtrail']['profile']['positionUv'],'49c1ec25031b36c03036b2b796e07fa0d45fc16ac32a59cf9df9cd6934fd9c9f');self.assertEqual(fs['Terrano']['profile']['geometry'],'2afd75bd071f0cb1bee35be8f99f0209511a5332b0e8880bb3b889fa52aaf847')
 def test_precise_exclusions(self):
  blocked={f['family'] for f in self.rows if f['status']!='SOURCE_ADMITTED'};self.assertEqual(blocked,{'Bruno','Jump','Mattserati','Ufo'});self.assertNotIn('Forklift',{f['family'] for f in self.rows});self.assertEqual(next(f for f in self.rows if f['family']=='Forester')['ps2_family'],'WOOLDAND')
 def test_fixture21positive(self):
  f=json.loads((HERE/'fixture-manifest.json').read_text());self.assertEqual(f['positive'],21);self.assertEqual(f['negative'],753);self.assertFalse(f['live_upload'])
if __name__=='__main__':unittest.main()
