"""Controlled native allocation/registration/destruction replay for mechanics.

Original entity/state/controller/interpolator constructors, setters, destructors
and scene clear execute as x86. Heap and name/Broker services are ABI stubs.
This cannot certify a live model load, allocator or repeated gameplay races.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tools')]
from vehicle_mechanics_native import append_mechanics
from validate_vehicle_physics_forces import machine, ptr, f32


def validate(exe):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_ECX as ECX, UC_X86_REG_ESP as ESP, UC_X86_REG_EIP as EIP
    profile = {'runtime_family': 'LancerEvo4', 'resource_keys': ['Vehicles/LancerEvo4/mechanics'+str(i) for i in range(4)]}
    _, blob, report = append_mechanics(exe, exe, b'\x90'*16, 0x10000000, [profile], 131072)
    u = machine(exe)
    u.mem_map(0, 4096)
    u.mem_map(0x10000000, 131072)
    u.mem_write(0x10000000, blob)
    manager, wheel, wheel_state = 0x2000000, 0x2002000, 0x2003000
    keys = {}; strings = {}; entities = {}; live = {}; next_heap = 0x2010000
    next_string = 0x2004000
    native_calls = []
    allocation_attempts = 0
    fail_at = None
    def read32(at): return struct.unpack('<I', u.mem_read(at,4))[0]
    def string(at):
        result = bytearray()
        while len(result) < 256:
            b = bytes(u.mem_read(at+len(result),1))
            if b == b'\0': return result.decode('ascii')
            result += b
        raise ValueError('unbounded native replay string')
    def key(name):
        nonlocal next_string
        if name not in keys:
            keys[name] = len(keys)+1
            strings[keys[name]] = next_string
            u.mem_write(next_string, name.encode()+b'\0')
            next_string += len(name)+1
        return keys[name]
    def ret(value=0, pop=0):
        sp = u.reg_read(ESP); address = read32(sp)
        u.reg_write(EAX,value); u.reg_write(ESP,sp+4+pop); u.reg_write(EIP,address)
    def hook(uc, at, size, data):
        nonlocal next_heap, allocation_attempts
        sp = uc.reg_read(ESP); this = uc.reg_read(ECX)
        if at == 0x43ed00:
            native_calls.append([read32(sp+4),read32(sp+8),read32(sp+12)])
            ret(0x12345678,12)
        elif at == 0x5c1cb4:
            amount = read32(sp+4); allocation_attempts += 1
            if allocation_attempts == fail_at: ret(0); return
            address = next_heap; next_heap += (amount+15)&~15
            if next_heap > 0x2020000: raise ValueError('native replay arena exceeded')
            live[address] = amount; u.mem_write(address,b'\0'*amount); ret(address)
        elif at == 0x5b4c00:
            address = read32(sp+4)
            if address and address not in live: raise ValueError(f'unknown/double native free {address:x}')
            live.pop(address,None); ret()
        elif at == 0x4d0580:
            ptr(u,this,key(string(read32(sp+4)))); ret(this,4)
        elif at == 0x4d0570: ret(strings[read32(this)])
        elif at == 0x4f6310: ret(manager)
        elif at == 0x4f5eb0: ret(entities.get(read32(read32(sp+4)),0),4)
        elif at == 0x50e450:
            entity = read32(sp+4); entities[read32(entity+0x5c)] = entity; ret(0,4)
        elif at == 0x50e650:
            entity = read32(sp+4); entities.pop(read32(entity+0x5c),None); ret(0,4)
        elif at == 0x50e6c0: entities.clear(); ret()
        elif at == 0x4f5350:
            # The name/Broker ABI is stubbed; native setter ownership executes.
            ptr(u,this+0xc,0); ret(0,4)
        elif at == 0x4f54c0:
            dest, entity = read32(sp+4), read32(sp+8)
            name = next(name for name, ident in keys.items() if ident == read32(entity+0x5c))
            ptr(u,dest,key('Physics/'+name+'/Transform')); ret(dest)
    u.hook_add(UC_HOOK_CODE,hook)
    def call(address,this,args=()):
        stack = 0x100f000
        u.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),0x1002000,*args))
        u.reg_write(ESP,stack); u.reg_write(ECX,this)
        u.emu_start(address,0x1002000,count=100000)
        if u.reg_read(EIP) != 0x1002000: raise ValueError('native replay did not return')
        return u.reg_read(ESP)-stack
    call(0x4f5d90,manager)
    baseline_live = dict(live)
    ptr(u,wheel+0x50,wheel_state)
    rows = []
    for cycle in range(2):
        for index in range(4):
            name = f'Car{cycle}/Wheel{index}'
            ptr(u,wheel+0x5c,key(name)); ptr(u,wheel_state+0xc,key('vehicles/LancerEvo4/wheel'))
            before = len(live)
            delta = call(report['entry_va'],0x2001000,(0x2001800,index,wheel))
            entity = entities[key(name+'/SDKMechanics')]
            state = read32(entity+0x50); controller = read32(entity+4); interp = read32(state+4)
            if delta != 16 or u.reg_read(EAX)!=0x12345678 or read32(controller+0xc) != key('Physics/'+name+'/Transform') or read32(interp) != 0x690178:
                raise ValueError('mechanical attachment native ABI/binding failed')
            if read32(state+0xc) != key(profile['resource_keys'][index]): raise ValueError('mechanical resource routing mismatch')
            after = len(live)
            call(report['entry_va'],0x2001000,(0x2001800,index,wheel))
            if len(live) != after: raise ValueError('duplicate wheel callback allocated a second instance')
            rows.append({'cycle':cycle,'wheel':index,'native_owned_allocations':after-before,'native_base_interpolator':hex(read32(interp))})
        call(0x4f60f0,manager)
        if live != baseline_live or entities: raise ValueError('native scene clear leaked a mechanical allocation/name')
    # Donor/foreign resource must call original registration once and pass through.
    ptr(u,wheel_state+0xc,key('Vehicles/Navara/wheel'))
    count = allocation_attempts
    call(report['entry_va'],0x2001000,(0x2001800,0,wheel))
    if count != allocation_attempts: raise ValueError('foreign wheel allocated mechanics')
    for model in ['VEHICLES\\lancerevo4\\WHEEL','vehicles/LancerEvo4/wheel']:
        ptr(u,wheel+0x5c,key('CaseGuard/Wheel0'));ptr(u,wheel_state+0xc,key(model))
        call(report['entry_va'],0x2001000,(0x2001800,0,wheel))
        if not entities:raise ValueError('case/slash model guard missed native family')
        call(0x4f60f0,manager)
    for model in ['vehicles/LancerEvo4Extra/wheel','vehicles/LancerEvo4/wheel.dx','vehicles/LancerEvo4/wheel/extra']:
        ptr(u,wheel_state+0xc,key(model));count=allocation_attempts
        call(report['entry_va'],0x2001000,(0x2001800,0,wheel))
        if count!=allocation_attempts:raise ValueError('near-match model escaped exact family guard')
    # Fail each explicit allocation after the native state constructor allocation.
    # Each failed construction must disappear through the actual native cleanup.
    failures=[]
    ptr(u,wheel_state+0xc,key('Vehicles/LancerEvo4/wheel'))
    for failure in (1,2,3,4):
        ptr(u,wheel+0x5c,key('Failure'+str(failure)+'/Wheel0'))
        fail_at = allocation_attempts+failure
        call(report['entry_va'],0x2001000,(0x2001800,0,wheel))
        fail_at = None
        call(0x4f60f0,manager)
        if live != baseline_live or entities: raise ValueError('native allocation failure leaked mechanics')
        failures.append(failure)
    return {'status':'PASS_CONTROLLED_NATIVE_MECHANICS_LIFECYCLE','cases':rows,
            'allocation_failure_points':failures,'native_registration_calls':len(native_calls),
            'foreign_resource_bypasses':True,'duplicates_bypass':True,'two_scene_clear_cycles':True,
            'native_lowercase_prefix_and_case_slash_variants_match':True,'model_prefix_and_extension_nearmisses_bypass':True,
            'native_executed':['4F5670 entity constructor','4F5A80 state constructor','4F59F0 name setter',
                               '4F5B70 model setter','4F5290 transform controller constructor',
                               '4F5950 controller ownership setter','448570 interpolator constructor',
                               '4F5CE0 interpolator ownership setter','4F60F0 scene clear',
                               '4F5780 entity destructor','4F5AF0 state destructor','native deleting component destructors'],
            'stubs':['allocator/free ledger','native registration boundary43ED00',
                     'name intern/string lookup','name index insert/remove/clear','Broker transform-key construction','transform-controller init Broker services'],
            'runtime_qualified':False,
            'boundary':'controlled x86 ownership and wrapper replay; no live resource load, native allocator, scene timing, rendering or gameplay'}


def pose_checks(exe):
    """Execute full original wheel-pose math, stopping before Broker services."""
    from unicorn.x86_const import UC_X86_REG_ECX as ECX, UC_X86_REG_ESP as ESP, UC_X86_REG_EBP as EBP, UC_X86_REG_EIP as EIP
    rows=[];interpolation_rows=[]
    for positive in (False,True):
        for jounce,steer,camber in [(0,0,0),(.08,.2,.1),(-.07,-.3,-.05)]:
            previous=None
            for spin,speed in [(0,0),(1.3,25),(-2,-15)]:
                u=machine(exe);u.mem_map(0,4096)
                wheel,link,actor,body=0x2000000,0x2001000,0x2002000,0x2003000
                ptr(u,wheel+0x18,link);ptr(u,link+8,actor);ptr(u,actor+4,body)
                u.mem_write(body+0xbc,struct.pack('<9f',1,0,0,0,1,0,0,0,1))
                for off,vec in [(0xe0,(0,1,0)),(0xec,(1,0,0)),(0xf8,(0,0,1))]:u.mem_write(body+off,struct.pack('<3f',*vec))
                hub=(.745 if positive else -.745,.15,1.3)
                u.mem_write(wheel+0x30,struct.pack('<3f',*hub));u.mem_write(wheel+0x40,struct.pack('<3f',0,1,0))
                for off,value in [(0x4c,.2),(0x50,.2),(0xe4,jounce),(0x140,steer),(0x150,camber),(0x128,spin),(0x120,speed)]:f32(u,wheel+off,value)
                u.mem_write(wheel+0x1d,bytes([int(positive)]));u.reg_write(ECX,wheel);u.reg_write(ESP,0x100f000)
                u.emu_start(0x441270,0x4418e9,count=10000)
                if u.reg_read(EIP)!=0x4418e9:raise ValueError('native pose did not reach publication boundary')
                matrix=bytes(u.mem_read(u.reg_read(EBP)-0x18c,64));values=struct.unpack('<16f',matrix)
                if previous is not None and previous!=matrix:raise ValueError('spin leaked into native wheel attachment pose')
                previous=matrix
                if max(abs(a-b) for a,b in zip(values[12:15],(hub[0],hub[1]+jounce,hub[2])))>1e-6:
                    raise ValueError('native hub/jounce translation differs')
                if jounce==steer==camber==0:
                    expected=(-1,1,-1) if positive else (1,1,1)
                    if max(abs(values[i*5]-expected[i]) for i in range(3))>4e-6:raise ValueError('native side rest basis differs')
            rows.append({'positive_side':positive,'jounce_m':jounce,'steer_input_rad':steer,'camber_rad':camber,
                         'matrix':list(values),'spin_variants_identical':True})
            # Execute original transform-controller copy and the exact native
            # generic interpolation evaluator selected by vtable00690178.
            from unicorn import UC_HOOK_CODE
            from unicorn.x86_const import UC_X86_REG_EAX as EAX
            entity,state,controller,current,old_matrix,out_matrix=0x2005000,0x2006000,0x2007000,0x2008000,0x2009000,0x200a000
            ptr(u,entity+0x50,state);ptr(u,controller+0xc,0xabc)
            u.mem_write(current,matrix)
            old_values=list(values);old_values[13]-=.04
            u.mem_write(old_matrix,struct.pack('<16f',*old_values))
            lookups=[]
            def getters(uc,at,size,data):
                if at not in (0x4d8ec0,0x4d6ad0):return
                sp=uc.reg_read(ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
                if at==0x4d8ec0:uc.reg_write(EAX,0x200b000);pop=0
                else:
                    key_ptr=struct.unpack('<I',uc.mem_read(sp+4,4))[0]
                    lookups.append(struct.unpack('<I',uc.mem_read(key_ptr,4))[0])
                    uc.reg_write(EAX,current);pop=4
                uc.reg_write(ESP,sp+4+pop);uc.reg_write(EIP,ret)
            handle=u.hook_add(UC_HOOK_CODE,getters)
            stack=0x100f000;u.mem_write(stack,struct.pack('<2I',0x1002000,entity));u.reg_write(ESP,stack);u.reg_write(ECX,controller)
            u.emu_start(0x4f5440,0x1002000,count=10000)
            u.hook_del(handle)
            if u.reg_read(EIP)!=0x1002000 or u.reg_read(ESP)!=stack+8 or lookups!=[0xabc] or bytes(u.mem_read(state+0x1c,64))!=matrix:raise ValueError('native transform controller copied wrong wheel Broker pose or ABI differs')
            for fraction in (0.,.5,1.):
                u.mem_write(stack,struct.pack('<IIfII',0x1002000,entity,fraction,old_matrix,out_matrix));u.reg_write(ESP,stack)
                u.emu_start(0x5090f0,0x1002000,count=10000)
                if u.reg_read(EIP)!=0x1002000 or u.reg_read(ESP)!=stack+20:raise ValueError('native generic interpolator ABI differs')
                output=struct.unpack('<16f',u.mem_read(out_matrix,64))
                expected_y=old_values[13]+fraction*(values[13]-old_values[13])
                if abs(output[13]-expected_y)>1e-6:raise ValueError('native no-spin generic interpolation translation differs')
                if max(abs(output[k]-values[k]) for k in range(12))>4e-6:raise ValueError('native generic interpolator added spin or changed fixed orientation')
                interpolation_rows.append({'positive_side':positive,'jounce_m':jounce,'fraction':fraction,'translation_m':list(output[12:15]),'broker_key_checked':True})
    return {'status':'PASS_ORIGINAL_NATIVE_UNSPRUNG_POSE','rows':rows,
            'native_controller_and_interpolation':interpolation_rows,
            'interval':['00441270','004418E9'],'runtime_qualified':False,
            'boundary':'original pose instruction replay, synthetic body/wheel fields from verified loads; stop before Broker publication; no runtime contacts/rendering'}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();exe=a.exe.read_bytes();r=validate(exe);r['pose']=pose_checks(exe);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
