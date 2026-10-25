"""Original cached texture reader versus batched adapter, isolated CPU replay."""
import argparse,functools,hashlib,json,struct
from pathlib import Path
from vehicle_dxt_bulk_native import compile_helper,ORIGINAL,RETAIL_SHA256
from native_audio_coff import link_object
from validate_vehicle_physics_forces import machine,ptr
from master_rallye.vehicle_physics_binding import parse_pe32_layout


@functools.lru_cache(maxsize=1)
def helper():return compile_helper()[0]


def imports(exe):
    layout=parse_pe32_layout(exe);pe=struct.unpack_from('<I',exe,0x3c)[0];rva=struct.unpack_from('<I',exe,pe+24+104)[0];at=layout.va_to_file_offset(0x400000+rva);result={}
    while any(struct.unpack_from('<5I',exe,at)):
        original,_,_,_,iat=struct.unpack_from('<5I',exe,at);source=layout.va_to_file_offset(0x400000+original);index=0
        while (value:=struct.unpack_from('<I',exe,source+index*4)[0]):
            if value<0x80000000:
                name=layout.va_to_file_offset(0x400000+value)+2;result[exe[name:exe.index(0,name)].decode()]=0x400000+iat+index*4
            index+=1
        at+=20
    return result


def replay(exe,width,height,pixels,*,fast,variant=None):
    from unicorn import UC_HOOK_CODE,UC_PROT_READ,UC_PROT_EXEC
    from unicorn.x86_const import UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_EBX as BX,UC_X86_REG_ESI as SI,UC_X86_REG_EDI as DI,UC_X86_REG_EBP as BP
    if hashlib.sha256(exe).hexdigest()!=RETAIL_SHA256:raise ValueError('unqualified DXT reader source')
    if len(pixels)!=width*height*4:raise ValueError('invalid synthetic pixel fixture')
    prefix=b'\0'*(13 if variant=='position' else 12);file_bytes=prefix+struct.pack('<II',width,height)+pixels+(b'TAIL' if variant=='trailing' else b'')
    u=machine(exe);u.mem_map(0x2100000,0x1000000);u.mem_map(0x4000000,4096);u.mem_map(0x10000000,65536)
    blob,entries=link_object(helper(),0x10000000);u.mem_write(0x10000000,blob);u.mem_protect(0x10000000,65536,UC_PROT_READ|UC_PROT_EXEC)
    stream=0x2000000;position=[len(prefix)];heap=[0x2100000];allocated=[];freed=[];reads=[];original_calls=[];allocation_attempts=[0]
    ptr(u,stream,0x69ce44);ptr(u,stream+0xc,42);u.mem_write(stream+0x10,bytes([variant=='archive']))
    if variant=='unknown_vtable':u.mem_write(stream+0x100,bytes(u.mem_read(0x69ce44,80)));ptr(u,stream,stream+0x100)
    api=imports(exe)
    for i,name in enumerate(('ReadFile','SetFilePointer','GetFileSize')):ptr(u,api[name],0x4000000+i*0x10)
    def word(at):return struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
    def ret(pop):sp=u.reg_read(SP);u.reg_write(IP,word(sp));u.reg_write(SP,sp+4+pop)
    def read_to(dest,size):
        available=max(0,len(file_bytes)-position[0]);count=min(size,available)
        if variant in ('short_read','short_read_true') and size>8:count=min(3,count)
        if count:u.mem_write(dest,file_bytes[position[0]:position[0]+count])
        position[0]+=count;reads.append(size);return count
    def hook(uc,address,size,data):
        sp=uc.reg_read(SP)
        if address==ORIGINAL:original_calls.append(address)
        elif address==0x5c1cb4:
            size=word(sp+4);allocation_attempts[0]+=1;failure={'first_allocation_fail':1,'allocation_fail':2,'wrapper_allocation_fail':3}.get(variant)
            value=0 if allocation_attempts[0]==failure else heap[0]
            if value:heap[0]+=(size+15)//16*16 or 16;allocated.append(value)
            uc.reg_write(AX,value);uc.reg_write(CX,0xdead);uc.reg_write(DX,0xbeef);ret(0)
        elif address==0x5b4c00:
            value=word(sp+4)
            if value:freed.append(value)
            ret(0)
        elif address==0x4000000:
            if word(sp+4)!=42:raise ValueError('wrong native file handle')
            count=read_to(word(sp+8),word(sp+12));ptr(uc,word(sp+16),count);uc.reg_write(AX,int(variant=='short_read_true' or count==word(sp+12)));ret(20)
        elif address==0x652990:
            count=read_to(word(sp+8),word(sp+12));uc.reg_write(AX,count);ret(0)
        elif address==0x4000010:
            distance=word(sp+8);mode=word(sp+16)
            if mode==0:position[0]=distance
            elif mode!=1:raise ValueError('unexpected native file seek')
            if word(sp+12):ptr(uc,word(sp+12),0)
            uc.reg_write(AX,position[0]);ret(16)
        elif address==0x4000020:
            if word(sp+8):ptr(uc,word(sp+8),0)
            uc.reg_write(AX,len(file_bytes));ret(8)
    u.hook_add(UC_HOOK_CODE,hook);stack=0x100f000;stop=0x1002000;u.mem_write(stack,struct.pack('<II',stop,stream));u.reg_write(SP,stack);u.reg_write(CX,0x2000300)
    saved={BX:0x12345678,SI:0x23456789,DI:0x3456789a,BP:0x456789ab}
    for r,v in saved.items():u.reg_write(r,v)
    u.emu_start(entries['_dxt_bulk@4'] if fast else ORIGINAL,stop,count=10000000)
    if u.reg_read(SP)!=stack+8 or u.reg_read(IP)!=stop or any(u.reg_read(r)!=v for r,v in saved.items()):raise ValueError('DXT decoder ABI changed')
    result=u.reg_read(AX);decoded=None
    if result:
        image=word(result);w,h=word(image+12),word(image+16);decoded=bytes(u.mem_read(word(image+8),w*h*4))
        if (w,h)!=(width,height) or decoded!=pixels:raise ValueError('DXT pixels/dimensions changed')
    return {'decoded_sha256':hashlib.sha256(decoded).hexdigest() if decoded is not None else None,'read_calls':len(reads),'read_sizes':reads if len(reads)<20 else [reads[0],reads[-1]],'position':position[0],'original_calls':len(original_calls),'allocated':len(allocated),'freed':len(freed),'success':bool(result),'abi':'PASS'}


def validate(exe):
    rows=[]
    for w,h in ((1,1),(8,4),(32,16)):
        pixels=bytes((i*17+31)%256 for i in range(w*h*4));old=replay(exe,w,h,pixels,fast=False);new=replay(exe,w,h,pixels,fast=True)
        if old['decoded_sha256']!=new['decoded_sha256'] or old['position']!=new['position'] or new['read_calls']!=2 or old['read_calls']!=w*h+2:raise ValueError('batch read equivalence failed')
        rows.append({'width':w,'height':h,'original':old,'batched':new})
    pixels=bytes(range(128))
    for variant in ('archive','unknown_vtable','position','trailing'):
        old=replay(exe,8,4,pixels,fast=False,variant=variant);new=replay(exe,8,4,pixels,fast=True,variant=variant)
        if old['decoded_sha256']!=new['decoded_sha256'] or old['position']!=new['position'] or new['original_calls']!=1:raise ValueError('fallback changed source behavior')
        rows.append({'variant':variant,'original':old,'batched':new})
    for variant in ('short_read','short_read_true','first_allocation_fail','allocation_fail','wrapper_allocation_fail'):
        new=replay(exe,8,4,pixels,fast=True,variant=variant)
        if new['success'] or new['allocated']!=new['freed']:raise ValueError('failed batch read leaked native image')
        rows.append({'variant':variant,'batched':new})
    return {'status':'PASS_ORIGINAL_DXT_PIXEL_READ_AND_BATCH_CPU_REPLAY','exe_sha256':hashlib.sha256(exe).hexdigest(),'cases':rows,
        'boundary':'original stream, scalar reader, image allocation/constructor/deleting destructor instructions; ReadFile/GetFileSize/SetFilePointer and allocation/free are typed mocks. Byte equality and native read counts, not measured gameplay speedup.','runtime_qualified':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate(a.exe.read_bytes());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])

