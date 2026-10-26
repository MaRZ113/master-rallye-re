"""Local exact-x86 whine seam/ownership replay; does not launch the game."""
from __future__ import annotations
import argparse,copy,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from vehicle_whine_native import append_whine,SITES,NEW,SFX_CONSTRUCTOR,response_values,RACE_BROKER,CAR_ID,INTERN
from validate_vehicle_physics_forces import machine,ptr,f32,get
from master_rallye.vehicle_physics_binding import parse_pe32_layout


def replay(exe,profile,*,gain_curve=False,fail_allocation=None):
    if fail_allocation is not None and (type(fail_allocation)is not int or not 1<=fail_allocation<=3):raise ValueError('failure index must be 1..3')
    from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC,UcError,UC_ERR_WRITE_PROT
    from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESI as SI,UC_X86_REG_EDI as DI,UC_X86_REG_EBX as BX,UC_X86_REG_EBP as BP,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EFLAGS as FL,UC_X86_REG_FPSW as FSW
    other=copy.deepcopy(profile);other['physical_car_id']=profile['physical_car_id']+1;other['namespace']='whine_probe_second'
    if 'transmission_whine' in other:other['transmission_whine']['response']['gain_drive']=.27;other['transmission_whine']['response']['gain_coast']=.05
    prefix=b'UNCHANGED_ENGINE_EXTENSION_PREFIX';baseva=0x10000000
    image,blob,report=append_whine(exe,exe,prefix,baseva,[profile,other],65536);layout=parse_pe32_layout(exe)
    if blob[:len(prefix)]!=prefix:raise ValueError('old payload prefix changed')
    u=machine(exe);u.mem_map(baseva,65536);u.mem_write(baseva,blob)
    # Match the real launcher: code is RX, only the exact map page is RW/NX.
    # Page zero deliberately remains unmapped so NULL dereferences fail.
    u.mem_protect(baseva,65536,UC_PROT_READ|UC_PROT_EXEC)
    for region in report['writable_ranges']:
        u.mem_protect(baseva+region['offset'],region['size'],UC_PROT_READ|UC_PROT_WRITE)
    for name,(site,before) in SITES.items():
        at=layout.va_to_file_offset(site);u.mem_write(site,image[at:at+len(before)])
    owner=0x2000000;binder=0x2001000;dynamic=0x2002000;actor=0x2003000;engine=0x2004000;manager=0x2005000
    live=0x2006000;retired=0x2006100;heap=[0x2008000];slot=[0];physical=[profile['physical_car_id']];observed=[];freed=[];ds_calls=[];clock=[10000]
    ptr(u,manager+0x10,live);ptr(u,live,live);ptr(u,live+4,live)
    ptr(u,manager+0x1c,retired);ptr(u,retired,retired);ptr(u,retired+4,retired)
    ptr(u,binder+8,dynamic);ptr(u,actor+0x10,engine);ptr(u,owner+0x54,slot[0])
    writes=[];allocation_number=[0]
    def word(at):return struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
    def ret(pop=0):
        sp=u.reg_read(SP);u.reg_write(IP,word(sp));u.reg_write(SP,sp+4+pop)
    def hook(uc,address,size,data):
        sp=uc.reg_read(SP)
        if 0x12341200<=address<0x12341300:
            method=address-0x12341200;args=[word(sp+i*4) for i in range(1,5)];ds_calls.append((method,args))
            if method==0x24:ptr(uc,args[1],0)
            ret({0x30:16,0x3c:8,0x44:8,0x24:8,0x48:4}[method])
        elif address==NEW:
            n=word(sp+4)
            if n==0x5c:allocation_number[0]+=1
            failed=n==0x5c and allocation_number[0]==fail_allocation
            p=0 if failed else heap[0]
            if not failed:heap[0]+=max(16,(n+15)//16*16)
            uc.reg_write(AX,p);uc.reg_write(CX,0xdead0101);uc.reg_write(DX,0xbeef0101);ret()
        elif address==RACE_BROKER:
            if word(sp+4)!=slot[0]:raise ValueError('wrong participant slot')
            uc.reg_write(AX,0x2007000);uc.reg_write(CX,0xdead);uc.reg_write(DX,0xbeef);ret()
        elif address==CAR_ID:
            if word(sp+4)!=slot[0] or uc.reg_read(CX)!=0x2007000:raise ValueError('wrong native CarID ABI')
            uc.reg_write(AX,physical[0]);uc.reg_write(CX,0xdead0202);uc.reg_write(DX,0xbeef0202);uc.reg_write(FL,0x246);ret(4)
        elif address==INTERN:
            name=bytes(uc.mem_read(word(sp+4),96)).split(b'\0',1)[0].decode();observed.append(name)
            ptr(uc,uc.reg_read(CX),0x33445566);uc.reg_write(AX,0xdead0303);uc.reg_write(CX,0xdead0304);uc.reg_write(DX,0xbeef0303);ret(4)
        elif address==0x12341000:clock[0]+=16;uc.reg_write(AX,clock[0]);ret()
        elif address==0x4f68f0:uc.reg_write(AX,manager);ret()
        elif address==0x5b4c00:freed.append(word(sp+4));ret()
    u.mem_map(0x12341000,4096);ptr(u,0x68f3a0,0x12341000)
    u.hook_add(UC_HOOK_CODE,hook)
    u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,address,size,value,data:writes.append((address,size)))
    regs={AX:0x11112222,CX:0x33334444,DX:0x55556666,SI:owner,DI:binder,BX:0x77778888,BP:0x9999aaaa}
    def setup():
        for reg,value in regs.items():u.reg_write(reg,value)
        u.reg_write(SP,0x100e000);u.reg_write(FL,0x203)
    def run(name,end):
        start=SITES[name][0];u.emu_start(start,end,count=50000)
        if u.reg_read(IP)!=end or u.reg_read(SP)!=0x100e000:raise ValueError(name+' seam stack/end mismatch')
        if u.reg_read(FL)!=0x203:raise ValueError(name+' seam flags changed')
        expected=dict(regs)
        if name=='construct':expected[CX]=0x12345678
        if name=='publish':expected[CX]=dynamic;expected[DX]=engine
        if name=='update':expected[CX]=dynamic;expected[DX]=owner+0x78
        if any(u.reg_read(reg)!=value for reg,value in expected.items()):raise ValueError(name+' seam register preservation failed')

    # Regression: reproduce the actual previous-launcher policy, not just an
    # arbitrary malformed input. The universal publisher must fault on RX data.
    region=report['writable_ranges'][0]
    u.mem_protect(baseva+region['offset'],region['size'],UC_PROT_READ|UC_PROT_EXEC)
    setup();ptr(u,0x100e000+0x58,actor);ptr(u,0x100e000+0x1c,engine)
    try:u.emu_start(SITES['publish'][0],0x492cd1,count=50000)
    except UcError as error:
        if error.errno!=UC_ERR_WRITE_PROT:raise
    else:raise ValueError('prior RX map policy did not reproduce write protection fault')
    u.mem_protect(baseva+region['offset'],region['size'],UC_PROT_READ|UC_PROT_WRITE)

    # Native SFX constructor and intrusive-list registration execute unchanged.
    setup();ptr(u,0x100e000+0x88,0x12345678);run('construct',0x409cb4)
    if fail_allocation is not None:
        count=sum(k in profile for k in ('transmission_whine','turbo_spool','bov_release'))
        if count!=3:raise ValueError('failure fixture needs all three supplemental layers')
        active=[word(report['entries']['voices']+4+i*4) for i in range(3)]
        if active[fail_allocation-1] or sum(bool(v) for v in active)!=2 or word(manager+0x14)!=2:raise ValueError('optional allocation failure damaged siblings')
        if word(owner+0x14):raise ValueError('failure overwrote stock optional owner')
        setup();ptr(u,0x100e000+0x58,actor);ptr(u,0x100e000+0x1c,engine);run('publish',0x492cd1)
        for _ in range(20):
            setup();f32(u,engine+0x28,4000*.10471967);f32(u,engine+0x50,500);f32(u,engine+0x94,500);ptr(u,engine+0x78,2);f32(u,0x100e010,1);u.mem_write(0x100e00f,b'\0');run('update',0x40a02c)
        def destroy_failed():
            ptr(u,owner+0xc,0);ptr(u,owner+0x10,0);u.reg_write(CX,owner);u.reg_write(SP,0x100e000-12);u.emu_start(0x409e25,0x409e9a,count=50000)
        destroy_failed()
        if word(manager+0x14) or any(v not in freed for v in active if v) or any(u.mem_read(report['entries']['map'],512)):raise ValueError('failed-source owner cleanup leaked state')
        setup();ptr(u,0x100e000+0x88,0x12345678);run('construct',0x409cb4)
        if word(manager+0x14)!=3:raise ValueError('reentry after allocation failure lost voices')
        setup();f32(u,0x100e010,1);run('update',0x40a02c)
        if any(get(u,word(report['entries']['voices']+4+i*4)+0x10)!=0 for i in range(3)):raise ValueError('failure reentry retained old actor')
        destroy_failed()
        if word(manager+0x14):raise ValueError('failure reentry cleanup leaked voices')
        return {'status':'PASS_OPTIONAL_VOICE_ALLOCATION_FAILURE','failed_layer_index':fail_allocation,'surviving_voices':2,'freed_voices':len(freed),'reentry':True,'stock_optional_untouched':True,
                'boundary':'Original x86 SFX constructors/destructors and generated seams; allocator failure injected, no missing DirectSound buffer/device or gameplay proof'}
    layer_count=sum(k in profile for k in ('transmission_whine','turbo_spool','bov_release'));effect=word(report['entries']['voices']+4)
    if not effect:effect=word(report['entries']['voices']+8)
    if not effect:effect=word(report['entries']['voices']+12)
    expected_flags=b'\1\1' if any(k in profile for k in ('transmission_whine','turbo_spool')) else b'\0\0'
    if not effect or word(word(live)+8)!=effect or word(manager+0x14)!=layer_count or bytes(u.mem_read(effect+0xe,2))!=expected_flags:raise ValueError('native SFX loop/registration failed')
    if observed!=['vehicles/sdk/'+profile['namespace']+'/'+k for k in ('transmission_whine','turbo_spool','bov_release') if k in profile]:raise ValueError('resource identity mismatch')
    # Supplemental ownership never writes stock optional +14.
    if word(owner+0x14):raise ValueError('stock optional owner overwritten')
    # Physics tap uses the original actor argument; only external map is written.
    setup();ptr(u,0x100e000+0x58,actor);ptr(u,0x100e000+0x1c,engine)
    before=bytes(u.mem_read(actor,0x2000));writes.clear();run('publish',0x492cd1)
    if before!=bytes(u.mem_read(actor,0x2000)) or word(report['entries']['map'])!=dynamic or word(report['entries']['map']+4)!=actor:raise ValueError('publisher changed physics or mismatched actor')
    # Bounded map survives more allocations than capacity, then refreshes the
    # active key. No actor is dereferenced by the pointer-publication tap.
    for i in range(72):
        ptr(u,binder+8,0x3000000+i*0x100);setup();ptr(u,0x100e000+0x58,0x3100000+i*0x100);ptr(u,0x100e000+0x1c,engine)
        u.emu_start(SITES['publish'][0],0x492cd1,count=50000)
        if u.reg_read(SP)!=0x100e000:raise ValueError('bounded map overflow changed stack')
    ptr(u,binder+8,dynamic);setup();ptr(u,0x100e000+0x58,actor);ptr(u,0x100e000+0x1c,engine);run('publish',0x492cd1)
    rows=[]
    for identity in (profile['physical_car_id'],other['physical_car_id'],7,26):
      for rpm,load,gear,volume,finished in [(0,1,2,1,False),(500,1,2,1,False),(4000,1,2,1,False),(6000,-.2,2,.8,False),(9000,.5,2,.7,False),(4000,1,1,1,False),(4000,1,2,1,True)]:
        physical[0]=identity;setup();f32(u,engine+0x28,rpm*.10471967);f32(u,engine+0x50,500);f32(u,engine+0x94,500*load);ptr(u,engine+0x78,gear)
        f32(u,0x100e010,volume);u.mem_write(0x100e00f,bytes([finished]));f32(u,effect+0x10,.123);f32(u,effect+0x14,1.)
        physics_before=bytes(u.mem_read(actor,0x2000));fp_before=u.reg_read(FSW)&0x3800
        run('update',0x40a02c)
        if physics_before!=bytes(u.mem_read(actor,0x2000)) or (u.reg_read(FSW)&0x3800)!=fp_before:raise ValueError('update changed physics or unbalanced x87 stack')
        pitch,gain=get(u,effect+0x14),get(u,effect+0x10)
        selected=other if identity==other['physical_car_id'] else profile
        expected=response_values(selected['transmission_whine']['response'],rpm,load*500,500,gear,volume,finished) if 'transmission_whine' in selected else None
        if identity not in (profile['physical_car_id'],other['physical_car_id']):
            if abs(gain-.123)>1e-6 or pitch!=1.:raise ValueError('foreign CarID effect changed')
        elif expected is None:pass
        elif identity in (profile['physical_car_id'],other['physical_car_id']):
            if abs(pitch-expected['pitch'])>2e-6 or abs(gain-expected['gain'])>2e-6:raise ValueError('native whine control differs '+str((rpm,load,gear,pitch,gain,expected)))
        elif abs(gain-.123)>1e-6 or pitch!=1.:raise ValueError('foreign CarID effect changed')
        rows.append({'physical_car_id':identity,'rpm':rpm,'signed_crank_load':load,'gear_index':gear,'finished':finished,'pitch':pitch,'gain':gain})

    # Per-participant spool and load-release state over real elapsed-ms input.
    physical[0]=profile['physical_car_id'];state=report['entries']['voices']
    for step in range(150):
        setup();f32(u,engine+0x28,4000*.10471967);f32(u,engine+0x50,500);f32(u,engine+0x94,500);ptr(u,engine+0x78,2);f32(u,0x100e010,1);u.mem_write(0x100e00f,b'\0');run('update',0x40a02c)
    pressure=get(u,state+20)
    if 'turbo_spool' in profile and pressure<.9:raise ValueError('native spool did not rise')
    setup();f32(u,engine+0x94,0);f32(u,0x100e010,1);run('update',0x40a02c)
    bov=word(state+12)
    if bov:
        if word(state+32)!=1 or bytes(u.mem_read(bov+0xe,2))!=b'\1\0':raise ValueError('BOV load-release event/one-shot failed')
        for step in range(10):setup();f32(u,0x100e010,1);run('update',0x40a02c)
        if word(state+32)!=1:raise ValueError('BOV retriggered on held release')
        # Explicit neutral policy: a previously accumulated load release may
        # play only when permitted; idle and a second held release never do.
        count=word(state+32);u.mem_write(bov+0xe,b'\0');f32(u,state+20,.95);f32(u,state+24,1);f32(u,state+28,0)
        setup();ptr(u,engine+0x78,1);f32(u,engine+0x94,0);f32(u,0x100e010,1);run('update',0x40a02c)
        permitted=not profile['bov_release']['response'].get('mute_neutral',True)
        if word(state+32)!=count+int(permitted):raise ValueError('native BOV neutral policy failed')
        count=word(state+32);u.mem_write(bov+0xe,b'\0');f32(u,state+20,.95);f32(u,state+24,1);f32(u,state+28,0)
        setup();f32(u,engine+0x28,800*.10471967);f32(u,0x100e010,1);run('update',0x40a02c)
        if word(state+32)!=count:raise ValueError('native neutral idle triggered BOV')

    # Execute the original backend through DirectSound COM methods, not only
    # authored gain math. These methods are typed mock device boundaries.
    backend=0x2010000;holder=0x2010100;ds=0x2010200;vt=0x2010300;listener=0x2010400
    ptr(u,backend,holder);ptr(u,holder,ds);ptr(u,ds,vt);ptr(u,backend+0x1c,48000)
    for method in (0x30,0x3c,0x44,0x24,0x48):ptr(u,vt+method,0x12341200+method)
    f32(u,effect+0x10,.18);f32(u,effect+0x14,1.25);u.mem_write(effect+0xe,b'\1\1')
    ptr(u,backend+0x30,(-10000)&0xffffffff)
    for distance in (0,30,150,300):
        f32(u,listener,distance);u.reg_write(CX,backend);u.reg_write(SP,0x100e000)
        u.mem_write(0x100e000,struct.pack('<4I',0x1002000,effect,listener,1))
        u.emu_start(0x5a8300,0x1002000,count=50000)
        if u.reg_read(SP)!=0x100e010:raise ValueError('DirectSound update stack mismatch')
    if not any(k==0x30 and a[3]==1 for k,a in ds_calls):raise ValueError('original backend did not Play looping')
    if not any(k==0x44 and a[1]==60000 for k,a in ds_calls):raise ValueError('original backend did not SetFrequency')
    volumes=[a[1] if a[1]<0x80000000 else a[1]-0x100000000 for k,a in ds_calls if k==0x3c]
    if not any(-10000<x<0 for x in volumes) or volumes[-1]!=-10000:raise ValueError('original attenuation/volume path failed')

    calibration=[]
    for gain in (.08,.18,.30,.55,.60,.65):
        f32(u,listener,0);f32(u,effect+0x10,gain);u.reg_write(CX,backend);u.reg_write(SP,0x100e000);u.mem_write(0x100e000,struct.pack('<4I',0x1002000,effect,listener,1));u.emu_start(0x5a8300,0x1002000,count=50000)
        value=word(backend+0x30);value=value if value<0x80000000 else value-0x100000000
        calibration.append({'authored_gain':gain,'native_hundredth_db':value})
    curve_check=None
    if gain_curve:
        from vehicle_sfx_gain import sfx_volume_hundredth_db
        for i in range(10001):
            gain=i/10000;start=len(ds_calls)
            f32(u,listener,0);f32(u,effect+0x10,gain);u.reg_write(CX,backend);u.reg_write(SP,0x100e000);u.mem_write(0x100e000,struct.pack('<4I',0x1002000,effect,listener,1));u.emu_start(0x5a8300,0x1002000,count=50000)
            value=word(backend+0x30);value=value if value<0x80000000 else value-0x100000000
            if value!=sfx_volume_hundredth_db(gain):raise ValueError('native SFX gain curve mismatch at '+str(gain))
            del ds_calls[start:]
        curve_check={'status':'PASS','cases':10001,'step':.0001,'input_range':[0,1]}
    if bov:
        # Native nonloop completion clears +0E, stops, and does not self-rearm.
        ptr(u,backend+0x24,0);u.mem_write(bov+0xe,b'\1\0')
        for step in range(3):
            u.reg_write(CX,backend);u.reg_write(SP,0x100e000);u.mem_write(0x100e000,struct.pack('<4I',0x1002000,bov,listener,1));u.emu_start(0x5a8300,0x1002000,count=50000)
        if bytes(u.mem_read(bov+0xe,1))!=b'\0' or word(backend+0x24)!=0:raise ValueError('original BOV backend did not finish')
        if not any(k==0x48 for k,a in ds_calls):raise ValueError('native one-shot did not stop')

    events=word(state+32)
    # Original destructor unregisters and frees exactly the optional SFX.
    ptr(u,owner+0xc,0);ptr(u,owner+0x10,0);u.reg_write(CX,owner);u.reg_write(SP,0x100e000);ptr(u,0x100e000,0x1002000)
    # Skip only Windows SEH registration/restore (FS:[0]); the real TEB is
    # absent in Unicorn. Keep page zero unmapped instead of masking NULL reads.
    u.reg_write(SP,0x100e000-12)
    u.emu_start(0x409e25,0x409e9a,count=50000)
    if word(manager+0x14)!=0 or word(manager+0x20)!=layer_count or effect not in freed:raise ValueError('native optional SFX lifetime failed')
    if any(bytes(u.mem_read(report['entries']['map'],512))):raise ValueError('destruction left stale physics pointers')
    # Address reuse across races must remain muted before a new publication.
    ptr(u,report['entries']['map'],dynamic);ptr(u,report['entries']['map']+4,0xdeadc000)
    setup();ptr(u,0x100e000+0x88,0x12345678);run('construct',0x409cb4)
    if any(bytes(u.mem_read(report['entries']['map'],512))):raise ValueError('new constructor retained stale map')
    setup();f32(u,0x100e010,1);run('update',0x40a02c)
    for k in range(3):
        v=word(state+4+k*4)
        if v and get(u,v+0x10)!=0:raise ValueError('prepublication voice not muted')
    ptr(u,owner+0xc,0);ptr(u,owner+0x10,0);u.reg_write(CX,owner);u.reg_write(SP,0x100e000-12);u.emu_start(0x409e25,0x409e9a,count=50000)
    if word(manager+0x14)!=0:raise ValueError('race re-entry leaked native SFX registration')
    for name,(site,preimage) in SITES.items():
        altered=bytearray(exe);altered[layout.va_to_file_offset(site)]=0x90
        try:append_whine(exe,bytes(altered),prefix,baseva,[profile],65536)
        except ValueError:pass
        else:raise ValueError('changed '+name+' seam was accepted')
    for src,allocation in [(b'X'+exe[1:],65536),(exe,1)]:
        try:append_whine(src,exe,prefix,baseva,[profile],allocation)
        except ValueError:pass
        else:raise ValueError('wrong executable or undersized allocation accepted')
    return {'status':'PASS','exe_sha256':hashlib.sha256(exe).hexdigest(),'binding':report,'cases':rows,
        'native_spool_after_drive':pressure,'bov_events':events,'directsound_mock_calls':ds_calls,'native_gain_calibration':calibration,'gain_curve_check':curve_check,'volume_hundredth_db':volumes,'bounded_map_publications':73,'preimage_and_allocation_rejections':'PASS','memory_protection':'RX payload; dedicated map page RW/NX; page zero unmapped','old_rx_policy_negative_control':'UC_ERR_WRITE_PROT reproduced at publisher map write',
        'ownership':'Original 004F63D0/004F6750 construct/register, supplemental separate entity binding, generated destruction seam/004F64A0/004F67A0 unregister/free replayed twice; stale map invalidated; Windows FS:[0] SEH setup/restore excluded.',
        'boundary':'Generated helper/seams, original SFX ownership and original 005A8300 Play/SetVolume/SetFrequency/Stop instructions executed. Broker, interner, allocator, singleton, frees, clock and DirectSound COM device methods are typed stubs. No actual DS device, audible race mix, game or GT parity confirmation.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--gain-curve',action='store_true');p.add_argument('--fail-allocation',type=int,choices=(1,2,3));a=p.parse_args()
    report=replay(a.exe.read_bytes(),json.loads(a.profile.read_text()),gain_curve=a.gain_curve,fail_allocation=a.fail_allocation);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'cases':len(report.get('cases',[])),'output':str(a.output)},indent=2))
