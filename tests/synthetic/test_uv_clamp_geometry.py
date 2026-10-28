import copy,math,tempfile,unittest
from pathlib import Path
from master_rallye.addon_sdk.uv_clamp_geometry import refine
from master_rallye.addon_sdk.texture_addressing import guarded_clamp

def fixture(mode=1):
    vs=[]
    for p,uv in zip(((0.,0.,0.),(2.,0.,0.),(0.,2.,0.)),((-2.,-.5),(3.,-.5),(-2.,2.5))):
        vs.append(dict(position=p,normal=(0.,0.,1.),uv=uv,rgba_ps2=(100,128,64,128),packet_offset=12))
    return dict(vertices=vs,triangles=[(0,1,2)],texture=dict(width=8,height=4,registers=dict(wrap_s=mode,wrap_t=1,min_u=2,max_u=5)))

def area(a,b,c):return ((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2

class ClampGeometryTests(unittest.TestCase):
    def test_compact_guard_bilinear_texels_match_source_and_keep_density(self):
        reg=dict(wrap_s=2,wrap_t=1,min_u=0,max_u=383)
        w,h=512,128;raw=bytes((i*73+i//13)%256 for i in range(w*h*4))
        uvs=[(0.,0.),(.75,1.),(.4,.7)]
        nw,nh,out,mapped,report=guarded_clamp(w,h,raw,reg,uvs,compact=True)
        self.assertEqual((nw,nh),(512,256));self.assertTrue(report['source_resolution_preserved'])
        oldw,oldh,_,_,_=guarded_clamp(w,h,raw,reg,uvs)
        self.assertEqual((oldw,oldh),(1024,256))
        def sample(data,width,height,u,v,source=False):
            x,y=u*width-.5,v*height-.5;ix,iy=math.floor(x),math.floor(y);fx,fy=x-ix,y-iy
            def pixel(px,py):
                px=min(383,max(0,px))if source else px%width;py=min(127,max(0,py))if source else py%height
                return data[(py*width+px)*4]
            return sum(pixel(ix+dx,iy+dy)*ax*ay for dx,ax in ((0,1-fx),(1,fx))for dy,ay in ((0,1-fy),(1,fy)))
        for u in (0.,.00001,.2,.74999,.75):
            for v in (0.,.001,.3,.999,1.):
                offset=report['guard_offsets'];a=sample(raw,w,h,u,v,True);b=sample(out,nw,nh,(u*w+offset[0])/nw,(v*h+offset[1])/nh)
                self.assertAlmostEqual(a,b,places=8)
        with self.assertRaisesRegex(ValueError,'bounded'):guarded_clamp(w,h,raw,reg,[(-1.,0.)],compact=True)

    def test_surface_winding_and_piecewise_uv_preserved(self):
        for mode in (1,2):
            d=fixture(mode);before=copy.deepcopy(d);r,report=refine(d)
            self.assertEqual(d,before);self.assertGreater(report['derived_triangles'],1)
            total=0
            for tri in r['triangles']:
                vs=[r['vertices'][i]for i in tri];a=area(*(v['position']for v in vs));self.assertGreaterEqual(a,-1e-12);total+=a
                # Each generated triangle samples the same clamped affine field
                # everywhere inside its planar region (not just at vertices).
                for weights in ((1/3,1/3,1/3),(.1,.2,.7),(.8,.15,.05)):
                    p=[sum(w*v['position'][k]for w,v in zip(weights,vs))for k in range(2)]
                    original=(-2+2.5*p[0],-.5+1.5*p[1])
                    uv=[sum(w*v['uv'][k]for w,v in zip(weights,vs))for k in range(2)]
                    ranges=((.25,.75),(0.,1.))if mode==2 else((0.,1.),(0.,1.))
                    for k,(lo,hi)in enumerate(ranges):self.assertAlmostEqual(uv[k],min(hi,max(lo,original[k])),places=11)
                    self.assertEqual(vs[0]['normal'],(0.,0.,1.))
            self.assertAlmostEqual(total,2.);self.assertIs(r['texture'],d['texture'])
            image=bytes(range(128));uvs=[v['uv']for v in r['vertices']]
            w,h,_,_,_=guarded_clamp(8,4,image,d['texture']['registers'],uvs)
            self.assertEqual((w,h),(16,8))

    def test_repeat_axis_is_not_clamped(self):
        d=fixture(0);r,_=refine(d)
        self.assertEqual(min(v['uv'][0]for v in r['vertices']),-2)
        self.assertEqual(max(v['uv'][0]for v in r['vertices']),3)
        d['texture']['registers']['wrap_t']=0
        r,a=refine(d);self.assertIs(r,d);self.assertFalse(a['changed'])

    def test_reject_unknown_ownership_bad_indices_nonfinite_and_budget(self):
        d=fixture();d['_mr_uv_vertices']=[0]
        with self.assertRaisesRegex(ValueError,'ownership'):refine(d)
        d=fixture();d['triangles']=[(0,1,-1)]
        with self.assertRaisesRegex(ValueError,'index'):refine(d)
        d=fixture();d['vertices'][0]['uv']=(math.nan,0)
        with self.assertRaisesRegex(ValueError,'attribute'):refine(d)
        with self.assertRaisesRegex(ValueError,'budget'):refine(fixture(),triangle_budget=1)
        d=fixture(3)
        with self.assertRaisesRegex(ValueError,'region-repeat'):refine(d)

    def test_rgba_linear_interpolation_only_quantized_once(self):
        d=fixture();d['vertices'][0]['rgba_ps2']=(0,0,0,128);d['vertices'][1]['rgba_ps2']=(127,80,15,128);d['vertices'][2]['rgba_ps2']=(33,90,110,128)
        r,_=refine(d)
        for v in r['vertices']:
            x,y,_=v['position']
            for k in range(4):
                expected=d['vertices'][0]['rgba_ps2'][k]*(1-x/2-y/2)+d['vertices'][1]['rgba_ps2'][k]*x/2+d['vertices'][2]['rgba_ps2'][k]*y/2
                self.assertLessEqual(abs(v['rgba_ps2'][k]-expected),.50000001)

if __name__=='__main__':unittest.main()
