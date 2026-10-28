"""Neutral-scene invariants and hostile metadata; all assets are invented."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from master_rallye import universal_vehicle_scene as uvs


def fixture(root):
    pixels=bytes((90,80,70,255))
    scene={'schema':uvs.SCHEMA,'source':{'root':str(root)},'metadata':{'name':'synthetic'},
           'coordinate_system':{'source_to_normalized':[2.,0.,0.,0.,0.,2.,0.,0.,0.,0.,-2.,0.,0.,0.,0.,1.],
                                'interpretation_status':'explicit test transform','evidence':['invented fixture']},
           'textures':[{'id':'texture','width':1,'height':1,'rgba_path':'textures/pixel.rgba',
                        'rgba_sha256':uvs.sha(pixels),'source_channels':{'mode':'RGBA'}}],
           'materials':[{'id':'material','diffuse_texture_id':'texture','raw_fields':['unknown'],
                         'unsupported':['original lighting']}],
           'meshes':[{'id':'mesh','positions':[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],
                      'normals':[[0.,0.,1.]]*3,'uvs':[[0.,0.],[1.,0.],[0.,1.]],
                      'triangles':[[0,1,2]],'material_id':'material','source':{'record':7}}],
           'nodes':[{'id':'node','parent_id':None,'mesh_ids':['mesh'],'visible':True,'source_visible':True,
                     'local_transform':uvs.IDENTITY[:],'source_local_transform':None,
                     'transform_evidence':'derived grouping; no original matrix'}],
           'unknown_semantics':[{'id':'glass','status':'UNSUPPORTED','meaning':'unknown source alpha'}]}
    return scene,{'textures/pixel.rgba':pixels}


def rebind_manifest(directory, name, data):
    """Model a self-consistent transport manifest, not trustworthy source claims."""
    (directory/name).write_bytes(data)
    manifest=json.loads((directory/'manifest.json').read_bytes())
    manifest['files'][name]={'bytes':len(data),'sha256':uvs.sha(data)}
    if name=='scene.json':manifest['scene_sha256']=uvs.sha(data)
    (directory/'manifest.json').write_bytes(uvs.canonical(manifest))


class UniversalVehicleSceneTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.source=self.base/'source';self.source.mkdir()
        self.original=self.source/'original';self.original.write_bytes(b'private original')
        self.scene,self.assets=fixture(self.source)

    def save(self, scene=None, assets=None, name='scene'):
        output=self.base/name
        uvs.save_scene(self.scene if scene is None else scene,output,self.assets if assets is None else assets)
        return output

    def test_roundtrip_is_deterministic_preserves_unknowns_and_raw_coordinates(self):
        before=copy.deepcopy(self.scene);a=self.save();b=self.save(name='second')
        restored=uvs.load_scene(a/'scene.json')
        self.assertEqual(restored,before);self.assertEqual(self.scene,before)
        for path in a.rglob('*'):
            if path.is_file():self.assertEqual(path.read_bytes(),(b/path.relative_to(a)).read_bytes())
        self.assertIsNone(restored['nodes'][0]['source_local_transform'])
        self.assertEqual(restored['meshes'][0]['positions'][1],[1.,0.,0.])
        self.assertEqual(uvs.transform_point(restored['coordinate_system']['source_to_normalized'],[1,2,3]),[2,4,-6])
        self.assertEqual(restored['unknown_semantics'][0]['status'],'UNSUPPORTED')
        self.assertEqual(self.original.read_bytes(),b'private original')

    def test_corrupt_sidecar_or_scene_cannot_reopen(self):
        output=self.save();(output/'textures/pixel.rgba').write_bytes(b'xxxx')
        with self.assertRaises(ValueError):uvs.load_scene(output/'scene.json')
        (output/'textures/pixel.rgba').write_bytes(self.assets['textures/pixel.rgba'])
        (output/'scene.json').write_bytes((output/'scene.json').read_bytes()+b' ')
        with self.assertRaises(ValueError):uvs.load_scene(output/'scene.json')

    def test_manifest_cannot_reassign_texture_content_without_source_binding(self):
        output=self.save();rebind_manifest(output,'textures/pixel.rgba',b'xxxx')
        with self.assertRaisesRegex(ValueError,'unbound texture'):uvs.load_scene(output/'scene.json')

    def test_json_duplicate_keys_and_nonfinite_constants_fail_even_with_rebound_manifest(self):
        for index,raw in enumerate((b'{"schema":"wrong","schema":"universal-vehicle-scene/1"}',b'{"test":NaN}',b'{"test":Infinity}',b'{"test":1e999}')):
            output=self.save(name='json'+str(index));rebind_manifest(output,'scene.json',raw)
            with self.assertRaises(ValueError):uvs.load_scene(output/'scene.json')

    def test_invalid_indices_uv_and_material_bindings_fail_before_output_creation(self):
        for field,value in (('triangles',[[0,1,3]]),('triangles',[[0,True,2]]),('uvs',[[0,0]]),
                            ('uvs',[[0,0],[1,float('nan')],[0,1]]),('material_id','absent'),('material_id',[])):
            scene=copy.deepcopy(self.scene);scene['meshes'][0][field]=value
            with self.assertRaises(ValueError):uvs.save_scene(scene,self.base/'bad',self.assets)
            self.assertFalse((self.base/'bad').exists())

    def test_bad_material_texture_bump_and_hash_metadata_reject(self):
        for field,value in (('diffuse_texture_id','absent'),('diffuse_texture_id',[]),('bump_texture_id','absent')):
            scene=copy.deepcopy(self.scene);scene['materials'][0][field]=value
            with self.assertRaises(ValueError):uvs.validate_scene(scene)
        scene=copy.deepcopy(self.scene);scene['textures'][0]['rgba_sha256']=None
        with self.assertRaises(ValueError):uvs.validate_scene(scene)

    def test_malformed_records_and_missing_absolute_source_root_raise_validation_error(self):
        for category in ('meshes','nodes','textures','materials'):
            scene=copy.deepcopy(self.scene);scene[category]=[None]
            with self.assertRaises(ValueError):uvs.validate_scene(scene)
        for root in (None,'','relative',123,'bad\0root'):
            scene=copy.deepcopy(self.scene);scene['source']['root']=root
            with self.assertRaises(ValueError):uvs.validate_scene(scene)

    def test_hierarchy_cycle_missing_parent_and_singular_matrices_reject(self):
        scene=copy.deepcopy(self.scene);node=scene['nodes'][0];node['parent_id']='node'
        with self.assertRaises(ValueError):uvs.validate_scene(scene)
        node['parent_id']='absent'
        with self.assertRaises(ValueError):uvs.validate_scene(scene)
        node['parent_id']=None;node['local_transform']=[0.]*16
        with self.assertRaises(ValueError):uvs.validate_scene(scene)
        node['local_transform']=uvs.IDENTITY[:];node['source_local_transform']=[0.]*16
        with self.assertRaises(ValueError):uvs.validate_scene(scene)

    def test_aggregate_animation_and_texture_budgets_do_not_reset_per_record(self):
        scene=copy.deepcopy(self.scene);scene['meshes'][0]['animation_frames']=[[[0.]*8]*3]
        second=copy.deepcopy(scene['meshes'][0]);second['id']='second';scene['meshes'].append(second)
        with patch.object(uvs,'MAX_VERTICES',5):
            # Reduce static vertices in each mesh so the combined animation
            # allocation, rather than base geometry, crosses the same budget.
            for mesh in scene['meshes']:
                mesh['positions']=mesh['positions'][:1];mesh['normals']=mesh['normals'][:1];mesh['uvs']=mesh['uvs'][:1]
                mesh['triangles']=[[0,0,0]];mesh['animation_frames']=[[[0.]*8] for _ in range(3)]
            with self.assertRaisesRegex(ValueError,'animation'):uvs.validate_scene(scene)
        with patch.object(uvs,'MAX_TEXTURE_BYTES',3):
            with self.assertRaises(ValueError):uvs.validate_scene(self.scene)

    def test_frame_type_errors_and_global_output_budget_are_bounded(self):
        scene=copy.deepcopy(self.scene);scene['meshes'][0]['animation_frames']=[None]
        with self.assertRaises(ValueError):uvs.validate_scene(scene)
        with patch.object(uvs,'MAX_OUTPUT_BYTES',8):
            with self.assertRaises(ValueError):self.save()
        self.assertFalse((self.base/'scene').exists())

    def test_reserved_case_alias_and_file_directory_paths_reject_before_writes(self):
        for bad in ({'SCENE.JSON':b'x'},{'textures':b'x'},{'scene.json/child':b'x'},
                    {'TEXTURES/PIXEL.RGBA':b'x'},{'../escape':b'x'},{'textures/NUL':b'x'},
                    {'trailingdot.':b'x'},{'trailing space ':b'x'}):
            with self.assertRaises(ValueError):self.save(assets={**self.assets,**bad})
            self.assertFalse((self.base/'scene').exists())

    def test_source_and_all_other_protected_roots_are_never_output_destinations(self):
        for target in (self.source,self.source/'child',self.base):
            with self.assertRaises(ValueError):uvs.save_scene(self.scene,target,self.assets)
        protected=self.base/'accepted';protected.mkdir();before=self.original.stat()
        with self.assertRaises(ValueError):uvs.save_scene(self.scene,protected/'new',self.assets,protected_roots=[protected])
        self.scene['source']['protected_roots']=[str(protected)]
        with self.assertRaises(ValueError):uvs.save_scene(self.scene,protected/'new',self.assets)
        self.assertEqual(self.original.read_bytes(),b'private original')
        self.assertEqual(self.original.stat().st_mtime_ns,before.st_mtime_ns)

    def test_links_in_source_reader_or_output_ancestors_are_rejected(self):
        link=self.base/'linked'
        try:link.symlink_to(self.source,target_is_directory=True)
        except OSError:self.skipTest('host cannot create synthetic symlink')
        with self.assertRaises(ValueError):uvs.read_bounded(link/'original',100)
        with self.assertRaises(ValueError):uvs.save_scene(self.scene,link/'new',self.assets)

    def test_optional_raw_samples_and_palette_are_required_and_hash_bound(self):
        scene=copy.deepcopy(self.scene);samples=b'\x02\x13';palette=b'\x00\x01\x02\x03'
        scene['textures'][0]['source_channels']={'samples_per_pixel':2,'raw_sample_bytes':2,
            'raw_samples_path':'textures/raw.samples','raw_samples_sha256':uvs.sha(samples),
            'palette_bytes':4,'palette_path':'textures/raw.palette','palette_sha256':uvs.sha(palette)}
        assets={**self.assets,'textures/raw.samples':samples,'textures/raw.palette':palette}
        with self.assertRaises(ValueError):self.save(scene=scene)
        output=self.save(scene,assets)
        self.assertEqual(uvs.load_scene(output/'scene.json'),scene)
        rebind_manifest(output,'textures/raw.samples',b'xx')
        with self.assertRaisesRegex(ValueError,'unbound texture'):uvs.load_scene(output/'scene.json')
        scene['textures'][0]['source_channels']['raw_sample_bytes']=1
        with self.assertRaises(ValueError):uvs.validate_scene(scene)

    def test_original_snapshot_and_mesh_texture_provenance_are_independently_bound(self):
        scene=copy.deepcopy(self.scene);original=b'original mesh';row={'member':'MODELS/body.smf',
            'snapshot_path':'original/MODELS/body.smf','bytes':len(original),'sha256':uvs.sha(original)}
        scene['source']['resources']=[row];scene['meshes'][0]['source']={'member':row['member'],'member_sha256':row['sha256']}
        scene['textures'][0]['source']=dict(row)
        assets={**self.assets,row['snapshot_path']:original}
        output=self.save(scene,assets);self.assertEqual(uvs.load_scene(output/'scene.json'),scene)
        rebind_manifest(output,row['snapshot_path'],b'replaced mesh')
        with self.assertRaises(ValueError):uvs.load_scene(output/'scene.json')
        for target in (scene['meshes'][0]['source'],scene['textures'][0]['source']):
            key='member_sha256'if'member_sha256'in target else'sha256';old=target[key];target[key]='0'*64
            with self.assertRaises(ValueError):uvs.validate_scene(scene)
            target[key]=old
        scene['source']['resources'].append(dict(row))
        with self.assertRaises(ValueError):uvs.validate_scene(scene)


if __name__=='__main__':unittest.main()
