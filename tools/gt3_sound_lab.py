"""Read-only GT3 RoFS/GTAR audio research and private nominal WAV audition.

GT3 INST is parsed independently from GT4 JAM. Exact-build optional native
evidence binds GTSE events and recovers leaf pitch; full runtime mix is separate.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

from gt3_audio_inspect import events
from gt3_ui_icon import inventory, read_member
from gt4_audio_extract import COEFFICIENTS, pcm_wav

MAX_BANK = 16 * 1024 * 1024
GT3_CORE_SHA256 = 'fdcea2aa43231873592adee0fb96499f2e40979e0269191af1eafcf95da12b0b'
GT3_EVENT_SHA256 = '8bd74f6834a52e39ea0708db4b875a5910e3151d1f7e35e417864953ac9d376e'
GT3_NATIVE_BANKS = (
    ('sound/gt3sys.ins', 'f94610227f3d4cbe9c1c36c3cc044d2c10f1a58aa7bbbd6912783746836ded4d'),
    ('sound/gt3se01.ins', 'd3170ce8123c8fbed12164e7898f0e4984d55f5bbc63bf6e0065d59f51aac426'),
    ('sound/gt3se02.ins', 'ebf2156231a109a820aaa3b9c395c86f20335301c0be1f3a3391155a470e1616'),
)
BOUNDARY = ('Static original-bank structure and SPU ADPCM only. Nominal sample '
            'rate, ADSR, voice layering, runtime event dispatch, tuning-bank '
            'selection, volume and exact game playback are not qualified.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unpack_core(source, output):
    """Reconstruct a static ELF carrier from GT3's supplied CORE container.

    RSA blobs are retained as hashes, without claiming signature verification.
    ELF metadata/permissions are generated for offline disassembly only; mapped
    segment bytes and addresses come from the original decompressed container.
    """
    source, output = Path(source), Path(output)
    if output.exists() or output.with_suffix('.json').exists():
        raise ValueError('new reconstructed ELF and sidecar required')
    raw = source.read_bytes()
    if not 6 < len(raw) <= MAX_BANK or raw[:2] != b'\x01\x01':
        raise ValueError('bounded unencrypted GT3 CORE container required')
    size = struct.unpack_from('<I', raw, 2)[0]
    if not 276 < size <= MAX_BANK:
        raise ValueError('GT3 CORE inflate budget')
    decoder = zlib.decompressobj(-15)
    inflated = decoder.decompress(raw[6:], size + 1)
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail or len(inflated) != size:
        raise ValueError('GT3 CORE inflate size/end mismatch')
    cursor, rsa = 0, []
    for _ in range(2):
        if cursor + 2 > len(inflated):
            raise ValueError('truncated GT3 RSA blob length')
        count = struct.unpack_from('<H', inflated, cursor)[0]
        cursor += 2
        if count != 128 or cursor + count > len(inflated):
            raise ValueError('unsupported GT3 RSA blob length')
        rsa.append({'offset': cursor, 'bytes': count, 'sha256': sha(inflated[cursor:cursor + count])})
        cursor += count
    count, entry = struct.unpack_from('<2I', inflated, cursor)
    cursor += 8
    if not 1 <= count <= 16:
        raise ValueError('GT3 CORE segment count budget')
    segments = []
    ranges = []
    for i in range(count):
        if cursor + 8 > len(inflated):
            raise ValueError('truncated GT3 segment descriptor')
        target, n = struct.unpack_from('<2I', inflated, cursor)
        cursor += 8
        if not 0x100000 <= target < target + n <= 0x2000000 or cursor + n > len(inflated) or any(target < b and a < target + n for a, b in ranges):
            raise ValueError('invalid/overlapping GT3 native segment')
        ranges.append((target, target + n))
        data = inflated[cursor:cursor + n]
        segments.append({'index': i, 'address': target, 'size': n,
                         'inflated_offset': cursor, 'sha256': sha(data)})
        cursor += n
    if cursor != len(inflated) or not any(a <= entry < b for a, b in ranges):
        raise ValueError('unaccounted GT3 CORE data or entry outside segments')
    elf = bytearray(b'\x7fELF\x01\x01\x01' + bytes(9))
    # MIPS flags match the paired SCUS_971.02 header; no original ELF is alleged.
    elf += struct.pack('<HHIIIIIHHHHHH', 2, 8, 1, entry, 52, 0, 0x20924001, 52, 32, count, 0, 0, 0)
    elf += bytes(32 * count)
    for i, seg in enumerate(segments):
        offset = (len(elf) + 4095) & ~4095
        offset += seg['address'] & 4095
        elf += bytes(offset - len(elf))
        data = inflated[seg['inflated_offset']:seg['inflated_offset'] + seg['size']]
        elf += data
        struct.pack_into('<8I', elf, 52 + 32 * i, 1, offset, seg['address'], seg['address'], seg['size'], seg['size'], 7, 4096)
        seg['elf_offset'] = offset
    result = {'source': str(source.resolve()), 'source_sha256': sha(raw),
              'inflated_sha256': sha(inflated), 'inflated_bytes': len(inflated),
              'segments': segments, 'entry': entry, 'rsa_blobs': rsa,
              'rsa_status': 'PRESENT_NOT_AUTHENTICATED', 'elf_sha256': sha(elf),
              'boundary': 'Reconstructed offline ELF carrier. Segment addresses/bytes are original container fields; ELF header and RWX flags generated. No runtime or RSA verification.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(elf)
    output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def _qualified_native_core(source):
    raw = Path(source).read_bytes()
    if sha(raw) != GT3_CORE_SHA256:
        raise ValueError('unqualified original GT3 CORE SHA256')
    inflated = zlib.decompress(raw[6:], -15)
    if len(inflated) != 2437879 or struct.unpack_from('<4I', inflated, 260) != (1, 0x100008, 0x100000, 2437603):
        raise ValueError('GT3 native segment mapping mismatch')
    image = inflated[276:]
    # Only digests/lengths of original instructions are kept in source.
    checks = {0x22c5c4: (4, '2b32c0adc190817141db86105e722fc62cd6862d7f02f28a4be6897ab7e5cd22'),
              0x22c5c8: (4, 'ba4f1f0d0c1e481920876366ee370346ebf42e8da851659252b40221b5a5a837'),
              0x22c5cc: (4, '0a2a9a6e50348179851b374615dd581bcc5bdd54edc2eeb08ba9c9f158ffa34f'),
              0x22c1a0: (4, '25ac6dee3ad9b1b847dd4a7f58c9da50ecc88e5dfe44a1716801cf71a9cc04c2'),
              0x22c1ac: (4, 'a7c16ee8d19647ef13b4708f5e7598bec8ce7350ec3e8d1e93a2098c3f97e28d'),
              0x2686dc: (4, '502a3b255ed7cc427ef55eaf5073f921bbff59ac41497c00ddf16b6e9bfd8eb3'),
              0x22bc74: (4, 'd6afd0e6bcaa67a178760591cc69dec7766979e12c3b6f8a95b48e544a4a3d06'),
              0x22bc78: (4, '880235b598f044c52592e33e3cd836915769ecaf9762a048064f50d5ea50d779'),
              0x22bc7c: (4, 'beaedf428103ba685c34f5ce2f6f223acd77d09ff3f96ae915555827610126b5'),
              0x2687b0: (4, '245feb5441f955f0a0f387de0f2a37965c72c821650bbb0ab5e51ce333411543'),
              0x2687b8: (4, '88db43c2f8f852f2297c32105a943920a19a343148a8c0899d8d29e21eba4c5c'),
              0x268818: (4, 'c4e76954872f97823b3ec29845f79673eade60ad5382ea4043c5bbd5d055313b'),
              0x268828: (4, '8064550b7b74f5d5b829ede2efe6e11d2ab77a422e4ced8e9944c6bd84121857'),
              0x2340e8: (4, '4bd0fb906432980c4452e97bf9b0ac4f7ed4473b745a562c94763e598731571d'),
              0x267d38: (4, '027fbb2e49ccbd3f92bbc5a25f3634718490e184a32a14644bf88d8536af67ca'),
              0x267d3c: (4, '96a629d1979d6727f7ac724cb69678a80890c5ca0a380f7bdbb45ee177774172'),
              0x267d40: (4, '82d6893b032b3468fe55cd43ab2e61ff55b75ff4881f4e39f32870b882c7f48e'),
              0x267d50: (4, '4009ed2d8e464ae54c79b4393388cd1fc7faa245a909ce3775c18db71b7e6864'),
              0x267d5c: (4, 'b4d66121d8e845b872c07a128d3e188b886d38f31751d17c494dfa1856d40a00')}
    for address, (length, expected) in checks.items():
        if sha(image[address - 0x100000:address - 0x100000 + length]) != expected:
            raise ValueError('GT3 native instruction mismatch at ' + hex(address))
    evidence = {'source': str(Path(source).resolve()), 'source_sha256': GT3_CORE_SHA256,
                'segment_sha256': sha(image), 'segment_address': 0x100000,
                'segment_inflated_offset': 276, 'rsa_status': 'PRESENT_NOT_AUTHENTICATED',
                'instruction_checks': [{'address': hex(a), 'inflated_offset': a - 0x100000 + 276,
                                        'length': n, 'sha256': h,
                                        'bytes': image[a - 0x100000:a - 0x100000 + n].hex()} for a, (n, h) in checks.items()],
                'evidence_type': 'STATIC_ORIGINAL_CODE_GHIDRA_R5900_AND_RABBITIZER',
                'boundary': 'Original GT3 container identity and bytes; reconstructed ELF analysis. No runtime execution or RSA authentication.'}
    return image, evidence


def _pitch_word(table, requested, base):
    delta, shift = requested - base, -2
    while delta < 0:
        delta += 0xc00
        shift -= 1
    while delta >= 0xc00:
        delta -= 0xc00
        shift += 1
    value = table[delta >> 3]
    return ((value >> ((-shift) & 31)) if shift <= 0 else (value << (shift & 31))) & 65535


def native_event_mapping(volume, core):
    """Bind named GTSE entries to original GT3 native bank/voice selectors.

    Leaf pitch is recovered; full runtime envelopes, volume, layering and any
    later pitch modulation remain separate from this source audition.
    """
    image, native = _qualified_native_core(core)
    def data(address, size):
        off = address - 0x100000
        if not 0 <= off < off + size <= len(image):
            raise ValueError('GT3 native evidence outside source segment')
        return image[off:off + size]
    native_names = {}
    for i in range(40):
        pointer = struct.unpack('<I', data(0x2e9380 + i * 8, 4))[0]
        name = data(pointer, 80).split(b'\0')[0].decode('ascii')
        native_names[name] = i
    table_bytes = data(0x345ae8, 384 * 2)
    table = struct.unpack('<384H', table_bytes)
    native['pitch_table'] = {'address': '0x345ae8', 'entries': 384, 'sha256': sha(table_bytes)}
    raw_events, event_source = read_member(Path(volume), 'sound/se.inf')
    if sha(raw_events) != GT3_EVENT_SHA256:
        raise ValueError('unqualified original GT3 GTSE SHA256')
    banks = []
    for member, expected in GT3_NATIVE_BANKS:
        report = inspect_member(volume, member)
        if report['sha256'] != expected:
            raise ValueError('unqualified original GT3 native INST bank SHA256')
        banks.append(report)
    result = []
    for row in events(raw_events):
        token = int(row['token'], 16)
        bank_index = token >> 24
        if bank_index >= len(banks):
            raise ValueError('GT3 token bank outside native loader table')
        bank = banks[bank_index]
        lanes = []
        for lane, index in (('primary', token >> 12 & 4095), ('secondary', token & 4095)):
            matches = [e for e in bank['entries'] if e['index'] == index]
            if len(matches) != 1:
                raise ValueError('GT3 event voice outside original bank')
            voice = matches[0]
            record = bytes.fromhex(voice['record_hex'])
            base = struct.unpack_from('<H', record, 8)[0]
            pitch = _pitch_word(table, record[16] << 8, base)
            lanes.append({'lane': lane, 'member': bank['member'], 'entry_id': voice['entry_id'],
                          'voice_index': index, 'sample': voice,
                          'pitch_word': pitch, 'requested_note_fixed8': record[16] << 8,
                          'base_note_fixed8': base, 'wave_rate_hz_at_48k_clock': 48000 * pitch / 4096,
                          'pitch_boundary': 'Native leaf note/pitch lookup; rate conversion assumes nominal SPU2 48000Hz clock. No later modulation or full mix reproduced.'})
        native_id = native_names.get(row['name'])
        result.append({**row, 'native_event_id': native_id, 'bank_index': bank_index,
                       'status': 'NATIVE_EVENT_BANK_VOICE_RECOVERED' if native_id is not None else 'GTSE_TOKEN_LAYOUT_RECOVERED_NATIVE_ENUM_ABSENT',
                       'lanes': lanes})
    return {'game': 'GT3', 'status': 'STATIC_NATIVE_EVENT_ROUTING_RECOVERED',
            'events': result, 'event_source': event_source, 'native_evidence': native,
            'native_names_missing_from_gtse': sorted(set(native_names) - {e['name'] for e in result}),
            'bank_sources': [b['source'] for b in banks],
            'boundary': 'Source event-to-sample association and native leaf pitch only. Event name does not prove real-world acoustic identity. Exact gameplay mix, ADSR, LFO, volume, modulation and SPU2 output remain untested.'}


def export_event(volume, core, event_name, output, lane='primary'):
    mapping = native_event_mapping(volume, core)
    matches = [e for e in mapping['events'] if e['name'] == event_name]
    if len(matches) != 1 or matches[0]['native_event_id'] is None:
        raise ValueError('one original GT3 event with native enum binding required')
    event = matches[0]
    matches = [e for e in event['lanes'] if e['lane'] == lane]
    if len(matches) != 1:
        raise ValueError('GT3 event lane must be primary or secondary')
    selection = matches[0]
    if selection['pitch_word'] == 0:
        raise ValueError('zero native pitch cannot be represented as WAV')
    rate = round(selection['wave_rate_hz_at_48k_clock'])
    result = export_member(volume, selection['member'], selection['entry_id'], output, rate)
    result.update(source_event_name=event_name, event=event, native_evidence=mapping['native_evidence'],
                  playback_rate_provenance='original GT3 native leaf pitch word; nominal 48000Hz SPU2 clock conversion rounded to WAV Hz',
                  boundary=mapping['boundary'])
    Path(output).with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def _engn_pitch_word(reference_rpm, base_pitch, rpm, multiplier=4096):
    # Original 0x267d50 is DIVU, even though the decompiler renders a signed
    # division. Preserve the original low32 multiply and unsigned division.
    denominator = reference_rpm & 0xffffffff
    if denominator == 0:
        raise ValueError('zero GT3 native reference RPM')
    quotient = ((base_pitch * rpm) & 0xffffffff) // denominator
    pitch = ((quotient * multiplier) & 0xffffffff) >> 12
    return max(1, pitch) & 65535


def native_engn_pitch(volume, core, member, entry_id, rpm=None):
    _, native = _qualified_native_core(core)
    report = inspect_member(volume, member)
    if report['format'] != 'ENGN':
        raise ValueError('GT3 native engine pitch requires ENGN')
    matches = [e for e in report['entries'] if e['entry_id'] == entry_id]
    if len(matches) != 1:
        raise ValueError('one GT3 ENGN entry_id required')
    entry = matches[0]
    record = bytes.fromhex(entry['record_hex'])
    reference = struct.unpack_from('<h', record)[0]
    base_pitch = struct.unpack_from('<I', record, 8)[0]
    rpm = reference if rpm is None else rpm
    if type(rpm) is not int or not 200 <= rpm <= 20000 or not 200 <= reference <= 20000:
        raise ValueError('GT3 engine audition RPM outside 200..20000')
    pitch = _engn_pitch_word(reference, base_pitch, rpm)
    return {'source': report['source'], 'entry_id': entry_id, 'reference_rpm': reference,
            'requested_rpm': rpm, 'base_pitch_word_u32': base_pitch,
            'pitch_word': pitch, 'wave_rate_hz_at_48k_clock': 48000 * pitch / 4096,
            'native_evidence': native,
            'boundary': 'Original GT3 ENGN pitch before previous-frame smoothing, with source-initial multiplier4096. Single raw sample at nominal 48000Hz SPU2 clock; no layering, gains, doppler or full runtime mix.'}


def _stream(raw, begin, end):
    """Validate block grammar; distinguish repeat from one-shot start markers.

    GT3 one-shots retain flag4 but terminate with flag1 and a canonical silent
    flag7 tail. That marker does not establish an active loop.
    """
    if not 0 <= begin < end <= len(raw) or (end - begin) % 16:
        raise ValueError('invalid GT3 SPU span')
    marker = None
    terminal = None
    flags_seen = collections.Counter()
    for at in range(begin, end, 16):
        header, flag = raw[at:at + 2]
        if header >> 4 >= 5 or header & 15 > 12 or flag not in (0, 1, 2, 3, 4, 6):
            raise ValueError('unsupported GT3 SPU frame before terminal')
        flags_seen[flag] += 1
        if flag in (4, 6):
            if marker is not None:
                raise ValueError('multiple GT3 SPU start markers')
            marker = (at - begin) // 16 * 28
        if flag in (1, 3):
            terminal = at + 16
            break
    if terminal is None:
        raise ValueError('GT3 SPU stream missing terminal')
    tail = raw[terminal:end]
    if tail and tail != bytes.fromhex('0007' + '77' * 14):
        raise ValueError('unaccounted GT3 SPU trailer')
    repeat = raw[terminal - 15] == 3
    if repeat and marker is None:
        raise ValueError('GT3 repeat terminal without start marker')
    count = (terminal - begin) // 16 * 28
    return {'sample_file_offset': begin, 'encoded_bytes': terminal - begin,
            'allocated_bytes': end - begin, 'padding_bytes': len(tail),
            'encoded_sha256': sha(raw[begin:terminal]), 'samples': count,
            'loop_start_marker_sample': marker,
            'loop_start_sample': marker if repeat else None,
            'loop_end_sample': count if repeat else None,
            'frame_flags': {str(k): v for k, v in sorted(flags_seen.items())},
            'codec_status': 'PCM_VALID'}


def decode_sample(raw, entry):
    """Return deterministic mono signed16 PCM; no nominal pitch is inferred."""
    begin = entry['sample_file_offset']
    size = entry['encoded_bytes']
    if not 0 <= begin < begin + size <= len(raw) or size % 16:
        raise ValueError('invalid explicit sample range')
    _stream(raw, begin, begin + size)
    h1 = h2 = 0
    samples = []
    for at in range(begin, begin + size, 16):
        header = raw[at]
        a, b = COEFFICIENTS[header >> 4]
        shift = header & 15
        for value in raw[at + 2:at + 16]:
            for nibble in (value & 15, value >> 4):
                nibble = nibble - 16 if nibble >= 8 else nibble
                pcm = ((nibble << 12) >> shift) + ((h1 * a + h2 * b + 32) >> 6)
                pcm = max(-32768, min(32767, pcm))
                samples.append(pcm)
                h2, h1 = h1, pcm
    return samples


def inspect_bank(raw):
    if not 40 <= len(raw) <= MAX_BANK or raw[:4] not in (b'ENGN', b'INST'):
        raise ValueError('bounded GT3 ENGN or INST required')
    reloc, hsize, runtime, bsize, body = struct.unpack_from('<5I', raw, 4)
    if reloc or runtime or hsize > body or body - hsize > 16 or body + bsize != len(raw) or bsize % 16 or any(raw[hsize:body]):
        raise ValueError('unsupported GT3 bank relocation/body layout')
    fmt = raw[:4].decode('ascii')
    rows = []
    programs = []
    if fmt == 'ENGN':
        if hsize < 48 or hsize != body:
            raise ValueError('unsupported GT3 ENGN header')
        occupied = set(range(48))
        tables = [struct.unpack_from('<II', raw, 24 + i * 8) for i in range(2)]
        if not 1 <= sum(n for n, _ in tables) <= 32:
            raise ValueError('GT3 ENGN entry count budget')
        for table, (count, at) in enumerate(tables):
            if not count:
                if at:
                    raise ValueError('unexpected empty GT3 ENGN table pointer')
                continue
            if at < 48 or at % 16 or at + count * 16 > hsize:
                raise ValueError('GT3 ENGN table outside header')
            span = set(range(at, at + count * 16))
            if span & occupied:
                raise ValueError('overlapping GT3 ENGN tables')
            occupied |= span
            for index in range(count):
                pos = at + 16 * index
                words = struct.unpack_from('<6HI', raw, pos)
                if words[5] or words[6] % 16 or words[6] >= bsize:
                    raise ValueError('unqualified GT3 ENGN sample pointer/reserved word')
                rows.append({'entry_id': f'table{table}:{index}', 'table': table,
                             'index': index, 'record_offset': pos,
                             'record_hex': raw[pos:pos + 16].hex(),
                             'words_u16': list(words[:6]), 'body_offset': words[6]})
        if any(raw[j] for j in range(48, hsize) if j not in occupied):
            raise ValueError('unaccounted GT3 ENGN header data')
    else:
        count, records, nprog, table = struct.unpack_from('<4I', raw, 24)
        if not 1 <= count <= 4096 or records != 40 or table != records + count * 24 or not 1 <= nprog <= 256 or table + nprog * 4 > hsize:
            raise ValueError('unsupported GT3 INST tables')
        for index in range(count):
            at = records + index * 24
            rec = raw[at:at + 24]
            offset = struct.unpack_from('<I', rec)[0] * 8
            if offset % 16 or offset >= bsize:
                raise ValueError('GT3 INST SSA outside body')
            rows.append({'entry_id': f'voice:{index}', 'index': index,
                         'record_offset': at, 'record_hex': rec.hex(),
                         'ssa_raw_u32': offset // 8, 'body_offset': offset,
                         'note_window_raw': list(rec[16:18]),
                         'record_words_u16': list(struct.unpack('<12H', rec))})
        cursor = table + nprog * 4
        for index in range(nprog):
            at = struct.unpack_from('<I', raw, table + index * 4)[0]
            if at != cursor or at + 4 > hsize:
                raise ValueError('GT3 INST program pointer/span mismatch')
            n = raw[at]
            end = (at + 4 + n + 3) & ~3
            if not n or end > hsize:
                raise ValueError('GT3 INST program outside header')
            voices = list(raw[at + 4:at + 4 + n])
            if any(v >= count for v in voices) or any(raw[at + 4 + n:end]):
                raise ValueError('GT3 INST program voice/padding invalid')
            programs.append({'program': index, 'pointer_offset': table + index * 4,
                             'record_offset': at, 'header_hex': raw[at:at + 4].hex(),
                             'voice_indices': voices})
            cursor = end
        if cursor != hsize:
            raise ValueError('unaccounted GT3 INST header bytes')
    offsets = sorted({r['body_offset'] for r in rows})
    if offsets[0] != 0 or (fmt == 'ENGN' and len(offsets) != len(rows)):
        raise ValueError('unaccounted/duplicate GT3 sample spans')
    spans = dict(zip(offsets, offsets[1:] + [bsize]))
    decoded = {}
    for offset, end in spans.items():
        decoded[offset] = _stream(raw, body + offset, body + end)
    for row in rows:
        row.update(decoded[row['body_offset']])
    return {'format': fmt, 'status': 'GT3_STRUCTURAL_AND_CODEC_VALID',
            'sha256': sha(raw), 'bytes': len(raw), 'header_bytes': hsize,
            'body_offset': body, 'body_bytes': bsize, 'entries': rows,
            'unique_samples': len(offsets), 'programs': programs,
            'ssa_scale_evidence': 'INST u32*8: original GT3 native relocator0x268630 shifts SPU byte-base delta right3 at0x2686dc; exact-build hash/bytes available through native_event_mapping. Complete aligned body partition and valid SPU frames corroborate.' if fmt == 'INST' else None,
            'boundary': BOUNDARY}


def _strings(raw):
    if len(raw) < 16 or raw[:4] != b'STDB':
        raise ValueError('GT3 STDB required')
    count, encoding, reserved, size = struct.unpack_from('<IhhI', raw, 4)
    if size != len(raw) or reserved or encoding not in (1, 2, -1) or count > 100000 or 16 + count * 4 > len(raw):
        raise ValueError('unsupported GT3 STDB layout')
    result = []
    for i in range(count):
        at = struct.unpack_from('<I', raw, 16 + i * 4)[0]
        if at < 16 + count * 4 or at + 2 > len(raw):
            raise ValueError('GT3 STDB string outside data')
        n = struct.unpack_from('<H', raw, at)[0]
        if at + 2 + n > len(raw):
            raise ValueError('GT3 STDB string outside member')
        b = raw[at + 2:at + 2 + n]
        # Preserve unresolved multibyte text as escaped bytes instead of
        # assuming the -1 flag is EUC-JP (local converter fails on this corpus).
        result.append(b.decode('utf-16le').rstrip('\0') if encoding == 2 else b.decode('ascii', 'backslashreplace').rstrip('\0'))
    return result


def _tables(raw):
    if len(raw) < 20 or raw[:4] != b'GTAR':
        raise ValueError('GT3 GTAR required')
    count, head, mask = struct.unpack_from('<3I', raw, 4)
    if count != 36 or mask != 7 or head != (16 + 4 * (count + 1) + 7) & ~7:
        raise ValueError('unsupported GT3 GTAR index')
    tables = []
    cursor = head
    for i in range(count):
        at = head + struct.unpack_from('<I', raw, 16 + 4 * i)[0]
        if at != cursor or at + 16 > len(raw) or raw[at:at + 4] != b'GTDT':
            raise ValueError('invalid GT3 GTDT span')
        version, tid, n, size, span = struct.unpack_from('<HhHHI', raw, at + 4)
        if version != 2087 or tid != i or not size or span != 16 + n * size or at + span > len(raw):
            raise ValueError('unqualified GT3 GTDT layout')
        tables.append({'offset': at, 'row_size': size,
                       'rows': [(at + 16 + j * size, raw[at + 16 + j * size:at + 16 + (j + 1) * size]) for j in range(n)]})
        cursor = at + span
    if cursor != len(raw) or head + struct.unpack_from('<I', raw, 16 + 4 * count)[0] != len(raw):
        raise ValueError('unaccounted GT3 GTAR trailer')
    return tables


def vehicle_mapping(volume, region='us'):
    if region not in ('us', 'eu', 'jp'):
        raise ValueError('GT3 region must be us, eu or jp')
    suffix = '' if region == 'jp' else '_' + region
    sources = {}
    def member(name):
        b, o = read_member(volume, f'database/{name}{suffix}.db')
        sources[name] = o
        return b
    db = _tables(member('paramdb'))
    labels = _strings(member('.id_db_str'))
    strings = _strings(member('paramstr'))
    names = _strings(member('paramunistr'))
    raw_ids = member('.id_db_idx')
    if raw_ids[:4] != b'IDDB' or len(raw_ids) < 8:
        raise ValueError('GT3 IDDB required')
    count = struct.unpack_from('<I', raw_ids, 4)[0]
    if count > 100000 or 8 + count * 16 != len(raw_ids):
        raise ValueError('GT3 IDDB length mismatch')
    ids = {}
    for i in range(count):
        key, value = struct.unpack_from('<Qq', raw_ids, 8 + i * 16)
        if key in ids or not 0 <= value < len(labels):
            raise ValueError('GT3 IDDB ambiguous label')
        ids[key] = labels[value]
    if db[6]['row_size'] != 88 or db[30]['row_size'] != 264:
        raise ValueError('unqualified GT3 CAR/ENGINE row size')
    engines = {}
    for at, row in db[6]['rows']:
        key = struct.unpack_from('<Q', row)[0]
        if key in engines:
            raise ValueError('duplicate GT3 engine key')
        engines[key] = (at, row)
    parts = {ti: {struct.unpack_from('<Q', row)[0]: (at, row) for at, row in db[ti]['rows']}
             for ti in (12, 20)}
    def part(ti, size, key):
        if key == 0:
            return None
        if db[ti]['row_size'] != size or key not in parts[ti]:
            raise ValueError('unqualified GT3 default tuning-part reference')
        return parts[ti][key]
    cars = []
    for at, row in db[30]['rows']:
        car_key = struct.unpack_from('<Q', row)[0]
        engine_key = struct.unpack_from('<Q', row, 56)[0]
        if engine_key not in engines or car_key not in ids or engine_key not in ids:
            raise ValueError('unresolved GT3 CAR/ENGINE key')
        eat, engine = engines[engine_key]
        owner_key = struct.unpack_from('<Q', engine, 8)[0]
        label_index = struct.unpack_from('<H', row, 232)[0]
        name_indices = struct.unpack_from('<2H', row, 228)
        maker_index = struct.unpack_from('<H', row, 260)[0]
        if label_index >= len(strings) or max(*name_indices, maker_index) >= len(names):
            raise ValueError('GT3 vehicle string index outside database')
        label = ids[car_key]
        if label != strings[label_index]:
            raise ValueError('GT3 CAR label sources disagree')
        muffler = part(20, 24, struct.unpack_from('<Q', row, 176)[0])
        turbine = part(12, 40, struct.unpack_from('<Q', row, 104)[0])
        muffler_category = muffler[1][16] if muffler else 0
        wastegate = turbine[1][17] if turbine else 0
        if muffler_category > 3:
            raise ValueError('GT3 default muffler category outside native bank table')
        category = ('turbo' if wastegate else 'normal') + str(muffler_category)
        cars.append({'car_label': label, 'name': ' '.join(names[i].strip() for i in name_indices).strip(),
                     'maker': names[maker_index].strip(), 'year': struct.unpack_from('<H', row, 234)[0],
                     'car_key': f'0x{car_key:016x}', 'engine_key': f'0x{engine_key:016x}',
                     'engine_label': ids[engine_key], 'sound_number': struct.unpack_from('<H', engine, 22)[0],
                     'engine_owner_key': f'0x{owner_key:016x}', 'engine_owner_label': ids.get(owner_key),
                     'engine_owner_matches_car': owner_key == car_key,
                     'car_row_offset': at, 'car_row_sha256': sha(row),
                     'engine_row_offset': eat, 'engine_row_sha256': sha(engine),
                     'default_secondary_bank_category': category,
                     'default_muffler_category': muffler_category, 'default_turbine_wastegate_raw': wastegate,
                     'default_muffler_row_offset': muffler[0] if muffler else None,
                     'default_turbine_row_offset': turbine[0] if turbine else None,
                     'default_bank_selection_evidence': 'CAR default part keys; original GT3 0x2340f8 reads MUFFLER table20 byte16 and adds4 iff TURBINEKIT table12 byte17!=0 (0x234048). Active modified parts/runtime state remain separate.',
                     'source_status': 'GT3_CAR_ENGINE_KEY_CHAIN_RECOVERED'})
    return {'region': region, 'sources': sources, 'vehicles': cars,
            'qualified_layout': 'GTAR36/GTDT v2087: CAR table30 size264 ENGINE key u64@56; ENGINE table6 size88 soundNum u16@22 and owner key@8',
            'text_policy': 'ASCII retained; unknown multibyte bytes escaped. No inferred short model-code association.'}


def inspect_member(volume, member):
    raw, source = read_member(Path(volume), member)
    return {**inspect_bank(raw), 'source': source, 'member': member, 'game': 'GT3'}


def catalog(volume, include_banks=True, region='us'):
    volume = Path(volume)
    rows = inventory(volume)
    banks = []
    for row in rows:
        if not row['path'].startswith('sound/') or row['path'] == 'sound/se.inf':
            continue
        member = row['path']
        if row['size'] > MAX_BANK or row['uncompressed_size'] > MAX_BANK:
            raise ValueError('GT3 audio member exceeds bank budget')
        if row['compressed']:
            raw, source = read_member(volume, member)
        else:
            # inventory already checked all source spans. Reusing those spans
            # avoids parsing the 5333-member RoFS once per sound bank.
            with volume.open('rb') as stream:
                stream.seek(row['offset'])
                raw = stream.read(row['size'])
            if len(raw) != row['size']:
                raise ValueError('truncated GT3 catalog source member')
            source = {**row, 'stored_sha256': sha(raw), 'decoded_sha256': sha(raw),
                      'inventory_count': len(rows)}
        parts = member.split('/')
        bank = {'bank_id': member, 'member': member,
                'category': parts[1] if len(parts) == 3 else 'instrument' if raw[:4] == b'INST' else 'other',
                'sound_number': int(parts[-1]) if parts[-1].isdigit() else None,
                'source': source, 'format': raw[:4].decode('ascii', 'backslashreplace')}
        if include_banks:
            try:
                bank['inspection'] = inspect_bank(raw)
            except ValueError as error:
                bank['inspection'] = {'status': 'UNSUPPORTED', 'error': str(error), 'entries': []}
        banks.append(bank)
    mapping = vehicle_mapping(volume, region)
    for car in mapping['vehicles']:
        car['bank_ids'] = [b['bank_id'] for b in banks if b['sound_number'] == car['sound_number']]
        car['default_secondary_bank_ids'] = [b['bank_id'] for b in banks if b['sound_number'] == car['sound_number'] and b['category'] == car['default_secondary_bank_category']]
    raw, event_source = read_member(volume, 'sound/se.inf')
    return {'game': 'GT3', 'status': 'STATIC_SOURCE_CATALOG',
            'volume': {'path': str(volume.resolve()), 'size': volume.stat().st_size, 'inventory_count': len(rows)},
            'banks': banks, 'vehicles': mapping['vehicles'], 'events': events(raw),
            'event_source': event_source, 'event_routing_status': 'OPAQUE_TOKENS_NO_SAMPLE_ATTRIBUTION',
            'database_sources': mapping['sources'], 'mapping_layout': mapping['qualified_layout'],
            'text_policy': mapping['text_policy'],
            'summary': {'banks': len(banks), 'vehicles': len(mapping['vehicles']),
                        'categories': dict(collections.Counter(b['category'] for b in banks)),
                        'inspection_status': dict(collections.Counter(b.get('inspection', {}).get('status', 'NOT_REQUESTED') for b in banks))},
            'boundary': BOUNDARY}


def export_member(volume, member, entry_id, output, sample_rate):
    output = Path(output)
    if output.exists() or output.with_suffix('.json').exists():
        raise ValueError('new WAV and sidecar paths required')
    raw, source = read_member(Path(volume), member)
    report = inspect_bank(raw)
    matches = [e for e in report['entries'] if e['entry_id'] == entry_id]
    if len(matches) != 1:
        raise ValueError('select exactly one existing GT3 entry_id')
    entry = matches[0]
    pcm = decode_sample(raw, entry)
    loop = None if entry['loop_start_sample'] is None else (entry['loop_start_sample'], entry['loop_end_sample'])
    wav = pcm_wav(pcm, sample_rate, loop)
    result = {'game': 'GT3', 'source': source, 'selection': entry,
              'sample_rate': sample_rate, 'wav_sha256': sha(wav),
              'bank_sha256': report['sha256'], 'authentic_effect_identity': None,
              'playback_rate_provenance': 'explicit caller-selected nominal audition Hz; native GT3 pitch not recovered',
              'boundary': BOUNDARY}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(wav)
    output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--volume', type=Path)
    source.add_argument('--core', type=Path, help='reconstruct offline native ELF from the original GT3 CORE')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--member')
    p.add_argument('--entry-id')
    p.add_argument('--sample-rate', type=int)
    p.add_argument('--native-core', type=Path, help='exact original GT3 CORE for static native event mapping/pitch')
    p.add_argument('--event', help='export one native-bound GTSE event at its recovered leaf pitch')
    p.add_argument('--lane', choices=('primary', 'secondary'), default='primary')
    p.add_argument('--region', choices=('us', 'eu', 'jp'), default='us')
    a = p.parse_args()
    if a.core:
        result = unpack_core(a.core, a.output)
    elif a.event:
        if not a.native_core:
            p.error('--event requires --native-core')
        result = export_event(a.volume, a.native_core, a.event, a.output, a.lane)
    elif a.entry_id:
        if not a.member or a.sample_rate is None:
            p.error('audition requires --member and explicit nominal --sample-rate')
        result = export_member(a.volume, a.member, a.entry_id, a.output, a.sample_rate)
    else:
        if a.sample_rate is not None:
            p.error('--sample-rate applies only to selected audition')
        if a.output.exists():
            raise ValueError('new report path required')
        result = native_event_mapping(a.volume, a.native_core) if a.native_core else inspect_member(a.volume, a.member) if a.member else catalog(a.volume, region=a.region)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'summary', 'wav_sha256') if k in result}))


if __name__ == '__main__':
    main()
