"""Interleaved multi-owner original-SFX lifecycle replay, not audible gameplay."""
import argparse,copy,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from vehicle_whine_native import append_whine,SITES,NEW,RACE_BROKER,CAR_ID,INTERN
from vehicle_audio_native import append_audio
from validate_vehicle_physics_forces import machine,ptr,f32,get
from master_rallye.vehicle_physics_binding import parse_pe32_layout


def replay(exe,profiles):
    from unicorn import UC_HOOK_CODE,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC
    from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESI as SI,UC_X86_REG_EDI as DI,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP
    if len(profiles)!=2:raise ValueError('supply exactly two independent audio profiles')
    image,blob,engine_report=append_audio(exe,exe,b'',0x10000000,profiles,65536)
    image,blob,report=append_whine(exe,image,blob,0x10000000,profiles,65536)
    u=machine(exe);u.mem_map(0x10000000,65536);u.mem_write(0x10000000,blob);u.mem_protect(0x10000000,65536,UC_PROT_READ|UC_PROT_EXEC)
    for region in report['writable_ranges']:u.mem_protect(0x10000000+region['offset'],region['size'],UC_PROT_READ|UC_PROT_WRITE)
    layout=parse_pe32_layout(exe)
    for name,(site,before) in SITES.items():u.mem_write(site,image[layout.va_to_file_offset(site):layout.va_to_file_offset(site)+len(before)])
    owners=[0x2000000,0x2001000,0x2002000];binders=[p+0x100 for p in owners];dynamics=[p+0x200 for p in owners];actors=[p+0x300 for p in owners];engines=[p+0x400 for p in owners]
    manager=0x2005000;live=manager+0x100;retired=manager+0x200;ptr(u,manager+0x10,live);ptr(u,live,live);ptr(u,live+4,live);ptr(u,manager+0x1c,retired);ptr(u,retired,retired);ptr(u,retired+4,retired)
    for i in range(3):ptr(u,owners[i]+0x54,i);ptr(u,binders[i]+8,dynamics[i]);ptr(u,actors[i]+0x10,engines[i])
    physical=[profiles[0]['physical_car_id'],profiles[1]['physical_car_id'],7];selected=[0];heap=[0x2008000];interned=[];freed=[];clock=[10000]
    def word(at):return struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
    def ret(pop=0):sp=u.reg_read(SP);u.reg_write(IP,word(sp));u.reg_write(SP,sp+4+pop)
    def hook(uc,address,size,data):
        sp=uc.reg_read(SP)
        if address==NEW:
            n=word(sp+4);p=heap[0];heap[0]+=(n+15)//16*16;uc.reg_write(AX,p);uc.reg_write(CX,0xdead0101);uc.reg_write(DX,0xbeef0101);ret()
        elif address==RACE_BROKER:
            if word(sp+4)!=selected[0]:raise ValueError('wrong slot')
            uc.reg_write(AX,0x2007000);uc.reg_write(CX,0xdead);uc.reg_write(DX,0xbeef);ret()
        elif address==CAR_ID:
            if word(sp+4)!=selected[0] or uc.reg_read(CX)!=0x2007000:raise ValueError('wrong getter ABI')
            uc.reg_write(AX,physical[selected[0]]);uc.reg_write(CX,0xdead);uc.reg_write(DX,0xbeef);ret(4)
        elif address==INTERN:
            name=bytes(uc.mem_read(word(sp+4),96)).split(b'\0',1)[0].decode();interned.append((selected[0],name));ptr(uc,uc.reg_read(CX),0x33445566);ret(4)
        elif address==0x12341000:clock[0]+=16;uc.reg_write(AX,clock[0]);ret()
        elif address==0x4f68f0:uc.reg_write(AX,manager);ret()
        elif address==0x5b4c00:freed.append(word(sp+4));ret()
    u.mem_map(0x12341000,4096);ptr(u,0x68f3a0,0x12341000);u.hook_add(UC_HOOK_CODE,hook)
    events=[];stack=0x100e000;state=report['entries']['voices'];stride=report.get('voice_slot_stride',44)
    def slot(i):
        return next((state+k*stride for k in range(64) if word(state+k*stride)==owners[i]),None)
    def voices(i):
        p=slot(i);return [word(p+4+k*4) for k in range(3)] if p else []
    def setup(i):
        selected[0]=i;u.reg_write(SI,owners[i]);u.reg_write(DI,binders[i]);u.reg_write(SP,stack);u.reg_write(CX,0x33334444);u.reg_write(DX,0x55556666)
    def run(name,i):
        setup(i)
        if name=='construct':ptr(u,stack+0x88,0x12345678)
        if name=='publish':ptr(u,stack+0x58,actors[i]);ptr(u,stack+0x1c,engines[i])
        if name=='update':f32(u,stack+0x10,1);u.mem_write(stack+0xf,b'\0')
        end={'construct':0x409cb4,'publish':0x492cd1,'update':0x40a02c}[name]
        u.emu_start(SITES[name][0],end,count=100000)
        if u.reg_read(SP)!=stack or u.reg_read(IP)!=end:raise ValueError('seam ABI failure')
        events.append((name,i))
    def update(i,load=1):
        f32(u,engines[i]+0x28,4000*.10471967);f32(u,engines[i]+0x50,500);f32(u,engines[i]+0x94,load*500);ptr(u,engines[i]+0x78,2);run('update',i)
    def destroy(i):
        setup(i);ptr(u,owners[i]+0xc,0);ptr(u,owners[i]+0x10,0);u.reg_write(CX,owners[i]);u.reg_write(SP,stack-12);ptr(u,stack,0x1002000);u.emu_start(SITES['destroy'][0],0x409e9a,count=100000);events.append(('destroy',i))
    # First live owner is already bound before the second constructor runs.
    run('construct',0);run('publish',0);update(0);map_before=bytes(u.mem_read(report['entries']['map'],512))
    run('construct',1)
    if map_before!=bytes(u.mem_read(report['entries']['map'],512)):raise ValueError('second construction cleared first publication')
    run('publish',1)
    for _ in range(120):update(0);update(1)
    va,vb=voices(0),voices(1)
    if set(v for v in va if v)&set(v for v in vb if v):raise ValueError('owners share SFX voices')
    if get(u,slot(0)+20)<.9 or get(u,slot(1)+20)<.9:raise ValueError('independent spool did not accumulate')
    before=word(slot(1)+32);update(0,0)
    if word(slot(0)+32)!=1 or word(slot(1)+32)!=before:raise ValueError('BOV event leaked between owners')
    # Stock construction/update cannot allocate sidecars or alter existing state.
    old=bytes(u.mem_read(state,64*stride));count=word(manager+0x14);run('construct',2);run('publish',2);update(2)
    if slot(2) or word(manager+0x14)!=count or old!=bytes(u.mem_read(state,64*stride)):raise ValueError('stock audio pass-through changed addon state')
    destroy(0)
    if any(v not in freed for v in va if v) or any(v in freed for v in vb if v):raise ValueError('destruction ownership mismatch')
    update(1)
    if get(u,slot(1)+20)<.9 or not any(get(u,v+0x10)>0 for v in vb if v):raise ValueError('survivor lost publication/audio')
    run('construct',0);update(0)
    if any(get(u,v+0x10)!=0 for v in voices(0) if v):raise ValueError('recreated owner used stale publication')
    update(1);run('publish',0);update(0)
    destroy(0);destroy(1)
    if word(manager+0x14) or any(u.mem_read(report['entries']['map'],512)):raise ValueError('last destruction leaked live state')
    # New race, same addresses, must wait for new publication.
    run('construct',1);update(1)
    if any(get(u,v+0x10)!=0 for v in voices(1) if v):raise ValueError('race reentry retained actor')
    run('publish',1);update(1);destroy(1)
    expected=[(i,'vehicles/sdk/'+p['namespace']+'/'+key) for i,p in enumerate(profiles) for key in ('transmission_whine','turbo_spool','bov_release') if key in p]
    if not set(expected)<=set(interned):raise ValueError('independent supplemental resource missing')
    # Check generated per-donor engine source wrapper independently of SFX list.
    for i,p in enumerate(profiles):
        entry=next(r['entry_va'] for r in engine_report['entries'] if any(x['physical_car_id']==p['physical_car_id'] for x in r['profiles']))
        setup(i);ptr(u,stack,0x1002000);ptr(u,stack+4,0x2007800);u.reg_write(CX,0x2007900);u.emu_start(entry,0x1002000,count=100000)
        if interned[-1]!=(i,'vehicles/sdk/'+p['namespace']+'/engine'):raise ValueError('engine identity mismatch')
    return {'status':'PASS_MULTI_OWNER_NATIVE_AUDIO_CPU_REPLAY','profiles':[{'physical_car_id':p['physical_car_id'],'namespace':p['namespace']} for p in profiles],
        'slot_stride':stride,'events':events,'interned_resources':sorted(set(interned)),'freed_voices':len(freed),'state_isolation':True,'stock_passthrough':True,'reentry':True,
        'boundary':'generated hooks/helper and original native SFX constructors/manager/destructors; Broker/interner/clock/allocator/free are typed mocks; Windows FS SEH prologue excluded; no game or DirectSound device/audio audibility proof','runtime_qualified':False,'exe_sha256':hashlib.sha256(exe).hexdigest()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--exe',type=Path,required=True);parser.add_argument('--profile',type=Path,action='append',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    report=replay(args.exe.read_bytes(),[json.loads(p.read_text()) for p in args.profile]);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
