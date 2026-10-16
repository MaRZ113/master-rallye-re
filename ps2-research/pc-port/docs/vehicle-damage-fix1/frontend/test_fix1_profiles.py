import hashlib, importlib.util, json, struct, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]

class Profiles(unittest.TestCase):
 def setUp(self):
  self.new=json.loads((HERE/'frontend-profiles.json').read_text())
  self.old=json.loads((PORT/'docs/vehicle-crew-port1/fleet/frontend-profiles.json').read_text())
 def test_twenty_existing_assets_unchanged(self):
  profiles={p['ps2_family']:p for p in self.new['profiles']}
  self.assertEqual(len(profiles),24)
  for p in self.old['profiles']:
   self.assertEqual((profiles[p['ps2_family']]['filename'],profiles[p['ps2_family']]['sha256']),(p['filename'],p['sha256']))
 def test_exact_primary_and_secondary_contract(self):
  for family,node in [('KIASPORTAGE',379852),('TATA',349913)]:
   profile=next(p for p in self.new['profiles'] if p['ps2_family']==family)
   source=next(m for m in profile['mesh_secondary_kinds'] if m['primary_default_from_original_loader'])
   self.assertEqual(source['mode'],3);self.assertTrue(source['mixed_reflection'])
   file=PORT/'.assets/vehicles'/profile['filename']
   if not file.exists():continue
   b=file.read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),profile['sha256'])
   size=struct.unpack_from('<I',b,12)[0];meta=json.loads(b[64:64+size])
   mesh=next(m for m in meta['meshes'] if m['node_offset']==node)
   self.assertEqual(mesh['texture_indices'][1],0xffffffff)
   texture=meta['texture_upload'][mesh['texture_indices'][0]]
   self.assertEqual(texture['path'],'\\TNG\\DEFAULT.GXI')
 def test_caralpha_authored_texture_and_exact_mode(self):
  for family,node in [('MATTSERATI',325502),('SIMMBUGGHINI',278266)]:
   profile=next(p for p in self.new['profiles'] if p['ps2_family']==family)
   file=PORT/'.assets/vehicles'/profile['filename']
   if not file.exists():continue
   b=file.read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),profile['sha256'])
   size=struct.unpack_from('<I',b,12)[0];meta=json.loads(b[64:64+size])
   mesh=next(m for m in meta['meshes'] if m['node_offset']==node)
   self.assertEqual((mesh['mode'],mesh['faces']),(2,12))
   self.assertEqual(mesh['textures'][0]['name'].lower(),'commontextures\\mnet1-tga')
 def test_runtime_registry_and_remaining_blocks(self):
  runtime=(PORT/'renderer/frontend_fleet_registry.hpp').read_text()
  for profile in self.new['profiles']:self.assertIn(profile['sha256'],runtime)
  rejected={p['family'] for p in self.new['rejected']}
  self.assertEqual(rejected,{'WOOLDAND','UFO','FORESTER','MOONBUGGY','TANK'})

if __name__=='__main__':unittest.main()
