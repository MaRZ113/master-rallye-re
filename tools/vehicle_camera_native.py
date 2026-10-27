"""Exact-retail camera-only bounds return, guarded by current CarN physical ID.

No shared XML, model data, physics, target transform or FOV is modified.
"""
import hashlib, struct
import patch_vehicle_registry_id26 as registry
from vehicle_shadow_native import make_wrapper as bounds_wrapper, RETAIL_SHA256, NATIVE

CALLS=(0x52c652,0x52c65e,0x52c677)
NAME=0x4d0570
BROKER=0x4ada50
CAR_ID=0x4ac660


def make_wrapper(base_va, profiles, *, selector=False):
    c=registry._CodeImage(base_va)
    emit=lambda x:c.emit(bytes.fromhex(x))
    c.label('entry');emit('9c60')
    # Reject unrelated model keys before invoking the native broker accessor
    # (which uses a mutable scratch key and is not a pure dictionary read).
    emit('8d490c');c.call(NAME);emit('85c0');c.je('fallback');emit('8be8')
    for i,p in enumerate(profiles):
        label='model_next'+str(i)
        emit('8bf5');c.mov_eax_literal('model_name'+str(i));emit('8bd8 b9');c.emit(struct.pack('<I',len(p['model_resource'])+1))
        c.label('model_char'+str(i));emit('8a06 3c5c');c.jne('model_slash'+str(i));emit('b02f')
        c.label('model_slash'+str(i));emit('3c41');c.emit(bytes.fromhex('0f82'));c.rel32.append((len(c.code),len(c.code)+4,'model_folded'+str(i)));c.emit(b'\0'*4)
        emit('3c5a');c.ja('model_folded'+str(i));emit('0c20')
        c.label('model_folded'+str(i));emit('3a03');c.jne(label)
        emit('46 43 49');c.jne('model_char'+str(i));c.jump('model_allowed');c.label(label)
    c.jump('fallback');c.label('model_allowed')
    # EDI is original initializer's target scene entity. Its +5C name is set
    # by 004F59F0; camera setup formats the same Car%d name at 004B7AFB.
    emit('85ff');c.je('fallback')
    emit('8d4f5c');c.call(NAME);emit('85c0');c.je('fallback')
    emit('803843');c.jne('fallback')
    emit('80780161');c.jne('fallback')
    emit('80780272');c.jne('fallback')
    emit('8d7003 31d2 31c9')
    c.label('digit');emit('0fb606 83e830 83f809');c.ja('fallback')
    emit('6bd20a 01c2 46 41')
    # At most two decimal digits and participant slot <=63. Native names are
    # canonical (Car0, not Car00); foreign/replay camera names pass through.
    emit('803e00');c.je('number_done')
    emit('83f902');c.je('fallback');emit('85d2');c.je('fallback');c.jump('digit')
    c.label('number_done');emit('83fa3f');c.ja('fallback')
    # Avoid lazy broker construction outside an initialized race lifetime.
    emit('833d94656f0000');c.je('fallback')
    emit('52');c.call(BROKER);emit('85c0');c.je('broker_null')
    emit('8bc8');c.call(CAR_ID)
    for i,p in enumerate(profiles):
        emit('3d');c.emit(struct.pack('<I',p['car_id']));c.je('selected'+str(i))
    c.jump('fallback')
    c.label('broker_null');emit('83c404');c.jump('fallback')
    for i,p in enumerate(profiles):
        c.label('selected'+str(i))
        if selector:
            # An allowed different model must not borrow this ID's parameters,
            # even when two source models happen to have identical bounds.
            emit('8bf5');c.mov_eax_literal('model_name'+str(i));emit('8bd8 b9');c.emit(struct.pack('<I',len(p['model_resource'])+1))
            c.label('selected_char'+str(i));emit('8a06 3c5c');c.jne('selected_slash'+str(i));emit('b02f')
            c.label('selected_slash'+str(i));emit('3c41');c.emit(bytes.fromhex('0f82'));c.rel32.append((len(c.code),len(c.code)+4,'selected_fold'+str(i)));c.emit(b'\0'*4)
            emit('3c5a');c.ja('selected_fold'+str(i));emit('0c20');c.label('selected_fold'+str(i));emit('3a03');c.jne('fallback');emit('46 43 49');c.jne('selected_char'+str(i))
            # Reuse the exact owner/model gate, and additionally pin all bounds.
            emit('8b4c2418');c.call(NATIVE);emit('85c0');c.je('fallback')
            for off in range(0,44,4):
                emit('8178');c.emit(bytes([off]));c.emit(bytes.fromhex(p['native_bounds_values_hex'])[off:off+4]);c.jne('fallback')
            emit('c744241c');c.emit(struct.pack('<I',i+1));emit('619dc3')
        else:emit('619d');c.jump('bounds'+str(i))
    c.label('fallback')
    if selector:emit('c744241c00000000619dc3')
    else:emit('619d');c.jump(NATIVE)
    for i,p in enumerate(profiles):
        c.label('model_name'+str(i));c.emit(p['model_resource'].encode('ascii')+b'\0')
    # Forward labels are resolved after the bounded wrappers are appended.
    return c


def make_parameter_wrapper(base_va,profiles,kind):
    """Wrap original record copy; modify only its private object/out-FOV values.

    EDI=target, ESI=manager at the two exact 004B82A0 copy calls. No pointers
    survive this invocation. Overrides intentionally apply to normal AND split.
    """
    c=registry._CodeImage(base_va);emit=lambda s:c.emit(bytes.fromhex(s))
    original=0x4b98e0 if kind=='follow'else 0x4b99c0;argc=4 if kind=='follow'else 3
    emit('55 8bec')
    for off in reversed(range(8,8+argc*4,4)):emit('ff75');c.emit(bytes([off]))
    c.call(original);emit('9c60')
    # Ordinary player cycle only. Alternate manager cycles are not authored.
    emit('80be e6010000 00');c.jne('done');emit('80be e7010000 00');c.jne('done')
    emit('85ff');c.je('done');emit('8b4f50 85c9');c.je('done');c.call('owner_gate')
    for i,p in enumerate(profiles):
        emit('3d');c.emit(struct.pack('<I',i+1));c.je('vehicle'+str(i))
    c.jump('done')
    for i,p in enumerate(profiles):
        c.label('vehicle'+str(i))
        for mode,values in p['profile'].get('mode_overrides',{}).items():
            if not mode.startswith(kind):continue
            label=f'next_{i}_{mode}';emit('837d0c');c.emit(bytes([int(mode[-1])])) ;c.jne(label)
            for name,value in values.items():
                if name=='FOV':emit('8b5510 c702');c.emit(struct.pack('<f',value))
                else:
                    emit('8b5508 c742');c.emit(bytes([{'Dist Front':0x48,'Dist Back':0x4c,'Dist Up':0x50}[name]]));c.emit(struct.pack('<f',value))
            c.jump('done');c.label(label)
        c.jump('done')
    c.label('done');emit('619d5d c2');c.emit(struct.pack('<H',argc*4))
    c.label('owner_gate');gate=make_wrapper(base_va+len(c.code),profiles,selector=True);c.emit(gate.build())
    return c.build()


def make_payload(base_va, profiles):
    c=make_wrapper(base_va,profiles)
    for i,p in enumerate(profiles):
        c.label('bounds'+str(i))
        tail,_=bounds_wrapper(base_va+len(c.code),[{**p,'shadow_bounds_hex':p['camera_bounds_hex']}])
        c.emit(tail)
    return c.build()


def append_camera(source,image,blob,payload_va,profiles,allocation_size):
    if not profiles:return image,blob,None
    if hashlib.sha256(source).hexdigest()!=RETAIL_SHA256 or len(image)!=len(source):raise ValueError('unqualified camera executable')
    if len(profiles)>16 or len({p['car_id'] for p in profiles})!=len(profiles):raise ValueError('duplicate/excessive camera profiles')
    for p in profiles:
        if type(p['car_id']) is not int or not 1<=p['car_id']<=29:raise ValueError('unsupported camera CarID (0 reserved until missing-key qualification)')
        if len(bytes.fromhex(p['native_bounds_values_hex']))!=44 or len(bytes.fromhex(p['camera_bounds_hex']))!=44:raise ValueError('invalid camera bounds record')
    pe=registry.parse_pe(source);offsets=[]
    for call in CALLS:
        off=registry.va_to_file_offset(pe,call,5);expected=b'\xe8'+struct.pack('<i',NATIVE-call-5)
        if source[off:off+5]!=expected or image[off:off+5]!=expected:raise ValueError('camera getter call preimage differs')
        offsets.append((call,off,expected))
    prefix=blob+b'\x90'*(-len(blob)%16);entry=payload_va+len(prefix)
    tail=make_payload(entry,profiles);combined=prefix+tail
    if len(combined)>allocation_size:raise ValueError('camera adapter exceeds existing allocation')
    result=bytearray(image);ops=[]
    for call,off,expected in offsets:
        after=b'\xe8'+struct.pack('<i',entry-call-5);result[off:off+5]=after
        ops.append({'name':'physical_car_camera_extents','file_offset':off,'original_bytes':expected.hex(),'replacement_bytes':after.hex()})
    if any(p['profile'].get('mode_overrides')for p in profiles):
        for kind,call,target in [('follow',0x4b83a0,0x4b98e0),('fixed',0x4b83f3,0x4b99c0)]:
            # Sites verified from original assembly; fail closed if source differs.
            off=registry.va_to_file_offset(pe,call,5);expected=b'\xe8'+struct.pack('<i',target-call-5)
            if source[off:off+5]!=expected or result[off:off+5]!=expected:raise ValueError('camera parameter-copy preimage differs: '+kind)
            combined+=b'\x90'*(-len(combined)%16);at=payload_va+len(combined)
            combined+=make_parameter_wrapper(at,profiles,kind)
            after=b'\xe8'+struct.pack('<i',at-call-5);result[off:off+5]=after
            ops.append({'name':'physical_car_'+kind+'_parameters','file_offset':off,'original_bytes':expected.hex(),'replacement_bytes':after.hex()})
        if len(combined)>allocation_size:raise ValueError('camera parameter adapter exceeds allocation')
    return bytes(result),combined,{'entry_va':entry,'operations':ops,'bindings':profiles,'scope':'Follow extents; optional per-mode parameter copies (normal AND split). Current CarN physical CarID plus exact source model/bounds guards; no cached owners or global XML writes.','runtime_qualified':False,'writable_ranges':[]}
