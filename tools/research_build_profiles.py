"""Exact INTERNAL Observatory identities and build-specific vehicle oracles.

Auditing never registers a build. No runtime writes or executable patching.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'research/r-observatory-modded-builds'
PRISTINE_SHA256 = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
MERC_SHA256 = '1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af'
SIZE = 3_121_214


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pe_layout(data):
    """Bounded PE32 inspection; reports unknown images without granting trust."""
    if len(data) < 0x100 or data[:2] != b'MZ':
        raise ValueError('Missing DOS header')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    if pe > len(data)-24 or data[pe:pe+4] != b'PE\0\0':
        raise ValueError('Missing PE header')
    machine, count, timestamp = struct.unpack_from('<HHI', data, pe+4)
    optional_size = struct.unpack_from('<H', data, pe+20)[0]
    opt = pe+24
    if machine != 0x14c or not 1 <= count <= 96 or optional_size < 96 or opt+optional_size+count*40 > len(data):
        raise ValueError('Invalid x86 PE headers')
    if struct.unpack_from('<H', data, opt)[0] != 0x10b:
        raise ValueError('Expected PE32')
    sections = []
    for i in range(count):
        at = opt+optional_size+i*40
        name = data[at:at+8].split(b'\0',1)[0].decode('ascii')
        vs, rva, size, raw = struct.unpack_from('<IIII', data, at+8)
        flags = struct.unpack_from('<I', data, at+36)[0]
        if size and (raw > len(data) or size > len(data)-raw):
            raise ValueError('Section extends beyond file')
        sections.append(dict(name=name, virtual_size=vs, rva=rva, raw_size=size,
                             raw_offset=raw, characteristics=flags))
    return dict(machine=machine, timestamp=timestamp,
                pe_header_sha256=digest(data[pe:opt+optional_size+count*40]),
                image_base=struct.unpack_from('<I',data,opt+28)[0],
                size_of_image=struct.unpack_from('<I',data,opt+56)[0],
                entry_rva=struct.unpack_from('<I',data,opt+16)[0], sections=sections)


def window(data, pe, va, length):
    rva = va-pe['image_base']
    for section in pe['sections']:
        if section['rva'] <= rva and rva+length <= section['rva']+section['raw_size']:
            start = section['raw_offset']+rva-section['rva']
            return data[start:start+length], section['name'], start
        if section['rva'] <= rva and rva+length <= section['rva']+section['virtual_size']:
            # PE zero-filled tail, not a runtime pointer read. The corresponding
            # accessor/logger fingerprints establish the slot's native owner.
            delta=rva-section['rva']
            backed=max(0,min(length,section['raw_size']-delta))
            start=section['raw_offset']+delta
            return data[start:start+backed]+bytes(length-backed),section['name'],None
    raise ValueError('Anchor outside file-backed section')


def definitions():
    return json.loads((EVIDENCE/'build-profiles.json').read_text(encoding='utf-8'))


def audit_build(data):
    pe = pe_layout(data)
    canonical = definitions()
    reference = canonical['retail_pe']
    layout_match = all(pe[k] == reference[k] for k in ('machine','timestamp','image_base','size_of_image','entry_rva'))
    # Unknown text extension is reported, never auto-trusted. All other section
    # locations/flags/extent must remain identical to the audited retail layout.
    actual_sections = [dict(s,virtual_size=0) if s['name']=='.text' else s for s in pe['sections']]
    expected_sections = [dict(s,virtual_size=0) if s['name']=='.text' else s for s in reference['sections']]
    layout_match &= actual_sections == expected_sections
    text = next((s for s in pe['sections'] if s['name']=='.text'),None)
    layout_match &= bool(text and text['virtual_size'] <= text['raw_size'])
    anchors=[]
    for anchor in canonical['anchors']:
        try:
            raw, section, offset = window(data,pe,anchor['va'],anchor['length'])
            observed = digest(raw)
            match = observed == anchor['sha256'] and section == anchor['section']
        except ValueError:
            observed, section, offset, match = None,None,None,False
        anchors.append(dict(name=anchor['name'],va=anchor['va'],rva=anchor['va']-pe['image_base'],
                            length=anchor['length'],section=section,file_offset=offset,
                            sha256=observed,compatible=match,semantics=anchor['semantics']))
    h=digest(data)
    registered=next((p for p in canonical['profiles'] if p['sha256']==h and p['size']==len(data)),None)
    compatible=layout_match and all(a['compatible'] for a in anchors)
    return dict(schema_version=1,sha256=h,size=len(data),pe=pe,layout_compatible=layout_match,
                anchors=anchors,anchor_compatible=compatible,
                status='ANCHOR_COMPATIBLE_ONLY' if compatible else 'INCOMPATIBLE',
                exact_registered_profile=registered['profile'] if registered else None,
                automatic_trust=False,runtime_full_pass=False,
                audit_does_not_register=True)


def identify(data):
    # Identity gate precedes anchor work. Matching anchors cannot admit unknowns.
    h=digest(data)
    profile=next((p for p in definitions()['profiles'] if p['sha256']==h and p['size']==len(data)),None)
    if profile is None:
        raise ValueError('Unknown executable hash/size; exact registered builds only')
    audit=audit_build(data)
    if not audit['anchor_compatible'] or audit['pe'] != profile['pe']:
        raise ValueError('Registered build failed layout/anchor verification')
    return profile


def registry(profile):
    """Committed profile, never a registry supplied by a runtime capture."""
    known=next((p for p in definitions()['profiles'] if p['profile']==profile),None)
    if known is None:
        raise ValueError('Unknown registry build profile')
    maps=json.loads((EVIDENCE/'registry-profile.json').read_text(encoding='utf-8'))
    stock=json.loads((ROOT/'research/r-ai1/vehicle-class-map.json').read_text(encoding='utf-8'))
    if stock['source_sha256']!=PRISTINE_SHA256:
        raise ValueError('Wrong canonical pristine vehicle map')
    rows={r['id']:dict(id=r['id'],**{'class':r['class']},tier=r['class_name'],
                       local_index=r['local_index'],identity=r['display_name'],
                       CarType=r['family'],WheelType=r['family'],
                       availability='Existing stock availability; class/frontend reachability separate',
                       evidence=r['evidence']) for r in stock['records']}
    for row in maps['registries'][known['vehicle_registry_profile']]['additional_records']:
        if row['id'] in rows:raise ValueError('Extra record would overwrite a stock ID')
        rows[row['id']]=row
    return rows


def vehicle(profile, id):
    if type(id) is not int or id not in registry(profile):
        raise ValueError('Vehicle ID invalid for this build registry')
    return dict(registry(profile)[id])


def absolute_id(profile, cls, local):
    if type(cls) is not int or type(local) is not int:
        raise ValueError('Class/local must be integers')
    matches=[r['id'] for r in registry(profile).values() if r['class']==cls and r['local_index']==local]
    if len(matches)!=1:
        raise ValueError('Invalid or ambiguous class-local entry')
    return matches[0]


def check_vehicle(snapshot, profile, slot, expected_id=None):
    """JSON/raw integrity must be checked by caller; state is not actor proof."""
    known=next((p for p in definitions()['profiles'] if p['profile']==profile),None)
    if known is None:raise ValueError('Unknown exact capture profile')
    source=snapshot.get('source',{})
    if (snapshot.get('kind')!='master-rallye-broker-dump-snapshot' or snapshot.get('schema_version')!=1
        or source.get('image_sha256')!=known['sha256'] or source.get('image_size')!=known['size']
        or source.get('build_profile')!=profile or source.get('freshness')!='post_baseline_complete_dump_proven'
        or source.get('broker_dump_variant')!='native_stock'):
        raise ValueError('Capture profile/identity/freshness mismatch')
    if source.get('label') not in ('merc-profile-stock-race','merc-id26-race','stock-profile-race'):
        raise ValueError('Use a known active-race lifecycle label, never Results')
    values={}
    for entry in snapshot['entries']:
        if entry['path'] in values:raise ValueError('Duplicate capture path')
        values[entry['path']]=entry.get('value')
    def get(path):
        if path not in values:raise ValueError('Missing '+path)
        return values[path]
    if type(slot) is not int or slot<0:raise ValueError('Invalid slot')
    # This compatibility handoff is the unchanged four-car first offline race.
    for path,wanted in {'Race/NumCars':4,'Race/NumPlayers':1,'Race/Type':2,
                        'Race/AttractMode':False,'Race/PlaybackReplay':False,
                        'Race/NumNetworkPlayers':0}.items():
        value=get(path)
        if type(value)!=type(wanted) or value!=wanted:raise ValueError('Not a fresh ordinary four-car active race')
    if slot>=4:raise ValueError('Slot outside active participants')
    participants=[]
    for n in range(4):
        prefix=f'Race/Car{n}/'
        id=get(prefix+'CarID');record=vehicle(profile,id)
        cls=get(prefix+'CarClass')
        if type(cls) is not int or cls!=record['class']:raise ValueError('CarID/Class registry mismatch')
        typ=get(prefix+'PlayerType');driver=get(prefix+'DriverID')
        if type(typ) is not int or typ!=(1 if n==0 else 2):raise ValueError('Human/AI mismatch')
        if type(driver) is not int or (driver!=30 if n==0 else not 0<=driver<=9):raise ValueError('Invalid driver')
        for field in ('CarType','WheelType'):
            actual=get(prefix+field);wanted=record[field]
            if not isinstance(actual,str) or (wanted is not None and actual.casefold()!=wanted.casefold()):
                raise ValueError('Runtime family mismatch: '+field)
        participants.append(dict(slot=n,id=id,**{'class':cls},DriverID=driver,PlayerType=typ))
    if len({p['id'] for p in participants})!=4 or len({p['DriverID'] for p in participants[1:]})!=3:
        raise ValueError('Duplicate ordinary Quick Race vehicle/driver identity')
    chosen=participants[slot]
    if expected_id is not None and chosen['id']!=expected_id:raise ValueError('Unexpected target Vehicle ID')
    for prefix in ('Vehicles','Physics'):
        if not any(p.startswith(f'{prefix}/Car{slot}/') for p in values):raise ValueError('Missing materialization state')
    return dict(status='BROKER_STATE_MATCH_ONLY',runtime_full_pass=False,profile=profile,
                participant=chosen,participants=participants,registry_entry=vehicle(profile,chosen['id']),
                physics_canaries=None,physics_canary_status='No Mercedes constants established in this phase',
                actor_visibility_proven=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for command in ('audit-build','verify-build','check-vehicle'):
        p=sub.add_parser(command);p.add_argument('exe',type=Path)
        p.add_argument('--output',type=Path)
        if command=='check-vehicle':
            p.add_argument('capture',type=Path);p.add_argument('--slot',type=int,default=0)
            p.add_argument('--expected-id',type=int);p.add_argument('--observatory',type=Path,required=True)
    args=parser.parse_args()
    if args.exe.stat().st_size>64*1024*1024:raise ValueError('Audit input exceeds bounded64MiB size')
    data=args.exe.read_bytes()
    if args.command=='audit-build':report=audit_build(data)
    elif args.command=='verify-build':report=identify(data)
    else:
        profile=identify(data)
        from r_ai1_observe import load_profile
        from r_ai1_mixed_class import verify_capture
        observe=load_profile(args.observatory,args.exe)
        snapshot=json.loads(args.capture.read_text(encoding='utf-8'))
        raw=args.capture.with_suffix('.dump.bin').read_bytes()
        verify_capture(snapshot,raw,observe.core.parse_dump_bytes)
        report=check_vehicle(snapshot,profile['profile'],args.slot,args.expected_id)
    if args.output:
        from r_ai1_mixed_class import ignored_output
        path=ignored_output(args.output);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
