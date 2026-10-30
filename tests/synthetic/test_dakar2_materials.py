"""Source-free arithmetic and fail-closed native material regressions."""
import copy,unittest
from master_rallye.source_adapters.dakar2_materials import decode_pixel_definition,evaluate_pixel_definition,qualify_scene,native_requirements
from master_rallye.source_adapters.dakar2 import PINS


def shader(*,multi=False):
    # Synthetic multiply/sum inputs, not a stored game executable payload.
    words=[0]*60;words[53]=0x11100|(3 if multi else 1);words[54]=0x421 if multi else 1
    words[57]=words[58]=0xffffffff
    words[34]=0x08040000;words[45]=0xd0 if multi else 0xc0
    words[0]=0x18141010;words[26]=0xd0 if multi else 0xc0
    if multi:
        words[35]=0x0a110000;words[46]=0xa0;words[57]=0xffffff0f
        words[36]=0x190a200d;words[47]=0xc00
        words[2]=0x18301010;words[28]=0xc0
    return words


def qualification_fixture():
    words=shader(multi=True);digest=decode_pixel_definition(words)['sha256']
    material={'id':'draw','raw_fields':[{'declaration':8,'source_offset':100,
                'texture_bindings':['xtx-001','xtx-002','xtx-003'],'native_four_texture_resource_ids':[1,2,3,None]}],
              'source_render_state':{'pixel_definition_sha256':digest,'blend':False,'depth_write':True,'alpha_test':'UNKNOWN','cull':'none'}}
    stream={'stride':8,'sha256':'a'*64}
    scene={'metadata':{'adapter':'dakar2-xbox-source/1'},'source':{'catalog':'PAJERO_HI_0_0.LOD'},
           'materials':[material], 'textures':[{'id':'xtx-'+str(i).zfill(3),'rgba_sha256':'b'*64}for i in(1,2,3)],
           'nodes':[{'id':'node','name':'BODY','mesh_ids':['mesh'],'render_pass':0,'source_transform_record':{'id':0}}],
           'meshes':[{'id':'mesh','material_id':'draw','triangles':[[0,1,2]],
                      'source':{'streams':{'9':dict(stream),'10':dict(stream)},'member_sha256':'c'*64}}]}
    evidence={'xbe_sha256':PINS['default.xbe'],'declarations':{'8':{'pixel_definition_words':words,'vertex_program_va':123}}}
    return scene,evidence


class MaterialTests(unittest.TestCase):
    def test_required_additive_secondary_maps_do_not_disappear_when_uvs_alias(self):
        decoded=decode_pixel_definition(shader(multi=True))
        with self.assertRaisesRegex(ValueError,'runtime pixel constant'):
            evaluate_pixel_definition(decoded,{'t0':[.2]*4,'t1':[.4]*4,'t2':[.5]*4},[1]*4)
        value=evaluate_pixel_definition(decoded,{'t0':[.2,.2,.2,.7],'t1':[.4]*4,'t2':[.5]*4},[1]*4,runtime_constants={0:[0,0,0,.5]})
        self.assertAlmostEqual(value[0],.3);self.assertAlmostEqual(value[3],.7)
        self.assertNotEqual(value[0],.2)

    def test_original_color_is_explicit_vertex_program_output(self):
        decoded=decode_pixel_definition(shader())
        value=evaluate_pixel_definition(decoded,{'t0':[.2,.4,.6,.8]},[.5,.25,1,.5])
        self.assertEqual(value,[.1,.1,.6,.4])
        with self.assertRaises(ValueError):evaluate_pixel_definition(decoded,{'t0':[1]*4},None)

    def test_alpha_does_not_inherit_secondary_rgb_addition(self):
        decoded=decode_pixel_definition(shader(multi=True));samples={'t0':[.1,.2,.3,.25],'t1':[1,1,1,1],'t2':[1,1,1,0]}
        value=evaluate_pixel_definition(decoded,samples,[1]*4,runtime_constants={0:[0,0,0,1]})
        self.assertEqual(value,[1.,1.,1.,.25])

    def test_secondary_alpha_mask_is_not_secondary_rgb(self):
        decoded=decode_pixel_definition(shader(multi=True));constants={0:[0,0,0,1]}
        inputs={'t0':[.2,.2,.2,.7],'t1':[1,0,0,.5],'t2':[.4,.4,.4,1]}
        value=evaluate_pixel_definition(decoded,inputs,[1]*4,runtime_constants=constants)
        self.assertEqual(value,[.4,.4,.4,.7])
        inputs['t1']=[0,1,1,.5]
        self.assertEqual(value,evaluate_pixel_definition(decoded,inputs,[1]*4,runtime_constants=constants))
        inputs['t1']=[0,1,1,0]
        self.assertEqual(evaluate_pixel_definition(decoded,inputs,[1]*4,runtime_constants=constants),[.2,.2,.2,.7])

    def test_no_automatic_baked_default_for_dynamic_constant(self):
        decoded=decode_pixel_definition(shader(multi=True))
        decoded['stages'][1]['constant0_argb']=0xff000000
        with self.assertRaisesRegex(ValueError,'runtime pixel constant'):
            evaluate_pixel_definition(decoded,{'t0':[1]*4,'t1':[1]*4,'t2':[1]*4},[1]*4)

    def test_reserved_layout_and_budget_rejected(self):
        for words in([0]*61,[0]*60,[False]*60):
            with self.assertRaises(ValueError):decode_pixel_definition(words)
        for index,value in[(53,9),(54,31),(34,0x06000000),(45,0x00f0)]:
            words=shader();words[index]=value
            with self.assertRaises(ValueError):decode_pixel_definition(words)

    def test_unknown_effect_never_silently_approximated(self):
        decoded=decode_pixel_definition(shader());decoded['final_combiner_enabled']=True
        with self.assertRaisesRegex(ValueError,'final combiner'):evaluate_pixel_definition(decoded,{'t0':[1]*4},[1]*4)
        decoded=decode_pixel_definition(shader());decoded['stages'][0]['rgb_outputs']['flags']=2
        with self.assertRaisesRegex(ValueError,'dot/mux'):evaluate_pixel_definition(decoded,{'t0':[1]*4},[1]*4)

    def test_missing_stage_and_nonfinite_inputs_rejected(self):
        decoded=decode_pixel_definition(shader(multi=True))
        with self.assertRaisesRegex(ValueError,'texture input'):evaluate_pixel_definition(decoded,{'t0':[1]*4},[1]*4)
        with self.assertRaisesRegex(ValueError,'Finite'):evaluate_pixel_definition(decoded,{'t0':[1]*4},[float('nan')]*4)

    def test_evaluator_preserves_inputs_and_is_deterministic(self):
        decoded=decode_pixel_definition(shader());snapshot=copy.deepcopy(decoded);textures={'t0':[.1,.2,.3,.4]}
        self.assertEqual(evaluate_pixel_definition(decoded,textures,[1]*4),evaluate_pixel_definition(decoded,textures,[1]*4))
        self.assertEqual(decoded,snapshot);self.assertEqual(textures,{'t0':[.1,.2,.3,.4]})

    def test_uv_data_alias_never_authorizes_material_omission_or_l3(self):
        scene,evidence=qualification_fixture();before=copy.deepcopy(scene)
        report=qualify_scene(scene,evidence);self.assertEqual(report['uv1_exact_aliases'],1)
        self.assertEqual(report['native_material_readiness'],'BLOCKED');self.assertFalse(report['native_fixture_allowed'])
        self.assertEqual(report['source_feature_policy'],{})
        requirement=native_requirements(scene,evidence)[0]
        self.assertFalse(requirement['allow_omit_for_mr']);self.assertEqual(requirement['required_texture_stages'],[0,1,2])
        self.assertFalse(requirement['source_uv_data_alias_is_shader_equivalence']);self.assertEqual(scene,before)

    def test_source_shader_and_texture_binding_corruption_rejected(self):
        for mutate in(lambda s:s['materials'][0]['source_render_state'].update(pixel_definition_sha256='0'*64),
                      lambda s:s['materials'][0]['raw_fields'][0]['texture_bindings'].__setitem__(1,'xtx-001'),
                      lambda s:s['textures'].pop(),
                      lambda s:s['source'].update(catalog='../../escape')):
            scene,evidence=qualification_fixture();mutate(scene)
            with self.assertRaises(ValueError):qualify_scene(scene,evidence)


if __name__=='__main__':unittest.main()
