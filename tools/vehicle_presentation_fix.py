"""Derive a presentation-only MRVR candidate from the actual active host.

Preserves the installed transaction, class maps, physics and DLLs. Never uses
the (possibly older) source_runtime named by catalog.json to rebuild a roster.
Run with Python 3.11, Pillow and Capstone, and the current Vehicle SDK source.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, struct, sys, zlib
from pathlib import Path
import xml.etree.ElementTree as ET
from roster_v4 import Image as NativeImage, Rvp, record_pushes, write_push, egg_span
from vehicle_roster_build import archive_index, fnv64


def sha(b): return hashlib.sha256(b).hexdigest()


class Resources:
    def __init__(self, host):
        self.host = host
        self.active = host / 'MRMods/Vehicles/active'
        self.blob, self.members = archive_index(host / 'Data.sma')

    def read(self, rel):
        for root in (self.active / 'resources', self.host):
            p = root / rel
            if p.is_file(): return p.read_bytes()
        method, at, size, _ = self.members[rel.replace('\\', '/').lower()]
        data = self.blob[at:at + size]
        return data if method == 0 else zlib.decompress(data, -15)


def marker_slots(img):
    """Locate original compiler immediates and SDK-authored tail floats.

    Immediate offsets come from decoded x86 instructions, not float-byte search.
    The native initializer ABI is unchanged: seven integers, a string, RGBA.
    """
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_ESP
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
    slots = {}; previous = 0
    ins = list(md.disasm(bytes(img.recon[0x58e70:0x598d0]), 0x458e70))
    for n, i in enumerate(ins):
        if i.mnemonic != 'call' or i.op_str != '0x45a0b0': continue
        pushes = ins[n-8:n-1]
        if len(pushes) != 7 or any(p.mnemonic != 'push' or p.operands[0].type != X86_OP_IMM for p in pushes):
            raise ValueError('unexpected stock initializer arguments')
        cid = pushes[-1].operands[0].imm
        floats = [p for p in ins[previous:n-8] if p.mnemonic == 'mov' and len(p.operands) == 2
                  and p.operands[0].type == X86_OP_MEM and p.operands[0].mem.base == X86_REG_ESP
                  and p.operands[1].type == X86_OP_IMM]
        offsets = [p.operands[0].mem.disp for p in floats]
        if len(floats) != 4 or offsets not in ([0x18,0x1c,0x20,0x24],[8,12,16,20],[8,12,32,36]):
            raise ValueError(f'stock colour ABI changed for {cid}')
        slots[cid] = [('file', p.address - 0x400000 + p.imm_offset, 4) for p in floats]
        previous = n + 1
    if set(slots) != set(range(25)): raise ValueError('stock initializer coverage changed')
    count = 35
    # Current candidate has records 0..34; caller checks count before this.
    for cid in range(25, count):
        store, at, _ = record_pushes(img,cid)[0]
        data = img.payload if store == 'payload' else img.recon
        # SUB ESP,16 followed by four MOV [ESP+disp8],imm32.
        start = at - 47
        if bytes(data[start-3:start]) != b'\x83\xec\x10': raise ValueError(f'no colour preamble for {cid}')
        rows = []
        for index in range(4):
            pos = start + index*8
            if bytes(data[pos:pos+4]) != b'\xc7\x44\x24' + bytes([index*4]):
                raise ValueError(f'RGBA writer changed for {cid}')
            rows.append((store,pos+4,4))
        slots[cid] = rows
    return slots


def build(source, output, sdk, spec):
    from PIL import Image, ImageDraw
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.r4e_writer import patch_dx_attributes
    from master_rallye.workshop.race_marker import normalized_rgb, colour_info
    from master_rallye.addon_sdk.ui_assets import parse_bank
    from master_rallye.dxt import parse_dxt_bytes, decode_rgba_pixels
    source, output = source.resolve(), output.resolve()
    if output.exists(): raise ValueError('output must be a new directory')
    if source == output or source in output.parents: raise ValueError('output must be outside source')
    resources = Resources(source); raw = (resources.active/'roster.mrvr').read_bytes()
    if raw[:4] != b'MRVR' or struct.unpack_from('<I',raw,4)[0] != 1: raise ValueError('MRVR v1 required')
    ro,rl,po,pl = struct.unpack_from('<4I',raw,144)
    if fnv64(raw[256:]) != struct.unpack_from('<Q',raw,160)[0]: raise ValueError('MRVR damaged')
    count = struct.unpack_from('<I',raw,168)[0]
    if count != 35: raise ValueError('this reviewed presentation spec covers the current 35 records')
    img = NativeImage(raw[po:po+pl],Rvp(raw[ro:ro+rl]),[],(source/'MRallye.exe').read_bytes())
    changes = {}; report = {'schema':'mr-vehicle-presentation-fix/1','source':str(source),'sdk':str(sdk),
                           'source_roster_sha256':sha(raw),'runtime_tested':False,'changes':[]}

    def resource(rel, data):
        before = resources.read(rel)
        if data != before:
            changes[rel] = data
            report['changes'].append({'path':rel,'before_sha256':sha(before),'after_sha256':sha(data)})

    # Use the owner's identified stock SIDE frame; no icon resampling or bank mutation.
    old_icon = record_pushes(img, spec['trooper_id'])[0]
    write_push(img,old_icon,spec['trooper_side_frame'])
    bank = parse_bank(resources.read('DataGx/Frontend/RaceResults/smallcarsheet.dxb'))
    if not 0 <= spec['trooper_side_frame'] < bank['count']: raise ValueError('missing Trooper SIDE frame')

    rel = 'DataScene/FrontendScreens/VehicleSelect.xml'
    text = resources.read(rel).decode('utf-8')
    counts_va,ptrs_va = struct.unpack_from('<2I',raw,128)
    counts = struct.unpack('<3I',img.read(counts_va,12)); ptrs = struct.unpack('<3I',img.read(ptrs_va,12))
    maps = {c:list(struct.unpack(f'<{counts[i]}I',img.read(ptrs[i],counts[i]*4))) for i,c in enumerate(('T1','T2','T3'))}
    report['classes'] = maps; report['menu_repairs'] = []
    for cls, ids in maps.items():
        for local,cid in enumerate(ids):
            name = f'{cls}_Car{local+1}'; start,end = egg_span(text,name); block = text[start:end]
            frame = re.search(r'Name="en2d Image Bank Index" Type="Int" Value="(\d+)"',block).group(1)
            before = block
            block = re.sub(r'(Name="True Value" Type="Int" Value=")\d+("\s*/>)',rf'\g<1>{frame}\2',block)
            if cid == spec['forklift_id']:
                # The native ID25 unlock owner asks Progress/UnlockedCars/Bonus2.
                # Reuse the stock Bonus1 button controllers, changing only flag and frame.
                ts,te = egg_span(text,'T3_Car12'); template = text[ts:te]
                for no in (0,3):
                    pattern = rf'<AI No="{no}">.*?</AI>'
                    ai = re.search(pattern,template,re.S).group().replace('/Bonus1','/Bonus2')
                    ai = re.sub(r'(Name="True Value" Type="Int" Value=")\d+("\s*/>)',rf'\g<1>{frame}\2',ai)
                    block = re.sub(pattern,lambda _:ai,block,flags=re.S)
            if block != before:
                report['menu_repairs'].append({'id':cid,'widget':name,'active_frame':int(frame)})
                text = text[:start] + block + text[end:]
    ET.fromstring(text)
    resource(rel,text.encode('utf-8'))

    # Correct only the environment bit on existing unlit brake core/halo draws.
    # The secondary sampler name is retained for byte-layout compatibility; it
    # is inactive with the environment feature disabled, as on stock lamps.
    report['brakes'] = []
    for family in spec['brake_families']:
        rel = f'DataGx/Vehicles/{family}/car.dx'; before = resources.read(rel); m = parse_dx_bytes(before)
        targets = [d.draw_index for d in m.physical_draws if not d.flags_0x20[2]
                   and any('breaklightson' in t.casefold() for t in d.texture_tuple) and d.unknown_0x24 & 4]
        if len(targets) != 2: raise ValueError(f'{family}: expected existing lit core and halo')
        patch = patch_dx_attributes(before,material_env={i:False for i in targets},source=rel)
        resource(rel,patch.data)
        report['brakes'].append({'family':family,'draws':targets,**patch.to_dict()})

    slots = marker_slots(img); report['markers'] = []
    for cid, row in enumerate(spec['markers']):
        if row['id'] != cid: raise ValueError('palette must cover each physical ID exactly once')
        fields = slots[cid]
        value = lambda s: struct.unpack_from('<f',img.payload if s[0]=='payload' else img.recon,s[1])[0]
        old = [value(s) for s in fields]
        rgb = normalized_rgb(row['hex']) if row.get('hex') else old[:3]
        new = [*rgb,old[3]]
        for slot,v in zip(fields,new):
            bits = struct.unpack('<I',struct.pack('<f',v))[0]
            store,at,width = slot
            if store == 'payload': struct.pack_into('<I',img.payload,at,bits)
            else:
                # Existing RVP ownership wins. Otherwise add an exact-preimage
                # original code-field operation, not a whole-function overwrite.
                encoded = struct.pack('<I',bits)
                # Sparse old operations can cover only part of an immediate.
                # Edit their owned bytes individually; never add an overlapping
                # four-byte operation over such a previous owner.
                for index,byte in enumerate(encoded):
                    pos=at+index
                    if img.recon[pos]==byte: continue
                    owned=next((o for o in img.rvp.ops if o['flags']!=1 and o['fo']<=pos<o['fo']+o['len']),None)
                    if owned: owned['after'][pos-owned['fo']]=byte
                    else: img.rvp.ops.append({'fo':pos,'rva':pos,'len':1,'flags':0,'page':1,'before':img.exe[pos:pos+1],'after':bytearray([byte])})
                    img.recon[pos]=byte
        report['markers'].append({**row,'original':colour_info(old),'current':colour_info(new),'changed':old!=new})

    rvp = img.rvp.build(); header = bytearray(raw[:256])
    if len(img.payload) != pl: raise ValueError('presentation changes must not resize native storage')
    struct.pack_into('<4I',header,144,256,len(rvp),256+len(rvp),pl)
    struct.pack_into('<Q',header,160,fnv64(rvp+img.payload))
    label = b'Roster V4 presentation fix 01'; header[176:256]=label+b'\0'*(80-len(label))
    fixed = bytes(header)+rvp+img.payload
    if header[100:144] != raw[100:144]: raise ValueError('MRVC ABI changed')
    # Fresh host: immutable archive alone is hardlinked; all mutable files are
    # independent copies. In particular saves, options and source overlay stay intact.
    output.mkdir(parents=True)
    for p in source.rglob('*'):
        relp = p.relative_to(source)
        if 'active.prev' in relp.parts or 'logs' in relp.parts or p.suffix.lower() in ('.log','.bin') and 'MRMods' not in relp.parts: continue
        dst = output/relp
        if p.is_dir(): dst.mkdir(parents=True,exist_ok=True)
        else:
            dst.parent.mkdir(parents=True,exist_ok=True)
            if relp == Path('Data.sma'): os.link(p,dst)
            else: shutil.copy2(p,dst)
    target = output/'MRMods/Vehicles/active'
    for rel,data in changes.items():
        p = target/'resources'/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
    (target/'roster.mrvr').write_bytes(fixed)
    catalog = json.loads((target/'catalog.json').read_text())
    catalog.update(label=label.decode(),classes=maps,roster_mrvr_sha256=sha(fixed),native_patch_operations_sha256=sha(rvp),
                   native_extension_sha256=sha(bytes(img.payload)),source_active_roster_sha256=sha(raw))
    catalog['resources']=[{'path':p.relative_to(target/'resources').as_posix(),'size':p.stat().st_size,'sha256':sha(p.read_bytes())}
                          for p in sorted((target/'resources').rglob('*')) if p.is_file()]
    (target/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
    report['output_roster_sha256']=sha(fixed); report['operations_before']=len(Rvp(raw[ro:ro+rl]).ops); report['operations_after']=len(img.rvp.ops)
    report['native_abi']='MRVR v1 / RVP1 / MRVC v1; 52-byte vehicle records; unchanged class maps and payload size'
    report['dlls']={n:sha((source/n).read_bytes()) for n in ('dinput8.dll','d3d8.dll','MRallye.exe')}
    if any(sha((output/n).read_bytes())!=v for n,v in report['dlls'].items()): raise ValueError('binary changed')
    (output/'vehicle-presentation-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    # Visual audit of every record, including reserved/non-menu ID34.
    contact = Image.new('RGB',(800,120*9),(45,45,45)); draw=ImageDraw.Draw(contact)
    frame_stock=[9,17,22,15,1,16,20,13,4,7,24,19,14,26,3,25,0,5,11,10,2,27,6,8,28]
    for row in report['markers']:
        cid=row['id']; x=(cid%4)*200; y=(cid//4)*120
        frame=frame_stock[cid] if cid<25 else spec['side_frames'][str(cid)]
        tex=parse_dxt_bytes(resources.read('DataGx/Frontend/RaceResults/'+bank['names'][frame]+'.dxt'))
        icon=Image.frombytes('RGBA',(tex.width,tex.height),decode_rgba_pixels(tex)).resize((128,64),Image.Resampling.NEAREST)
        contact.paste(icon,(x+32,y+16),icon)
        draw.text((x+4,y+2),f"{cid} {row['family']}",fill='white')
        draw.rectangle((x+5,y+85,x+92,y+103),fill=row['original']['hex'])
        draw.rectangle((x+100,y+85,x+188,y+103),fill=row['current']['hex'])
        draw.text((x+5,y+106),'Original / '+row['current']['hex'],fill='white')
    contact.save(output/'progress-marker-palette.png')
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-host',type=Path,required=True); p.add_argument('--output-host',type=Path,required=True)
    p.add_argument('--sdk',type=Path,required=True); p.add_argument('--spec',type=Path,required=True)
    a=p.parse_args(); sys.path.insert(0,str(a.sdk.resolve()/'src'))
    result=build(a.source_host,a.output_host,a.sdk,json.loads(a.spec.read_text()))
    print(json.dumps({k:result[k] for k in ('output_roster_sha256','menu_repairs','operations_before','operations_after')},indent=2))
