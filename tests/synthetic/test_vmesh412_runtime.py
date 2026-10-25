"""Focused UI alignment, optional PMB input and wheel-layering regressions."""
import hashlib,math,struct,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import gtmat,gt3_ui_icon as gt,vmesh_wheel_layers as layers
from master_rallye.addon_sdk.ui_assets import fit_rgba,alpha_bounds
from master_rallye.addon_sdk.manifest import AddonValidationError
from master_rallye.vehicle_project import VehicleProject,_compile_texture
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry

class FinalPassTests(unittest.TestCase):
    def test_lower_template_alignment(self):
        px=fit_rgba((51,27,bytes((30,60,90,255))*51*27),128,128,target_bounds=(12,67,102,119))
        x,y,xx,yy=alpha_bounds((128,128,px))
        self.assertGreaterEqual(x,13);self.assertGreaterEqual(y,68)
        self.assertLessEqual(xx,101);self.assertLessEqual(yy,118)
        self.assertGreater(y,64)

    def test_small_thumbnail_default_unchanged(self):
        src=(8,4,bytes((50,60,70,255))*32)
        px=fit_rgba(src,32,16)
        self.assertEqual(alpha_bounds((32,16,px)),(2,1,30,15))
        self.assertEqual(px,fit_rgba(src,32,16,target_bounds=(0,0,32,16)))

    def test_bounds_fail_closed(self):
        for bounds in ((0,0,200,2),(1,1,1,9),(0,-1,10,10)):
            with self.assertRaises(AddonValidationError):fit_rgba((1,1,bytes((0,0,0,255))),128,128,target_bounds=bounds)

    def test_pmb_raw_and_gzip_extraction(self):
        tex=b'Tex1'+bytes(8)+struct.pack('<I',48)+bytes(32)
        for chunk in (tex,zlib.compress(tex,wbits=31)):
            data=struct.pack('<6I',14,16,1,16,len(tex),24)+chunk
            out,report=gt.pmb_texture(data,0);self.assertEqual(out,tex)
            self.assertEqual(report['mapping_policy'],'explicit caller index; no inferred vehicle identity')
            with self.assertRaises(ValueError):gt.pmb_texture(data,1)
            with self.assertRaises(ValueError):gt.pmb_texture(data[:-8],0)

    def test_pmb_unknown_header_and_span(self):
        for b in (bytes(40),struct.pack('<6I',14,16,1,16,48,16)+bytes(48)):
            with self.assertRaises(ValueError):gt.pmb_texture(b,0)

    def test_explicit_background_key_preserves_interior_island(self):
        w=5;pixels=bytearray(bytes((126,126,126,255))*25)
        for y in range(1,4):
            for x in range(1,4):pixels[4*(y*w+x):4*(y*w+x)+4]=bytes((20,50,100,255))
        pixels[48:52]=bytes((126,126,126,255))
        out,report=gt.key_border_background((w,w,bytes(pixels)),(126,126,126))
        self.assertEqual(report['pixels_cleared'],16);self.assertEqual(out[2][51],255);self.assertEqual(out[2][3],0)
        with self.assertRaises(ValueError):gt.key_border_background((w,w,bytes(pixels)),(0,0,0))

    def test_corner_swatch_preserves_face_and_guard(self):
        w=64;src=bytes((110,100,60,217))*w*w
        edited,uv,report=layers.metal_swatch((w,w,src))
        self.assertEqual(uv,(3.5/64,1-3.5/64))
        for y in range(w):
            for x in range(w):
                if math.hypot(2*(x+.5)/w-1,2*(y+.5)/w-1)<=1+2/w:
                    i=4*(y*w+x);self.assertEqual(src[i:i+4],edited[2][i:i+4])
        with self.assertRaises(ValueError):layers.metal_swatch((32,32,bytes((10,10,10,217))*1024))
        with self.assertRaises(ValueError):layers.metal_swatch((64,64,bytes(16384)))

    def test_crc_refresh_opt_in_keeps_other_header_words(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=struct.pack('<5I',0xfeed,1,1234,2,2)+bytes((20,30,40,255))*4
            (root/'rim.dxt').write_bytes(source);(root/'rim.png').write_bytes(gtmat.png_from_rgba(2,2,bytes((60,70,80,217))*4))
            p=VehicleProject(root/'project.json','X',root,{}, {},{})
            spec={'source_sha256':hashlib.sha256(source).hexdigest(),'png':'rim.png'}
            old,_=_compile_texture(p,'rim.dxt',spec);self.assertEqual(old[:20],source[:20])
            fresh,_=_compile_texture(p,'rim.dxt',{**spec,'refresh_crc32':True})
            self.assertEqual(fresh[:8]+fresh[12:20],source[:8]+source[12:20])
            self.assertEqual(struct.unpack_from('<I',fresh,8)[0],zlib.crc32(fresh[20:])&0xffffffff)
            with self.assertRaises(ValueError):_compile_texture(p,'rim.dxt',{**spec,'refresh_crc32':'true'})

    @unittest.skipUnless((ROOT/'.research-output/vehicles/vmesh411/v411-exp-005/runtime/resource-root/DataGx/Vehicles/ImprezaProto/wheel.dx').exists(),'private vehicle fixture unavailable')
    def test_stock_profile_preserves_tyre_and_refuses_second_pass(self):
        target=ROOT/'.research-output/vehicles/vmesh411/v411-exp-005/runtime/resource-root/DataGx/Vehicles/ImprezaProto/wheel.dx'
        ref=ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Pajero/wheel.dx'
        original=target.read_bytes();image=(64,64,bytes((110,100,60,217))*4096)
        data,_,report=layers.layer_rim(original,ref.read_bytes(),image)
        a=source_geometry(parse_dx_bytes(original));b=source_geometry(parse_dx_bytes(data))
        for i in (0,1,2):self.assertEqual(a[i],b[i])
        self.assertAlmostEqual(report['reference']['rings'][-1][0],.80992,places=4)
        self.assertGreater(report['rim_depth_m'],.04)
        for v in b[3].vertices:self.assertAlmostEqual(sum(n*n for n in v.normal),1,places=5)
        with self.assertRaises(ValueError):layers.layer_rim(data,ref.read_bytes(),image)
        narrowed,_,tuned=layers.layer_rim(original,ref.read_bytes(),image,shelf_width_scale=.42,face_uv_scale=.9)
        g=source_geometry(parse_dx_bytes(narrowed))[3];n=tuned['segments']
        self.assertAlmostEqual(tuned['target_rings'][-1][0]/tuned['target_radius_m'],.9201664,places=5)
        self.assertAlmostEqual(max(math.hypot(2*(v.uvs[0][0]-.5),2*(v.uvs[0][1]-.5)) for v in g.vertices[1:n+1]),.9,places=5)
        for args in ({'shelf_width_scale':0},{'face_uv_scale':1.5},{'face_uv_scale':True}):
            with self.assertRaises(ValueError):layers.layer_rim(original,ref.read_bytes(),image,**args)

if __name__=='__main__':unittest.main()
