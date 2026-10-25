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


def make_wrapper(base_va, profiles):
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
        c.label('selected'+str(i));emit('619d');c.jump('bounds'+str(i))
    c.label('fallback');emit('619d');c.jump(NATIVE)
    for i,p in enumerate(profiles):
        c.label('model_name'+str(i));c.emit(p['model_resource'].encode('ascii')+b'\0')
    # Forward labels are resolved after the bounded wrappers are appended.
    return c


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
    return bytes(result),combined,{'entry_va':entry,'operations':ops,'bindings':profiles,'scope':'follow initializer only; current CarN physical CarID plus source model/bounds guards','runtime_qualified':False,'writable_ranges':[]}
