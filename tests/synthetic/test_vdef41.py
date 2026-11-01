import copy,json,struct,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from master_rallye.addon_sdk.marker_colour import analyze,summarize,select
from master_rallye.addon_sdk.demo_restoration import restoration_physics,verify_retail_clone
from master_rallye.addon_sdk.physics_profile import compile_family
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from tests.synthetic.test_heritage_source import fixture
from sdk_addon_ai import validate_eligibility,T3


def family(root):
    # Huge green atlas area is deliberately unreferenced; UVs select red only.
    def geometry(scale=1.,uv=(.125,.5)):
        return DrawGeometry(tuple(CompiledVertex(p,(0,0,1),b'\xff'*4,(uv,))for p in((0,0,0),(scale,0,0),(0,scale,0))),((0,1,2),))
    parts=[ScenePart(geometry(),('paint-tga','Null','Null')),ScenePart(geometry(20),('glass-tga','Null','Null'),alpha=True),ScenePart(geometry(20),('wheel-tga','Null','Null')),ScenePart(geometry(20),('whitesuit32-tga','Null','Null'))]
    (root/'car.dx').write_bytes(write_scene_dx(fixture(),parts))
    # DXT native BGRA storage, one used red column and three unused green ones.
    (root/'paint-tga.dxt').write_bytes(struct.pack('<5I',0xfeed,1,0,4,1)+bytes((0,0,240,255))+bytes((0,255,0,255))*3)
    return root


class MarkerColourTests(unittest.TestCase):
    def test_uv_area_ignores_misleading_atlas_glass_and_wheels(self):
        with tempfile.TemporaryDirectory()as folder:
            root=family(Path(folder));before={p.name:p.read_bytes()for p in root.iterdir()}
            r=analyze(root);self.assertGreater(r['dominant'][0],.9);self.assertEqual(r['dominant'][1],0)
            self.assertEqual([d['draw']for d in r['used_draws']],[0]);self.assertEqual(len(r['excluded_draws']),3)
            self.assertEqual(analyze(root),r);self.assertEqual({p.name:p.read_bytes()for p in root.iterdir()},before)

    def test_zero_alpha_is_not_paint_and_explicit_fallback_is_labelled(self):
        with tempfile.TemporaryDirectory()as folder:
            root=family(Path(folder));p=root/'paint-tga.dxt';raw=bytearray(p.read_bytes());raw[23]=0;p.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'No qualified exterior'):analyze(root)
            r=analyze(root,fallback_texture='paint-tga');self.assertEqual(r['method'],'EXPLICIT_TEXTURE_FALLBACK');self.assertEqual(r['dominant'],[0.,1.,0.])

    def test_perceptual_multicolour_swatches_and_area_weights(self):
        r=summarize([([1,0,0],3),([0,0,1],2),([1,1,1],1)])
        self.assertEqual(r['dominant'],[1,0,0]);self.assertEqual(len(r['swatches']),3)
        self.assertEqual(r['swatches'][0]['weight'],.5);self.assertNotEqual(r['dominant'],r['average'])
        self.assertEqual(summarize([([.02,.02,.02],1)])['dominant'],[.02,.02,.02])

    def test_manual_and_historical_are_not_automatic(self):
        r=summarize([([1,0,0],1)]);r['schema']='vehicle-marker-analysis/1'
        self.assertEqual(select({'mode':'MANUAL','rgba':[0,1,0,.5]},r),[0,1,0,.5])
        for status in ('UNKNOWN','INFERRED'):
            with self.assertRaises(ValueError):select({'mode':'HISTORICAL'},r,{'status':status,'value':[1,0,0,1],'evidence':'wrong version'})
        old={'status':'PROVEN','value':[.91796875,.29296875,.36328125,1],'evidence':'original source record'}
        self.assertEqual(select({'mode':'HISTORICAL','contrast':True},r,old),old['value'])
        for bad in ([float('nan'),0,0,1],[True,0,0,1],[0,0,0,2]):
            with self.assertRaises(ValueError):select({'mode':'MANUAL','rgba':bad})

    def test_manual_history_recalculate_and_restore(self):
        from tests.synthetic.test_workshop_vehicle import project
        from unittest.mock import patch
        from master_rallye.workshop.service import WorkshopProject
        with tempfile.TemporaryDirectory()as folder:
            p,_=project(Path(folder));before=(p.working/'physics-profile.json').read_bytes();state=p.vehicle_state()
            p.marker_select('MANUAL',manual=[.2,.4,.6,.8]);chosen=p.marker_inspect()
            with patch('master_rallye.workshop.marker_authoring.analyze',return_value={'dominant':[1,0,0]}):p.marker_recalculate()
            self.assertEqual(WorkshopProject(p.root).marker_inspect(),chosen)
            p.undo();self.assertEqual(p.vehicle_state(),state);p.redo();self.assertEqual(p.marker_inspect(),chosen)
            p.vehicle_reset('race_marker');self.assertEqual(p.vehicle_state()['race_marker'],state['race_marker']);self.assertEqual((p.working/'physics-profile.json').read_bytes(),before)

    def test_auto_refreshes_source_changes_but_manual_never_does(self):
        from tests.synthetic.test_workshop_vehicle import project
        from unittest.mock import patch
        from master_rallye.workshop.vehicle_authoring import sha
        with tempfile.TemporaryDirectory()as folder:
            p,_=project(Path(folder));pins={'car.dx':sha((p.assets/'car.dx').read_bytes())}
            old={'schema':'vehicle-marker-analysis/1','dominant':[1,0,0],'average':[1,0,0],'source_pins':pins}
            state=p.vehicle_state();state['race_marker']=[1,0,0,1];state['marker_policy']={'version':1,'historical':None,'policy':{'mode':'AUTO_DOMINANT'},'analysis':old}
            p._vehicle_commit(state)
            changed={**old,'dominant':[0,0,1],'source_pins':{'car.dx':'0'*64}}
            p.data['vehicle_authoring']['marker_policy']['analysis']['source_pins']={'car.dx':'0'*64}
            with patch('master_rallye.addon_sdk.marker_colour.analyze',return_value=changed):p.vehicle_materialize()
            self.assertEqual(p.vehicle_state()['race_marker'],[0,0,1,1])
            p.marker_select('MANUAL',manual=[0,1,0,.5])
            with patch('master_rallye.addon_sdk.marker_colour.analyze',side_effect=AssertionError('manual must not analyse')):p.vehicle_materialize()
            self.assertEqual(p.vehicle_state()['race_marker'],[0,1,0,.5])

    def test_historical_policy_cannot_restore_an_old_placeholder_rgba(self):
        from tests.synthetic.test_workshop_vehicle import project
        with tempfile.TemporaryDirectory()as folder:
            p,_=project(Path(folder));state=p.vehicle_state();state['race_marker']=[0,0,1,1]
            state['marker_policy']={'version':1,'policy':{'mode':'HISTORICAL'},'historical':{'status':'PROVEN','value':[.9,.3,.4,1],'evidence':'verified original record'}}
            p._vehicle_commit(state);self.assertEqual(p.vehicle_state()['race_marker'],[.9,.3,.4,1])

    def test_sample_budgets_and_invalid_explicit_ownership(self):
        with self.assertRaises(ValueError):summarize([([1,0,0],-1)])
        with self.assertRaises(ValueError):summarize([([1,0,0],1)]*120001)
        with tempfile.TemporaryDirectory()as folder:
            root=family(Path(folder))
            for draws in ([True],[999],[0,0],[]):
                with self.assertRaises(ValueError):analyze(root,paint_draws=draws)


class PhysicsAndAITests(unittest.TestCase):
    def test_ai_class_comes_from_current_roster_not_stale_heritage_metadata(self):
        from tests.synthetic.test_workshop_vehicle import project
        with tempfile.TemporaryDirectory()as folder:
            root=Path(folder);p,_=project(root);plan=root/'plan';plan.mkdir()
            (p.working/'historical-identity.json').write_text(json.dumps({'runtime_class':'T2'}))
            config={'projects':[{'physical_id':28,'vehicle_class':'T3','project':str(root/'author')}]}
            (plan/'roster-config.json').write_text(json.dumps(config));p.data['build_settings']['roster_candidate']=str(plan)
            self.assertEqual(p.ai_inspect()['vehicle_class'],'T3');self.assertIn('invitation',p.ai_inspect()['supported_modes'])
            config['projects'][0]['vehicle_class']='T1';(plan/'roster-config.json').write_text(json.dumps(config))
            self.assertEqual(p.ai_inspect()['vehicle_class'],'T1');self.assertNotIn('invitation',p.ai_inspect()['supported_modes'])

    def test_full_retail_clone_cannot_admit_historical_overrides(self):
        from tests.synthetic.test_physics_profile import fixture as physics
        members,profile=physics();policy={'mode':'retail','require_exact_clone':True,'donor_family':'Navara','reason':'owner clone'}
        result,_=restoration_physics(policy,profile,{},members,runtime_family='AddonOne')
        compiled={name:compile_family(raw,result,donor_family='Navara',runtime_family='AddonOne',source_label=name)[0]for name,raw in members.items()}
        self.assertTrue(verify_retail_clone(members,compiled,donor_family='Navara',runtime_family='AddonOne'))
        for bad in ({**profile,'overrides':{'DataGame/vehicles.xml':{'Chassis/TotalMass':1200}}},{**profile,'owned_tyres':{}}):
            with self.assertRaises(ValueError):restoration_physics(policy,bad,{},members,runtime_family='AddonOne')

    def test_authored_events_stay_disabled_and_dynamic_modes_are_class_bound(self):
        for cls in ('T1','T2','T3'):
            for mode in ('quick_race','master_rallye'):validate_eligibility(cls,{mode:{'enabled':True}})
            with self.assertRaises(ValueError):validate_eligibility(cls,{'challenge':{'enabled':True}})
        for mode in ('invitation','rallye_cup'):validate_eligibility('T3',{mode:{'enabled':True}})
        self.assertEqual(len(T3),4)

    def test_original_t3_loop_preimage_is_required(self):
        import sdk_addon_ai as ai
        from types import SimpleNamespace
        from patch_vehicle_registry_id26 import _CodeImage
        rows=[{'physical_id':32,'vehicle_class':'T3','ai_eligibility':{'quick_race':{'enabled':True},'master_rallye':{'enabled':False}}}]
        fake=SimpleNamespace(registry=SimpleNamespace(va_to_file_offset=lambda *a:0))
        with self.assertRaisesRegex(ValueError,'preimage conflict'):ai.emit(_CodeImage(0x10000000),rows,b'\0'*9,None,fake,[])

    def test_shared_cup_invitation_gates_are_independent_and_save_registers(self):
        from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESI as SI,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP
        from types import SimpleNamespace
        from patch_vehicle_registry_id26 import _CodeImage
        import sdk_addon_ai as ai,build_vehicle_multislot_i0 as i0
        image=b''.join(bytes.fromhex(r[4])for r in T3);offsets={r[1]:i*9 for i,r in enumerate(T3)}
        fake=SimpleNamespace(i0=i0,registry=SimpleNamespace(va_to_file_offset=lambda pe,va,size:offsets[va]))
        for cup,invitation in ((True,False),(False,True),(True,True)):
            flags={k:{'enabled':v}for k,v in [('quick_race',False),('master_rallye',False),('rallye_cup',cup),('invitation',invitation)]}
            code=_CodeImage(0x10000000);hooks=[];ai.emit(code,[{'physical_id':32,'vehicle_class':'T3','ai_eligibility':flags}],image,None,fake,hooks);blob=code.build()
            for mode,hook,reentry,exit_,_ in T3[2:]:
                for runtime,expected in ((6,cup),(8,invitation),(5,False)):
                    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000);u.mem_map(0x10000000,0x10000);u.mem_map(0x20000000,0x10000);u.mem_write(0x10000000,blob)
                    u.reg_write(SP,0x20008000);u.reg_write(SI,20);u.reg_write(AX,0x12345678);seen=[]
                    entry=code.base_va+code.labels['pool_t3_'+mode]
                    def monitor(uc,at,size,user):
                        if at in(0x4ada50,0x4abe90):
                            sp=uc.reg_read(SP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0];uc.reg_write(AX,runtime if at==0x4abe90 else 0x600000);uc.reg_write(CX,0xbad);uc.reg_write(DX,0xbad);uc.reg_write(SP,sp+4);uc.reg_write(IP,ret)
                        elif at==reentry:seen.append(uc.reg_read(SI));uc.reg_write(IP,entry)
                        elif at==exit_:uc.emu_stop()
                    u.hook_add(UC_HOOK_CODE,monitor);u.emu_start(entry,0,count=300)
                    self.assertEqual(seen,[32]if expected else[]);self.assertEqual(u.reg_read(SP),0x20008000);self.assertEqual(u.reg_read(AX),0x12345678);self.assertEqual(u.reg_read(SI),21)

    def test_reconstruction_manifest_preserves_menu_and_physical_id(self):
        root=Path(__file__).resolve().parents[2];m=json.loads((root/'research/vehicles/sdk/restorations/tomcat-841.json').read_text())
        self.assertEqual(m['runtime']['physical_id'],32);self.assertTrue(m['physics']['require_exact_clone'])
        self.assertEqual(m['identity']['artwork']['vehicle_select_art']['presentation'],'source-pixels-v1')
        hud=m['identity']['artwork']['smallcarsheet'];self.assertEqual(hud['status'],'RECONSTRUCTED');self.assertEqual(hud['rendering']['azimuth'],-90)


if __name__=='__main__':unittest.main()
