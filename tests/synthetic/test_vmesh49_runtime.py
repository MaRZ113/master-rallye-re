"""Source-backed trim cleanup, density priorities, rim depth and native brake binding."""
import dataclasses
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from tools import vmesh_materials as vm,vmesh_surface_repair as sr,vmesh_wheels as wh,vmesh_brake_lights as brake,gtmat
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from tests.synthetic.test_vmesh_geometry import DONOR_DIR,HAVE_DONOR,_png
from tests.synthetic.test_vmesh_materials import SPECIAL,RESERVED


@unittest.skipUnless(HAVE_DONOR,'retail donor unavailable')
class CleanupTests(unittest.TestCase):
    def test_clear_black_restoration_is_limited_to_lamp_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'clear.png';p.write_bytes(_png(1,1,lambda x,y:(0,0,0,0)))
            tri=[((x,y,0),(0,0,1),(i,0),uv) for i,((x,y),uv) in enumerate(zip(((0,0),(1,0),(0,1)),((0,0),(1,0),(0,1))))]
            faces=[('lamp','cap',tri),('bumper','decal',tri),('bumper','cap',tri)]
            cl=SimpleNamespace(lamp_objects={'lamp'},_decide=lambda o,m:('black','fixture'))
            donor={n:(DONOR_DIR/n).read_bytes() for n in ('car.dx','complete.dx')}
            plan=vm.MaterialPlan(faces,{'cap':p,'decal':p},cl,1,donor,DONOR_DIR,SPECIAL,RESERVED,
                                 solid_black_swatches=True,solid_black_lamp_caps_only=True)
            self.assertEqual(plan.routes[0][0],'black');self.assertEqual(plan.routes[1][0],'drop')
            self.assertEqual(plan.routes[2][0],'drop')
            self.assertEqual(plan.textures['decal'].alpha,b'\0')

    def test_source_caps_policy_does_not_make_outer_lamp_or_decal_backs(self):
        tri=[((0,0,0),None,(0,0),(0,0)),((1,0,0),None,(1,0),(1,0)),((0,1,0),None,(2,0),(0,1))]
        cl=SimpleNamespace(z_front=0,length=5,lamp_objects={'lamp'},_decide=lambda o,m:('head_lamp','fixture'))
        plan=SimpleNamespace(_cls={0:('head_lamp','cutout')},lamp_glass_uv=None,decal_materials=set())
        _,r=sr.repair((DONOR_DIR/'car.dx').read_bytes(),[('lamp','lens',tri)],cl,plan,lambda p:p,[],source_caps_only=True)
        self.assertEqual(r['backing_source_faces'],[])

    def test_density_weight_allocates_real_atlas_pixels(self):
        a,b=gtmat.Island(('a','cutout')),gtmat.Island(('b','cutout'))
        for i in (a,b):i.bbox=[0,1,0,1];i.area=.1;i.flat=False
        a.density_weight=8
        pool=gtmat.Pool('test',64,64,'cutout');gtmat.pack_pool(pool,[a,b],{'a':(128,128),'b':(128,128)})
        sizes={i.key[0]:w*h for i,x,y,w,h in pool.placements}
        self.assertGreater(sizes['a'],sizes['b']*4)

    def test_compact_rectangles_reuse_space_beside_large_islands(self):
        sizes=[(81,81),(68,20),(57,41),(44,24)]
        self.assertIsNone(gtmat._shelf_pack(sizes,128,128))
        packed=gtmat._maxrect_pack(sizes,128,128);self.assertIsNotNone(packed)
        for i,((x,y),(w,h)) in enumerate(zip(packed,sizes)):
            self.assertTrue(0<=x<=128-w and 0<=y<=128-h)
            for j in range(i):
                xx,yy=packed[j];ww,hh=sizes[j]
                self.assertTrue(x+w<=xx or xx+ww<=x or y+h<=yy or yy+hh<=y)

    def test_stock_derived_rim_depth_preserves_envelope_and_tyre_annulus(self):
        source=(DONOR_DIR/'wheel.dx').read_bytes();flat,_=wh.convert(source,rim_draw=3,rim_ratio=.8)
        out,report=wh.recess_rim(flat,source,rim_draw=3)
        a,b=source_geometry(parse_dx_bytes(flat)),source_geometry(parse_dx_bytes(out))
        self.assertGreater(report['recess_depth_m'],.005);self.assertLess(report['recess_depth_m'],.04)
        for axis in range(3):
            self.assertAlmostEqual(min(v.position[axis] for g in a.values() for v in g.vertices),min(v.position[axis] for g in b.values() for v in g.vertices),places=6)
            self.assertAlmostEqual(max(v.position[axis] for g in a.values() for v in g.vertices),max(v.position[axis] for g in b.values() for v in g.vertices),places=6)
        # A rebuilt draw has new global source IDs; compare actual attributes.
        for d in (1,2):
            self.assertEqual(a[d].triangles,b[d].triangles)
            self.assertEqual([(v.position,v.normal,v.color,v.uvs) for v in a[d].vertices],
                             [(v.position,v.normal,v.color,v.uvs) for v in b[d].vertices])
        self.assertGreater(max(v.position[0] for v in b[3].vertices)-min(v.position[0] for v in b[3].vertices),.005)
        self.assertTrue(report['removed_redundant_cap_triangles'])
        for g in b.values():
            for v in g.vertices:self.assertAlmostEqual(math.sqrt(sum(n*n for n in v.normal)),1,places=5)

    def test_recess_refuses_repeated_or_invalid_application(self):
        source=(DONOR_DIR/'wheel.dx').read_bytes();flat,_=wh.convert(source,rim_draw=3,rim_ratio=.8)
        deep,_=wh.recess_rim(flat,source,rim_draw=3)
        with self.assertRaises(ValueError):wh.recess_rim(deep,source,rim_draw=3)
        with self.assertRaises(ValueError):wh.recess_rim(flat,source,rim_draw=3,depth_scale=float('nan'))

    def test_shoulder_is_rounded_without_changing_tread_or_envelope(self):
        source=(DONOR_DIR/'wheel.dx').read_bytes();flat,_=wh.convert(source,rim_draw=3,rim_ratio=.8)
        deep,_=wh.recess_rim(flat,source,rim_draw=3);out,r=wh.round_tyre_shoulder(deep,rim_draw=3)
        a,b=(parse_dx_bytes(x) for x in (deep,out));ag,bg=source_geometry(a),source_geometry(b)
        self.assertEqual(r['rings'],9);self.assertTrue(r['bead_matches_rim_lip'])
        self.assertGreater(len(bg[r['draw']].triangles),len(ag[r['draw']].triangles))
        for axis in range(3):
            for fn in (min,max):self.assertAlmostEqual(fn(p[axis] for p in a.vertices.positions),fn(p[axis] for p in b.vertices.positions),places=6)
        for d in (1,2,3):
            self.assertEqual(ag[d].triangles,bg[d].triangles)
            self.assertEqual([(v.position,v.normal,v.color,v.uvs) for v in ag[d].vertices],[(v.position,v.normal,v.color,v.uvs) for v in bg[d].vertices])
        for v in bg[r['draw']].vertices:self.assertAlmostEqual(math.sqrt(sum(n*n for n in v.normal)),1,places=5)

    def test_metallic_rim_keeps_rgb_and_dark_opaque_gaps(self):
        source=(DONOR_DIR/'wheel.dx').read_bytes();image=(2,1,bytes((140,120,45,26,9,10,12,0)))
        out,report=wh.metallic_rim_image(source,image,rim_draw=3,reflection=.85)
        self.assertEqual(out[2],bytes((140,120,45,217,9,10,12,0)))
        self.assertEqual(report['native_blend_and_test_flags'],[0,0])
        self.assertEqual(report['native_helper'],'chrome-tga')
        with self.assertRaises(ValueError):wh.metallic_rim_image(source,image,rim_draw=3,reflection=float('nan'))

    def test_native_brake_state_owns_lit_surface_and_halo(self):
        model=parse_dx_bytes((DONOR_DIR/'car.dx').read_bytes());layout=brake.switch_layout(model)
        self.assertEqual(layout['case1'],[28]);self.assertEqual(layout['case2'],[29,30])
        self.assertNotIn(30,layout['case1'])
        data=(DONOR_DIR/'car.dx').read_bytes();faces=[]
        for sign in (-1,1):
            points=[(sign*.5,.5,-2),(sign*.7,.5,-2),(sign*.5,.65,-2)]
            faces.append(('source_tail_lamp_on','Mat2_emit',[(p,(0,0,-1),(i,0),(0,0)) for i,p in enumerate(points)]))
        out,r=brake.bind(data,data,faces,lambda p:p)
        self.assertEqual(r['lit_triangles'],2);self.assertEqual(r['halo_triangles'],28)
        self.assertEqual(brake.switch_layout(parse_dx_bytes(out)),layout)
        before,after=parse_dx_bytes(data),parse_dx_bytes(out)
        for a,b in zip(before.physical_draws,after.physical_draws):
            self.assertEqual((a.tag,a.control_words,a.group_label,a.flags_0x20,a.unknown_0x24),
                             (b.tag,b.control_words,b.group_label,b.flags_0x20,b.unknown_0x24))

    def test_unknown_brake_layout_fails_closed(self):
        m=parse_dx_bytes((DONOR_DIR/'car.dx').read_bytes())
        m.physical_draws[28].control_words=(2,2,8,1,2)
        with self.assertRaises(ValueError):brake.switch_layout(m)


if __name__=='__main__':unittest.main()
