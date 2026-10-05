"""Exact retail native opponent selector extension; no capacity/count shim or DLL."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

from r_ai1_mixed_class import (RETAIL_SHA256, RETAIL_SIZE, REPOSITORY, TEXT_SIZE_OFFSET,
                              ORIGINAL_TEXT_SIZE, apply_ranges, ignored_output, sha256,
                              stock_map, verify_capture)
from r_ai1_hardening import hardening_ranges, compose_ranges, jump
from r_ai1_2_randomizer import Asm
from patch_vehicle_slot25 import parse_pe, va_to_file_offset

COMMON_BASE = '8a17f2ddf59d81dd8f4f75e8c7601d61becc4c10'
PROFILE = 'retail-r-ui1-opponents-seven-hardened'
CANDIDATE_SHA256 = '5507f3ebc474931084f9ddf2b06a3f7afe186c4e29a2dbd81519b86d00f32966'
HOOK = 0x479DCB
CONTINUE = 0x479DD3
CAVE = 0x68E300
ORIGINAL = bytes.fromhex('8b54241489742428')
LABELS = ('ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN')
LANGUAGE_TABLES = ((0, 'English', 0x6C9A60), (1, 'German', 0x6BB888),
                   (2, 'French', 0x6B8000), (3, 'Italian', 0x6C2998),
                   (4, 'Spanish', 0x6BF110), (5, 'Portuguese', 0x6C6220))


def ai_count(index):
    if type(index) != int or not 0 <= index < 7:
        raise ValueError('Opponent selection index must be 0..6')
    return index + 1


def navigate(index, direction):
    ai_count(index)
    if type(direction) != int or direction not in (-1, 1):
        raise ValueError('Only native left/right navigation')
    return max(0, min(6, index + direction))


def list_code():
    # Hook after the original third append, before its existing temporary cleanup.
    # EBX is that native StringList; preserve the entire live register/flag set.
    a = Asm(CAVE)
    a.emit('9c6083ec048bf3bf03000000')
    a.label('next')
    a.call(0x485CF0)
    a.emit('576a408bc88b10ff520c')  # native localized bank64, indices3..6
    a.emit('508d4c2404')
    a.call(0x4D11D0)  # original enString construction in one stack cell, RET4
    a.emit('8d0424506a01ff76088bce')
    a.call(0x407B30)  # same native StringList insert(end,1,&enString), RET12
    a.emit('ff3424')
    a.call(0x5B4C00)  # release temporary string, list holds its copied identity
    a.emit('83c4044783ff07')
    a.branch('0f8c', 'next')
    a.emit('83c404619d')
    a.emit(ORIGINAL)
    a.branch('e9', CONTINUE)
    return a.finish()[0]


def ranges():
    code = list_code()
    ui = [dict(va=HOOK, offset=HOOK-0x400000, original=ORIGINAL,
               replacement=jump(HOOK, CAVE)+b'\x90'*3,
               purpose='After stock three labels append localized Four..Seven to the same native list'),
          dict(va=0x47A32C, offset=0x47A32C-0x400000, original=bytes.fromhex('83fd02'),
               replacement=bytes.fromhex('83fd06'),
               purpose='Opponent right-arrow availability: highest zero-based index6; other mode/difficulty guards unchanged'),
          dict(va=CAVE, offset=CAVE-0x400000, original=bytes(len(code)), replacement=code,
               purpose='Native localization and StringList append/temporary cleanup; replay displaced MOVs'),
          dict(va=None, offset=TEXT_SIZE_OFFSET, original=struct.pack('<I', ORIGINAL_TEXT_SIZE),
               replacement=struct.pack('<I', CAVE+len(code)-0x401000),
               purpose='Declare bounded existing text padding')]
    if CAVE+len(code) >= 0x68F000:
        raise ValueError('Cave exceeds pristine zero padding')
    return compose_ranges(hardening_ranges(), ui)


def localization(source):
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise ValueError('Require exact pristine source')
    tables = []
    for language, name, base in LANGUAGE_TABLES:
        rows = []
        for offset in range(base-0x400000, len(source)-12, 12):
            bank, index, pointer = struct.unpack_from('<iiI', source, offset)
            if bank == -2:
                break
            if bank == 64:
                start = pointer-0x400000
                end = source.index(0, start)
                rows.append(dict(index=index, ai_count=ai_count(index), row_va=offset+0x400000,
                                 string_va=pointer, raw_text_hex=source[start:end].hex()))
        if [r['index'] for r in rows] != list(range(7)):
            raise ValueError('Unexpected localized number bank')
        tables.append(dict(language_id=language, language=name, table_va=base, labels=rows))
    return tables


def manifest(digest):
    return dict(phase='R-UI1', common_base=COMMON_BASE, profile=PROFILE,
                source_sha256=RETAIL_SHA256, output_sha256=digest, size=RETAIL_SIZE,
                status='PREPARED_RUNTIME_UNTESTED', broker_dump_variant='native_hardened',
                list_bank=64, list_indices=list(range(7)), semantic_ai_counts=list(range(1, 8)),
                hidden_count_shim=False, randomizer_dependency=False, engine_arrays_changed=False,
                race_setup_changed=False, loose_data=[], human_safe_start_max_ai=4,
                human_menu_only_ai=[5, 6, 7],
                ranges=[{**{k:v for k,v in r.items() if k not in ('original','replacement')},
                         'length':len(r['original']), 'original_hex':r['original'].hex(),
                         'replacement_hex':r['replacement'].hex()} for r in ranges()])


def build(source):
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise ValueError('Require exact pristine retail hash and size')
    pe = parse_pe(source)
    for r in ranges():
        if r['va'] is not None and va_to_file_offset(pe, r['va']) != r['offset']:
            raise ValueError('Target layout mismatch')
    localization(source)
    binary = apply_ranges(source, ranges(), RETAIL_SHA256)
    digest = sha256(binary)
    if digest != CANDIDATE_SHA256:
        raise ValueError('Pinned UI output mismatch')
    return binary, manifest(digest)


def verify(binary):
    if len(binary) != RETAIL_SIZE or sha256(binary) != CANDIDATE_SHA256:
        raise ValueError('Unknown UI candidate')
    original = bytearray(binary)
    for r in ranges():
        o = r['offset']; end = o+len(r['replacement'])
        if binary[o:end] != r['replacement']:
            raise ValueError('Replacement mismatch')
        original[o:end] = r['original']
    reproduced, report = build(bytes(original))
    if reproduced != binary:
        raise ValueError('Inverse/reproduction mismatch')
    return report


def check_snapshot(snapshot, expected_ai, stage='menu'):
    if type(expected_ai) != int:
        raise ValueError('Expected AI count must be an integer')
    ai_count(expected_ai-1)
    if stage not in ('menu', 'race', 'results') or (stage != 'menu' and expected_ai != 4):
        raise ValueError('Only Four may be started in this independent UI proof')
    src = snapshot.get('source', {})
    label = 'ui-opponents-'+LABELS[expected_ai-1].lower() if stage == 'menu' else 'ui-four-'+stage
    if (snapshot.get('schema_version') != 1 or snapshot.get('kind') != 'master-rallye-broker-dump-snapshot'
        or src.get('label') != label or src.get('freshness') != 'post_baseline_complete_dump_proven'
        or src.get('image_sha256') != CANDIDATE_SHA256 or src.get('build_profile') != PROFILE
        or src.get('broker_dump_variant') != 'native_hardened'):
        raise ValueError('Need fresh exact-profile lifecycle capture')
    entries = snapshot['entries']
    def entry(path):
        rows = [r for r in entries if r['path'] == path]
        if len(rows) != 1:
            raise ValueError('Missing/ambiguous '+path)
        return rows[0]
    def value(path):
        return entry(path)['value']
    if stage == 'menu':
        mode=value('Frontend/QuickModeSelect/Mode'); index=value('Frontend/QuickModeSelect/NumOpponents')
        if type(mode) != int or mode != 1 or type(index) != int or index != expected_ai-1:
            raise ValueError('Wrong zero-based frontend selection')
        row = entry('Frontend/QuickModeSelect/NumOpponentsList')
        if row['type'] != 'StringList' or not isinstance(row['value'], list) or len(row['value']) != 7 or any(not isinstance(v,str) for v in row['value']):
            raise ValueError('Expected seven native labels')
        # Strings are native quote-bearing Dump representation; match parsed state
        # against the selected authored list entry without imposing English.
        def unquote(s):
            if not isinstance(s, str): raise ValueError('Invalid native string')
            return s[1:-1] if s.startswith('"') and s.endswith('"') else s
        if unquote(value('Frontend/QuickModeSelect/NumOpponentsText')) != unquote(row['value'][expected_ai-1]):
            raise ValueError('Displayed-text source does not match selected list item')
        # QuickRace/NumOpponents is committed on Next; it may still hold the prior
        # value while browsing this screen. Report, do not conflate these fields.
        return dict(status='BROKER_FRONTEND_MATCH_ONLY', runtime_full_pass=False,
                    selection_index=expected_ai-1, semantic_ai_count=expected_ai,
                    label_source=row['value'][expected_ai-1], committed_count=value('Frontend/QuickRace/NumOpponents'))
    for path, expected in {'Frontend/QuickRace/NumOpponents':4, 'Frontend/QuickRace/Track':10,
                           'Frontend/QuickRace/Ghost':0, 'Race/NumCars':5, 'Race/NumPlayers':1,
                           'Race/NumNetworkPlayers':0, 'Race/Type':2, 'Race/AttractMode':False,
                           'Race/FinishingType':0, 'Race/NetworkSyncActive':False, 'Race/GhostPlayback':False}.items():
        actual = value(path)
        if type(actual) != type(expected) or actual != expected:
            raise ValueError('Wrong '+path)
    ids = []; drivers = []
    vehicles = stock_map()
    for n in range(5):
        id = value(f'Race/Car{n}/CarID'); cl = value(f'Race/Car{n}/CarClass')
        driver = value(f'Race/Car{n}/DriverID'); player_type = value(f'Race/Car{n}/PlayerType')
        if type(id) != int or id not in range(7) or type(cl) != int or cl != vehicles[id]['class'] or type(player_type) != int or player_type != (1 if n == 0 else 2):
            raise ValueError('Expected five valid normal T1 participants')
        if type(driver) != int or (driver != 30 if n == 0 else not 0 <= driver < 10):
            raise ValueError('Invalid driver identity')
        if n == 0 and id != 0:
            raise ValueError('Expected stock player ID0')
        ids.append(id); drivers.append(driver)
        if not any(r['path'].startswith(f'Vehicles/Car{n}/') for r in entries) or not any(r['path'].startswith(f'Physics/Car{n}/') for r in entries):
            raise ValueError('Missing participant materialization state')
    if len(set(ids)) != 5 or len(set(drivers)) != 5:
        raise ValueError('Aliased participant identity')
    report = dict(status='BROKER_STATE_MATCH_ONLY', runtime_full_pass=False, num_cars=5, car_ids=ids, drivers=drivers)
    if stage == 'results':
        lists = {name:value('Frontend/RaceResults/'+name) for name in ('PositionList','NameList','TimeList')}
        if any(entry('Frontend/RaceResults/'+name)['type'] != 'StringList' or not isinstance(v, list) or len(v) != 5 for name,v in lists.items()):
            raise ValueError('Expected five result entries')
        if lists['PositionList'] != [f'"{n}"' for n in range(1,6)]:
            raise ValueError('Wrong result ranking')
        report.update(status='BROKER_RESULTS_MATCH_ONLY', result_lists=lists)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    for command in ('build','verify','check-menu','check-race','check-results'):
        q = sub.add_parser(command); q.add_argument('candidate', type=Path)
        if command == 'build': q.add_argument('--output', required=True, type=Path)
        if command.startswith('check-'):
            q.add_argument('snapshot', type=Path); q.add_argument('--observatory', required=True, type=Path)
            q.add_argument('--expected-ai', type=int, choices=range(1,8), required=True)
    a = p.parse_args()
    if a.command == 'build':
        binary, report = build(a.candidate.read_bytes()); out = ignored_output(a.output)
        if out.exists(): raise ValueError('Refuse candidate overwrite')
        out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(binary)
        out.with_suffix('.manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    else:
        report = verify(a.candidate.read_bytes())
        if a.command.startswith('check-'):
            from r_ai1_observe import load_profile
            adapter = load_profile(a.observatory, a.candidate)
            snapshot = json.loads(a.snapshot.read_text(encoding='utf-8')); name = snapshot['source']['raw_sidecar']
            if Path(name).name != name: raise ValueError('Invalid raw sidecar name')
            verify_capture(snapshot, a.snapshot.with_name(name).read_bytes(), adapter.core.parse_dump_bytes)
            report = check_snapshot(snapshot, a.expected_ai, a.command[6:])
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
