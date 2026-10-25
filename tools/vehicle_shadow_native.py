"""Append an exact retail, model-scoped shadow-only bounds adapter."""
import hashlib
import struct
import patch_vehicle_registry_id26 as registry
from master_rallye.addon_sdk.vehicle_shadow import validate_profile

RETAIL_SHA256 = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
CALL = 0x58848a
NATIVE = 0x4f5bc0
RESOURCE_NAME = 0x4d0570


def make_wrapper(base_va, bounds):
    code = registry._CodeImage(base_va)
    emit = lambda s: code.emit(bytes.fromhex(s))
    code.label('entry')
    # ECX = model node. Native call first and exactly once; keep its returned
    # bounds pointer in EBX, and the original node in EBP. No FPU work is added.
    emit('55 53 56 57 8be9')
    code.call(NATIVE)
    emit('9c 50 51 52 8bd8 85c0'); code.je('done')
    emit('8d4d0c'); code.call(RESOURCE_NAME)
    emit('85c0'); code.je('done')
    emit('8bf0')
    for i, bound in enumerate(bounds):
        label = 'next' + str(i)
        emit('56')
        code.mov_eax_literal('name' + str(i)); emit('8bf8 b9')
        name = bound['model_resource'].encode('ascii') + b'\0'
        code.emit(struct.pack('<I', len(name)))
        code.label('character' + str(i))
        # Full ASCII key, including NUL. Normalize only case and path slashes.
        emit('8a06 3c5c'); code.jne('slash' + str(i)); emit('b02f')
        code.label('slash' + str(i)); emit('3c41')
        code.emit(bytes.fromhex('0f82')); code.rel32.append((len(code.code), len(code.code) + 4, 'folded' + str(i))); code.emit(b'\0' * 4)
        emit('3c5a'); code.ja('folded' + str(i)); emit('0c20')
        code.label('folded' + str(i)); emit('3a07'); code.jne('mismatch' + str(i))
        emit('46 47 49'); code.jne('character' + str(i))
        emit('5e 8bf3')
        code.mov_eax_literal('original' + str(i)); emit('8bf8 b90b000000 fc f3a7'); code.jne(label)
        code.mov_eax_literal('replacement' + str(i))
        # Saved native EAX is replaced; original native flags are restored.
        emit('89442408'); code.jump('done')
        code.label('mismatch' + str(i)); emit('5e')
        code.label(label)
        # Original name pointer must survive a bounds mismatch too.
        if i + 1 < len(bounds):
            emit('8d4d0c'); code.call(RESOURCE_NAME); emit('8bf0')
    code.label('done'); emit('5a 59 58 9d 5f 5e 5b 5d c3')
    for i, bound in enumerate(bounds):
        code.label('name' + str(i)); code.emit(bound['model_resource'].encode('ascii') + b'\0'); code.align(4)
        code.label('original' + str(i)); code.emit(bytes.fromhex(bound['native_bounds_values_hex']))
        code.label('replacement' + str(i)); code.emit(bytes.fromhex(bound['shadow_bounds_hex']))
    return code.build(), {key: base_va + value for key, value in code.labels.items()}


def append_shadow(source, image, blob, payload_va, profiles, allocation_size):
    """profiles are bind_profile() results, prepared against sealed emitted car.dx."""
    if not profiles:
        return image, blob, None
    if len(profiles) > 16 or len({p['model_resource'] for p in profiles}) != len(profiles):
        raise ValueError('duplicate or excessive shadow profiles')
    for p in profiles:
        validate_profile(p['profile'])
        if len(bytes.fromhex(p['native_bounds_values_hex'])) != 44 or len(bytes.fromhex(p['shadow_bounds_hex'])) != 44:
            raise ValueError('shadow native bounds binding size mismatch')
        if p['model_resource'] != f'vehicles/{p["profile"]["runtime_family"].lower()}/car':
            raise ValueError('shadow resource binding mismatch')
    if hashlib.sha256(source).hexdigest() != RETAIL_SHA256 or len(image) != len(source):
        raise ValueError('unqualified shadow executable')
    pe = registry.parse_pe(source)
    off = registry.va_to_file_offset(pe, CALL, 5)
    expected = b'\xe8' + struct.pack('<i', NATIVE - CALL - 5)
    pre = registry.va_to_file_offset(pe, CALL - 2, 2)
    if source[pre:pre + 2] != bytes.fromhex('8bce') or source[off:off + 5] != expected or image[off:off + 5] != expected:
        raise ValueError('shadow getter call preimage changed')
    prefix = blob + b'\x90' * (-len(blob) % 16)
    entry = payload_va + len(prefix)
    tail, entries = make_wrapper(entry, profiles)
    combined = prefix + tail
    if len(combined) > allocation_size:
        raise ValueError('shadow adapter exceeds existing sealed allocation')
    replacement = b'\xe8' + struct.pack('<i', entry - CALL - 5)
    result = bytearray(image); result[off:off + 5] = replacement
    return bytes(result), combined, {'entry_va': entry, 'entries': entries, 'call_va': CALL, 'native_getter_va': NATIVE,
        'prefix_size': len(blob), 'prefix_sha256': hashlib.sha256(blob).hexdigest(), 'size': len(tail),
        'bindings': profiles, 'identity': 'sealed source SHA256 plus native canonical resource key and all 44 native-loaded bounds bytes including radius squared',
        'scope': 'only 00588200 shadow consumer; native getter called once; source model/collision/texture untouched',
        'operations': [{'name': 'source_scoped_shadow_bounds', 'file_offset': off, 'original_bytes': expected.hex(), 'replacement_bytes': replacement.hex()}],
        'runtime_qualified': False}
