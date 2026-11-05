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

class PairedOrientation(unittest.TestCase):
    def test_reversed_copy_is_one_native_surface_in_either_order(self):
        from types import SimpleNamespace as S
        model=S(vertices=S(positions=[(0,0,0),(1,0,0),(0,0,1)],normals=[(0,1,0)]*3),local_indices=[0,1,2,1,0,2])
        draw=S(vertex_base=0,index_start=0,index_count=6)
        self.assertEqual(lighting.orientation_votes(model,draw),[1,0])
        model.local_indices=[1,0,2,0,1,2]
        self.assertEqual(lighting.orientation_votes(model,draw),[1,0])
    def test_unpaired_opposed_orientation_is_not_relabelled(self):
        from types import SimpleNamespace as S
        model=S(vertices=S(positions=[(0,0,0),(1,0,0),(0,0,1)],normals=[(0,1,0)]*3),local_indices=[1,0,2])
        self.assertEqual(lighting.orientation_votes(model,S(vertex_base=0,index_start=0,index_count=3)),[0,1])

class ScopedStaticPass(unittest.TestCase):
    def test_fresh_detail_proof_replaces_stale_seed_but_not_source_conflicts(self):
        row=dict(course='Custom',material='conc',texture_sha256='a'*64,category=4,flags=lighting.PLAIN|lighting.NOISE,winding=-1)
        denied=dict(row,category=0,flags=lighting.DENY)
        self.assertEqual(lighting.merge_source_material(row,denied,False,True),row)
        for source_seen,detail in [(True,True),(False,False),(True,False)]:
            self.assertEqual(lighting.merge_source_material(row,denied,source_seen,detail)['flags'],lighting.DENY)
        for previous in [dict(denied,material='glass'),dict(denied,flags=lighting.DENY|lighting.ENV_TEXTURE),dict(row,category=2,flags=lighting.NOISE)]:
            self.assertEqual(lighting.merge_source_material(row,previous,False,True)['flags'],lighting.DENY)
        # A subsequent source conflict cannot be erased by a later good alias.
        bad=lighting.merge_source_material(denied,row,True,False)
        self.assertEqual(lighting.merge_source_material(row,bad,True,True)['flags'],lighting.DENY)

    def test_static_detail_and_plain_share_one_material_role(self):
        for name in ['f_conc-tga', 'cement-tga', 'new_bridge-tga', 'metal_panel-tga']:
            contracts=[(name,'Null','Null'),(name,'Null','noise-tga')]
            self.assertTrue(lighting.static_detail_capability(name,contracts))
        self.assertTrue(lighting.static_detail_capability('custom', [('custom','Null','Null'),('custom','Null','noise-tga')], 'static'))

    def test_detail_reconciliation_keeps_unknown_and_special_materials_closed(self):
        for name in ['unknown', 'concentrate', 'water_conc', 'glass_wall', 'glow_panel', 'shadow_concrete']:
            self.assertFalse(lighting.static_detail_capability(name,[(name,'Null','Null'),(name,'Null','noise-tga')]))
        for contracts in [[('wall','Null','Null')], [('wall','Null','noise-tga')], [('wall','Null','Null'),('wall','aluminium-tga','Null')], [('wall','Null','Null'),('wall','Null','arbitrary')], [('wall','Null','Null'),('other','Null','noise-tga')]]:
            self.assertFalse(lighting.static_detail_capability('wall',contracts))
        for role in ['exclude', 'terrain', 'signage']:
            self.assertFalse(lighting.static_detail_capability('wall',[('wall','Null','Null'),('wall','Null','noise-tga')],role))

    def test_static_plain_counterpart_does_not_authorize_other_shaders(self):
        self.assertTrue(lighting.static_plain_capability('fencegate-tga',[('fencegate-tga','Null','Null'),('fencegate-tga','aluminium-tga','Null')]))
        self.assertFalse(lighting.static_plain_capability('fencegate-tga',[('fencegate-tga','glass-tga','Null')]))
        self.assertFalse(lighting.static_plain_capability('waterwall-tga',[('waterwall-tga','Null','Null')]))
        self.assertFalse(lighting.static_plain_capability('unknown-tga',[('unknown-tga','aluminium-tga','Null')]))
        self.assertFalse(lighting.static_plain_capability('fencegate-tga',[('fencegate-tga','Null','Null')],'exclude'))

    def test_common_props_are_course_independent_signage(self):
        import sys
        src=str(Path(__file__).parents[1]/'src')
        if src not in sys.path:sys.path.insert(0,src)
        from master_rallye import course_lighting as package
        root=Path(r'D:/Game/Master Rallye/Data.sma_unpacked/DataGx')
        if not (root/'Misc/Checkpoints/stamp_01-tga.dxt').exists():self.skipTest('private unpacked DataGx fixture')
        base=package.encode_metadata([])
        data,report=package.add_common_records(base,root)
        rows=package.decode_metadata(data)
        self.assertTrue(rows and all(r['course']=='Common' and r['category']==4 and r['flags']==package.PLAIN|package.ALPHA_TEST and r['winding']==-1 for r in rows))
        self.assertEqual({m['material'] for m in report['materials']},{'i2a_planks2-tga','stamp_01-tga','masterlogo-tga'})
        again,_=package.add_common_records(data,root)
        self.assertEqual(again,data)


if __name__=='__main__':unittest.main()

class EnvironmentCapabilities(unittest.TestCase):
    def test_course_paint_environment_is_general_but_glass_and_glow_stay_closed(self):
        for secondary in lighting.STATIC_ENVIRONMENTS:
            inferred=secondary not in lighting.ROLE_ONLY_ENVIRONMENTS
            self.assertEqual(lighting.static_environment_capability('new_layout_prop',[('new_layout_prop',secondary,'Null')]),inferred)
            self.assertTrue(lighting.static_environment_capability('new_layout_prop',[('new_layout_prop',secondary,'Null')],'static'))
            for primary in ('glass','window','lamp','glow','wheel'):
                self.assertFalse(lighting.static_environment_capability(primary,[(primary,secondary,'Null')]))
    def test_glass_secondary_needs_explicit_static_role(self):
        contracts=[('marina_alphas-tga','glass-tga','Null')]
        self.assertFalse(lighting.static_environment_capability('marina_alphas-tga',contracts))
        self.assertTrue(lighting.static_environment_capability('marina_alphas-tga',contracts,'static'))
        self.assertFalse(lighting.static_environment_capability('marina_alphas-tga',contracts,'signage'))
        self.assertFalse(lighting.static_environment_capability('window-tga',[('window-tga','glass-tga','Null')],'static'))
    def test_static_secondary_is_scoped_to_aluminium(self):
        for name in ('metalpanel-tga','caravan-tga','fencegate-tga'):
            self.assertTrue(lighting.static_environment_capability(name,[(name,'aluminium-tga','Null')]))
            self.assertFalse(lighting.static_environment_capability(name,[(name,'perspex-tga','Null')]))
            self.assertFalse(lighting.static_environment_capability(name,[(name,'aluminium-tga','noise-tga')]))
        self.assertFalse(lighting.static_environment_capability('watermetal-tga',[('watermetal-tga','aluminium-tga','Null')]))
        self.assertTrue(lighting.static_environment_capability('new_custom_label-tga',[('new_custom_label-tga','aluminium-tga','Null')]))
        self.assertFalse(lighting.static_environment_capability('new_custom_label-tga',[('new_custom_label-tga','Null','Null')]))
    def test_environment_metadata_roundtrip_and_unsafe_certificate(self):
        row=dict(course='CustomLayout',material='aluminium-tga',texture_sha256='a'*64,category=0,flags=lighting.DENY|lighting.ENV_TEXTURE,winding=-1)
        self.assertEqual(lighting.decode_metadata(lighting.encode_metadata([row]))[0],row)
        glass=dict(row,material='glass-tga')
        self.assertEqual(lighting.decode_metadata(lighting.encode_metadata([glass]))[0],glass)
        for changes in ({'category':4},{'material':'perspex-tga'},{'flags':lighting.ENV_TEXTURE},{'flags':lighting.ENVIRONMENT|lighting.DENY}):
            with self.assertRaises(ValueError):lighting.decode_metadata(lighting.encode_metadata([{**row,**changes}]))

class StaticCoverageMetadata(unittest.TestCase):
    def test_static_cutout_capability_round_trip_and_rejections(self):
        row=dict(course='NewLayout',material='authored_panel',texture_sha256='1'*64,category=4,flags=lighting.PLAIN|lighting.ALPHA_TEST,winding=-1)
        self.assertEqual(lighting.decode_metadata(lighting.encode_metadata([row]))[0]['flags'],row['flags'])
        for category,flags in [(3,lighting.PLAIN|lighting.ALPHA_TEST|lighting.ENVIRONMENT),(4,lighting.PLAIN|lighting.TWO_SIDED),(2,lighting.NOISE|lighting.ALPHA_TEST)]:
            with self.assertRaises(ValueError):lighting.decode_metadata(lighting.encode_metadata([dict(row,category=category,flags=flags)]))

class CoursePackages(unittest.TestCase):
    def test_asset_names_do_not_have_to_match_course(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            for n in ['track01.dx','second.DX','texture.dxt']:(folder/n).write_bytes(b'')
            self.assertEqual([p.name for p in lighting.course_model_paths(folder)],['second.DX','track01.dx'])
    def test_combined_plain_cutout_and_environment_capabilities(self):
        row=dict(course='Combined',material='staticmetal',texture_sha256='1'*64,category=4,flags=lighting.PLAIN|lighting.ALPHA_TEST|lighting.ENVIRONMENT,winding=-1)
        self.assertEqual(lighting.decode_metadata(lighting.encode_metadata([row]))[0]['flags'],row['flags'])

class InheritedMaterialRoles(unittest.TestCase):
    def test_accepted_roles_survive_without_bypassing_explicit_exclusion(self):
        rows=[dict(course='Turkey3',material='boat2-tga',category=4,flags=lighting.PLAIN|lighting.NOISE),dict(course='Common',material='board',category=4,flags=lighting.PLAIN)]
        roles=lighting.inherit_base_roles(rows,{'Turkey3':{'board':'exclude'}},['Turkey3','NewLayout'])
        self.assertEqual(roles['Turkey3']['boat2-tga'],'static');self.assertEqual(roles['Turkey3']['board'],'exclude');self.assertEqual(roles['NewLayout']['board'],'static')
        self.assertEqual(lighting.material_role('glass',('glass','Null','Null'),'static'),(0,lighting.DENY))
    def test_ambiguous_base_roles_are_not_inherited(self):
        rows=[dict(course='Test',material='mixed',category=c,flags=lighting.PLAIN) for c in (2,4)]
        self.assertNotIn('mixed',lighting.inherit_base_roles(rows,None,['Test'])['Test'])

class Atmosphere5NameRoles(unittest.TestCase):
    def test_italy_and_france_props_are_classified_by_name(self):
        plain=lambda n:lighting.material_role(n,(n,'Null','Null'))
        for name in ('pinus-tga','pinus2-tga','conniffer-tga','hedge-tga','vines1-tga'):
            self.assertEqual(plain(name)[0],3,name)
        for name in ('i_largevilla1-tga','village04-tga','shelter1-tga','railpylon-tga','raillings-tga','crate1-tga','turkshack01-tga','tower-tga','balcony-tga'):
            self.assertEqual(plain(name),(4,lighting.PLAIN),name)
        for name in ('ravine-tga','temp-tga','ctyre-tga','s_light01-tga'):
            self.assertEqual(plain(name),(0,lighting.DENY),name)
