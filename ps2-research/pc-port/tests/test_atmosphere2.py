import hashlib,importlib.util,json,os,struct,gzip,unittest
from pathlib import Path
PORT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gt3_atmo',PORT/'tools/atmosphere_gt3_sky.py');gt=importlib.util.module_from_spec(spec);spec.loader.exec_module(gt)
class SourceContracts(unittest.TestCase):
 def test_course_material_policy_is_exact_and_scoped(self):
  spec=importlib.util.spec_from_file_location('atmo_scene_authoring',PORT/'tools/atmosphere_scene_atlas.py');scene=importlib.util.module_from_spec(spec);spec.loader.exec_module(scene)
  for course,name,category in [('France1','road-tga',1),('Turkey2','sandtrack_lft-tga',1),('Turkey2','basegrass-tga',2),('Turkey2','green shrub-tga',3),('Turkey2','concrete-tga',4),('Turkey3','bedroad-tga',1),('Turkey3','base1-tga',2),('Turkey3','shrub1-tga',3),('Turkey3','hut_01-tga',4)]:
   self.assertEqual(scene.category_for(course,name),category)
  for course,name in [('France1','basegrass-tga'),('Turkey2','base1-tga'),('Turkey3','water-tga'),('Turkey3','boat2-tga'),('Turkey3','tred1-tga'),('Turkey3','plating2-tga'),('Turkey2','basegrass-tga-extra'),('Unknown','road-tga')]:
   self.assertEqual(scene.category_for(course,name),0)
  self.assertEqual(scene.category_for('Turkey3','shrubtrig2-tga'),3)
  self.assertEqual(scene.category_for('France1','shrubtrig2-tga'),0)
 def test_bl1_selector_source_is_unchanged(self):
  b=(PORT/'renderer/atmosphere.hpp').read_bytes();prefix=b[:b.index(b'class Pilot')]
  for line in prefix.splitlines(keepends=True):
   if any(name in line for name in (b'atmosphere_scene.hpp',b'scene_resolver.hpp',b'atmosphere_sun.hpp',b'atmosphere_water.hpp',b'atmosphere_capture.hpp',b'atmosphere_regions.hpp')):prefix=prefix.replace(line,b'')
  # 2.8 changes only the requested preset input; preserve the complete BL1
  # original getter, RET-4 bridge, lifecycle/network guards and choose logic.
  prefix=prefix.replace(b'int requested=parse_preset(text);',b'const int requested=parse_preset(text);')
  prefix=b''.join(line for line in prefix.splitlines(keepends=True) if b'// ATMOSPHERE2.8: selection only;' not in line)
  self.assertEqual(hashlib.sha256(prefix).hexdigest(),'4ff9e49cc354ecbbe14e47769228a74131af76c60cce91f58cf1b2a16e183214')
 @unittest.skipUnless(os.environ.get('MRR_ATMOSPHERE_GT3_COURSES'),'optional private GT3 source')
 def test_real_reverse_sky_bindings_and_vif_shapes(self):
  for name,counts in [('r_deepforest',[20,20,20,20,188]),('r_grandvalley',[84,70,70,70,72,70,70,70,70])]:
   raw=gzip.decompress((Path(os.environ['MRR_ATMOSPHERE_GT3_COURSES'])/(name+'.gz')).read_bytes());a,b=struct.unpack_from('<2I',raw,0x54);model=raw[a:b]
   actual=[0]*len(counts)
   for i,vertices,uv,colors,faces in gt.shapes(model):actual[i]+=len(vertices);self.assertEqual(len(vertices),len(uv))
   self.assertEqual(actual,counts)
   bad=bytearray(model);mt=gt.word(model,32);mo=gt.word(model,mt);bad[mo+100]=0
   with self.assertRaises(ValueError):list(gt.shapes(bad))
 @unittest.skipUnless(os.environ.get('MRR_ATMOSPHERE_GT3_SKY'),'optional generated private sky set')
 def test_projection_alpha_and_wrap_are_preserved(self):
  p=Path(os.environ['MRR_ATMOSPHERE_GT3_SKY']);r=json.loads((p/'provenance.json').read_text())
  self.assertEqual(len(r['courses']),2)
  for course in r['courses']:
   self.assertEqual(course['ray_coverage'],1)
   for resource in course['resources']:
    self.assertEqual(resource['alpha_sha256'],resource['native_alpha_sha256']);self.assertEqual(resource['horizontal_edge_delta_max'],0)
    self.assertEqual(hashlib.sha256((p/'sets'/course['course']/(resource['name']+'.dxt')).read_bytes()).hexdigest(),resource['sha256'])
