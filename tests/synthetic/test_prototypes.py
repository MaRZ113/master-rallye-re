from __future__ import annotations
import importlib.util, struct, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
DX=load('dx_mesh_probe',ROOT/'tools/prototypes/dx_mesh_probe.py')
DXT=load('dxt_decode',ROOT/'tools/prototypes/dxt_decode.py')
class PrototypeTests(unittest.TestCase):
    def test_dxt_header_and_png(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'synthetic.dxt';dst=Path(td)/'synthetic.png'
            pixels=bytes((255,0,0,255, 0,0,255,128))
            src.write_bytes(struct.pack('<5I',0xFEED,1,0x12345678,2,1)+pixels)
            header,payload=DXT.parse_dxt(src);self.assertEqual((header['width'],header['height']),(2,1));self.assertEqual(payload,pixels)
            DXT.write_png(dst,2,1,payload,'bgra');self.assertEqual(dst.read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
    def test_minimal_dx_sections(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'synthetic.dx'
            blob=bytearray(struct.pack('<4I',0xD00D,135,1337,1))
            blob+=struct.pack('<3f',1,2,3)+struct.pack('<3f',0,1,0)+bytes((10,20,30,255))
            blob+=struct.pack('<I2fI3H2I',1,0.25,0.75,3,0,0,0,1,1)
            src.write_bytes(blob);result,_=DX.parse_dx(src)
            self.assertEqual(result['header']['vertex_count'],1);self.assertEqual(result['sections']['indices']['triangle_count'],1)
            self.assertTrue(result['sections']['indices']['all_in_vertex_range']);self.assertAlmostEqual(result['sections']['normals']['length_mean'],1)
if __name__=='__main__':unittest.main()
