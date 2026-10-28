#!/usr/bin/env python3
"""Bounded read-only Sega Rally Revo SBF/SBZ1 archive and DDS smoke.

Independent wire-layout probe informed by the documented Game Extractor
Plugin_SBF_SBZ1 archive layout (commit 1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a).
No third-party implementation is incorporated. No mesh reconstruction/import.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import struct
import zlib

MAX_STORED = 64 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_ENTRIES = 20_000
MAX_DIMENSION = 8192
MAX_PIXELS = 16_777_216


class ProbeError(ValueError):
    """Unrecognized, malformed or out-of-budget input."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def span(data: bytes, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise ProbeError(f"range outside archive: {offset}+{size}/{len(data)}")
    return data[offset:offset + size]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack('<I', span(data, offset, 4))[0]


def expand(data: bytes) -> tuple[bytes, dict]:
    if len(data) > MAX_STORED:
        raise ProbeError('stored input exceeds budget')
    if data[:4] != b'SBZ1':
        if data[:4] != b'\x04\0\0\0':
            raise ProbeError('unsupported SBF header (expected LE4 or SBZ1)')
        return data, {'kind': 'SBF_LE4', 'compression': 'none'}
    advertised = u32(data, 4)
    if advertised < 24 or advertised > MAX_EXPANDED:
        raise ProbeError('advertised expansion outside budget')
    decoder = zlib.decompressobj()
    try:
        output = decoder.decompress(data[8:], advertised + 1)
    except zlib.error as error:
        raise ProbeError(f'invalid zlib stream: {error}') from error
    if len(output) > advertised or decoder.unconsumed_tail:
        raise ProbeError('actual expansion exceeds advertised size')
    if not decoder.eof or decoder.unused_data:
        raise ProbeError('truncated zlib stream or trailing bytes')
    if len(output) != advertised:
        raise ProbeError('expanded size differs from advertised size')
    return output, {'kind': 'SBZ1', 'compression': 'zlib', 'advertised_size': advertised}


def dds_metadata(data: bytes) -> dict:
    if len(data) < 128 or data[:4] != b'DDS ' or u32(data, 4) != 124 or u32(data, 76) != 32:
        raise ProbeError('invalid or truncated DDS header')
    height, width = u32(data, 12), u32(data, 16)
    if not 0 < width <= MAX_DIMENSION or not 0 < height <= MAX_DIMENSION or width * height > MAX_PIXELS:
        raise ProbeError('DDS dimensions exceed budget')
    if u32(data, 28) > 32:
        raise ProbeError('DDS mipmap count exceeds budget')
    return {'width': width, 'height': height, 'mipmaps': u32(data, 28),
            'fourcc_hex': data[84:88].hex(), 'size': len(data), 'sha256': digest(data)}


def inspect(data: bytes) -> tuple[dict, list[tuple[int, bytes]]]:
    expanded, compression = expand(data)
    if expanded[:4] != b'\x04\0\0\0' or span(expanded, 4, 16) != bytes(16):
        raise ProbeError('unsupported expanded archive header')
    count = u32(expanded, 20)
    if not 0 < count <= MAX_ENTRIES:
        raise ProbeError('directory count outside budget')
    table_end = 24 + count * 8
    span(expanded, 24, count * 8)
    directory = []
    for index in range(count):
        key, offset = struct.unpack('<II', span(expanded, 24 + index * 8, 8))
        if offset < table_end or offset > len(expanded) - 32:
            raise ProbeError('member offset overlaps directory or exceeds archive')
        directory.append((offset, index, key))
    directory.sort()
    if len({entry[0] for entry in directory}) != count:
        raise ProbeError('duplicate/overlapping member offsets')
    members, textures = [], []
    for order, (offset, index, key) in enumerate(directory):
        end = directory[order + 1][0] if order + 1 < count else len(expanded)
        member = span(expanded, offset, end - offset)
        if len(member) < 32:
            raise ProbeError('member header overlaps following member')
        kind = u32(member, 0)
        payload_skip = 68 if kind == 4 else 32
        payload = span(member, payload_skip, len(member) - payload_skip)
        item = {'directory_index': index, 'directory_key_hex': f'{key:08x}',
                'offset_space': 'expanded_archive', 'offset': offset, 'end': end,
                'size': len(member), 'member_sha256': digest(member), 'type': kind,
                'header_words': list(struct.unpack('<8I', member[:32])),
                'payload_offset': offset + payload_skip, 'payload_size': len(payload),
                'payload_sha256': digest(payload), 'status': 'PASS'}
        if kind == 4:
            item['dds'] = dds_metadata(payload)
            item['meaning'] = 'DDS texture payload; native material association NOT TESTED'
            textures.append((index, payload))
        elif kind == 1:
            item['meaning'] = 'mesh candidate; mesh/UV/hierarchy reconstruction NOT TESTED'
        else:
            item['meaning'] = 'unknown member semantics retained'
            item['status'] = 'WARN'
        members.append(item)
    result = {'schema': 'rally-workshop-revo-probe/1', 'stored_size': len(data),
              'stored_sha256': digest(data), 'expanded_size': len(expanded),
              'expanded_sha256': digest(expanded), 'container': compression,
              'directory_count': count, 'directory_end': table_end,
              'type_counts': dict(Counter(str(member['type']) for member in members)),
              'members': members, 'L0': 'PASS', 'L1': 'NOT TESTED',
              'L2': 'NOT TESTED', 'Gameplay': 'NOT TESTED',
              'qualification': 'single archive structure and DDS headers only'}
    if any(member['status'] != 'PASS' for member in members):
        result['L0'] = 'WARN'
    return result, textures


def unlinked(path: Path) -> None:
    for entry in (path.absolute(), *path.absolute().parents):
        if entry.is_symlink() or (entry.exists() and getattr(entry.stat(), 'st_file_attributes', 0) & 0x400):
            raise ProbeError(f'linked/reparse path rejected: {entry}')


def read_source(path: Path) -> bytes:
    unlinked(path)
    before = path.stat()
    if not path.is_file() or before.st_size > MAX_STORED:
        raise ProbeError('input is not a bounded regular file')
    with path.open('rb') as handle:
        data = handle.read(MAX_STORED + 1)
    after = path.stat()
    if len(data) != before.st_size or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ProbeError('input changed during inspection')
    return data


def protected_roots(config: Path, extra_roots: list[Path]) -> tuple[list[Path], str]:
    unlinked(config)
    if config.stat().st_size > 1024 * 1024:
        raise ProbeError('source-root config exceeds budget')
    raw = read_source(config)
    if len(raw) > 1024 * 1024:
        raise ProbeError('source-root config exceeds budget')
    cfg = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(cfg, dict) or cfg.get('schema') != 'source-garage-roots/1' or not isinstance(cfg.get('base'), str) or not cfg['base']:
        raise ProbeError('unsupported source-root config')
    games = cfg.get('games')
    if not isinstance(games, list) or not 0 < len(games) <= 64:
        raise ProbeError('invalid source-root game list')
    ids = set()
    base = Path(cfg['base'])
    roots = [base, *extra_roots]
    for game in games:
        if not isinstance(game, dict) or not isinstance(game.get('id'), str) or not game['id'] or game['id'] in ids:
            raise ProbeError('invalid or duplicate game ID')
        if not isinstance(game.get('path'), str) or not game['path']:
            raise ProbeError('invalid configured game path')
        ids.add(game['id'])
        path = Path(game['path'])
        roots.append(path if path.is_absolute() else base / path)
    for root in roots:
        unlinked(root)
    return [root.resolve() for root in roots], digest(raw)


def guard_output(output: Path, roots: list[Path]) -> None:
    unlinked(output)
    output = output.resolve()
    if any(output == root or output.is_relative_to(root) or root.is_relative_to(output) for root in roots):
        raise ProbeError('output must be separate from every configured/protected root')


def decode_one_dds(textures: list[tuple[int, bytes]], output: Path) -> dict:
    if not textures:
        return {'status': 'MISSING INPUT', 'reason': 'selected archive contains no DDS member'}
    try:
        from PIL import Image, __version__
    except ImportError:
        return {'status': 'NOT TESTED', 'reason': 'Pillow unavailable'}
    index, data = textures[0]
    metadata = dds_metadata(data)
    target = output / f'member-{index:04d}-texture.png'
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format != 'DDS' or source.size != (metadata['width'], metadata['height']):
                raise ProbeError('DDS decoder metadata mismatch')
            source.load()
            image = source.convert('RGBA')
        with target.open('xb') as handle:
            image.save(handle, format='PNG')
    except (OSError, ValueError) as error:
        return {'status': 'FAIL', 'reason': str(error), 'member_index': index, 'pillow': __version__}
    return {'status': 'PASS', 'member_index': index, 'pillow': __version__,
            'path': str(target), 'png_sha256': digest(target.read_bytes()),
            'meaning': 'individual diffuse/role UNKNOWN; not vehicle rendering parity', **metadata}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--protected-root', type=Path, action='append', default=[],
                        help='Additional immutable root, for example external tools; repeatable')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        for path in (args.source_root, args.input, args.output):
            unlinked(path)
        root, source, output = args.source_root.resolve(), args.input.resolve(), args.output.resolve()
        source.relative_to(root)
        roots, config_sha256 = protected_roots(args.config, args.protected_root)
        guard_output(output, [root, *roots])
        if (output / 'report.json').exists():
            raise ProbeError('report already exists; choose a new output directory')
        data = read_source(source)
        result, textures = inspect(data)
        output.mkdir(parents=True, exist_ok=True)
        result['source'] = {'root': str(root), 'relative_path': source.relative_to(root).as_posix(),
                            'sha256': digest(data), 'size': len(data)}
        result['decoder_source_sha256'] = digest(Path(__file__).read_bytes())
        result['root_config_sha256'] = config_sha256
        result['protected_roots'] = [str(path) for path in roots]
        result['texture_preview'] = decode_one_dds(textures, output)
        result['original_bytes_unchanged'] = digest(read_source(source)) == digest(data)
        if not result['original_bytes_unchanged']:
            raise ProbeError('source changed during probe')
        with (output / 'report.json').open('x', encoding='utf-8') as handle:
            json.dump(result, handle, indent=2)
            handle.write('\n')
        print(json.dumps({key: result[key] for key in ('L0', 'L1', 'directory_count', 'type_counts', 'texture_preview')}))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
