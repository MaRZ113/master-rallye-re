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
AUDIT_VERSION = 'retail-broker-v1.0'
PROFILE_SCHEMA_VERSION = 1
PROFILE_CACHE_ROOT = ROOT / '.research-output/observatory/build-profiles'


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


def registry_definitions():
    return json.loads((EVIDENCE/'registry-profile.json').read_text(encoding='utf-8'))


def _family_layout_matches(pe, reference):
    layout_match = all(pe[k] == reference[k] for k in ('machine', 'timestamp', 'image_base', 'size_of_image', 'entry_rva'))
    actual_sections = [dict(s, virtual_size=0) if s['name'] == '.text' else s for s in pe['sections']]
    expected_sections = [dict(s, virtual_size=0) if s['name'] == '.text' else s for s in reference['sections']]
    layout_match &= actual_sections == expected_sections
    text = next((s for s in pe['sections'] if s['name'] == '.text'), None)
    rdata = next((s for s in pe['sections'] if s['name'] == '.rdata'), None)
    layout_match &= bool(text and text['virtual_size'] <= text['raw_size']
                         and (rdata is None or text['rva'] + text['virtual_size'] <= rdata['rva']))
    return bool(layout_match)


def _registry_profile_for(data, pe, exact_profile):
    if exact_profile:
        return exact_profile.get('vehicle_registry_profile', 'unknown'), 'committed_exact'
    maps = registry_definitions()
    for profile, markers in maps.get('detection_fingerprints', {}).items():
        matches = True
        for marker in markers:
            try:
                raw, section, _ = window(data, pe, marker['va'], marker['length'])
                matches &= section == marker['section'] and digest(raw) == marker['sha256']
            except (KeyError, ValueError):
                matches = False
        if matches:
            return profile, 'structural_fingerprint'
    return 'unknown', 'unrecognized'


def _audit_fingerprint(audit):
    canonical = {
        'audit_version': AUDIT_VERSION,
        'family': audit.get('compatibility_family'),
        'layout_compatible': audit.get('layout_compatible'),
        'anchors': [(a['name'], a.get('sha256'), a.get('compatible')) for a in audit.get('anchors', [])],
        'capabilities': audit.get('capabilities', {}),
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return digest(raw)


def _profile_document(audit, *, exact_profile=None, registry_profile=None, registry_origin=None):
    origin = 'committed_exact' if exact_profile else 'locally_audited'
    profile_id = exact_profile['profile'] if exact_profile else 'local-audited-' + audit['sha256'][:12]
    family = audit.get('compatibility_family')
    caps = dict(audit.get('capabilities', {}))
    reg = registry_profile if registry_profile is not None else audit.get('registry_profile', 'unknown')
    caps['vehicle_registry_profile'] = reg
    return {
        'schema_version': PROFILE_SCHEMA_VERSION,
        'sha256': audit['sha256'],
        'size': audit['size'],
        'profile_id': profile_id,
        'profile_origin': origin,
        'compatibility_family': family,
        'audit_version': AUDIT_VERSION,
        'audit_fingerprint': _audit_fingerprint(audit),
        'vehicle_registry_profile': reg,
        'registry_profile_origin': registry_origin or ('committed_exact' if exact_profile else 'structural_fingerprint' if reg != 'unknown' else 'unrecognized'),
        'capabilities': caps,
        'pe_identity': {key: audit['pe'][key] for key in ('machine', 'image_base', 'size_of_image', 'entry_rva')},
    }


def _cache_path(root, image_hash):
    root = Path(root).resolve()
    if root.name != 'build-profiles':
        raise ValueError('Profile cache must use a build-profiles directory')
    return root / (image_hash + '.json')


def _load_valid_cache(path, audit):
    try:
        cached = json.loads(path.read_text(encoding='utf-8'))
        expected = _profile_document(audit, registry_profile=audit.get('registry_profile'),
                                     registry_origin=audit.get('registry_profile_origin'))
        return cached if cached == expected else None
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        return None


def _write_cache(path, profile):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(profile, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def audit_build(data):
    pe = pe_layout(data)
    canonical = definitions()
    reference = canonical['retail_pe']
    layout_match = _family_layout_matches(pe, reference)
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
    families = canonical.get('families', {})
    family_id = next((name for name, family in families.items()
                      if family.get('pe_reference') == 'retail_pe'),
                     'retail-broker-v1' if not families else None)
    family = families.get(family_id, {})
    required = set(family.get('anchor_names', [a['name'] for a in canonical['anchors']]))
    by_name = {a['name']: a for a in anchors}
    required_anchors_match = bool(required) and all(by_name.get(name, {}).get('compatible') for name in required)
    compatible=layout_match and required_anchors_match
    registry_profile, registry_origin = _registry_profile_for(data, pe, registered)
    capabilities = dict(family.get('capabilities', {})) if compatible else {}
    # Capabilities are derived only from matching anchors, never from a build name.
    dump_anchor = by_name.get('native_dump_walker', {}).get('compatible', False)
    route_anchor = by_name.get('broker_editor_dump_route', {}).get('compatible', False)
    broker_anchor_set = all(by_name.get(name, {}).get('compatible', False) for name in (
        'broker_editor_dump_route', 'broker_singleton_accessor', 'debug_logger', 'debug_sink_vtable',
        'debug_sink_global', 'broker_manager_global', 'main_loop'))
    capabilities['broker_read'] = bool(compatible and broker_anchor_set)
    capabilities['open_broker_editor'] = bool(compatible and route_anchor)
    capabilities['native_dump'] = bool(compatible and route_anchor and dump_anchor)
    capabilities['broker_capture_active_race'] = bool(capabilities['native_dump'])
    capabilities['active_race_native_dump_safe'] = bool(capabilities['native_dump'])
    capabilities['post_results_native_dump_safe'] = False if dump_anchor else None
    capabilities['hardened_dump'] = False
    capabilities['flow_builder'] = False
    capabilities['legacy_loading_attract_present'] = bool(by_name.get('loading_legacy_failure', {}).get('compatible'))
    capabilities['broker_dump_variant'] = 'native_stock' if dump_anchor else 'unknown'
    return dict(schema_version=1,sha256=h,size=len(data),pe=pe,layout_compatible=layout_match,
                anchors=anchors,anchor_compatible=compatible,
                status='ANCHOR_COMPATIBLE_ONLY' if compatible else 'INCOMPATIBLE',
                compatibility_family=family_id if compatible else None,
                family_anchor_names=sorted(required),
                family_anchor_compatible=required_anchors_match,
                registry_profile=registry_profile,
                registry_profile_origin=registry_origin,
                capabilities=capabilities,
                audit_version=AUDIT_VERSION,
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


def resolve_build(data, *, cache_root=None, write_local_profile=True):
    """Resolve exact identity first, otherwise audit and locally bind one family-compatible SHA."""
    audit = audit_build(data)
    exact = next((p for p in definitions()['profiles']
                  if p['sha256'] == audit['sha256'] and p['size'] == audit['size']), None)
    if exact:
        committed = identify(data)
        profile = _profile_document(audit, exact_profile=committed,
                                    registry_profile=committed['vehicle_registry_profile'],
                                    registry_origin='committed_exact')
        resolved = {**audit, **profile, 'local_profile_cache': None, 'cache_reused': False}
    else:
        if not audit['anchor_compatible'] or not audit.get('compatibility_family'):
            failures = [a['name'] for a in audit['anchors'] if not a['compatible']]
            raise ValueError('Unknown executable failed structural family audit: ' +
                             (', '.join(failures) if failures else 'PE/layout mismatch'))
        if not (audit['capabilities'].get('broker_read')
                and audit['capabilities'].get('open_broker_editor')
                and audit['capabilities'].get('native_dump')):
            raise ValueError('Compatible family lacks capabilities required for Broker capture')
        cache_root = Path(cache_root) if cache_root is not None else PROFILE_CACHE_ROOT
        path = _cache_path(cache_root, audit['sha256'])
        cached = _load_valid_cache(path, audit) if path.exists() else None
        profile = cached or _profile_document(audit)
        if write_local_profile and not cached:
            _write_cache(path, profile)
        resolved = {**audit, **profile, 'local_profile_cache': str(path), 'cache_reused': bool(cached)}
    family_name = resolved.get('compatibility_family')
    family = definitions().get('families', {}).get(family_name, {})
    exact_for_layout = next((p for p in definitions()['profiles']
                             if p['profile'] == family.get('observatory_layout_profile')), None)
    resolved['profile'] = resolved['profile_id']
    resolved['exact_profile_id'] = resolved.get('profile_id') if resolved['profile_origin'] == 'committed_exact' else None
    resolved['broker_dump_variant'] = resolved.get('capabilities', {}).get('broker_dump_variant', 'unknown')
    resolved['native_dump_post_results_safe'] = resolved.get('capabilities', {}).get('post_results_native_dump_safe')
    resolved['legacy_loading_attract_present'] = resolved.get('capabilities', {}).get('legacy_loading_attract_present')
    resolved['observatory'] = exact_for_layout.get('observatory') if exact_for_layout else None
    return resolved


def registry(profile):
    """Resolve a registry identity independently of the executable identity."""
    known=next((p for p in definitions()['profiles'] if p['profile']==profile),None)
    registry_name = known['vehicle_registry_profile'] if known else profile
    maps=json.loads((EVIDENCE/'registry-profile.json').read_text(encoding='utf-8'))
    if registry_name not in maps['registries']:
        raise ValueError('Unknown vehicle registry profile')
    stock=json.loads((ROOT/'research/r-ai1/vehicle-class-map.json').read_text(encoding='utf-8'))
    if stock['source_sha256']!=PRISTINE_SHA256:
        raise ValueError('Wrong canonical pristine vehicle map')
    rows={r['id']:dict(id=r['id'],**{'class':r['class']},tier=r['class_name'],
                       local_index=r['local_index'],identity=r['display_name'],
                       CarType=r['family'],WheelType=r['family'],
                       availability='Existing stock availability; class/frontend reachability separate',
                       evidence=r['evidence']) for r in stock['records']}
    for row in maps['registries'][registry_name]['additional_records']:
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


def _validate_capture_build_source(snapshot, build):
    source = snapshot.get('source', {})
    if (snapshot.get('kind') != 'master-rallye-broker-dump-snapshot'
            or snapshot.get('schema_version') != 1
            or source.get('image_sha256', source.get('exe_sha256')) != build['sha256']
            or source.get('image_size', source.get('exe_size')) != build['size']):
        raise ValueError('Capture executable identity mismatch')
    if build['profile_origin'] == 'locally_audited':
        if source.get('build_profile') != build['profile_id']:
            raise ValueError('Capture local profile ID mismatch')
        for key, expected in (
            ('profile_origin', 'locally_audited'),
            ('compatibility_family', build['compatibility_family']),
            ('audit_version', build['audit_version']),
            ('audit_fingerprint', build['audit_fingerprint']),
            ('vehicle_registry_profile', build['vehicle_registry_profile']),
        ):
            if source.get(key) != expected:
                raise ValueError('Capture provenance mismatch: ' + key)
    elif source.get('build_profile') != build['profile_id']:
        # Older exact captures use build_profile as the canonical profile ID.
        raise ValueError('Capture exact profile mismatch')
    if source.get('compatibility_family') not in (None, build['compatibility_family']):
        raise ValueError('Capture compatibility family mismatch')
    return source


def check_broker_capture(snapshot, build):
    """Validate generic Broker provenance without making registry semantics claims."""
    if build.get('compatibility_family') not in definitions().get('families', {}):
        raise ValueError('Unknown compatibility family')
    if not build.get('capabilities', {}).get('broker_capture_active_race'):
        raise ValueError('Build profile lacks active-race Broker capture capability')
    source = _validate_capture_build_source(snapshot, build)
    values = {}
    for entry in snapshot.get('entries', []):
        path = entry.get('path')
        if not isinstance(path, str) or path in values:
            raise ValueError('Invalid or duplicate Broker path')
        values[path] = entry.get('value')
    count = values.get('Race/NumCars')
    if type(count) is not int or not 1 <= count <= 64:
        raise ValueError('Missing or invalid Race/NumCars')
    rows = []
    for slot in range(count):
        key = f'Race/Car{slot}/CarID'
        if key not in values or type(values[key]) is not int or values[key] < 0:
            raise ValueError('Missing or invalid raw CarID: ' + key)
        player_key = f'Race/Car{slot}/PlayerType'
        if player_key in values and (type(values[player_key]) is not int or values[player_key] not in (1, 2)):
            raise ValueError('Invalid PlayerType: ' + player_key)
        rows.append(dict(slot=slot, CarID=values[key],
                         PlayerType=values.get(player_key)))
    return dict(status='BROKER_STRUCTURE_MATCH_ONLY', runtime_full_pass=False,
                exact_profile_id=build.get('profile_id'),
                profile_origin=build['profile_origin'],
                compatibility_family=build['compatibility_family'],
                vehicle_registry_profile=build.get('vehicle_registry_profile', 'unknown'),
                vehicle_semantics='NOT_CHECKED' if build.get('vehicle_registry_profile') == 'unknown' else 'AVAILABLE_TO_REGISTRY_CHECKER',
                participants=rows, capture_label=source.get('label'))


def check_vehicle(snapshot, profile, slot, expected_id=None):
    """JSON/raw integrity must be checked by caller; Broker state is not actor proof."""
    if isinstance(profile, str):
        known = next((p for p in definitions()['profiles'] if p['profile'] == profile), None)
        if known is None:
            raise ValueError('Unknown exact capture profile')
        build = {
            'sha256': known['sha256'], 'size': known['size'], 'profile_id': known['profile'],
            'profile_origin': 'committed_exact', 'compatibility_family': known['compatibility_family'],
            'audit_version': AUDIT_VERSION, 'audit_fingerprint': None,
            'vehicle_registry_profile': known['vehicle_registry_profile'],
            'capabilities': known['capabilities'],
        }
    elif isinstance(profile, dict):
        build = profile
    else:
        raise ValueError('Invalid resolved build profile')
    registry_name = build.get('vehicle_registry_profile', 'unknown')
    if registry_name == 'unknown':
        raise ValueError('UNKNOWN_REGISTRY_PROFILE: generic Broker state is valid, but vehicle semantics are unavailable')
    known = next((p for p in definitions()['profiles'] if p['profile'] == build['profile_id']), None)
    if build['profile_origin'] == 'committed_exact' and known is None:
        raise ValueError('Invalid committed exact build profile')
    _validate_capture_build_source(snapshot, build)
    source=snapshot.get('source',{})
    if (source.get('freshness')!='post_baseline_complete_dump_proven'
        or source.get('broker_dump_variant')!='native_stock'):
        raise ValueError('Capture profile/identity/freshness mismatch')
    if source.get('label') not in ('merc-profile-stock-race','merc-id26-race','stock-profile-race',
                                   'mercv2-stock-race','mercv2-id26-race'):
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
        id=get(prefix+'CarID');record=vehicle(registry_name,id)
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
    return dict(status='BROKER_STATE_MATCH_ONLY',runtime_full_pass=False,profile=build['profile_id'],
                participant=chosen,participants=participants,registry_entry=vehicle(registry_name,chosen['id']),
                physics_canaries=None,physics_canary_status='No Mercedes constants established in this phase',
                actor_visibility_proven=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for command in ('audit-build','verify-build','check-vehicle','check-broker'):
        p=sub.add_parser(command);p.add_argument('exe',type=Path)
        p.add_argument('--output',type=Path)
        if command == 'audit-build':p.add_argument('--audit-only',action='store_true')
        if command in ('check-vehicle','check-broker'):
            p.add_argument('capture',type=Path);p.add_argument('--slot',type=int,default=0)
            p.add_argument('--expected-id',type=int);p.add_argument('--observatory',type=Path,required=True)
    args=parser.parse_args()
    if args.exe.stat().st_size>64*1024*1024:raise ValueError('Audit input exceeds bounded64MiB size')
    data=args.exe.read_bytes()
    if args.command=='audit-build':
        report=audit_build(data) if args.audit_only else resolve_build(data)
    elif args.command=='verify-build':report=resolve_build(data)
    else:
        profile=resolve_build(data)
        from r_ai1_observe import load_profile
        from r_ai1_mixed_class import verify_capture
        observe=load_profile(args.observatory,args.exe)
        snapshot=json.loads(args.capture.read_text(encoding='utf-8'))
        raw=args.capture.with_suffix('.dump.bin').read_bytes()
        verify_capture(snapshot,raw,observe.core.parse_dump_bytes)
        report=(check_broker_capture(snapshot,profile) if args.command=='check-broker'
                else check_vehicle(snapshot,profile,args.slot,args.expected_id))
    if args.output:
        from r_ai1_mixed_class import ignored_output
        path=ignored_output(args.output);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if args.command in ('audit-build','verify-build'):
        audit_only = getattr(args, 'audit_only', False)
        print('Build SHA256:', report['sha256'])
        print('Exact profile:', report.get('exact_profile_id') or report.get('exact_registered_profile') or 'unknown')
        print('Compatibility family:', report.get('compatibility_family') or 'REJECT')
        print('Vehicle registry:', report.get('vehicle_registry_profile', report.get('registry_profile', 'unknown')))
        print('Broker capture:', 'enabled' if report.get('capabilities', {}).get('broker_capture_active_race') else 'disabled')
        print('Native Dump:', 'enabled' if report.get('capabilities', {}).get('native_dump') else 'disabled')
        print('Post-Results Dump safe:', report.get('native_dump_post_results_safe',
              report.get('capabilities', {}).get('post_results_native_dump_safe', 'unknown')))
        if not audit_only:
            print('Local profile:', report.get('local_profile_cache') or 'committed exact profile')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
