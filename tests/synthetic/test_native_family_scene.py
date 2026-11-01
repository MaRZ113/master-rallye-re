from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_gt4_material_pipeline import scene
from master_rallye import universal_vehicle_scene as u
from master_rallye.native_family_scene import snapshot
from master_rallye.universal_scene_bridge import _dxt
from master_rallye.dx import parse_dx_bytes


class NativeMigrationTests(unittest.TestCase):
    def test_snapshot_retains_original_native_inputs_and_explicit_instances(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);native=root/'native';native.mkdir();raw=scene()[0];model=parse_dx_bytes(raw)
            for name in('car.dx','complete.dx','wheel.dx'):(native/name).write_bytes(raw)
            for draw in model.physical_draws:
                for name in draw.texture_tuple:
                    if name!='Null':(native/(name+'.dxt')).write_bytes(_dxt(1,1,bytes([255]*4),'preserve'))
            explicit={'race_wheel_instances':[{'translation':[x,0,z],'rotation_y':0.,'scale':[1,1,1]}for x,z in((1,1),(-1,1),(1,-1),(-1,-1))],
                      'provenance':'Explicit synthetic MR pose; not original GT recovery'}
            (native/'preview-profile.json').write_bytes(u.canonical(explicit))
            before={p.name:p.read_bytes()for p in native.iterdir()}
            first=snapshot(native,root/'first');second=snapshot(native,root/'second')
            self.assertEqual(first['scene_sha256'],second['scene_sha256'])
            loaded=u.load_scene(root/'first/scene.json');self.assertEqual(len(loaded['nodes']),5)
            self.assertTrue(all('not newly recovered' in n['transform_evidence']for n in loaded['nodes'][1:]))
            self.assertEqual(before,{p.name:p.read_bytes()for p in native.iterdir()})
            (native/'car.dx').write_bytes(b'bad')
            with self.assertRaises(Exception):snapshot(native,root/'bad')


if __name__=='__main__':unittest.main()
