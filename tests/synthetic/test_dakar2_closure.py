"""Closure evidence refines blockers; controlled contexts never authorize L3."""
import copy
import unittest
from master_rallye.source_adapters.dakar2_materials import qualify_closure
from master_rallye.source_adapters.dakar2 import PINS
from test_dakar2_materials import qualification_fixture


def inputs():
    scene,evidence=qualification_fixture()
    coverage={'source_catalog':scene['source']['catalog'],'runtime_evidence':'NOT TESTED',
              'entry_alpha_enabled':False,'effective_reference_supplied':100,
              'draws':[{'mesh_id':'mesh','material_id':'draw','source_kind':0,'source_lod_flags':0,
                        'draw_pass':0,'explicit_cutout':False,'enabled':False,'comparison':'INHERITED','reference':None}]}
    vertex={'schema':'dakar2-vertex-evidence/1','xbe_sha256':PINS['default.xbe'],
            'native_linkers_match':True,'matrix_uploads_verified':True}
    return scene,evidence,coverage,vertex


class ClosureTests(unittest.TestCase):
    def test_static_evidence_does_not_erase_dynamic_dependencies(self):
        args=inputs();snapshot=copy.deepcopy(args);result=qualify_closure(*args)
        self.assertEqual(args,snapshot);self.assertEqual(result['native_material_readiness'],'BLOCKED')
        self.assertFalse(result['native_fixture_allowed']);self.assertEqual(result['source_feature_policy'],{})
        row=result['draws'][0]
        self.assertIn('position/normal/world-dependent',row['native_options']['A_static_composite'])
        self.assertFalse(row['coverage_runtime_verified']);self.assertFalse(row['native_fixture_allowed'])
        self.assertTrue(any('89/255' in x for x in row['blockers']))
        self.assertEqual(result,qualify_closure(*args))

    def test_missing_vertex_shader_evidence_rejected(self):
        args=list(inputs());args[3]={}
        with self.assertRaisesRegex(ValueError,'vertex evidence'):qualify_closure(*args)
        args=list(inputs());args[3]['xbe_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'vertex evidence'):qualify_closure(*args)

    def test_missing_duplicate_or_cross_vehicle_coverage_rejected(self):
        for mutate in(lambda x:x.update(draws=[]),lambda x:x['draws'].append(dict(x['draws'][0])),
                      lambda x:x.update(source_catalog='OTHER'),lambda x:x['draws'][0].update(material_id='other')):
            args=list(inputs());mutate(args[2])
            with self.assertRaisesRegex(ValueError,'coverage|Coverage'):qualify_closure(*args)

    def test_false_runtime_or_native_claim_is_not_consumed(self):
        args=list(inputs());args[2]['runtime_evidence']='PASS'
        with self.assertRaisesRegex(ValueError,'controlled coverage'):qualify_closure(*args)
        args=list(inputs());args[3]['native_fixture_allowed']=True
        self.assertFalse(qualify_closure(*args)['native_fixture_allowed'])


if __name__=='__main__':unittest.main()
