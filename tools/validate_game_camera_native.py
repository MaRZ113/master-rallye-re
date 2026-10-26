"""Controlled first-update native pose replay; not live D3D8 camera parity."""
import argparse,json,struct,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from validate_vehicle_physics_forces import machine,ptr,f32,get
from master_rallye.game_camera import static_pose


def replay(exe,extents,parameters,position=(0.,0.,0.),yaw_degrees=0.):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP as SP,UC_X86_REG_ECX as CX,UC_X86_REG_EAX as AX,UC_X86_REG_EIP as IP
    expected=static_pose(extents,parameters,position,yaw_degrees)
    u=machine(exe);cam,entity,frame,bank,output,stack,stop=0x2000000,0x2001000,0x2002000,0x2005000,0x2006000,0x100f000,0x1002000
    ptr(u,entity+0x50,frame);ptr(u,bank,output);u.mem_write(cam+0xc,b'\1')
    # Controlled upright target frame: native +2C up, +3C forward, +4C origin.
    a=math.radians(yaw_degrees)
    for at,vals in [(frame+0x2c,(0,1,0)),(frame+0x3c,(math.sin(a),0,math.cos(a))),(frame+0x4c,position)]:u.mem_write(at,struct.pack('<3f',*vals))
    for off,val in [(0x40,extents['half_length_m']),(0x44,extents['height_m']),(0x48,parameters['Dist Front']),(0x4c,parameters['Dist Back']),(0x50,parameters['Dist Up']),(0x64,parameters['Smooth Camera Multi']),(0x68,parameters['Body Dir Multi'])]:f32(u,cam+off,val)
    # Pitch disabled in this explicitly flat first-frame qualification.
    u.mem_write(cam+0x60,b'\0');observed=[];calls={};matrices=[];matrix_address=[]
    def word(at):return struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
    def ret(pop=0):s=u.reg_read(SP);target=word(s);u.reg_write(SP,s+4+pop);u.reg_write(IP,target)
    def hook(uc,at,size,data):
        if at==0x52cc6e:
            matrices.append(list(struct.unpack('<16f',bytes(uc.mem_read(matrix_address[0],64)))));return
        if at not in (0x4d8ec0,0x4d6760,0x4e3dd0,0x4895f0):return
        calls[hex(at)]=calls.get(hex(at),0)+1
        if at==0x4d8ec0:uc.reg_write(AX,cam+0x70);ret(4)
        elif at==0x4d6760:uc.reg_write(AX,0);ret()
        elif at==0x4e3dd0:uc.reg_write(AX,bank);ret()
        else:
            s=uc.reg_read(SP);observed.append([list(struct.unpack('<3f',bytes(uc.mem_read(word(s+i),12))))for i in (4,8,12)]);matrix_address.append(word(s+16))
            # Let the ORIGINAL basis/matrix writer and its vector helpers run.
    u.hook_add(UC_HOOK_CODE,hook);ptr(u,stack,stop);ptr(u,stack+4,entity);u.reg_write(SP,stack);u.reg_write(CX,cam);u.emu_start(0x52c6d0,stop,count=100000)
    if u.reg_read(IP)!=stop or u.reg_read(SP)!=stack+8 or len(observed)!=1:raise ValueError('Native follow return/pose ABI mismatch')
    for got,want in zip(observed[0],[expected['eye'],expected['target'],expected['up']]):
        if any(abs(a-b)>max(1e-5,abs(b)*2e-6)for a,b in zip(got,want)):raise ValueError('Native first-update pose differs from Core rule')
    def normalized(v):
        n=math.sqrt(sum(x*x for x in v));return [x/n for x in v]
    forward=normalized([b-a for a,b in zip(expected['eye'],expected['target'])]);right=normalized([forward[2],0,-forward[0]])
    up=[forward[1]*right[2]-forward[2]*right[1],forward[2]*right[0]-forward[0]*right[2],forward[0]*right[1]-forward[1]*right[0]]
    wanted=[*right,0.,*up,0.,*forward,0.,*expected['eye'],1.]
    if len(matrices)!=1 or any(abs(a-b)>max(1e-5,abs(b)*2e-6)for a,b in zip(matrices[0],wanted)):raise ValueError('Original camera basis/matrix mismatch')
    return {'status':'PASS_ORIGINAL_FIRST_UPDATE_POSE','eye_target_up':observed[0],'native_world_matrix_before_renderer_axis_flip':matrices[0],'service_stubs':{k:v for k,v in calls.items()if k!='0x4895f0'},'original_matrix_writer_calls':calls.get('0x4895f0',0),'scenario':expected['scenario'],'boundary':'Original follow updater, basis/matrix writer and vector helpers execute. Timer due check and renderer camera-array getter are typed mocks. Pitch disabled; no live target/acceleration/terrain/smoothing/FOV/device proof.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[]
    params={'Dist Front':14.,'Dist Back':3.5,'Dist Up':.65,'FOV':90.,'Smooth Camera Multi':.3,'Body Dir Multi':.3}
    for half,height in [(2.25,1.5),(2.61983,2.01947),(2.08582,1.48964),(2.18842,1.68474)]:
        for position,yaw in [((0,0,0),0),((3,2,-4),0),((0,0,0),90),((0,0,0),-35)]:rows.append(replay(a.exe.read_bytes(),dict(half_length_m=half,height_m=height),params,position,yaw))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'status':'PASS','cases':rows},indent=2)+'\n');print('PASS_NATIVE_STATIC_POSE',len(rows))
