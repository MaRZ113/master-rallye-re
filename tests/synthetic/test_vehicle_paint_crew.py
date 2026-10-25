"""Generated geometry only: source-qualified paint, rigid crew and allocation bounds."""
import copy,hashlib,json,math,struct,sys,tempfile,unittest
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from master_rallye.addon_sdk.gt4_paint import prepare_paint
from master_rallye.addon_sdk.crew import fit_crew
from master_rallye.scene_dx_writer import write_scene_dx,ScenePart
from master_rallye.topology_writer import DrawGeometry
from tests.synthetic.test_gt4_material_pipeline import scene,draws
import build_runtime_launcher


class PaintCrewTests(unittest.TestCase):
    def test_shared_environment_packet_uses_triangle_local_gain(self):
        base,env=draws([65]*16);base['packet']=0
        second={**copy.deepcopy(base),'packet':1,'triangles':[base['triangles'][1]]};base['triangles']=[base['triangles'][0]]
        combined=copy.deepcopy(env[0]);combined.update(source_shape=8,packet=0,vertices=[],triangles=[])
        for part,gain in zip(env,(64,128)):
            start=len(combined['vertices'])
            for i in part['triangles'][0]:combined['vertices'].append({**part['vertices'][i],'rgba_ps2':(gain,gain,gain,128)})
            combined['triangles'].append((start,start+1,start+2))
        out=prepare_paint([base,second,combined],[{'shape':7,'packets':[0,1],'role':'own exterior'}])
        self.assertEqual([d['_mr_paint_reflection']['gain_rgb'] for d in out if '_mr_paint_reflection' in d],[[.5]*3,[1.]*3])
    def test_partition_keeps_parent_texture_guard_uv_mapping(self):
        from build_gt4_vehicle import compile_draws
        base,env=draws([0]+[65]*15);base['packet']=0;base['vertices'][0]['uv']=(0.,0.)
        base['texture']['registers'].update(wrap_s=1,wrap_t=1)
        for i,d in enumerate(env):d.update(source_shape=8,packet=i)
        with tempfile.TemporaryDirectory() as td:
            output=Path(td);old,_=compile_draws([base],output)
            texture=struct.pack('<5I',0xfeed,1,0,1,1)+b'\xff'*4
            new,_=compile_draws([base,*env],output,environment_reference=texture,material_policy={'qualified_environment':True,'paint_surfaces':[{'shape':7,'packets':[0],'role':'own exterior'}]})
            expected={v.position:v.uvs for v in old[0].geometry.vertices}
            for p in new:
                for v in p.geometry.vertices:self.assertEqual(v.uvs,expected[v.position])
    def test_paint_partitions_existing_triangles_without_uv_or_vertex_changes(self):
        base,env=draws([0]+[65]*15);base['packet']=0;base['vertices'][0]['uv']=(0.,0.)
        for i,d in enumerate(env):d.update(source_shape=8,packet=i)
        out=prepare_paint([base,*env],[{'shape':7,'packets':[0],'role':'test exterior'}])
        parts=[d for d in out if '_mr_paint_reflection' in d]
        self.assertEqual({d['_mr_paint_reflection']['coverage'] for d in parts},{'opaque_uv_footprint','paint_cutout_floor'})
        self.assertCountEqual([t for d in parts for t in d['triangles']],base['triangles'])
        for d in parts:self.assertEqual(d['vertices'],base['vertices'])
    def test_paint_rejects_unmatched_and_destination_alpha_exclusions(self):
        base,env=draws([65]*16);base['packet']=0;role=[{'shape':7,'packets':[0],'role':'test exterior'}]
        for i,d in enumerate(env):d.update(source_shape=8,packet=i)
        with self.assertRaises(ValueError):prepare_paint([base],role)
        base['texture']['rgba_ps2']=bytes((100,120,140,128))*16
        with self.assertRaises(ValueError):prepare_paint([base,*env],role)
        with self.assertRaises(ValueError):prepare_paint([base,*env],[{'shape':8,'packets':[0],'role':'missing'}])
    def test_crew_preserves_stock_uv_colours_and_rigid_yaw(self):
        template,p=scene();a=replace(p,geometry=replace(p.geometry,vertices=tuple(replace(v,position=(v.position[0]+1,v.position[1],v.position[2])) for v in p.geometry.vertices)))
        b=replace(p,geometry=replace(p.geometry,vertices=tuple(replace(v,position=(v.position[0]-3,v.position[1],v.position[2])) for v in p.geometry.vertices)))
        raw=write_scene_dx(template,[ScenePart(DrawGeometry(a.geometry.vertices+b.geometry.vertices,((0,1,2),(3,4,5))),('own-tga','Null','Null'))])
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'car.dx').write_bytes(raw);out=root/'out';out.mkdir()
            tex=struct.pack('<5I',0xfeed,1,0,1,1)+b'\xff'*4;(root/'own-tga.dxt').write_bytes(tex)
            cfg={'source':'car.dx','source_sha256':hashlib.sha256(raw).hexdigest(),'draws':[{'index':0,'textures':['own-tga','Null','Null'],'role':'own fixture'}],
                'people':{'a':{'side':1,'pivot':[0,0,0]},'b':{'side':-1,'pivot':[0,0,0]}},'placements':{'race':{who:{'lateral':.2,'vertical':.3,'longitudinal':-.4,'yaw_degrees':90} for who in ('a','b')}}}
            parts,records=fit_crew(root,cfg,'race',out);self.assertEqual(len(parts),2);self.assertEqual(sum(r['triangles'] for r in records),2)
            self.assertEqual(parts[0].geometry.vertices[0].uvs,a.geometry.vertices[0].uvs);self.assertEqual(parts[0].geometry.vertices[0].color,a.geometry.vertices[0].color)
            self.assertAlmostEqual(parts[0].geometry.vertices[0].position[0],.2);self.assertAlmostEqual(parts[0].geometry.vertices[0].position[2],-1.4)
            self.assertEqual((out/(parts[0].textures[0]+'.dxt')).read_bytes(),tex)
            subset=copy.deepcopy(cfg);subset['draws'][0]['triangles']=[0,1]
            selected,rows=fit_crew(root,subset,'race',out)
            self.assertEqual(selected,parts)
            self.assertEqual([r['source_triangle_indices'] for r in rows],[[0],[1]])
            for ids in ([0,0],[1,0],[-1,1],[0,2],[True,1],[],[0]):
                bad=copy.deepcopy(cfg);bad['draws'][0]['triangles']=ids
                with self.assertRaises(ValueError):fit_crew(root,bad,'race',out)
            bad=copy.deepcopy(cfg);bad['source_sha256']='0'*64
            with self.assertRaises(ValueError):fit_crew(root,bad,'race',out)
            bad=copy.deepcopy(cfg);bad['placements']['race']['a']['vertical']=math.nan
            with self.assertRaises(ValueError):fit_crew(root,bad,'race',out)
            bad=copy.deepcopy(cfg);bad['draws'][0]['textures'][0]='wrong'
            with self.assertRaises(ValueError):fit_crew(root,bad,'race',out)
    def test_large_private_extension_is_bounded_to_damage_profile(self):
        profile={'profile':'sdk-native-damage-coverage-alpha','retail_exe':{'sha256':'0'*64},'resource_count':1,
            **{k:'0'*64 for k in ('addon_plan_sha256','native_patch_manifest_sha256','native_patch_operations_sha256','resource_manifest_sha256','resource_index_sha256','reconstructed_reference_file_sha256')},
            'native_extension':{'address':0x10000000,'size':73651,'sha256':'0'*64,'allocation_size':131072}}
        h=build_runtime_launcher._header(profile,{'operations':[{}]});self.assertIn(b'MR_EXTENSION_ALLOCATION_SIZE 131072u',h)
        bad=copy.deepcopy(profile);bad['profile']='scale-experiment'
        with self.assertRaises(build_runtime_launcher.LauncherBuildError):build_runtime_launcher._header(bad,{'operations':[{}]})
        for size,allocation in ((131073,131072),(73651,262144),(100,131072)):
            bad=copy.deepcopy(profile);bad['native_extension'].update(size=size,allocation_size=allocation)
            with self.assertRaises(build_runtime_launcher.LauncherBuildError):build_runtime_launcher._header(bad,{'operations':[{}]})
