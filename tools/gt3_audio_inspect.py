"""Bounded optional GT3 RoFS sound-event inventory; no game assets bundled.

GTSE tokens are preserved as opaque integers. Their bitfields and INST routing
are deliberately not promoted to qualified event/sample mappings.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
from gt3_ui_icon import read_member


def events(raw):
    if len(raw) < 16 or raw[:4] != b'GTSE':
        raise ValueError('GTSE header required')
    version, reserved, count = struct.unpack_from('<3I', raw, 4)
    if version != 1 or reserved or not 1 <= count <= 4096 or 16 + count * 8 > len(raw) or len(raw) > 1024 * 1024:
        raise ValueError('unsupported GTSE table')
    rows=[]; seen=set()
    for i in range(count):
        pointer, token = struct.unpack_from('<II',raw,16+i*8)
        if not 16+count*8 <= pointer < len(raw):
            raise ValueError('GTSE name outside string region')
        end=raw.find(b'\0',pointer)
        if end < 0 or end-pointer > 128:
            raise ValueError('invalid GTSE name')
        name=raw[pointer:end].decode('ascii')
        if not name or name in seen or any(ord(c)<32 or ord(c)>126 for c in name):
            raise ValueError('ambiguous GTSE name')
        seen.add(name);rows.append({'name':name,'token':f'0x{token:08x}','record_offset':16+i*8})
    return rows


def inspect(volume):
    raw, origin=read_member(volume,'sound/se.inf')
    banks=[]
    for member in ('sound/gt3se01.ins','sound/gt3se02.ins','sound/gt3sys.ins','sound/se01.ins','sound/sys.ins'):
        bank, evidence=read_member(volume,member)
        if bank[:4]!=b'INST' or len(bank)<40:
            raise ValueError('expected original INST member')
        banks.append({**evidence,'header40_hex':bank[:40].hex()})
    return {'format':'GT3 GTSE version1','source':origin,'events':events(raw),'banks':banks,
            'status':'NAMED_EVENTS_ONLY_NOT_QUALIFIED_SAMPLE_ROUTING',
            'boundary':'No sample decoded or selected by pitch/content. GT3 INST and runtime dispatch still require independent qualification.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--volume',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('output exists')
    result=inspect(a.volume);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'events':len(result['events']),'status':result['status']}))
