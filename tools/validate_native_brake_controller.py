"""Execute the original brake-state update and setter, with resource getters mocked.

No game is started. Native controller/threshold/branch/setter instructions are
real retail bytes; live named-switch registration remains a human runtime gate.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import j2_frontend_reentry as j2
from vehicle_damage_native import RETAIL_SHA256


def validate(exe):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as EAX,UC_X86_REG_ECX as ECX,UC_X86_REG_ESP as ESP,UC_X86_REG_EIP as EIP
    if hashlib.sha256(exe).hexdigest()!=RETAIL_SHA256:raise ValueError('unqualified executable')
    _,sections=j2.addon_runtime._pe_sections(exe);checks=[]
    for brake,want in [(0.,1),(.099,1),(.1,1),(.101,2),(1.,2)]:
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
        for s in sections:u.mem_write(0x400000+s['rva'],exe[s['raw_offset']:s['raw_offset']+s['raw_size']])
        u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x10000)
        controller=0x2000000;instance=0x2001000;selected=0x2002000;cases=0x2002100;vehicle=0x2003000;properties=0x2004000
        u.mem_write(controller+0x14,struct.pack('<II',0,instance))
        u.mem_write(instance+4,struct.pack('<I',selected));u.mem_write(instance+0x14,struct.pack('<I',cases));u.mem_write(instance+0x20,struct.pack('<I',1))
        u.mem_write(cases,struct.pack('<I',2));u.mem_write(selected,struct.pack('<I',0xdeadbeef))
        u.mem_write(vehicle+8,struct.pack('<I',properties));u.mem_write(properties+0x24,struct.pack('<f',brake))
        u.mem_write(0x100fff0,struct.pack('<II',0x1001000,0));u.reg_write(ESP,0x100fff0);u.reg_write(ECX,controller)
        calls=[]
        def hook(uc,at,size,user):
            if at not in (0x4d8ec0,0x4d6fb0):return
            calls.append(hex(at));stack=uc.reg_read(ESP);ret=struct.unpack('<I',uc.mem_read(stack,4))[0]
            uc.reg_write(EAX,vehicle);uc.reg_write(ESP,stack+4+(8 if at==0x4d8ec0 else 0));uc.reg_write(EIP,ret)
        u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x4ca1d0,0x1001000,count=10000)
        actual=struct.unpack('<I',u.mem_read(selected,4))[0]
        if actual!=want or u.reg_read(EIP)!=0x1001000 or u.reg_read(ESP)!=0x100fff8:raise ValueError(f'native brake state/ABI mismatch: {brake} -> {actual}, expected {want}')
        checks.append({'brake':brake,'native_case':actual,'getter_mocks':calls})
    return {'status':'PASS_ORIGINAL_NATIVE_BRAKE_UPDATE_AND_SETTER','checks':checks,'native_update_va':'004CA1D0','native_setter_va':'004D3C50',
            'exe_sha256':RETAIL_SHA256,'boundary':'Unicorn executes original threshold/update/setter; two resource getters mocked; no live registration or game launch','runtime_qualified':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=validate(a.exe.read_bytes());a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
