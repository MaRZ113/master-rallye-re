"""One evidence-bound PE32 adapter shared by offline and native validation.

The original EXE digest is provenance, never the admission criterion.
"""
import struct
from .demo_identity import load_segments,file_offset


def number(value):
    return int(value,0) if isinstance(value,str) else int(value)


def validate(raw,profile):
    if profile['schema']!='vehicle-setup-native-adapter/1':raise ValueError('Unknown setup adapter')
    segments=load_segments(raw)
    pe=struct.unpack_from('<I',raw,60)[0]
    if struct.unpack_from('<H',raw,pe+4)[0]!=0x14c or struct.unpack_from('<I',raw,pe+52)[0]!=number(profile['image_base']):
        raise ValueError('Unsupported setup image architecture/base')
    checked=[]
    def read(va,count):return raw[file_offset(segments,va,count):file_offset(segments,va,count)+count]
    for name,item in profile['apis'].items():
        va=number(item['va']);expected=bytes.fromhex(item['bytes'])
        if len(expected)!=8 or read(va,8)!=expected:raise ValueError('Native setup API preimage differs: '+name)
        checked.append(name)
    menu=profile['menu'];base=number(menu['vtable'])
    for role in ('tick','init'):
        slot=base+menu[role+'_offset'];target=number(menu[role])
        if struct.unpack('<I',read(slot,4))[0]!=target:raise ValueError('Native setup vtable owner differs: '+role)
    for role,item in profile['publishers'].items():
        va=number(item['call']);target=number(item['target'])
        if read(va,5)!=b'\xe8'+struct.pack('<i',target-va-5):raise ValueError('Native parameter writer call differs: '+role)
    return {'status':'PASS_STATIC_ADAPTER','apis':checked,'tick_slot':base+menu['tick_offset'],
            'qualification':'Original bytes/address mapping only; no gameplay proof'}


def header(profile):
    rows=['#pragma once','#include <array>','#include <cstdint>','namespace mrsetup::adapter {',
          'struct Api {uintptr_t va;std::array<unsigned char,8> bytes;};']
    rows.append('inline constexpr uintptr_t image_base='+hex(number(profile['image_base']))+';')
    for name,item in profile['apis'].items():rows.append('inline constexpr uintptr_t '+name+'='+hex(number(item['va']))+';')
    rows.append('inline constexpr Api apis[]={'+','.join('{'+hex(number(v['va']))+',{'+','.join('0x'+v['bytes'][i:i+2] for i in range(0,16,2))+'}}' for v in profile['apis'].values())+'};')
    menu=profile['menu']
    rows.append('inline constexpr uintptr_t menu_vtable='+hex(number(menu['vtable']))+';')
    rows.append('inline constexpr uintptr_t menu_tick_slot='+hex(number(menu['vtable'])+menu['tick_offset'])+',menu_tick_target='+hex(number(menu['tick']))+';')
    rows.append('inline constexpr uintptr_t menu_init_slot='+hex(number(menu['vtable'])+menu['init_offset'])+',menu_init_target='+hex(number(menu['init']))+';')
    for name,item in profile['publishers'].items():
        rows.append('inline constexpr uintptr_t '+name+'_call='+hex(number(item['call']))+','+name+'_target='+hex(number(item['target']))+';')
    return '\n'.join(rows+['}'])+'\n'
