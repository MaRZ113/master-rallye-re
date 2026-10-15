"""Compact evidence checks; original models are not required for handoff tests."""
from pathlib import Path
import unittest,json,collections
H=Path(__file__).resolve().parent
class CrewIdentity(unittest.TestCase):
 def setUp(self):self.e=json.loads((H/'pc-crew-components.json').read_text())
 def test_pc17_topology_closes_on_heads_and_helmets(self):
  r=self.e['records']['17'];self.assertEqual([c['face_count'] for c in r['components']],[12,7,12,7,2,2])
  for c,face in zip(r['components'][:4],('16','16','18','18')):
   self.assertGreater(c['exact_shared_vertices'][face],0);self.assertGreater(c['exact_shared_vertices']['19'],0);self.assertEqual(c['exact_shared_vertices']['20'],0)
  self.assertEqual([f['ordinal'] for f in r['faces'] if f['category']=='VERIFIED_PS2_TRIM'],[38,39,40,41])
 def test_exact_categories_require_complete_record(self):
  r=self.e['records']['17'];expect=collections.Counter({f['hash']:f['multiplicity'] for f in r['runtime_hash_categories']});current=collections.Counter(f['hash'] for f in r['faces']);self.assertEqual(expect,current)
  short=current.copy();short.subtract([r['faces'][0]['hash']]);self.assertNotEqual(expect,short)
  duplicate=current.copy();duplicate.update([r['faces'][0]['hash']]);self.assertNotEqual(expect,duplicate)
  foreign=current.copy();foreign.subtract([r['faces'][0]['hash']]);foreign.update(['0'*64]);self.assertNotEqual(expect,foreign)
 def test_side_mapping_and_static_source_coverage(self):
  self.assertLess(self.e['records']['16']['bounds'][1][0],0);self.assertGreater(self.e['records']['18']['bounds'][0][0],0)
  self.assertEqual(self.e['mapping']['16']['component_seed'],123);self.assertEqual(self.e['mapping']['18']['component_seed'],222)
  self.assertEqual(sum(v['faces'] for v in self.e['mapping'].values()),544)
  self.assertEqual(sum(f['category']=='CREW' for r in self.e['records'].values() for f in r['faces']),444)
 def test_current_world_coherence(self):
  o=json.loads((H/'current-frame-observation.json').read_text());self.assertEqual(len(o['records']),6);self.assertEqual({r['source_record'] for r in o['records']},{16,17,18,19,20});self.assertEqual(len({tuple(r['world_bits']) for r in o['records']}),1)
if __name__=='__main__':unittest.main()
