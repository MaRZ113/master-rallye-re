"""Synthetic command/state fixtures for qualified non-spatial VM callbacks."""
import copy,unittest
from unittest.mock import patch
from master_rallye.addon_sdk.gt4_scene import reconstruct


PROFILE={'vm_context':'GT4Beta.CarModel.callback_vtable_006C15B8','engine_sha256':'962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0','callback_indices':[1,2,3,4],'evidence':'qualified original Beta scalar setter'}


class TweenCallbackTests(unittest.TestCase):
    def scene(self,transforms,*,profile=PROFILE,morph=False,freeze=False):
        model={'base':0,'sha256':'a'*64,'models':[{'commands_offset':0}],'shapes':[{'offset':20,'flags':[0]}],'materials':[]}
        vertices=[{'position':p,'normal':(0.,0.,1.),'uv':None,'rgba_ps2':None,'morph_target':{'position':p} if morph else None} for p in [(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]]
        geo={'vertices':vertices,'triangles':[(0,1,2)],'packets':[{'texture':0,'material':0,'first_triangle':0,'triangle_count':1,'untranslated_attributes':[],'gif':{'blend':False}}]}
        call={'shape':0,'commands':[],'transforms':transforms,'texture_table':{'kind':'internal','index':0},'tween':None,'command_offset':4}
        with patch('master_rallye.addon_sdk.gt4_scene.modelset',return_value=model),patch('master_rallye.addon_sdk.gt4_scene.shape_geometry',return_value=geo),patch('master_rallye.addon_sdk.gt4_scene.model_texture_sets',return_value=[]),patch('master_rallye.addon_sdk.gt4_scene.command_graph',return_value={'nodes':[{'opcode':4,'operands':[0],'offset':4}]}),patch('master_rallye.addon_sdk.gt4_scene.binding_trace',return_value={'blocked_at':None,'draws':[call]}):
            return reconstruct(b'own fixture',freeze_morphs=freeze,vm_tween_callback_profile=profile)['draws'][0]

    def test_static_surface_after_known_tween_callbacks_is_not_a_matrix_instance(self):
        ts=[{'opcode':89,'operands':[i]} for i in (4,3,1,2)]
        self.assertEqual(self.scene(ts)['issues'],[])
        self.assertEqual(self.scene(ts)['qualified_tween_callbacks'],ts)
        self.assertIn('unresolved instance transforms',self.scene(ts,profile=None)['issues'])
        self.assertIn('unresolved instance transforms',self.scene(ts+[{'opcode':17,'operands':[]}])['issues'])
        self.assertIn('unresolved instance transforms',self.scene([{'opcode':89,'operands':[5]}])['issues'])

    def test_morph_still_requires_explicit_freeze_and_unknown_engine_is_rejected(self):
        ts=[{'opcode':89,'operands':[1]}]
        self.assertIn('unresolved tween weight',self.scene(ts,morph=True)['issues'])
        self.assertEqual(self.scene(ts,morph=True,freeze=True)['issues'],[])
        bad=copy.deepcopy(PROFILE);bad['engine_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'engine semantics'):self.scene(ts,profile=bad)
        bad=copy.deepcopy(PROFILE);bad['vm_context']='unqualified handler'
        with self.assertRaisesRegex(ValueError,'engine semantics'):self.scene(ts,profile=bad)
        bad=copy.deepcopy(PROFILE);bad['callback_indices']=[5]
        with self.assertRaisesRegex(ValueError,'callback index'):self.scene(ts,profile=bad)


if __name__=='__main__':unittest.main()
