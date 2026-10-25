import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from master_rallye.addon_sdk.external_source import inspect_obj

class SourceTests(unittest.TestCase):
    def fixture(self,root,face):
        p=root/'model.obj';p.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nvt -1 2\nvn 0 0 1\nusemtl Mat4_Tex4\nf '+face+'\n');p.with_suffix('.mtl').write_text('newmtl Mat4_Tex4\nKd 1 1 1 1\n');return p
    def test_material_numbers_are_not_render_classes(self):
        with tempfile.TemporaryDirectory() as d:
            r=inspect_obj(self.fixture(Path(d),'1/1/1 2/1/1 3/1/1'))
            self.assertEqual(r['triangles'],1);self.assertEqual(r['uv_outside_unit_square'],1)
            self.assertIn('UNKNOWN',r['opacity_policy']);self.assertEqual(r['materials']['Mat4_Tex4']['coefficients']['Kd'],[1]*4)
    def test_negative_indices_supported(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(inspect_obj(self.fixture(Path(d),'-3/1/1 -2/1/1 -1/1/1'))['triangles'],1)
    def test_invalid_indices_fail_closed(self):
        for face in ('0 2 3','1 2 4','-4 2 3'):
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):inspect_obj(self.fixture(Path(d),face))
    def test_positive_forward_references_resolve_at_end_of_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.fixture(Path(d),'1/2/1 2/2/1 3/2/1');p.write_text(p.read_text()+'vt .5 .5\n')
            self.assertEqual(inspect_obj(p)['forward_attribute_references'],3)
if __name__=='__main__':unittest.main()
