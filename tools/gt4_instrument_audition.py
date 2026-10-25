"""Optional private GT4 INST/JAM sample inspection, with explicit nominal pitch.

This decodes program/split PCM, not GTSE event dispatch or effect attribution.
Layout evidence: user-local PDTools InsHeader/JamHeader/JamProgChunk readers.
No samples or proprietary fixtures are shipped.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
from gt4_audio_extract import decode_spu, pcm_wav


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(raw):
    if not 80 <= len(raw) <= 16 * 1024 * 1024 or raw[:4] != b'INST':
        raise ValueError('bounded INST required')
    reloc, body_at, runtime, body_size, body_pointer = struct.unpack_from('<5I', raw, 4)
    if reloc or runtime or body_at != body_pointer or body_at + body_size != len(raw) or body_at % 16 or body_size % 16:
        raise ValueError('unsupported INST body/relocation')
    jam_size, jam_body, reserved = struct.unpack_from('<3I', raw, 32)
    if raw[44:48] != b'SShd' or jam_body != body_size or reserved or not 48 <= jam_size <= body_at - 32:
        raise ValueError('unsupported GT4 JAM header (GT3 INST is distinct)')
    rows = []
    scanned_bytes = 0
    for kind, pointer_at in (('program', 48), ('se_program', 68)):
        rel = struct.unpack_from('<i', raw, pointer_at)[0]
        if rel == -1:
            continue
        at = 32 + rel
        if not 80 <= at < body_at - 2:
            raise ValueError('program table outside header')
        last = struct.unpack_from('<h', raw, at)[0]
        if not 0 <= last <= 1023 or at + 2 + (last + 1) * 2 > body_at:
            raise ValueError('program count budget')
        for index in range(last + 1):
            off = struct.unpack_from('<h', raw, at + 2 + index * 2)[0]
            if off == -1:
                continue
            pos = at + off
            if off < 2 + (last + 1) * 2 or pos + 8 > body_at:
                raise ValueError('program outside header')
            head = raw[pos:pos + 8]
            count = head[7] - head[6] + 1 if head[0] == 255 else (head[0] & 15) + 1
            if not 1 <= count <= 128 or pos + 8 + count * 16 > body_at:
                raise ValueError('split count/bounds')
            for split in range(count):
                if len(rows) >= 4096:
                    raise ValueError('total split budget')
                sat = pos + 8 + split * 16
                data = raw[sat:sat + 16]
                ssa = ((data[5] << 16) | struct.unpack_from('<H', data, 6)[0]) * 16
                if ssa >= body_size:
                    rows.append({'kind': kind, 'program': index, 'split': split,
                                 'split_record_offset': sat, 'split_record_hex': data.hex(),
                                 'flags_unqualified': data[4], 'ssa_byte_offset': ssa,
                                 'codec_status': 'UNSUPPORTED', 'codec_error': 'SSA outside body; noise/sentinel semantics unqualified'})
                    continue
                begin = body_at + ssa
                end = begin
                while end + 16 <= len(raw):
                    scanned_bytes += 16
                    if scanned_bytes > 64 * 1024 * 1024:
                        raise ValueError('aggregate sample scan budget')
                    flags = raw[end + 1]
                    end += 16
                    if flags in (1, 3):
                        break
                else:
                    raise ValueError('sample missing bounded end marker')
                try:
                    decoded = decode_spu(raw[begin:end])
                    codec = {'codec_status': 'PCM_VALID', 'samples': len(decoded['samples']),
                             'loop_start_sample': decoded['loop_start_sample'],
                             'loop_end_sample': decoded['loop_end_sample']}
                except ValueError as error:
                    codec = {'codec_status': 'UNSUPPORTED', 'codec_error': str(error)}
                rows.append({'kind': kind, 'program': index, 'split': split,
                             'program_header_hex': head.hex(), 'split_record_offset': sat,
                             'split_record_hex': data.hex(), 'note_min': data[0], 'note_max': data[1],
                             'base_note_unqualified': data[2], 'flags_unqualified': data[4],
                             'sample_file_offset': begin, 'encoded_bytes': end - begin,
                             'encoded_sha256': digest(raw[begin:end]), **codec})
    return {'status': 'STRUCTURAL_PCM_ONLY_EVENT_ROUTING_UNQUALIFIED', 'sha256': digest(raw),
            'bytes': len(raw), 'body_offset': body_at, 'entries': rows,
            'boundary': 'Program/note records and SPU PCM are recovered. GTSE routing, nominal pitch, ADSR/LFO, noise flags, layering and event identity are not reproduced.'}


def extract(source, output, kind, program, split, sample_rate):
    raw = Path(source).read_bytes()
    report = inspect(raw)
    entries = [e for e in report['entries'] if (e['kind'], e['program'], e['split']) == (kind, program, split)]
    if len(entries) != 1:
        raise ValueError('select exactly one existing program/split')
    e = entries[0]
    if e['codec_status'] != 'PCM_VALID':
        raise ValueError('selected split unsupported: ' + e['codec_error'])
    at = e['sample_file_offset']
    decoded = decode_spu(raw[at:at + e['encoded_bytes']])
    loop = None if decoded['loop_start_sample'] is None else (decoded['loop_start_sample'], decoded['loop_end_sample'])
    wav = pcm_wav(decoded['samples'], sample_rate, loop)
    output = Path(output)
    if output.exists() or output.with_suffix('.json').exists():
        raise ValueError('new output and sidecar required')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(wav)
    evidence = {'source': str(Path(source).resolve()), 'bank_sha256': report['sha256'], 'selection': e,
                'wav_sha256': digest(wav), 'sample_rate': sample_rate,
                'playback_rate_provenance': 'caller-selected nominal audition rate; not source-qualified pitch',
                'authentic_effect_identity': None, 'boundary': report['boundary']}
    output.with_suffix('.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    return evidence


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--program', type=int)
    p.add_argument('--split', type=int, default=0)
    p.add_argument('--kind', choices=('program', 'se_program'), default='program')
    p.add_argument('--sample-rate', type=int)
    a = p.parse_args()
    if a.program is None:
        if a.sample_rate is not None:
            p.error('sample rate applies only to explicit program audition')
        report = inspect(a.source.read_bytes())
        if a.output.exists():
            raise ValueError('new report required')
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(report['status'], len(report['entries']))
    else:
        if a.sample_rate is None:
            p.error('explicit nominal --sample-rate required')
        extract(a.source, a.output, a.kind, a.program, a.split, a.sample_rate)
        print('PRIVATE_NOMINAL_AUDITION_ONLY')
