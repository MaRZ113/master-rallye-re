"""Bounded Michelin PDI1 payload research, not a qualified vehicle adapter.

Independent implementation of published TEA and conventional LZSS wire formats.
The Game Extractor GPL reader is a documented format lead, not vendored code.
No MR authoring, wheel fitting, coordinate conversion or inferred transparency.
"""
from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
import re
import struct

from ..universal_vehicle_scene import canonical, output_directory, read_bounded, relative_name, sha

VERSION = 'michelin-source-research/1'
MAX_FILE = 64 * 1024 * 1024
MAX_DECODED = 64 * 1024 * 1024
MAX_MEMBERS = 1024
MAX_GEOMETRY = 100000
TEA_KEY = b'THEEVENTHORIZONS'
TARGETS = ('Car25A.PDO', 'Car06A.PDO')


def _name(raw: bytes) -> str:
    if b'\0' not in raw:
        raise ValueError('unterminated PDI1 member name')
    try:
        name = raw.split(b'\0', 1)[0].decode('ascii')
    except UnicodeError as exc:
        raise ValueError('non-ASCII member name') from exc
    relative_name(name)
    if '/' in name:
        raise ValueError('PDI1 flat member name contains directory separator')
    return name


def directory(data: bytes) -> dict:
    """Preserve raw hierarchy links; never invent virtual paths from sentinels."""
    if not 28 <= len(data) <= MAX_FILE or data[:4] != b'PDI1':
        raise ValueError('PDI1 signature/header/byte budget')
    slots, used, unknown, start, cdi, size = struct.unpack_from('<6I', data, 4)
    if not 0 < used <= slots <= MAX_MEMBERS or start < 28 or start + slots * 68 != cdi:
        raise ValueError('PDI1 directory bounds/count')
    if cdi + size != len(data) or data[cdi:cdi + 4] != b'CDI1':
        raise ValueError('PDI1 CDI1 signature/range')
    entries = []; ranges = []; names = set(); decoded_total = 0
    for index in range(slots):
        offset = start + index * 68
        record = data[offset:offset + 68]
        kind, = struct.unpack_from('<H', record)
        if index >= used:
            if kind != 0:
                raise ValueError('non-padding directory slot after used count')
            continue
        if kind not in (4, 24, 25):
            raise ValueError('unsupported PDI1 entry type')
        name = _name(record[20:64])
        # A flat archive cannot safely export case aliases; preserve hierarchy
        # instead of silently choosing one resource when a future input differs.
        if name.casefold() in names:
            raise ValueError('duplicate or case-aliased PDI1 resource')
        names.add(name.casefold())
        row = {'index': index, 'name': name, 'type': kind, 'record_offset': offset,
               'record_hex': record.hex()}
        if kind == 4:
            row['unresolved_links_i16'] = list(struct.unpack_from('<5h', record, 2))
        else:
            relative, length = struct.unpack_from('<2I', record, 12)
            at = cdi + relative
            if length < 12 or at < cdi or at + length > len(data):
                raise ValueError('PDI1 resource range')
            expanded, zero, flags = struct.unpack_from('<IHH', data, at + 4)
            decoded_total += expanded
            if zero != 0 or flags not in (16, 17) or not 0 < expanded <= MAX_DECODED or decoded_total > MAX_DECODED:
                raise ValueError('PDI1 wrapper flags/expanded byte budget')
            row.update(span=[at, length], wrapper_offset=at + 4, decoded_bytes=expanded,
                       flags=flags, encoded_span=[at + 12, length - 12],
                       prefix_hex=data[at:at + 4].hex())
            ranges.append((at, at + length))
        entries.append(row)
    ordered = sorted(ranges)
    if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('overlapping PDI1 resource spans')
    return {'slots': slots, 'used': used, 'directory_offset': start,
            'cdi1_offset': cdi, 'unknown_header_u32': unknown,
            'declared_decoded_total': decoded_total, 'entries': entries}


def tea_decode(data: bytes, key: bytes = TEA_KEY) -> bytes:
    """32-cycle TEA, little-endian words, independent ECB blocks.

    Actual selected payloads retain a short final plaintext tail; never read
    bytes from the next member to manufacture another complete cipher block.
    """
    if len(key) != 16 or len(data) > MAX_FILE:
        raise ValueError('TEA key length/byte budget')
    words = struct.unpack('<4I', key)
    result = bytearray(data)
    for offset in range(0, len(data) - 7, 8):
        left, right = struct.unpack_from('<2I', data, offset)
        accumulator = 0xC6EF3720
        for _ in range(32):
            right = (right - (((left << 4) + words[2]) ^ (left + accumulator) ^ ((left >> 5) + words[3]))) & 0xffffffff
            left = (left - (((right << 4) + words[0]) ^ (right + accumulator) ^ ((right >> 5) + words[1]))) & 0xffffffff
            accumulator = (accumulator - 0x9E3779B9) & 0xffffffff
        struct.pack_into('<2I', result, offset, left, right)
    return bytes(result)


def lzss_decode(data: bytes, expected: int) -> bytes:
    """4096-byte zero window, initial cursor4078; LSB-first literal flags.

    Back-reference = low byte + high nibble, length = low nibble +3.
    Require exact output and exact encoded consumption; no zero-fill fallback.
    """
    if not 0 < expected <= MAX_DECODED or len(data) > MAX_FILE:
        raise ValueError('LZSS byte budget')
    ring = bytearray(4096); cursor = 4078; position = 0; result = bytearray()
    while len(result) < expected:
        if position >= len(data):
            raise ValueError('truncated LZSS flag')
        flags = data[position]; position += 1
        for bit in range(8):
            if len(result) == expected:
                break
            if flags & (1 << bit):
                if position >= len(data):
                    raise ValueError('truncated LZSS literal')
                chunk = [data[position]]; position += 1
            else:
                if position + 2 > len(data):
                    raise ValueError('truncated LZSS reference')
                low, high = data[position:position + 2]; position += 2
                at = low | ((high & 0xf0) << 4); count = (high & 15) + 3
                if len(result) + count > expected:
                    raise ValueError('LZSS reference overruns declared output')
                # Copy through the ring immediately so overlapping references
                # have conventional LZSS semantics.
                for step in range(count):
                    value = ring[(at + step) & 4095]
                    result.append(value); ring[cursor] = value; cursor = (cursor + 1) & 4095
                continue
            for value in chunk:
                result.append(value); ring[cursor] = value; cursor = (cursor + 1) & 4095
    if position != len(data):
        raise ValueError('unconsumed LZSS trailing bytes')
    return bytes(result)


def decode_member(data: bytes, record: dict) -> bytes:
    at, size = record['encoded_span']
    if at < 0 or size < 0 or at + size > len(data):
        raise ValueError('encoded member range')
    decoded = tea_decode(data[at:at + size])
    if record['flags'] == 17:
        decoded = lzss_decode(decoded, record['decoded_bytes'])
    elif record['flags'] != 16:
        raise ValueError('unsupported member encoding')
    if len(decoded) != record['decoded_bytes']:
        raise ValueError('decoded member size mismatch')
    return decoded


def indexed_tga(data: bytes) -> dict:
    """Selected original uncompressed8-bit indexed TGAs; no alpha inference."""
    if len(data) < 18 or len(data) > MAX_DECODED:
        raise ValueError('TGA header/byte budget')
    id_size, mapped, kind, first, palette_count, palette_bits, ox, oy, width, height, bits, descriptor = struct.unpack_from('<3B2HB4H2B', data)
    if mapped != 1 or kind != 1 or bits != 8 or palette_bits != 24 or first != 0 or not 0 < palette_count <= 256:
        raise ValueError('unsupported indexed TGA encoding')
    pixels = width * height
    if not 0 < width <= 4096 or not 0 < height <= 4096 or pixels > MAX_DECODED // 4:
        raise ValueError('TGA dimensions/budget')
    palette_offset = 18 + id_size; pixel_offset = palette_offset + palette_count * 3
    end = pixel_offset + pixels
    if end > len(data) or any(index >= palette_count for index in data[pixel_offset:end]):
        raise ValueError('TGA palette index/pixel range')
    footer = data[end:]
    if footer and (len(footer) != 26 or footer[8:] != b'TRUEVISION-XFILE.\0'):
        raise ValueError('unsupported TGA trailing metadata')
    return {'width': width, 'height': height, 'image_type': kind, 'sample_bits': bits,
            'palette_entries': palette_count, 'palette_bits': palette_bits,
            'palette_offset': palette_offset, 'palette_bytes': palette_count * 3,
            'palette_sha256': sha(data[palette_offset:pixel_offset]),
            'pixels_offset': pixel_offset, 'pixels_bytes': pixels,
            'pixels_sha256': sha(data[pixel_offset:end]), 'descriptor': descriptor,
            'declared_attribute_bits': descriptor & 15, 'origin': [ox, oy],
            'footer_bytes': len(footer), 'alpha_status': 'UNRESOLVED: descriptor attribute bits are not a decoded alpha channel',
            'channel_policy': 'Original8-bit indices and BGR24 palette preserved; no generated transparency'}


def _floats(data: bytes, at: int, count: int) -> list:
    values = list(struct.unpack_from('<' + str(count) + 'f', data, at))
    if not all(math.isfinite(value) for value in values):
        raise ValueError('non-finite XOBJ geometry')
    return values


def xobj_structure(data: bytes) -> dict:
    """Actual observed XOBJ108-byte triangle layout; retains unknown fields.

    Structural associations are validated, but no wheel/body hierarchy or
    game material flags/coordinate semantics are claimed.
    """
    if len(data) < 76 or len(data) > MAX_DECODED or data[:4] != b'XOBJ':
        raise ValueError('XOBJ signature/header/byte budget')
    sections = struct.unpack_from('<12I', data, 28)
    triangles, tri_at, tri_size, vertices, vertex_at, vertex_size, normals, normal_at, normal_size, textures, texture_at, texture_size = sections
    if not all(0 < count <= MAX_GEOMETRY for count in (triangles, vertices, normals)) or not 0 < textures <= 256:
        raise ValueError('XOBJ count budget')
    if (tri_size, vertex_size, normal_size) != (108 * triangles, 12 * vertices, 12 * normals):
        raise ValueError('XOBJ section stride mismatch')
    if tri_at != 76 or vertex_at != tri_at + tri_size or normal_at != vertex_at + vertex_size or texture_at != normal_at + normal_size or texture_at + texture_size != len(data):
        raise ValueError('XOBJ section range/contiguity')
    positions = [_floats(data, vertex_at + 12 * i, 3) for i in range(vertices)]
    normal_values = [_floats(data, normal_at + 12 * i, 3) for i in range(normals)]
    names = []; cursor = texture_at
    for _ in range(textures):
        end = data.find(b'\0', cursor, min(cursor + 128, len(data)))
        if end < 0:
            raise ValueError('XOBJ texture string unterminated')
        names.append(_name(data[cursor:end + 1])); cursor = end + 1
    tail = data[cursor:]
    if tail != b'\0' * textures:
        raise ValueError('unqualified XOBJ texture block trailer')
    faces = []; winding = Counter(); materials = Counter(); flags = Counter()
    for index in range(triangles):
        at = tri_at + index * 108
        indices = list(struct.unpack_from('<3I', data, at + 24))
        normal_indices = list(struct.unpack_from('<3I', data, at + 36))
        if any(i >= vertices for i in indices) or any(i >= normals for i in normal_indices):
            raise ValueError('invalid XOBJ vertex/normal index')
        face_normal = _floats(data, at + 4, 3); uv = _floats(data, at + 84, 6)
        candidate_texture, = struct.unpack_from('<I', data, at + 80)
        if candidate_texture > textures:
            raise ValueError('XOBJ candidate one-based texture index out of range')
        materials[candidate_texture] += 1
        raw_flags = list(struct.unpack_from('<5I', data, at + 48))
        flags[tuple(raw_flags)] += 1
        a, b, c = [positions[i] for i in indices]
        ab = [b[j] - a[j] for j in range(3)]; ac = [c[j] - a[j] for j in range(3)]
        cross = [ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0]]
        dot = sum(x*y for x, y in zip(cross, face_normal))
        winding['positive' if dot > 0 else 'negative' if dot < 0 else 'zero'] += 1
        faces.append({'source_offset': at, 'vertex_indices': indices, 'normal_indices': normal_indices,
                      'face_normal': face_normal, 'uv': [uv[:2], uv[2:4], uv[4:]],
                      'candidate_texture_index': candidate_texture,
                      'unknown_prefix_u32': struct.unpack_from('<I', data, at)[0],
                      'unknown_f32_at16': _floats(data, at + 16, 2),
                      'unknown_u32_at48': raw_flags,
                      'corner_color_u32_at68': list(struct.unpack_from('<3I', data, at + 68))})
    return {'schema': 'michelin-xobj-structural/1', 'status': 'WARN structural reconstruction',
            'header_hex': data[:76].hex(), 'sections_u32': list(sections),
            'counts': {'triangles': triangles, 'vertices': vertices, 'normals': normals, 'texture_names': textures},
            'positions': positions, 'normals': normal_values, 'triangles': faces,
            'texture_names': names, 'texture_table_trailer_hex': tail.hex(),
            'candidate_texture_index_histogram': dict(materials),
            'unknown_flags_histogram': [{'values': list(key), 'triangles': value} for key, value in sorted(flags.items())],
            'cross_dot_face_normal_signs': dict(winding),
            'source_bounds': [[min(p[i] for p in positions), max(p[i] for p in positions)] for i in range(3)],
            'unknown_semantics': ['coordinate axes, handedness and units', 'body/wheel/hub hierarchy and transforms',
                                  'flags, lighting, transparency, glass and animation',
                                  'candidate texture indexing:0 untextured /1..N not runtime-confirmed',
                                  'external vertex stream versus XOBJ positions and damage states',
                                  'PTOC LOD/variant selection and thresholds']}


def inspect_archive(data: bytes) -> tuple[dict, dict[str, bytes]]:
    report = directory(data); assets = {}; rows = report['entries']
    for row in rows:
        if row['type'] == 4:
            continue
        decoded = decode_member(data, row); name = row['name']
        row.update(decoded_sha256=sha(decoded), encoded_sha256=sha(data[row['encoded_span'][0]:sum(row['encoded_span'])]),
                   payload_status='PASS exact decoded size and full encoded consumption',
                   plaintext_tail_bytes=row['encoded_span'][1] % 8)
        assets['decoded/' + name] = decoded
        if name.upper().endswith('.TGA'):
            row['texture'] = indexed_tga(decoded)
        elif name.upper().endswith('.XO'):
            geometry = xobj_structure(decoded)
            row['geometry'] = {key: geometry[key] for key in ('status', 'counts', 'source_bounds', 'cross_dot_face_normal_signs', 'texture_names', 'unknown_semantics')}
            assets['structure/' + name + '.json'] = canonical(geometry)
        elif name.upper().endswith('_VERTEX.BIN'):
            if len(decoded) % 12 or not 0 < len(decoded) // 12 <= MAX_GEOMETRY:
                raise ValueError('external vertex stream stride')
            values = [_floats(decoded, at, 3) for at in range(0, len(decoded), 12)]
            row['external_vertex_stream'] = {'candidate_positions': len(values), 'stride': 12,
                                             'source_bounds': [[min(p[i] for p in values), max(p[i] for p in values)] for i in range(3)],
                                             'status': 'WARN positions structurally finite; damage/animation relationship unresolved'}
        elif name.upper() == 'INDEX.TOC':
            if decoded[:4] != b'PTOC':
                raise ValueError('PTOC signature')
            row['toc'] = {'magic': 'PTOC', 'header_u32_at4': struct.unpack_from('<I', decoded, 4)[0],
                          'literal_xo_names': [match.group().decode('ascii') for match in re.finditer(rb'car\d+[A-Z]_\d\.xo', decoded, re.I)],
                          'status': 'WARN decoded original preserved; record/LOD semantics not qualified'}
    return report, assets


def run(source_root: Path, output: Path, targets=TARGETS) -> dict:
    """Private exact payload exports + deterministic report; originals opened rb."""
    root = Path(source_root).absolute()
    target = output_directory(Path(output), (root,))
    if not 0 < len(targets) <= 8 or len({str(name).casefold() for name in targets}) != len(targets):
        raise ValueError('archive target count budget')
    report = {'schema': VERSION, 'source_root': str(root), 'archives': [],
              'boundary': 'Payload and structural proof only; no complete vehicle assembly, UVS adapter, original renderer parity or MR import.'}
    assets = {}; originals = {}; total = 0
    for name in targets:
        relative_name(name)
        if '/' in name or not name.upper().endswith('.PDO'):
            raise ValueError('only explicitly selected flat PDO names accepted')
        path = root / 'Data' / 'Objects' / name
        before = path.stat(); raw = read_bounded(path, MAX_FILE)
        tree, decoded = inspect_archive(raw)
        tree.update(path=str(path), bytes=len(raw), sha256=sha(raw), archive=name)
        originals[path] = (sha(raw), before.st_size, before.st_mtime_ns)
        total += sum(len(value) for value in decoded.values())
        if total > MAX_DECODED:
            raise ValueError('aggregate research output budget')
        for relative, value in decoded.items():
            assets[name + '/' + relative] = value
        report['archives'].append(tree)
    exe = root / 'RallyMasters.EXE'
    if exe.exists():
        before = exe.stat(); raw = read_bounded(exe, MAX_FILE)
        report['executable'] = {'path': str(exe), 'bytes': len(raw), 'sha256': sha(raw),
                                'key_literal_file_offsets': [m.start() for m in re.finditer(TEA_KEY, raw)],
                                'boundary': 'literal corroboration; no native loader trace or runtime execution'}
        originals[exe] = (sha(raw), before.st_size, before.st_mtime_ns)
    evidence = {}
    for relative in ('Server/Data/Cars.BIN', 'Server/Scripts/singlerace.scr'):
        path = root / relative
        if not path.exists():
            evidence[relative] = {'status': 'MISSING INPUT'}
            continue
        before = path.stat(); raw = read_bounded(path, MAX_FILE)
        row = {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}
        originals[path] = (sha(raw), before.st_size, before.st_mtime_ns)
        if relative.endswith('.BIN'):
            if len(raw) != 24 * 1608:
                raise ValueError('unqualified Michelin Cars.BIN record layout')
            records = []
            for index in range(24):
                at = index * 1608
                number = struct.unpack_from('<I', raw, at + 28)[0]
                if number in (6, 25):
                    label = raw[at + 32:at + 64].split(b'\0', 1)[0].decode('latin1')
                    records.append({'record_offset': at, 'id_offset': at + 28, 'label_offset': at + 32,
                                    'id': number, 'label': label})
            if sorted(record['id'] for record in records) != [6, 25]:
                raise ValueError('Michelin selected catalog records missing/ambiguous')
            row.update(status='WARN observed fixed-stride source catalog', selected_records=records)
        else:
            lines = raw.decode('ascii').splitlines(); pairs = []
            for line_number, line in enumerate(lines, 1):
                if re.match(r'^\s*cars\s', line):
                    values = line.split()[1:]
                    if len(values) % 2 or any(not re.fullmatch(r'\d{2}', values[i]) or not re.fullmatch('[A-Z]', values[i + 1]) for i in range(0, len(values), 2)):
                        raise ValueError('unsupported Michelin cars script grammar')
                    pairs.extend({'line': line_number, 'id': int(values[i]), 'variant': values[i + 1]}
                                 for i in range(0, len(values), 2) if int(values[i]) in (6, 25))
            row.update(status='PASS literal selected script pairs', selected_pairs=pairs)
        evidence[relative] = row
    report['catalog_evidence'] = evidence
    for path, expected in originals.items():
        now = path.stat()
        if (sha(read_bounded(path, MAX_FILE)), now.st_size, now.st_mtime_ns) != expected:
            raise ValueError('original source changed during inspection')
    report['original_files_unchanged'] = True
    report['implementation_sha256'] = sha(read_bounded(Path(__file__), MAX_FILE))
    assets['report.json'] = canonical(report)
    manifest = {'schema': VERSION + '-manifest', 'files': {name: {'bytes': len(value), 'sha256': sha(value)} for name, value in sorted(assets.items())},
                'total_bytes': sum(map(len, assets.values()))}
    assets['manifest.json'] = canonical(manifest)
    if sum(map(len, assets.values())) > MAX_DECODED:
        raise ValueError('aggregate serialized research output budget')
    target.mkdir(parents=True, exist_ok=False)
    for name, data in sorted(assets.items()):
        relative_name(name)
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    return {'status': 'WARN structural research', 'output': str(target), 'archives': len(report['archives']),
            'decoded_files': sum(row['type'] != 4 for archive in report['archives'] for row in archive['entries']),
            'manifest_sha256': sha(assets['manifest.json']), 'original_files_unchanged': True}
