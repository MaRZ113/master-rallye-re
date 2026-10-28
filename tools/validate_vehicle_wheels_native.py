"""Controlled exact-x86 wheel selection/registration replay; no game launch."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tools')]
from vehicle_wheels_native import append_wheels, _wrapper, REGISTER_WHEEL, MODEL_SETTER, RETAIL_SHA256
from vehicle_mechanics_native import append_mechanics
from validate_vehicle_physics_forces import machine, ptr

PROFILE = {'runtime_family': 'Evo2FourRunner',
           'resource_keys': ['Vehicles/Evo2FourRunner/wheel'+str(i) for i in range(4)]}


def synthetic_wrapper_replay():
    """No private fixture: emitted x86 ABI, family/index guards and routing."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_PROT_READ, UC_PROT_EXEC
    from unicorn.x86_const import UC_X86_REG_ESP as SP, UC_X86_REG_EIP as IP, UC_X86_REG_EAX as AX, UC_X86_REG_ECX as CX, UC_X86_REG_EDX as DX, UC_X86_REG_EBX as BX, UC_X86_REG_ESI as SI, UC_X86_REG_EDI as DI, UC_X86_REG_EBP as BP, UC_X86_REG_EFLAGS as FL
    u = Uc(UC_ARCH_X86, UC_MODE_32)
    for at, size in ((0x400000, 0x200000), (0x1000000, 0x20000), (0x2000000, 0x20000), (0x10000000, 65536)):
        u.mem_map(at, size)
    entry, stop, stack = 0x10000000, 0x1002000, 0x100f000
    wheel, state, string_base = 0x2000000, 0x2001000, 0x2002000
    code = _wrapper(entry, [PROFILE], REGISTER_WHEEL)
    u.mem_write(entry, code); u.mem_protect(entry, 65536, UC_PROT_READ|UC_PROT_EXEC)
    u.mem_write(REGISTER_WHEEL, b'\xc2\x0c\x00')
    keys, strings = {}, {}; next_string = string_base
    calls, selected = [], []
    def read32(at): return struct.unpack('<I', bytes(u.mem_read(at, 4)))[0]
    def string(at):
        out = bytearray()
        for i in range(256):
            b = bytes(u.mem_read(at+i, 1))
            if b == b'\0': return out.decode('ascii')
            out += b
        raise ValueError('synthetic string bound')
    def key(value):
        nonlocal next_string
        if value not in keys:
            keys[value] = len(keys)+1; strings[keys[value]] = next_string
            u.mem_write(next_string, value.encode()+b'\0'); next_string += len(value)+1
        return keys[value]
    def ret(value, pop=0):
        sp=u.reg_read(SP); u.reg_write(AX, value); u.reg_write(IP, read32(sp)); u.reg_write(SP, sp+4+pop)
    def hook(_u, at, size, data):
        sp=u.reg_read(SP)
        if at == 0x4d0570: ret(strings[read32(u.reg_read(CX))])
        elif at == 0x4d0580:
            ptr(u, u.reg_read(CX), key(string(read32(sp+4)))); ret(u.reg_read(CX), 4)
        elif at == MODEL_SETTER:
            value=read32(read32(sp+4)); ptr(u,u.reg_read(CX)+0xc,value)
            selected.append(value); ret(0,4)
        elif at == REGISTER_WHEEL:
            calls.append((u.reg_read(CX), [read32(sp+4+i*4) for i in range(3)], read32(state+0xc)))
            u.reg_write(AX,0x12345678);u.reg_write(CX,0x89abcdef);u.reg_write(DX,0x10203040);u.reg_write(FL,0x246)
    u.hook_add(UC_HOOK_CODE, hook)
    cases=[]
    inputs=[('Vehicles/Evo2FourRunner/wheel',i,True)for i in range(4)]
    inputs += [('VEHICLES\\evo2fourrunner\\WHEEL',0,True), ('vehicles/Evo2FourRunner/wheel',3,True)]
    inputs += [(value,0,False)for value in ('Vehicles/Terrano/wheel','Vehicles/Evo2FourRunnerExtra/wheel','Vehicles/Evo2FourRunner/wheel.dx','Vehicles/Evo2FourRunner/wheel/extra')]
    inputs += [('Vehicles/Evo2FourRunner/wheel',4,False),('Vehicles/Evo2FourRunner/wheel',0xffffffff,False)]
    for value,index,change in inputs:
        initial=key(value);ptr(u,wheel+0x50,state);ptr(u,state+0xc,initial)
        u.mem_write(stack,struct.pack('<4I',stop,0x2007000,index,wheel));u.reg_write(SP,stack);u.reg_write(CX,0x2008000)
        saved={BX:0x11223344,SI:0x55667788,DI:0x12344321,BP:0x76543210}
        for reg,v in saved.items():u.reg_write(reg,v)
        n=len(calls);nselected=len(selected);u.emu_start(entry,stop,count=20000)
        if u.reg_read(IP)!=stop or u.reg_read(SP)!=stack+16 or any(u.reg_read(reg)!=v for reg,v in saved.items()):
            raise ValueError('wheel selector callee-saved/stack ABI changed')
        if (u.reg_read(AX),u.reg_read(CX),u.reg_read(DX),u.reg_read(FL))!=(0x12345678,0x89abcdef,0x10203040,0x246):
            raise ValueError('original registration return registers/flags changed')
        expected=key(PROFILE['resource_keys'][index])if change else initial
        if len(calls)!=n+1 or calls[-1]!=(0x2008000,[0x2007000,index,wheel],expected):
            raise ValueError('wheel selector changed delegate arguments/routing/count')
        if len(selected)-nselected!=int(change):raise ValueError('wheel selector family/index isolation')
        cases.append({'model':value,'index':index,'selected':change})
    # Null wheel/state/key are guarded without invoking resource services.
    for wheel_arg,state_arg,key_arg in ((0,state,0),(wheel,0,0),(wheel,state,0)):
        ptr(u,wheel+0x50,state_arg);ptr(u,state+0xc,key_arg)
        u.mem_write(stack,struct.pack('<4I',stop,0x2007000,0,wheel_arg));u.reg_write(SP,stack);u.reg_write(CX,0x2008000)
        n=len(selected);u.emu_start(entry,stop,count=20000)
        if len(selected)!=n:raise ValueError('null wheel/state/key selected a model')
    return {'status':'PASS_SYNTHETIC_WHEEL_SELECTOR_X86','cases':cases,'null_guards':3,
            'callee_saved_stack_arguments_return_registers_and_flags':True,'delegate_calls_once':True}


def validate(exe):
    """Execute original model setter, key constructor and wheel registration.

    Typed services replace interning, allocator/free and unrelated scene-name
    resolution. Original registration/constructor/interpolator ownership code
    executes; no game process or model loader is invoked.
    """
    from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_EXEC
    from unicorn.x86_const import UC_X86_REG_ESP as SP, UC_X86_REG_EIP as IP, UC_X86_REG_EAX as AX, UC_X86_REG_ECX as CX
    if hashlib.sha256(exe).hexdigest()!=RETAIL_SHA256:raise ValueError('unqualified wheel replay target')
    rows=[]
    for chained in (False,True):
        blob=b'\x90'*32; image=exe; old=None
        if chained:
            mechanics={'runtime_family':'LancerEvo4','resource_keys':['Vehicles/LancerEvo4/mechanics'+str(i)for i in range(4)]}
            image,blob,old=append_mechanics(exe,image,blob,0x10000000,[mechanics],131072)
        image,blob,report=append_wheels(exe,image,blob,0x10000000,[PROFILE],131072,mechanics_report=old)
        u=machine(exe);u.mem_map(0,4096);u.mem_map(0x10000000,131072);u.mem_write(0x10000000,blob)
        u.mem_protect(0x10000000,131072,UC_PROT_READ|UC_PROT_EXEC)
        manager,vec,record,body,physics,wheel,state=0x2000000,0x2000100,0x2000200,0x2000300,0x2001000,0x2002000,0x2003000
        ptr(u,manager+0x18,vec);ptr(u,manager+0x1c,vec+4);ptr(u,vec,record);ptr(u,record+0x1c,body);ptr(u,record+0xc,physics)
        ptr(u,wheel+0x50,state)
        keys={};strings={};next_string=0x2004000;next_heap=0x2010000;live={};registrations=[];setter_calls=[];deletes=[];alloc_fail=False
        def read32(at):return struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
        def string(at):
            out=bytearray()
            for i in range(256):
                b=bytes(u.mem_read(at+i,1))
                if b==b'\0':return out.decode('ascii')
                out+=b
            raise ValueError('native replay string bound')
        def key(value):
            nonlocal next_string
            if value not in keys:
                keys[value]=len(keys)+1;strings[keys[value]]=next_string
                u.mem_write(next_string,value.encode()+b'\0');next_string+=len(value)+1
            return keys[value]
        def ret(value=0,pop=0):
            sp=u.reg_read(SP);u.reg_write(AX,value);u.reg_write(IP,read32(sp));u.reg_write(SP,sp+4+pop)
        def hook(_u,at,size,data):
            nonlocal next_heap
            sp=u.reg_read(SP)
            if at==0x4d0570:ret(strings[read32(u.reg_read(CX))])
            elif at==0x4d44f0:ret(read32(sp+4),4) # typed intern lookup token
            elif at==0x4d4460:ret(key(string(u.reg_read(CX))))
            elif at==MODEL_SETTER:setter_calls.append([u.reg_read(CX),read32(read32(sp+4))])
            elif at==REGISTER_WHEEL:registrations.append([u.reg_read(CX),*[read32(sp+4+i*4)for i in range(3)],read32(state+0xc)])
            elif at==0x5c1cb4:
                if alloc_fail:ret(0);return
                amount=read32(sp+4);address=next_heap;next_heap+=(amount+15)&~15
                if next_heap>0x2020000:raise ValueError('wheel replay heap bound')
                live[address]=amount;u.mem_write(address,b'\0'*amount);ret(address)
            elif at==0x5b4c00:
                address=read32(sp+4)
                if address not in live:raise ValueError('unknown/double wheel interpolator free')
                live.pop(address);ret()
            elif at==0x1003000:
                # A typed cached-model deleting destructor sentinel. The
                # original setter performs the actual virtual dispatch.
                if read32(sp+4)!=1:raise ValueError('cached model destructor ABI')
                deletes.append(u.reg_read(CX));ret(0,4)
        u.hook_add(UC_HOOK_CODE,hook)
        participant=key('Race/Car0');ptr(u,body+0x5c,participant);ptr(u,0x2005000,participant)
        cached=0x2006000;vtable=0x2006100;ptr(u,cached,vtable);ptr(u,vtable,0x1003000)
        stop,stack=0x1002000,0x100f000
        for cycle in range(2):
            for index in range(4):
                ptr(u,state+0xc,key('Vehicles/Evo2FourRunner/wheel'));ptr(u,state+0x74,cached)
                wheelname=key(f'Race/Car0/Wheel{index}');ptr(u,wheel+0x5c,wheelname)
                u.mem_write(stack,struct.pack('<4I',stop,0x2005000,index,wheel));u.reg_write(SP,stack);u.reg_write(CX,manager)
                n=len(registrations);u.emu_start(report['entry_va'],stop,count=100000)
                if u.reg_read(IP)!=stop or u.reg_read(SP)!=stack+16 or len(registrations)!=n+1:
                    raise ValueError('native original registration stack/count')
                if read32(state+0xc)!=key(PROFILE['resource_keys'][index]) or read32(state+0x74)!=0:
                    raise ValueError('native original model setter/cache invalidation')
                if read32(physics+index*0x188+0x180)!=wheelname:raise ValueError('native wheel-name publication')
                interp=read32(state+4)
                if read32(interp)!=0x690170 or read32(interp+4)!=physics+index*0x188:
                    raise ValueError('original wheel spin interpolator/binding replaced')
                rows.append({'mechanics_chain':chained,'cycle':cycle,'index':index,'resource_key':PROFILE['resource_keys'][index],
                             'original_spin_vtable':hex(read32(interp)),'original_registration_calls':1})
        # Allocation failure is original-native behavior; the selector does
        # not add allocations or new lifecycle ownership to it.
        alloc_fail=True;ptr(u,state+0xc,key('Vehicles/Evo2FourRunner/wheel'));ptr(u,state+0x74,0)
        u.mem_write(stack,struct.pack('<4I',stop,0x2005000,0,wheel));u.reg_write(SP,stack);u.reg_write(CX,manager)
        u.emu_start(report['entry_va'],stop,count=100000)
        if read32(state+4)!=0:raise ValueError('original allocation failure setter did not clear old interpolator')
        if live:raise ValueError('old native wheel interpolator leaked during replacement/failure')
        if len(deletes)!=8:raise ValueError('cached original models not disposed exactly once per change')
    # Reuse the existing accepted mechanics ownership replay with this selector
    # outside it. Its own four Lancer resources, duplicate guards, two scene
    # clears and four allocation-failure paths must remain unchanged.
    import validate_vehicle_mechanics_native as mechanics_validation
    from unittest.mock import patch
    def composed(source,image,blob,payload_va,profiles,allocation_size):
        image,blob,old=append_mechanics(source,image,blob,payload_va,profiles,allocation_size)
        return append_wheels(source,image,blob,payload_va,[PROFILE],allocation_size,mechanics_report=old)
    with patch.object(mechanics_validation,'append_mechanics',composed):
        mechanics_passthrough=mechanics_validation.validate(exe)
    return {'status':'PASS_CONTROLLED_NATIVE_WHEEL_RESOURCE_SELECTION','rows':rows,
            'native_executed':['4D0580 key constructor','4F5B70 model setter/cache invalidation',
                               '43ED00 original wheel registration','448570 spin interpolator constructor',
                               '4F5CE0 interpolator ownership setter','4485C0 deleting interpolator destructor'],
            'service_stubs':['name intern/lookup','allocator/free ledger','cached-model destructor sentinel'],
            'same_wheel_entity_and_original_spin_controller':True,'no_auxiliary_entities':True,
            'mechanics_delegate_rebuilt_and_executed':True,'original_interpolator_allocation_failure_replayed':True,
            'accepted_mechanics_passthrough':mechanics_passthrough,
            'runtime_qualified':False,'boundary':'controlled original x86 and generated wrapper, no real model load/D3D8 render/gameplay'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=validate(a.exe.read_bytes());result['synthetic']=synthetic_wrapper_replay()
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
