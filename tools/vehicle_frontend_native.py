"""Resource-scoped VehicleSelect private-target correction; retail only."""
import hashlib,struct
import patch_vehicle_registry_id26 as registry
from master_rallye.frontend_presentation import EYE,TARGET,f32,validate_profile

SHA='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
CALL=0x52a7bc
ORIGINAL=0x4895f0
NAME=0x4d0570
BOUNDS=0x4f5bc0

def make_wrapper(base,bindings):
    c=registry._CodeImage(base);emit=lambda s:c.emit(bytes.fromhex(s))
    # Source stack proven from 0052A6D0. No retained pointers or x87 work.
    emit('9c 60 8b6c2468 85ed');c.je('done')
    emit('8d4d5c');c.call(NAME);emit('85c0');c.je('done')
    for off,byte in enumerate(b'CarModel\0'):
        emit('8078');c.emit(bytes([off,byte]));c.jne('done')
    emit('8b6d50 85ed');c.je('done')
    for off,value in [(0x4c,8.),(0x50,-2.),(0x54,189.)]:
        emit('817d');c.emit(bytes([off]));c.emit(struct.pack('<f',value));c.jne('done')
    for stack,values in [(0x28,EYE),(0x2c,TARGET),(0x30,(0.,1.,0.))]:
        emit('8b4424');c.emit(bytes([stack]));emit('85c0');c.je('done')
        for off,value in enumerate(values):
            emit('8178');c.emit(bytes([off*4]));c.emit(struct.pack('<f',value));c.jne('done')
    emit('8bcd');c.call(BOUNDS);emit('85c0');c.je('done');emit('8bd8 8d4d0c');c.call(NAME);emit('85c0');c.je('done');emit('8bd0')
    for i,b in enumerate(bindings):
        nxt='next'+str(i);emit('8bf2');c.mov_eax_literal('name'+str(i));emit('8bf8 b9');name=b['model_resource'].encode()+b'\0';c.emit(struct.pack('<I',len(name)))
        c.label('char'+str(i));emit('8a06 3c5c');c.jne('slash'+str(i));emit('b02f');c.label('slash'+str(i));emit('3c41 0f82');c.rel32.append((len(c.code),len(c.code)+4,'fold'+str(i)));c.emit(b'\0'*4);emit('3c5a');c.ja('fold'+str(i));emit('0c20');c.label('fold'+str(i));emit('3a07');c.jne(nxt);emit('46 47 49');c.jne('char'+str(i))
        emit('8bf3');c.mov_eax_literal('bounds'+str(i));emit('8bf8 b90b000000 fc f3a7');c.jne(nxt)
        emit('8b44242c c74004');c.emit(struct.pack('<f',f32(TARGET[1]-b['profile']['vertical_offset_m'])));c.jump('done');c.label(nxt)
    c.label('done');emit('61 9d');c.jump(ORIGINAL)
    for i,b in enumerate(bindings):
        c.label('name'+str(i));c.emit(b['model_resource'].encode()+b'\0');c.align(4);c.label('bounds'+str(i));c.emit(bytes.fromhex(b['native_bounds_values_hex']))
    return c.build()

def append_frontend(source,image,blob,payload_va,bindings,allocation):
    if not bindings:return image,blob,None
    if len(bindings)>16 or len({b['model_resource']for b in bindings})!=len(bindings)or len({b['profile']['car_id']for b in bindings})!=len(bindings):raise ValueError('Duplicate frontend identity')
    for b in bindings:
        p=validate_profile(b['profile'])
        if b['model_resource']!='vehicles/'+p['runtime_family'].lower()+'/complete' or len(bytes.fromhex(b['native_bounds_values_hex']))!=44:raise ValueError('Invalid frontend source binding')
    if hashlib.sha256(source).hexdigest()!=SHA or len(source)!=len(image):raise ValueError('Unqualified frontend EXE')
    off=registry.va_to_file_offset(registry.parse_pe(source),CALL,5);expected=b'\xe8'+struct.pack('<i',ORIGINAL-CALL-5)
    if source[off:off+5]!=expected or image[off:off+5]!=expected:raise ValueError('Frontend call ownership/preimage mismatch')
    prefix=blob+b'\x90'*(-len(blob)%16);entry=payload_va+len(prefix);tail=make_wrapper(entry,bindings)
    if len(prefix)+len(tail)>allocation:raise ValueError('Frontend payload exceeds sealed allocation')
    replacement=b'\xe8'+struct.pack('<i',entry-CALL-5);out=bytearray(image);out[off:off+5]=replacement
    return bytes(out),prefix+tail,{'entry_va':entry,'bindings':bindings,'prefix_size':len(blob),'prefix_sha256':hashlib.sha256(blob).hexdigest(),'runtime_qualified':False,'scope':'CarModel/scene pose + unique complete resource + all44 bounds bytes; private target.y only; resource identity, not a live CarID getter','operations':[{'name':'frontend_private_target','file_offset':off,'original_bytes':expected.hex(),'replacement_bytes':replacement.hex()}]}
