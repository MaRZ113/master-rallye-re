import math,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'tools')]
import vmesh_final_cleanup as cleanup
from master_rallye.topology_writer import CompiledVertex


class CleanupTests(unittest.TestCase):
    def test_rim_keeps_metal_and_opaque_dark_interior(self):
        image=(2,2,bytes((100,90,50,217,9,10,12,0,100,90,50,217,9,10,12,0)))
        result,report=cleanup.rim_interior(image)
        self.assertEqual(result[2][:4],image[2][:4]);self.assertEqual(result[2][8:12],image[2][8:12])
        self.assertEqual(result[2][3::4],image[2][3::4]);self.assertTrue(report['opaque_face'])
        self.assertNotEqual(result[2][4:7],image[2][4:7])

    def test_sidewall_never_samples_donor_rim(self):
        w=64;px=bytearray()
        for y in range(w):
            for x in range(w):
                r=math.hypot(2*(x+.5)/w-1,2*(y+.5)/w-1)
                px.extend((220,200,30,217) if r<.62 else (18,19,20,0))
        result=cleanup.tyre_only_sidewall((w,w,bytes(px)),old_ratio=.62,new_ratio=.8)
        self.assertTrue(all(result[2][i:i+4]==bytes((18,19,20,0)) for i in range(0,len(px),4)))

    def test_sidewall_rejects_invalid_ratios(self):
        with self.assertRaises(ValueError):cleanup.tyre_only_sidewall((1,1,bytes(4)),old_ratio=.8,new_ratio=.6)

    def test_clip_interpolates_uv_z_color(self):
        def v(x,y):return CompiledVertex((x,y,2*x),(0,0,-1),bytes((100,100,100,255)),((x,y),))
        clipped=cleanup.clip_polygon([v(-1,0),v(1,0),v(0,1)],[(0,0),(1,0),(1,1),(0,1)])
        self.assertGreaterEqual(len(clipped),3)
        for p in clipped:
            self.assertGreaterEqual(p.position[0],-1e-10)
            self.assertAlmostEqual(p.position[2],2*p.position[0]);self.assertEqual(p.uvs[0],p.position[:2])

    def test_degenerate_mask_rejected(self):
        with self.assertRaises(ValueError):cleanup.hull_xy([(0,0),(1,1),(2,2)])

if __name__=='__main__':unittest.main()
