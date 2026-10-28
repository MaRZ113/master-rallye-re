"""Read-only priority format probes; metadata only, no game/importer execution.

PDI1 field observations were cross-checked against GameExtractor's public
Plugin_PDT_PDI1. This independent bounded directory probe does not decode TEA,
LZSS, meshes or textures, and does not reproduce that GPL implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import stat
import struct

MAX_FILE = 64 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_source(path, limit=MAX_FILE):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        info = part.lstat()
        if part.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('linked/reparse source rejected')
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError('source file budget/type')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    after = path.stat()
    if len(data) > limit or (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError('source changed or exceeds budget')
    return data


def safe_name(raw):
    value = raw.split(b'\0', 1)[0].decode('ascii')
    if not value or any(c in value for c in '/\\:') or value in ('.', '..') or any(ord(c) < 32 for c in value):
        raise ValueError('unsafe source member name')
    return value


def pdi_directory(data):
    """Inspect directory and wrapper spans only. No reconstructed virtual paths."""
    if len(data) < 28 or data[:4] != b'PDI1':
        raise ValueError('PDI1 signature/header')
    slots, used, unknown, directory, cdi, declared = struct.unpack_from('<6I', data, 4)
    if not 0 < used <= slots <= 200000 or directory < 28 or directory + slots * 68 != cdi:
        raise ValueError('PDI1 directory count/range')
    if cdi + declared != len(data) or data[cdi:cdi + 4] != b'CDI1':
        raise ValueError('PDI1 CDI1 range/signature')
    entries = []; counts = Counter(); ranges = []
    for index in range(slots):
        at = directory + index * 68
        kind = struct.unpack_from('<H', data, at)[0]
        counts[kind] += 1
        if index >= used:
            if kind != 0:
                raise ValueError('PDI1 non-padding entry after used count')
            continue
        if kind not in (4, 24, 25):
            raise ValueError('PDI1 unsupported directory entry type')
        name = safe_name(data[at + 20:at + 64])
        entry = {'index': index, 'record_offset': at, 'type': kind, 'name': name}
        if kind == 4:
            entry['unresolved_directory_links'] = list(struct.unpack_from('<5h', data, at + 2))
        else:
            relative, length = struct.unpack_from('<II', data, at + 12)
            # Observed records occupy CDI1+relative .. +length. The wrapper is
            # four bytes later; reported GE exporter payload uses length-12.
            # This probe validates both ranges but exports neither.
            start = cdi + relative
            wrapper = start + 4
            if length < 12 or start < cdi or start + length > len(data):
                raise ValueError('PDI1 member range')
            expanded, zero, flags = struct.unpack_from('<IHH', data, wrapper)
            if zero != 0 or expanded > MAX_FILE or flags not in (16, 17):
                raise ValueError('PDI1 unqualified wrapper/budget')
            entry.update(relative_offset=relative, record_span=[start, length], wrapper_offset=wrapper,
                         declared_decoded_bytes=expanded, wrapper_flags=flags,
                         encoded_payload_span=[wrapper + 8, length - 12],
                         payload_status='UNSUPPORTED: TEA' + (' + LZSS8' if flags == 17 else ''))
            ranges.append((start, start + length))
        entries.append(entry)
    ordered = sorted(ranges)
    if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('PDI1 overlapping member spans')
    return {'status': 'PASS', 'scope': 'directory and encoded-wrapper ranges only',
            'slots': slots, 'used_records': used, 'unknown_u32_at12': unknown,
            'directory_offset': directory, 'cdi1_offset': cdi, 'cdi1_length': declared,
            'entry_types': dict(counts), 'entries': entries,
            'warning': 'Variable directory offset validated from header; no forced46. Directory hierarchy links and decoded payloads remain unqualified.'}


def pssg_dictionary(data):
    if len(data) < 16 or data[:4] != b'PSSG':
        raise ValueError('PSSG signature/header')
    stored, attr_count, node_count = struct.unpack_from('>3I', data, 4)
    if stored != len(data) - 8 or not 0 < node_count <= 4096 or not 0 <= attr_count <= 32768:
        raise ValueError('PSSG size/count budget')
    cursor = 16

    def number():
        nonlocal cursor
        if cursor + 4 > len(data):
            raise ValueError('PSSG truncated dictionary')
        value = struct.unpack_from('>I', data, cursor)[0]; cursor += 4
        return value

    def name():
        nonlocal cursor
        length = number()
        if not 0 < length <= 256 or cursor + length > len(data):
            raise ValueError('PSSG string budget/range')
        raw = data[cursor:cursor + length]; cursor += length
        if any(x < 32 or x > 126 for x in raw):
            raise ValueError('PSSG non-ascii dictionary')
        return raw.decode('ascii')

    nodes = []; attributes = set(); node_ids = set(); duplicates = []; total_attributes = 0
    for _ in range(node_count):
        node_id = number(); label = name(); count = number()
        if node_id in node_ids or not 0 < node_id <= node_count or count > attr_count:
            raise ValueError('PSSG node ID/attribute count')
        node_ids.add(node_id); fields = []
        for _ in range(count):
            attr_id = number(); label_attr = name()
            if not 0 < attr_id <= attr_count:
                raise ValueError('PSSG outside attribute ID')
            if attr_id in attributes:
                duplicates.append({'id': attr_id, 'node': label, 'name': label_attr})
            attributes.add(attr_id); fields.append({'id': attr_id, 'name': label_attr})
            total_attributes += 1
        nodes.append({'id': node_id, 'name': label, 'attributes': fields})
    if total_attributes != attr_count:
        raise ValueError('PSSG aggregate attribute count')
    return {'status': 'WARN' if duplicates else 'PASS', 'scope': 'header/dictionary only; no scene tree or mesh decode',
            'big_endian_size_field': stored, 'node_types': node_count,
            'attribute_types': attr_count, 'dictionary_end': cursor,
            'nodes': nodes, 'duplicate_attribute_ids': duplicates,
            'mesh_status': 'NOT TESTED', 'texture_status': 'NOT TESTED'}


def opaque_markers(data):
    found = {}
    for token in (b'RallyCar 1.00', b'ArchList', b'Gex#MainBody.x'):
        offsets = []; start = 0
        while len(offsets) < 64:
            position = data.find(token, start)
            if position < 0:
                break
            offsets.append(position); start = position + len(token)
        found[token.decode('ascii')] = offsets
    return {'status': 'WARN', 'scope': 'opaque TC header; bounded literal-marker observations',
            'markers': found, 'mesh_status': 'UNSUPPORTED',
            'identity': 'Pajero filename lead only; no V60/V20 or shared MR geometry evidence'}


def car_catalog(data):
    """Locally observed fixed record candidate, not a general Cars.BIN decoder."""
    stride = 1608
    if len(data) != 24 * stride:
        raise ValueError('unqualified Cars.BIN observed layout')
    records = []; seen = set()
    for index in range(24):
        at = index * stride; number = struct.unpack_from('<I', data, at + 28)[0]
        raw = data[at + 32:at + 64].split(b'\0', 1)[0]
        if not 0 < number < 100 or number in seen or not raw or any(x < 32 for x in raw):
            raise ValueError('Cars.BIN ID/label layout mismatch')
        seen.add(number)
        records.append({'record': index, 'offset': at, 'candidate_car_id': number,
                        'label_offset': at + 32, 'label': raw.decode('latin1')})
    return {'status': 'WARN', 'record_stride': stride, 'records': records,
            'boundary': 'Observed fixed-stride ID/label association; full record semantics/runtime consumer not decoded.'}


def validate_output(source_root, output):
    source_root = Path(source_root).absolute(); output = Path(output).absolute()
    for part in (output, *output.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('linked/reparse output rejected')
    source_root = source_root.resolve(); output = output.resolve()
    if output.is_relative_to(source_root) or source_root.is_relative_to(output):
        raise ValueError('output must be outside source collection')
    if output.exists():
        raise ValueError('output exists; choose a fresh report path')


def run(root):
    root = Path(root)
    report = {'schema': 'source-garage-priority-probe/1', 'files': {},
              'boundary': 'Read-only source metadata; no asset export, game execution, vehicle importer or gameplay qualification.'}
    jobs = {
        'Paris-Dakar Rally/Data/PajeroRED.tc': opaque_markers,
        'Paris-Dakar Rally/Data/PajeroSilver.tc': opaque_markers,
        'Michelin Rally Masters/Data/Objects/Car01D.PDO': pdi_directory,
        'Michelin Rally Masters/Data/Objects/Car06A.PDO': pdi_directory,
        'Michelin Rally Masters/Data/Objects/Car25A.PDO': pdi_directory,
        'Michelin Rally Masters/Data/Objects/Track01_long.PDT': pdi_directory,
        'Michelin Rally Masters/Data/RallyMasters.DTA': pdi_directory,
        'Michelin Rally Masters/Server/Data/Cars.BIN': car_catalog,
        'DiRT/cars/131/131_gen_high.pssg': pssg_dictionary,
        'Dirt 2/cars/350/350_highLOD.pssg': pssg_dictionary,
    }
    for name, reader in jobs.items():
        try:
            data = read_source(root / name)
            item = {'size': len(data), 'sha256': digest(data)}
            try:
                item['inspection'] = reader(data)
            except (ValueError, UnicodeError, struct.error) as error:
                item['inspection'] = {'status': 'FAIL', 'error': str(error)}
            item['unchanged_after_inspection'] = digest(read_source(root / name)) == item['sha256']
            report['files'][name] = item
        except FileNotFoundError:
            report['files'][name] = {'status': 'MISSING INPUT'}
    script = 'Michelin Rally Masters/Server/Scripts/singlerace.scr'
    try:
        data = read_source(root / script, 1024 * 1024)
        lines = data.decode('ascii').splitlines(); rows = []
        for no, line in enumerate(lines, 1):
            if re.match(r'^\s*cars\s', line):
                tokens = line.split()[1:]
                if len(tokens) % 2 or any(not re.fullmatch(r'\d{2}', tokens[i]) or not re.fullmatch('[A-Z]', tokens[i + 1]) for i in range(0, len(tokens), 2)):
                    raise ValueError('unsupported cars script grammar')
                rows.append({'line': no, 'pairs': [tokens[i:i + 2] for i in range(0, len(tokens), 2)]})
        report['files'][script] = {'size': len(data), 'sha256': digest(data), 'cars_rows': rows,
                                 'unchanged_after_inspection': digest(read_source(root / script)) == digest(data)}
    except FileNotFoundError:
        report['files'][script] = {'status': 'MISSING INPUT'}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    validate_output(args.sources_root, args.output)
    result = run(args.sources_root)
    result['probe_sha256'] = digest(read_source(Path(__file__).resolve()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'output': str(args.output.resolve()), 'files': len(result['files']),
                      'failures': [name for name, value in result['files'].items() if value.get('inspection', {}).get('status') == 'FAIL']}))


if __name__ == '__main__':
    main()
