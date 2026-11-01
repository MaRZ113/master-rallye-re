import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_source_scene_preview import scene_fixture
from master_rallye import universal_vehicle_scene as u
from master_rallye.workshop.preview_cache import PreviewCache,SceneMemory,Task,Cancelled,identity,stage


class CacheTests(unittest.TestCase):
    def test_reuse_restart_corruption_and_force_refresh(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp)/'cache';cache=PreviewCache(root);calls=[]
            def build(folder,task):calls.append(1);(folder/'a').write_bytes(b'valid');return {'value':1}
            key=identity('fixture');p,_,hit=cache.get(key,build);self.assertFalse(hit)
            self.assertTrue(PreviewCache(root).get(key,build)[2]);self.assertEqual(len(calls),1)
            (p/'a').write_bytes(b'bad!!');self.assertFalse(cache.get(key,build)[2]);self.assertEqual(cache.stats['recovered'],1)
            self.assertFalse(cache.get(key,build,refresh=True)[2]);self.assertEqual(len(calls),3)

    def test_atomic_cancel_and_budget_never_commit_partial_outputs(self):
        with tempfile.TemporaryDirectory()as tmp:
            cache=PreviewCache(Path(tmp)/'cache',max_bytes=1024);task=Task()
            def build(folder,job):(folder/'a').write_bytes(b'partial');job.cancelled.set();return {}
            with self.assertRaises(Cancelled):cache.get(identity('cancel'),build,task=task)
            self.assertEqual([p.name for p in cache.root.iterdir()],['.lock'])
            def large(folder,job):(folder/'a').write_bytes(b'x'*2000);return {}
            with self.assertRaisesRegex(ValueError,'budget'):cache.get(identity('large'),large)
            self.assertFalse(any(p.name.startswith('.pending')for p in cache.root.iterdir()))

    def test_lru_keeps_bounded_entries(self):
        with tempfile.TemporaryDirectory()as tmp:
            cache=PreviewCache(Path(tmp)/'cache',max_bytes=1500)
            def build(folder,task):(folder/'a').write_bytes(b'x'*900);return {}
            cache.get(identity('old'),build);cache.get(identity('new'),build)
            self.assertFalse((cache.root/identity('old')).exists());self.assertTrue((cache.root/identity('new')).exists())

    def test_scene_memory_checks_all_manifest_dependencies_and_isolates_mutation(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);project,scene=scene_fixture(root)
            assets={'texture.rgba':(project/'texture.rgba').read_bytes()}
            u.save_scene(scene,root/'sealed',assets)
            path=root/'sealed/scene.json';memory=SceneMemory();first,hit=memory.load(path);self.assertFalse(hit)
            first['meshes'][0]['positions'][0][0]=999
            second,hit=memory.load(path);self.assertTrue(hit);self.assertNotEqual(second,first)
            (path.parent/'texture.rgba').write_bytes(b'xxxx')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):memory.load(path)

    def test_material_geometry_camera_and_texture_invalidation(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);project,scene=scene_fixture(root);u.save_scene(scene,root/'sealed',{'texture.rgba':(project/'texture.rgba').read_bytes()})
            cache=PreviewCache(root/'cache');options={'scene_root':root/'sealed'}
            p,_,hit=stage(cache,scene,options);self.assertFalse(hit);self.assertTrue(stage(cache,scene,options)[2])
            edited=copy.deepcopy(scene);edited['meshes'][0]['positions'][0][0]=.5
            p2,_,hit=stage(cache,edited,options);self.assertFalse(hit);self.assertNotEqual(p,p2)
            edited['materials'][0]['preview']={'opacity':.5};options['material_mode']='interpreted'
            self.assertFalse(stage(cache,edited,options)[2])
            self.assertEqual(scene['meshes'][0]['positions'][0][0],0)

    def test_cache_cannot_target_original_or_escape_with_key(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);project,scene=scene_fixture(root)
            with self.assertRaises(ValueError):PreviewCache(root/'cache').get('../bad',lambda p,t:{})
            with self.assertRaisesRegex(ValueError,'protected source'):
                stage(PreviewCache(project/'cache'),scene,{'scene_root':project})
            self.assertFalse((project/'cache').exists())


if __name__=='__main__':unittest.main()
