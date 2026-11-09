"""Native configurable capacity core over the accepted SDK33 parent.

Emits process-operation evidence and a private extension, never a game EXE.
Not admitted by the runtime launcher: presentation, AI pools, damage tables,
persistent competition and mod consumers require separate closure first.
"""
from dataclasses import replace
import re
import struct

import sdk_capacity_native as legacy
from master_rallye.addon_sdk.capacity_profile import SDK33, validate_profile, layout

registry = legacy.registry
BASE_COUNT = 33
BASE_ADDRESS = 0x10000000


def build_core(source, parent_image, parent_extension, profile, records, *, parent_allocation_size=524288):
    """Return virtual image, combined allocation and evidence; inputs immutable.

    records contains VehicleRecordProfiles for every appended physical ID.
    Native strings and record ownership use the existing full initializer.
    """
    p = validate_profile(profile);count = p['record_count']
    if set(p['classes']) != set(SDK33):
        raise ValueError('More than three classes needs separate native state/campaign relocation')
    if len(parent_image) != len(source): raise ValueError('Parent PE size differs')
    pe = registry.parse_pe(source)
    if type(parent_allocation_size) is not int or parent_allocation_size < len(parent_extension) or parent_allocation_size % 65536:
        raise ValueError('Parent allocation must contain its extension and use allocation granularity')
    # Complete declarations are mandatory. Uninitialized default records are
    # not silently advertised as playable vehicles.
    records = sorted(records, key=lambda r: r.slot_id)
    if [r.slot_id for r in records] != list(range(BASE_COUNT, count)):
        raise ValueError('Supply every appended record exactly once')
    for r in records:
        if not isinstance(r.internal_name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',r.internal_name):
            raise ValueError('Native family must follow the existing SDK resource-family schema')
        if len(r.stats)!=4 or len(r.race_colour_rgba_bits)!=4 or any(type(v) is not int or not 0<=v<=0xffffffff for v in r.race_colour_rgba_bits):
            raise ValueError('Native record requires four stats and four float bit patterns')
    offset = (len(parent_extension)+15)//16*16
    va = BASE_ADDRESS+offset
    code = registry._CodeImage(va)
    ops = []

    def label(name):code.label(name)
    def emit(raw):code.emit(raw)
    def patch(name, address, before, after):
        at = registry.va_to_file_offset(pe, address, len(before))
        if parent_image[at:at+len(before)] != before:
            raise ValueError('Capacity preimage/owner mismatch: '+name)
        if len(before) != len(after): raise ValueError('Operation must preserve PE size')
        ops.append(legacy.i0._operation(name, 'v-cap-core', at, before, after, name, va=address))
    def hook(name, address, stolen):
        patch(name, address, stolen, legacy.i0._rel32(address, va+code.labels[name], 0xe9)+b'\x90'*(len(stolen)-5))
    # Widen the actual instructions, not only their sign-extended imm8 bytes.
    # All stolen instructions have verified fixed, non-relative semantics.
    for name, address, tail in [
        ('construct_count', 0x458cf3, bytes.fromhex('8d4604')),
        ('destruct_count', 0x458e45, bytes.fromhex('83c604')),
        ('unwind_count', 0x686795, bytes.fromhex('6a348b45f0')),
    ]:
        label(name);emit(b'\x68'+struct.pack('<I',count)+tail)
        code.jump(address+2+len(tail))
        hook(name,address,b'\x6a\x21'+tail)
    old, new = layout(BASE_COUNT),p['layout']
    patch('registry_allocation',0x45a3e0,struct.pack('<I',old['allocation_size']),struct.pack('<I',new['allocation_size']))
    for address in (0x458d12,0x458e2c,0x6867b3):
        patch('racetest_lifetime_'+hex(address),address,struct.pack('<I',old['racetest_base']),struct.pack('<I',new['racetest_base']))
    for address, disp in registry.SECONDARY_INIT_LEAS:
        patch('racetest_init_'+hex(address),address+2,struct.pack('<I',disp+7*52),struct.pack('<I',disp+(count-26)*52))
    for address, disp in registry.SECONDARY_CONSUMER_DISPS:
        patch('racetest_consumer_'+hex(address),address+3,struct.pack('<I',disp+7*52),struct.pack('<I',disp+(count-26)*52))
    counts=[len(p['classes'][c]) for c in SDK33]
    for c,address,previous,value in zip(SDK33,(0x68e638,0x68e63f,0x480a65),(8,12,13),counts):
        patch('class_count_'+c,address,struct.pack('<I',previous),struct.pack('<I',value))
    # Original publisher's 64-byte key buffer holds the decimal index. Its
    # iteration count is separate from registered scene widgets/atlas frames.
    label('publisher');emit(b'\x81\xfe'+struct.pack('<I',max(counts)))
    emit(b'\x0f\x8c'+struct.pack('<i',0x48195a-(code.va+6)))
    code.jump(0x4819a9);hook('publisher',0x4819a4,bytes.fromhex('83fe0d7cb1'))

    # O(1) forward map, bounds checked before dereferencing the table.
    label('forward');emit(bytes.fromhex('8b411083f803'))
    emit(b'\x0f\x83'+bytes(4));code.rel32.append((len(code.code)-4,len(code.code),'invalid_forward'))
    emit(bytes.fromhex('8b548114')) # EDX = [ECX+EAX*4+14]
    emit(b'\x3b\x14\x85');code.imm32.append((len(code.code),'counts'));emit(bytes(4))
    emit(b'\x0f\x83'+bytes(4));code.rel32.append((len(code.code)-4,len(code.code),'invalid_forward'))
    emit(b'\x8b\x04\x85');code.imm32.append((len(code.code),'class_ptrs'));emit(bytes(4))
    emit(bytes.fromhex('8b0490c3'))
    label('invalid_forward');emit(bytes.fromhex('b8ffffffffc3'))
    label('reverse');emit(bytes.fromhex('8b4424043d')+struct.pack('<I',count))
    emit(b'\x0f\x83'+bytes(4));code.rel32.append((len(code.code)-4,len(code.code),'invalid_reverse'))
    emit(bytes.fromhex('568bf18b1485'));code.imm32.append((len(code.code),'reverse_classes'));emit(bytes(4))
    emit(bytes.fromhex('8956108b0485'));code.imm32.append((len(code.code),'reverse_locals'));emit(bytes(4))
    emit(bytes.fromhex('89449614'));code.jump(0x481e89)
    label('invalid_reverse');emit(bytes.fromhex('c20400'))
    for name, address in [('forward',0x481e20),('reverse',0x481e50)]:
        at=registry.va_to_file_offset(pe,address,5)
        if parent_image[at]!=0xe9:raise ValueError('Expected SDK33 mapping owner')
        hook(name,address,parent_image[at:at+5])
    # Preserve the complete parent's initialization chain and all old records.
    label('init');emit(bytes.fromhex('568bf18bce'))
    parent_init=legacy.branch_target(parent_image,pe,0x458d3f,0xe8)
    if not BASE_ADDRESS <= parent_init < BASE_ADDRESS+len(parent_extension):
        raise ValueError('SDK33 initializer does not belong to the supplied extension')
    code.call(parent_init)
    class_for={i:c for c,ids in p['classes'].items() for i in ids}
    for n,r in enumerate(records):
        r=replace(r,vehicle_class=list(SDK33).index(class_for[r.slot_id]))
        registry._emit_record_initializer(code,r,4+r.slot_id*52,'name'+str(n),wide_immediates=True)
    emit(bytes.fromhex('8bc65ec3'))
    at=registry.va_to_file_offset(pe,0x458d3f,5)
    patch('initializer',0x458d3f,parent_image[at:at+5],legacy.i0._rel32(0x458d3f,va+code.labels['init'],0xe8))
    code.align(4);label('descriptor')
    emit(struct.pack('<4s6I',b'MRVC',1,44,count,52,3,0x45a3c0))
    for target in ('counts','class_ptrs','reverse_classes','reverse_locals'):
        code.imm32.append((len(code.code),target));emit(bytes(4))
    label('counts');emit(struct.pack('<3I',*counts))
    label('class_ptrs')
    for c in SDK33:code.imm32.append((len(code.code),'map_'+c));emit(bytes(4))
    for c,ids in p['classes'].items():label('map_'+c);emit(struct.pack('<'+str(len(ids))+'I',*ids))
    reverse={i:(c,n) for c,ids in enumerate(p['classes'].values()) for n,i in enumerate(ids)}
    label('reverse_classes');emit(struct.pack('<'+str(count)+'I',*[reverse[i][0] for i in range(count)]))
    label('reverse_locals');emit(struct.pack('<'+str(count)+'I',*[reverse[i][1] for i in range(count)]))
    for n,r in enumerate(records):label('name'+str(n));emit(r.internal_name.encode('ascii')+b'\0')
    blob=code.build();combined=parent_extension+bytes(offset-len(parent_extension))+blob
    allocation=max(parent_allocation_size,(len(combined)+65535)//65536*65536)
    if allocation+new['allocation_size']>p['memory_budget_bytes']:
        raise ValueError('Emitted core exceeds the configured tool memory budget')
    if BASE_ADDRESS+allocation>0x7fffffff:raise ValueError('Private arena exceeds admitted signed x86 address range')
    image=legacy.i0._apply_layer(parent_image,ops)
    report={'schema':'mr-capacity-core/1','profile':p,'operations':ops,
        'entries':{name:va+n for name,n in code.labels.items()},
        'extension_offset':offset,'extension_size':len(blob),'private_allocation_size':allocation,
        'parent_bytes_preserved':combined[:len(parent_extension)]==parent_extension,
        'runtime_installable':False,'runtime_qualified':False,
        'status':'OFFLINE_NATIVE_CORE_ONLY',
        'unresolved_runtime_gates':['frontend scene widgets and icon banks','new-record unlock/display/audio routes',
            'AI candidate enumeration','damage and optional mod per-ID tables','active championship/save lifecycle',
            'binary replay/network encoding','complete game lifecycle and resource qualification'],
        'abi':{'record':52,'CarID':'nonnegative 32-bit','RaceTest':'39 x 44, moved as one owned tail',
               'mapping':'thiscall; reverse continues at 0x481e89 with saved ESI',
               'installation_precondition':'Suspended process before first registry construction; global 0x6F5ED4 must still be zero',
               'allocation':'fixed before registry construction; never reallocates live owned strings'}}
    return image,combined,report
