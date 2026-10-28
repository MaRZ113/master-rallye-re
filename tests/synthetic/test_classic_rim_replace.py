"""Measured MR rim replacement on synthetic alpha source wheels."""
import copy,math,struct,tempfile,unittest
from pathlib import Path
from master_rallye.topology_writer import CompiledVertex,DrawGeometry,source_geometry
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.dx import parse_dx_bytes
from master_rallye.classic_wheels import replace_source_rim
from master_rallye.addon_sdk.gt3_assembly import place
from tests.synthetic.test_workshop import family

def ring_mesh(rings,cap=False):
    vs=[];ts=[];n=16
    if cap:vs.append(CompiledVertex((rings[0][1],0,0),(-1,0,0),bytes([255]*4),((.5,.5),)))
    for r,x in rings:
        for j in range(n):
            a=j*math.tau/n;y,z=math.cos(a),math.sin(a);vs.append(CompiledVertex((x,r*y,r*z),(-1,0,0),bytes([255]*4),((.5+.45*z,.5+.45*y),)))
    if cap:ts.extend((0,1+(j+1)%n,1+j)for j in range(n))
    off=int(cap)
    for row in range(len(rings)-1):
        a,b=off+row*n,off+(row+1)*n
        for j in range(n):
            k=(j+1)%n;ts.extend(((a+j,b+k,b+j),(a+j,a+k,b+k)))
    return DrawGeometry(tuple(vs),tuple(ts))

class RimReplacementTests(unittest.TestCase):
    def fixture(self,root):
        family(root/'fixture');template=(root/'fixture/wheel.dx').read_bytes()
        tyre=ring_mesh(((.32,-.12),(.25,-.12),(.25,.12),(.32,.12)))
        face=ring_mesh(((.20,-.09),),True);shelf=ring_mesh(((.25,-.10),(.23,-.095),(.20,-.09)))
        parts=[ScenePart(tyre,('face','Null','Null')),ScenePart(face,('face','Null','Null'),True),ScenePart(shelf,('face','Null','Null'),True,True)]
        wheel=write_scene_dx(template,parts)
        reference=write_scene_dx(template,[ScenePart(p.geometry,p.textures)for p in parts])
        groups=[];complete=[]
        for x,z,a in ((-.8,1.2,0),(.8,1.2,math.pi),(-.8,-1.2,0),(.8,-1.2,math.pi)):
            groups.append({'draws':list(range(len(complete),len(complete)+3)),'translation':[x,.32,z],'rotation_y':a});complete+=place(parts,(x,.32,z),a)
        image=struct.pack('<5I',0xfeed,1,0,64,64)+bytes((100,110,120,255))*4096
        resources={'wheel.dx':wheel,'complete.dx':write_scene_dx(template,complete),'face.dxt':image}
        cfg=dict(mode='stock_insert',rim_draws=[1,2],reference_face=1,reference_shelf=2,radius_m=.25,outboard_x_m=-.10,texture='face.dxt',face_crop_pixels=[0,0,64,64],output_texture='classic-test-rim.dxt',environment_reference='env',backing_x_m=.05,shelf_width_scale=.35,face_uv_scale=.9,face_center_depth_m=.006,embedded_groups=groups,evidence='synthetic explicit source faces/tyre bead')
        return resources,reference,cfg,image
    def test_opaque_layering_preserves_tyre_and_instance_hubs(self):
        with tempfile.TemporaryDirectory()as t:
            r,ref,cfg,env=self.fixture(Path(t));before=copy.deepcopy(r);out,audit=replace_source_rim(r,ref,cfg,env)
            self.assertEqual(r,before);self.assertTrue(audit['tyres_hubs_preserved'])
            a,b=map(parse_dx_bytes,(r['wheel.dx'],out['wheel.dx']));self.assertEqual(source_geometry(a)[0],source_geometry(b)[0])
            for i in (1,2):self.assertEqual(b.physical_draws[i].flags_0x20[:2],bytes(2));self.assertEqual(b.physical_draws[i].unknown_0x24,7)
            self.assertEqual(len(parse_dx_bytes(out['complete.dx']).physical_draws),12)
            self.assertEqual(out,replace_source_rim(r,ref,cfg,env)[0])
    def test_bad_crop_and_unproven_embedded_transform_rejected(self):
        with tempfile.TemporaryDirectory()as t:
            r,ref,cfg,env=self.fixture(Path(t));cfg['face_crop_pixels']=[1,0,64,64]
            with self.assertRaisesRegex(ValueError,'crop'):replace_source_rim(r,ref,cfg,env)
            cfg['face_crop_pixels']=[0,0,64,64];cfg['embedded_groups'][0]['translation'][0]+=.01
            with self.assertRaisesRegex(ValueError,'transform'):replace_source_rim(r,ref,cfg,env)

if __name__=='__main__':unittest.main()
