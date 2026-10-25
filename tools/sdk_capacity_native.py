"""Bounded native roster extension over a verified J.2 collection image.

Returns bytes/operations for the external suspended-process launcher only.
No executable is written. Stock and existing addon routes are fallbacks.
The audited twelve-position frontend publisher is a profile bound, not an
engine-wide maximum. AI pool extension is limited to native T2 loop owners.
"""
from __future__ import annotations
from dataclasses import replace
import struct
from master_rallye.addon_sdk.manifest import _validate_one

import build_vehicle_multislot_i0 as i0
import addon_collection_runtime as collection

registry = i0.registry


def validate_rows(rows):
    """Validate resolved rows through the ordinary SDK authorship schema."""
    for row in rows:
        raw = {k:v for k,v in row.items() if k not in {'class_local_index','race_colour_rgba_f32le_hex'}}
        raw.update(manifest_version=1, description='Explicit SCALE1 research capacity probe',
                   class_local_placement='append',
                   physical_id={'policy':'explicit','value':row['physical_id']})
        _validate_one(raw)
        if type(row['class_local_index']) is not int:
            raise ValueError('class_local_index must be an integer')
        if row.get('race_colour_rgba_f32le_hex') != struct.pack('<4f',*row['race_colour_rgba']).hex():
            raise ValueError('resolved race colour bytes mismatch')
    for key in ('addon_id',):
        if len({r[key] for r in rows}) != len(rows):
            raise ValueError('duplicate resolved addon identity')
    for key in ('runtime_family','model_family','wheel_family','physics_family'):
        if len({r['identity'][key].casefold() for r in rows}) != len(rows):
            raise ValueError('colliding resolved resource family')


def branch_target(image, pe, va, opcode):
    off = registry.va_to_file_offset(pe, va, 5)
    if image[off] != opcode:
        raise ValueError(f'expected branch {opcode:#x} at {va:#x}')
    return va + 5 + struct.unpack_from('<i', image, off + 1)[0]


def _profile(row):
    cls = {'T1':0, 'T2':1, 'T3':2}[row['vehicle_class']]
    if row['unlock'] != {'policy':'mirror_stock_unlock','stock_vehicle_id':10}:
        raise ValueError('extension currently admits the audited stock-ID10 unlock oracle only')
    p = collection._record_for_id27(row, 'scale1-roster-extension')
    return replace(p, slot_id=row['physical_id'], vehicle_class=cls,
                   local_index=row['class_local_index'])


def emit_audio_lookup(code, rows, parent):
    """Translate the qualified parent's result; never look up a participant twice."""
    code.label('audio'); code.emit(bytes.fromhex('ff742404')); code.call(parent)
    for n,row in enumerate(rows):
        i0._comparison_bytes(code,'eax',row['physical_id']); code.jne(f'a{n}')
        code.emit(b'\xb8'+struct.pack('<I',row['audio']['stock_audio_profile_id'])+bytes.fromhex('c20400')); code.label(f'a{n}')
    code.emit(bytes.fromhex('c20400'))


def payload(image, pe, rows, va):
    code = registry._CodeImage(va)
    rows = sorted(rows, key=lambda r:r['physical_id'])
    profiles = [_profile(r) for r in rows]
    old_init = branch_target(image, pe, i0.REGISTRY_INITIALIZER_CALL_VA, 0xe8)
    code.label('init'); code.emit(bytes.fromhex('568bf18bce')); code.call(old_init)
    for n,p in enumerate(profiles):
        registry._emit_record_initializer(code, p, 4 + p.slot_id * 52, f'name{n}')
    code.emit(bytes.fromhex('8bc65ec3'))
    code.label('forward')
    for n,p in enumerate(profiles):
        code.emit(b'\x83\x79\x10' + bytes([p.vehicle_class])); code.jne(f'f{n}')
        code.emit(b'\x83\x79' + bytes([0x14+4*p.vehicle_class,p.local_index])); code.jne(f'f{n}')
        code.emit(b'\xb8'+struct.pack('<I',p.slot_id)+b'\xc3'); code.label(f'f{n}')
    code.jump(branch_target(image,pe,i0.FORWARD_CLASS_HOOK_VA,0xe9))
    code.label('reverse')
    for n,p in enumerate(profiles):
        code.emit(b'\x81\x7c\x24\x04'+struct.pack('<I',p.slot_id)); code.jne(f'r{n}')
        code.emit(bytes.fromhex('568bf1'))
        code.emit(b'\xc7\x46\x10'+struct.pack('<I',p.vehicle_class))
        code.emit(b'\xc7\x46'+bytes([0x14+4*p.vehicle_class])+struct.pack('<I',p.local_index))
        code.jump(0x00481e89); code.label(f'r{n}')
    code.jump(branch_target(image,pe,i0.REVERSE_CLASS_HOOK_VA,0xe9))
    # Each bridge extends all existing identities, with the original helper as
    # fallback. Hook/continuation ABI is inherited from the prior audited layer.
    bridges = [
        (0x481a0e,'edi','manufacturer',0x481a18),
        (0x481a4b,'edi','model',0x481a55),
        *[(v,'eax','combined',v+8) for v in registry.QUICKRACE_LOCALIZATION_CALLS],
        *[(v,'esi','manufacturer' if group==0x33 else 'model',resume)
          for v,group,label,string,resume in registry.RACE_OPTIONS_LOCALIZATION_CALLS],
        *[(hook,'eax','combined',resume) for hook,slot,label,group,call,resume in registry.RACE_DETAILS_LOCALIZATION_CALLS],
        (0x44fa29,'edi','combined',0x44fa33),
    ]
    hooks = []
    for j,(hook,reg,field,resume) in enumerate(bridges):
        label=f'display{j}'; code.label(label)
        for n,p in enumerate(profiles):
            i0._comparison_bytes(code,reg,p.slot_id); code.jne(f'd{j}_{n}')
            code.mov_eax_literal(f'{field}{n}'); code.jump(resume); code.label(f'd{j}_{n}')
        code.jump(branch_target(image,pe,hook,0xe9)); hooks.append((hook,label,0xe9))
    code.label('results'); code.emit(i0.natural.results_name_stub_bytes()[:8])
    for n,p in enumerate(profiles):
        i0._comparison_bytes(code,'ecx',p.slot_id); code.jne(f'res{n}')
        code.mov_eax_literal(f'results{n}'); code.jump(i0.natural.RESULTS_AFTER_LOOKUP_VA); code.label(f'res{n}')
    code.jump(branch_target(image,pe,i0.natural.RESULTS_NAME_HOOK_VA,0xe9))
    code.label('unlock')
    for n,p in enumerate(profiles):
        code.emit(b'\x81\x79\x04'+struct.pack('<I',p.slot_id)); code.je('unlock_new')
    code.jump(branch_target(image,pe,i0.UNLOCK_CALL_VA,0xe8))
    code.label('unlock_new'); code.emit(bytes.fromhex('5183ec08c7042400000000c74424040a0000008d0c24'))
    code.call(0x45a150); code.emit(bytes.fromhex('83c40859c3'))
    code.label('locked')
    for n,p in enumerate(profiles):
        i0._comparison_bytes(code,'eax',p.slot_id-3); code.je('locked_new')
    code.jump(branch_target(image,pe,i0.LOCKED_REASON_HOOK_VA,0xe9))
    code.label('locked_new'); code.emit(bytes.fromhex('bb0c000000')); code.jump(0x481b49)
    # Chain the qualified parent lookup exactly once. The native thiscall
    # getter is allowed to clobber ECX/EDX. Calling it before falling back to
    # the parent caused a second lookup with a destroyed this pointer (e.g.
    # ECX=2 -> native read at 0x5e), crashing every stock race during audio init.
    # Parent already translates IDs26/27; new physical IDs pass through it.
    emit_audio_lookup(code,rows,branch_target(image,pe,i0.AUDIO_PROFILE_CALL_VA,0xe8))
    for mode,hook,reentry,exit_ in [
        ('quick_race',i0.QUICKRACE_T2_HOOK_VA,i0.QUICKRACE_T2_REENTRY_VA,i0.QUICKRACE_T2_EXIT_VA),
        ('rallye_cup',i0.CUP_T2_HOOK_VA,i0.CUP_T2_REENTRY_VA,i0.CUP_T2_EXIT_VA),
        ('master_rallye',i0.MASTER_T2_HOOK_VA,i0.MASTER_T2_REENTRY_VA,i0.MASTER_T2_EXIT_VA)]:
        pool=[r['physical_id'] for r in rows if r['vehicle_class']=='T2' and r['ai_eligibility'][mode]['enabled']]
        if not pool:continue
        label='pool_'+mode; code.label(label)
        # Existing ID27 loop visits the hook with ESI=14 then ESI=28. Let
        # the old stub append ID27 first; at 28 chain new entries through the
        # unchanged native exclusion/append body, then restore stock sentinel.
        for k,physical in enumerate(pool):
            prior=28 if k==0 else pool[k-1]+1
            i0._comparison_bytes(code,'esi',prior); code.jne(f'{label}_{k}')
            code.emit(b'\xbe'+struct.pack('<I',physical)); code.jump(reentry); code.label(f'{label}_{k}')
        i0._comparison_bytes(code,'esi',pool[-1]+1); code.jne(label+'_old')
        code.emit(b'\xbe\x0e\x00\x00\x00'); code.jump(exit_); code.label(label+'_old')
        code.jump(branch_target(image,pe,hook,0xe9)); hooks.append((hook,label,0xe9))
    for n,(p,r) in enumerate(zip(profiles,rows)):
        fields={'name':p.internal_name,'manufacturer':p.display_manufacturer,'model':p.display_model,
                'combined':p.display_quickrace,'results':r['results']['display_name']}
        for field,text in fields.items():
            code.label(f'{field}{n}'); code.emit(text.encode('ascii')+b'\0')
    hooks.extend([(i0.REGISTRY_INITIALIZER_CALL_VA,'init',0xe8),
                  (i0.FORWARD_CLASS_HOOK_VA,'forward',0xe9),(i0.REVERSE_CLASS_HOOK_VA,'reverse',0xe9),
                  (i0.natural.RESULTS_NAME_HOOK_VA,'results',0xe9),(i0.UNLOCK_CALL_VA,'unlock',0xe8),
                  (i0.LOCKED_REASON_HOOK_VA,'locked',0xe9),(i0.AUDIO_PROFILE_CALL_VA,'audio',0xe8)])
    return code.build(), {k:va+v for k,v in code.labels.items()}, hooks


def extend_image(source, image, rows, *, base_count=28, storage='existing_cave', payload_va=0x10000000):
    """Build one reversible extension; no source/frozen image is modified."""
    if i0.sha256(source)!=i0.RETAIL_SHA256 or len(image)!=len(source):
        raise ValueError('unsupported retail identity/image size')
    validate_rows(rows)
    pe=registry.parse_pe(source); rows=sorted(rows,key=lambda r:r['physical_id'])
    if not rows or [r['physical_id'] for r in rows]!=list(range(base_count,base_count+len(rows))):
        raise ValueError('native extension requires contiguous appended global records')
    classes={'T1':8,'T2':8,'T3':12}
    for r in rows:
        c=r['vehicle_class']
        if r['class_local_index']!=classes[c] or classes[c]>=12:
            raise ValueError('class slot must append within the audited twelve-position publisher')
        if c!='T2' and any(v['enabled'] for v in r['ai_eligibility'].values()):
            raise ValueError('new AI pool routes currently qualified for T2 loop structure only')
        classes[c]+=1
    count=base_count+len(rows)
    if count>=128:raise ValueError('current lifecycle/initializer signed imm8 encoding bound exceeded')
    ops=[]
    def patch(name,va,expected,replacement):
        off=registry.va_to_file_offset(pe,va,len(expected))
        if image[off:off+len(expected)]!=expected:raise ValueError(f'preimage changed: {name}')
        ops.append(i0._operation(name,'scale1-native-roster',off,expected,replacement,name,va=va))
    layout=i0.registry_layout(count-1);old=i0.registry_layout(base_count-1)
    patch('allocate_registry',i0.REGISTRY_ALLOCATOR_VA,struct.pack('<I',old['allocation_size']),struct.pack('<I',layout['allocation_size']))
    for va in [i0.CONSTRUCT_RECORD_COUNT_VA,i0.DESTRUCT_RECORD_COUNT_VA,i0.UNWIND_RECORD_COUNT_VA]:
        patch(f'lifecycle_{va:x}',va,bytes([base_count]),bytes([count]))
    for va in [i0.CONSTRUCT_RACETEST_BASE_VA,i0.DESTRUCT_RACETEST_BASE_VA,i0.UNWIND_RACETEST_BASE_VA]:
        patch(f'racetest_base_{va:x}',va,struct.pack('<I',old['racetest_base']),struct.pack('<I',layout['racetest_base']))
    for va,disp in registry.SECONDARY_INIT_LEAS:
        patch(f'racetest_init_{va:x}',va+2,struct.pack('<I',disp+(base_count-26)*52),struct.pack('<I',disp+(count-26)*52))
    for va,disp in registry.SECONDARY_CONSUMER_DISPS:
        patch(f'racetest_consumer_{va:x}',va+3,struct.pack('<I',disp+(base_count-26)*52),struct.pack('<I',disp+(count-26)*52))
    # G.1 constructor capacity stub has MOV [ESI+20],8 / [ESI+24],8.
    for c,va in [('T1',0x68e638),('T2',0x68e63f)]:
        if classes[c]!=8:patch('capacity_'+c,va,bytes([8]),bytes([classes[c]]))
    # Select only untouched bytes inside the already admitted code-cave page.
    chosen=None
    if storage=='private_allocation':
        # Fixed, independently reserved x86 address. The launcher fails before
        # resume if unavailable; no guessed relocation or fallback address.
        if type(payload_va) is not int or payload_va%16 or not 0x10000000<=payload_va<0x10040000:
            raise ValueError('capacity payload must be aligned within the bounded shared allocation')
        va=payload_va;blob,entries,hooks=payload(image,pe,rows,va)
        if len(blob)>65536:raise ValueError('private native payload budget exceeded')
        chosen=(va,blob,entries,hooks)
    elif storage=='existing_cave':
        for va in range(0x68e800,0x68f000,16):
            blob,entries,hooks=payload(image,pe,rows,va)
            if va+len(blob)>0x68f000:break
            off=registry.va_to_file_offset(pe,va,len(blob))
            if image[off:off+len(blob)]==bytes(len(blob)):
                chosen=(va,blob,entries,hooks);break
    else:raise ValueError('unsupported native storage backend')
    if chosen is None:raise ValueError(f'current external code-cave capacity exhausted ({len(blob)} bytes required); not an engine roster limit')
    va,blob,entries,hooks=chosen
    if storage=='existing_cave':patch('roster_payload',va,bytes(len(blob)),blob)
    for hook,label,opcode in hooks:
        off=registry.va_to_file_offset(pe,hook,5)
        patch('hook_'+label,hook,image[off:off+5],i0._rel32(hook,entries[label],opcode))
    # J.2 already maps the full cave page. No new PE layout or on-disk EXE.
    result=i0._apply_layer(image,ops)
    report={'operations':ops,'entries':entries,'payload_va':va,'payload_size':len(blob),
            'layout':layout,'classes':classes,'runtime_qualified':False,'storage':storage}
    if storage=='private_allocation':report['private_payload_hex']=blob.hex()
    return result,report
