import copy
from pathlib import Path
import tempfile
import struct
import unittest

from master_rallye.demo_vehicle_audit import surfaces,comparison,dx_evidence,signed_axis_alignment,transform_surface
from master_rallye.addon_sdk.heritage_source import inspect_family,compare_editions,family_folders
from tests.synthetic.test_heritage_source import fixture


class DemoAuditTests(unittest.TestCase):
    def test_collision_comparison_needs_no_optional_cooker_oracle(self):
        from types import SimpleNamespace as NS
        from master_rallye.demo_dx import _representation
        geometry=NS(vertex_count=3,triangle_count=1,vertices=((0.,0.,0.),)*3,triangles=((0,1,2),))
        hull=NS(geometry_a=geometry,geometry_b=geometry,referenced_vertex_indices=(0,1,2),
                edges=((0,1),(1,2),(2,0)),edge_face_adjacency=((0,),)*3,
                face_loop_indices=((0,1,2),),face_scalars=(1.,),
                face_descriptors=(NS(primary_indices=(0,1,2),secondary_indices=(3,4,5)),))
        other=copy.deepcopy(hull);other.face_descriptors[0].secondary_indices=(5,3,4)
        result=_representation(hull,other)
        self.assertEqual(result['core_topology']['classification'],'CORE_TOPOLOGY_EQUAL')
        self.assertFalse(result['secondary_descriptors_equal'])
        self.assertTrue(result['secondary_descriptor_multisets_equal_per_face'])
        self.assertEqual(result['secondary_descriptor_analysis']['semantics'],'UNRESOLVED')

    def shape(self,points=None,triangles=None,uv=None):
        points=points or [(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
        triangles=triangles or [(0,1,2)]
        return surfaces(points,[(0.,0.,1.)]*3,b'\xff'*12,[uv or [(0.,0.),(1.,0.),(0.,1.)]],triangles,[b'paint']*len(triangles))

    def test_vertex_reorder_and_cyclic_corner_rotation_do_not_change_evidence(self):
        a=self.shape();b=self.shape([(0.,1.,0.),(0.,0.,0.),(1.,0.,0.)],[(2,0,1)],[(0.,1.),(0.,0.),(1.,0.)])
        self.assertEqual(a['surface_sha256'],b['surface_sha256'])
        self.assertEqual(a['uv_surface_sha256'],b['uv_surface_sha256'])
        self.assertEqual(comparison(a,b)['kind'],'EXACT_DECODED_SURFACE')

    def test_winding_uv_and_material_changes_remain_distinguishable(self):
        a=self.shape();b=self.shape(triangles=[(0,2,1)])
        self.assertEqual(comparison(a,b)['kind'],'SAME_SURFACE_WINDING_DIFFERS')
        c=self.shape(uv=[(.5,0.),(1.,0.),(0.,1.)])
        self.assertEqual(a['surface_sha256'],c['surface_sha256'])
        self.assertNotEqual(a['uv_surface_sha256'],c['uv_surface_sha256'])
        d=surfaces([(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)],[(0.,0.,1.)]*3,b'\xff'*12,[[(0.,0.),(1.,0.),(0.,1.)]],[(0,1,2)],[b'glass'])
        self.assertNotEqual(a['material_surface_sha256'],d['material_surface_sha256'])

    def test_duplicate_triangles_and_invalid_indices_are_not_silently_dropped(self):
        a=self.shape();b=self.shape(triangles=[(0,1,2),(0,1,2)])
        self.assertNotEqual(a['surface_sha256'],b['surface_sha256'])
        with self.assertRaisesRegex(ValueError,'index'):self.shape(triangles=[(0,1,3)])

    def test_native_reader_signature_is_deterministic(self):
        a=dx_evidence(fixture(),'one');b=dx_evidence(fixture(),'two')
        self.assertEqual(a['surface_sha256'],b['surface_sha256'])
        self.assertEqual(a['status'],'PASS_DRAW_SURFACES')

    def test_stale_global_cache_does_not_invent_render_geometry_change(self):
        from master_rallye.dx import parse_dx_bytes
        raw=fixture();m=parse_dx_bytes(raw);changed=bytearray(raw)
        struct.pack_into('<I',changed,m.global_index_table.data_offset,0)
        a=dx_evidence(raw,'original');b=dx_evidence(bytes(changed),'stale global cache')
        self.assertEqual(a['surface_sha256'],b['surface_sha256'])
        self.assertFalse(b['global_table_agrees'])

    def test_missing_texture_does_not_crash_or_claim_shared_fidelity(self):
        with tempfile.TemporaryDirectory()as td:
            root=Path(td)
            for name in ('car.dx','complete.dx','wheel.dx'):(root/name).write_bytes(fixture())
            row=inspect_family(root)
            self.assertIsNone(row['textures']['base-tga']['source'])
            result=compare_editions([{'edition':'demo','vehicles':[row]}],{'vehicles':[copy.deepcopy(row)]})
            self.assertEqual(result[0]['classification'],'SHARED_MODELS_TEXTURES_UNRESOLVED')
            (root/'base-tga.dxt').write_bytes(b'bad texture')
            row=inspect_family(root)
            self.assertFalse(row['qualified_for_staging'])
            self.assertEqual(row['textures']['base-tga']['policy'],'INVALID_TEXTURE')

    def test_deep_nested_and_gxm_only_families_are_discovered(self):
        with tempfile.TemporaryDirectory()as td:
            root=Path(td)
            for name,model in [('A','car.dx'),('Original/B/C','car.gxm'),('A/Nested','wheel.gxm')]:
                path=root/name;path.mkdir(parents=True,exist_ok=True);(path/model).write_bytes(b'not parsed in discovery')
            self.assertEqual({p.relative_to(root).as_posix()for p in family_folders(root)}, {'A','Original/B/C','A/Nested'})

    def test_original_gxm_texture_paths_resolve_without_fake_suffix_gaps(self):
        from tools.audit_demo_vehicles import texture_stem,texture_inventory
        self.assertEqual(texture_stem('D:/project/Vehicles/A/Black-tga.gxi'),'black-tga')
        self.assertEqual(texture_stem('D:\\project\\Paint.tga'),'paint-tga')
        self.assertEqual(texture_stem('black-tga.dxt'),'black-tga')
        self.assertEqual(texture_inventory({}, {'car.gxm':{'source_materials':[{'textures':[{'reference':'Null'}]}]}}),{})

    def test_small_position_changes_are_measured_without_promoting_exact_match(self):
        a=self.shape();b=self.shape([(0.,0.,0.),(1.001,0.,0.),(0.,1.,0.)])
        result=comparison(a,b)
        self.assertNotEqual(result['kind'],'EXACT_DECODED_SURFACE')
        self.assertGreater(result['sampled_unscaled_rms'],0)

    def test_axis_alignment_is_measured_and_does_not_modify_source(self):
        points=[(.1+i*.17,.2+i*i*.03,.3+(i%4)*.23)for i in range(12)]
        tris=[(i,i+1,i+2)for i in range(0,12,3)]
        source=surfaces(points,[],b'',[],tris)
        target=surfaces([(p[0],p[2],-p[1])for p in points],[],b'',[],tris)
        alignment=signed_axis_alignment(source,target)
        self.assertEqual(alignment['permutation'],[0,2,1])
        self.assertEqual(alignment['signs'],[1,1,-1])
        transformed=transform_surface(source,alignment)
        self.assertEqual(transformed['surface_sha256'],target['surface_sha256'])
        self.assertEqual(source['_positions'],points)


if __name__=='__main__':unittest.main()
