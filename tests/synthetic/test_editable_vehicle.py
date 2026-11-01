import copy
import tempfile
from pathlib import Path
import unittest
from master_rallye import universal_vehicle_scene as u
from master_rallye.editable_vehicle import EditableVehicle,build_fixture,copy_native_material
from test_universal_vehicle_scene import fixture
from test_gt4_material_pipeline import scene as native_template


class EditableTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        donor=self.root/'donor';donor.mkdir();self.scene,self.assets=fixture(donor)
        node=copy.deepcopy(self.scene['nodes'][0]);node.update(id='wheel',mesh_ids=[self.scene['meshes'][0]['id']],role='wheel');node['local_transform'][3]=2
        self.scene['nodes'].append(node)
        u.save_scene(self.scene,self.root/'source',self.assets);self.source=self.root/'source/scene.json';self.before=self.source.read_bytes()
        self.project=EditableVehicle.create(self.source)
        self.mid=self.scene['meshes'][0]['id']

    def test_transactions_undo_redo_restore_and_atomic_reopen(self):
        p=self.project;p.edit({'op':'vertex','mesh':self.mid,'index':0,'value':[.1,.2,.3]})
        p.save(self.root/'edited.json');reopened=EditableVehicle.open(self.root/'edited.json')
        self.assertEqual(p.evaluate(),reopened.evaluate());self.assertEqual(self.source.read_bytes(),self.before)
        p.undo();self.assertNotEqual(p.evaluate(),reopened.evaluate());p.redo();self.assertEqual(p.evaluate(),reopened.evaluate())
        p.restore();self.assertEqual(p.diagnostics()['source_fidelity'],'PASS')

    def test_invalid_topology_rolls_back_without_losing_journal(self):
        before=copy.deepcopy(self.project.document)
        for op in({'op':'delete_vertex','mesh':self.mid,'index':0}, {'op':'add_face','mesh':self.mid,'vertices':[0,1,99]},
                   {'op':'vertex','mesh':self.mid,'index':True,'value':[0,0,0]}):
            with self.assertRaises(ValueError):self.project.edit(op)
            self.assertEqual(self.project.document,before)

    def test_user_vertices_faces_and_meshes_need_no_donor_face_ids(self):
        p=self.project;p.edit({'op':'add_vertex','mesh':self.mid,'positions':[1,1,1],'normals':[0,1,0],'uvs':[0,1]})
        index=len(p.evaluate()['meshes'][0]['positions'])-1
        p.edit({'op':'add_face','mesh':self.mid,'vertices':[0,1,index]})
        mesh=p.evaluate()['meshes'][0];self.assertTrue(mesh['face_ids'][-1].startswith('authored-'))
        geometry={k:copy.deepcopy(mesh[k])for k in('positions','normals','uvs','triangles','material_id')}
        p.edit({'op':'add_mesh','geometry':geometry,'name':'Wheel backing'})
        self.assertTrue(p.evaluate()['meshes'][-1]['source']['user_created'])

    def test_stable_faces_and_effects_do_not_migrate_after_delete(self):
        p=self.project;face=p.evaluate()['meshes'][0]['face_ids'][0]
        p.edit({'op':'add_face','mesh':self.mid,'vertices':[0,2,1]})
        p.edit({'op':'glow','mesh':self.mid,'faces':[face],'trigger':'brake','rgba':[255,30,10,255]})
        p.edit({'op':'delete_faces','mesh':self.mid,'faces':[face]})
        self.assertNotIn(face,p.evaluate()['authored_effects'])
        with self.assertRaises(ValueError):p.edit({'op':'material','mesh':self.mid,'faces':[face],'rule':{}})

    def test_source_fidelity_is_strict_and_other_modes_are_explicit(self):
        p=EditableVehicle.create(self.source,'Source Fidelity');self.assertEqual(p.evaluate(),self.scene)
        with self.assertRaises(ValueError):p.edit({'op':'vertex','mesh':self.mid,'index':0,'value':[1,2,3]})
        self.assertEqual(p.document['cursor'],0)

    def test_assign_material_glow_and_build_shared_native_fixture(self):
        p=self.project
        p.edit({'op':'material','mesh':self.mid,'rule':{'mode':'opaque','role':'opaque_body','evidence':'Deliberate synthetic MR Classic material'}})
        face=p.evaluate()['meshes'][0]['face_ids'][0]
        p.edit({'op':'glow','mesh':self.mid,'faces':[face],'trigger':'brake','rgba':[255,20,10,255]})
        template=native_template()[0];first=build_fixture(p,self.root/'one',template,scale=1)
        second=build_fixture(p,self.root/'two',template,scale=1)
        self.assertEqual(first,second);self.assertFalse(first['runtime_qualified']);self.assertEqual(self.source.read_bytes(),self.before)

    def test_unassigned_material_remains_repairable_not_blanket_bypass(self):
        with self.assertRaisesRegex(ValueError,'Assign a native material'):
            build_fixture(self.project,self.root/'bad',native_template()[0],scale=1)
        with self.assertRaisesRegex(ValueError,'protected source'):self.project.save(self.root/'source/edited.json')

    def test_changed_source_reopen_rejected_even_for_customized(self):
        p=self.root/'edited.json';self.project.save(p);self.source.write_bytes(self.before+b' ')
        with self.assertRaisesRegex(ValueError,'identity changed'):EditableVehicle.open(p)

    def test_explicit_winding_preserves_face_ownership_and_is_undoable(self):
        p=self.project;before=p.evaluate();ids=before['meshes'][0]['face_ids'][:]
        p.edit({'op':'orient_winding','mesh':self.mid});after=p.evaluate()
        self.assertEqual(ids,after['meshes'][0]['face_ids']);p.undo();self.assertEqual(before,p.evaluate())

    def test_bulk_edit_is_one_undo_transaction_and_redo_replays_it(self):
        p=self.project;before=p.evaluate()
        p.edit_many([{'op':'vertex','mesh':self.mid,'index':0,'value':[1,2,3]},
                     {'op':'uv','mesh':self.mid,'index':0,'value':[.2,.4]}])
        after=p.evaluate();p.undo();self.assertEqual(p.evaluate(),before);p.redo();self.assertEqual(p.evaluate(),after)
        p.undo();p.edit({'op':'vertex','mesh':self.mid,'index':0,'value':[5,6,7]});self.assertEqual(len(p.document['operations']),1)
        p.restore();p.document['mode']='Source Fidelity'
        with self.assertRaisesRegex(ValueError,'derived workflow'):p.redo()
        self.assertEqual(p.document['cursor'],0)

    def test_partial_reflection_splits_only_receiving_derived_group(self):
        p=self.project;p.edit({'op':'add_face','mesh':self.mid,'vertices':[0,2,1]});face=p.evaluate()['meshes'][0]['face_ids'][0]
        p.edit({'op':'material','mesh':self.mid,'faces':[face],'rule':{'mode':'opaque','role':'reflective_paint','evidence':'Intentional partial authored section'}})
        derived=p.evaluate();self.assertEqual(len(derived['meshes']),2)
        self.assertEqual(len(derived['meshes'][1]['triangles']),1)
        self.assertNotEqual(derived['meshes'][0]['material_id'],derived['meshes'][1]['material_id'])
        self.assertEqual(self.source.read_bytes(),self.before)

    def test_native_build_reverifies_parent_after_preview_cached_edit(self):
        self.project.edit({'op':'material','mesh':self.mid,'rule':{'mode':'opaque','role':'opaque_body','evidence':'Explicit test adaptation'}})
        self.source.write_bytes(self.before+b' ')
        with self.assertRaisesRegex(ValueError,'parent changed'):build_fixture(self.project,self.root/'new',native_template()[0],scale=1)

    def test_new_component_budget_is_checked_before_copying_large_arrays(self):
        geometry={'positions':[[0,0,0]]*u.MAX_VERTICES,'normals':[[0,1,0]]*u.MAX_VERTICES,
                  'uvs':[[0,0]]*u.MAX_VERTICES,'triangles':[[0,1,2]],'material_id':'material'}
        before=copy.deepcopy(self.project.document)
        with self.assertRaisesRegex(ValueError,'allocation budget'):self.project.edit({'op':'add_mesh','geometry':geometry})
        self.assertEqual(self.project.document,before)

    def test_copy_native_reference_rejects_missing_draw_and_pins_supported_state(self):
        from master_rallye.dx import parse_dx_bytes
        from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
        from master_rallye.topology_writer import source_geometry
        template=native_template()[0];geometry=source_geometry(parse_dx_bytes(template))[0]
        path=self.root/'reference.dx';path.write_bytes(write_scene_dx(template,[ScenePart(geometry,('test','Null','Null'))]));index=0
        rule,references=copy_native_material(path,index,'opaque_body')
        self.assertEqual(rule['mode'],'opaque');self.assertIn(u.sha(path.read_bytes()),rule['evidence']);self.assertEqual(references,{})
        with self.assertRaises(ValueError):copy_native_material(path,9999,'opaque_body')


if __name__=='__main__':unittest.main()
