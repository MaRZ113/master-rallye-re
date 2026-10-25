"""Own synthetic fixtures only; no GT or MR retail bytes are required."""
import math,struct,tempfile,unittest
from pathlib import Path
from master_rallye.addon_sdk.gt4_spec import DatabaseTable,label_id
from master_rallye.addon_sdk.gt4_rig import wheel_point
from master_rallye.addon_sdk.texture_addressing import guarded_clamp
from master_rallye.addon_sdk.texture_budget import require_vehicle_budget,simulate_texture_cache,texture_working_set
from master_rallye.addon_sdk.wheel_orientation import orient_parts,instance_angle
from master_rallye.addon_sdk.damage_policy import alpha_ownership
from master_rallye.addon_sdk.gt4_mr_materials import environment_pairs
from master_rallye.addon_sdk.gt4_textures import TextureSet
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx,validate_scene_dx
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from master_rallye.dx import parse_dx_bytes
from master_rallye.vehicle_project import _topology_candidate
from tests.synthetic.test_library import synthetic_dx,simple_record,footer56


class ReconstructionTests(unittest.TestCase):
    def test_redundant_gt4_coverage_test_is_removed_without_destroying_cutouts(self):
        import sys,copy
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
        from build_gt4_vehicle import compile_draws
        draw={'source_shape':0,'issues':[],'triangles':[(0,1,2)],'gif':{'blend':False},
            'vertices':[{'position':p,'normal':(0.,0.,1.),'rgba_ps2':(128,128,128,128),'uv':(0.,0.)} for p in [(0,0,0),(1,0,0),(0,1,0)]],
            'texture':{'width':2,'height':1,'rgba_ps2':bytes((200,100,50,128))*2,
                       'registers':{'wrap_s':0,'wrap_t':0,'tfx':0,'tcc':1}},
            'state':{'alpha_fail':0,'depth_test':True,'depth_func':2,'depth_write':True,'variable_scale':[1.,1.,1.,1.],
                     'variable_offset':[0.,0.,0.,0.],'date':False,'fbmask':0,'alpha_test':True,'alpha_func':6,'alpha_ref':0,'blend':[0,1,0,1,0]}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);parts,records=compile_draws([draw],root)
            self.assertFalse(parts[0].alpha);self.assertFalse(parts[0].alpha_test)
            self.assertTrue(records[0]['coverage_proven_opaque'])
            cut=copy.deepcopy(draw);cut['texture']['rgba_ps2']=bytes((200,100,50,128,200,100,50,0))
            parts,_=compile_draws([cut],root);self.assertTrue(parts[0].alpha_test)
            blend=copy.deepcopy(draw);blend['gif']['blend']=True
            self.assertFalse(compile_draws([blend],root)[0][0].alpha)
            blend['state']['depth_write']=False
            self.assertTrue(compile_draws([blend],root)[0][0].alpha)
    def test_source_bound_native_damage_payload_and_budget(self):
        from dataclasses import replace
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
        import vehicle_damage_native as native
        template,part=self.scene();part=replace(part,alpha=True,alpha_test=True)
        data=write_scene_dx(template,[part]);blob,policy=native.payload(data)
        self.assertEqual(blob,native.payload(data)[0])
        self.assertEqual(policy['vertex_count'],3)
        offsets={k:v-native.PAYLOAD_VA for k,v in policy['entries'].items()}
        model=parse_dx_bytes(data)
        self.assertEqual(blob[offsets['positions']:offsets['uvs']],b''.join(struct.pack('<3f',*p) for p in model.vertices.positions))
        self.assertEqual(blob[offsets['mask']:],b'\x01'*3)
        large,large_policy=native.payload(write_scene_dx(template,[part]*1100))
        self.assertGreater(len(large),65536);self.assertEqual(large_policy['allocation_size'],131072)
        with self.assertRaisesRegex(ValueError,'128-KiB'):native.payload(write_scene_dx(template,[part]*2100))
        with self.assertRaisesRegex(ValueError,'retail'):native.extend_image(b'not retail',b'not retail',data)
    def test_four_wheel_culling_qualifier_rejects_mirrors_and_inward_faces(self):
        import sys,copy
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
        from validate_vehicle_wheels import qualify
        template,_=self.scene()
        g=DrawGeometry(tuple(CompiledVertex(p,(-1.,0.,0.),b'\xff'*4,((0.,0.),))
            for p in [(0.,0.,0.),(0.,1.,0.),(0.,0.,-1.)]),((0,1,2),))
        data=write_scene_dx(template,[ScenePart(g,('own','Null','Null'))])
        profile={'race_wheel_instances':[{'translation':[side,.2,z],'rotation_y':instance_angle(side)} for z in (-1,1) for side in (-1,1)]}
        self.assertEqual(qualify(data,profile,[0])['status'],'PASS_FOUR_VISUAL_REST_INSTANCES')
        bad=copy.deepcopy(profile);bad['race_wheel_instances'][0]['scale']=[-1,1,1]
        with self.assertRaisesRegex(ValueError,'mirrored'):qualify(data,bad,[0])
        bad=copy.deepcopy(profile);bad['race_wheel_instances'][0]['rotation_y']=math.pi
        with self.assertRaisesRegex(ValueError,'inward'):qualify(data,bad,[0])
    def test_native_wheel_basis_keeps_winding_normals_and_hubs_coherent(self):
        template,part=self.scene();turned=orient_parts([part],source_outward_x=1)[0]
        self.assertEqual(turned.geometry.triangles,part.geometry.triangles)
        for a,b in zip(part.geometry.vertices,turned.geometry.vertices):
            self.assertEqual(b.position,(-a.position[0],a.position[1],-a.position[2]))
            self.assertEqual(b.normal,(-a.normal[0],a.normal[1],-a.normal[2]))
            self.assertEqual((a.uvs,a.color),(b.uvs,b.color))
        # Four independent rest instances; local -X points out on each side.
        for side in (-1,1,-1,1):
            angle=instance_angle(side)
            self.assertAlmostEqual(-math.cos(angle),side)
            self.assertAlmostEqual(math.sin(angle),0.,places=12)
        with self.assertRaises(ValueError):orient_parts([part],source_outward_x=0)
    def test_damage_alpha_policy_preserves_coverage_without_disabling_deformation(self):
        template,part=self.scene()
        with self.assertRaises(ValueError):alpha_ownership(write_scene_dx(template,[part]))
        from dataclasses import replace
        data=write_scene_dx(template,[part,replace(part,alpha=True,alpha_test=True)])
        p=alpha_ownership(data)
        self.assertEqual(p['coverage_vertex_count'],3)
        self.assertEqual(bytes.fromhex(p['mask_hex']),bytes((0,0,0,1,1,1)))
        self.assertEqual(p['mixed_vertex_count'],0)
    def test_empty_texture_bank_keeps_its_lod_index(self):
        empty=b'Tex1'+bytes(44);bank=TextureSet(empty,0);self.assertEqual(bank.registers,[])
        with self.assertRaises(ValueError):bank.texture(0)
        with self.assertRaises(ValueError):TextureSet(empty[:-1],0)
        with self.assertRaises(ValueError):TextureSet(empty[:20]+b'\x01'+empty[21:],0)
    def test_original_table_and_label_bounds(self):
        data=b'GTDB'+struct.pack('<HHII',0,0,2,3)+struct.pack('<4I',7,0,9,3)+b'abcdef'
        db=DatabaseTable(data);self.assertEqual(db.row(7),b'abc');self.assertEqual(db.row(9),b'def')
        with self.assertRaises(ValueError):db.row(8)
        with self.assertRaises(ValueError):DatabaseTable(data[:-1]).row(9)
        label=b'ch_example\0';idi=b'GTID'+struct.pack('<I',1)+bytes(8)+struct.pack('<IIH',0,7,len(label))+label
        self.assertEqual(label_id(idi,'ch_example'),7)
        with self.assertRaises(ValueError):label_id(idi,'absent')
        with self.assertRaises(ValueError):label_id(idi[:-1], 'ch_example')
    def test_huffman_template_and_difference_rows(self):
        # A simple complete eight-bit dictionary; symbols use little bit order.
        prefix=b''.join(bytes((i,8)) for i in range(256))
        codes=b''.join(struct.pack('<BBHI',8,i,0,i) for i in range(256))
        code_header=struct.pack('<II',0x208+len(codes),256)+prefix+codes
        templates=struct.pack('<II',11,1)+b'abc'
        rows=bytes((1,0,3,128,2,ord('Z'),4,64))+b'xyz'
        data=b'GTDB'+struct.pack('<HHII',1,0,3,3)+struct.pack('<6I',7,0,8,2,9,6)+code_header+templates+rows
        db=DatabaseTable(data);self.assertEqual(db.row(7),b'abc');self.assertEqual(db.row(8),b'aZc');self.assertEqual(db.row(9),b'xyz')
        bad=bytearray(data);bad[-5]=65
        with self.assertRaises(ValueError):DatabaseTable(bytes(bad)).row(9)
    def test_native_normal_four_wheel_layer_dimensions(self):
        w={'width':.215,'rim_radius':.2286,'sidewall':.09675,'hub':[-.745,.18535,-1.255],'side':-1}
        a=wheel_point((0.,.86,0),w,kind='tyre',radial_range=(.86,1.32),max_x=1.)
        b=wheel_point((1.,1.32,0),w,kind='tyre',radial_range=(.86,1.32),max_x=1.)
        self.assertAlmostEqual(a[1]-w['hub'][1],w['rim_radius']);self.assertAlmostEqual(b[1]-w['hub'][1],.32535)
        self.assertAlmostEqual(b[0]-a[0],.215)
        with self.assertRaises(ValueError):wheel_point((0,0,0),w,kind='tyre',radial_range=(1,1),max_x=1)
    def test_clamp_guard_affine_and_repeat(self):
        raw=bytes((255,0,0,255,0,0,255,255));reg={'wrap_s':1,'wrap_t':0}
        uv=[(-.5,-2.),(1.5,3.)];w,h,p,remapped,r=guarded_clamp(2,1,raw,reg,uv)
        self.assertEqual(h,1);self.assertEqual([v[1] for v in remapped],[-2.,3.])
        for old,new in zip(uv,remapped):
            src=min(1,max(0,math.floor(old[0]*2)));dst=math.floor(new[0]*w)
            self.assertEqual(p[dst*4:dst*4+4],raw[src*4:src*4+4])
        with self.assertRaises(ValueError):guarded_clamp(2,1,raw,{'wrap_s':3,'wrap_t':0},uv)
        with self.assertRaises(ValueError):guarded_clamp(2,1,raw,reg,[(-100.,0.)])
    def test_clamp_guard_retains_resolution_without_whole_image_padding(self):
        raw=bytes(c for y in range(32) for x in range(64) for c in (x,y,128,255))
        w,h,p,uv,r=guarded_clamp(64,32,raw,{'wrap_s':1,'wrap_t':1},[(0.,0.),(1.,1.)])
        self.assertEqual((w,h),(128,64)) # Old rule: 256x128 (16x source area).
        self.assertTrue(r['source_resolution_preserved'])
        ox,oy=r['guard_offsets']
        for y in range(32):
            self.assertEqual(p[((y+oy)*w+ox)*4:((y+oy)*w+ox+64)*4],raw[y*256:(y+1)*256])
        # Equal bilinear footprints throughout the interpolated UV interval,
        # including fractional and out-of-range coordinates. No vertex clamp.
        for mode in (1,2):
            reg={'wrap_s':mode,'wrap_t':0,'min_u':2,'max_u':60}
            w,h,p,uv,r=guarded_clamp(64,32,raw,reg,[(-.13,0.),(1.27,1.)])
            for i in range(101):
                old=-.13+1.4*i/100;new=uv[0][0]+(uv[1][0]-uv[0][0])*i/100
                x=old*64-.5;nx=new*w-.5;lo,hi=(0,63) if mode==1 else (2,60)
                for j in (0,1):
                    src=min(hi,max(lo,math.floor(x)+j));dst=math.floor(nx)+j
                    self.assertEqual(p[dst*4:dst*4+4],raw[src*4:src*4+4])
                self.assertAlmostEqual(x-math.floor(x),nx-math.floor(nx),places=10)
    def test_native_texture_budget_gate_and_cache_churn(self):
        self.assertEqual(require_vehicle_budget({'cache_bytes':1024})['native_cache_headroom_bytes'],32*1024*1024-1024)
        with self.assertRaises(ValueError):require_vehicle_budget({'cache_bytes':17*1024*1024})
        with self.assertRaises(ValueError):require_vehicle_budget({'cache_bytes':1},32*1024*1024)
        stable=simulate_texture_cache({'ui':3,'a':3,'b':3},['ui','a','b'],capacity=10)
        self.assertEqual([s['misses'] for s in stable],[3,0,0])
        churn=simulate_texture_cache({'ui':3,'a':4,'b':4},['ui','a','b'],capacity=10)
        self.assertEqual([s['misses'] for s in churn],[3,3,3])
        self.assertEqual(simulate_texture_cache({'a':11},['a'],capacity=10)[0]['resident_bytes'],11)
        with self.assertRaises(ValueError):simulate_texture_cache({'a':0},['a'])
    def test_native_texture_budget_reads_references_not_unrelated_files(self):
        template,part=self.scene()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ('car.dx','complete.dx','wheel.dx'):(root/name).write_bytes(write_scene_dx(template,[part,part]))
            (root/'own.dxt').write_bytes(struct.pack('<5I',0xfeed,1,0,2,2)+b'\xff'*16)
            (root/'unreferenced.dxt').write_bytes(b'irrelevant')
            report=texture_working_set(root)
            self.assertEqual(report['cache_bytes'],16);self.assertEqual(report['unique_textures'],1)
            self.assertEqual(report['models']['complete.dx']['request_sequence'],['own','own'])
            (root/'own.dxt').write_bytes(struct.pack('<5I',0xfeed,1,0,3,1)+b'\xff'*12)
            with self.assertRaises(ValueError):texture_working_set(root)
    def scene(self):
        ps=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
        template=synthetic_dx(ps,[0,1,2],[simple_record(0,2,0,3,('old','Null','Null'))],[(0,0,3)],trailing=footer56(ps))
        g=DrawGeometry(tuple(CompiledVertex(p,(0.,0.,1.),b'\xff'*4,((0.,0.),)) for p in ps),((0,1,2),))
        return template,ScenePart(g,('own','Null','Null'))
    def test_shared_scene_writer_and_donor_boundary(self):
        template,p=self.scene();out=write_scene_dx(template,[p,p]);model=parse_dx_bytes(out)
        self.assertEqual(model.vertex_count,6);self.assertEqual(len(model.physical_draws),2)
        self.assertEqual(out,write_scene_dx(template,[p,p]));self.assertTrue(validate_scene_dx(template,out)['collision_preserved'])
        # The original same-draw topology authoring rule remains unchanged.
        with self.assertRaises(ValueError):_topology_candidate(template,out,'car.dx')
        bad=bytearray(out);bad[-4:]=struct.pack('<f',100.)
        with self.assertRaises(ValueError):validate_scene_dx(template,bytes(bad))
        bad=bytearray(out);bad[model.physical_draws[0].offset+32]=2
        with self.assertRaises(ValueError):validate_scene_dx(template,bytes(bad))
    def test_environment_translation_requires_proven_pair_and_coverage(self):
        def draw(issues,blend=False):
            return {'issues':issues,'triangles':[(0,1,2)],'vertices':[{'position':p,'normal':(0,0,1),'rgba_ps2':(64,64,64,128)} for p in [(0,0,0),(1,0,0),(0,1,0)]],
                'gif':{'blend':blend},'texture':{'rgba_ps2':bytes((200,100,50,64)),'registers':{'tfx':0,'tcc':1}},
                'state':{'blend':[0,2,1,1,0],'fbmask':0,'depth_write':True,'date':False,'datm':0,'alpha_test':True,'alpha_func':6,'alpha_ref':0}}
        base=draw([]);env=draw(['runtime-generated external texture / texgen unavailable'],True);env['state']['date']=True
        pairs,used=environment_pairs([base,env]);self.assertIn(0,pairs);self.assertEqual(used,{1:0})
        base['texture']['rgba_ps2']=bytes((200,100,50,0));self.assertEqual(environment_pairs([base,env]),({},{}) )
        base['texture']['rgba_ps2']=bytes((200,100,50,128));self.assertEqual(environment_pairs([base,env]),({},{}) )
        env['state']['date']=False;self.assertEqual(environment_pairs([base,dict(base),env]),({},{}) )

if __name__=='__main__':unittest.main()
