import json,struct,hashlib,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; PORT=HERE.parents[2];D=json.loads((HERE/'manifest.json').read_text())['fleet']
def sha(b):return hashlib.sha256(b).hexdigest()
class FleetWheels(unittest.TestCase):
 def test_complete_inventory(self):
  self.assertEqual(len(D),25);self.assertEqual(sum(x['status'].startswith('SOURCE_READY') for x in D),24)
  u=next(x for x in D if x['family']=='Ufo');self.assertEqual(u['native_sources'],[])
  self.assertEqual({x['native_source_count'] for x in D if 'native_source_count'in x},{4,5})
 def test_pivots_no_fitting(self):
  for x in D:
   if 'filename'in x:self.assertEqual(x['ps2_bounds'],x['pc_bounds']);self.assertIsNone(x['native_wheel_owner_count'])
 def test_all_assets(self):
  for x in D:
   if 'filename'not in x:continue
   p=PORT/'.assets/vehicles'/x['filename']
   if not p.exists():continue
   b=p.read_bytes();self.assertEqual(sha(b),x['sha256']);self.assertEqual(len(b),x['bytes'])
   magic,version,meta,meshes,verts,indices,textures,src=struct.unpack_from('<8s6I32s',b)
   self.assertEqual((magic,version,verts,indices,meshes,textures),(b'PS2MDL02',2,x['vertices'],x['indices'],len(x['meshes']),x['textures']));self.assertEqual(src.hex(),x['source_sha256'])
 def test_native_fixture_original_xyz_uv_winding(self):
  total=0
  for x in D:
   if 'filename'not in x:continue
   m=json.loads((HERE/x['family']/'fixture-manifest.json').read_text());p=PORT/'.assets/vehicles'/m['filename']
   if not p.exists():continue
   b=p.read_bytes();self.assertEqual(sha(b),m['sha256']);self.assertEqual(b[:8],b'PS2KWH01');n=struct.unpack_from('<I',b,8)[0];self.assertEqual(n,x['native_source_count']);o=12
   for s in x['native_sources']:
    f,stride,n,t,nb,ni=struct.unpack_from('<6I',b,o);o+=24;vb=b[o:o+nb];o+=nb;ib=b[o:o+ni];o+=ni
    self.assertEqual((f,stride,n,t),(0x142,24,s['vertices'],s['faces']))
    xyz=b''.join(vb[i*24:i*24+12]for i in range(n));uv=b''.join(vb[i*24+16:i*24+24]for i in range(n));self.assertEqual(sha(xyz),s['ordered_position_sha256']);self.assertEqual(sha(uv+ib),s['native_uv_winding_sha256']);total+=1
   self.assertEqual(o,len(b))
  if total==0:self.skipTest("Private original native fixtures intentionally not shipped; run canonical native tests locally")
  self.assertEqual(total,116)
 def test_materials_are_source_derived(self):
  for x in D:
   for m in x.get('meshes',[]):
    self.assertEqual(m['mode'],3);self.assertEqual(m['mixed_reflection'],m['contract']['effective_secondary'].lower().endswith('rendertarget64x64'))
if __name__=='__main__':unittest.main()
