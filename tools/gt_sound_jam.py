"""Bounded GT4 INST/JAM inspector using supplied-CORE SSA address semantics.

Static interpretation, never proof of runtime build pairing or acoustic identity.
Nominal audition rate is explicit; no ADSR, LFO, noise or game mixing emulation.
"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path
from gt4_audio_extract import decode_spu, pcm_wav

CORE_SHA256 = '962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0'
BANK_SLOTS = {0: 'gt4sys.ins', 1: 'gt4race.ins', 2: 'gt4count.ins', 3: 'gt4race2.ins'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(raw):
    if not 160 <= len(raw) <= 16 * 1024 * 1024 or raw[:4] != b'INST':
        raise ValueError('bounded GT4 INST required')
    reloc, body_at, runtime, body_size, body_pointer = struct.unpack_from('<5I', raw, 4)
    if reloc or runtime or body_at != body_pointer or body_at + body_size != len(raw) or body_at % 16 or body_size % 16:
        raise ValueError('unsupported INST body/relocation')
    jam_size, jam_body, reserved = struct.unpack_from('<3I', raw, 32)
    if raw[44:48] != b'SShd' or jam_body != body_size or reserved or not 128 <= jam_size <= body_at - 32:
        raise ValueError('unsupported GT4 JAM header')
    # 005338C8 selects shift 3 for nonzero JAM+0x7c, otherwise shift 4.
    address_mode = struct.unpack_from('<I', raw, 32 + 0x7c)[0]
    shift = 3 if address_mode else 4
    rows, programs = [], []
    scanned_bytes = 0
    for kind, pointer_at in (('program', 48), ('se_program', 68)):
        rel = struct.unpack_from('<i', raw, pointer_at)[0]
        if rel == -1:
            continue
        at = 32 + rel
        if not 160 <= at <= body_at - 2:
            raise ValueError('program table outside header')
        last = struct.unpack_from('<H', raw, at)[0]
        if last > 1023 or at + 2 + (last + 1) * 2 > body_at:
            raise ValueError('program count budget')
        for index in range(last + 1):
            off = struct.unpack_from('<H', raw, at + 2 + index * 2)[0]
            if off == 0xffff:
                programs.append({'kind': kind, 'program': index, 'present': False})
                continue
            pos = at + off
            if off < 2 + (last + 1) * 2 or pos + 8 > body_at:
                raise ValueError('program outside header')
            head = raw[pos:pos + 8]
            count = head[7] - head[6] + 1 if head[0] == 255 else (head[0] & 15) + 1
            if not 1 <= count <= 128 or pos + 8 + count * 16 > body_at:
                raise ValueError('split count/bounds')
            programs.append({'kind': kind, 'program': index, 'present': True, 'program_record_offset': pos,
                             'program_header_hex': head.hex(), 'split_count': count})
            for split in range(count):
                if len(rows) >= 4096:
                    raise ValueError('total split budget')
                sat = pos + 8 + split * 16
                data = raw[sat:sat + 16]
                ssa_units = (data[5] << 16) | struct.unpack_from('<H', data, 6)[0]
                ssa = ssa_units << shift
                entry = {'kind': kind, 'program': index, 'split': split,
                         'program_header_hex': head.hex(), 'split_record_offset': sat,
                         'split_record_hex': data.hex(), 'note_min': data[0], 'note_max': data[1],
                         'base_note_unqualified': data[2], 'flags_unqualified': data[4],
                         'ssa_units': ssa_units, 'ssa_address_shift': shift, 'ssa_byte_offset': ssa}
                rows.append(entry)
                if ssa >= body_size or ssa % 16:
                    entry.update(codec_status='UNSUPPORTED', codec_error='SSA outside body or not ADPCM-frame aligned')
                    continue
                begin = body_at + ssa
                end = begin
                while end + 16 <= len(raw):
                    scanned_bytes += 16
                    if scanned_bytes > 64 * 1024 * 1024:
                        raise ValueError('aggregate sample scan budget')
                    flags = raw[end + 1]
                    end += 16
                    if flags & 1:
                        break
                else:
                    entry.update(codec_status='UNSUPPORTED', codec_error='sample missing bounded end marker')
                    continue
                entry.update(sample_file_offset=begin, encoded_bytes=end - begin, encoded_sha256=digest(raw[begin:end]))
                try:
                    decoded = decode_spu(raw[begin:end])
                    entry.update(codec_status='PCM_VALID', samples=len(decoded['samples']),
                                 loop_start_sample=decoded['loop_start_sample'], loop_end_sample=decoded['loop_end_sample'])
                except ValueError as error:
                    entry.update(codec_status='UNSUPPORTED', codec_error=str(error))
    return {'status': 'NATIVE_SSA_STRUCTURAL_PCM_ONLY', 'sha256': digest(raw), 'bytes': len(raw),
            'body_offset': body_at, 'body_bytes': body_size, 'jam_address_mode_word': address_mode,
            'ssa_address_shift': shift, 'programs': programs, 'entries': rows,
            'native_semantics': {'core_sha256': CORE_SHA256, 'bank_open_va': '0x005338c8',
                                 'ssa_consumer_va': '0x00533730', 'runtime_pairing_confirmed': False},
            'boundary': 'Supplied-CORE static interpretation of source banks. Nominal rate is caller-selected; ADSR/LFO/noise and original runtime mix are not reproduced.'}


def resolve_events(banks_by_slot, events):
    """Resolve only the proven direct-program/first-split path, preserving gaps.

    banks_by_slot maps integer slots to inspect() reports; events is a mapping
    from literal GTSE names to uint32 tokens (or an iterable of such pairs).
    """
    items = events.items() if hasattr(events, 'items') else events
    result = []
    for name, token in items:
        if not isinstance(token, int) or not 0 <= token <= 0xffffffff:
            raise ValueError('uint32 GTSE token required')
        slot, mode, index, low = (token >> 24, (token >> 16) & 255, (token >> 8) & 255, token & 255)
        entry = {'name': name, 'token': f'0x{token:08x}', 'bank_slot': slot,
                 'bank_name': BANK_SLOTS.get(slot), 'sequence_mode': mode,
                 'program': index, 'low_byte': low, 'authentic_effect_identity': None}
        result.append(entry)
        bank = banks_by_slot.get(slot)
        if mode:
            entry['status'] = 'SE_SEQUENCE_ROUTING_UNSUPPORTED'
        elif bank is None:
            entry['status'] = 'BANK_NOT_SUPPLIED'
        else:
            matches = [row for row in bank['entries'] if row['kind'] == 'program' and row['program'] == index and row['split'] == 0]
            if matches:
                entry.update(status='STATIC_DIRECT_FIRST_SPLIT', selection=matches[0], bank_sha256=bank['sha256'],
                             low_byte_semantics='passed but unused by supplied CORE direct initializer 0x00533fc8')
            else:
                entry['status'] = 'DIRECT_PROGRAM_ABSENT'
    return result


def extract(source, output, kind, program, split, sample_rate):
    raw = Path(source).read_bytes()
    report = inspect(raw)
    entries = [e for e in report['entries'] if (e['kind'], e['program'], e['split']) == (kind, program, split)]
    if len(entries) != 1:
        raise ValueError('select exactly one existing program/split')
    entry = entries[0]
    if entry['codec_status'] != 'PCM_VALID':
        raise ValueError('selected split unsupported: ' + entry['codec_error'])
    at = entry['sample_file_offset']
    decoded = decode_spu(raw[at:at + entry['encoded_bytes']])
    loop = None if decoded['loop_start_sample'] is None else (decoded['loop_start_sample'], decoded['loop_end_sample'])
    wav = pcm_wav(decoded['samples'], sample_rate, loop)
    output = Path(output)
    sidecar = output.with_suffix('.json')
    if output.exists() or sidecar.exists() or output == sidecar:
        raise ValueError('new WAV output and sidecar required')
    evidence = {'source': str(Path(source).resolve()), 'bank_sha256': report['sha256'], 'selection': entry,
                'native_semantics': report['native_semantics'], 'wav_sha256': digest(wav), 'sample_rate': sample_rate,
                'playback_rate_provenance': 'caller-selected nominal audition rate; not source-qualified pitch',
                'authentic_effect_identity': None, 'boundary': report['boundary']}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(wav)
    sidecar.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    return evidence
