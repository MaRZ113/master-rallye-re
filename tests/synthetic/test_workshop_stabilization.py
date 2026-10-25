import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from master_rallye.preview_scene import stage_vehicle
from master_rallye.workshop.service import WorkshopProject
from tests.synthetic.test_workshop import family

def scene_draws(path):
    b=path.read_bytes();_,_,nt,nd=struct.unpack_from('<4I',b);offset=40;result=[]
    def string():
        nonlocal offset
        n=struct.unpack_from('<I',b,offset)[0];offset+=4;text=b[offset:offset+n].decode();offset+=n;return text
    for _ in range(nt):
        string();w,h=struct.unpack_from('<II',b,offset);offset+=8+w*h*4
    for _ in range(nd):
        name=string();values=struct.unpack_from('<Iii4I3fII',b,offset);offset+=48
        nv,ni=values[-2:];vertices=b[offset:offset+nv*36];offset+=nv*36
        indices=struct.unpack_from(f'<{ni}I',b,offset);offset+=ni*4;result.append((name,values[0],vertices,indices))
    return result

class WorkshopStabilization(unittest.TestCase):
    def test_mirror_corrects_winding_and_keeps_raw_geometry(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);family(root/'assets');config={'provenance':'synthetic reflected wheel','race_wheel_instances':[{'translation':[0,0,0],'rotation_y':0,'scale':[-1,1,1]}]}
            (root/'profile.json').write_text(json.dumps(config));report=stage_vehicle(root/'assets/car.dx',root/'scene',profile=root/'profile.json')
            rows=scene_draws(root/'scene');raw=next(d for d in rows if d[0].startswith('wheel.dx') and d[1]==3);mirror=next(d for d in rows if d[1]==5)
            self.assertEqual(mirror[3],(raw[3][0],raw[3][2],raw[3][1]));self.assertIn('@wheel0',mirror[0]);self.assertTrue(report['instance_handedness'][0]['mirrored'])
            digest=hashlib.sha256((root/'scene').read_bytes()).hexdigest();stage_vehicle(root/'assets/car.dx',root/'scene',profile=root/'profile.json');self.assertEqual(hashlib.sha256((root/'scene').read_bytes()).hexdigest(),digest)

    def test_preview_edit_persists_without_touching_runtime_resources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);family(root/'source');p=WorkshopProject.create(root/'source',root/'project');before={f.name:f.read_bytes() for f in p.assets.glob('*.dx')}
            config={'provenance':'explicit manual fixture','race_wheel_instances':[{'translation':[i,0,0],'rotation_y':0} for i in range(4)]}
            p.save_preview_profile(config);q=WorkshopProject(p.root);self.assertEqual(q.preview_profile(),config);q.materialize();self.assertEqual(before,{f.name:f.read_bytes() for f in q.assets.glob('*.dx')});self.assertEqual(q.data['edits'],{})
            config['race_wheel_instances'][0]['translation'][0]=float('nan')
            with self.assertRaises(ValueError):p.save_preview_profile(config)
