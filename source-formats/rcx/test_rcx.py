"""Portable synthetic regression tests; optional corpus via RCX_ASTRA_PATH."""
import os,struct,tempfile,unittest
from pathlib import Path
from rcx_extract import unpack,read
from qto_inspect import parse
from tex_decode import decode
ROOT=Path(__file__).resolve().parent
class DecoderTests(unittest.TestCase):
 def test_literals_and_short_backref(self):self.assertEqual(unpack(b'\xe0abcd\x00\x03\xfc',7),b'abcdabc')
 def test_long_and_extended_backrefs(self):
  self.assertEqual(unpack(b'\xe0abcd\x80\x00\x03\xfc',8),b'abcdabcd')
  self.assertEqual(unpack(b'\xe0abcd\xc0\x00\x03\x00\xfc',9),b'abcdabcda')
 def test_terminal_literals(self):self.assertEqual(unpack(b'\xffxyz',3),b'xyz')
 def test_bad_streams(self):
  for data,size in [(b'\0\0\xfc',3),(b'\xe0abc',4),(b'\xfc',1),(b'\xfc\x00',0)]:
   with self.subTest(data=data),self.assertRaises(ValueError):unpack(data,size)
 def test_tex_bgra_and_bounds(self):
  head=struct.pack('<6I',0x0da7adde,1,1,1,21,1);d=decode(head+bytes((3,2,1,4)))
  self.assertEqual(d['mips'][0]['rgba'],bytes((1,2,3,4)))
  with self.assertRaises(ValueError):decode(head+b'\x00')
  with self.assertRaises(ValueError):decode(head+bytes(5))
 def test_dxt_blocks(self):
  # Uniform opaque red RGB565 blocks, independent of source assets.
  dxt1=struct.pack('<HHI',0xf800,0x0000,0)
  h=struct.pack('<6I',0x0da7adde,1,4,4,0x31545844,1)
  self.assertEqual(decode(h+dxt1)['mips'][0]['rgba'],bytes((255,0,0,255))*16)
  dxt3=b'\xff'*8+dxt1;h=struct.pack('<6I',0x0da7adde,1,4,4,0x33545844,1)
  self.assertEqual(decode(h+dxt3)['mips'][0]['rgba'],bytes((255,0,0,255))*16)
  with self.assertRaises(ValueError):decode(h+dxt3[:-1])
 def test_qto_texture_index_flags_and_bounds(self):
  h=struct.pack('<8I',7,2,1,2,3,3,0,0);group=bytearray(57);struct.pack_into('<4I',group,0,9,1,123,0x3086);struct.pack_into('<3I',group,17,0,3,1)
  vert=bytearray(64);struct.pack_into('<3f',vert,28,0,0,1)
  data=h+group+b'a.tex\0b.tex\0'+vert*3+struct.pack('<3H',0,1,2)
  with tempfile.TemporaryDirectory(dir=ROOT) as td:
   p=Path(td)/'sample.qto';p.write_bytes(data);obj=parse(p);self.assertEqual(obj['groups'][0]['texture_index'],1);self.assertEqual(obj['groups'][0]['material_flags_raw'],0x3086);self.assertEqual(obj['textures'][1],'b.tex')
   p.write_bytes(data[:-1])
   with self.assertRaises(ValueError):parse(p)
 def test_optional_source(self):
  if not os.environ.get('RCX_ASTRA_PATH'):self.skipTest('set RCX_ASTRA_PATH to source Astra.rcx')
  b,rows=read(Path(os.environ['RCX_ASTRA_PATH']));r=next(x for x in rows if x['name']=='exterior.tex');out=unpack(b[r['offset']:r['offset']+r['stored']],r['expanded']);self.assertEqual(out[:8],bytes.fromhex('deada70d01000000'))
if __name__=='__main__':unittest.main()
