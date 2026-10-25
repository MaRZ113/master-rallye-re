"""Controlled original x86 force/drivetrain replay, not a running race."""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.vehicle_physics_binding import parse_pe32_layout
from master_rallye.vehicle_config_analysis import parse_vehicle_config_bytes
from master_rallye.addon_sdk.physics_model import suspension_summary,effective_setup
from validate_vehicle_physics_native import replay
from vehicle_physics_native import append_reference,reference_match_name,RETAIL_SHA256,PUBLISH
import j2_frontend_reentry as j2

def machine(exe):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP
    if hashlib.sha256(exe).hexdigest()!=RETAIL_SHA256:raise ValueError('unqualified native force target')
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
    for s in j2.addon_runtime._pe_sections(exe)[1]:u.mem_write(0x400000+s['rva'],exe[s['raw_offset']:s['raw_offset']+s['raw_size']])
    u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x20000)
    u.mem_write(0x1001000,bytes.fromhex('dbe3'));u.emu_start(0x1001000,0x1001002,count=1)
    return u

def f32(u,at,value):u.mem_write(at,struct.pack('<f',value))
def ptr(u,at,value):u.mem_write(at,struct.pack('<I',value))
def get(u,at):return struct.unpack('<f',bytes(u.mem_read(at,4)))[0]

def spring_checks(exe,fields):
    from unicorn.x86_const import UC_X86_REG_ESP as ESP,UC_X86_REG_EIP as EIP
    rows=replay(exe,fields)['rows'];results=[]
    for row in rows[::2]:
        axle=row['axle'];n=lambda name:float(fields[f'Suspension/{axle}/{name}']['value'])
        for jounce,velocity in [(0,0),(.02,0),(0,.1),(-.05,0),(.1,.3),(-.2,0)]:
            u=machine(exe);wheel=0x2000000;other=0x2000200;vehicle=0x2000400;actor=0x2000500;body=0x2000600
            for w in [wheel,other]:
                ptr(u,w+0x18,vehicle);f32(u,w+0x20,row['sprung_corner_mass']);f32(u,w+0x24,n('UnsprungMass'))
                for off,key in [(0x50,'MaxDroop'),(0x60,'SpringRate'),(0x64,'SpringArmRatio'),(0x68,'DamperRate'),(0x6c,'DamperArmRatio'),(0x70,'AuxRollStiffness')]:f32(u,w+off,n(key))
                f32(u,w+0x74,n('AuxRollStiffness')*.1);f32(u,w+0xe4,jounce);f32(u,w+0xe8,velocity);f32(u,w+0xd4,1)
            ptr(u,vehicle+8,actor);ptr(u,actor+4,body);g=float(fields['Chassis/Gravity']['value']);f32(u,body+0x1c,g);f32(u,body+0xe4,1)
            sp=0x100f000;u.mem_write(sp,struct.pack('<5I',0x1002000,wheel,other,0,0));u.reg_write(ESP,sp)
            u.emu_start(0x446b10,0x1002000,count=10000)
            if u.reg_read(EIP)!=0x1002000:raise ValueError('force branch did not return')
            contact=get(u,wheel+0xf4)
            u.reg_write(ESP,sp);u.emu_start(0x446d20,0x1002000,count=10000);bodyforce=get(u,wheel+0x8c)
            active=jounce>=-n('MaxDroop');m=row['sprung_corner_mass'];r=n('SpringArmRatio');dr=n('DamperArmRatio')
            expected=(m*r+n('UnsprungMass'))*g+n('SpringRate')*r*r*jounce+n('DamperRate')*dr*dr*velocity if active else 0
            expected_body=m*g+n('SpringRate')*r*jounce+n('DamperRate')*dr*velocity if active else 0
            if abs(contact-max(0,expected))>max(.01,abs(expected)*1e-5) or abs(bodyforce-expected_body)>max(.01,abs(expected_body)*1e-5):raise ValueError('native preload/force relation mismatch')
            results.append({'axle':axle,'jounce_m':jounce,'velocity_m_s':velocity,'contact_N':contact,'body_N':bodyforce,'contact_active':active})
    return results

def reference_checks(exe,profile):
    from unicorn.x86_const import UC_X86_REG_ESP as ESP,UC_X86_REG_EIP as EIP,UC_X86_REG_EAX as EAX,UC_X86_REG_ECX as ECX,UC_X86_REG_EDX as EDX,UC_X86_REG_EBX as EBX,UC_X86_REG_EBP as EBP,UC_X86_REG_ESI as ESI,UC_X86_REG_EDI as EDI,UC_X86_REG_EFLAGS as FLAGS
    image,blob,report=append_reference(exe,exe,b'\x90'*32,0x10000000,[profile],65536);results=[]
    if report is None:return []
    # Execute original callsite LEA/PUSH instructions, not a hand-built wrapper ABI.
    match=reference_match_name(profile)
    families=[match,'Navara',match+'Extra','ImprezaProto','',('Vehicles/'+profile['runtime_family'] if match==profile['runtime_family'] else profile['runtime_family'])]
    for family in families:
        for delta in [-.15,0,.15]:
            u=machine(exe);u.mem_map(0x10000000,65536);u.mem_write(0x10000000,blob)
            layout=parse_pe32_layout(exe);off=layout.va_to_file_offset(0x44f334);u.mem_write(0x44f334,image[off:off+15])
            base=0x100e000;cfg=base+0x34;ptr(u,base+0x18,0x2000000);u.mem_write(0x2000000,family.encode()+b'\0')
            f32(u,cfg+0x110,delta);f32(u,cfg+0x17c,delta)
            u.reg_write(ESP,base);u.reg_write(EBP,2);u.reg_write(EBX,123);u.reg_write(ESI,456);u.reg_write(EDI,789);u.reg_write(EDX,654)
            u.reg_write(FLAGS,0x203)
            u.mem_write(0x1003000,bytes.fromhex('d9eb d9e8'));u.emu_start(0x1003000,0x1003004,count=2) # pi, then 1
            u.emu_start(0x44f334,PUBLISH,count=10000)
            if u.reg_read(EIP)!=PUBLISH or u.reg_read(ESP)!=base-12:raise ValueError('publication adapter ABI failed')
            if [u.reg_read(x) for x in [EBP,EBX,ESI,EDI,EDX]]!=[2,123,456,789,654] or u.reg_read(ECX)!=base+0x1c or u.reg_read(EAX)!=cfg:raise ValueError('publication adapter corrupted registers')
            if u.reg_read(FLAGS)!=0x203:raise ValueError('publication adapter corrupted integer flags')
            u.mem_write(0x1003010,bytes.fromhex('dd1d00400002 dd1d08400002'));u.emu_start(0x1003010,0x100301c,count=2)
            if struct.unpack('<2d',bytes(u.mem_read(0x2004000,16)))!=(1.,math.pi):raise ValueError('publication adapter unbalanced x87 stack')
            for axle,offset in [('Front',0x110),('Rear',0x17c)]:
                expected=delta+(profile['ride_height_reference_m'][axle] if family==match else 0)
                if abs(get(u,cfg+offset)-expected)>1e-6:raise ValueError('family isolation/reference mismatch')
            results.append({'family':family,'menu_mm':delta*1000,'front_physical_m':get(u,cfg+0x110),'rear_physical_m':get(u,cfg+0x17c)})
    # Prefix, foreign build and callsite changes are rejected.
    if blob[:32]!=b'\x90'*32:raise ValueError('existing extension prefix changed')
    try:append_reference(b'X'+exe[1:],exe,b'\x90'*32,0x10000000,[profile],65536)
    except ValueError:pass
    else:raise ValueError('foreign executable was accepted')
    altered=bytearray(exe);off=parse_pe32_layout(exe).va_to_file_offset(0x44f33e);altered[off]=0x90
    try:append_reference(exe,bytes(altered),b'\x90'*32,0x10000000,[profile],65536)
    except ValueError:pass
    else:raise ValueError('changed parent callsite was accepted')
    return results

def drivetrain_checks(exe):
    from unicorn.x86_const import UC_X86_REG_ESP as ESP,UC_X86_REG_ECX as ECX
    out=[]
    for mode in (0,1,2):
        u=machine(exe);obj=0x2000000;ptr(u,obj,mode)
        # Synthetic virtual inputs return zero traction; native limited-slip
        # helper therefore divides each admitted axle equally.
        u.mem_write(0x1003000,bytes.fromhex('d9ee c3'))
        ptr(u,0x2001000,0x2001100);ptr(u,0x2001104,0x1003000)
        for i in range(1,7):ptr(u,obj+i*4,0x2001000)
        for i in range(8,11):f32(u,obj+i*4,1.3)
        for i in (1,2,3,4):ptr(u,0x2001000+0xc,0x2002000)
        sp=0x100f000;u.mem_write(sp,struct.pack('<7I',0x1002000,400,0x2003000,0x2003004,0x2003008,0x200300c,0))
        f32(u,sp+4,400);u.reg_write(ESP,sp);u.reg_write(ECX,obj);u.emu_start(0x43d480,0x1002000,count=10000)
        values=[get(u,0x2003000+i*4) for i in range(4)]
        expected={0:[100]*4,1:[200,200,0,0],2:[0,0,200,200]}[mode]
        if values!=expected:raise ValueError('native drivetrain axle routing differs')
        out.append({'internal_mode':mode,'wheel_torques':values,'wheel_order':'front pair, rear pair','input_torque':400})
    return out

def engine_checks(exe,fields):
    from unicorn.x86_const import UC_X86_REG_ESP as ESP,UC_X86_REG_ECX as ECX,UC_X86_REG_EIP as EIP
    n=lambda k:float(fields['Engine/'+k]['value']);curve=[list(map(float,fields[f'Engine/TorqueEntry{i}']['value'].split())) for i in range(int(n('TorqueEntries')))];rows=[]
    def value(x):
        if x<=curve[0][0]:return curve[0][1]
        for a,b in zip(curve,curve[1:]):
            if x<=b[0]:return a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0])
        return curve[-1][1]
    for rpm in [1000,2000,3500,4500,5500,6500,n('RevLimit')+100]:
        for throttle in [0,1]:
            u=machine(exe);engine=0x2000000;obj=0x2001000;samples=0x2002000;sp=0x100f000
            ptr(u,engine+0x70,obj);ptr(u,obj,len(curve));ptr(u,obj+4,samples)
            u.mem_write(samples,b''.join(struct.pack('<2f',*p) for p in curve))
            omega=rpm*.10471967;limit=n('RevLimit')*.10471967
            for off,v in [(0x28,omega),(0x44,limit),(0x50,n('PeakTorque')),(0x54,n('EngineDamping')),(0x58,n('LiftOffEngineDamping'))]:f32(u,engine+off,v)
            ptr(u,sp,0x1002000);f32(u,sp+4,throttle);u.reg_write(ESP,sp);u.reg_write(ECX,engine)
            u.emu_start(0x43c570,0x43c606,count=10000)
            if u.reg_read(EIP)!=0x43c606:raise ValueError('engine torque prefix missed boundary')
            torque=get(u,engine+0x94);expected=(value(rpm/n('RevLimit'))*n('PeakTorque')*throttle if rpm<n('RevLimit') else 0)-omega*(n('EngineDamping') if throttle else n('LiftOffEngineDamping'))
            if abs(torque-expected)>.001:raise ValueError('native engine curve/damping mismatch')
            rows.append({'rpm':rpm,'throttle':throttle,'net_crank_torque_Nm':torque,'net_power_kW':torque*omega/1000})
    return rows

def controls_checks(exe,fields):
    from unicorn.x86_const import UC_X86_REG_ESP as ESP,UC_X86_REG_ECX as ECX
    rows=[]
    for front in (True,False):
        u=machine(exe);wheel=0x2000000;link=0x2001000;control=0x2002000;sp=0x100f000
        ptr(u,wheel+0x18,link);ptr(u,link+0x14,control);u.mem_write(wheel+0x1c,bytes([int(front)]))
        brake=float(fields['Chassis/BrakeTorque'+('Front' if front else 'Rear')]['value']);hand=0 if front else float(fields['Chassis/HandBrakeTorque']['value'])
        for off,val in [(0x114,brake),(0x118,hand),(0x148,.75),(0x14c,.25)]:f32(u,wheel+off,val)
        f32(u,control+0xc,.2);ptr(u,sp,0x1002000);u.reg_write(ESP,sp);u.reg_write(ECX,wheel);u.emu_start(0x441240,0x1002000,count=1000)
        if abs(get(u,wheel+0xf8)-brake*.75)>.001 or abs(get(u,wheel+0xfc)-hand*.25)>.001:raise ValueError('native brake controller mismatch')
        u.reg_write(ESP,sp);u.reg_write(ECX,wheel);u.emu_start(0x440f70,0x1002000,count=1000)
        if abs(get(u,wheel+0x13c)-(.2 if front else 0))>1e-6:raise ValueError('native steering axle routing mismatch')
        rows.append({'front':front,'brake_torque':get(u,wheel+0xf8),'handbrake_torque':get(u,wheel+0xfc),'steer_input':get(u,wheel+0x13c),'boundary':'controller-to-wheel helper, not tyre force or steering kinematics'})
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--vehicles',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    exe=a.exe.read_bytes();profile=json.loads(a.profile.read_text());fields=parse_vehicle_config_bytes(a.vehicles.read_bytes(),build='retail-2001-verified').families[profile['runtime_family']]
    fields,setup=effective_setup(fields,reference=profile.get('ride_height_reference_m'))
    r={'status':'PASS_CONTROLLED_NATIVE_PHYSICS','original_exe_sha256':RETAIL_SHA256,'setup':setup,'native_initialization':replay(exe,fields),'native_spring_forces':spring_checks(exe,fields),'ride_reference_cases':reference_checks(exe,profile),'native_drivetrain':drivetrain_checks(exe),'native_engine_curve':engine_checks(exe,fields),'native_controls':controls_checks(exe,fields),'force_summary':suspension_summary(fields),'runtime_qualified':False,'boundary':'original x86 functions, controlled synthetic contacts and parameter blocks; no whole-race integration, collision track, AI, jumping, landing or gameplay qualification'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
