"""One bounded current F10 roster -> original SpeedDial class observation.
No heap scan, engine calls, process writes or replacement. A stable read is not
an atomic draw-time or native race-generation snapshot. Bank/key is UNKNOWN.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import struct
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('rigid_readonly', ROOT / 'tools/rigid_lifecycle_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
VTABLE = 0x690F38
MAX_ENTITIES = 64


def roster(rows, pid):
    if not rows or rows[0].get('type') != 'frame_begin':
        raise probe.ProbeError('Complete frame_begin required')
    header = rows[0]
    if header.get('exe_sha256') != probe.EXE_SHA:
        raise probe.ProbeError('Exact retail executable required')
    race = next((r for r in rows if r.get('type') == 'race_epoch_snapshot'), {})
    if not race.get('live_certificate_valid') or race.get('frame') != header.get('frame'):
        raise probe.ProbeError('Same-frame live race certificate required')
    generation = race.get('race_lifecycle_generation')
    ownership = header.get('ui_margins', {}).get('ui_ownership_probe', {})
    if not ownership.get('complete') or ownership.get('overflow') or ownership.get('record_drops'):
        raise probe.ProbeError('Complete bounded ownership capture required')
    selected = {}
    for draw in ownership.get('draw_records', []):
        if (draw.get('identity_status') != 'validated_current' or draw.get('identity_field_mask') != 31
                or draw.get('frame') != header.get('frame') or draw.get('race_lifecycle_generation') != generation
                or draw.get('draw_callsite_rva') != 0x16D7C4 or draw.get('fvf') != 0x142
                or not draw.get('forwarded') or draw.get('suppressed')):
            raise probe.ProbeError('Stale, suppressed or unsupported UI record')
        entity = probe.pointer(draw['native_entity_pointer'])
        packet = probe.pointer(draw['native_packet_pointer'])
        if draw.get('observed_packet_pointer') != packet or draw.get('point_storage') != packet + 0x54:
            raise probe.ProbeError('Consumer packet identity mismatch')
        identity = (packet, draw['content_storage'], draw['packet_mode'], draw['ui_epoch'])
        if entity in selected and selected[entity]['identity'] != identity:
            raise probe.ProbeError('Entity identity changed within capture')
        selected.setdefault(entity, {'identity': identity, 'draws': []})['draws'].append(draw)
    if not selected or len(selected) > MAX_ENTITIES:
        raise probe.ProbeError('Current roster must contain 1..64 entities')
    return header, race, selected


def observe(memory, selected):
    result = []
    for entity, row in sorted(selected.items()):
        before = memory.read(entity + 4, 16)
        packet, storage, mode, epoch = row['identity']
        if probe.u32(memory, entity + 0x4C) != packet:
            raise probe.ProbeError('Current entity packet differs from F10')
        packet_before = memory.read(packet + 8, 4) + memory.read(packet + 0x68, 4)
        if struct.unpack('<II', packet_before) != (storage, mode):
            raise probe.ProbeError('Current packet storage/mode differs from F10')
        ais = []
        for slot, ai in enumerate(struct.unpack('<4I', before)):
            if ai:
                vtable = probe.u32(memory, probe.pointer(ai))
                if vtable == VTABLE:
                    ais.append({'slot': slot, 'ai': ai, 'vtable': vtable})
        after = memory.read(entity + 4, 16)
        if (after != before or probe.u32(memory, entity + 0x4C) != packet
                or memory.read(packet + 8, 4) + memory.read(packet + 0x68, 4) != packet_before):
            raise probe.ProbeError('Owner/packet changed during bounded read')
        for candidate in ais:
            if probe.u32(memory, candidate['ai']) != VTABLE:
                raise probe.ProbeError('AI identity changed during bounded read')
            result.append(dict(candidate, entity=entity, packet=packet, storage=storage,
                               packet_mode=mode, capture_ui_epoch=epoch, draws=row['draws']))
    if len(result) > 1:
        raise probe.ProbeError('Multiple SpeedDial candidates; player ownership ambiguous')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--frame', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    match = re.fullmatch(r'frame-(\d+)-d\d+-\d+\.jsonl', args.frame.name)
    if not match or int(match[1]) != args.pid:
        raise probe.ProbeError('Frame filename PID must match explicit current process')
    stat = args.frame.stat()
    if not 0 <= time.time() - stat.st_mtime <= 60 or stat.st_size > 32 * 1024 * 1024:
        raise probe.ProbeError('Require a fresh (<=60s), bounded complete F10 capture')
    payload = args.frame.read_bytes()
    header, race, selected = roster([json.loads(x) for x in payload.splitlines() if x.strip()], args.pid)
    memory = probe.WindowsReadOnlyProcess(args.pid)
    try:
        created = memory.identity['process_creation_filetime'] / 10000000 - 11644473600
        if stat.st_mtime < created or not memory.alive():
            raise probe.ProbeError('Capture predates current process or process exited')
        candidates = observe(memory, selected)
        if not memory.alive() or args.frame.read_bytes() != payload:
            raise probe.ProbeError('Process or frame capture changed during read')
        report = {'schema_version': 1, 'status': 'CURRENT_STRUCTURAL_CANDIDATE' if candidates else 'NOT_FOUND_IN_CURRENT_ROSTER',
                  'identity': memory.identity, 'frame_sha256': hashlib.sha256(payload).hexdigest(),
                  'frame': header['frame'], 'device': header['device'], 'proxy_sha256': header.get('proxy_sha256'),
                  'capture_race_generation': race['race_lifecycle_generation'], 'bytes_read': memory.bytes_read,
                  'candidates': candidates, 'bank0_native_mapping': 'UNKNOWN',
                  'replacement_authorized': False,
                  'limitations': ['External reads are not atomic or at original draw time.',
                                  'Current native UI/race generation is not independently re-read.',
                                  'Double reads do not exclude pointer reuse/ABA.',
                                  'Original player ownership and bank0 plate geometry remain unproved.']}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    finally:
        memory.close()

if __name__ == '__main__':
    main()
