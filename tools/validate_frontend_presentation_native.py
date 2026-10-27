"""Replay original static-camera locals and emitted private-target wrapper.

Broker/name/bounds and matrix writer are typed seams; no D3D8 gameplay claim.
"""
import struct
from validate_vehicle_physics_forces import machine,ptr,f32
from vehicle_frontend_native import make_wrapper,NAME,BOUNDS,ORIGINAL,CALL
from master_rallye.frontend_presentation import EYE,TARGET

def validate(exe,binding,delivered=None):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EBX as BX,UC_X86_REG_EBP as BP,UC_X86_REG_ESI as SI,UC_X86_REG_EDI as DI,UC_X86_REG_FPSW as FP
    base=0x10000000;blob=make_wrapper(base,[binding]);entry=base
    if delivered:
        import patch_vehicle_registry_id26 as reg
        image,blob,base=delivered;off=reg.va_to_file_offset(reg.parse_pe(exe),CALL,5)
        assert image[off]==0xe8;entry=CALL+5+struct.unpack_from('<i',image,off+1)[0]
        assert base<=entry<base+len(blob)
    rows=[]
    for case in ('original','selected','other_name','other_model','bounds_changed','scene_changed','position_changed','target_changed','null_entity','null_node','null_bounds','null_name','uppercase_slashes'):
        u=machine(exe);u.mem_map(base,262144);u.mem_write(base,blob)
        ai,entity,node,bounds,names,camera,table=[0x2000000+i*0x1000 for i in range(7)]
        stack=0x100f000;stop=0x1002000;calls=[];u.mem_write(bounds,bytes.fromhex(binding['native_bounds_values_hex']))
        if case=='bounds_changed':f32(u,bounds+20,99.)
        ptr(u,entity+0x50,0 if case=='null_node'else node)
        for i,v in enumerate((8.,-2.,188. if case=='scene_changed'else 189.)):f32(u,node+0x4c+i*4,v)
        u.mem_write(names,(b'Other\0'if case=='other_name'else b'CarModel\0'))
        name=binding['model_resource']+('x'if case=='other_model'else'')
        if case=='uppercase_slashes':name=name.upper().replace('/','\\')
        u.mem_write(names+128,name.encode()+b'\0');ptr(u,table,camera);u.mem_write(ai+0x11,b'\1')
        for i,v in enumerate(EYE):f32(u,ai+0x14+i*4,v+(.1 if i==1 and case=='position_changed'else 0.))
        for i,v in enumerate((-1.22,2.18,0.)):f32(u,ai+0x2c+i*4,v+(.1 if i==1 and case=='target_changed'else 0.))
        def ret(value=None,pop=0):
            s=u.reg_read(SP);dest=struct.unpack('<I',u.mem_read(s,4))[0]
            if value is not None:u.reg_write(AX,value)
            u.reg_write(SP,s+4+pop);u.reg_write(IP,dest)
        def hook(uc,a,s,d):
            if a==0x4d8ec0:ret(0,4)
            elif a==0x4d6760:ret(0)
            elif a==0x4e3dd0:ret(table)
            elif a==NAME:ret(0 if case=='null_name'else names if uc.reg_read(CX)==entity+0x5c else names+128)
            elif a==BOUNDS:ret(0 if case=='null_bounds'else bounds)
            elif a==ORIGINAL:
                sp=u.reg_read(SP);args=struct.unpack('<4I',u.mem_read(sp+4,16));vectors=[list(struct.unpack('<3f',u.mem_read(p,12)))for p in args[:3]];calls.append(vectors);ret()
        u.hook_add(UC_HOOK_CODE,hook)
        # Full original updater proves local vectors and entity stack offset.
        # Null entity is tested directly; original updater itself dereferences it.
        if case in('null_entity','null_node'):
            points=[0x2008000+i*32 for i in range(4)]
            for p,vs in zip(points,[EYE,TARGET,(0.,1.,0.)]):u.mem_write(p,struct.pack('<3f',*vs))
            u.mem_write(stack,struct.pack('<5I',stop,*points));ptr(u,stack+0x44,0 if case=='null_entity'else entity);start=entry;expected_sp=stack+4
        else:
            if case!='original':u.mem_write(CALL,b'\xe8'+struct.pack('<i',entry-CALL-5))
            u.mem_write(stack,struct.pack('<2I',stop,entity));u.reg_write(CX,ai);start=0x52a6d0;expected_sp=stack+8
        u.reg_write(SP,stack);u.reg_write(BX,0x12345678);u.reg_write(BP,0x23456789);u.reg_write(SI,0x34567890);u.reg_write(DI,0x45678901);fp=u.reg_read(FP)&0x3800
        try:u.emu_start(start,stop,count=50000)
        except Exception as exc:raise AssertionError((case,hex(u.reg_read(IP)),hex(u.reg_read(SP))))from exc
        eye=list(EYE)
        if case=='position_changed':eye[1]=struct.unpack('<f',struct.pack('<f',EYE[1]+.1))[0]
        assert len(calls)==1 and calls[0][0]==eye,(case,calls)
        target=list(TARGET)
        selected=case in('selected','uppercase_slashes')
        if selected:target[1]=struct.unpack('<f',struct.pack('<f',TARGET[1]-binding['profile']['vertical_offset_m']))[0]
        if case=='scene_changed':target[2]=188.
        if case in('position_changed','target_changed'):
            assert not selected
        else:assert calls[0][1]==target,(case,calls[0][1],target)
        assert u.reg_read(SP)==expected_sp and u.reg_read(BX)==0x12345678 and u.reg_read(BP)==0x23456789 and u.reg_read(SI)==0x34567890 and u.reg_read(DI)==0x45678901 and (u.reg_read(FP)&0x3800)==fp
        rows.append({'case':case,'eye_target_up':calls[0],'status':'PASS'})
    return {'status':'PASS_ORIGINAL_AND_EMITTED_X86','cases':rows,'boundary':'Typed service seams; no live engine/device claim'}
