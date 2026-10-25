"""Controlled original-x86 follow initializer with guarded SDK extent adapter."""
import json,struct
from pathlib import Path
from vehicle_camera_native import append_camera,NATIVE,NAME,BROKER,CAR_ID
from validate_vehicle_physics_forces import machine,ptr,get


def validate(exe, binding, *, delivered=None):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EDI as DI,UC_X86_REG_FPSW as FPSW
    image,blob,report=delivered if delivered is not None else append_camera(exe,exe,b'',0x10000000,[binding],262144)
    # Each case executes the original arithmetic/calls and native generated x86.
    # Name lookup, registry broker and bounds services are typed stubs only.
    rows=[]
    cases=[('selected',binding['car_id'],'Car0',True,True,True),('shared_model_other_id',27,'Car1',True,True,False),
           ('stock_id',1,'Car2',True,True,False),('last_slot',binding['car_id'],'Car63',True,True,True),
           ('unknown_slot',binding['car_id'],'Car64',True,True,False),('leading_zero',binding['car_id'],'Car00',True,True,False),
           ('foreign_target',binding['car_id'],'Replay0',True,True,False),('no_broker',binding['car_id'],'Car0',False,True,False),
           ('extents_disabled',binding['car_id'],'Car0',True,False,False)]
    for label,physical,name,broker,enabled,selected in cases:
        for mismatch in (False,True):
            u=machine(exe);u.mem_map(0x10000000,262144);u.mem_write(0x10000000,blob)
            import patch_vehicle_registry_id26 as reg
            pe=reg.parse_pe(exe)
            for op in report['operations']:
                # Exact virtual callsites were already independently qualified.
                va=next(c for c in (0x52c652,0x52c65e,0x52c677) if reg.va_to_file_offset(pe,c,5)==op['file_offset'])
                u.mem_write(va,bytes.fromhex(op['replacement_bytes']))
            camera,entity,node,bounds,names,stack,stop,vtable=0x2000000,0x2001000,0x2002000,0x2003000,0x2004000,0x100f000,0x1002000,0x2005000
            values=bytes.fromhex(binding['native_bounds_values_hex']);u.mem_write(bounds,values)
            modelname=binding['model_resource']+('x' if mismatch else '')
            u.mem_write(names,name.encode()+b'\0');u.mem_write(names+128,modelname.encode()+b'\0')
            ptr(u,entity+0x50,node);ptr(u,camera,vtable);ptr(u,vtable+0x10,stop+16);u.mem_write(stop+16,bytes.fromhex('c20400'))
            ptr(u,0x6f6594,0x2006000 if broker else 0);u.mem_write(camera+0x3c,bytes([enabled]));ptr(u,stack,stop);ptr(u,stack+4,entity)
            calls={'bounds':0,'broker':0,'id':0};slot=[]
            def hook(uc,address,size,data):
                if address not in (NATIVE,NAME,BROKER,CAR_ID):return
                sp=uc.reg_read(SP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0];pop=0
                if address==NATIVE:calls['bounds']+=1;result=bounds
                elif address==NAME:result=names if uc.reg_read(CX)==entity+0x5c else names+128
                elif address==BROKER:calls['broker']+=1;result=0x2006000
                else:
                    calls['id']+=1;slot.append(struct.unpack('<I',uc.mem_read(sp+4,4))[0]);result=physical;pop=4
                uc.reg_write(AX,result);uc.reg_write(CX,0xdeadbeef);uc.reg_write(DX,0xbaadf00d);uc.reg_write(SP,sp+4+pop);uc.reg_write(IP,ret)
            u.hook_add(UC_HOOK_CODE,hook);u.reg_write(SP,stack);u.reg_write(CX,camera);u.reg_write(DI,0x12345678)
            fp=u.reg_read(FPSW)&0x3800;u.emu_start(0x52c630,stop,count=20000)
            chosen=bytes.fromhex(binding['camera_bounds_hex']) if selected and not mismatch else values
            expected=[abs(struct.unpack_from('<f',chosen,0x28)[0]-struct.unpack_from('<f',chosen,0x1c)[0])*.5,abs(struct.unpack_from('<f',chosen,0x24)[0]-struct.unpack_from('<f',chosen,0x18)[0])] if enabled else [0,0]
            actual=[get(u,camera+0x40),get(u,camera+0x44)]
            if any(abs(a-b)>1e-5 for a,b in zip(actual,expected)) or bytes(u.mem_read(bounds,44))!=values or u.reg_read(DI)!=0x12345678 or u.reg_read(SP)!=stack+8 or (u.reg_read(FPSW)&0x3800)!=fp:raise ValueError('camera replay mismatch: '+label)
            if calls['bounds']!=(3 if enabled else 0):raise ValueError('native getter call count changed')
            rows.append({'case':label,'model_mismatch':mismatch,'physical_car_id':physical,'slot':slot,'terms':actual,'calls':calls})
    return {'status':'PASS_ORIGINAL_X86_CAMERA_ADAPTER','cases':rows,'runtime_qualified':False,'boundary':'Original initializer and generated adapter execute; scene/bounds/broker services stubbed. Not live follow update, split-screen/replay lifetime or gameplay confirmation.'}
