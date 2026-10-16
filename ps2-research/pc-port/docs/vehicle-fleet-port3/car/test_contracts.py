import json, unittest, struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.p=json.loads((HERE/'contracts.json').read_text())['profiles']
 def test_full_fleet(self):self.assertEqual(len(self.p),25);self.assertEqual(len({p['family'] for p in self.p}),25)
 def test_no_duplicate_healthy_identity(self):self.assertFalse(any(p['duplicate_healthy_sources'] for p in self.p))
 def test_missing_never_silently_static(self):
  for p in self.p:
   self.assertEqual(p['referenced_vertices'],p['mapped_vertices']+p['static_vertices']+len(p['unresolved_vertices']))
   self.assertFalse(p['eligible'] and p['unresolved_vertices'])
 def test_ufo_complete_no_invented_wheels(self):
  p=next(p for p in self.p if p['family']=='Ufo');self.assertTrue(p['eligible']);self.assertEqual(p['static_vertices'],0)
 def test_preserve_separate_proven_paths(self):
  kia=next(p for p in self.p if p['family']=='KiaSportage');self.assertEqual(kia['static_vertices'],956)
  self.assertFalse(next(p for p in self.p if p['family']=='Xtrail')['eligible'])
 def test_never_runtime_grant(self):self.assertFalse(any(p['runtime_grant'] for p in self.p))
 def test_runtime_header_skips_ineligible_arrays(self):
  h=(HERE/'runtime_damage_registry.hpp').read_text()
  for p in self.p:self.assertEqual((' '+p['ps2_family']+'_mapping[]=') in h,p['eligible'])
 def test_forester_revision_is_not_nearest_admitted(self):
  p=next(p for p in self.p if p['family']=='Forester');self.assertEqual(len(p['unresolved_diagnostics']),4)
  self.assertTrue(all(d['nearest_distance_diagnostic_only']>.04 and not d['mapping_authorized'] for d in p['unresolved_diagnostics']))
 def test_static_component_accepts_rigid_source_translation(self):
  from prepare_contracts import component_signature
  raw=[struct.pack('<9f',x,y,z,0,0,1,0,0,0) for x,y,z in [(0,0,0),(1,0,0),(0,1,0)]]
  translated=[struct.pack('<3f',*(v+3 for v in struct.unpack_from('<3f',b)))+b[12:] for b in raw]
  self.assertEqual(component_signature(raw,[(0,1,2)]),component_signature(translated,[(0,1,2)]))
 def test_static_component_rejects_uv_or_deformation(self):
  from prepare_contracts import component_signature
  raw=[struct.pack('<9f',x,y,z,0,0,1,0,0,0) for x,y,z in [(0,0,0),(1,0,0),(0,1,0)]]
  changed=list(raw);changed[1]=struct.pack('<f',1.1)+raw[1][4:]
  self.assertNotEqual(component_signature(raw,[(0,1,2)]),component_signature(changed,[(0,1,2)]))
  changed=list(raw);changed[1]=raw[1][:-4]+struct.pack('<f',.1)
  self.assertNotEqual(component_signature(raw,[(0,1,2)]),component_signature(changed,[(0,1,2)]))
if __name__=='__main__':unittest.main()
