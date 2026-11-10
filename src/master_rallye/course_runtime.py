"""COURSE-CAP2 layout and native-code composition (x86 retail profile).

The caller supplies the accepted Vehicle SDK emitter and patched parent image.
No second launcher, game installation, or per-Race-ID executable patch is used.
"""
from __future__ import annotations
import copy
import hashlib
import re
import struct

from .course_registry import validate_manifest, storage_layout, identity_contract

STOCK_MENU = [list(range(10,13)), list(range(13,16)), list(range(16,19)),
              list(range(19,22)), list(range(22,25)), list(range(25,36)),
              list(range(10)), list(range(36,39))]
STOCK_STAGES = [list(range(10,13)), list(range(13,16)), list(range(16,19)),
                list(range(19,22)), list(range(22,25)), list(range(36,39))]


def qualify(manifest, baseline, vehicle_profile):
    """Bind capacity to the actual accepted MRVC profile, never an independent N."""
    count = vehicle_profile['capacity_profile']['record_count']
    if manifest.get('vehicle_count', count) != count:
        raise ValueError('Course vehicle_count disagrees with accepted Vehicle Registry')
    doc = copy.deepcopy(manifest)
    doc['vehicle_count'] = count
    result = validate_manifest(doc, baseline)
    budget = result.get('runtime_budget', {})
    if not isinstance(budget.get('max_shared_bytes'), int) or result['layout']['allocation_size'] > budget['max_shared_bytes']:
        raise ValueError('Explicit shared-object qualification budget required')
    menu = copy.deepcopy(STOCK_MENU)
    additions = {}
    progress = set()
    for r in result['races'][39:]:
        if r.get('modes') != ['QuickRace']:
            raise ValueError('New race runtime admission currently supports offline QuickRace only')
        key = r.get('progress_key', '')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', key) or key in progress:
            raise ValueError('Each new race needs an independent stable progress key')
        progress.add(key)
        m = r.get('menu', {})
        g, pos = m.get('group'), m.get('position')
        if type(m.get('flag_frame')) is not int or m['flag_frame']<0:
            raise ValueError('Explicit nonnegative menu flag-frame binding required')
        if type(m.get('screenshot_pair')) is not int or m['screenshot_pair']<0:
            raise ValueError('Explicit independent screenshot-pair binding required')
        # Preserve all native unlock/mode groups. Additive rows currently enter
        # always-available group 0, after its original three rows.
        if g != 0 or type(pos) is not int or not 3 <= pos < 3+len(result['races'])-39 or pos in additions:
            raise ValueError('New QuickRace entry requires an additive group-0 position')
        additions[pos]=r['id']
        if not isinstance(r.get('title'), str) or not r['title'] or len(r['title'].encode('ascii')) > 160:
            raise ValueError('Need a bounded native ASCII title')
    menu[0].extend(additions[p] for p in range(3,3+len(additions)))
    reverse = {i:(g,p) for g,rows in enumerate(menu) for p,i in enumerate(rows)}
    if len(reverse) != len(result['races']):
        raise ValueError('Menu and registry are not bijective')
    result.update(stage_schedules=copy.deepcopy(STOCK_STAGES)+[g['races'] for g in result.get('competitions',[])],
                  menu_groups=menu, reverse_menu=[reverse[i] for i in range(len(reverse))],
                  status='NATIVE_CANDIDATE_REQUIRES_OWNER_TEST', runtime_qualified=False)
    return result


def next_stage(stages, race_id):
    """Explicit schedule semantics, with no RaceID+1 assumption."""
    if len(set(stages)) != len(stages) or race_id not in stages:
        raise ValueError('Race is not a unique stage of this competition')
    i = stages.index(race_id)
    return {'stage_index':i, 'next_race_id':stages[i+1] if i+1<len(stages) else None}


def append_native(source, image, parent_blob, catalog, *, emitter, pe_offset):
    """Append to the Vehicle arena and return one composed reference transaction.

    Preimages are verified against the accepted parent. Final RVP generation
    subsequently compares the complete result to the original retail image.
    """
    layout = catalog['layout']; count=layout['race_count']; base=layout['race_base']
    prefix=parent_blob+b'\x90'*((-len(parent_blob))%16)
    c=emitter(0x10000000+len(prefix)); ops=[]; work=bytearray(image)
    def u(n):return struct.pack('<I',n)
    def patch(va, before, after, name):
        off=pe_offset(va,len(before))
        if work[off:off+len(before)] != before:
            raise ValueError(f'Course hook preimage/owner mismatch: {name} at {va:08x}')
        if len(before)!=len(after):raise ValueError('Fixed-width operation required')
        work[off:off+len(before)]=after
        ops.append({'name':name,'file_offset':off,'original_bytes':before.hex(),'replacement_bytes':after.hex(),'va':va})
    def branch(va,target,opcode=0xe9):return bytes([opcode])+struct.pack('<i',target-va-5)
    def hook(va, before, label):
        patch(va,before,branch(va,c.base_va+c.labels[label])+b'\x90'*(len(before)-5),label)
    # All original 39 constructors/destructors are retained. Only their vector
    # count changes; the original vector helper owns exceptional unwind.
    for name,va,continuation,lea in [('construct',0x458d0e,0x458d16,b'\x8d\x8e'),('destroy',0x458e28,0x458e30,b'\x8d\x86')]:
        c.label(name);c.emit(b'\x68'+u(count)+lea+u(base));c.jump(continuation)
        hook(va,b'\x6a\x27'+lea+u(base),name)
    c.label('unwind');c.emit(b'\x68'+u(count)+b'\x6a\x2c\x8b\x45\xf0');c.jump(0x6867b2)
    hook(0x6867ab,b'\x6a\x27\x6a\x2c\x8b\x45\xf0','unwind')
    patch(0x45a3e0,u(storage_layout(layout['vehicle_count'],39)['allocation_size']),u(layout['allocation_size']),'shared_allocation')
    c.label('initialize_additions');c.call(0x45a330)
    for r in catalog['races'][39:]:
        f=r['native_fields']
        for v in reversed(f[7:]):c.emit(b'\x68'+u(v))
        c.emit(b'\x51\x8b\xcc');c.push_literal('scene_'+str(r['id']));c.call(0x4d11d0)
        for v in reversed(f[:7]):c.emit(b'\x68'+u(v))
        c.emit(b'\x8d\x8e'+u(base+r['id']*44));c.call(0x45a330)
    c.jump(0x459fdc)
    hook(0x459fd7,branch(0x459fd7,0x45a330,0xe8),'initialize_additions')
    # Forward and reverse selection share exactly the same manifest maps.
    c.label('menu_forward');c.emit(b'\x8b\x41\x10\x83\xf8\x07');c.ja('invalid')
    c.emit(b'\x8b\x54\x81\x14\x3b\x14\x85');c.imm32.append((len(c.code),'menu_counts'));c.emit(b'\0'*4)
    c.emit(b'\x0f\x83\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'invalid'))
    c.emit(b'\x8b\x04\x85');c.imm32.append((len(c.code),'menu_pointers'));c.emit(b'\0'*4+b'\x8b\x04\x90\xc3')
    hook(0x47f2b0,b'\x8b\x41\x10\x83\xf8\x07','menu_forward')
    c.label('menu_reverse');c.emit(b'\x8b\x44\x24\x04\x3d'+u(count));c.emit(b'\x0f\x83\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'invalid'))
    for g, rows in enumerate(catalog['menu_groups']):
        if rows!=STOCK_MENU[g]:c.emit(b'\xc7\x41'+bytes([0x54+g*4])+u(len(rows)))
    c.emit(b'\x8b\x14\x85');c.imm32.append((len(c.code),'reverse_group'));c.emit(b'\0'*4+b'\x89\x51\x10\x8b\x04\x85')
    c.imm32.append((len(c.code),'reverse_local'));c.emit(b'\0'*4+b'\x89\x44\x91\x14\xc2\x04\x00')
    hook(0x47f320,b'\x8b\x44\x24\x04\x83\xf8\x0a','menu_reverse')
    c.label('menu_position_bound');c.emit(b'\x81\xfe'+u(max(map(len,catalog['menu_groups']))));c.emit(b'\x0f\x8c\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),0x47ecba));c.jump(0x47ed09)
    hook(0x47ed04,b'\x83\xfe\x0b\x7c\xb1','menu_position_bound')
    # Retail +0x550 = race_base+4, i.e. RaceID itself, not an artwork field.
    # Separate new image identities before the native 2*pair/+1 publisher.
    c.label('menu_image_pair');c.emit(b'\x8b\xac\x38'+u(base+4)+b'\x83\xfb\x27')
    c.emit(b'\x0f\x82\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'image_pair_done'))
    c.emit(b'\x8b\x2c\x9d');c.imm32.append((len(c.code),'image_pairs'));c.emit(b'\0'*4)
    c.label('image_pair_done');c.jump(0x47ed5a)
    hook(0x47ed53,b'\x8b\xac\x38'+u(base+4),'menu_image_pair')
    # Distinguish actual race contexts from Master aggregate index 39. The
    # original getter/setter and its original table remain untouched.
    def clone_progress(start,size,label):
        c.align();c.label(label);new=c.va
        raw=bytearray(source[pe_offset(start,size):pe_offset(start,size)+size])
        from capstone import Cs,CS_ARCH_X86,CS_MODE_32
        cs=Cs(CS_ARCH_X86,CS_MODE_32)
        for ins in cs.disasm(bytes(raw),start):
            at=ins.address-start
            if ins.bytes[0] == 0xe8:
                target=ins.address+5+struct.unpack_from('<i',ins.bytes,1)[0]
                struct.pack_into('<i',raw,at+1,target-(new+at+5))
        marker=u(0x6f6780)
        if raw.count(marker)!=1:raise ValueError('Native progress table operand changed')
        at=raw.index(marker);raw[at:at+4]=b'\0'*4
        c.imm32.append((len(c.code)+at,'progress_keys'));c.emit(raw)
    for original,size,label,ret in [(0x4b0000,133,'get_race_best',4),(0x4aff80,128,'set_race_best',8)]:
        c.label(label+'_dispatch');c.emit(b'\x81\x7c\x24\x04'+u(39));c.emit(b'\x0f\x82\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),original))
        c.emit(b'\x81\x7c\x24\x04'+u(count));c.emit(b'\x0f\x83\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'invalid'));c.jump(label)
        clone_progress(original,size,label)
    # All race-context owners, including the shared Results view. Master's
    # aggregate owners 453BD0/453D10 and stock default reset 4B0090 stay native.
    from capstone import Cs,CS_ARCH_X86,CS_MODE_32
    cs=Cs(CS_ARCH_X86,CS_MODE_32)
    for start,size in [(0x458870,212),(0x449d40,336),(0x4501d0,311),(0x45b3f0,288),
                       (0x45eb30,1451),(0x460b50,1734),(0x47ed10,1387)]:
        for ins in cs.disasm(source[pe_offset(start,size):pe_offset(start,size)+size],start):
            if ins.bytes[0]!=0xe8:continue
            target=ins.address+5+struct.unpack_from('<i',ins.bytes,1)[0]
            if target in (0x4b0000,0x4aff80):
                label=('get' if target==0x4b0000 else 'set')+'_race_best_dispatch'
                patch(ins.address,bytes(ins.bytes),branch(ins.address,c.base_va+c.labels[label],0xe8),'race_context_'+hex(ins.address))
    # Retain the original details publisher and override only the new caption.
    # Broker arguments are interned gaString IDs (4D0580), not owned enString
    # buffers (4D11D0). Passing a heap pointer as an ID corrupts Broker indexing.
    c.label('publish_details');c.emit(b'\x56\x8b\xf1\x83\xec\x08');c.call(0x47ed10)
    c.emit(b'\x8b\xce');c.call('menu_forward');c.emit(b'\x83\xf8\x27')
    c.emit(b'\x0f\x82\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'details_done'))
    c.emit(b'\x8b\x04\x85');c.imm32.append((len(c.code),'title_pointers'));c.emit(b'\0'*4)
    c.emit(b'\x50\x8d\x4c\x24\x08');c.call(0x4d0580)
    c.emit(b'\x68'+u(0x6b7230)+b'\x8d\x4c\x24\x04');c.call(0x4d0580)
    c.emit(b'\x8d\x54\x24\x04\x8d\x04\x24\x52\x50');c.call(0x4d8ec0);c.emit(b'\x8b\xc8');c.call(0x4d85f0)
    c.label('details_done');c.emit(b'\x83\xc4\x08\x5e\xc3')
    # Decode original instructions, so inline jump-table bytes are not mistaken
    # for relocations. There are exactly three native direct call owners.
    calls=[]
    for start,size in [(0x47e2d0,1859),(0x47f3d0,111),(0x47f440,120)]:
        for ins in cs.disasm(source[pe_offset(start,size):pe_offset(start,size)+size],start):
            if ins.bytes[0]==0xe8 and ins.address+5+struct.unpack_from('<i',ins.bytes,1)[0]==0x47ed10:
                calls.append(ins.address);patch(ins.address,bytes(ins.bytes),branch(ins.address,c.base_va+c.labels['publish_details'],0xe8),'details_'+hex(ins.address))
    if len(calls)!=3:raise ValueError('Native details caller coverage differs')
    # Admission is at the confirm action, not a misleading menu substitution.
    # Denied selections return to the original UI epilogue with no RaceID write.
    c.label('admit_selection');c.call('menu_forward');c.emit(b'\x83\xf8\x27')
    c.emit(b'\x0f\x82\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'admission_return'))
    c.emit(b'\x50');c.call(0x4ae700);c.emit(b'\x8b\xc8');c.call(0x4addb0);c.emit(b'\x84\xc0');c.je('selection_denied')
    c.call(0x4ae700);c.emit(b'\x8b\xc8');c.call(0x4ae2d0);c.emit(b'\x84\xc0');c.jne('selection_denied')
    c.call(0x4ada50);c.emit(b'\x8b\xc8');c.call(0x4ad930);c.emit(b'\x84\xc0');c.jne('selection_denied')
    c.emit(b'\x58');c.label('admission_return');c.emit(b'\xc3')
    c.label('selection_denied');c.emit(b'\x83\xc4\x08\x6a\x30');c.push_literal('admission_message');c.push_literal('admission_message');c.emit(b'\x6a\x00\xff\x15'+u(0x68f2b4));c.jump(0x47ec84)
    for va in [0x47ea6b,0x47ea9d,0x47eaf6]:
        patch(va,branch(va,0x47f2b0,0xe8),branch(va,c.base_va+c.labels['admit_selection'],0xe8),'admit_'+hex(va))
    # Executable schedule lookup. stdcall(index, RaceID) -> EAX stage ordinal,
    # EDX next RaceID/-1, ECX stage count, CF=invalid. Nonvolatile regs retained.
    c.label('lookup_stage');c.emit(b'\x56\x57\x53\x8b\x44\x24\x10\x8b\x54\x24\x14\x3d'+u(len(catalog['stage_schedules'])))
    c.emit(b'\x0f\x83\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'stage_invalid'))
    c.emit(b'\xbe');c.imm32.append((len(c.code),'competitions'));c.emit(b'\0'*4+b'\x31\xdb')
    c.label('schedule_seek');c.emit(b'\x39\xc3');c.je('schedule_found');c.emit(b'\x8b\x0e\x8d\x74\x8e\x04\x43');c.jump('schedule_seek')
    c.label('schedule_found');c.emit(b'\x8b\x3e\x83\xc6\x04\x31\xc0')
    c.label('stage_seek');c.emit(b'\x39\xf8');c.emit(b'\x0f\x83\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'stage_invalid'))
    c.emit(b'\x3b\x14\x86');c.je('stage_found');c.emit(b'\x40');c.jump('stage_seek')
    c.label('stage_found');c.emit(b'\x8b\xcf\x8d\x58\x01\xba\xff\xff\xff\xff\x39\xfb')
    c.emit(b'\x0f\x83\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'stage_return'))
    c.emit(b'\x8b\x14\x9e');c.label('stage_return');c.emit(b'\xf8\x5b\x5f\x5e\xc2\x08\x00')
    c.label('stage_invalid');c.emit(b'\xb8\xff\xff\xff\xff\x8b\xd0\xf9\x5b\x5f\x5e\xc2\x08\x00')
    # Native stock Cup/Invitation advance now consumes explicit lists. Original
    # result keys, trophy rules and unlock transitions are unchanged.
    c.label('cup_stage_index');c.emit(b'\x53\x55\x50');c.call('lookup_stage')
    c.emit(b'\x0f\x82\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'invalid'));c.jump(0x45b1ff)
    hook(0x45b1fa,b'\x8b\xc5\x53\x2b\xc6','cup_stage_index')
    c.label('cup_next_stage');c.call(0x4ae700);c.emit(b'\x8b\xc8');c.call(0x4ae620);c.emit(b'\x55\x50');c.call('lookup_stage')
    c.emit(b'\x0f\x82\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),'invalid'))
    c.emit(b'\x83\xfa\xff');c.emit(b'\x0f\x84\0\0\0\0');c.rel32.append((len(c.code)-4,len(c.code),0x45b235))
    c.emit(b'\x8b\xea');c.jump(0x45b39f)
    hook(0x45b22c,b'\x45\x3b\xef\x0f\x8e\x6a\x01\x00\x00','cup_next_stage')
    # Invalid runtime indexes must stop instead of loading a different course.
    c.label('invalid');c.emit(b'\x6a\x10');c.push_literal('invalid_message');c.push_literal('invalid_message');c.emit(b'\x6a\x00\xff\x15'+u(0x68f2b4)+b'\x6a\x01\xff\x15'+u(0x68f114)+b'\x0f\x0b')
    c.label('invalid_message');c.emit(b'Course Registry: invalid race/menu/stage index. Stopped before resource or progress access.\0')
    c.label('admission_message');c.emit(b'Course Registry: new races currently support offline Quick Race only. Selection was not changed.\0')
    for r in catalog['races'][39:]:
        c.label('scene_'+str(r['id']));c.emit(r['scene'].removeprefix('DataScene/').removesuffix('.xml').encode('ascii')+b'\0')
        c.label('progress_'+str(r['id']));c.emit(('CourseRegistryV1/'+r['progress_key']).encode('ascii')+b'\0')
        c.label('title_'+str(r['id']));c.emit(r['title'].encode('ascii')+b'\0')
    c.align(4);c.label('menu_counts');c.emit(b''.join(u(len(rows)) for rows in catalog['menu_groups']))
    c.label('menu_pointers')
    for g in range(8):c.imm32.append((len(c.code),'menu_'+str(g)));c.emit(b'\0'*4)
    for g, rows in enumerate(catalog['menu_groups']):c.label('menu_'+str(g));c.emit(b''.join(u(i) for i in rows))
    for label,index in [('reverse_group',0),('reverse_local',1)]:c.label(label);c.emit(b''.join(u(row[index]) for row in catalog['reverse_menu']))
    c.label('image_pairs');c.emit(b''.join(u(r['id'] if r['id']<39 else r['menu']['screenshot_pair']) for r in catalog['races']))
    c.label('progress_keys')
    for r in catalog['races']:
        if r['id']<39:
            # Stock keys are runtime-constructed enString handles in BSS.
            # Dispatch never indexes this private table for original races.
            c.emit(u(0))
        else:c.imm32.append((len(c.code),'progress_'+str(r['id'])));c.emit(b'\0'*4)
    c.label('title_pointers')
    for r in catalog['races']:
        if r['id']<39:c.emit(u(0))
        else:c.imm32.append((len(c.code),'title_'+str(r['id'])));c.emit(b'\0'*4)
    c.label('competitions')
    for stages in catalog['stage_schedules']:
        c.emit(u(len(stages))+b''.join(u(i) for i in stages))
    c.align(4);c.label('descriptor')
    fields=[int.from_bytes(b'MRCR','little'),1,64,count,44,layout['vehicle_count'],base,layout['allocation_size'],0x45a3c0]
    c.emit(b''.join(u(i) for i in fields))
    for label in ['menu_counts','menu_pointers','reverse_group','reverse_local','progress_keys','competitions']:
        c.imm32.append((len(c.code),label));c.emit(b'\0'*4)
    c.emit(u(len(catalog['stage_schedules'])))
    blob=prefix+c.build()
    return bytes(work),blob,{'operations':ops,'entries':{k:c.base_va+v for k,v in c.labels.items()},
        'layout':layout,'parent_prefix_preserved':blob[:len(parent_blob)]==parent_blob,
        'identity_sha256':identity_contract(catalog),'runtime_qualified':False,
        'mode_admission':'New records: single-player QuickRace; stock competitions unchanged',
        'pending':['custom competition runtime dispatch','owner menu/race/Results/save verification']}
