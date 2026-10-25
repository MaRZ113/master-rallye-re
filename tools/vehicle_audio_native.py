"""Bounded physical-CarID-scoped MR engine waveform substitution.

Only constructor engine-name interning calls change. Native synthesis, tuning,
physics identity, other sounds and stock donor resources remain unchanged.
"""
from __future__ import annotations
import hashlib, struct
try:
    import patch_vehicle_registry_id26 as registry
except ImportError:
    from tools import patch_vehicle_registry_id26 as registry
from master_rallye.addon_sdk.audio_profile import validate_profile, engine_resource

RETAIL_SHA256='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
INTERN=0x4d0580
RACE_BROKER=0x4ada50
CAR_ID=0x4ac660
# Original constructor case-specific intern calls, not guessed Mat/profile IDs.
SITES={0:0x4090c8,1:0x409130,2:0x409198,3:0x409200,4:0x409268,5:0x4092d0,
       6:0x409338,7:0x4093a0,8:0x409408,9:0x409470,10:0x4094d8,11:0x409540,
       12:0x4095a8,13:0x409614,14:0x409656,15:0x409764,16:0x409694,
       17:0x4096fc,18:0x40989c,19:0x4097cc,20:0x409834,21:0x40989c,22:0x409904}

def call(source,target):return b'\xe8'+struct.pack('<i',target-source-5)

def make_wrapper(base_va,profiles):
    """Entry ESI is native gaAiVehicleSound*, ECX is intern output handle.

    [ESI+54] is participant slot. Original getter seam has already mapped the
    constructor tuning ID, so resolve the physical ID again through the native
    Race broker. No process-global current-car scratch or donor mutation.
    """
    code=registry._CodeImage(base_va);code.label('entry');code.emit(bytes.fromhex('9c60 ff7654'))
    code.call(RACE_BROKER);code.emit(bytes.fromhex('89c1'));code.call(CAR_ID)
    for i,p in enumerate(profiles):
        code.emit(b'\x3d'+struct.pack('<I',p['physical_car_id']));code.jne('next'+str(i))
        code.mov_eax_literal('resource'+str(i));code.emit(bytes.fromhex('89442428'));code.jump('done');code.label('next'+str(i))
    code.label('done');code.emit(bytes.fromhex('619d'));code.jump(INTERN)
    for i,p in enumerate(profiles):code.label('resource'+str(i));code.emit(engine_resource(p).encode('ascii')+b'\0')
    return code.build()

def append_audio(source,image,blob,payload_va,profiles,allocation_size):
    if not profiles:return image,blob,None
    if len(profiles)>16:raise ValueError('audio profile count exceeds SDK guard')
    ids=set();names=set();groups={}
    for p in profiles:
        validate_profile(p)
        if p['physical_car_id'] in ids or p['namespace'] in names:raise ValueError('duplicate custom audio CarID or namespace')
        ids.add(p['physical_car_id']);names.add(p['namespace']);groups.setdefault(SITES[p['stock_audio_profile_id']],[]).append(p)
    if hashlib.sha256(source).hexdigest()!=RETAIL_SHA256:raise ValueError('unqualified custom-audio executable')
    pe=registry.parse_pe(source);out=bytearray(image);combined=blob;operations=[];entries=[]
    # ESI ownership and slot producer must still match the original constructor.
    at=registry.va_to_file_offset(pe,0x408f9e,9)
    if source[at:at+9]!=bytes.fromhex('c70608f96800894654') or image[at:at+9]!=source[at:at+9]:raise ValueError('audio constructor slot ABI preimage changed')
    for site,rows in sorted(groups.items()):
        rows=sorted(rows,key=lambda x:x['physical_car_id']);off=registry.va_to_file_offset(pe,site,5);before=call(site,INTERN)
        if source[off:off+5]!=before or image[off:off+5]!=before:raise ValueError('engine-name intern call preimage changed')
        combined+=b'\x90'*((-len(combined))%16);entry=payload_va+len(combined)
        body=make_wrapper(entry,rows);combined+=body;after=call(site,entry);out[off:off+5]=after
        operations.append({'name':'independent_engine_source_'+hex(site),'file_offset':off,'original_bytes':before.hex(),'replacement_bytes':after.hex()})
        entries.append({'entry_va':entry,'size':len(body),'call_va':site,'profiles':[{'physical_car_id':p['physical_car_id'],'stock_audio_profile_id':p['stock_audio_profile_id'],'engine_resource':engine_resource(p)} for p in rows]})
    if len(combined)>allocation_size:raise ValueError('custom audio exceeds existing sealed allocation')
    report={'operations':operations,'entries':entries,'prefix_size':len(blob),'prefix_sha256':hashlib.sha256(blob).hexdigest(),
        'native_intern_va':INTERN,'physical_carid_getter_va':CAR_ID,'race_broker_va':RACE_BROKER,
        'scope':'engine source name at construction, exact physical CarID; native tuning and per-frame synthesis unchanged',
        'runtime_qualified':False}
    return bytes(out),combined,report
