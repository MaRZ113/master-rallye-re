"""Bounded actual x86 count/roster, storage, publication and teardown for N6..8."""
import argparse,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import r_ai2_1_capacity as c
import r_ai2_emulate as old
M=old.BoundedMachine

def setup(program,api,monitor,total,state,direct=False):
    m=M(program,api,monitor,c.CAVE if direct else 0x47B780);writes=[];reads=[];fallback=[]
    registry=m.alloc(bytes(0x1000));quick=m.alloc(bytes(0x100));race=m.alloc(bytes(0x100))
    for id in range(25):m.write(registry+id*0x34+12,0 if id<7 else 1 if id<14 else 2)
    m.put('ECX',quick);numcars=[0];participants={}
    expected=c.effective_opponents(total,**state)
    getters={0x4AE090:'mode',0x4AE2D0:'split',0x4AE0F0:'ghost',0x4AE030:'track'}
    def boundary(pc):
        sp=m.reg('ESP')
        if pc==0x4AE700:m.ret(quick)
        elif pc==0x4ADA50:m.ret(race)
        elif pc==0x4AE150:reads.append(state['opponents']);m.ret(state['opponents'])
        elif pc in getters:m.ret(int(state[getters[pc]]))
        elif pc==0x4ADFB0:m.ret(state['player'],4)
        elif pc==0x45A3C0:m.ret(registry)
        elif pc in (0x4AE1B0,0x4AE210):m.ret(0)
        elif pc in (0x4ACAF0,0x4ACC10,0x4ACCD0):
            n,value=m.read(sp+4),m.read(sp+8)
            if not 0<=n<expected+1:raise ValueError('Participant setter one-past-end')
            key={0x4ACAF0:'CarID',0x4ACC10:'CarClass',0x4ACCD0:'DriverID'}[pc]
            participants.setdefault(n,{})[key]=value;writes.append((n,key,value));m.ret(None,8)
        elif pc in (0x4AC2B0,0x4AC220,0x4AC1C0,0x4AC500,0x4AC3D0,0x4AC4D0):
            if pc==0x4AC3D0:numcars[0]=m.read(sp+4)
            m.ret(None,4)
        elif pc==0x4AC040:m.ret(numcars[0])
        elif pc in (0x4AC660,0x4AC730):
            if m.read(sp+4)!=0:raise ValueError('Unexpected human identity getter')
            id=state['player'];m.ret(id if pc==0x4AC660 else 0 if id<7 else 1 if id<14 else 2,4)
        elif pc==0x458950:m.ret(0x720000)
        elif pc==0x458090:fallback.append([m.read(sp+4),m.read(sp+8)]);m.ret(None,20)
        else:return False
        return True
    try:
        m.execute_bounded(boundary)
        if direct:
            if m.reg('EAX')!=expected or reads!=[state['opponents']]:raise ValueError('Count shim mismatch')
        else:
            if numcars[0]!=expected+1:raise ValueError('NumCars mismatch')
            active=state['mode']==2 and expected==total-1
            if active:
                wanted={n:{'CarID':id,'CarClass':0 if id<7 else 1 if id<14 else 2,'DriverID':n-1} for n,id in enumerate(c.ROSTER[1:total],1)}
                if {n:p for n,p in participants.items() if n}!=wanted or fallback:raise ValueError('Deterministic roster publication mismatch')
            elif state['mode']!=1 and fallback!=[[1,expected]]:raise ValueError('Stock chooser fallback lost')
        return dict(kind='count/roster',total=total,direct=direct,state=state,NumCars=numcars[0],participants=participants,stock_chooser_calls=fallback,original_reads=len(reads),redzones_intact=True)
    finally:m.emu.dispose()

def vector(program,api,monitor,count):
    m=M(program,api,monitor,0x43BB70);obj=m.alloc(bytes(16));value=m.alloc(bytes(4));lengths=[]
    try:
        for n in range(count):
            m.write(value,n);m.put('ECX',obj);m.put('ESP',m.stack);m.put('EIP',0x43BB70)
            for i,v in enumerate((m.stop,m.read(obj+8),1,value)):m.write(m.stack+i*4,v)
            m.execute_bounded(m.heap_boundary,12)
            begin,end,capacity=(m.read(obj+i) for i in (4,8,12))
            if end-begin!=(n+1)*4 or end>capacity or [m.read(begin+i*4) for i in range(n+1)]!=list(range(n+1)):raise ValueError('Vector capacity violation')
            lengths.append(n+1)
        return dict(kind='physical vector',indices=list(range(count)),lengths=lengths,allocation_sizes=[s for _,s in m.native_allocations],redzones_intact=True)
    finally:m.emu.dispose()

def cleanup(program,api,monitor,total,ai=False):
    count=total-1 if ai else total;m=M(program,api,monitor,0x42A6B0 if ai else 0x43E020)
    obj=m.alloc(bytes(0xC8 if ai else 0x80));vec=m.alloc(bytes(count*4));items=[m.alloc(bytes(0xD4 if ai else 0x2C)) for _ in range(count)]
    for n,p in enumerate(items):m.write(vec+n*4,p)
    begin=0x88 if ai else 0x18
    for offset,value in ((begin,vec),(begin+4,vec+count*4),(begin+8,vec+count*4)):m.write(obj+offset,value)
    m.put('ECX',obj);destroyed=[]
    def boundary(pc):
        if m.heap_boundary(pc):return True
        if pc==(0x42CDA0 if ai else 0x4436C0):destroyed.append(m.reg('ECX'));m.ret()
        elif ai and pc in (0x429F60,0x42B4F0):m.ret()
        else:return False
        return True
    try:
        m.execute_bounded(boundary)
        if destroyed!=items or m.frees!=items+[vec]:raise ValueError('Cleanup missed/aliased participant')
        return dict(kind='AI cleanup' if ai else 'physics cleanup',indices=list(range(1,total)) if ai else list(range(total)),redzones_intact=True)
    finally:m.emu.dispose()

def physics_enumeration(program,api,monitor,count):
    m=M(program,api,monitor,0x43EF80,(0,));obj=m.alloc(bytes(0x80));m.put('ECX',obj);indices=[]
    def boundary(pc):
        sp=m.reg('ESP')
        if pc==0x4D0580:m.ret(m.reg('ECX'),4)
        elif pc in (0x4D8EC0,0x4F6310):m.ret(m.reg('ECX'))
        elif pc==0x4D6650:m.emu.writeRegister('ST0',0);m.ret(None,4) # float Broker property boundary
        elif pc==0x4D6760:m.ret(count,4)
        elif pc==0x4F5EB0:m.ret(0,4)
        elif pc==0x43EE00:m.ret(None,4)
        elif pc==0x43F020:
            n=m.read(sp+4)
            if not 0<=n<count:raise ValueError('Physics actor index outside N')
            indices.append(n);m.ret(None,4)
        elif pc in (0x43EF40,0x43F310,0x43F890):m.ret()
        else:return False
        return True
    try:
        m.execute_bounded(boundary,4)
        if indices!=list(range(count)):raise ValueError('Physics count enumeration mismatch')
        return dict(kind='physics init enumeration',indices=indices,body_constructor_boundary=True,redzones_intact=True)
    finally:m.emu.dispose()

def network_eight(program,api,monitor):
    m=M(program,api,monitor,0x4333D0);obj=m.alloc(bytes(0xC8));buffer=m.alloc(bytes(0x800));m.write(obj+0x10,buffer);m.write(obj+0x80,0xDEADC0DE);m.put('ECX',obj);paths=[]
    def boundary(pc):
        sp=m.reg('ESP')
        if pc==0x5C20BA:
            dest,fmt=m.read(sp+4),m.text(m.read(sp+8));text=fmt%m.read(sp+12);m.emu.writeMemory(api.toAddr(dest),text.encode()+b'\0');m.ret(len(text))
        elif pc==0x4D0580:paths.append(m.text(m.read(sp+4)));m.ret(m.reg('ECX'),4)
        elif pc==0x4D8EC0:m.ret(m.reg('ECX'))
        elif pc in (0x4D7AA0,0x4D7ED0):m.ret(None,8)
        else:return False
        return True
    try:
        m.execute_bounded(boundary)
        if any(m.read(obj+0x60+i*4) for i in range(8)) or m.read(obj+0x80)!=0xDEADC0DE:raise ValueError('Inline [8] boundary crossed')
        indices=sorted({int(x) for p in paths if (match:=re.search(r'Car(\d+)',p)) for x in (match[1],)})
        if indices!=list(range(8)):raise ValueError('Network eight keys mismatch')
        return dict(kind='native inline Network [8]',base='+0x60',stride=4,count=8,next_field_80_unchanged=True,indices=indices,redzones_intact=True)
    finally:m.emu.dispose()

def ai_enumeration(program,api,monitor,count):
    m=M(program,api,monitor,0x42A890,(0,));obj=m.alloc(bytes(0xC8));m.put('ECX',obj);current=[''];bound=[];inserted=[]
    wrapper=m.alloc(bytes(4));rng=m.alloc(bytes(4));vt=m.alloc(bytes(8));m.write(wrapper,rng);m.write(rng,vt);m.write(vt+4,0x7FF200);m.write(0x6F8B94,wrapper)
    def boundary(pc):
        sp=m.reg('ESP')
        if m.heap_boundary(pc):return True
        if pc==0x4AE700:m.ret(0x720000)
        elif pc==0x4ADB70:m.ret(0)
        elif pc==0x42B1B0:m.ret(0)
        elif pc==0x42AD30:m.ret(None,8)
        elif pc==0x5C20BA:
            dest,fmt=m.read(sp+4),m.text(m.read(sp+8));text=fmt%m.read(sp+12);m.emu.writeMemory(api.toAddr(dest),text.encode()+b'\0');m.ret(len(text))
        elif pc==0x4D0580:current[0]=m.text(m.read(sp+4));m.ret(m.reg('ECX'),4)
        elif pc==0x4D8EC0:m.ret(0x720000)
        elif pc==0x4D6760:
            path=current[0];match=re.search(r'Car(\d+)',path)
            if match:
                n=int(match[1])
                if not 0<=n<count:raise ValueError('AI getter one-past-end')
                value=(1 if n==0 else 2) if path.endswith('PlayerType') else n-1
            elif path=='Race/NumCars':value=count
            else:raise ValueError('Unknown AI integer key '+path)
            m.ret(value,4)
        elif pc==0x4D7470:m.ret(int(current[0].endswith('DriverID')),4)
        elif pc==0x42CC30:m.ret(m.reg('ECX'))
        elif pc==0x42AC80:m.ret(0,4)
        elif pc==0x42ABD0:m.ret(m.reg('ECX'),4)
        elif pc==0x42CDB0:
            n=m.read(sp+4)
            if not 1<=n<count:raise ValueError('AI binding outside active AI')
            bound.append(n);m.ret(None,20)
        elif pc==0x42AD40:inserted.append(m.read(m.read(sp+12)));m.ret(None,12)
        elif pc==0x42AF50:m.ret(None,12)
        elif pc in (0x42B6D0,0x42B830,0x7FF200):m.ret(None,4)
        else:return False
        return True
    try:
        m.execute_bounded(boundary,4)
        if bound!=list(range(1,count)) or len(set(inserted))!=count-1 or sum(s==0xD4 for _,s in m.native_allocations)!=count-1:raise ValueError('AI count/allocation mismatch')
        return dict(kind='native AI allocation/enumeration',indices=bound,independent_allocations=count-1,controller_constructor_profile_boundary=True,redzones_intact=True)
    finally:m.emu.dispose()

def replay_array(program,api,monitor,count):
    m=M(program,api,monitor,0x4CADF0,(count,));obj=m.alloc(bytes(4));m.put('ECX',obj);constructed=[]
    def boundary(pc):
        sp=m.reg('ESP')
        if m.heap_boundary(pc):return True
        if pc==0x5C210C:
            ptr,stride,n=m.read(sp+4),m.read(sp+8),m.read(sp+12)
            if stride!=16 or n!=count:raise ValueError('Replay array constructor count')
            constructed.extend(range(n));m.ret(None,20)
        else:return False
        return True
    try:
        m.execute_bounded(boundary,4);ptr=m.read(obj)
        if m.native_allocations[0][1]!=count*16+4 or m.read(ptr-4)!=count or constructed!=list(range(count)):raise ValueError('Replay cookie/physical extent mismatch')
        return dict(kind='native replay allocation',indices=constructed,stride=16,size=count*16+4,per_record_constructor_boundary=True,redzones_intact=True)
    finally:m.emu.dispose()

def vehicle_publication_loop(program,api,monitor,count):
    m=M(program,api,monitor,0x44A320);m.put('ECX',m.alloc(bytes(0x40)));visits={'type':[],'family':[],'physics':[]}
    def boundary(pc):
        sp=m.reg('ESP')
        if pc in (0x4ADA50,0x4D8EC0,0x44FA80):m.ret(0x720000)
        elif pc==0x4AC040:m.ret(count)
        elif pc==0x4AC070:m.ret(1)
        elif pc==0x4ABE90:m.ret(2)
        elif pc in (0x44A450,0x44A510,0x44ED50):
            n=m.read(sp+4)
            if not 0<=n<count:raise ValueError('Vehicle publication outside N')
            visits[{0x44A450:'type',0x44A510:'family',0x44ED50:'physics'}[pc]].append(n);m.ret(None,8)
        elif pc==0x4D0580:m.ret(m.reg('ECX'),4)
        elif pc==0x4D6520:m.ret(0,4)
        elif pc==0x4AD3C0:m.ret(None,8)
        elif pc==0x4AC430:m.ret(None,4)
        else:return False
        return True
    try:
        m.execute_bounded(boundary)
        if any(v!=list(range(count)) for v in visits.values()):raise ValueError('Vehicle path publication misses participant')
        return dict(kind='native vehicle/Broker preparation enumeration',visits=visits,family_physics_helpers_are_boundaries=True,redzones_intact=True)
    finally:m.emu.dispose()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('install','project','source','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();source=a.source.read_bytes()
    for n in c.TOTALS:c.build(source,n)
    import pyghidra
    pyghidra.start(install_dir=a.install)
    from java.lang import Object
    from ghidra.program.flatapi import FlatProgramAPI
    project=pyghidra.open_project(a.project,'MasterRallye');consumer=Object();g=project.getProjectData().getFile('/MRallye.exe').getReadOnlyDomainObject(consumer,-1,pyghidra.task_monitor());tx=g.startTransaction('R-AI2.1 unsaved bounded proof')
    try:
        if str(g.getExecutableSHA256())!=c.RETAIL_SHA256:raise ValueError('Unknown pristine project')
        api=FlatProgramAPI(g);monitor=pyghidra.task_monitor();rows=[]
        normal=dict(opponents=3,mode=2,split=False,ghost=0,player=0,track=10)
        states=[normal]+[{**normal,k:v} for k,v in (('opponents',0),('opponents',1),('opponents',2),('mode',1),('mode',3),('ghost',1),('player',1),('player',7),('track',9))]
        for n in c.TOTALS:
            for r in c.ranges(n):
                if r['va'] is None:continue
                addr=api.toAddr(r['va']);data=r['replacement'];api.clearListing(addr,addr.add(len(data)-1));g.getMemory().setBytes(addr,data);api.disassemble(addr)
            rows.extend(setup(g,api,monitor,n,s,direct=d) for s in states for d in (True,False))
            rows.append(setup(g,api,monitor,n,{**normal,'split':True},direct=True))
            rows.extend((vector(g,api,monitor,n),cleanup(g,api,monitor,n),cleanup(g,api,monitor,n,True),old.progress_init(g,api,monitor,n),old.result_records(g,api,monitor,n),physics_enumeration(g,api,monitor,n),ai_enumeration(g,api,monitor,n),replay_array(g,api,monitor,n),vehicle_publication_loop(g,api,monitor,n)))
        rows.append(network_eight(g,api,monitor))
        report=dict(status='STATIC_CAPACITY_6_7_8_MATCH_ONLY',passed=len(rows),failed=0,skipped=0,runtime_full_pass=False,source_sha256=c.RETAIL_SHA256,rows=rows,limits='Controlled typed Broker/heap/scene/body/ranking boundaries; no collision/damage/rendering/AI driving simulation',project_saved=False)
        c.ignored_output(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
    finally:g.endTransaction(tx,False);g.release(consumer);project.close()
if __name__=='__main__':main()
