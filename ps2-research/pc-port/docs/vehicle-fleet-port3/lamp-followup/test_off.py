from pathlib import Path
import json,hashlib,struct,unittest,re
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
class OffContracts(unittest.TestCase):
 def test_known_mixed_native_reflection_exception_is_explicit(self):
  def keys(path):return set(re.findall(r'\{"([^"\n]+)","([0-9a-f]{64})"',path.read_text()))
  whole=keys(PORT/'renderer/reflection_pilot.hpp')
  mixed=keys(PORT/'renderer/vehicle_partition_registry.hpp')|keys(PORT/'renderer/lamp_partition_registry.hpp')
  self.assertTrue(whole);self.assertTrue(mixed)
  self.assertEqual(whole&mixed,{('Terrano','7f46a206c472a37c9cb951f0f110f63bb6742ce57466d4adea1ec8896854784e')})
 def setUp(self):self.rows=json.loads((HERE/'contracts.json').read_text())['families']
 def test_exact_bounded_families(self):
  self.assertEqual([r['family'] for r in self.rows],['NewRav','Bruno','Mattserati','Jump','Ufo'])
  for r in self.rows:
   self.assertEqual(r['mode'],3);self.assertEqual(r['material'],'$shader(carshiny)' if r['mixed_reflection'] else '$shader(carbrakelight)');self.assertEqual(r['mixed_reflection'],r['family']!='Ufo')
   for key in ['native_geometry','native_position_uv','native_ordered_xyz','native_ordered_uv_indices','source_pc_sha256','source_ps2_sha256','sha256']:self.assertEqual(len(r[key]),64)
 def test_complete_original_mapping(self):
  for r in self.rows:
   self.assertEqual(len(r['mapping']),r['vertices']);self.assertEqual(len(r['source_vertex_ids']),r['vertices'])
   used=[]
   for first,count in r['mapping']:
    self.assertGreater(count,0);self.assertLessEqual(first+count,len(r['candidates']));used+=list(range(first,first+count))
    self.assertTrue(all(0<=v<r['native_vertices'] for v in r['candidates'][first:first+count]))
   self.assertEqual(used,list(range(len(r['candidates']))))
 def test_revision_is_explicit(self):
  self.assertLess(self.rows[0]['max_xyz_revision'],1e-6)
  self.assertGreater(self.rows[1]['max_uv_revision'],1e-6)
  self.assertGreater(self.rows[2]['max_xyz_revision'],.001)
 def test_no_other_source_record_identity(self):
  old=json.loads((PORT/'docs/vehicle-fleet-kia/fleet-lamps/source-registry.json').read_text())['families']
  keys=[]
  for r in self.rows:
   key=(r['native_geometry'],r['native_position_uv']);keys.append(key)
   f=next(x for x in old if x['family']==r['family'])
   for n in f['negative_sources']:
    if n['record']==r['native_source_record']:continue
    self.assertNotEqual(key,(n['geometry'],n['positionUv']))
  self.assertEqual(len(keys),len(set(keys)))
 def test_pinned_private_assets(self):
  paths=[PORT/'.assets/vehicles'/r['asset'] for r in self.rows]
  if not all(p.exists() for p in paths):self.skipTest('Original private source assets are intentionally excluded from clean source handoff')
  for r,p in zip(self.rows,paths):
   b=p.read_bytes();self.assertEqual(len(b),r['size']);self.assertEqual(hashlib.sha256(b).hexdigest(),r['sha256'])
   magic,version,meta,meshes,vertices,indices,textures,source=struct.unpack_from('<8s6I32s',b)
   self.assertEqual((magic,version,meshes,vertices,indices,textures),(b'PS2MDL02',2,1,r['vertices'],r['indices'],len(r['textures'])))
   self.assertEqual(source.hex(),r['source_ps2_sha256']);at=64+meta;node,mode,t0,t1,t2,start,count=struct.unpack_from('<7I',b,at)
   self.assertEqual((node,mode,start,count),(r['node'],3,0,r['indices']));self.assertLess(t0,textures)
   at+=28+vertices*36;ii=struct.unpack_from('<%dI'%indices,b,at);self.assertEqual(set(ii),set(range(vertices)))
if __name__=='__main__':unittest.main()
