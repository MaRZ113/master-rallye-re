"""Optional exact-retail unsprung scene instances; original EXE remains immutable.

The wrapper calls stock wheel registration once, then adds explicitly profiled
visual instances through the same scene allocator/name/model/controller path.
Physics publication, wheel registration and wheel spin remain native.
"""
import hashlib
import struct

import patch_vehicle_registry_id26 as registry

RETAIL_SHA256 = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
CALL = 0x43f22c
REGISTER_WHEEL = 0x43ed00


def append_mechanics(source, image, blob, payload_va, profiles, allocation_size):
    """Append an opt-in resource binding after the qualified native wheel call.

    Profile: runtime_family and exactly four local model resource keys, in
    native wheel order. No source/target physics parameters are accepted here.
    """
    if not profiles:
        return image, blob, None
    if len(profiles) > 8:
        raise ValueError('mechanical attachment family budget')
    families = set()
    for p in profiles:
        if set(p) != {'runtime_family', 'resource_keys'}:
            raise ValueError('unsupported mechanical attachment native profile')
        family = p['runtime_family']
        if not isinstance(family, str) or not family.isascii() or not 1<=len(family)<=63 or not all(c.isalnum() or c in '_-' for c in family) or family.casefold() in families:
            raise ValueError('invalid or duplicate mechanical runtime family')
        families.add(family.casefold())
        keys = p['resource_keys']
        if not isinstance(keys, list) or len(keys) != 4 or len(set(keys)) != 4:
            raise ValueError('four distinct mechanical model keys are required')
        prefix = f'Vehicles/{family}/'
        if any(not isinstance(k, str) or not k.isascii() or not k.lower().startswith(prefix.lower()) or not 1<=len(k[len(prefix):])<=64 or not all(c.isalnum() or c in '_-' for c in k[len(prefix):]) for k in keys):
            raise ValueError('mechanical keys must be local extensionless family model names')
    if hashlib.sha256(source).hexdigest() != RETAIL_SHA256 or len(source) != len(image):
        raise ValueError('unqualified mechanical attachment executable')
    pe = registry.parse_pe(source)
    off = registry.va_to_file_offset(pe, CALL, 5)
    expected = b'\xe8' + struct.pack('<i', REGISTER_WHEEL - CALL - 5)
    if source[off:off+5] != expected or image[off:off+5] != expected:
        raise ValueError('native wheel registration call preimage differs')
    prefix = blob + b'\x90' * ((-len(blob)) % 16)
    c = registry._CodeImage(payload_va + len(prefix))
    emit = lambda value: c.emit(bytes.fromhex(value))
    c.label('entry')
    emit('55 8bec 81ec20010000 53 56 57')
    # Original this and three stack args; original callee pops 12 bytes.
    emit('ff7510 ff750c ff7508')
    c.call(REGISTER_WHEEL)
    emit('8945fc 9c 8f45f8')  # preserve original EAX and resulting flags
    emit('8b7510 85f6'); c.je('done')
    emit('837d0c03'); c.ja('done')
    emit('8b4650 85c0'); c.je('done')
    emit('8b400c 8945f4')
    emit('8d4df4'); c.call(0x4d0570)
    emit('85c0'); c.je('done')
    emit('8945d8')
    for i, p in enumerate(profiles):
        literal=f"vehicles/{p['runtime_family']}/wheel".lower()
        emit('8b55d8');c.mov_eax_literal('family'+str(i));emit('89c7 b9');c.emit(struct.pack('<I',len(literal)+1))
        c.label('guard_loop'+str(i))
        emit('8a02 8a1f 3c40');c.ja('guard_upper'+str(i));c.jump('guard_case_done'+str(i))
        c.label('guard_upper'+str(i));emit('3c5a');c.ja('guard_case_done'+str(i));emit('0c20')
        c.label('guard_case_done'+str(i));emit('3c5c');c.jne('guard_slash_done'+str(i));emit('b02f')
        c.label('guard_slash_done'+str(i));emit('38d8');c.jne('guard_next'+str(i))
        emit('84c0');c.je('family_match'+str(i))
        emit('42 47 49');c.jne('guard_loop'+str(i))
        c.label('guard_next'+str(i))
    c.jump('done')
    for i, p in enumerate(profiles):
        c.label('family_match'+str(i))
        # Keep the actual wheel entity and source resource guard independent
        # from participant CarID numbering. Its scene name is already native.
        emit('8d4e5c'); c.call(0x4d0570)
        emit('89c2 8dbdf0feffff b960000000')
        c.label('name_copy'+str(i))
        emit('8a02 42 84c0'); c.je('name_suffix'+str(i))
        emit('8807 47 49'); c.jne('name_copy'+str(i))
        c.jump('done')
        c.label('name_suffix'+str(i))
        c.mov_eax_literal('suffix'); emit('89c6 b90e000000 fc f3a4 8b7510')
        emit('8d85f0feffff 50 8d4dec'); c.call(0x4d0580)
        # Duplicate native names cannot allocate another instance.
        emit('8d45ec 50'); c.call(0x4f6310)
        emit('8bc8'); c.call(0x4f5eb0)
        emit('85c0'); c.jne('done')
        emit('6a78'); c.call(0x5c1cb4); emit('83c404 85c0'); c.je('done')
        emit('8bc8'); c.call(0x4f5670)
        emit('8bf8 8b4750 85c0'); c.je('cleanup')
        emit('8d45ec 50 8bcf'); c.call(0x4f59f0)
        for wheel in range(4):
            emit('837d0c'+f'{wheel:02x}'); c.je(f'resource_{i}_{wheel}')
        c.jump('cleanup')
        for wheel in range(4):
            c.label(f'resource_{i}_{wheel}')
            c.mov_eax_literal(f'model_{i}_{wheel}')
            c.jump('set_model'+str(i))
        c.label('set_model'+str(i))
        emit('50 8d4de8'); c.call(0x4d0580)
        emit('8d45e8 50 8b4f50'); c.call(0x4f5b70)
        emit('6a10'); c.call(0x5c1cb4); emit('83c404 85c0'); c.je('cleanup')
        emit('8bc8'); c.call(0x4f5290)
        emit('8945e4 50 6a00 8bcf'); c.call(0x4f5950)
        # Key constructor is the same helper used by the original wheel
        # publisher: Physics/<actual wheel scene name>/Transform.
        emit('56 8d45e0 50'); c.call(0x4f54c0); emit('83c408')
        emit('8b4de4 8b45e0 89410c')
        # Native wheel-interpolator allocation/constructor size is qualified
        # at43ED8E..43EDB9. Select its native base dispatch: generic pose
        # interpolation5090F0, without the spin extension4485E0. The native
        # deleting base destructor4485C0 frees this owned allocation.
        emit('6a1c'); c.call(0x5c1cb4); emit('83c404 85c0'); c.je('cleanup')
        emit('6a00 8bc8'); c.call(0x448570)
        emit('c70078016900 50 8b4f50'); c.call(0x4f5ce0)
        emit('c6476c02')
        c.jump('done')
    c.label('cleanup')
    emit('8bcf'); c.call(0x4f5780)
    emit('57'); c.call(0x5b4c00); emit('83c404')
    c.label('done')
    emit('ff75f8 9d 8b45fc 5f 5e 5b 8be5 5d c20c00')
    c.label('suffix'); c.emit(b'/SDKMechanics\0')
    for i, p in enumerate(profiles):
        c.label('family'+str(i)); c.emit(f"vehicles/{p['runtime_family']}/wheel".lower().encode()+b'\0')
        for wheel, key in enumerate(p['resource_keys']):
            c.label(f'model_{i}_{wheel}'); c.emit(key.encode()+b'\0')
    tail = c.build()
    result = prefix + tail
    if len(result) > allocation_size:
        raise ValueError('mechanics extension exceeds the existing allocation')
    replacement = b'\xe8' + struct.pack('<i', c.base_va-CALL-5)
    output = bytearray(image)
    output[off:off+5] = replacement
    report = {'entry_va': c.base_va, 'source_exe_sha256': RETAIL_SHA256,
              'prefix_size': len(blob), 'prefix_sha256': hashlib.sha256(blob).hexdigest(),
              'families': profiles, 'native_wheel_register_va': REGISTER_WHEEL,
              'operations': [{'name': 'optional_unsprung_mechanics_after_native_wheel_registration',
                              'file_offset': off, 'original_bytes': expected.hex(),
                              'replacement_bytes': replacement.hex()}],
              'runtime_qualified': False,
              'ownership': 'native scene manager/entity/controller/interpolator destructors; independent unsprung visuals',
              'interpolation': 'native base vtable690178 / evaluator5090F0; source wheel spin4485E0 excluded',
              'boundary': 'prototype requires controlled native lifecycle replay and human repeated-race qualification'}
    return bytes(output), result, report
