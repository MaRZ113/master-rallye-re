"""Adversarial, source-free cross-engine boundary tests; no donor payloads."""
import copy
from pathlib import Path
import struct,tempfile,unittest
from master_rallye import universal_vehicle_scene as u
from master_rallye import scene_semantics as sem
from master_rallye.source_qualification import preflight
from tests.synthetic.test_universal_vehicle_scene import fixture,rebind_manifest
from tests.synthetic import test_universal_scene_bridge as bridge_fixture


class SceneSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.original=self.base/'original';self.original.mkdir()
        self.scene,self.assets=fixture(self.original)
        self.doc={'schema':sem.SCHEMA,'source_scene_sha256':'a'*64,'claims':[]}

    def claim(self,role='opaque_body',triangles='all',mesh='mesh'):
        return {'mesh_id':mesh,'material_id':'material','triangles':triangles,'role':role,
                'interpretation':'mr_authoring','evidence':'Invented source triangle identity and bounded role'}

    def test_unknown_is_not_mandatory_classification(self):
        before=copy.deepcopy(self.scene);r=sem.validate(self.scene,self.doc,'a'*64)
        self.assertEqual(r['unclassified_triangles'],1);self.assertEqual(self.scene,before)
        self.assertEqual(sum(r['roles'].values()),0)

    def test_glass_cannot_share_door_or_frame_triangles(self):
        for opaque in ('opaque_body','frame','lamp_off'):
            self.doc['claims']=[self.claim(opaque),self.claim('glass')]
            with self.assertRaisesRegex(ValueError,'conflicting'):sem.validate(self.scene,self.doc,'a'*64)

    def test_claims_require_exact_material_source_hash_and_triangle_ids(self):
        for key,value in (('material_id','different'),('mesh_id','unknown'),('triangles',[1]),('triangles',[0,0]),('triangles',[True]),('evidence','')):
            c=self.claim();c[key]=value;self.doc['claims']=[c]
            with self.assertRaises(ValueError):sem.validate(self.scene,self.doc,'a'*64)
        self.doc['claims']=[self.claim()]
        with self.assertRaises(ValueError):sem.validate(self.scene,self.doc,'b'*64)

    def test_reflections_require_complete_original_material_group(self):
        second=copy.deepcopy(self.scene['meshes'][0]);second['id']='mesh2';self.scene['meshes'].append(second)
        self.doc['claims']=[self.claim('reflective_paint')]
        with self.assertRaisesRegex(ValueError,'fragmented'):sem.validate(self.scene,self.doc,'a'*64)
        self.doc['claims'].append(self.claim('reflective_paint',mesh='mesh2'))
        self.assertEqual(sem.validate(self.scene,self.doc,'a'*64)['roles']['reflective_paint'],2)

    def test_alpha_blend_cannot_override_opaque_body_ownership(self):
        profile={'materials':{'material':{'mode':'alpha_blend'}}};self.doc['claims']=[self.claim()]
        with self.assertRaisesRegex(ValueError,'unqualified body'):sem.native_roles(self.scene,profile,self.doc)
        self.doc['claims']=[self.claim('glass')];sem.native_roles(self.scene,profile,self.doc)

    def test_semantic_duplicate_claim_budget_and_unsupported_role_fail(self):
        self.doc['claims']=[self.claim(),self.claim()]
        with self.assertRaises(ValueError):sem.validate(self.scene,self.doc,'a'*64)
        self.doc['claims']=[self.claim('invented_damage_zone')]
        with self.assertRaises(ValueError):sem.validate(self.scene,self.doc,'a'*64)
        self.doc['claims']=[self.claim()]*8193
        with self.assertRaisesRegex(ValueError,'budget'):sem.validate(self.scene,self.doc,'a'*64)

    def test_secondary_uv_count_finiteness_and_evidence_boundaries(self):
        channel={'values':[[0.,0.],[1.,0.],[0.,1.]],'evidence':'invented raw source stream'}
        mesh=self.scene['meshes'][0];mesh['uv_channels']={'1':channel};u.validate_scene(self.scene)
        for values in ([[0.,0.]],[[0.,0.],[float('nan'),0.],[0.,1.]]):
            channel['values']=values
            with self.assertRaises(ValueError):u.validate_scene(self.scene)
        channel['values']=mesh['uvs'];channel['evidence']=''
        with self.assertRaises(ValueError):u.validate_scene(self.scene)

    def test_stream_hash_cannot_be_reassigned_by_transport_manifest(self):
        raw=struct.pack('<6f',0,0,1,0,0,1);mesh=self.scene['meshes'][0]
        mesh['source']['streams']={'10':{'path':'streams/uv1.bin','stride':8,'sha256':u.sha(raw)}}
        self.assets['streams/uv1.bin']=raw;output=self.base/'scene';u.save_scene(self.scene,output,self.assets)
        changed=struct.pack('<6f',0,0,0,1,1,0);rebind_manifest(output,'streams/uv1.bin',changed)
        with self.assertRaisesRegex(ValueError,'unbound'):u.load_scene(output/'scene.json')

    def test_stream_stride_count_and_missing_payload_rejected_before_writes(self):
        mesh=self.scene['meshes'][0]
        for stride in (0,257,True,8):
            mesh['source']['streams']={'10':{'path':'uv1.bin','stride':stride,'sha256':'0'*64}}
            with self.assertRaises(ValueError):u.save_scene(self.scene,self.base/'bad',self.assets)
            self.assertFalse((self.base/'bad').exists())

    def test_source_corner_colors_rejected_on_reopen_or_save(self):
        mesh=self.scene['meshes'][0]
        for color in ([[1,2,3,255]],[[1,2,3,256]]*3,[[True,2,3,255]]*3):
            mesh['preview_colors_bgra']=color
            with self.assertRaises(ValueError):u.validate_scene(self.scene)

    def test_uv_alias_is_lossless_only_with_exact_data(self):
        mesh=self.scene['meshes'][0];mesh['uv_channels']={'1':{'values':copy.deepcopy(mesh['uvs']),'evidence':'synthetic'}}
        policy={'mesh:mesh:uv1':{'disposition':'alias_uv0','evidence':'Equal raw channels','impact':'No data loss; shader behavior separately unknown'}}
        self.assertEqual(sem.feature_policy(self.scene,policy)[0]['status'],'PASS')
        mesh['uv_channels']['1']['values'][0][0]=.25
        with self.assertRaisesRegex(ValueError,'not identical'):sem.feature_policy(self.scene,policy)

    def test_secondary_stage_is_not_silently_diffuse_only(self):
        self.scene['materials'][0]['raw_fields']=[{'texture_bindings':['a','b','c']}]
        with self.assertRaisesRegex(ValueError,'unapproved'):sem.feature_policy(self.scene,{})
        features=sem.features(self.scene)
        policy={f['id']:{'disposition':'omit_for_mr','evidence':'Explicit research approximation','impact':'Secondary shader unavailable; source preserved, not source fidelity'}for f in features}
        self.assertEqual([x['status']for x in sem.feature_policy(self.scene,policy)],['WARN','WARN'])

    def test_actual_bridge_rejects_secondary_uv_until_explicit_disposition(self):
        fixture_=bridge_fixture.UniversalSceneBridgeTests();fixture_.setUp();self.addCleanup(fixture_.doCleanups)
        fixture_.scene['meshes'][0]['uv_channels']={'1':{'values':copy.deepcopy(fixture_.scene['meshes'][0]['uvs']),'evidence':'synthetic'}}
        fixture_.save()
        with self.assertRaisesRegex(ValueError,'unapproved native feature'):fixture_.compile()
        fixture_.profile['source_feature_policy']={'mesh:mesh:uv1':{'disposition':'alias_uv0','evidence':'Exact equal values','impact':'No channel data loss'}}
        self.assertEqual(fixture_.compile()['report']['source_feature_dispositions'][0]['status'],'PASS')

    def test_preflight_never_equates_structural_pass_with_gameplay_or_missing_policy(self):
        output=self.base/'scene';u.save_scene(self.scene,output,self.assets)
        before={p.name:p.read_bytes()for p in output.iterdir()if p.is_file()}
        r=preflight(output/'scene.json')
        self.assertEqual(r['levels'],{'L0':'PASS','L1':'PASS','L2':'WARN','L3':'BLOCKED','L4':'NOT TESTED'})
        self.assertFalse(r['native_entry_allowed'])
        self.assertEqual(before,{p.name:p.read_bytes()for p in output.iterdir()if p.is_file()})

    def test_partition_is_conservative_and_does_not_invent_glass_alpha_or_overlays(self):
        fixture_=bridge_fixture.UniversalSceneBridgeTests();fixture_.setUp();self.addCleanup(fixture_.doCleanups)
        mesh=fixture_.scene['meshes'][0]
        mesh['positions'].append([1.,1.,0.]);mesh['normals'].append([0.,0.,1.]);mesh['uvs'].append([1.,1.])
        mesh['triangles'].append([1,3,2]);fixture_.save();compiled=fixture_.compile()
        doc={'schema':sem.SCHEMA,'source_scene_sha256':fixture_.profile['source_scene_sha256'],
             'claims':[self.claim('opaque_body',[0]),self.claim('glass',[1]),self.claim('damage_eligible')]}
        parts,bindings=sem.partition(compiled,fixture_.scene,doc)
        self.assertEqual(sum(len(p.geometry.triangles)for p in parts),sum(len(p.geometry.triangles)for p in compiled['complete_parts']))
        glass=parts[next(b['part']for b in bindings if b['role']=='glass')]
        self.assertFalse(glass.alpha);self.assertTrue(all(v.color[3]==255 for v in glass.geometry.vertices))
        self.assertFalse(any(b['role']=='damage_eligible'for b in bindings))
        before=[tuple(p.geometry.vertices[i].position for i in face)for p in compiled['complete_parts']for face in p.geometry.triangles]
        after=[tuple(p.geometry.vertices[i].position for i in face)for p in parts for face in p.geometry.triangles]
        self.assertCountEqual(before,after)

    def test_unselected_lod_material_is_retained_without_becoming_an_active_blocker(self):
        fixture_=bridge_fixture.UniversalSceneBridgeTests();fixture_.setUp();self.addCleanup(fixture_.doCleanups)
        mesh=copy.deepcopy(fixture_.scene['meshes'][0]);mesh.update(id='unused-lod',material_id='unused-material')
        material=copy.deepcopy(fixture_.scene['materials'][0]);material.update(id='unused-material',raw_fields=[{'texture_bindings':['texture','texture']}])
        fixture_.scene['meshes'].append(mesh);fixture_.scene['materials'].append(material);fixture_.save()
        fixture_.profile['wheel_slots']={k.replace('-','_'):v for k,v in fixture_.profile['wheel_slots'].items()}
        fixture_.profile['canonical_wheel_slot']='front_left'
        r=preflight(fixture_.path/'scene.json',profile=fixture_.profile)
        self.assertTrue(r['native_geometry_compiler_allowed'])
        self.assertEqual(r['issues'][0]['status'],'NOT TESTED')
        self.assertFalse(r['native_entry_allowed']);self.assertEqual(r['levels']['L4'],'NOT TESTED')

    def test_explicit_uv_flip_is_verified_reversibly_without_claiming_unchanged_uvs(self):
        from dataclasses import replace
        from master_rallye.source_qualification import conservation
        fixture_=bridge_fixture.UniversalSceneBridgeTests();fixture_.setUp();self.addCleanup(fixture_.doCleanups)
        fixture_.profile['uv_v_policy']='flip';compiled=fixture_.compile()
        report=conservation(fixture_.scene,compiled)
        self.assertFalse(report['uvs_preserved']);self.assertTrue(report['uv_conversion_reversible'])
        part=compiled['complete_parts'][0];vertices=list(part.geometry.vertices)
        vertices[0]=replace(vertices[0],uvs=((.25,.75),))
        compiled['complete_parts'][0]=replace(part,geometry=replace(part.geometry,vertices=tuple(vertices)))
        with self.assertRaisesRegex(ValueError,'UV conservation'):conservation(fixture_.scene,compiled)


if __name__=='__main__':unittest.main()
