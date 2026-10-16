import unittest,json,hashlib,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent;D=json.loads((HERE/'contract.json').read_text());PORT=HERE.parents[2]
class KiaWheel(unittest.TestCase):
 def test_sources(self):
  self.assertEqual(len(D['native_sources']),4)
  for s in D['native_sources']:
   for k in ['geometry_sha256','ordered_position_sha256','native_uv_winding_sha256']:self.assertEqual(len(s[k]),64)
 def test_source_pivot_and_scale(self):
  self.assertEqual(D['ps2_bounds'],D['pc_bounds'])
  for low,high in D['ps2_bounds']:self.assertEqual(low,-high)
 def test_original_faces_and_materials(self):
  self.assertEqual(sum(m['faces'] for m in D['meshes']),252);self.assertEqual(len(D['meshes']),4)
  self.assertTrue(all(m['mode']==3 for m in D['meshes']))
  self.assertTrue(any(m['primary_u_wrap'] and m['u_range'][1]>1 for m in D['meshes']))
  self.assertTrue(any(m['mixed_reflection'] for m in D['meshes']))
  self.assertTrue(any(not m['mixed_reflection'] for m in D['meshes']))
 def test_private_asset(self):
  p=PORT/'.assets/vehicles'/D['filename']
  if not p.exists():self.skipTest('Private original assets not distributed')
  raw=p.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),D['sha256']);self.assertEqual(len(raw),D['bytes'])
  magic,version,meta,meshes,verts,indices,textures,sha=struct.unpack_from('<8s6I32s',raw)
  self.assertEqual((magic,version,meshes,verts,indices),(b'PS2MDL02',2,4,300,756));self.assertEqual(sha.hex(),D['source_sha256'])
 def test_native_fixture_streams(self):
  p=PORT/'.assets/vehicles/kia-wheel-fixtures.bin'
  if not p.exists():self.skipTest('Private fixture not distributed')
  raw=p.read_bytes();meta=json.loads((HERE/'fixture-manifest.json').read_text());self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['sha256']);self.assertEqual(raw[:8],b'PS2KWH01');self.assertEqual(struct.unpack_from('<I',raw,8)[0],4);offset=12
  for s in D['native_sources']:
   fvf,stride,n,t,vbsize,ibsize=struct.unpack_from('<6I',raw,offset);offset+=24;vb=raw[offset:offset+vbsize];offset+=vbsize;ib=raw[offset:offset+ibsize];offset+=ibsize
   self.assertEqual((fvf,stride,n,t),(0x142,24,s['vertices'],s['faces']))
   xyz=b''.join(vb[i*24:i*24+12] for i in range(n));uv=b''.join(vb[i*24+16:i*24+24] for i in range(n))
   self.assertEqual(hashlib.sha256(xyz).hexdigest(),s['ordered_position_sha256']);self.assertEqual(hashlib.sha256(uv+ib).hexdigest(),s['native_uv_winding_sha256'])
  self.assertEqual(offset,len(raw))
if __name__=='__main__':unittest.main()
