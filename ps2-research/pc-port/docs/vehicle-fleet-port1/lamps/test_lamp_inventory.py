import unittest,json,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
class LampInventory(unittest.TestCase):
 def setUp(self):
  self.r=json.loads((HERE/'missing-source-comparison.json').read_text())
 def test_five_unique_exact_native_sources(self):
  expected={'FRONTERA':32,'JUMP':28,'MATTSERATI':24,'RMONSTER':24,'TATA':32}
  for f in self.r['families']:
   g=next(m for m in f['meshes'] if m['mode']==14)
   cs=[c for c in g['pc_candidates'] if c['exact_uv_triangle_multiset'] and c['ordered_texture_slots'] in (['breaklightsonglow-tga','Null','Null'],['breaklightsonglow-tga','perspex-tga','Null'])]
   self.assertEqual(len(cs),1);self.assertEqual(cs[0]['record'],expected[f['family']]);self.assertEqual(cs[0]['max_uv_error'],0)
   self.assertGreater(cs[0]['max_position_error'],.001)
 def test_no_on_surface_admitted(self):
  for f in self.r['families']:
   on=next(m for m in f['meshes'] if m['mode']==1)
   glow=next(m for m in f['meshes'] if m['mode']==14)
   g=next(c for c in glow['pc_candidates'] if c['exact_uv_triangle_multiset'])
   self.assertNotIn(g['position_uv_corner_sha256'],[c['position_uv_corner_sha256'] for c in on['pc_candidates']])
 def test_legacy20_byte_identical(self):
  s=importlib.util.spec_from_file_location('old',PORT/'docs/vehicle-crew-port1/lamps/generate_runtime_registry.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  old=m.generate();new=(HERE/'brake_glow_registry_draft.hpp').read_text()
  oldrows=[x for x in old.splitlines() if x.startswith(' {"')]
  newrows=[x for x in new.splitlines() if x.startswith(' {"')]
  self.assertEqual(newrows[:20],oldrows);self.assertEqual(len(newrows),25)
 def test_explicit_native_geometry_limitation(self):
  d=json.loads((HERE/'admission-decisions.json').read_text())
  self.assertFalse(d['new_ps2_geometry_replacement']);self.assertEqual(len(d['added_profiles']),5)
  for r in d['added_profiles']:
   self.assertTrue(r['original_pc_geometry_retained']);self.assertEqual(r['runtime_validation'],'PENDING_USER_BRAKE_OFF_ON')
if __name__=='__main__':unittest.main()
