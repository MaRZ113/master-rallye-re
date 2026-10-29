"""Common MR bridge invariants; synthetic neutral scenes contain no game assets."""
import copy
import math
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from master_rallye import universal_vehicle_scene as uvs
from master_rallye import universal_scene_bridge as bridge
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.scene_dx_writer import write_scene_dx,validate_scene_dx
from tests.synthetic.test_universal_vehicle_scene import fixture
from tests.synthetic.test_gt4_material_pipeline import scene as native_template


class UniversalSceneBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.original=self.base/'original';self.original.mkdir()
        self.scene,self.assets=fixture(self.original)
        rgba=bytes((10,20,30,255,40,50,60,255,70,80,90,255,100,110,120,255))
        self.scene['textures'][0].update(width=2,height=2,rgba_sha256=uvs.sha(rgba))
        self.assets['textures/pixel.rgba']=rgba
        for number,(slot,x,z)in enumerate((('front-left',1,2),('front-right',-1,2),('rear-left',1,-2),('rear-right',-1,-2))):
            mesh=copy.deepcopy(self.scene['meshes'][0]);mesh['id']='wheel-'+slot
            # Distinct left/right shapes are intentional and must not be
            # replaced with an assumed shared template or a guessed rotation.
            mesh['positions'][1][0]=.2 if x>0 else .4
            self.scene['meshes'].append(mesh)
            node=copy.deepcopy(self.scene['nodes'][0]);node.update(id=slot,mesh_ids=[mesh['id']])
            node['local_transform'][3]=x;node['local_transform'][11]=z
            node['source_transform_record']={'translation':[x,0,z],'rotation':None,'scale':None}
            self.scene['nodes'].append(node)
        self.profile={'schema':bridge.SCHEMA,'source_scene_sha256':'','normalized_to_mr':uvs.IDENTITY[:],
            'authoring_transform':uvs.IDENTITY[:],'transform_evidence':'invented evidenced test frame',
            'body_node_ids':['node'],'wheel_slots':{node['id']:node['id']for node in self.scene['nodes'][1:]},
            'canonical_wheel_slot':'front-left','texture_row_policy':'preserve','uv_v_policy':'preserve',
            'materials':{'material':{'mode':'opaque','interpretation':'mr_authoring','role':'test body/wheel',
                                     'evidence':'qualified synthetic MR interpretation'}}}
        self.save()

    def save(self):
        self.path=self.base/('input'+str(len(list(self.base.glob('input*')))))
        result=uvs.save_scene(self.scene,self.path,self.assets)
        self.profile['source_scene_sha256']=result['scene_sha256']

    def compile(self,profile=None,**kwargs):
        return bridge.compile_scene(self.path/'scene.json',self.profile if profile is None else profile,**kwargs)

    def test_compilation_is_pure_deterministic_and_preserves_source_ids_unknowns(self):
        before={p.relative_to(self.path):(p.read_bytes(),p.stat().st_mtime_ns)for p in self.path.rglob('*')if p.is_file()}
        profile_before=copy.deepcopy(self.profile);first=self.compile();second=self.compile()
        self.assertEqual(first,second);self.assertEqual(self.profile,profile_before)
        report=first['report'];draw=report['body_draws'][0]
        self.assertEqual((draw['node_id'],draw['mesh_id'],draw['material_id']),('node','mesh','material'))
        self.assertEqual(draw['source_vertex_ids'],[0,1,2]);self.assertEqual(draw['source_triangle_ids'],[0])
        self.assertEqual(report['unknown_semantics'],self.scene['unknown_semantics'])
        self.assertFalse(report['runtime_qualified']);self.assertFalse(report['runtime_single_wheel_safe'])
        for relative,value in before.items():
            p=self.path/relative;self.assertEqual((p.read_bytes(),p.stat().st_mtime_ns),value)

    def test_negative_determinant_reverses_winding_and_normals_without_uv_edits(self):
        result=self.compile();part=result['body_parts'][0]
        self.assertEqual(part.geometry.triangles,((0,2,1),))
        self.assertEqual(part.geometry.vertices[1].position,(2.,0.,0.))
        self.assertEqual(part.geometry.vertices[0].normal,(0.,0.,-1.))
        self.assertEqual(part.geometry.vertices[1].uvs,((1.,0.),))
        self.assertTrue(result['report']['body_draws'][0]['winding_reversed'])

    def test_hierarchy_and_nonuniform_inverse_transpose_are_reversible(self):
        self.scene['coordinate_system']['source_to_normalized']=uvs.IDENTITY[:]
        group=copy.deepcopy(self.scene['nodes'][0]);group.update(id='group',mesh_ids=[])
        group['local_transform'][3]=1;group['local_transform'][7]=2;group['local_transform'][11]=3
        self.scene['nodes'][0]['parent_id']='group';self.scene['nodes'].append(group)
        self.scene['meshes'][0]['normals']=[[1.,1.,0.]]*3
        self.profile['normalized_to_mr']=[-1.,0,0,0,0,1.,0,0,0,0,-1.,0,0,0,0,1.]
        self.profile['authoring_transform']=[2.,0,0,0,0,3.,0,0,0,0,4.,0,0,0,0,1.]
        self.save();result=self.compile();part=result['body_parts'][0]
        self.assertEqual(part.geometry.vertices[1].position,(-4.,6.,-12.))
        length=math.hypot(.5,1/3)
        for a,b in zip(part.geometry.vertices[0].normal,(-.5/length,(1/3)/length,0.)):
            self.assertAlmostEqual(a,b)
        record=result['report']['body_draws'][0]
        restored=uvs.transform_point(record['mr_to_source'],part.geometry.vertices[1].position)
        for a,b in zip(restored,[1.,0.,0.]):self.assertAlmostEqual(a,b)

    def test_original_left_and_right_wheel_shapes_and_literal_hubs_remain_separate(self):
        result=self.compile();wheels=result['wheel_parts_by_slot']
        self.assertEqual(len(wheels),4);self.assertEqual(len(result['complete_parts']),5)
        self.assertEqual(wheels['front-left'][0].geometry.vertices[1].position,(.4,0.,0.))
        self.assertEqual(wheels['front-right'][0].geometry.vertices[1].position,(.8,0.,0.))
        self.assertEqual(result['report']['hubs']['front-left']['source_hub_mr'],[2.,0.,-4.])
        self.assertEqual(result['report']['hubs']['front-right']['source_hub_mr'],[-2.,0.,-4.])
        self.assertEqual(result['report']['hubs']['front-left']['source_transform_record']['translation'],[1,0,2])
        self.assertIsNone(result['report']['hubs']['front-left']['source_local_transform'])

    def test_derived_hub_override_cannot_move_source_or_change_hub_local_shape(self):
        original=self.compile();self.profile['hub_overrides']={'front-left':[7.,3.,5.]};self.profile['hub_evidence']='explicit reversible donor fit'
        changed=self.compile();row=changed['report']['hubs']['front-left']
        self.assertEqual(row['source_hub_mr'],[2.,0.,-4.]);self.assertEqual(row['derived_hub_mr'],[7.,3.,5.])
        self.assertEqual(row['fit_delta_mr'],[5.,3.,9.])
        self.assertEqual(original['wheel_parts_by_slot']['front-left'],changed['wheel_parts_by_slot']['front-left'])
        self.assertNotEqual(original['complete_parts'][1],changed['complete_parts'][1])

    def test_unreferenced_vertices_are_removed_only_in_derived_draw_with_explicit_map(self):
        mesh=self.scene['meshes'][0];mesh['positions'].append([999.,999.,999.]);mesh['normals'].append([0,0,1]);mesh['uvs'].append([.5,.5])
        self.save();result=self.compile()
        self.assertEqual(len(result['body_parts'][0].geometry.vertices),3)
        self.assertEqual(result['report']['body_draws'][0]['source_vertex_ids'],[0,1,2])
        self.assertEqual(uvs.load_scene(self.path/'scene.json')['meshes'][0]['positions'][-1],[999.,999.,999.])

    def test_alpha_is_not_inferred_from_unknown_source_channels_or_flattened_silently(self):
        raw=bytes((10,20,30,0,40,50,60,127,70,80,90,128,100,110,120,255))
        self.assets['textures/pixel.rgba']=raw;self.scene['textures'][0]['rgba_sha256']=uvs.sha(raw);self.save()
        with self.assertRaisesRegex(ValueError,'unapproved source alpha'):self.compile()
        self.profile['materials']['material']['mode']='alpha_blend'
        result=self.compile();texture=parse_dxt_bytes(next(iter(result['textures'].values())))
        self.assertEqual(texture.bgra[3::4],bytes((0,127,128,255)))
        self.assertTrue(result['body_parts'][0].alpha);self.assertFalse(result['body_parts'][0].alpha_test)
        self.assertEqual((self.path/'textures/pixel.rgba').read_bytes(),raw)
        self.profile['materials']['material'].update(mode='opaque',allow_alpha_flatten=True)
        texture=parse_dxt_bytes(next(iter(self.compile()['textures'].values())))
        self.assertEqual(texture.bgra[3::4],b'\xff'*4)

    def test_explicit_cutout_threshold_and_authored_glass_alpha_stay_per_material(self):
        rule=self.profile['materials']['material'];rule.update(mode='alpha_test',alpha_ref=128)
        self.assets['textures/pixel.rgba']=bytes((1,2,3,0,4,5,6,127,7,8,9,128,10,11,12,255))
        self.scene['textures'][0]['rgba_sha256']=uvs.sha(self.assets['textures/pixel.rgba']);self.save()
        result=self.compile();self.assertTrue(result['body_parts'][0].alpha_test)
        self.assertEqual(parse_dxt_bytes(next(iter(result['textures'].values()))).bgra[3::4],b'\0\0\xff\xff')
        rule.pop('alpha_ref');rule.update(mode='alpha_blend',alpha_override=64)
        self.assertEqual(parse_dxt_bytes(next(iter(self.compile()['textures'].values()))).bgra[3::4],bytes([64]*4))
        rule['interpretation']='source_qualified'
        with self.assertRaises(ValueError):self.compile()

    def test_texture_row_and_uv_v_policies_are_independent_explicit_operations(self):
        self.profile.update(texture_row_policy='flip_vertical',uv_v_policy='flip')
        result=self.compile();rgba=self.assets['textures/pixel.rgba'];texture=parse_dxt_bytes(next(iter(result['textures'].values())))
        self.assertEqual(texture.bgra[:4],bytes((rgba[10],rgba[9],rgba[8],rgba[11])))
        self.assertEqual(result['body_parts'][0].geometry.vertices[0].uvs,((0.,1.),))
        self.assertFalse(result['report']['body_draws'][0]['source_uvs_preserved'])

    def test_environment_reference_is_explicit_native_and_hash_pinned(self):
        blob=struct.pack('<5I',0xfeed,1,0,1,1)+bytes((3,2,1,255))
        self.profile['materials']['material']['environment_reference']={'key':'stock','sha256':uvs.sha(blob)}
        with self.assertRaisesRegex(ValueError,'reference hash'):self.compile()
        result=self.compile(references={'stock':blob});self.assertTrue(result['body_parts'][0].environment)
        self.assertIn(blob,result['textures'].values())

    def test_profiles_cannot_silently_select_hidden_nodes_missing_roles_or_bad_frames(self):
        for change in ({'source_scene_sha256':'0'*64},{'body_node_ids':['node','node']},{'materials':{}},
                       {'wheel_slots':{'bad':'node'}},{'hub_overrides':[]},{'normalized_to_mr':[0.]*16}):
            profile=copy.deepcopy(self.profile);profile.update(change)
            with self.assertRaises(ValueError):self.compile(profile)
        self.scene['nodes'][0]['visible']=False;self.save()
        with self.assertRaisesRegex(ValueError,'hidden'):self.compile()

    def test_instanced_geometry_and_texture_budgets_are_bounded_without_writes(self):
        before=set(self.base.iterdir())
        with patch.object(bridge,'MAX_VERTICES',3):
            with self.assertRaisesRegex(ValueError,'geometry budget'):self.compile()
        with patch.object(bridge,'MAX_TEXTURE_BYTES',1):
            with self.assertRaisesRegex(ValueError,'texture budget'):self.compile()
        self.assertEqual(set(self.base.iterdir()),before)

    def test_evidenced_local_wheel_rotation_preserves_hubs_and_other_wheels(self):
        original=self.compile()
        turn=[-1.,0,0,0,0,1.,0,0,0,0,-1.,0,0,0,0,1.]
        self.profile.update(wheel_local_transforms={'front-left':turn},wheel_transform_evidence='synthetic rim-side evidence')
        rotated=self.compile()
        for slot in self.profile['wheel_slots']:
            self.assertEqual(original['report']['hubs'][slot]['derived_hub_mr'],rotated['report']['hubs'][slot]['derived_hub_mr'])
            if slot!='front-left':self.assertEqual(original['wheel_parts_by_slot'][slot],rotated['wheel_parts_by_slot'][slot])
        before=original['wheel_parts_by_slot']['front-left'][0].geometry
        after=rotated['wheel_parts_by_slot']['front-left'][0].geometry
        self.assertEqual(before.triangles,after.triangles)
        self.assertAlmostEqual(after.vertices[1].position[0],-before.vertices[1].position[0])
        self.assertEqual(before.vertices[1].uvs,after.vertices[1].uvs)

    def test_local_wheel_rotation_rejects_unevidenced_translation_scale_reflection_and_wrong_slot(self):
        for field,value in ((3,1.),(0,2.),(0,-1.),(1,.2)):
            rotation=uvs.IDENTITY[:];rotation[field]=value
            p=copy.deepcopy(self.profile);p.update(wheel_local_transforms={'front-left':rotation},wheel_transform_evidence='test')
            with self.assertRaises(ValueError):self.compile(p)
        self.profile['wheel_local_transforms']={'front-left':uvs.IDENTITY[:]}
        with self.assertRaises(ValueError):self.compile()
        self.profile.update(wheel_local_transforms={'absent':uvs.IDENTITY[:]},wheel_transform_evidence='test')
        with self.assertRaises(ValueError):self.compile()

    def test_source_corner_color_preservation_is_explicit_and_bounded(self):
        for mesh in self.scene['meshes']:mesh['preview_colors_bgra']=[[11,22,33,255]]*len(mesh['positions'])
        self.save();self.profile['materials']['material'].update(preserve_source_colors=True,vertex_rgba=[255,255,255,128])
        self.assertEqual(self.compile()['body_parts'][0].geometry.vertices[0].color,bytes((11,22,33,128)))
        for bad in (None,[[256,0,0,255]]*3,[[1,2,3,4]],[[1.,2,3,4]]*3):
            self.scene['meshes'][0]['preview_colors_bgra']=bad;self.save()
            with self.assertRaises(ValueError):self.compile()

    def test_common_scene_dx_writer_accepts_all_three_outputs_and_retains_collision(self):
        template,_=native_template();result=self.compile()
        for key in ('body_parts','complete_parts','wheel_parts'):
            data=write_scene_dx(template,result[key]);report=validate_scene_dx(template,data)
            self.assertTrue(report['collision_preserved'])
            self.assertEqual(report['output_draws'],len(result[key]))
            self.assertEqual(report['output_triangles'],len(result[key]))


if __name__=='__main__':unittest.main()
