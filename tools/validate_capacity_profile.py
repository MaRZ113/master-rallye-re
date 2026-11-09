"""Execute emitted capacity core on Unicorn, never a game or live process."""
import argparse
import json
from pathlib import Path
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import sdk_capacity_native as native
import j2_frontend_reentry as j2
from build_sdk_capacity_profile import load_parent


def validate(image,blob,report):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as EAX,UC_X86_REG_ECX as ECX,UC_X86_REG_EDX as EDX,UC_X86_REG_ESP as ESP,UC_X86_REG_ESI as ESI,UC_X86_REG_EBP as EBP,UC_X86_REG_EIP as EIP
    start=time.perf_counter();p=report['profile'];n=p['record_count'];_,sections=j2.addon_runtime._pe_sections(image)
    def machine():
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
        for s in sections:u.mem_write(0x400000+s['rva'],image[s['raw_offset']:s['raw_offset']+s['raw_size']])
        u.mem_map(0x10000000,report['private_allocation_size']);u.mem_write(0x10000000,blob)
        u.mem_map(0x1000000,0x20000)
        u.mem_map(0x2000000,((p['layout']['allocation_size']+0x4000+4095)//4096)*4096)
        u.reg_write(ESP,0x100fff0);u.mem_write(0x100fff0,struct.pack('<I',0x1001000));u.reg_write(ECX,0x2000000)
        return u
    def run(u,a,stop=0x1001000):
        u.emu_start(a,stop,count=10000000)
        if u.reg_read(EIP)!=stop:raise ValueError('Capacity helper did not reach expected continuation')
    def require(condition,reason):
        if not condition:raise ValueError(reason)
    queries=0;times=[]
    for c,ids in enumerate(p['classes'].values()):
        u=machine()
        for local,i in enumerate(ids):
            u.reg_write(ESP,0x100fff0);u.reg_write(ECX,0x2000000)
            u.mem_write(0x2000010,struct.pack('<I',c));u.mem_write(0x2000014+c*4,struct.pack('<I',local))
            before=time.perf_counter();run(u,0x481e20);times.append(time.perf_counter()-before)
            require(u.reg_read(EAX)==i and u.reg_read(ESP)==0x100fff4,'Forward map or stack mismatch')
            u.reg_write(ESP,0x100fff0);u.mem_write(0x100fff4,struct.pack('<I',i));run(u,0x481e50,0x481e89)
            require(struct.unpack('<I',u.mem_read(0x2000010,4))[0]==c,'Reverse class mismatch')
            require(struct.unpack('<I',u.mem_read(0x2000014+c*4,4))[0]==local,'Reverse local mismatch')
            require(u.reg_read(ESP)==0x100ffec,'Reverse continuation stack mismatch');queries+=2
    for c,local in ((3,0),(0,len(p['classes']['T1'])),(0,0xffffffff),(0xffffffff,0)):
        u=machine();u.mem_write(0x2000010,struct.pack('<I',c));u.mem_write(0x2000014,struct.pack('<I',local));run(u,0x481e20)
        require(u.reg_read(EAX)==0xffffffff,'Invalid forward index was not rejected')
    u=machine();u.mem_write(0x100fff4,struct.pack('<I',n));run(u,0x481e50)
    require(u.reg_read(ESP)==0x100fff8,'Invalid reverse index was not rejected')
    for a,stop,unwind in [(0x458cf3,0x458cf8,False),(0x458e45,0x458e4a,False),(0x686795,0x68679c,True)]:
        u=machine();u.reg_write(ESI,0x2000000);u.reg_write(EBP,0x2000100);run(u,a,stop)
        require(struct.unpack('<I',u.mem_read(u.reg_read(ESP)+(4 if unwind else 0),4))[0]==n,'Lifecycle count truncation')
    # Replay the publisher comparison itself around both sides of its bound.
    for i,expected in ((max(map(len,p['classes'].values()))-1,0x48195a),(max(map(len,p['classes'].values())),0x4819a9)):
        u=machine();u.reg_write(ESI,i);run(u,0x4819a4,expected)
    # Resolve the hook RVA through the actual parent PE sections.
    parent_at=next(s['raw_offset']+0x58d3f-s['rva'] for s in sections if s['rva']<=0x58d3f< s['rva']+s['raw_size'])
    core_init=0x458d44+struct.unpack_from('<i',image,parent_at+1)[0]
    # Core initializer starts PUSH ESI; MOV ESI,ECX; MOV ECX,ESI; CALL parent.
    init_offset=core_init-0x10000000
    parent_init=core_init+10+struct.unpack_from('<i',blob,init_offset+6)[0]
    u=machine();seen=[];parents=[]
    untouched=bytes([0xa5])*(4+33*52);u.mem_write(0x2000000,untouched)
    def callback(uc,at,size,user):
        if at not in (parent_init,native.registry.STRING_CONSTRUCTOR_VA,native.registry.VEHICLE_INITIALIZER_VA):return
        sp=uc.reg_read(ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
        cleanup=0 if at==parent_init else 4 if at==native.registry.STRING_CONSTRUCTOR_VA else 48
        if at==parent_init:parents.append(at)
        if at==native.registry.VEHICLE_INITIALIZER_VA:
            args=struct.unpack('<12I',uc.mem_read(sp+4,48));i=args[0];dest=uc.reg_read(ECX)
            require(dest==0x2000000+4+i*52,'Initializer destination mismatch')
            require(33<=i<n,'Initializer attempted to overwrite SDK33 record')
            seen.append(i);uc.mem_write(dest+4,struct.pack('<I',i))
        # Native thiscall callees are allowed to clobber volatile registers.
        uc.reg_write(EAX,0xdeadbeef);uc.reg_write(ECX,2);uc.reg_write(EDX,0xbad00001)
        uc.reg_write(ESP,sp+4+cleanup);uc.reg_write(EIP,ret)
    u.hook_add(UC_HOOK_CODE,callback);run(u,0x458d3f,0x458d44)
    require(seen==list(range(33,n)) and len(parents)==1,'Initializer missed/repeated records or parent')
    require(u.reg_read(ESP)==0x100fff0 and u.reg_read(EAX)==0x2000000,'Initializer stack/return ABI mismatch')
    require(bytes(u.mem_read(0x2000000,len(untouched)))==untouched,'Old record storage changed')
    for i in range(33,n):require(struct.unpack('<I',u.mem_read(0x2000000+8+i*52,4))[0]==i,'New record ID truncated')
    return {'status':'PASS_EMITTED_NATIVE_CORE','records':n,'bidirectional_queries':queries,
            'lifecycle_routes':3,'initializers':len(seen),'parent_initializer_calls':1,
            'invalid_indices_rejected':5,'publisher_boundary_checked':True,
            'lookup_emulation_us_median':sorted(times)[len(times)//2]*1e6,
            'seconds':time.perf_counter()-start,'runtime_qualified':False,
            'limitations':['CPU-only; no game, GPU, save or network execution',
                'Native allocator, strings, record initializer and accepted parent initialization are mocked',
                'All ID mappings, widened lifetime operands and original continuation addresses execute emitted x86']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--parent',type=Path,required=True);p.add_argument('--experiment',type=Path,required=True)
    a=p.parse_args();report=json.loads((a.experiment/'capacity-core.json').read_text());image,_,_=load_parent(a.source.read_bytes(),a.parent)
    for op in report['operations']:
        off=op['file_offset'];before=bytes.fromhex(op['original_bytes']);after=bytes.fromhex(op['replacement_bytes'])
        if image[off:off+len(before)]!=before:raise ValueError('Experiment preimage mismatch')
        image=image[:off]+after+image[off+len(after):]
    result=validate(image,(a.experiment/'capacity-extension.bin').read_bytes(),report)
    (a.experiment/'cpu-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
