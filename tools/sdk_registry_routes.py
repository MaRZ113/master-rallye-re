"""Append SDK record presentation/audio/AI routes without owning registry storage.

The caller composes these operations after the configurable capacity core.
The accepted SDK33 helpers remain the exact fallback; no constructor, mapping,
count, lifetime or resource-bank operation belongs to this layer.
"""
from __future__ import annotations
import struct
import sdk_capacity_native as native
import sdk_addon_ai as ai

BASE = 0x10000000


def _parent_bytes(image, pe, extension, address, size):
    if address >= BASE:
        offset = address - BASE
        if not 0 <= offset <= len(extension) - size:
            raise ValueError('Parent helper is outside the supplied extension')
        return extension[offset:offset + size]
    offset = native.registry.va_to_file_offset(pe, address, size)
    return image[offset:offset + size]


def _pool(rows, cls, mode):
    shared = cls == 'T3' and mode in ('rallye_cup', 'invitation')
    modes = ('rallye_cup', 'invitation') if shared else (mode,)
    return sorted((r for r in rows if r['vehicle_class'] == cls and
                   any(r['ai_eligibility'][m]['enabled'] for m in modes)),
                  key=lambda r: r['physical_id'])


def append_routes(source, image, extension, parent_plan, rows, *, allocation_size):
    """Return (virtual_image, combined_extension, operation_report).

    ``parent_plan`` is the original accepted plan, not a plan already extended
    with ``rows``. The input extension may already include the capacity core.
    All comparisons are imm32. Bounds/identity admission belongs to the profile.
    """
    rows = sorted(rows, key=lambda r: r['physical_id'])
    if not rows:
        return image, extension, {'operations': [], 'entries': {}, 'ai_pools': [], 'runtime_qualified': False}
    native.validate_rows(rows)
    parent_rows = parent_plan['addons'] if isinstance(parent_plan, dict) else parent_plan
    parent_ids = {r['physical_id'] for r in parent_rows}
    if any(type(r['physical_id']) is not int or not 33 <= r['physical_id'] < 0x7fffffff
           or r['physical_id'] in parent_ids for r in rows):
        raise ValueError('Additional routes require unique appended signed-32 physical IDs')
    for r in rows:
        ai.validate_eligibility(r['vehicle_class'], r['ai_eligibility'])
    pe = native.registry.parse_pe(source)
    padding = bytes((-len(extension)) % 16)
    va = BASE + len(extension) + len(padding)
    code = native.registry._CodeImage(va)
    profiles = [native._profile(r) for r in rows]
    hooks = []
    bridges = [(0x481a0e, 'edi', 'manufacturer', 0x481a18),
               (0x481a4b, 'edi', 'model', 0x481a55),
               *[(v, 'eax', 'combined', v + 8) for v in native.registry.QUICKRACE_LOCALIZATION_CALLS],
               *[(v, 'esi', 'manufacturer' if group == 0x33 else 'model', resume)
                 for v, group, label, string, resume in native.registry.RACE_OPTIONS_LOCALIZATION_CALLS],
               *[(hook, 'eax', 'combined', resume) for hook, slot, label, group, call, resume
                 in native.registry.RACE_DETAILS_LOCALIZATION_CALLS],
               (0x44fa29, 'edi', 'combined', 0x44fa33)]
    for j, (hook, reg, field, resume) in enumerate(bridges):
        label = f'display{j}'
        code.label(label)
        for n, p in enumerate(profiles):
            native.i0._comparison_bytes(code, reg, p.slot_id)
            code.jne(f'd{j}_{n}')
            code.mov_eax_literal(f'{field}{n}')
            code.jump(resume)
            code.label(f'd{j}_{n}')
        code.jump(native.branch_target(image, pe, hook, 0xe9))
        hooks.append((hook, label, 0xe9, 5))
    code.label('results')
    code.emit(native.i0.natural.results_name_stub_bytes()[:8])
    for n, p in enumerate(profiles):
        native.i0._comparison_bytes(code, 'ecx', p.slot_id)
        code.jne(f'res{n}')
        code.mov_eax_literal(f'results{n}')
        code.jump(native.i0.natural.RESULTS_AFTER_LOOKUP_VA)
        code.label(f'res{n}')
    code.jump(native.branch_target(image, pe, native.i0.natural.RESULTS_NAME_HOOK_VA, 0xe9))
    code.label('unlock')
    for p in profiles:
        code.emit(b'\x81\x79\x04' + struct.pack('<I', p.slot_id))
        code.je('unlock_new')
    code.jump(native.branch_target(image, pe, native.i0.UNLOCK_CALL_VA, 0xe8))
    code.label('unlock_new')
    code.emit(bytes.fromhex('5183ec08c7042400000000c74424040a0000008d0c24'))
    code.call(0x45a150)
    code.emit(bytes.fromhex('83c40859c3'))
    code.label('locked')
    for p in profiles:
        native.i0._comparison_bytes(code, 'eax', p.slot_id - 3)
        code.je('locked_new')
    code.jump(native.branch_target(image, pe, native.i0.LOCKED_REASON_HOOK_VA, 0xe9))
    code.label('locked_new')
    code.emit(bytes.fromhex('bb0c000000'))
    code.jump(0x481b49)
    native.emit_audio_lookup(code, rows, native.branch_target(image, pe, native.i0.AUDIO_PROFILE_CALL_VA, 0xe8))
    pools = []
    t2 = [('quick_race', native.i0.QUICKRACE_T2_HOOK_VA, native.i0.QUICKRACE_T2_REENTRY_VA, native.i0.QUICKRACE_T2_EXIT_VA),
          ('rallye_cup', native.i0.CUP_T2_HOOK_VA, native.i0.CUP_T2_REENTRY_VA, native.i0.CUP_T2_EXIT_VA),
          ('master_rallye', native.i0.MASTER_T2_HOOK_VA, native.i0.MASTER_T2_REENTRY_VA, native.i0.MASTER_T2_EXIT_VA)]
    for cls, sites in [('T1', ai.T1), ('T2', t2), ('T3', ai.T3)]:
        for site in sites:
            mode, hook, reentry, exit_ = site[:4]
            selected = _pool(rows, cls, mode)
            if not selected:
                continue
            parents = _pool(parent_rows, cls, mode)
            terminal = parents[-1]['physical_id'] + 1 if parents else {'T1': 7, 'T2': 14, 'T3': 21}[cls]
            target = native.branch_target(image, pe, hook, 0xe9)
            label = f'pool_{cls}_{mode}'
            code.label(label)
            if cls == 'T3':
                # Parent displaced the whole INC/LEA/CMP/JL sequence. Perform
                # INC once here; the fallback resumes immediately after INC.
                expected = bytes.fromhex(site[4])[:7]
                if _parent_bytes(image, pe, extension, target, 7) != expected:
                    raise ValueError('T3 parent increment/derived-counter owner changed')
                code.emit(b'\x46')
                target += 1
            for k, row in enumerate(selected):
                prior = terminal if k == 0 else selected[k - 1]['physical_id'] + 1
                native.i0._comparison_bytes(code, 'esi', prior)
                code.je(f'{label}_select{k}')
            native.i0._comparison_bytes(code, 'esi', selected[-1]['physical_id'] + 1)
            code.je(label + '_done')
            code.jump(target)
            for k, row in enumerate(selected):
                code.label(f'{label}_select{k}')
                if cls == 'T3' and mode in ('rallye_cup', 'invitation'):
                    code.emit(b'\x9c\x60')
                    code.call(0x4ada50)
                    code.emit(b'\x8b\xc8')
                    code.call(0x4abe90)
                    for key, value in [('rallye_cup', 6), ('invitation', 8)]:
                        if row['ai_eligibility'][key]['enabled']:
                            code.emit(b'\x83\xf8' + bytes([value]))
                            code.je(f'{label}_allow{k}')
                    code.emit(b'\x61\x9d')
                    code.jump(f'{label}_select{k + 1}' if k + 1 < len(selected) else label + '_done')
                    code.label(f'{label}_allow{k}')
                    code.emit(b'\x61\x9d')
                code.emit(b'\xbe' + struct.pack('<I', row['physical_id']))
                code.jump(reentry)
            code.label(label + '_done')
            sentinel = {'T1': 7, 'T2': 14, 'T3': 21}[cls]
            code.emit(b'\xbe' + struct.pack('<I', sentinel))
            if cls == 'T3':
                code.emit(bytes.fromhex('8d56f2' if mode in ('quick_race', 'invitation') else '8d4ef2'))
            code.jump(exit_)
            hooks.append((hook, label, 0xe9, 9 if cls == 'T3' else 5))
            pools.append(dict(vehicle_class=cls, mode=mode, parent_terminal=terminal,
                              physical_ids=[r['physical_id'] for r in selected],
                              reentry_va=reentry, exit_va=exit_, hook_va=hook))
    for n, (p, r) in enumerate(zip(profiles, rows)):
        for field, text in [('manufacturer', p.display_manufacturer), ('model', p.display_model),
                            ('combined', p.display_quickrace), ('results', r['results']['display_name'])]:
            code.label(f'{field}{n}')
            code.emit(text.encode('ascii') + b'\0')
    hooks += [(native.i0.natural.RESULTS_NAME_HOOK_VA, 'results', 0xe9, 5),
              (native.i0.UNLOCK_CALL_VA, 'unlock', 0xe8, 5),
              (native.i0.LOCKED_REASON_HOOK_VA, 'locked', 0xe9, 5),
              (native.i0.AUDIO_PROFILE_CALL_VA, 'audio', 0xe8, 5)]
    blob = code.build()
    combined = extension + padding + blob
    if len(combined) > allocation_size:
        raise ValueError('Registry route helpers exceed the configured allocation budget')
    entries = {k: va + offset for k, offset in code.labels.items()}
    operations = []
    for hook, label, opcode, size in hooks:
        offset = native.registry.va_to_file_offset(pe, hook, size)
        original = image[offset:offset + size]
        replacement = native.i0._rel32(hook, entries[label], opcode) + bytes([0x90]) * (size - 5)
        operations.append(native.i0._operation('registry_route_' + label, 'vcap2-routes', offset,
                          original, replacement, 'Extend accepted SDK33 route; preserve its fallback', va=hook))
    result = native.i0._apply_layer(image, operations)
    return result, combined, dict(operations=operations, entries=entries, ai_pools=pools,
                                 payload_va=va, payload_size=len(blob), runtime_qualified=False,
                                 abi='SDK33 native presentation/audio/AI continuations; imm32 IDs')
