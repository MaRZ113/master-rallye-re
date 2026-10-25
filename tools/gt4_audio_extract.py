"""Optional local GT4 ENGN bank inspection and mono SPU-ADPCM extraction.

No retail assets are bundled. Choose an explicit nominal playback rate, or
provide the qualified user-local CORE to apply its recovered SPU pitch rule.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from master_rallye.addon_sdk.gt4_spec import DatabaseTable, label_id

MAX_BANK = 16 * 1024 * 1024
COEFFICIENTS = ((0, 0), (60, 0), (115, -52), (98, -55), (122, -60))
QUALIFIED_CORE_SHA256 = '962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0'


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def pitch_core_evidence(path):
    """Verify the supplied reconstructed CORE before applying its pitch rule.

    This CORE is supplied beside the assets but identifies as Online US. It is
    comparative native evidence, not an assertion of exact Beta runtime parity.
    """
    raw = Path(path).read_bytes()
    if sha256(raw) != QUALIFIED_CORE_SHA256 or raw[:4] != b'\x7fELF':
        raise ValueError('unqualified GT4 pitch CORE hash')
    phoff = struct.unpack_from('<I', raw, 28)[0]
    count = struct.unpack_from('<H', raw, 44)[0]
    segments = [struct.unpack_from('<8I', raw, phoff + i * 32) for i in range(count)]
    expected = {0x532a84: '0800a38c', 0x532a88: '0000a284',
                0x532a8c: '18186600', 0x532a98: '1b006200',
                0x532b80: '06002585', 0x538100: '9400a294'}
    checks = []
    for address, encoded in expected.items():
        matches = [raw[p[1] + address - p[2]:p[1] + address - p[2] + 4]
                   for p in segments if p[0] == 1 and p[2] <= address and address + 4 <= p[2] + p[4]]
        if len(matches) != 1 or matches[0].hex() != encoded:
            raise ValueError('GT4 pitch evidence byte mismatch at ' + hex(address))
        checks.append({'address': hex(address), 'bytes': encoded})
    return {'core_sha256': QUALIFIED_CORE_SHA256, 'instructions': checks,
            'rule': 'SPU pitch = entry_u32_at_8 * requested_RPM / entry_i16_at_0; wave rate at anchor = 48000 * pitch / 4096',
            'boundary': 'Supplied reconstructed CORE / Online-US identity; not independently paired Beta runtime proof. 48kHz SPU2 nominal clock, no doppler/global pitch. WAV integer rate is rounded.'}


def mapping(spec_folder, car_label):
    """Follow explicit GT4 US2560 GENERIC_CAR -> DEFAULT_PARTS -> ENGINE keys.

    This is a qualified layout, not a universal SpecDB field-name heuristic.
    ModelCode/CAR_VARIATION association remains separate source evidence.
    """
    folder = Path(spec_folder)
    if not re.fullmatch(r'[a-z0-9_]{1,100}', car_label):
        raise ValueError('invalid explicit GT4 car label')
    evidence = {}

    def row(name, row_id=None, label=None, size=None):
        raw = (folder / (name + '.dbt')).read_bytes()
        db = DatabaseTable(raw)
        if label is not None:
            labels = (folder / (name + '.idi')).read_bytes()
            row_id = label_id(labels, label)
        result = db.row(row_id)
        if len(result) != size:
            raise ValueError('unqualified GT4 audio mapping row layout ' + name)
        evidence[name] = {'table_sha256': sha256(raw), 'row_id': row_id,
                          'row_size': len(result), 'row_sha256': sha256(result)}
        if label is not None:
            evidence[name].update(label=label, labels_sha256=sha256(labels))
        return result, row_id

    generic, _ = row('GENERIC_CAR', label=car_label, size=24)
    parts_id, parts_table = struct.unpack_from('<ii', generic, 0)
    if parts_table != 36 or parts_id < 0:
        raise ValueError('unqualified DefaultParts reference')
    parts, _ = row('DEFAULT_PARTS', row_id=parts_id, size=208)
    engine_id, engine_table = struct.unpack_from('<ii', parts, 88)
    if engine_table != 12 or engine_id < 0:
        raise ValueError('unqualified Engine reference')
    engine, _ = row('ENGINE', row_id=engine_id, size=113)
    sound_id = struct.unpack_from('<H', engine, 24)[0]
    if not 1 <= sound_id <= 65535:
        raise ValueError('invalid GT4 sound number')
    engine_table_raw = (folder / 'ENGINE.dbt').read_bytes()
    engine_db = DatabaseTable(engine_table_raw)
    shared = [i for i in sorted(engine_db.rows) if struct.unpack_from('<H', engine_db.row(i), 24)[0] == sound_id]
    return {'status': 'SOURCE_KEY_CHAIN_RECOVERED', 'car_label': car_label,
            'sound_number': sound_id, 'rows': evidence,
            'engine_rows_using_same_sound_number': shared,
            'qualified_layout': 'GT4_PREMIUM_US2560: 24/208/113-byte rows; DefaultParts@0 table36; Engine@88 table12; soundNum ushort@24',
            'boundary': 'Source row keys prove association. Column labels follow user-local PDTools metadata. Tuning-bank selection and exact playback are not inferred.'}


def parse_engn(raw):
    if not 48 <= len(raw) <= MAX_BANK or raw[:4] != b'ENGN':
        raise ValueError('invalid ENGN bank or budget')
    reloc, hsize, runtime, ssize, sptr = struct.unpack_from('<5I', raw, 4)
    if reloc or runtime or sptr != hsize or hsize < 48 or hsize + ssize != len(raw) or ssize % 16:
        raise ValueError('unsupported ENGN relocation/body layout')
    tables = [struct.unpack_from('<II', raw, 24 + i * 8) for i in range(2)]
    if not 1 <= sum(n for n, _ in tables) <= 32:
        raise ValueError('ENGN entry count budget')
    entries = []
    occupied = set(range(48))
    for table, (count, at) in enumerate(tables):
        if count == 0:
            if at != 0:
                raise ValueError('unexpected empty ENGN table pointer')
            continue
        if at % 16 or at < 48 or at + count * 16 > hsize:
            raise ValueError('ENGN table outside header')
        for j in range(at, at + count * 16):
            if j in occupied:
                raise ValueError('overlapping ENGN tables')
            occupied.add(j)
        for index in range(count):
            words = struct.unpack_from('<6HI', raw, at + index * 16)
            offset = words[6]
            if offset % 16 or offset >= ssize or words[5] != 0:
                raise ValueError('unqualified ENGN entry offset/reserved word')
            entries.append({'table': table, 'index': index, 'record_offset': at + index * 16,
                            'words_u16': list(words[:6]), 'body_offset': offset})
    if any(raw[j] for j in range(48, hsize) if j not in occupied):
        raise ValueError('unexplained ENGN header bytes')
    offsets = sorted(e['body_offset'] for e in entries)
    if len(set(offsets)) != len(offsets) or offsets[0] != 0:
        raise ValueError('duplicate/unaccounted ENGN body ranges')
    ends = dict(zip(offsets, offsets[1:] + [ssize]))
    for entry in entries:
        begin = entry['body_offset']
        data = raw[sptr + begin:sptr + ends[begin]]
        decoded = decode_spu(data)
        entry.update(encoded_bytes=len(data), encoded_sha256=sha256(data),
                     samples=len(decoded['samples']), loop_start_sample=decoded['loop_start_sample'],
                     loop_end_sample=decoded['loop_end_sample'])
    return {'status': 'ENGN_STRUCTURAL_AND_CODEC_VALID', 'sha256': sha256(raw),
            'bytes': len(raw), 'header_bytes': hsize, 'body_bytes': ssize,
            'header_words_40_44': list(struct.unpack_from('<2I', raw, 40)), 'entries': entries,
            'semantics': 'All six source words preserved verbatim. Words0/1/2 resemble reference/boundary RPM; words3/4 require native interpretation. No automatic gain, pitch, throttle or bank-role claims.'}


def decode_spu(data):
    """Decode bounded mono PSX/SPU ADPCM blocks, retaining actual loop markers."""
    if not data or len(data) % 16 or len(data) > MAX_BANK:
        raise ValueError('invalid SPU stream size')
    hist1 = hist2 = 0
    samples = []
    loop_start = loop_end = None
    for at in range(0, len(data), 16):
        header, flags = data[at:at + 2]
        predictor, shift = header >> 4, header & 15
        if predictor >= len(COEFFICIENTS) or shift > 12 or flags > 7 or flags == 5:
            raise ValueError('unsupported SPU predictor/shift/flags')
        if flags in (4, 6):
            if loop_start is not None:
                raise ValueError('multiple SPU loop starts')
            loop_start = len(samples)
        a, b = COEFFICIENTS[predictor]
        for packed in data[at + 2:at + 16]:
            for nibble in (packed & 15, packed >> 4):
                nibble = nibble - 16 if nibble >= 8 else nibble
                value = 0 if flags == 7 else ((nibble << 12) >> shift) + ((hist1 * a + hist2 * b + 32) >> 6)
                value = max(-32768, min(32767, value))
                samples.append(value)
                hist2, hist1 = hist1, value
        if flags & 1:
            if at + 16 != len(data):
                raise ValueError('unaccounted bytes after SPU end marker')
            if flags == 3:
                loop_end = len(samples)
            elif loop_start is not None:
                raise ValueError('SPU loop start without repeat end')
    if not data[-15] & 1:
        raise ValueError('SPU stream missing final end marker')
    if (loop_start is None) != (loop_end is None):
        raise ValueError('incomplete SPU loop markers')
    return {'samples': samples, 'loop_start_sample': loop_start, 'loop_end_sample': loop_end}


def pcm_wav(samples, rate, loop=None):
    if type(rate) is not int or not 8000 <= rate <= 96000:
        raise ValueError('explicit WAV rate outside 8000..96000 Hz')
    pcm = struct.pack('<' + 'h' * len(samples), *samples)
    chunks = [(b'fmt ', struct.pack('<HHIIHH', 1, 1, rate, rate * 2, 2, 16)), (b'data', pcm)]
    if loop is not None:
        start, end = loop
        if not 0 <= start < end <= len(samples):
            raise ValueError('invalid WAV sample loop')
        # WAV smpl end is inclusive; source/code interfaces use exclusive ends.
        chunks.append((b'smpl', struct.pack('<9I', 0, 0, round(1e9 / rate), 60, 0, 0, 0, 1, 0)
                       + struct.pack('<6I', 0, 0, start, end - 1, 0, 0)))
    body = b'WAVE' + b''.join(tag + struct.pack('<I', len(buf)) + buf + bytes(len(buf) % 2) for tag, buf in chunks)
    return b'RIFF' + struct.pack('<I', len(body)) + body


def extract(source, output, sample_rate=None, pitch_core=None):
    """Write private full/loop-only PCM and provenance; never normalize or resample."""
    source, output = Path(source), Path(output)
    raw = source.read_bytes()
    report = parse_engn(raw)
    if (sample_rate is None) == (pitch_core is None):
        raise ValueError('choose exactly one explicit nominal rate or qualified pitch CORE')
    native = None if pitch_core is None else pitch_core_evidence(pitch_core)
    if output.exists():
        raise ValueError('extraction output must be a new directory')
    # Validate rate and every band before creating output.
    rates = []
    for entry in report['entries']:
        if native:
            words = entry['words_u16']
            if not 200 <= words[0] <= 20000 or not 1 <= words[4] <= 0x3fff or words[5]:
                raise ValueError('invalid source pitch/reference RPM')
            exact_rate = 48000 * words[4] / 4096
            rate = round(exact_rate)
            entry.update(reference_rpm=words[0], full_gain_rpm_min=words[1], full_gain_rpm_max=words[2],
                         gain_code=words[3], base_spu_pitch=words[4], source_rate_exact_hz=exact_rate)
        else:
            rate = sample_rate
        pcm_wav([0], rate)
        rates.append(rate)
    output.mkdir(parents=True)
    for entry, rate in zip(report['entries'], rates):
        begin = report['header_bytes'] + entry['body_offset']
        decoded = decode_spu(raw[begin:begin + entry['encoded_bytes']])
        name = f"table{entry['table']}-band{entry['index']:02d}"
        loop = None if decoded['loop_start_sample'] is None else (decoded['loop_start_sample'], decoded['loop_end_sample'])
        full = pcm_wav(decoded['samples'], rate, loop)
        (output / (name + '.wav')).write_bytes(full)
        entry.update(wav=name + '.wav', wav_sha256=sha256(full), sample_rate_hz=rate)
        if loop:
            loop_wav = pcm_wav(decoded['samples'][loop[0]:loop[1]], rate)
            (output / (name + '-loop.wav')).write_bytes(loop_wav)
            entry.update(loop_wav=name + '-loop.wav', loop_wav_sha256=sha256(loop_wav))
    report.update(source=str(source.resolve()), sample_rate_hz=sample_rate,
                  native_pitch_evidence=native,
                  playback_rate_provenance='qualified supplied CORE pitch rule at anchor RPM; rounded integer WAV Hz' if native else 'explicit caller-selected nominal rate; not recovered from ENGN',
                  codec='integer PSX ADPCM with +32 predictor rounding and clamped history; float decoders may differ slightly',
                  boundary='Authentic source sample bytes, mono decoded PCM. Source-pitch mode reproduces the supplied CORE anchor pitch, not full GT4 mixing/doppler/global pitch. Exact layer balance, throttle mapping and tuning-bank selection are not reproduced. Loop-only WAV preserves source loop region without cosmetic fades.')
    (output / 'bank.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('mapping'); p.add_argument('--spec-folder', type=Path, required=True)
    p.add_argument('--car-label', required=True); p.add_argument('--carsound-root', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('inspect'); p.add_argument('source', type=Path); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('extract'); p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, required=True)
    rates = p.add_mutually_exclusive_group(required=True)
    rates.add_argument('--sample-rate', type=int)
    rates.add_argument('--pitch-core', type=Path)
    args = parser.parse_args()
    if args.command == 'mapping':
        result = mapping(args.spec_folder, args.car_label)
        if args.carsound_root:
            result['available_banks'] = []
            for bank in ('engine', 'normal0', 'normal1', 'normal2', 'normal3', 'turbo0', 'turbo1', 'turbo2', 'turbo3'):
                source = args.carsound_root / bank / str(result['sound_number'])
                if source.is_file():
                    result['available_banks'].append({'bank': bank, 'source': str(source.resolve()), **parse_engn(source.read_bytes())})
    elif args.command == 'inspect':
        result = parse_engn(args.source.read_bytes())
    else:
        result = extract(args.source, args.output, args.sample_rate, args.pitch_core)
        print(result['status']); return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'])


if __name__ == '__main__':
    main()
