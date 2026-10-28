import math,unittest
import numpy as np
from master_rallye.gt_auto_profile import detect_arches,_circle
from master_rallye.gt3_vehicle import _roof
from master_rallye.scene_dx_writer import ScenePart
from master_rallye.topology_writer import CompiledVertex,DrawGeometry


def side_panel(x,arches,length=4.,height=1.,step=.05,radius=.36):
    """Outer side skin at |x| with semicircular arch openings (MR frame)."""
    tris=[];sign=1 if x>0 else -1
    zs=np.arange(-length/2,length/2,step)
    for z in zs:
        for y in np.arange(0.,height,step):
            c=(z+step/2,y+step/2)
            if any(math.hypot(c[0]-az,c[1]-ay)<radius for az,ay in arches):continue
            a,b,cc,d=(x,y,z),(x,y,z+step),(x,y+step,z+step),(x,y+step,z)
            # Outward winding (normal sign follows x).
            tris+= [(a,b,cc),(a,cc,d)] if sign<0 else [(a,cc,b),(a,d,cc)]
    return tris


class AutoProfileTests(unittest.TestCase):
    def test_circle_fit(self):
        pts=[(1+.4*math.cos(t),.3+.4*math.sin(t))for t in np.linspace(.3,2.8,20)]
        cz,cy,r=_circle(pts);self.assertAlmostEqual(cz,1,3);self.assertAlmostEqual(cy,.3,3);self.assertAlmostEqual(r,.4,3)

    def test_detects_both_arches_and_wheelbase(self):
        arches=[(1.25,.3),(-1.3,.3)]
        tris=np.asarray(side_panel(.9,arches)+side_panel(-.9,arches),float)
        a=detect_arches(tris)
        self.assertAlmostEqual(a['wheelbase'],2.55,delta=.05)
        self.assertAlmostEqual(a['front']['centre_z'],1.25,delta=.04);self.assertAlmostEqual(a['rear']['centre_z'],-1.3,delta=.04)
        self.assertAlmostEqual(a['front']['radius'],.36,delta=.05)

    def test_missing_arch_is_reported_not_guessed(self):
        tris=np.asarray(side_panel(.9,[(1.25,.3)])+side_panel(-.9,[(1.25,.3)]),float)
        with self.assertRaises(ValueError):detect_arches(tris)

    def test_roof_ignores_antenna_and_wing(self):
        def quad(y,z0,z1,x=.3):
            v=[CompiledVertex(p,(0.,1.,0.),b'\xff'*4,((0.,0.),))for p in ((-x,y,z0),(x,y,z0),(x,y,z1),(-x,y,z1))]
            return ScenePart(DrawGeometry(tuple(v),((0,2,1),(0,3,2))),('t','Null','Null'))
        # roof 1.4 m from z -0.8..0.6, small wing higher at the tail.
        z,y=_roof([quad(1.4,-.8,.6),quad(1.5,-2.,-1.8),quad(1.,1.,2.)])
        self.assertAlmostEqual(z,-.1,delta=.06);self.assertAlmostEqual(y,1.4,delta=.01)


class CompilerPolicyTests(unittest.TestCase):
    def test_policy_keys_validated(self):
        from master_rallye.source_scene_compile import compile_draws
        with self.assertRaises(ValueError):compile_draws([],None,material_policy={'strict':'no'})
        with self.assertRaises(ValueError):compile_draws([],None,material_policy={'max_texture_dim':300})


if __name__=='__main__':unittest.main()
