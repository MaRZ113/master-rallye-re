"""Pilot admission, immutable snapshots and collision fit rebase guards."""
import copy
from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from master_rallye import source_garage_pilot as pilot
from master_rallye import universal_vehicle_scene as uvs
from master_rallye.addon_sdk.physics_collision import rebase_unchanged_core
from master_rallye.scene_dx_writer import write_scene_dx
from tests.synthetic.test_universal_vehicle_scene import fixture
from tests.synthetic.test_gt4_material_pipeline import scene as native_scene


class SourceGaragePilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.original=self.root/'game';self.original.mkdir()
        self.scene,self.assets=fixture(self.original)

    def test_fresh_output_cannot_overlap_any_configured_input_or_ancestor(self):
        other=self.root/'other-game';other.mkdir()
        self.scene['source']['protected_roots']=[str(self.original),str(other)]
        for path in (other/'new',self.original/'new',self.root):
            with self.subTest(path=path),self.assertRaises(ValueError):pilot._admit_output(path,self.scene,[])
        self.assertEqual(pilot._admit_output(self.root/'private',self.scene,[]),self.root/'private')

    def test_validated_scene_snapshot_is_exact_and_leaves_original_bytes_mtimes(self):
        uvs.save_scene(self.scene,self.root/'neutral',self.assets)
        before={p:(p.read_bytes(),p.stat().st_mtime_ns)for p in (self.root/'neutral').rglob('*')if p.is_file()}
        copied=pilot._copy_scene(self.root/'neutral/scene.json',self.root/'copy')
        self.assertEqual(uvs.load_scene(copied),self.scene)
        for path,expected in before.items():
            self.assertEqual((path.read_bytes(),path.stat().st_mtime_ns),expected)
            self.assertEqual((copied.parent/path.relative_to(self.root/'neutral')).read_bytes(),expected[0])

    def test_corrupted_sidecar_fails_before_snapshot_is_created(self):
        uvs.save_scene(self.scene,self.root/'neutral',self.assets)
        (self.root/'neutral/textures/pixel.rgba').write_bytes(b'bad')
        with self.assertRaises(ValueError):pilot._copy_scene(self.root/'neutral/scene.json',self.root/'copy')
        self.assertFalse((self.root/'copy').exists())

    def test_unreviewed_title_or_pod_is_rejected(self):
        uvs.save_scene(self.scene,self.root/'neutral',self.assets)
        with self.assertRaisesRegex(ValueError,'catalog'):pilot.pilot_profile(self.root/'neutral/scene.json')
        self.scene['source']['catalog']=pilot.CATALOG
        uvs.save_scene(self.scene,self.root/'neutral2',self.assets)
        with self.assertRaisesRegex(ValueError,'revision'):pilot.pilot_profile(self.root/'neutral2/scene.json')

    def test_material_baseline_does_not_make_roof_alpha_from_glass_name(self):
        self.scene['source'].update(catalog=pilot.CATALOG,pod={'sha256':pilot.POD_SHA256})
        self.scene['meshes'][0]['source']['member_sha256']=pilot.BODY_SHA256
        self.scene['selection']={'wheel_detail':'16','body_detail':2}
        self.scene['materials'][0]['source']={'object_name':'GlassE'}
        self.scene['nodes'][0]['role']='body'
        uvs.save_scene(self.scene,self.root/'neutral',self.assets)
        policy=pilot.pilot_profile(self.root/'neutral/scene.json')
        self.assertEqual(policy['materials']['material']['mode'],'opaque')
        self.assertNotIn('alpha_override',policy['materials']['material'])
        self.assertEqual(policy['authoring_transform'][11],-.10668)

    def test_physics_changes_only_measured_spans_radius_and_qualified_drive_with_native_reference(self):
        self.scene['measurements']={'wheelbase_static_metres':2.706624,'front_track_metres':1.505712,'rear_track_metres':1.496568}
        self.scene['source']['catalog_original']={'raw_lines':[
            {'line':91,'text':'faxle.torque_pct'},{'line':92,'text':'0.000000'},
            {'line':93,'text':'raxle.torque_pct'},{'line':94,'text':'1.000000'}]}
        with patch('master_rallye.addon_sdk.project.read_sma_member',return_value=b'synthetic original XML'):
            profile=pilot._physics(Path('never-opened'),self.scene)
        self.assertTrue(all(key.startswith('Dimensions/')or key=='Engine/DriveType'for values in profile['overrides'].values()for key in values))
        self.assertEqual(profile['overrides']['DataGame/vehicles.xml']['Engine/DriveType'],1)
        self.assertEqual(profile['ride_height_reference_m'],{'Front':.18288,'Rear':.18288})
        self.assertEqual(profile['ride_height_reference_binding'],'registry_name')
        self.assertNotIn('Chassis/TotalMass',next(iter(profile['overrides'].values())))

    def test_source_axle_torque_split_is_authority_not_unrelated_drive_enum(self):
        self.scene['source']['catalog_original']={'raw_lines':[
            {'line':1,'text':'drive_type'},{'line':2,'text':'0'},
            {'line':91,'text':'faxle.torque_pct'},{'line':92,'text':'0.000000'},
            {'line':93,'text':'raxle.torque_pct'},{'line':94,'text':'1.000000'}]}
        self.assertEqual(pilot._drive_type(self.scene),1)
        self.scene['source']['catalog_original']['raw_lines'][3]['text']='0.500000'
        with self.assertRaisesRegex(ValueError,'torque split changed'):pilot._drive_type(self.scene)


class CollisionCoreRebaseTests(unittest.TestCase):
    def setUp(self):
        self.template,self.part=native_scene()
        self.before=write_scene_dx(self.template,[self.part,self.part])
        self.definition={'source_sha256':hashlib.sha256(self.before).hexdigest(),'core_draw_indices':[0],
                         'padding_m':[0.,0.,0.],'evidence':'synthetic core shell selection'}

    def test_crew_or_appearance_outside_core_can_repin_without_mutating_definition(self):
        geometry=replace(self.part.geometry,vertices=tuple(replace(v,position=(v.position[0]+.1,*v.position[1:]))for v in self.part.geometry.vertices))
        after=write_scene_dx(self.template,[replace(self.part,textures=('new-paint','Null','Null')),replace(self.part,geometry=geometry)])
        before=copy.deepcopy(self.definition)
        rebound=rebase_unchanged_core(self.before,after,self.definition)
        self.assertEqual(self.definition,before)
        self.assertEqual(rebound,{**before,'source_sha256':hashlib.sha256(after).hexdigest()})

    def test_changed_core_geometry_and_wrong_original_hash_fail_closed(self):
        geometry=replace(self.part.geometry,vertices=tuple(replace(v,position=(v.position[0]+.1,*v.position[1:]))for v in self.part.geometry.vertices))
        after=write_scene_dx(self.template,[replace(self.part,geometry=geometry),self.part])
        with self.assertRaisesRegex(ValueError,'core geometry'):rebase_unchanged_core(self.before,after,self.definition)
        with self.assertRaisesRegex(ValueError,'baseline hash'):rebase_unchanged_core(self.before,self.before,{**self.definition,'source_sha256':'0'*64})

    def test_invalid_model_is_rejected(self):
        with self.assertRaises((ValueError,EOFError)):rebase_unchanged_core(self.before,b'bad',self.definition)
