"""Source-free renderer state, compact matrix and comparison regressions."""
from copy import deepcopy
from pathlib import Path
import struct
import tempfile
import unittest
from master_rallye.source_adapters.dakar2_formats import compact_transform
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_scene_preview import stage_source_scene,viewer_command,preview_cull
from tests.synthetic.test_source_scene_preview import scene_fixture


class FidelityTests(unittest.TestCase):
    def test_original_row_vector_rotation_transposes_to_uvs(self):
        m=compact_transform([1,0,0,0,0,-1,0,1,0,2,3,4])
        self.assertEqual(u.transform_point(m,[0,1,0]),[2,3,3])
        self.assertEqual(u.determinant(m),1)

    def test_reflection_is_retained_not_silently_repaired(self):
        m=compact_transform([-1,0,0,0,1,0,0,0,1,0,0,0])
        self.assertEqual(u.determinant(m),-1)
        self.assertEqual(u.transform_point(m,[2,3,4]),[-2,3,4])

    def test_unknown_scale_shear_and_nan_rejected(self):
        for values in ([2,0,0,0,1,0,0,0,1,0,0,0],[1,1,0,0,1,0,0,0,1,0,0,0],[float('nan')]*12):
            with self.assertRaises(ValueError):compact_transform(values)

    def test_source_state_command_is_explicit(self):
        c=viewer_command(Path('viewer.exe'),Path('scene.mrpv'),cull='source')
        self.assertIn('--source-states',c)
        self.assertNotIn('--source-states',viewer_command(Path('v'),Path('s'),cull='none'))
        self.assertEqual(preview_cull({'metadata':{'neutral_preview':{'cull':'source'}}}),'source')

    def test_v2_preserves_original_color_winding_and_source(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);project,s=scene_fixture(root)
            s['meshes'][0]['preview_colors_bgra']=[[11,22,33,44]]*3
            s['materials'][0]['source_render_state']={'schema':'dakar2-render-research/1','cull':'none',
                'depth_write':True,'blend':True,'draw_pass':1,'draw_order':0}
            before=deepcopy(s);out=root/'a.mrpv';stage_source_scene(s,out,scene_root=project)
            data=out.read_bytes();self.assertEqual(struct.unpack_from('<I',data,4)[0],2)
            # One 1x1 texture; then draw string, 48-byte draw header, 12-byte states.
            pos=40;n=struct.unpack_from('<I',data,pos)[0];pos+=4+n+8+4
            n=struct.unpack_from('<I',data,pos)[0];pos+=4+n+48
            self.assertEqual(struct.unpack_from('<III',data,pos),(1,1,1))
            self.assertEqual(data[pos+12+24:pos+12+28],bytes([11,22,33,44]))
            self.assertEqual(s,before)
            other=root/'b.mrpv';stage_source_scene(s,other,scene_root=project)
            self.assertEqual(data,other.read_bytes())

    def test_invalid_colors_and_unqualified_state_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);project,s=scene_fixture(root)
            s['meshes'][0]['preview_colors_bgra']=[[256,0,0,0]]*3
            with self.assertRaisesRegex(ValueError,'colors'):stage_source_scene(s,root/'a.mrpv',scene_root=project)
            del s['meshes'][0]['preview_colors_bgra']
            s['materials'][0]['source_render_state']={'schema':'guessed'}
            with self.assertRaisesRegex(ValueError,'draw state'):stage_source_scene(s,root/'a.mrpv',scene_root=project)


if __name__=='__main__':unittest.main()
