"""Replay the shadow adapter and original footprint arithmetic in isolated x86.

Most cases stub native bounds/name services; five replay original getters and
the interner with only backing model-cache lookup stubbed. Terrain selection,
the graphics driver and live rendering are outside this CPU experiment.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools')]
from master_rallye.addon_sdk.vehicle_shadow import bind_profile
import vehicle_shadow_native as native
import j2_frontend_reentry as j2


def load_bounds(exe, serialized):
    """Execute original 00553CA4..00553D9A after successful allocation.

    Only the stream virtual scalar reader is stubbed; original x87 layout,
    radius square and all destination writes execute from the immutable EXE.
    """
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as AX, UC_X86_REG_ECX as CX, UC_X86_REG_EDI as DI, UC_X86_REG_ESI as SI, UC_X86_REG_ESP as SP, UC_X86_REG_EIP as IP
    if hashlib.sha256(exe).hexdigest() != native.RETAIL_SHA256: raise ValueError('unqualified executable')
    u = Uc(UC_ARCH_X86, UC_MODE_32); u.mem_map(0x400000, 0x400000); u.mem_map(0x2000000, 0x20000)
    _, sections = j2.addon_runtime._pe_sections(exe)
    for section in sections:
        u.mem_write(0x400000 + section['rva'], exe[section['raw_offset']:section['raw_offset'] + section['raw_size']])
    put = lambda address, *v: u.mem_write(address, struct.pack('<' + 'I' * len(v), *v))
    reader, table, output, parser, resource, stack, stop = [0x2000000 + n for n in (0, 0x100, 0x200, 0x300, 0x400, 0x10000, 0x500)]
    put(parser, reader, resource); put(reader, table); put(table + 0x3c, stop)
    # Original epilogue restores 4 registers, local frame then return.
    put(stack + 16 + 0x3c, stop + 1)
    remaining = [serialized[i:i + 4] for i in range(4, len(serialized), 4)]
    def hook(uc, address, size, data):
        if address != stop: return
        sp = uc.reg_read(SP); dest = struct.unpack('<I', uc.mem_read(sp + 4, 4))[0]
        if not remaining: raise ValueError('bounds loader overread')
        uc.mem_write(dest, remaining.pop(0)); ret = struct.unpack('<I', uc.mem_read(sp, 4))[0]
        uc.reg_write(SP, sp + 8); uc.reg_write(IP, ret)
    u.hook_add(UC_HOOK_CODE, hook)
    u.mem_write(stop + 0x10, bytes.fromhex('dbe3')); u.emu_start(stop + 0x10, stop + 0x12)
    u.reg_write(SP, stack); u.reg_write(SI, parser); u.reg_write(DI, output)
    u.emu_start(0x553ca4, stop + 1, count=1000)
    if remaining or u.reg_read(IP) != stop + 1: raise ValueError('original bounds loader incomplete')
    return bytes(u.mem_read(output, 44))


def execute(exe, bounds, *, name, values, adapted=True, null_bounds=False, native_services=False):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as AX, UC_X86_REG_ECX as CX, UC_X86_REG_EDX as DX, UC_X86_REG_EBX as BX, UC_X86_REG_ESI as SI, UC_X86_REG_EDI as DI, UC_X86_REG_EBP as BP, UC_X86_REG_ESP as SP, UC_X86_REG_EIP as IP, UC_X86_REG_EFLAGS as FL
    if hashlib.sha256(exe).hexdigest() != native.RETAIL_SHA256:
        raise ValueError('unqualified executable')
    u = Uc(UC_ARCH_X86, UC_MODE_32); u.mem_map(0x400000, 0x400000)
    _, sections = j2.addon_runtime._pe_sections(exe)
    for s in sections:
        u.mem_write(0x400000 + s['rva'], exe[s['raw_offset']:s['raw_offset'] + s['raw_size']])
    u.mem_map(0x10000000, 0x20000); u.mem_map(0x2000000, 0x20000)
    blob, entries = native.make_wrapper(0x10000000, bounds); u.mem_write(0x10000000, blob)
    node, bbox, string, stack, stop = 0x2000000, 0x2001000, 0x2002000, 0x2010000, 0x2003000
    # Exact 44-byte native layout, produced by 00553C80 (no vtable header).
    u.mem_write(bbox, values); u.mem_write(string, name.encode('ascii') + b'\0')
    u.mem_write(stack, struct.pack('<I', stop)); u.mem_write(stop, b'\x90')
    native_calls, name_calls, snapshots = [], [], []
    native_return = []
    native_flags = 0x246
    if native_services:
        put = lambda address, *v: u.mem_write(address, struct.pack('<' + 'I' * len(v), *v))
        # Existing singleton state, matching original 004D3920/004D44F0.
        put(0x6f93d0, 0x2004500); put(0x2004500, 0x2004600); put(0x2004600, 0x6922c8)
        put(0x6f9cf0, 0x2004300); put(0x2004304, 0x2004400)
        put(0x2004708, 0 if null_bounds else bbox)
        put(0x6f93d4, 0x2004000); put(0x2004004, 0x2004100)
        put(0x2004104, 0x2004200, 0x2004208); put(0x2004200, 0, string)
        put(node + 0xc, 1)
    def hook(uc, address, _size, _data):
        if native_return and address == native_return[0]:
            snapshots.append((uc.reg_read(CX), uc.reg_read(DX), uc.reg_read(FL)))
        if address == native.NATIVE:
            native_calls.append(uc.reg_read(CX))
            if native_services:
                native_return.append(struct.unpack('<I', uc.mem_read(uc.reg_read(SP), 4))[0])
                return
            uc.reg_write(AX, 0 if null_bounds else bbox); uc.reg_write(CX, 0x12345678); uc.reg_write(DX, 0x23456789); uc.reg_write(FL, native_flags)
            sp = uc.reg_read(SP); ret = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            uc.reg_write(SP, sp + 4); uc.reg_write(IP, ret)
        elif address == native.RESOURCE_NAME:
            name_calls.append(uc.reg_read(CX))
            if native_services: return
            uc.reg_write(AX, string); uc.reg_write(CX, 0x77777777); uc.reg_write(DX, 0x88888888); uc.reg_write(FL, 0x202)
            sp = uc.reg_read(SP); ret = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            uc.reg_write(SP, sp + 4); uc.reg_write(IP, ret)
        elif native_services and address == 0x54b320:
            sp = uc.reg_read(SP)
            if uc.reg_read(CX) != 0x2004400 or struct.unpack('<I', uc.mem_read(sp + 4, 4))[0] != node + 0xc:
                raise ValueError('original getter resolved wrong model resource key')
            uc.reg_write(AX, 0x2004700); uc.reg_write(CX, 0x12345678); uc.reg_write(DX, 0x23456789)
            ret = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            uc.reg_write(SP, sp + 8); uc.reg_write(IP, ret)
    u.hook_add(UC_HOOK_CODE, hook)
    saved = {BX: 0x3456789a, SI: 0x456789ab, DI: 0x56789abc, BP: 0x6789abcd}
    for reg, value in saved.items(): u.reg_write(reg, value)
    u.reg_write(SP, stack); u.reg_write(CX, node); u.reg_write(FL, 0x202)
    u.emu_start(0x10000000 if adapted else native.NATIVE, stop, count=100000)
    if u.reg_read(IP) != stop or u.reg_read(SP) != stack + 4:
        raise ValueError('shadow wrapper did not return with original ABI')
    if any(u.reg_read(reg) != value for reg, value in saved.items()):
        raise ValueError('shadow wrapper changed callee-saved registers')
    wanted = snapshots[0] if snapshots else (0x12345678, 0x23456789, native_flags)
    if native_services and not adapted: wanted = (u.reg_read(CX), u.reg_read(DX), u.reg_read(FL))
    if (u.reg_read(CX), u.reg_read(DX), u.reg_read(FL)) != wanted:
        raise ValueError('shadow wrapper failed to preserve native volatile registers/flags')
    if native_calls != [node] or any(p != node + 0xc for p in name_calls):
        raise ValueError('shadow wrapper used incorrect native this or called getter more than once')
    pointer = u.reg_read(AX)
    result = {'adapted': pointer != bbox and pointer != 0, 'native_calls': len(native_calls), 'name_calls': len(name_calls), 'returned_null': pointer == 0,
        'native_bounds_unchanged': bytes(u.mem_read(bbox, 44)) == values, 'native_services_replayed': native_services}
    if pointer:
        # Execute the unchanged original x87 min/max/center segment, ending
        # before the matrix-transform call. Initialize the FPU explicitly.
        u.mem_write(0x2003100, bytes.fromhex('dbe3')); u.emu_start(0x2003100, 0x2003102, count=1)
        u.reg_write(AX, pointer); u.reg_write(SP, stack)
        u.emu_start(0x58848f, 0x588515, count=100)
        read = lambda off: struct.unpack('<f', u.mem_read(stack + off, 4))[0]
        result['quad_size_xz_m'] = [read(0x20), read(0x1c)]
        result['quad_center_xyz_m'] = [read(0x4c), read(0x50), read(0x54)]
    return result


def validate(exe, bound):
    values = bytes.fromhex(bound['native_bounds_values_hex']); name = bound['model_resource']
    # Recover the serialized input from the qualified runtime layout.
    serialized = struct.pack('<I', 1339) + values[:16] + values[20:]
    loaded = load_bounds(exe, serialized)
    if loaded != values: raise ValueError('actual native loader disagrees with binding')
    rows = []
    def check(case, records, resource, native_values, wanted, **kwargs):
        r = execute(exe, records, name=resource, values=native_values, **kwargs)
        if r['adapted'] != wanted or not r['native_bounds_unchanged']:
            raise ValueError('shadow admission mismatch: ' + case)
        rows.append({'case': case, **r})
        return r
    base = check('original', [bound], name, values, False, adapted=False)
    fixed = check('source model', [bound], name, values, True)
    for got, target in zip(fixed['quad_size_xz_m'], bound['generated_quad_size_xz_m']):
        if abs(got - target) > 2e-6: raise ValueError('original arithmetic disagrees with profile quad size')
    for got, target in zip((fixed['quad_center_xyz_m'][0], fixed['quad_center_xyz_m'][2]), bound['generated_quad_center_xz_m']):
        if abs(got - target) > 2e-6: raise ValueError('original arithmetic disagrees with profile center')
    check('case and slash normalization', [bound], name.upper().replace('/', '\\'), values, True)
    check('stock passthrough', [bound], 'vehicles/navara/car', values, False)
    check('complete passthrough', [bound], name[:-3] + 'complete', values, False)
    check('suffix rejection', [bound], name + 'suffix', values, False)
    check('null native result', [bound], name, values, False, null_bounds=True)
    for i in range(44):
        wrong = bytearray(values); wrong[i] ^= 1
        check('bounds byte ' + str(i), [bound], name, bytes(wrong), False)
    # First record has matching name but mismatched bounds; second must still
    # compare the original name pointer. Third exercises a name mismatch first.
    wrong = {**bound, 'native_bounds_values_hex': (bytes([values[0] ^ 1]) + values[1:]).hex()}
    check('multiple bounds mismatch then match', [wrong, bound], name, values, True)
    wrong_name = {**bound, 'model_resource': 'vehicles/other/car'}
    check('multiple name mismatch then match', [wrong_name, bound], name, values, True)
    check('original native getters and interning', [bound], name, values, True, native_services=True)
    check('original native getters normalized path', [bound], name.upper().replace('/', '\\'), values, True, native_services=True)
    check('original native getters stock passthrough', [bound], 'vehicles/navara/car', values, False, native_services=True)
    wrong = bytearray(values); wrong[20] ^= 1
    check('original native getters changed bounds', [bound], name, bytes(wrong), False, native_services=True)
    check('original native getters null result', [bound], name, values, False, native_services=True, null_bounds=True)
    return {'status': 'PASS_ISOLATED_SHADOW_WRAPPER_AND_ORIGINAL_ARITHMETIC', 'cases': len(rows), 'rows': rows, 'original_bounds_loader_replayed': True,
        'runtime_qualified': False, 'boundary': 'original bounds-loader writes/x87 with scalar stream reads stubbed; exact original x87 footprint instructions and getters/interner in five cases; backing model cache lookup stubbed, no terrain, D3D or live race'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('exe', 'profile', 'model', 'texture', 'output'): p.add_argument('--' + flag, type=Path, required=True)
    a = p.parse_args(); b = bind_profile(json.loads(a.profile.read_text()), a.model.read_bytes(), a.texture.read_bytes())
    result = validate(a.exe.read_bytes(), b); a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'cases', 'runtime_qualified')}))
