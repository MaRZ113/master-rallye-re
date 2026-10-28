"""Exact-retail per-wheel model selection before original wheel registration.

No auxiliary entities or replacement interpolators are created. The original
registration installs the original steering/spin controller on the same wheel.
An existing mechanics wrapper can be a verified delegate for disjoint families.
"""
from __future__ import annotations

import copy
import hashlib
import struct

import patch_vehicle_registry_id26 as registry

RETAIL_SHA256 = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
CALL = 0x43f22c
REGISTER_WHEEL = 0x43ed00
MODEL_SETTER = 0x4f5b70


def _profiles(profiles):
    if not isinstance(profiles, list) or not 1 <= len(profiles) <= 8:
        raise ValueError('wheel resource family budget')
    families = set()
    for profile in profiles:
        if not isinstance(profile, dict) or set(profile) != {'runtime_family', 'resource_keys'}:
            raise ValueError('unsupported wheel resource native profile')
        family = profile['runtime_family']
        if (not isinstance(family, str) or not family.isascii() or not 1 <= len(family) <= 63
                or not all(c.isalnum() or c in '_-' for c in family)
                or family.casefold() in families):
            raise ValueError('invalid or duplicate wheel runtime family')
        families.add(family.casefold())
        keys = profile['resource_keys']
        prefix = f'Vehicles/{family}/'
        if not isinstance(keys, list) or len(keys) != 4:
            raise ValueError('four native-order wheel resource keys required')
        # Repeated resources on front/rear are legitimate. Each instance still
        # uses its original native wheel entity and controller.
        if any(not isinstance(key, str) or not key.isascii()
               or not key.lower().startswith(prefix.lower())
               or not 1 <= len(key[len(prefix):]) <= 64
               or not all(c.isalnum() or c in '_-' for c in key[len(prefix):])
               for key in keys):
            raise ValueError('wheel keys must be local extensionless family model names')
    return families


def _wrapper(entry_va, profiles, delegate):
    """Emit thiscall wrapper with the original three callee-popped arguments."""
    _profiles(profiles)
    code = registry._CodeImage(entry_va)
    emit = lambda value: code.emit(bytes.fromhex(value))
    code.label('entry')
    emit('55 8bec 83ec10 53 56 57 894df0')  # original this at EBP-10
    emit('8b7510 85f6'); code.je('register')
    emit('837d0c03'); code.ja('register')
    emit('8b7e50 85ff'); code.je('register')
    emit('8b470c 85c0'); code.je('register')
    emit('8945fc 8d4dfc'); code.call(0x4d0570)
    emit('85c0'); code.je('register')
    emit('8945f8')
    for index, profile in enumerate(profiles):
        literal = f"vehicles/{profile['runtime_family']}/wheel".lower()
        emit('8b55f8'); code.mov_eax_literal('family'+str(index))
        emit('89c6 b9'); code.emit(struct.pack('<I', len(literal)+1))
        code.label('guard_loop'+str(index))
        emit('8a02 8a1e 3c40'); code.ja('upper'+str(index))
        code.jump('case_done'+str(index))
        code.label('upper'+str(index)); emit('3c5a'); code.ja('case_done'+str(index))
        emit('0c20')
        code.label('case_done'+str(index)); emit('3c5c'); code.jne('slash_done'+str(index))
        emit('b02f')
        code.label('slash_done'+str(index)); emit('38d8'); code.jne('next'+str(index))
        emit('84c0'); code.je('match'+str(index))
        emit('42 46 49'); code.jne('guard_loop'+str(index))
        code.label('next'+str(index))
    code.jump('register')
    for index, _profile in enumerate(profiles):
        code.label('match'+str(index))
        for wheel in range(4):
            emit('837d0c'+f'{wheel:02x}'); code.je(f'model_{index}_{wheel}')
        code.jump('register')
        for wheel in range(4):
            code.label(f'model_{index}_{wheel}')
            code.mov_eax_literal(f'key_{index}_{wheel}')
            code.jump('set_model'+str(index))
        code.label('set_model'+str(index))
        # Exact native key construction and render-state model setter. The
        # latter disposes any old cached model at +74 and clears that cache.
        emit('50 8d4df4'); code.call(0x4d0580)
        emit('8d45f4 50 8bcf'); code.call(MODEL_SETTER)
        code.jump('register')
    code.label('register')
    # EBX may have had BL used by comparisons above: reload original this
    # from its own saved local, not a partially clobbered volatile register.
    emit('8b4df0 ff7510 ff750c ff7508'); code.call(delegate)
    emit('5f 5e 5b 8be5 5d c20c00')
    for index, profile in enumerate(profiles):
        code.label('family'+str(index))
        code.emit(f"vehicles/{profile['runtime_family']}/wheel".lower().encode()+b'\0')
        for wheel, key in enumerate(profile['resource_keys']):
            code.label(f'key_{index}_{wheel}'); code.emit(key.encode()+b'\0')
    return code.build()


def append_wheels(source, image, blob, payload_va, profiles, allocation_size, *, mechanics_report=None):
    """Append bounded selector; preserve original registration and prior payload.

    Four keys follow native +Xfront/-Xfront/+Xrear/-Xrear order. With a prior
    mechanics hook, its complete generated payload is independently rebuilt
    and compared before that exact entry is allowed as our delegate.
    """
    if not profiles:
        return image, blob, None
    families = _profiles(profiles)
    if hashlib.sha256(source).hexdigest() != RETAIL_SHA256 or len(source) != len(image):
        raise ValueError('unqualified wheel resource executable')
    pe = registry.parse_pe(source)
    offset = registry.va_to_file_offset(pe, CALL, 5)
    original = b'\xe8'+struct.pack('<i', REGISTER_WHEEL-CALL-5)
    if source[offset:offset+5] != original:
        raise ValueError('original wheel registration call preimage differs')
    delegate = REGISTER_WHEEL
    if mechanics_report is not None:
        from vehicle_mechanics_native import append_mechanics
        if not isinstance(mechanics_report, dict):
            raise ValueError('verified mechanics delegate report required')
        size = mechanics_report.get('prefix_size')
        if type(size) is not int or not 0 <= size <= len(blob):
            raise ValueError('mechanics delegate prefix range')
        prefix = blob[:size]
        if hashlib.sha256(prefix).hexdigest() != mechanics_report.get('prefix_sha256'):
            raise ValueError('mechanics delegate prefix hash')
        prior_profiles = mechanics_report.get('families')
        if not isinstance(prior_profiles, list) or not prior_profiles:
            raise ValueError('mechanics delegate families required')
        if families & {p.get('runtime_family', '').casefold() for p in prior_profiles if isinstance(p, dict)}:
            raise ValueError('wheel replacement and auxiliary mechanics families overlap')
        prior_image, prior_blob, prior_report = append_mechanics(source, source, prefix, payload_va,
                                                               prior_profiles, allocation_size)
        if (prior_report['entry_va'] != mechanics_report.get('entry_va')
                or blob[:len(prior_blob)] != prior_blob
                or image[offset:offset+5] != prior_image[offset:offset+5]):
            raise ValueError('mechanics delegate bytes/entry differ')
        delegate = prior_report['entry_va']
    elif image[offset:offset+5] != original:
        raise ValueError('wheel registration hook already occupied; verified delegate required')
    prefix = blob+b'\x90'*((-len(blob)) % 16)
    entry_va = payload_va+len(prefix)
    result = prefix+_wrapper(entry_va, profiles, delegate)
    if len(result) > allocation_size:
        raise ValueError('wheel resource extension exceeds existing allocation')
    replacement = b'\xe8'+struct.pack('<i', entry_va-CALL-5)
    output = bytearray(image); output[offset:offset+5] = replacement
    return bytes(output), result, {
        'entry_va': entry_va, 'source_exe_sha256': RETAIL_SHA256,
        'prefix_size': len(blob), 'prefix_sha256': hashlib.sha256(blob).hexdigest(),
        'families': copy.deepcopy(profiles), 'delegate_registration_va': delegate,
        'native_wheel_register_va': REGISTER_WHEEL, 'model_setter_va': MODEL_SETTER,
        'mechanics_delegate_verified': mechanics_report is not None,
        'operations': [{'name': 'per_wheel_model_before_original_registration',
                        'file_offset': offset, 'original_bytes': original.hex(),
                        'displaced_bytes': image[offset:offset+5].hex(),
                        'replacement_bytes': replacement.hex()}],
        'runtime_qualified': False,
        'ownership': 'same native wheel entity, controller, spin interpolator and native destruction',
        'auxiliary_entities_added': 0,
        'boundary': 'exact native model selector; controlled CPU evidence does not establish D3D8 resource loading/gameplay',
    }
