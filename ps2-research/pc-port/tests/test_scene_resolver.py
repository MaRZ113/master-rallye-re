import importlib.util
from pathlib import Path
import hashlib
import struct
import unittest
import os

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('lighting_metadata_authoring',ROOT/'src/master_rallye/course_lighting.py')
sdk=importlib.util.module_from_spec(spec);spec.loader.exec_module(sdk)

class MetadataContracts(unittest.TestCase):
 def test_shader_material_roles_and_exclusions(self):
  for label,category in [('new road',1),('new hillside',2),('light brown gravel',2)]:
   self.assertEqual(sdk.material_role(label,('ground-tga','Null','noise-tga')),(category,sdk.NOISE))
  self.assertEqual(sdk.material_role('new tree',('tree-tga','Null','Null')),(3,sdk.PLAIN|sdk.ALPHA_TEST|sdk.TWO_SIDED))
  self.assertEqual(sdk.material_role('unfamiliar',('x','Null','Null')),(0,sdk.DENY))
  self.assertEqual(sdk.material_role('unfamiliar',('x','Null','Null'),'static'),(4,sdk.PLAIN))
  for label in ['water','glass','glow-on','lamp','shadow']:
   self.assertEqual(sdk.material_role(label,(label,'Null','Null'),'static'),(0,sdk.DENY))
  # Course tyre stacks: vehicle words stay closed by name, an authored 'static' role lifts them.
  self.assertEqual(sdk.material_role('tyre',('tyre','Null','Null')),(0,sdk.DENY))
  self.assertEqual(sdk.material_role('tyre',('tyre','Null','Null'),'static'),(4,sdk.PLAIN))
  # Static course boats (and Turkey3 rails on the boat atlas): Deny unless authored.
  self.assertEqual(sdk.material_role('boat2',('boat2','Null','Null')),(0,sdk.DENY))
  self.assertEqual(sdk.material_role('boat2',('boat2','Null','Null'),'static'),(4,sdk.PLAIN))
  self.assertEqual(sdk.material_role('metal',('base','reflection','Null'),'static'),(0,sdk.DENY))
 def test_metadata_is_material_scoped_without_geometry_records(self):
  row=dict(course='CustomLayout',material='NewRock',texture_sha256='a'*64,category=2,flags=1)
  data=sdk.encode_metadata([row]);self.assertEqual(len(data),313)
  self.assertEqual(struct.unpack_from('<4sII',data),(b'LSM1',1,1))
  self.assertEqual(data[12:76],hashlib.sha256(data[76:]).hexdigest().encode())
  self.assertNotIn(b'geometry',data)
  for bad in ['../France1','A/B','', 'x'*64]:
   with self.assertRaises(ValueError):sdk.encode_metadata([dict(row,course=bad)])
 def test_universal_route_does_not_load_atlas_or_hash_each_draw(self):
  native=(ROOT/'ps2-research/pc-port/renderer/atmosphere_native.hpp').read_text()
  route=native[native.index('inline HRESULT universal_draw'):native.index('inline HRESULT begin')]
  self.assertNotIn('atlas.load',route);self.assertNotIn('sha256_bytes(',route)
  for contract in ['vm->mutex','im->mutex','poisoned','initialized','vertex_revision','index_revision','texture_generation','resolver.entries','same_source','saved.fog_changed']:
   self.assertIn(contract,route)
 def test_body_prototype_is_source_bonnet_only_and_default_off(self):
  body=(ROOT/'ps2-research/pc-port/renderer/atmosphere_body_native.hpp').read_text()
  for contract in ['vertices!=48','count!=55','private_tree','fleet_owner_world','race_descriptors','kTataBonnetGeometrySha','0587119628cdc1f4a5d0903756f9091290f61b697711d83ec49a2ae6a6ecb66c','transformed_normal','v+24']:
   self.assertIn(contract,body)
  self.assertNotIn('kFleetOffLampProfiles',body)
  for forbidden in ['SetTexture(','SetTextureStageState(','SetRenderTarget(','SetTransform(']:self.assertNotIn(forbidden,body)
  pilot=(ROOT/'ps2-research/pc-port/renderer/atmosphere.hpp').read_text();self.assertIn('bool body_tata=false',pilot)
 def test_ps2_replacement_preflight_precedes_deferred_lighting(self):
  renderer=Path(os.environ.get('MRR_PC_PORT_RENDERER_ROOT',ROOT/'ps2-research/pc-port/.staging/ps2-enabled/modernization/renderer'))
  source=(renderer/'src/visual_wrappers.cpp').read_text();start=source.index('HRESULT Device8::draw_indexed_at(');end=source.index('HRESULT Device8::repair_reflection()',start);body=source[start:end]
  late=body.index('if(atmosphere_deferred)')
  for proof in ['waterintegration::draw','rigidintegration::hide_checkpoint_board','xtrailintegration::glass_draw','frontendmodelintegration::draw_race','vehicleintegration::draw','ps2_reflection.pre_draw_status']:
   self.assertLess(body.index(proof),late)
  self.assertLess(late,body.index('real_->DrawIndexedPrimitive('))
  self.assertIn('atmosphere_deferred?S_OK:',body)

if __name__=='__main__':unittest.main()
