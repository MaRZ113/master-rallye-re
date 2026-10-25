"""Original registry/caller slices qualify the ride guard's actual namespace.

String allocation/copy is an explicit ABI stub; name bytes are never prefixed
by the harness. Registry construction, field addressing and shim execute x86.
This is controlled replay, not live suspension or gameplay evidence.
"""
import argparse,copy,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from validate_vehicle_physics_forces import machine,ptr,f32,get
from vehicle_physics_native import append_reference,PUBLISH
from master_rallye.vehicle_physics_binding import parse_pe32_layout

def validate(exe,profile):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ECX as ECX,UC_X86_REG_ESP as ESP,UC_X86_REG_EAX as EAX,UC_X86_REG_ESI as ESI,UC_X86_REG_EBP as EBP,UC_X86_REG_EIP as EIP
    if profile.get('ride_height_reference_binding')!='registry_name':raise ValueError('new qualification requires explicit registry_name binding')
    layout=parse_pe32_layout(exe);family=profile['runtime_family'];rows=[]
    for fixed in (False,True):
        definition=copy.deepcopy(profile)
        if not fixed:definition.pop('ride_height_reference_binding')
        image,blob,_=append_reference(exe,exe,b'\x90'*32,0x10000000,[definition],131072)
        for name in (family,'Navara',family+'Extra','Vehicles/'+family,'ImprezaProto'):
            for delta in (-.15,0.,.15):
                u=machine(exe);u.mem_map(0x10000000,131072);u.mem_write(0x10000000,blob)
                patch=layout.va_to_file_offset(0x44f33e);u.mem_write(0x44f33e,image[patch:patch+5])
                def hook(uc,at,size,data):
                    if at==0x4d1990:
                        # Native string-copy boundary. Preserve supplied bytes;
                        # no allocator/refcount semantics claimed by this stub.
                        sp=uc.reg_read(ESP);ret,arg=struct.unpack('<2I',uc.mem_read(sp,8))
                        ptr(uc,uc.reg_read(ECX),arg);uc.reg_write(EAX,uc.reg_read(ECX))
                        uc.reg_write(ESP,sp+8);uc.reg_write(EIP,ret)
                u.hook_add(UC_HOOK_CODE,hook)
                raw=0x2010000;u.mem_write(raw,name.encode()+b'\0')
                registry=0x2000000;record=registry+4+27*0x34;sp=0x100d000
                ptr(u,sp+0x2c,raw);u.reg_write(ECX,record);u.reg_write(ESP,sp)
                u.emu_start(0x45a0c5,0x45a10f,count=1000)
                if struct.unpack('<I',u.mem_read(record+0x20,4))[0]!=raw:raise ValueError('native record name destination changed')
                base=0x100e000;u.reg_write(ESP,base);u.reg_write(EAX,registry);u.reg_write(ESI,27)
                u.emu_start(0x44ee5b,0x44ee71,count=1000)
                if struct.unpack('<I',u.mem_read(base+0x18,4))[0]!=raw:raise ValueError('native caller did not retain raw registry name')
                cfg=base+0x34
                for off in (0x110,0x17c):f32(u,cfg+off,delta)
                u.reg_write(ESP,base);u.reg_write(EBP,0)
                u.emu_start(0x44f334,PUBLISH,count=10000)
                if u.reg_read(EIP)!=PUBLISH or u.reg_read(ESP)!=base-12:raise ValueError('native publisher boundary/ABI failed')
                values={axle:get(u,cfg+off) for axle,off in [('Front',0x110),('Rear',0x17c)]}
                applied=(name==family) if fixed else (name=='Vehicles/'+family)
                for axle,value in values.items():
                    expected=delta+(profile['ride_height_reference_m'][axle] if applied else 0)
                    if abs(value-expected)>1e-6:raise ValueError('raw registry chain disagrees with intended guard')
                rows.append({'corrected_binding':fixed,'raw_registry_name':name,'menu_mm':delta*1000,'published_ride_m':values,'reference_applied':applied})
    return {'status':'PASS_NATIVE_REGISTRY_PUBLICATION_CHAIN','cases':rows,'legacy_real_name_bypasses':True,
        'corrected_real_name_applies_once':True,'prefixed_and_longer_names_bypass_corrected_guard':True,
        'runtime_qualified':False,'boundary':'original registry initializer and caller addressing plus emitted adapter; string copy ABI stub; stop before Broker publisher; no track/contacts'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=validate(a.exe.read_bytes(),json.loads(a.profile.read_text()));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
