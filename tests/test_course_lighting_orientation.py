"""Material admission must not depend on a source variant's smoothing normals."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('course_lighting_orientation',Path(__file__).parents[1]/'src/master_rallye/course_lighting.py')
lighting=importlib.util.module_from_spec(spec);spec.loader.exec_module(lighting)

class CourseLightingOrientation(unittest.TestCase):
    def test_pc_and_mixed_ps2_normals_keep_the_same_noise_capability(self):
        pc=lighting.orientation_policy(2,lighting.NOISE,1836,1)
        ps2=lighting.orientation_policy(2,lighting.NOISE,1721,353)
        self.assertEqual(pc,ps2)
        self.assertEqual(pc,(2,lighting.NOISE,-1))

    def test_noise_winding_comes_from_native_geometry_not_authored_normals(self):
        for negative,positive in [(0,0),(1,50),(50,1)]:
            self.assertEqual(lighting.orientation_policy(1,lighting.NOISE,negative,positive),(1,lighting.NOISE,-1))

    def test_shader_exclusions_cannot_be_requalified_by_normal_votes(self):
        for name in ['water','glass','glow','lamp','tyre','reflection']:
            category,flags=lighting.material_role(name,(name,'Null','noise-tga'))
            self.assertEqual((category,flags),(0,lighting.DENY))
            self.assertEqual(lighting.orientation_policy(category,flags,1721,353)[:2],(0,lighting.DENY))

    def test_plain_material_orientation_ambiguity_stays_closed(self):
        self.assertEqual(lighting.orientation_policy(4,lighting.PLAIN,1721,353)[:2],(0,lighting.DENY))
        self.assertEqual(lighting.orientation_policy(4,lighting.PLAIN,1836,1),(4,lighting.PLAIN,-1))

    def test_authored_signage_is_plain_static_not_a_shader_bypass(self):
        self.assertEqual(lighting.material_role('new_advert',('new_advert','Null','Null'),'signage'),(4,lighting.PLAIN))
        self.assertEqual(lighting.orientation_policy(4,lighting.PLAIN,176,80,True),(4,lighting.PLAIN,-1))
        self.assertEqual(lighting.material_role('new_advert',('new_advert','reflection','Null'),'signage'),(0,lighting.DENY))
        self.assertEqual(lighting.material_role('water',('water','Null','Null'),'signage'),(0,lighting.DENY))
        self.assertEqual(lighting.material_role('new_advert',('new_advert','Null','noise-tga'),'signage'),(0,lighting.DENY))

class GeometryRoles(unittest.TestCase):
    @staticmethod
    def model(points,indices):
        from types import SimpleNamespace as S
        model=S(vertices=S(positions=points),local_indices=indices)
        return model,[S(vertex_base=0,index_start=0,index_count=len(indices))]
    def test_large_cw_ground_is_inferred_without_material_name(self):
        model,draws=self.model([(0,0,0),(40,0,0),(0,0,40)],[0,1,2])
        self.assertEqual(lighting.geometry_role(model,draws),'terrain')
    def test_upright_connected_banner_is_inferred_without_brand_name(self):
        model,draws=self.model([(0,0,0),(4,0,0),(4,1,0),(0,1,0)],[0,1,2,0,2,3])
        self.assertEqual(lighting.geometry_role(model,draws),'signage')
    def test_small_horizontal_prop_and_crossed_billboards_remain_unknown(self):
        model,draws=self.model([(0,0,0),(4,0,0),(0,0,4)],[0,1,2])
        self.assertIsNone(lighting.geometry_role(model,draws))
        model,draws=self.model([(0,0,0),(4,0,0),(4,1,0),(0,0,4),(0,1,4)],[0,1,2,0,3,4])
        self.assertIsNone(lighting.geometry_role(model,draws))

if __name__=='__main__':unittest.main()
