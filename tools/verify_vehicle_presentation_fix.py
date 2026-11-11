"""Targeted offline verification of a derived presentation candidate.

The native caller ABI is executed with Unicorn; external string/record sinks
are intercepted. This is initializer evidence, not a running-game visual test.
"""
from __future__ import annotations
import argparse, json, struct, sys, hashlib
from pathlib import Path
from vehicle_presentation_fix import Resources, marker_slots, sha
from roster_v4 import Image, Rvp, record_pushes, egg_span
from vehicle_roster_build import fnv64


def native(host):
    raw=(host/'MRMods/Vehicles/active/roster.mrvr').read_bytes()
    ro,rl,po,pl=struct.unpack_from('<4I',raw,144)
    assert fnv64(raw[256:])==struct.unpack_from('<Q',raw,160)[0]
    img=Image(raw[po:po+pl],Rvp(raw[ro:ro+rl]),[],(host/'MRallye.exe').read_bytes())
    return raw,img


def machine(host,img):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_ESI
    u=Uc(UC_ARCH_X86,UC_MODE_32);exe=(host/'MRallye.exe').read_bytes()
    pe=struct.unpack_from('<I',exe,0x3c)[0];n=struct.unpack_from('<H',exe,pe+6)[0]
    size=struct.unpack_from('<H',exe,pe+20)[0];image_size=struct.unpack_from('<I',exe,pe+24+56)[0]
    u.mem_map(0x400000,(image_size+4095)&~4095)
    for i in range(n):
        at=pe+24+size+i*40
        _vs,rva,rs,fo=struct.unpack_from('<4I',exe,at+8)
        u.mem_write(0x400000+rva,exe[fo:fo+rs])
    for op in img.rvp.ops:
        if op['flags'] != 1:u.mem_write(0x400000+op['rva'],bytes(op['after']))
    u.mem_map(0x10000000,(len(img.payload)+4095)&~4095);u.mem_write(0x10000000,bytes(img.payload))
    u.mem_map(0x20000000,0x20000);u.mem_map(0x21000000,0x10000)
    u.mem_map(0x22000000,0x1000)
    u.reg_write(UC_X86_REG_ESP,0x20010000);u.mem_write(0x20010000,struct.pack('<I',0x22000000))
    u.reg_write(UC_X86_REG_ECX,0x21000000);u.reg_write(UC_X86_REG_ESI,0x21000000)
    return u


def capture_initializers(host,img):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_EAX
    result={}
    def hook(u,at,size,user):
        esp=u.reg_read(UC_X86_REG_ESP)
        ret=struct.unpack('<I',u.mem_read(esp,4))[0]
        def finish(pop):
            u.reg_write(UC_X86_REG_ESP,esp+4+pop);u.reg_write(UC_X86_REG_EIP,ret)
        if at==0x4d11d0:
            p=bytes(u.mem_read(esp+4,4));u.mem_write(u.reg_read(UC_X86_REG_ECX),p);finish(4)
        elif at==0x45a0b0:
            args=bytes(u.mem_read(esp+4,48));values=struct.unpack_from('<7I',args)
            cid=values[0];nameptr=struct.unpack_from('<I',args,28)[0]
            name=bytes(u.mem_read(nameptr,128)).split(b'\0')[0].decode('ascii')
            assert u.reg_read(UC_X86_REG_ECX)==0x21000000+4+cid*52
            assert cid not in result
            result[cid]={'integers':list(values),'family':name,'rgba_hex':args[32:48].hex()}
            u.reg_write(UC_X86_REG_EAX,u.reg_read(UC_X86_REG_ECX));finish(48)
    u=machine(host,img);u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x458e70,0x22000000,count=100000)
    assert set(result)==set(range(25))
    for cid in range(25,35):
        store,at,_=record_pushes(img,cid)[0];base=0x10000000 if store=='payload'else 0x400000
        data=img.payload if store=='payload'else img.recon
        # End at the instruction after CALL VehicleRecord::Initialize.
        lea=bytes(data).find(b'\x8d\x8e'+struct.pack('<I',4+52*cid),at)
        assert bytes(data[lea+6:lea+7])==b'\xe8'
        u=machine(host,img);u.hook_add(UC_HOOK_CODE,hook);u.emu_start(base+at-50,base+lea+11,count=10000)
    assert set(result)==set(range(35))
    return result


def check_bonus2(host,img):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
    outcomes=[]
    # Follow the installed frontend bridge, including all existing SDK hooks,
    # rather than testing only the retail helper in isolation.
    assert img.recon[0x819ce]==0xe8
    entry=0x4819ce+5+struct.unpack_from('<i',img.recon,0x819cf)[0]
    for bonus,cars,allcars in ((False,False,False),(True,False,False),(False,True,False),(False,False,True)):
        u=machine(host,img);u.mem_write(0x21000004,struct.pack('<I',25));seen=[]
        def hook(u,at,size,user):
            if at not in (0x4b0310,0x4afea0,0x4afb70):return
            esp=u.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',u.mem_read(esp,4))[0]
            index=struct.unpack('<I',u.mem_read(esp+4,4))[0]
            if at==0x4b0310:pop=0;answer=0
            elif at==0x4afea0:pop=4;answer=int({0:cars,6:allcars}[index])
            else:pop=4;seen.append(index);assert index==15;answer=int(bonus)
            u.reg_write(UC_X86_REG_EAX,answer);u.reg_write(UC_X86_REG_ESP,esp+4+pop);u.reg_write(UC_X86_REG_EIP,ret)
        u.hook_add(UC_HOOK_CODE,hook);u.emu_start(entry,0x22000000,count=10000)
        actual=bool(u.reg_read(UC_X86_REG_EAX)&255);assert actual==(bonus or cars or allcars)
        outcomes.append({'Bonus2':bonus,'UnlockCars':cars,'UnlockAll':allcars,'allowed':actual,'flag_reads':seen})
    return outcomes


def verify(source,candidate,spec):
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.preview_scene import logical_cases
    from master_rallye.workshop.race_marker import normalized_rgb
    a,ai=native(source);b,bi=native(candidate)
    before=capture_initializers(source,ai);after=capture_initializers(candidate,bi)
    report={'status':'OFFLINE_VALIDATED','gameplay_tested':False,'record_count':35,'initializer_abi_cases':35,
            'stock_and_forester_colour_preserved':True,'changed_colours':[]}
    for cid in range(35):
        old,new=before[cid],after[cid];row=spec['markers'][cid]
        assert old['family']==new['family']==row['family']
        assert old['integers'][:6]==new['integers'][:6]
        assert new['integers'][6]==(23 if cid==29 else old['integers'][6])
        if cid<25 or cid==30:assert new['rgba_hex']==old['rgba_hex']
        if row.get('hex'):
            alpha=struct.unpack('<4f',bytes.fromhex(old['rgba_hex']))[3]
            assert new['rgba_hex']==struct.pack('<4f',*normalized_rgb(row['hex']),alpha).hex()
        if old['rgba_hex']!=new['rgba_hex']:report['changed_colours'].append(cid)
    ar,br=Resources(source),Resources(candidate)
    text=br.read('DataScene/FrontendScreens/VehicleSelect.xml').decode()
    import xml.etree.ElementTree as ET
    root=ET.fromstring(text)
    for egg in root.iter('Egg'):
        if not egg.attrib.get('Name','').startswith(('T1_Car','T2_Car','T3_Car')):continue
        values={v.attrib['Name']:v.attrib.get('Value') for v in egg.iter('Value')}
        if 'True Value'in values:assert values['True Value']==values['en2d Image Bank Index']
    s,e=egg_span(text,'T3_Car13');block=text[s:e]
    assert 'gaFrontendDisablerAI'in block and 'gaFrontendButtonUnlockerAI'in block and '/Bonus2'in block and '/Bonus1'not in block
    report['forklift_native_unlock']=check_bonus2(candidate,bi)
    for family in spec['brake_families']:
        rel=f'DataGx/Vehicles/{family}/car.dx';original=ar.read(rel);fixed=br.read(rel)
        x,y=parse_dx_bytes(original),parse_dx_bytes(fixed)
        assert x.vertices==y.vertices and x.uv_sets==y.uv_sets and x.local_indices==y.local_indices
        assert logical_cases(x)==logical_cases(y)
        diff=[i for i,(v,w)in enumerate(zip(original,fixed)) if v!=w]
        assert len(original)==len(fixed) and len(diff)==2
        expected=[d.core_offset+0x24 for d in x.physical_draws if any('breaklightson'in t for t in d.texture_tuple)]
        assert diff==expected and all(original[i]==5 and fixed[i]==1 for i in diff)
    # Existing operations are byte-identical outside identified colour/icon fields;
    # new operations must be exact original preimages with no overlapping owners.
    allowed=set();payload_allowed=set()
    for cid in report['changed_colours']:
        for store,at,_ in marker_slots(ai)[cid][:3]:
            (allowed if store=='file'else payload_allowed).update(range(at,at+4))
    store,at,size=record_pushes(ai,29)[0]
    (allowed if store=='file'else payload_allowed).update(range(at,at+size))
    assert all(i in allowed for i,(v,w)in enumerate(zip(ai.recon,bi.recon)) if v!=w)
    assert len(ai.payload)==len(bi.payload)
    assert all(i in payload_allowed for i,(v,w)in enumerate(zip(ai.payload,bi.payload)) if v!=w)
    native_ranges=[]
    for op in bi.rvp.ops:
        if op['flags']==1:continue
        assert (source/'MRallye.exe').read_bytes()[op['fo']:op['fo']+op['len']]==op['before']
        native_ranges.append((op['rva'],op['rva']+op['len']))
    native_ranges.sort();assert all(left[1]<=right[0] for left,right in zip(native_ranges,native_ranges[1:]))
    assert a[100:144]==b[100:144] and a[20:96]==b[20:96]
    source_files={p.relative_to(source):sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    changed=[]
    for rel,digest in source_files.items():
        p=candidate/rel
        if p.is_file() and sha(p.read_bytes())!=digest:changed.append(rel.as_posix())
    expected_changes={'MRMods/Vehicles/active/roster.mrvr','MRMods/Vehicles/active/catalog.json',
                      'MRMods/Vehicles/active/resources/DataScene/FrontendScreens/VehicleSelect.xml',
                      *[f'MRMods/Vehicles/active/resources/DataGx/Vehicles/{f}/car.dx'for f in spec['brake_families']]}
    assert set(changed)==expected_changes,(set(changed)^expected_changes)
    report['changed_host_files']=changed
    report['roster_sha256']=sha(b);report['initializers']=after
    (candidate/'vehicle-presentation-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return {k:v for k,v in report.items() if k!='initializers'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-host',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--sdk',type=Path,required=True);p.add_argument('--spec',type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.sdk.resolve()/'src'))
    print(json.dumps(verify(a.source_host,a.candidate,json.loads(a.spec.read_text())),indent=2))
