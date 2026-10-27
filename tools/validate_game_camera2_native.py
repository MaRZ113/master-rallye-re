"""Original x86 five-mode selection, projection and isolated parameter-copy replay.

No game/device lifecycle claim: entity/name/Broker services are typed seams.
"""
import argparse,json,struct,sys,math,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from validate_vehicle_physics_forces import machine,ptr,f32,get
from vehicle_camera_native import make_parameter_wrapper,NAME,BROKER,CAR_ID,NATIVE
from master_rallye.game_camera import vertical_fov


def validate(exe,binding,*,delivered=None):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EDI as DI,UC_X86_REG_ESI as SI,UC_X86_REG_EBP as BP,UC_X86_REG_EBX as BX,UC_X86_REG_FPSW as FP
    rows=[];stack,stop=0x100f000,0x1002000
    def ret(u,value=None,pop=0):
        s=u.reg_read(SP);dest=struct.unpack('<I',u.mem_read(s,4))[0]
        if value is not None:u.reg_write(AX,value)
        u.reg_write(SP,s+4+pop);u.reg_write(IP,dest)
    # All five player choices, repeated wrap; original dispatcher, not a model.
    u=machine(exe);manager,params=0x2000000,0x2001000;ptr(u,params+12,3);ptr(u,params+16,2)
    u.hook_add(UC_HOOK_CODE,lambda uc,a,s,d:ret(uc,params)if a==0x4b7fb0 else None)
    seen=[]
    for n in range(10):
        seen.append(list(struct.unpack('<2I',bytes(u.mem_read(manager+0x1dc,8))))[::-1])
        ptr(u,stack,stop);u.reg_write(SP,stack);u.reg_write(CX,manager);u.emu_start(0x4b8170,stop,count=2000)
    assert seen==[[0,0],[0,1],[0,2],[1,0],[1,1]]*2,seen
    # Native FOV getter executes exact source arithmetic including portrait path.
    projections=[]
    for width,height in [(640,480),(1920,1080),(480,640),(960,270)]:
        u=machine(exe);cam=0x2000000;f32(u,cam,83.);ptr(u,cam+0x80,width);ptr(u,cam+0x84,height)
        u.mem_write(stop,bytes.fromhex('d91d00010002'));ptr(u,stack,stop);u.reg_write(SP,stack);u.reg_write(CX,cam)
        u.emu_start(0x4f2350,stop+6,count=100)
        assert abs(get(u,0x2000100)-vertical_fov(83.,width,height))<1e-5
        radians=vertical_fov(83.,width,height)*.01745329252;aspect=width/height;near,far=.1,100.
        matrix=0x2000200;u.mem_write(stack,struct.pack('<II4f',stop+16,matrix,radians,aspect,near,far));u.reg_write(SP,stack)
        u.emu_start(0x5d681f,stop+16,count=2000);m=list(struct.unpack('<16f',u.mem_read(matrix,64)));scale=1/math.tan(radians/2)
        error=max(abs(m[0]-scale/aspect),abs(m[5]-scale));assert error<2e-6 and m[11]==1. and abs(m[10]-far/(far-near))<2e-6
        projections.append({'viewport':[width,height],'vertical_fov':get(u,0x2000100),'xy_scale_error':error,'native_lh_projection':m})
    # Real native copy followed by delivered generated owner gate / overrides.
    for kind,count,original in [('follow',3,0x4b98e0),('fixed',2,0x4b99c0)]:
        base_va=0x10000000;entry=base_va;allocation=262144
        if delivered is None:
            other=copy.deepcopy(binding);other.update(car_id=1 if binding['car_id']!=1 else 2,model_resource=binding['model_resource']+'_other')
            code=make_parameter_wrapper(base_va,[binding,other],kind)
        else:
            import patch_vehicle_registry_id26 as reg
            image,code,base_va=delivered;entry=base_va;site=0x4b83a0 if kind=='follow'else 0x4b83f3
            offset=reg.va_to_file_offset(reg.parse_pe(exe),site,5)
            if image[offset]!=0xe8:raise ValueError('Delivered camera copy hook missing')
            entry=site+5+struct.unpack_from('<i',image,offset+1)[0]
            if not base_va<=entry<base_va+len(code):raise ValueError('Delivered camera hook outside private payload')
        for mode in range(count):
            for case in ('selected','other_id','foreign','leading_zero','slot63','slot64','no_broker','model_mismatch','cross_model','bounds_mismatch','null_entity','null_node','null_bounds','broker_null','alternate_cycle','special_cycle'):
                u=machine(exe);u.mem_map(base_va,allocation);u.mem_write(base_va,code)
                cam,entity,node,bounds,names,params,records,out= [0x2000000+i*0x1000 for i in range(8)]
                ptr(u,entity+0x50,0 if case=='null_node'else node);raw=bytes.fromhex(binding['native_bounds_values_hex']);u.mem_write(bounds,raw)
                if case=='bounds_mismatch':f32(u,bounds+0x14,99.)
                u.mem_write(names,({'foreign':'Replay0','leading_zero':'Car00','slot63':'Car63','slot64':'Car64'}.get(case,'Car0')).encode()+b'\0')
                u.mem_write(names+128,(binding['model_resource']+('x'if case=='model_mismatch'else'_other'if case=='cross_model'else'')).encode()+b'\0')
                ptr(u,0x6f6594,0 if case=='no_broker'else out+128)
                stride=44 if kind=='follow'else 24;off=0x2c if kind=='follow'else 0x3c
                ptr(u,params+off,records);ptr(u,params+off+4,records+stride*count)
                for n in range(count):
                    for k in range(stride//4):f32(u,records+n*stride+k*4,float(k+1))
                    f32(u,records+n*stride+(36 if kind=='follow'else 20),90.)
                record_before=bytes(u.mem_read(records,stride*count));arg=[cam,mode,out]+([out+4]if kind=='follow'else[])
                u.mem_write(stack,struct.pack('<'+'I'*(len(arg)+1),stop,*arg))
                def hook(uc,a,s,d):
                    if a==NAME:ret(uc,names if uc.reg_read(CX)==entity+0x5c else names+128)
                    elif a==NATIVE:ret(uc,0 if case=='null_bounds'else bounds)
                    elif a==BROKER:ret(uc,0 if case=='broker_null'else out+128)
                    elif a==CAR_ID:ret(uc,binding['car_id']if case!='other_id'else 1,4)
                manager=out+512
                if case=='alternate_cycle':u.mem_write(manager+0x1e6,b'\1')
                if case=='special_cycle':u.mem_write(manager+0x1e7,b'\1')
                u.hook_add(UC_HOOK_CODE,hook);u.reg_write(CX,params);u.reg_write(DI,0 if case=='null_entity'else entity);u.reg_write(SI,manager);u.reg_write(BP,0x23456789);u.reg_write(BX,0x34567890);u.reg_write(SP,stack)
                fp=u.reg_read(FP)&0x3800;u.emu_start(entry,stop,count=50000)
                selected=case in ('selected','slot63');fields=binding['profile']['mode_overrides'].get(kind+str(mode),{})if selected else{}
                assert abs(get(u,out)-fields.get('FOV',90.))<1e-5,(kind,mode,case,get(u,out),fields)
                if kind=='follow':
                    for name,offset,base in [('Dist Front',0x48,1.),('Dist Back',0x4c,2.),('Dist Up',0x50,3.)]:assert abs(get(u,cam+offset)-fields.get(name,base))<1e-5,(name,case)
                assert bytes(u.mem_read(records,stride*count))==record_before
                assert u.reg_read(SP)==stack+4+4*len(arg)and u.reg_read(BP)==0x23456789 and u.reg_read(SI)==manager and u.reg_read(BX)==0x34567890 and (u.reg_read(FP)&0x3800)==fp
                rows.append({'kind':kind,'preset':mode,'case':case,'fov':get(u,out)})
    return {'status':'PASS_ORIGINAL_X86_CAMERA2','five_mode_cycle':seen,'projection_cases':projections,'parameter_cases':rows,'boundary':'Original dispatcher/FOV/LH projection/copy and emitted guard execute; Broker/name/bounds are seams. Preview RH basis convention is separate; D3D8/live lifetime pending owner.'}


def validate_fixed(exe,minimum,maximum):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP as SP,UC_X86_REG_ECX as CX,UC_X86_REG_EAX as AX,UC_X86_REG_EIP as IP
    from master_rallye.game_camera import fixed_pose
    rows=[]
    for kind in (0,1):
     for yaw in (0,90,-35):
      u=machine(exe);cam,ent,frame,bounds,bank,out,vt= [0x2000000+i*0x1000 for i in range(7)];sp=0x100f000;stop=0x1002000
      a=math.radians(yaw);P=(3.,2.,-4.);forward=(math.sin(a),0,math.cos(a));up=(0,1,0);right=(math.cos(a),0,-math.sin(a))
      for off,vals in [(0x1c,right),(0x2c,up),(0x3c,forward),(0x4c,P)]:u.mem_write(frame+off,struct.pack('<3f',*vals))
      lo,hi=minimum,maximum;u.mem_write(bounds+0x14,struct.pack('<6f',*lo,*hi));ptr(u,ent+0x50,frame);ptr(u,bank,out);ptr(u,cam,vt);ptr(u,vt+0x10,stop+16);u.mem_write(stop+16,bytes.fromhex('c20400'));ptr(u,cam+0xc,kind);observed=[]
      def word(at):return struct.unpack('<I',u.mem_read(at,4))[0]
      def ret(value,pop=0):
       s=u.reg_read(SP);u.reg_write(AX,value);u.reg_write(SP,s+4+pop);u.reg_write(IP,word(s))
      def hook(uc,at,size,data):
       if at==0x4f5bc0:ret(bounds)
       elif at==0x4d8ec0:ret(cam+0x24,4)
       elif at==0x4d6760:ret(0)
       elif at==0x4e3dd0:ret(bank)
       elif at==0x4895f0:
        s=u.reg_read(SP);observed.append([list(struct.unpack('<3f',u.mem_read(word(s+i),12)))for i in (4,8,12)])
      u.hook_add(UC_HOOK_CODE,hook)
      for address in (0x52bec0,0x52c090):
       ptr(u,sp,stop);ptr(u,sp+4,ent);u.reg_write(SP,sp);u.reg_write(CX,cam);u.emu_start(address,stop,count=50000);assert u.reg_read(SP)==sp+8
      want=fixed_pose({'minimum':lo,'maximum':hi},{'Type':kind,'FOV':90},P,yaw)
      assert len(observed)==1
      for got,key in zip(observed[0],('eye','target','up')):
       assert max(abs(x-y)for x,y in zip(got,want[key]))<1e-5,(kind,yaw,key,got,want)
      rows.append({'kind':kind,'yaw':yaw,'observed':observed[0]})
    return {"status":"PASS_ORIGINAL_FIXED_INIT_UPDATE","cases":rows}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--binding',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    value=validate(a.exe.read_bytes(),json.loads(a.binding.read_text()));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(value,indent=2)+'\n');print(value['status'],len(value['parameter_cases']))
