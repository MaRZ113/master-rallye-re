"""Read-only Ghidra native Loading/idle-branch regression; no executable-file output."""
import argparse
import json
import sys
from pathlib import Path
from inspect_legacy_attract import inspect, REPLACEMENT, ROOT, expected_loading, SHA

def run(program,api,monitor):
    sys.path.insert(0,str(ROOT.parents[1]/'tools/scanner'))
    from r_ai1_hardening_emulate import Machine,loading
    from jpype import JArray,JByte
    memory=program.getMemory();original=expected_loading();buffer=JArray(JByte)(374)
    if memory.getBytes(api.toAddr(0x464e40),buffer)!=374 or bytes(int(x)&255 for x in buffer)!=original:
        raise ValueError('Ghidra Loading memory differs from exact production context')
    rows=[]
    for guarded in (False,True):
        site=api.toAddr(0x464f69)
        code=REPLACEMENT if guarded else original[0x129:0x12e]
        api.clearListing(site,site.add(4));memory.setBytes(site,code);api.disassemble(site)
        for counter in range(6):
            for stat,size in ((1,0),(0,0),(0,0x20001234),(0,0x20001235),(0,0xffffffff)):
                result=loading(program,api,monitor,counter,stat,size)
                failed=stat!=0 or size<=0x20001234 or size==0xffffffff
                expected=[] if counter%2==0 else ([('Race/Starter',1)] if guarded or not failed
                                                 else [('Race/AttractMode',1),('Race/Type',1)])
                if result['writes']!=expected:raise ValueError(f'Native Loading contract {guarded,counter,stat,size}: {result}')
                rows.append({'guarded':guarded,'counter':counter,'stat':stat,'size':size,**result})
        for timer in (-1,0,1):
            m=Machine(program,api,monitor,0x465694,(0,));obj=m.alloc(bytes(32));m.put('ESI',obj);m.saved['ESI']=obj;m.write(obj+0x10,timer&0xffffffff)
            writes=[];modes=[]
            def boundary(pc):
                sp=m.reg('ESP')
                if pc==0x4d0580:m.write(m.reg('ECX'),m.read(sp+4));m.ret(m.reg('ECX'),4)
                elif pc==0x4d8ec0:m.ret(0x720000)
                elif pc==0x4d7aa0:writes.append((m.text(m.read(m.read(sp+4))),m.read(sp+8)));m.ret(None,8)
                elif pc==0x45d910:modes.append(m.read(sp+4));m.ret(None,4)
                elif pc==0x4656c6:m.ret(None,4) # Explicit stop before the unrelated menu-action/epilogue branch.
                else:return False
                return True
            try:
                m.execute(boundary)
                if writes!=([('Race/AttractMode',1)] if timer<0 else []) or modes!=([10] if timer<0 else []):raise ValueError('Idle Attract native branch changed')
                rows.append({'guarded':guarded,'idle_timer':timer,'writes':writes,'mode_transitions':modes,'steps':m.steps})
            finally:m.emu.dispose()
    return {'phase':'R-ATTR1','status':'CONFIRMED_BY_SYNTHETIC_TEST','runtime_game_test':False,
            'loading_cases':60,'idle_branch_cases':6,'project_saved':False,'only_in_memory_patch_va':'0x00464F69',
            'boundaries':['stat','allocation','Broker setters','native menu transition','idle branch stop at 004656C6'],
            'existing_attract_false_writes':0,'cases':rows}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('install','project','binary','java','output'):ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args();inspect(a.binary.read_bytes());output=a.output.resolve()
    if not output.is_relative_to(ROOT/'scratch-camera') or output.suffix!='.json':raise ValueError('Use the ignored non-dotted renderer scratch-camera directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    import pyghidra
    from pyghidra.launcher import HeadlessPyGhidraLauncher
    launcher=HeadlessPyGhidraLauncher(install_dir=a.install);launcher.java_home=a.java
    launcher.add_vmargs('-Dapplication.settingsdir='+str(output.parent/'settings'),'-Dapplication.cachedir='+str(output.parent/'cache'),'-Dapplication.tempdir='+str(output.parent/'temp'));launcher.start()
    from java.lang import Object
    from ghidra.framework.data import DefaultProjectData
    from ghidra.framework.model import ProjectLocator
    from ghidra.program.flatapi import FlatProgramAPI
    project=DefaultProjectData(ProjectLocator(str(a.project),'MasterRallye'),False,False);consumer=Object();program=None;tx=None
    try:
        program=project.getFile('/MRallye.exe').getReadOnlyDomainObject(consumer,-1,pyghidra.task_monitor())
        if str(program.getExecutableSHA256()).lower()!=SHA:raise ValueError('Ghidra exact-build mismatch')
        tx=program.startTransaction('R-ATTR1 temporary five-byte emulation')
        result=run(program,FlatProgramAPI(program),pyghidra.task_monitor())
        output.write_text(json.dumps(result,indent=2)+'\n');print('R-ATTR1 native emulation: 60 Loading + 6 idle branch cases PASS')
    finally:
        if program is not None:
            if tx is not None:program.endTransaction(tx,False)
            program.release(consumer)
        project.close()

if __name__=='__main__':main()
