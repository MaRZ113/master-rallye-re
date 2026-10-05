"""Unsaved native preview/publication/Start tests; DLL/OS/rendering are boundaries."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import r_ai1_2a_preview as patch
import r_ai1_2_emulate as old
from r_ai2_emulate import BoundedMachine

def install(program,api,monitor,source,patched):
    old.install(program,api,monitor,source,patched)
    for row in patch.preview_ranges():
        if row['va'] is None:continue
        address=api.toAddr(row['va']);code=row['replacement'] if patched else row['original']
        api.clearListing(address,address.add(len(code)-1));program.getMemory().setBytes(address,code);api.disassemble(address)

def preview(program,api,monitor,event,human,authored,chosen):
    m=BoundedMachine(program,api,monitor,0x45EC15)
    m.stop=0x45ED46;registry=m.alloc(bytes(0x1200));screen=m.alloc(bytes(0x20))
    m.write(screen+0x10,event);m.put('ESI',screen)
    m.write(registry+(event+25)*0x2c+0x570,human);m.write(registry+(event+25)*0x2c+0x574,authored)
    broker=m.alloc(bytes(32));lang=m.alloc(bytes(16));vtable=m.alloc(bytes(16));m.write(lang,vtable);m.write(vtable+12,0x7FF000)
    writes={};names=[];calls=[]
    def boundary(pc):
        sp=m.reg('ESP')
        if pc==0x45A3C0:m.ret(registry)
        elif pc==patch.base.LOADER:
            args=[m.read(sp+i*4) for i in range(1,5)]
            if args!=[1,event+100,human,authored]:raise ValueError('Preview bridge argument mismatch')
            calls.append(args);m.ret(chosen,16)
        elif pc in (0x4D11D0,0x4D0580):
            ptr=m.reg('ECX');m.write(ptr,m.read(sp+4));m.ret(ptr,4)
        elif pc==0x485CF0:m.ret(lang)
        elif pc==0x7FF000:
            bank,id=m.read(sp+4),m.read(sp+8);names.append((bank,id));m.ret(m.cstring('NAME_'+str(id)),8)
        elif pc==0x4D8EC0:m.ret(broker)
        elif pc in (0x4D8000,0x4D8720):
            path=m.text(m.read(m.read(sp+4)));value=m.read(sp+8)
            writes[path]=m.text(m.read(value)) if pc==0x4D8720 else value
            m.ret(None,8)
        elif pc==0x5B4C00:m.ret()
        else:return False
        return True
    try:
        while m.emu.getExecutionAddress().getOffset()!=m.stop:
            pc=m.emu.getExecutionAddress().getOffset()
            if not boundary(pc) and not m.emu.step(monitor):raise ValueError(f'Preview x86 {pc:x}: {m.emu.getLastError()}')
            m.steps+=1
            if m.steps>1000:raise ValueError('Preview instruction bound')
        wanted=chosen if 0<=chosen<=24 else authored
        if m.reg('ESP')!=m.stack or m.reg('ESI')!=screen:raise ValueError('Preview stack/object corruption')
        if writes!={'Frontend/Challenge/Car1Text':'NAME_'+str(human),'Frontend/Challenge/Car2Text':'NAME_'+str(wanted),'Frontend/Challenge/PlayerCar':human,'Frontend/Challenge/OpponentCar':wanted}:raise ValueError(writes)
        if names!=[(53,human),(53,wanted)]:raise ValueError('Name and model differ')
        m.guards()
        return {'event':event,'authored_human':human,'authored_ai':authored,'selected':wanted,'writes':writes,'name_indices':names,'callback_calls':len(calls)}
    finally:m.emu.dispose()

def start(program,api,monitor,event,human,authored,chosen):
    m=old.Game(program,api,monitor,'Challenge',1,human)
    m.write(m.stack+4,event)
    m.write(m.registry+(event+25)*0x2c+0x570,human);m.write(m.registry+(event+25)*0x2c+0x574,authored)
    calls=[];original=m.boundary
    def boundary(pc):
        if pc==patch.base.LOADER:
            sp=m.reg('ESP');args=[m.read(sp+i*4) for i in range(1,5)]
            if args!=[1,1,1,1]:raise ValueError('Native Start arguments changed')
            calls.append(args);m.ret(chosen,16);return True
        return original(pc)
    m.boundary=boundary
    try:
        result=m.execute_case();result['cache_consume_calls']=len(calls);return result
    finally:m.emu.dispose()

def reset(program,api,monitor,back):
    address=patch.RESET_BACK if back else patch.RESET_ENTRY
    m=BoundedMachine(program,api,monitor,address,(2,) if back else ())
    calls=[];native=[]
    def boundary(pc):
        sp=m.reg('ESP')
        if pc==patch.base.LOADER:
            args=[m.read(sp+i*4) for i in range(1,5)]
            if args!=[1,0xffffff9c,0,0]:raise ValueError('Reset args')
            calls.append(args);m.ret(-1,16)
        elif pc==(0x45D910 if back else 0x4E3DD0):
            native.append(m.read(sp+4) if back else None);m.ret(0x12345678,4 if back else 0)
        else:return False
        return True
    try:
        m.execute_bounded(boundary,4 if back else 0)
        if len(calls)!=1 or len(native)!=1 or (back and native!=[2]) or m.reg('EAX')!=0x12345678:raise ValueError('Reset/native replay mismatch')
        return {'reset':'Back' if back else 'entry','native_call_preserved':True}
    finally:m.emu.dispose()

def retry(program,api,monitor):
    m=BoundedMachine(program,api,monitor,0x47E020,(0,));screen=m.alloc(bytes(0x20));controller=m.alloc(bytes(0x10));m.write(screen+12,controller);m.put('ECX',screen)
    transition=[]
    def boundary(pc):
        if pc==0x45D6C0:m.ret()
        elif pc==0x45DBC0:m.ret(0)
        elif pc==0x45D930:m.ret(1,4)
        elif pc==0x45D910:transition.append(m.read(m.reg('ESP')+4));m.ret(None,4)
        elif pc in (patch.base.LOADER,0x44FEC0):raise ValueError('Retry rebuilds roster')
        else:return False
        return True
    try:
        m.execute_bounded(boundary,4)
        if transition!=[10]:raise ValueError('Retry no longer targets Loading')
        return {'kind':'native-Retry','transition':10,'constructor_calls':0,'policy_calls':0}
    finally:m.emu.dispose()

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source=a.source.read_bytes();patch.build(source)
    import pyghidra
    pyghidra.start(install_dir=a.install)
    from java.lang import Object
    from ghidra.program.flatapi import FlatProgramAPI
    project=pyghidra.open_project(a.project,'MasterRallye');consumer=Object();program=project.getProjectData().getFile('/MRallye.exe').getReadOnlyDomainObject(consumer,-1,pyghidra.task_monitor())
    transaction=program.startTransaction('R-AI1.2a unsaved native oracle')
    try:
        if str(program.getExecutableSHA256())!=patch.RETAIL_SHA256:raise ValueError('Unknown program')
        api=FlatProgramAPI(program);monitor=pyghidra.task_monitor();cases=[]
        for event in range(11):
            human,authored=patch.AUTHORED[event] # exact retail constructor constants
            install(program,api,monitor,source,False)
            baseline_preview=preview(program,api,monitor,event,human,authored,-1)
            baseline_start=start(program,api,monitor,event,human,authored,-1)
            install(program,api,monitor,source,True)
            for policy,chosen in (('Stock',-1),('Mixed',14),('Diverse',2 if human!=2 else 3),('invalid',25)):
                prev=preview(program,api,monitor,event,human,authored,chosen)
                race=start(program,api,monitor,event,human,authored,chosen)
                wanted=chosen if 0<=chosen<=24 else authored
                if race['cars'][1]['CarID']!=wanted or race['cars'][1]['CarClass']!=patch.stock_class_local(wanted)[0]:raise ValueError('Preview/race mismatch')
                if race['cars'][0]!=baseline_start['cars'][0] or race['cars'][1]['DriverID']!=baseline_start['cars'][1]['DriverID']:raise ValueError('Native human/driver publication changed')
                if race['cache_consume_calls']!=1 or prev['callback_calls']!=1:raise ValueError('Callback seam count')
                if policy in ('Stock','invalid') and any(race[key]!=baseline_start[key] for key in ('cars','writes','rng')):raise ValueError('Stock differs')
                if policy=='Stock' and prev['writes']!=baseline_preview['writes']:raise ValueError('Stock preview differs')
                cases.append({'kind':'preview/Start','policy':policy,**prev,'native_driver_route_preserved':True})
        cases.extend(reset(program,api,monitor,b) for b in (False,True))
        cases.append(retry(program,api,monitor))
        # Existing mode/count builders, loader and persistence regressions against
        # the SAME composed bridge; DLL callbacks remain controlled boundaries.
        regression=old.run_builders(program,api,monitor,source)
        persistence=old.persistence(program,api,monitor)
        old.install(program,api,monitor,source,True)
        loaders=old.loader_cases(program,api,monitor)
        life=old.lifecycle_cases(program,api,monitor)
        report={'status':'STATIC_CHALLENGE_PREVIEW_PASS','challenge_cases':len(cases),'challenge':cases,'r_ai1_2_cases':len(regression)+bool(persistence)+len(loaders)+len(life),'regressions':regression,'persistence':persistence,'loader':loaders,'lifecycle':life,'failed':0,'skipped':0,'runtime_game_test':False,'project_saved':False,'boundaries':['typed Broker','interned/localized strings','DLL callback/cache result','heap','OS','rendering'],'single_generation_state_machine_test':'compiled native-preview-tests.json; actual DLL+Windows game not co-executed'}
        output=patch.ignored_output(a.output);output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k in ('status','challenge_cases','r_ai1_2_cases','failed','skipped','runtime_game_test')},indent=2))
    finally:program.endTransaction(transaction,False);program.release(consumer);project.close()

if __name__=='__main__':main()
