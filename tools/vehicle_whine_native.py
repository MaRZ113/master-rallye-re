"""Exact-retail bounded independently owned supplemental audio voices.

Original SFX constructor/manager/backend, separate per-owner lifecycle, one
RW/NX state page. No original disk binary or stock audio resource edits.
"""
from __future__ import annotations
import hashlib, math, struct
try:
    import patch_vehicle_registry_id26 as registry
    from vehicle_audio_native import RETAIL_SHA256, RACE_BROKER, CAR_ID, INTERN
except ImportError:
    from tools import patch_vehicle_registry_id26 as registry
    from tools.vehicle_audio_native import RETAIL_SHA256, RACE_BROKER, CAR_ID, INTERN
from master_rallye.addon_sdk.audio_profile import validate_profile, whine_resource

SFX_CONSTRUCTOR=0x4f63d0
NEW=0x5c1cb4
SITES={
    'construct':(0x409cad,bytes.fromhex('8b8c2488000000')),
    'publish':(0x492cca,bytes.fromhex('8b4f088b54241c')),
    'destroy':(0x409e25,bytes.fromhex('51568bf157')),
    'update':(0x40a026,bytes.fromhex('8b4f088d5678')),
}
MAP_CAPACITY=64


def _bits(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def _u32(value):return struct.pack('<I',value)


def response_values(response,rpm,net_crank_torque,peak_torque,gear_index,volume=1.,finished=False):
    """Documented offline counterpart of the additive control, not native DSP."""
    if any(not math.isfinite(float(x)) for x in (rpm,net_crank_torque,peak_torque,volume)) or not 0<=abs(rpm)<=30000 or not 1<=peak_torque<=100000:
        return {'pitch':1.,'gain':0.}
    rpm=abs(rpm)
    pitch=max(response['pitch_min'],min(response['pitch_max'],rpm/response['reference_rpm']))
    load=max(0.,min(1.,net_crank_torque/peak_torque))
    gain=(response['gain_coast']+(response['gain_drive']-response['gain_coast'])*load)*min(1.,rpm/response['fade_in_rpm'])*max(0.,min(1.,volume))
    if finished or (response['mute_neutral'] and gear_index==1):gain=0.
    return {'pitch':pitch,'gain':gain,'load_proxy':load}


def make_payload(base_va,profiles):
    from native_audio_coff import compile_object,link_object
    from master_rallye.addon_sdk.audio_profile import turbo_resource,bov_resource
    raw,compiler=compile_object();native,functions=link_object(raw,base_va)
    c=registry._CodeImage(base_va);c.emit(native);c.align()
    def emit(h):c.emit(bytes.fromhex(h))
    def state():c.push_literal('cursor')
    def guard(prefix):
        emit('ff7654');c.call(RACE_BROKER);emit('89c1');c.call(CAR_ID)
        for i,p in enumerate(profiles):
            c.emit(b'\x3d'+_u32(p['physical_car_id']));c.je(prefix+str(i))
    c.label('construct');emit('9c60');guard('construct_profile');c.jump('construct_done')
    for i,p in enumerate(profiles):
        c.label('construct_profile'+str(i));state();c.push_literal('profile'+str(i));emit('56');c.call(functions['_layers_construct']);emit('83c40c');c.jump('construct_done')
    c.label('construct_done');emit('619d');c.emit(SITES['construct'][1]);c.jump(0x409cb4)
    c.label('destroy');emit('9c60');state();emit('51');c.call(functions['_layers_destroy']);emit('83c408 619d');c.emit(SITES['destroy'][1]);c.jump(0x409e2a)
    c.label('publish');emit('9c60 8b4f08 8b7c247c');c.mov_eax_literal('map');emit('89c2 bb40000000')
    c.label('map_scan');emit('390a');c.je('map_write');emit('833a00');c.je('map_write');emit('83c208 4b');c.jne('map_scan')
    c.emit(b'\xa1'+b'\0'*4);c.imm32.append((len(c.code)-4,'cursor'));emit('83e03f c1e003 01c2 81ea00020000')
    c.emit(bytes.fromhex('ff05')+b'\0'*4);c.imm32.append((len(c.code)-4,'cursor'))
    c.label('map_write');emit('890a 897a04 619d');c.emit(SITES['publish'][1]);c.jump(0x492cd1)
    c.label('update');emit('9c60');guard('update_profile');c.jump('update_done')
    for i,p in enumerate(profiles):
        c.label('update_profile'+str(i));c.mov_eax_literal('profile'+str(i));emit('89c5');c.jump('update_selected')
    c.label('update_selected')
    # Imported native winmm timeGetTime: no new import or injected OS resolver.
    emit('ff15a0f36800 8b4f08 0fb6542433 8b5c2434 51 52 53 50');state();emit('55 56');c.call(functions['_layers_update']);emit('83c41c')
    c.label('update_done');emit('619d');c.emit(SITES['update'][1]);c.jump(0x40a02c)
    for i,p in enumerate(profiles):
        flags=0
        for k,getter in enumerate((whine_resource,turbo_resource,bov_resource)):
            key=('transmission_whine','turbo_spool','bov_release')[k]
            if key in p:flags|=1<<k
            c.label('resource'+str(i)+'_'+str(k));c.emit((getter(p) if key in p else '').encode()+b'\0')
        c.align(4);c.label('profile'+str(i));c.emit(_u32(flags))
        for k in range(3):c.emit(b'\0'*4);c.imm32.append((len(c.code)-4,'resource'+str(i)+'_'+str(k)))
        wh=p.get('transmission_whine',{}).get('response',{})
        sp=p.get('turbo_spool',{}).get('response',{})
        bv=p.get('bov_release',{}).get('response',{})
        values=[wh.get(k,d) for k,d in zip(('reference_rpm','pitch_min','pitch_max','gain_drive','gain_coast','fade_in_rpm','mute_neutral'),(4000,.35,1.8,.3,.1,1000,True))]
        values += [sp.get(k,d) for k,d in zip(('reference_rpm','pitch_min','pitch_max','gain','fade_in_rpm','load_threshold','spool_up_seconds','spool_down_seconds','mute_neutral'),(4000,.35,1.8,.3,1500,.15,.35,.55,True))]
        values += [bv.get(k,d) for k,d in zip(('release_rate_threshold','boost_threshold','gain','pitch_variation','retrigger_seconds','release_decay_seconds','min_rpm','mute_neutral'),(3,.45,.45,.08,.5,.2,2000,True))]
        c.emit(struct.pack('<24f',*values))
    c.emit(b'\0'*(-(base_va+len(c.code))%4096));c.label('cursor');c.emit(b'\0'*4);c.label('map');c.emit(b'\0'*512);c.label('voices');c.emit(b'\0'*(64*44));c.emit(b'\0'*(4096-516-64*44))
    entries={name:base_va+c.labels[name] for name in ('construct','publish','update','destroy','map','cursor','voices')}
    return c.build(),entries


def append_whine(source,image,blob,payload_va,profiles,allocation_size):
    selected=[];ids=set();names=set()
    for p in profiles:
        validate_profile(p)
        if not any(k in p for k in ('transmission_whine','turbo_spool','bov_release')):continue
        if p['physical_car_id'] in ids or p['namespace'] in names:raise ValueError('duplicate whine CarID or namespace')
        ids.add(p['physical_car_id']);names.add(p['namespace']);selected.append(p)
    if not selected:return image,blob,None
    if len(selected)>16:raise ValueError('whine profile count exceeds SDK guard')
    if hashlib.sha256(source).hexdigest()!=RETAIL_SHA256:raise ValueError('unqualified transmission-whine executable')
    selected.sort(key=lambda p:p['physical_car_id'])
    pe=registry.parse_pe(source);out=bytearray(image);combined=blob+b'\x90'*((-len(blob))%16)
    body,entries=make_payload(payload_va+len(combined),selected);combined+=body;operations=[]
    for name,(site,before) in SITES.items():
        off=registry.va_to_file_offset(pe,site,len(before))
        if source[off:off+len(before)]!=before or image[off:off+len(before)]!=before:raise ValueError('whine '+name+' ABI preimage changed')
        after=b'\xe9'+struct.pack('<i',entries[name]-site-5)+b'\x90'*(len(before)-5)
        out[off:off+len(before)]=after
        operations.append({'name':'independent_transmission_whine_'+name,'file_offset':off,'original_bytes':before.hex(),'replacement_bytes':after.hex()})
    if len(combined)>allocation_size:raise ValueError('transmission whine exceeds existing sealed allocation')
    return bytes(out),combined,{'operations':operations,'entries':entries,'prefix_size':len(blob),'prefix_sha256':hashlib.sha256(blob).hexdigest(),
        'profiles':[{'physical_car_id':p['physical_car_id'],'layers':[k for k in ('transmission_whine','turbo_spool','bov_release') if k in p]} for p in selected],
        'writable_ranges':[{'offset':entries['cursor']-payload_va,'size':4096}],
        'native_helper':__import__('native_audio_coff').compile_object()[1],
        'map_capacity':MAP_CAPACITY,'voice_slot_stride':44,'scope':'bounded independently owned native SFX list voices; timeGetTime response; owner-scoped publication cleanup; no physics-state writes',
        'runtime_qualified':False}
