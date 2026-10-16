import json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Coverage(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=json.loads((HERE/'coverage.json').read_text())['vehicles']
 def test_playable_all25(self):self.assertEqual(len(self.rows),25);self.assertEqual(len({r['family'] for r in self.rows}),25);self.assertFalse(any(r['family'].lower()=='forklift' for r in self.rows))
 def test_ufo_never_wheels(self):
  u=next(r for r in self.rows if r['family']=='Ufo');self.assertFalse(u['wheels']['implemented']);self.assertEqual(u['wheels']['policy'],'NO_WHEELS_BY_DESIGN')
 def test_damage_is_not_generic_tag_enable(self):
  self.assertEqual({r['family'] for r in self.rows if r['CAR']['damaged_implemented']},{'Xtrail','KiaSportage','Ufo'});self.assertTrue(all(r['CAR']['damage_unresolved_vertices']>0 for r in self.rows if not r['CAR']['damaged_implemented']))
 def test_verified_lamp_boundaries(self):
  self.assertEqual(sum(r['lamps']['OFF']['implemented'] for r in self.rows),21);self.assertTrue(all(r['lamps']['ON_CORE']['implemented'] and r['lamps']['ADDITIVE_GLOW']['implemented'] for r in self.rows))
 def test_runtime_and_source_are_distinct(self):
  self.assertEqual({r['family'] for r in self.rows if r['CAR']['healthy_runtime']=='USER_RUNTIME_CONFIRMED'},{'Xtrail','KiaSportage'});self.assertEqual(next(r for r in self.rows if r['family']=='Forester')['ps2_family'],'WOOLDAND')
if __name__=='__main__':unittest.main()
