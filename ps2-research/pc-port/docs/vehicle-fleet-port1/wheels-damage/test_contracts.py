import json, unittest
from pathlib import Path
D=json.loads(Path(__file__).with_name('contracts.json').read_text())
class Contracts(unittest.TestCase):
 def test_full_playable_fleet(self):
  rows=D['families'];self.assertEqual(len(rows),25);self.assertEqual(len({r['pc_family'] for r in rows}),25)
 def test_no_generic_four_record_assumption(self):
  self.assertEqual({r['pc_family'] for r in D['families'] if r['native_wheel_records']==4},{'KiaSportage','Navara','Tata','Xtrail'})
  self.assertEqual(sum(r['native_wheel_records']==5 for r in D['families']),20)
 def test_exact_partition_whitelist(self):
  self.assertEqual({r['pc_family'] for r in D['families'] if r['source_partition']=='EXACT_EXHAUSTIVE_FACE_MULTISET'},{'megane','Navara','NewRav','Xtrail'})
 def test_no_fake_ufo_wheel(self):
  u=next(r for r in D['families'] if r['pc_family']=='Ufo');self.assertEqual(u['source_partition'],'NO_PAIRED_WHEEL_RESOURCE');self.assertEqual(u['native_wheel_records'],0)
 def test_remaining_geometry_not_claimed_equal(self):
  others=[r for r in D['families'] if r['source_partition']=='SOURCE_GEOMETRY_DIFFERS'];self.assertEqual(len(others),20)
  for r in others:self.assertEqual((r['original_pc_faces'],r['original_ps2_faces'],r['pc_only_faces'],r['ps2_only_faces']),(252,252,252,252))
if __name__=='__main__':unittest.main()
