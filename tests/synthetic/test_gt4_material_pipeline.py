"""Generated fixtures for GT4 material ownership and native brake envelopes."""
import copy,struct,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from master_rallye.addon_sdk.gt4_mr_materials import qualified_environment_pairs,covered_uv_footprint
from master_rallye.addon_sdk.native_brakes import write_brake_scene,validate_brake_scene
from master_rallye.addon_sdk.gt4_brakes import native_surfaces
from master_rallye.addon_sdk.damage_policy import alpha_ownership
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.preview_scene import logical_cases
from tests.synthetic.test_library import synthetic_dx,simple_record,footer56


def scene():
    ps=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
    template=synthetic_dx(ps,[0,1,2],[simple_record(0,2,0,3,('own','Null','Null'))],[(0,0,3)],trailing=footer56(ps))
    part=ScenePart(DrawGeometry(tuple(CompiledVertex(p,(0.,0.,1.),b'\xff'*4,((0.,0.),)) for p in ps),((0,1,2),)),('own','Null','Null'))
    return template,part


def native_template():
    template,p=scene();lit=replace(p,diffuse=False);glow=replace(lit,alpha=True)
    data=write_scene_dx(template,[p,lit,glow],allow_unlit=True);m=parse_dx_bytes(data);rs=[]
    for i,d in enumerate(m.physical_draws):
        core=data[d.core_offset:d.offset+d.own_size]
        if i==0:core=struct.pack('<II',7,6)+b'blight'+struct.pack('<5I',2,2,8,1,1)+core
        elif i==1:core=struct.pack('<3I',8,2,2)+core
        rs.append(core)
    return data[:m.draw_table_offset]+struct.pack('<II',1,1)+b''.join(rs)+data[m.global_index_table.preamble_offset:]


def draws(alphas):
    ps=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(1.,1.,0.)]
    vertices=[{'position':p,'normal':(0.,0.,1.),'uv':uv,'rgba_ps2':(128,128,128,128)} for p,uv in zip(ps,[(.55,.55),(.65,.55),(.55,.65),(.65,.65)])]
    state={'alpha_test':True,'alpha_func':6,'alpha_ref':0,'alpha_fail':0,'depth_test':True,'depth_func':2,'depth_write':True,
           'fbmask':0,'date':False,'datm':0,'blend':[0,1,0,1,0],'variable_scale':[1.]*4,'variable_offset':[0.]*4}
    base={'source_shape':7,'vertices':vertices,'triangles':[(0,1,2),(1,3,2)],'state':state,'gif':{'blend':False},'issues':[],
          'texture':{'width':4,'height':4,'registers':{'tfx':0,'tcc':1,'wrap_s':0,'wrap_t':0},'rgba_ps2':bytes(v for a in alphas for v in (100,120,140,a))}}
    env=[]
    for tri in base['triangles']:
        d=copy.deepcopy(base);d['triangles']=[tri];d['texture']=None;d['issues']=['runtime-generated external texture / texgen unavailable'];d['gif']['blend']=True
        d['state'].update(alpha_test=False,depth_write=False,date=True,blend=[0,2,1,1,0]);env.append(d)
    return base,env


class MaterialPipelineTests(unittest.TestCase):
    def test_material_policy_rejects_ambiguous_configuration(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
        from build_gt4_vehicle import compile_draws
        d,_=draws([128]*16)
        with tempfile.TemporaryDirectory() as tmp:
            for policy in ({'qualified_environment':'yes'},{'window_decal_shapes':[True]},
                           {'window_decal_shapes':[7,7]},{'decal_alpha_ref':128},{'decal_alpha_ref':float('nan')}):
                with self.assertRaises(ValueError):compile_draws([d],Path(tmp),material_policy=policy)
    def test_environment_matches_oriented_triangles_across_packets(self):
        base,env=draws([0]+[65]*15)
        self.assertTrue(covered_uv_footprint(base))
        pairs,used=qualified_environment_pairs([base,*env]);self.assertEqual(pairs[0]['coverage'],'opaque_uv_footprint')
        self.assertEqual(pairs[0]['source_environment_packets'],[1,2]);self.assertEqual(used,{1:[0],2:[0]})
    def test_cutout_and_destination_alpha_are_independent(self):
        base,env=draws([0]+[65]*15)
        base['vertices'][0]['uv']=(0.,0.)
        self.assertFalse(covered_uv_footprint(base))
        self.assertEqual(qualified_environment_pairs([base,*env])[0][0]['coverage'],'exact_GREATER128_cutout')
        for d in env:d['state']['datm']=1
        self.assertEqual(qualified_environment_pairs([base,*env]),({},{}))
    def test_rejects_ambiguous_reverse_or_inactive_environment(self):
        base,env=draws([65]*16)
        self.assertEqual(qualified_environment_pairs([base,*env,copy.deepcopy(env[0])]),({},{}))
        env[0]['triangles']=[(0,2,1)]
        self.assertEqual(qualified_environment_pairs([base,*env]),({},{}))
        base,env=draws([128]*16)
        self.assertEqual(qualified_environment_pairs([base,*env]),({},{}))
    def test_depth_safe_decal_keeps_rgb_and_glass_stays_blended(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
        from build_gt4_vehicle import compile_draws
        d,_=draws([0]+[105]*15);d['gif']['blend']=True;d['state'].update(depth_write=False,fbmask=0xff000000,alpha_test=False)
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);parts,records=compile_draws([d],output,material_policy={'window_decal_shapes':[7]})
            self.assertTrue(parts[0].alpha_test);self.assertTrue(records[0]['depth_safe_window_decal'])
            tex=parse_dxt_bytes((output/(parts[0].textures[0]+'.dxt')).read_bytes())
            self.assertEqual(set(tex.bgra[3::4]),{0,255});self.assertEqual(tex.bgra[:3],bytes((140,120,100)))
            parts,_=compile_draws([d],output);self.assertTrue(parts[0].alpha);self.assertFalse(parts[0].alpha_test)
            tex=parse_dxt_bytes((output/(parts[0].textures[0]+'.dxt')).read_bytes());self.assertIn(209,tex.bgra[3::4])
            d['state']['depth_write']=True
            with self.assertRaises(ValueError):compile_draws([d],output,material_policy={'window_decal_shapes':[7]})
    def test_native_cases_count_materials_and_bypass_diffuse_only_when_lit(self):
        template=native_template();_,p=scene();lit=replace(p,alpha=True,alpha_test=True,diffuse=False);glow=replace(lit,alpha_test=False)
        data=write_brake_scene(template,[p],[p,p],[lit,lit],[glow]);r=validate_brake_scene(template,data)
        self.assertEqual(r['case1_draws'],[1,2]);self.assertEqual(r['case2_draws'],[3,4,5])
        m=parse_dx_bytes(data);cases,_=logical_cases(m);self.assertEqual(cases,{1:(1,1),2:(1,1),3:(1,2),4:(1,2),5:(1,2)})
        self.assertEqual(m.declared_top_level_record_count,2)
        with self.assertRaises(ValueError):validate_brake_scene(template,data.replace(b'blight',b'broken'))
        with self.assertRaises(ValueError):write_scene_dx(template,[lit])
        with self.assertRaises(ValueError):write_brake_scene(template,[p],[],[lit],[glow])
    def test_unlit_native_light_coverage_does_not_own_vertex_alpha(self):
        template,p=scene();coverage=replace(p,alpha=True,alpha_test=True);unlit=replace(coverage,diffuse=False)
        data=write_scene_dx(template,[coverage,unlit],allow_unlit=True)
        policy=alpha_ownership(data);self.assertEqual(bytes.fromhex(policy['mask_hex']),bytes((1,1,1,0,0,0)))
    def test_explicit_brake_selectors_fail_closed(self):
        from unittest.mock import patch
        from master_rallye.addon_sdk.gt4_brakes import source_states
        off,_=draws([128]*16);off.update(command_offset=1,packet=0,source_shape=24)
        on=copy.deepcopy(off);on.update(command_offset=2,source_shape=26)
        profile={'native_brakes':{'callback':0,'off_case':0,'on_case':1},'body_callbacks':{'0':0},'selection':{'race_model':0}}
        for selector in ({},None,[],{'off':[],'on':[26]},{'off':[True],'on':[26]},
                         {'off':[24,24],'on':[26]},{'off':[25],'on':[26]},{'off':[24],'on':[26],'extra':[]}):
            p=copy.deepcopy(profile);p['native_brakes']['source_shapes']=selector
            with patch('master_rallye.addon_sdk.gt4_brakes.reconstruct',side_effect=[{'draws':[off]},{'draws':[on]}]):
                with self.assertRaises(ValueError):source_states(b'fixture',p)
        for selector in (None,{'off':[24],'on':[26]}):
            p=copy.deepcopy(profile)
            if selector is not None:p['native_brakes']['source_shapes']=selector
            with patch('master_rallye.addon_sdk.gt4_brakes.reconstruct',side_effect=[{'draws':[off]},{'draws':[on]}]):
                a,b,_=source_states(b'fixture',p);self.assertEqual((len(a),len(b)),(1,1))

    def test_native_builder_preserves_cutout_core_and_only_halos_blended_lens(self):
        from unittest.mock import patch
        import build_gt4_vehicle as builder
        _,p=scene();core=replace(p,alpha=True,alpha_test=True);lens=replace(p,alpha=True)
        lit=replace(lens,diffuse=False);glow=replace(lit,alpha_test=False)
        off={'command_offset':1,'source_shape':24,'packet':0}
        profile={'native_brakes':{'callback':0}}
        with patch.object(builder,'source_states',return_value=([off],[],{})), \
             patch.object(builder,'compile_draws',side_effect=[([p],[]),([p],[]),([core,lens],[])]), \
             patch.object(builder,'native_surfaces',return_value=([lit],[glow],{})) as surfaces, \
             patch.object(builder,'write_brake_scene',return_value=b'fixture') as writer:
            builder.build_model('car.dx',[],b'',Path('.'),brake_source=b'',profile=profile,stock_glow=b'')
            self.assertEqual(surfaces.call_args.args[0],[lens])
            emitted=writer.call_args.args[3];self.assertEqual(len(emitted),2)
            self.assertEqual(emitted[0].textures,core.textures)
            self.assertTrue(emitted[0].alpha_test);self.assertFalse(emitted[0].diffuse)
            self.assertFalse(emitted[1].diffuse)

    def test_generated_halo_ceiling_does_not_resize_lit_source(self):
        _,p=scene();p=replace(p,alpha=True)
        texture=struct.pack('<5I',0xfeed,1,0,64,64)+b'\xff'*(64*64*4)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'own.dxt').write_bytes(texture)
            lit,glow,r=native_surfaces([p],root,texture,halo_max_edge=32)
            self.assertEqual(parse_dxt_bytes((root/(lit[0].textures[0]+'.dxt')).read_bytes()).width,64)
            self.assertEqual(parse_dxt_bytes((root/(glow[0].textures[0]+'.dxt')).read_bytes()).width,32)
            for bad in (True,0,31,2048):
                with self.assertRaises(ValueError):native_surfaces([p],root,texture,halo_max_edge=bad)

    def test_glow_is_intersected_with_source_lens_mask(self):
        _,p=scene();p=replace(p,alpha=True)
        def texture(pixels):return struct.pack('<5I',0xfeed,1,0,2,1)+pixels
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'own.dxt').write_bytes(texture(bytes((0,0,255,0,0,0,255,255))))
            lit,glow,r=native_surfaces([p],root,texture(b'\xff'*8))
            t=parse_dxt_bytes((root/(glow[0].textures[0]+'.dxt')).read_bytes());self.assertEqual(t.bgra[3::4],bytes((0,255)))
            self.assertFalse(lit[0].diffuse);self.assertFalse(glow[0].diffuse);self.assertTrue(lit[0].alpha_test)
            self.assertEqual(glow[0].geometry.triangles,p.geometry.triangles)
            self.assertAlmostEqual(glow[0].geometry.vertices[0].position[2],.001)


if __name__=='__main__':unittest.main()
