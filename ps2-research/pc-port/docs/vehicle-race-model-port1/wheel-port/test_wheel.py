"""Focused pinned metadata/resource checks; original bytes remain local only."""
import unittest,json,struct,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
class WheelTests(unittest.TestCase):
 def test_exact_partition(self):
  d=json.loads((HERE/'draw-evidence.json').read_text())
  self.assertEqual([m['faces'] for m in d['meshes']],[72,36,54,90])
  self.assertEqual([m['pc_record'] for m in d['meshes']],[0,1,2,3])
  self.assertEqual([m['path'] for m in d['meshes']],['root.0','root.1','root.0','root.2'])
  self.assertEqual([m['signature'] for m in d['meshes']],[m['signature'] for m in d['pc_records']])
  self.assertEqual(d['faces'],252);self.assertEqual(d['vertices'],300)
 def test_original_materials(self):
  d=json.loads((HERE/'draw-evidence.json').read_text())
  for m in d['meshes']:
   self.assertEqual(m['mode'],3)
   self.assertEqual([s['slot'] for s in m['textures']],[0,1])
   self.assertIn(m['textures'][1]['name'].lower(),['commontextures\\rubber-tga','commontextures\\chrome-tga'])
 def test_local_asset(self):
  for stem,evidence in [('XTRAIL-WHEEL','conversion-evidence.json'),('XTRAIL-WHEEL-DRAW','draw-evidence.json')]:
   path=PORT/'.assets/vehicles'/ (stem+'.ps2model')
   if not path.exists():self.skipTest('Private original asset intentionally not distributed')
   raw=path.read_bytes();d=json.loads((HERE/evidence).read_text())
   self.assertEqual(hashlib.sha256(raw).hexdigest(),d['asset_sha256']);self.assertEqual(len(raw),d['bytes'])
   magic,version,meta,meshes,verts,indices,textures,sha=struct.unpack_from('<8s6I32s',raw)
   self.assertEqual((magic,version,verts,indices),(b'PS2MDL02',2,300,756));self.assertEqual(sha.hex(),d['source_sha256'])
   self.assertEqual(meshes,d['mesh_count']);self.assertEqual(textures,d['texture_count'])
if __name__=='__main__':unittest.main()
