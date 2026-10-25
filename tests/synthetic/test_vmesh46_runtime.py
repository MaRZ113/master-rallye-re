"""Coverage, role reflection masks and reusable donor wheel conversion."""
import math
import tempfile
import unittest
from pathlib import Path

from tools import vmesh_geometry as geo, vmesh_materials as vm, vmesh_lod0 as lod, vmesh_wheels as wheels
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from tests.synthetic.test_vmesh_geometry import DONOR_DIR, HAVE_DONOR, _png
from tests.synthetic.test_vmesh_lod0 import write_assets
from tests.synthetic.test_vmesh_materials import SPECIAL, RESERVED


@unittest.skipUnless(HAVE_DONOR, "retail donor unavailable")
class ConversionTests(unittest.TestCase):
    def test_trim_is_solid_and_nonreflective_but_panes_stay_blended(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            obj = write_assets(path)
            gt = geo.parse_gt_full(obj)
            # Reuse an existing non-window face with a trim material and low alpha.
            o,m,t = next(f for f in gt['faces'] if f[1].startswith('Mat1'))
            trim = path/'trim.png'
            trim.write_bytes(_png(8,8,lambda x,y:(35,40,60,65)))
            gt['textures']['Mat6_Trim'] = trim
            gt['faces'].append((o,'Mat6_Trim',t))
            cl = lod.Lod0Classifier(gt['faces'],gt['textures'])
            donor = {n:(DONOR_DIR/n).read_bytes() for n in ('car.dx','complete.dx')}
            plan = vm.MaterialPlan(gt['faces'],gt['textures'],cl,1,donor,DONOR_DIR,SPECIAL,RESERVED,
                                   structural_coverage=True,solid_trim_coverage=True,
                                   role_reflection_scales={'black':0,'interior':0})
            self.assertEqual(set(plan.textures['Mat6_Trim'].alpha),{255})
            self.assertEqual(set(plan.textures['Mat6_Tex37'].alpha),{230})
            spec = plan.routes[len(gt['faces'])-1][1]
            self.assertEqual(spec[1].pass_,'opaque')
            _,pool,island,(x,y,w,h) = spec
            px = plan.pool_images()[pool.name+'.dxt'][2]
            self.assertEqual(px[((y+h//2)*pool.width+x+w//2)*4+3],0)
            result = vm.verify_material_mapping(plan,gt['faces'],plan.pool_images())
            self.assertLess(result['mean_colour_error'],12)

    def test_wheel_remains_centred_and_round_with_preserved_width(self):
        old = (DONOR_DIR/'wheel.dx').read_bytes()
        new, report = wheels.convert(old,rim_draw=3)
        a,b = parse_dx_bytes(old),parse_dx_bytes(new)
        self.assertEqual(min(p[0] for p in a.vertices.positions),min(p[0] for p in b.vertices.positions))
        self.assertEqual(max(p[0] for p in a.vertices.positions),max(p[0] for p in b.vertices.positions))
        for k in (1,2):
            self.assertAlmostEqual(min(p[k] for p in b.vertices.positions),-max(p[k] for p in b.vertices.positions),places=6)
        g = source_geometry(b)[3]
        self.assertEqual(len(g.triangles),36)
        self.assertEqual(report['hub_translation'],[0,0,0])
        for v in g.vertices[1:]:
            self.assertAlmostEqual(math.hypot(*v.position[1:]),report['rim_radius'],places=6)
        with self.assertRaises(ValueError): wheels.convert(old,rim_draw=3,segments=3)

    def test_frontend_uses_same_local_mesh_with_outward_faces(self):
        wheel,_ = wheels.convert((DONOR_DIR/'wheel.dx').read_bytes(),rim_draw=3)
        hubs = [(-1.,.5,1.5),(1.,.5,1.5),(-1.,.5,-1.5),(1.,.5,-1.5)]
        result = wheels.embed((DONOR_DIR/'complete.dx').read_bytes(),wheel,hubs,(20,21,22,23))
        rim = source_geometry(parse_dx_bytes(result))[20]
        n = len(rim.vertices)//4
        self.assertLess(rim.vertices[0].position[0],-1)
        self.assertGreater(rim.vertices[n].position[0],1)
        self.assertEqual(rim.vertices[0].normal[0],-1)
        self.assertEqual(rim.vertices[n].normal[0],1)


if __name__ == '__main__': unittest.main()
