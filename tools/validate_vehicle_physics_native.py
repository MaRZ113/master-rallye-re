"""Execute exact retail wheel-parameter initialization in isolated Unicorn.

Stops before tyre-table resolution and simulates neither contacts nor a race.
The captured anchor is the suspension attachment datum, not settled ride height.
"""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.vehicle_config_analysis import parse_vehicle_config_bytes
from master_rallye.vehicle_family_broker import RETAIL_EXE_SHA256
from master_rallye.vehicle_physics_binding import parse_pe32_layout
import j2_frontend_reentry as j2
import copy

FLOAT_OFFSETS={
 'Dimensions/Length':0,'Dimensions/Width':4,'Dimensions/Height':8,'Dimensions/WheelBase':0xc,
 'Dimensions/TrackWidthFront':0x10,'Dimensions/TrackWidthRear':0x14,'Dimensions/WheelRadiusFront':0x18,'Dimensions/WheelRadiusRear':0x1c,
 'Chassis/TotalMass':0x20,'Chassis/HandBrakeTorque':0x40,'Chassis/BrakeTorqueFront':0x44,'Chassis/BrakeTorqueRear':0x48,
 'Chassis/RollingDrag':0x4c,'Chassis/DragCoeff':0x50,'Chassis/AerodynamicDragCoeff':0x54,
 'Chassis/MinAerodynamicDownForceSpeed':0x58,'Chassis/MaxAerodynamicDownForceSpeed':0x5c,'Chassis/AerodynamicDownForceCoeff':0x60,
 'Chassis/Restitution':0x64,'Chassis/SlidingFriction':0x68,'Chassis/Gravity':0x6c,
 'Steering/MinSpeed':0x70,'Steering/MaxSpeed':0x74,'Steering/SteerScale':0x78,'Steering/MaxSteer':0x7c,'Steering/SteerOffset':0x80,
}
SUSP_FIELDS=('UnsprungMass','WheelMOI','AntiDiveCoeff','MaxBounce','MaxDroop','SpringArmRatio','DamperArmRatio','ToeVsLong','SteerVsLat','SteerVsMoment','ToeVsJounce','CamverVsJounce','RideHeight','SpringRate','DamperRate','AuxRollStiffness','ToeIn','Camber')
for axle,base in [('Front',0xe0),('Rear',0x14c)]:
    FLOAT_OFFSETS.update({f'Suspension/{axle}/{key}':base+i*4 for i,key in enumerate(SUSP_FIELDS)})
    FLOAT_OFFSETS.update({f'Suspension/{axle}/{key}':base+offset for key,offset in [('WheelDamping',0x58),('WaterDamping',0x5c),('SuspAppPointOffsetLat',0x60),('SuspAppPointOffsetLong',0x64),('SuspAppPointOffsetVert',0x68)]})

def replay(exe,fields):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ECX as ECX,UC_X86_REG_ESP as ESP,UC_X86_REG_EIP as EIP
    if hashlib.sha256(exe).hexdigest()!=RETAIL_EXE_SHA256:raise ValueError('unqualified original EXE')
    layout=parse_pe32_layout(exe);start=0x44077c;end=0x440af1
    # Entry and branch constants are checked independently against mapped bytes.
    if exe[layout.va_to_file_offset(0x440770):layout.va_to_file_offset(0x44077c)]!=bytes.fromhex('51535556578bf1e8d4810c00'):
        raise ValueError('native wheel initializer entry bytes differ')
    output=[]
    for front,positive in [(True,True),(True,False),(False,True),(False,False)]:
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
        _,sections=j2.addon_runtime._pe_sections(exe)
        for s in sections:u.mem_write(0x400000+s['rva'],exe[s['raw_offset']:s['raw_offset']+s['raw_size']])
        u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x10000)
        cfg=0x2000000;wheel=0x2001000
        for path,offset in FLOAT_OFFSETS.items():u.mem_write(cfg+offset,struct.pack('<f',float(fields[path]['value'])))
        cg=[float(x) for x in fields['Chassis/CentreOfGravity']['value'].split()];u.mem_write(cfg+0x34,struct.pack('<3f',*cg))
        u.mem_write(wheel+0x17c,struct.pack('<I',cfg));u.mem_write(wheel+0x1c,bytes([int(front),int(positive),1]))
        u.mem_write(0x1002000,bytes.fromhex('dbe3'));u.emu_start(0x1002000,0x1002002,count=1)
        # Prefix has ESI=wheel and zero EBP after its own branch. It makes no
        # external calls within this selected interval.
        from unicorn.x86_const import UC_X86_REG_ESI as ESI
        u.reg_write(ECX,wheel);u.reg_write(ESI,wheel);u.reg_write(ESP,0x100fff0)
        u.emu_start(start,end,count=100000)
        if u.reg_read(EIP)!=end:raise ValueError('native parameter prefix did not reach the tyre-table boundary')
        def vec(offset,n=1):return list(struct.unpack('<'+'f'*n,bytes(u.mem_read(wheel+offset,4*n))))
        axle='Front' if front else 'Rear';anchor=vec(0x30,3);expected=[float(fields[f'Dimensions/TrackWidth{axle}']['value'])*(.5 if positive else -.5),-float(fields[f'Suspension/{axle}/RideHeight']['value']),float(fields['Dimensions/WheelBase']['value'])*(.5 if front else -.5)]
        if math.dist(anchor,expected)>1e-6:raise ValueError('native anchor differs from declared formula')
        output.append({'axle':axle,'positive_x':positive,'anchor':anchor,'radius':vec(0x3c)[0],'sprung_corner_mass':vec(0x20)[0],'spring_rate':vec(0x60)[0],'damper_rate':vec(0x68)[0],'travel_bounce_droop':vec(0x4c,2),'toe_radians':vec(0x134)[0],'camber_radians':vec(0x154)[0]})
    return {'status':'PASS_ORIGINAL_NATIVE_PARAMETER_PREFIX','original_exe_sha256':RETAIL_EXE_SHA256,'instruction_interval':[hex(start),hex(end)],'rows':output,'chassis':chassis_replay(exe,fields),'runtime_qualified':False,'boundary':'isolated CPU prefix, synthetic initialized parameter block; stops before tyre-table lookup; no contact integration, dynamic sag, rendering or gameplay claimed'}

def chassis_replay(exe,fields):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ECX as ECX,UC_X86_REG_ESP as ESP,UC_X86_REG_EIP as EIP
    if hashlib.sha256(exe).hexdigest()!=RETAIL_EXE_SHA256:raise ValueError('unqualified original EXE')
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
    _,sections=j2.addon_runtime._pe_sections(exe)
    for s in sections:u.mem_write(0x400000+s['rva'],exe[s['raw_offset']:s['raw_offset']+s['raw_size']])
    u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x10000);cfg=0x2000000;actor=0x2002000;out=0x2003000
    for path,offset in FLOAT_OFFSETS.items():u.mem_write(cfg+offset,struct.pack('<f',float(fields[path]['value'])))
    radii=[float(x) for x in fields['Chassis/MomentOfInertia']['value'].split()];cuboid=fields['Chassis/UseCuboidMOI']['value']=='True'
    u.mem_write(cfg+0x24,struct.pack('<3f',*radii));u.mem_write(cfg+0x30,bytes([int(cuboid)]));u.mem_write(actor+8,struct.pack('<I',cfg))
    u.mem_write(0x1002000,bytes.fromhex('dbe3'));u.emu_start(0x1002000,0x1002002,count=1)
    u.mem_write(0x100fff0,struct.pack('<2I',0x1001000,out));u.reg_write(ECX,actor);u.reg_write(ESP,0x100fff0);u.emu_start(0x43a390,0x1001000,count=10000)
    if u.reg_read(EIP)!=0x1001000 or u.reg_read(ESP)!=0x100fff8:raise ValueError('native chassis helper ABI mismatch')
    tensor=list(struct.unpack('<3f',bytes(u.mem_read(out,12))));f=lambda key:float(fields[key]['value'])
    sprung=f('Chassis/TotalMass')-2*(f('Suspension/Front/UnsprungMass')+f('Suspension/Rear/UnsprungMass'))
    L,W,H=(f('Dimensions/'+x) for x in ('Length','Width','Height'))
    expected=[x*sprung/12 for x in (L*H,L*W,W*H)] if cuboid else [x*x*sprung for x in radii]
    if any(abs(a-b)>max(1e-3,abs(b)*1e-6) for a,b in zip(tensor,expected)):raise ValueError('native inertia formula mismatch')
    return {'sprung_mass':sprung,'native_diagonal_inertia':tensor,'UseCuboidMOI':cuboid,'observed_formula':'sprung_mass*(L*H,L*W,W*H)/12' if cuboid else 'sprung_mass*MomentOfInertia_component^2','boundary':'exact 0043A390 / 0043A370 instructions; native cuboid branch uses products, not a textbook squared-sum formula'}

def sensitivity(exe,fields):
    base=replay(exe,fields);checks=[]
    for path,delta,field,component,expected in [
        ('Dimensions/WheelBase',.1,'anchor',2,.05),('Dimensions/TrackWidthFront',.1,'anchor',0,.05),
        ('Dimensions/WheelRadiusFront',.01,'radius',None,.01),('Suspension/Front/RideHeight',.01,'anchor',1,-.01),
        ('Suspension/Front/SpringRate',1000,'spring_rate',None,1000),('Suspension/Front/DamperRate',100,'damper_rate',None,100),
        ('Suspension/Front/MaxBounce',.01,'travel_bounce_droop',0,.01),('Suspension/Front/MaxDroop',.01,'travel_bounce_droop',1,.01)]:
        changed=copy.deepcopy(fields);changed[path]['value']=str(float(changed[path]['value'])+delta);result=replay(exe,changed)
        a=base['rows'][0][field];b=result['rows'][0][field];actual=b[component]-a[component] if component is not None else b-a
        if abs(actual-expected)>max(1e-5,abs(expected)*1e-5):raise ValueError('native parameter sensitivity mismatch '+path)
        checks.append({'path':path,'input_delta':delta,'native_front_positive_field':field,'component':component,'observed_delta':actual,'expected_delta':expected,'scope':'initialization only, no integration'})
    changed=copy.deepcopy(fields);changed['Chassis/TotalMass']['value']=str(float(fields['Chassis/TotalMass']['value'])+100);mass=replay(exe,changed)
    expected=(1+float(fields['Chassis/CentreOfGravity']['value'].split()[2])/float(fields['Dimensions/Length']['value']))*25
    actual=mass['rows'][0]['sprung_corner_mass']-base['rows'][0]['sprung_corner_mass']
    if abs(actual-expected)>1e-4:raise ValueError('native corner-mass sensitivity mismatch')
    checks.append({'path':'Chassis/TotalMass','input_delta':100,'native_field':'front sprung corner mass','observed_delta':actual,'expected_delta':expected})
    changed=copy.deepcopy(fields);changed['Chassis/UseCuboidMOI']['value']='True';box=chassis_replay(exe,changed)
    checks.append({'path':'Chassis/UseCuboidMOI','input_value':True,'native_chassis':box,'scope':'helper instructions only; no behavior tuning applied'})
    changed=copy.deepcopy(fields);values=[float(x) for x in changed['Chassis/MomentOfInertia']['value'].split()];values[0]+=.1;changed['Chassis/MomentOfInertia']['value']=' '.join(str(x) for x in values);changed['Chassis/UseCuboidMOI']['value']='False'
    tensor=chassis_replay(exe,changed);checks.append({'path':'Chassis/MomentOfInertia','input_delta':[.1,0,0],'native_chassis':tensor,'scope':'exact native squared-radius formula verified'})
    return checks

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--vehicles',type=Path,required=True);p.add_argument('--family',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--sensitivity',action='store_true');a=p.parse_args()
    d=parse_vehicle_config_bytes(a.vehicles.read_bytes(),build='retail-2001-verified');exe=a.exe.read_bytes();fields=d.families[a.family];r=replay(exe,fields)
    if a.sensitivity:r['sensitivity_checks']=sensitivity(exe,fields)
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
