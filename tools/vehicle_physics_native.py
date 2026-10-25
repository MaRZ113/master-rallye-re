"""Exact retail participant-publication adapter for an optional ride datum.

The original menu continues to edit absolute -0.15..+0.15 values, now relative
to this explicit SDK datum. No spring, wheel mesh or visual offset is changed.
Only the selected named family is adjusted, after native player deltas and
before the unchanged CarN publisher. Original on-disk executable is untouched.
"""
import hashlib,struct
import patch_vehicle_registry_id26 as registry
from master_rallye.addon_sdk.physics_profile import validate_profile

CALL=0x44f33e
PUBLISH=0x4938c0
RETAIL_SHA256='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'

def reference_match_name(profile):
    """0044ED50 retains the bare registry name; 00493770 adds Vehicles/ later.

    Omitted binding reproduces the historical V-PHYS2 payload byte for byte.
    New profiles must explicitly opt into the source-qualified registry name.
    """
    return ('' if profile.get('ride_height_reference_binding')=='registry_name' else 'Vehicles/')+profile['runtime_family']

def runtime_reference(profile):
    """Actual raw-name publication result, unlike the old intended preview."""
    return profile.get('ride_height_reference_m',{}) if profile.get('ride_height_reference_binding')=='registry_name' else {}

def append_reference(source,image,blob,payload_va,profiles,allocation_size):
    """Append bounded code to the sealed damage extension; preserve its prefix."""
    active=[]
    for profile in profiles:
        validate_profile(profile,donor_family=profile['donor_family'],runtime_family=profile['runtime_family'])
        if 'ride_height_reference_m' in profile:active.append(profile)
    if not active:return image,blob,None
    if len(active)>16 or len({p['runtime_family'] for p in active})!=len(active):raise ValueError('duplicate or excessive physics reference families')
    if hashlib.sha256(source).hexdigest()!=RETAIL_SHA256:raise ValueError('unqualified physics reference executable')
    pe=registry.parse_pe(source);off=registry.va_to_file_offset(pe,CALL,5)
    expected=b'\xe8'+struct.pack('<i',PUBLISH-CALL-5)
    # Caller ABI and frame: family string at caller ESP+18, config at ESP+34;
    # two PUSHes and CALL put them at wrapper ESP+24 and ESP+08 respectively.
    pre=registry.va_to_file_offset(pe,0x44f334,10)
    if source[pre:pre+10]!=bytes.fromhex('8d4424348d4c241c5055') or source[off:off+5]!=expected or image[off:off+5]!=expected:raise ValueError('physics publisher caller preimage changed')
    prefix=blob+b'\x90'*((-len(blob))%16);code=registry._CodeImage(payload_va+len(prefix))
    emit=lambda s:code.emit(bytes.fromhex(s))
    code.label('entry');emit('9c60') # preserve flags and all integer registers
    for i,p in enumerate(active):
        emit('8b742448 85f6');code.je('next'+str(i))
        code.mov_eax_literal('family'+str(i));emit('89c7 b9');code.emit(struct.pack('<I',len(reference_match_name(p).encode())+1))
        emit('fc f3a6');code.jne('next'+str(i))
        emit('8b44242c') # original second argument: parameter block
        for axle,offset in [('Front',0x110),('Rear',0x17c)]:
            emit('d980');code.emit(struct.pack('<I',offset))
            code.mov_eax_literal('offset'+axle+str(i));emit('d800')
            emit('8b44242c d998');code.emit(struct.pack('<I',offset))
        code.jump('done');code.label('next'+str(i))
    code.label('done');emit('619d');code.jump(PUBLISH)
    for i,p in enumerate(active):
        code.label('family'+str(i));code.emit(reference_match_name(p).encode()+b'\0');code.align(4)
        for axle in ('Front','Rear'):
            code.label('offset'+axle+str(i));code.emit(struct.pack('<f',p['ride_height_reference_m'][axle]))
    tail=code.build();combined=prefix+tail
    if len(combined)>allocation_size:raise ValueError('physics reference exceeds existing sealed allocation')
    out=bytearray(image);after=b'\xe8'+struct.pack('<i',code.base_va-CALL-5);out[off:off+5]=after
    report={'entry_va':code.base_va,'prefix_size':len(blob),'prefix_sha256':hashlib.sha256(blob).hexdigest(),
        'families':[{ 'family':'Vehicles/'+p['runtime_family'],'reference_m':p['ride_height_reference_m']} for p in active],
        'call_va':CALL,'native_publisher_va':PUBLISH,'caller_family_stack_offset':0x24,'caller_parameter_stack_offset':8,
        'operations':[{'name':'family_scoped_ride_reference_before_participant_publish','file_offset':off,'original_bytes':expected.hex(),'replacement_bytes':after.hex()}],
        'scope':'after native player deltas, before CarN publication; exact family string including terminator; stock passes through',
        'runtime_qualified':False}
    if any(p.get('ride_height_reference_binding') for p in active):
        report['registry_name_binding']=[{'runtime_family':p['runtime_family'],'match':reference_match_name(p)} for p in active]
    return bytes(out),combined,report
