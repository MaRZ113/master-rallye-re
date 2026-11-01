"""Prepare a private, non-installable loose-resource draft from an SDK bundle.

No runtime binary or loader is supplied. Source files are read only. All
candidate resources remain private and must be reviewed before installation.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

from master_rallye.vehicle_packaging import _open_sma_archive, normalize_sma_member_name

ROOTS = {'datagame', 'datagx', 'datascene', 'dataaudio', 'datavideo'}
MUTABLE = {'datagame/options.xml', 'datagame/playerstate.xml', 'datagame/playerstate.xml#'}
MAX_FILE = 64 * 1024 * 1024
MAX_OUTPUT = 512 * 1024 * 1024
MAX_ARCHIVE = 2 * 1024 * 1024 * 1024
MAX_FILES = 20000


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name:
        raise ValueError('unsafe resource path')
    parts = name.split('/')
    if (len(parts) < 2 or parts[0].casefold() not in ROOTS or
            any(not part or part in ('.', '..') or any(c in part for c in ':<>"|?*') or
                part.endswith((' ', '.')) or part.split('.')[0].casefold() in
                {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)), *(f'lpt{i}' for i in range(1, 10))}
                for part in parts)):
        raise ValueError('unsafe resource path: ' + name)
    if PurePosixPath(name).suffix.casefold() in ('.exe', '.dll', '.cmd', '.bat', '.ps1'):
        raise ValueError('executable resource forbidden: ' + name)
    return '/'.join(parts)


def unlinked(path):
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        if item.is_symlink() or getattr(item, 'is_junction', lambda: False)():
            raise ValueError('link-backed path rejected: ' + str(item))
    return path


def bounded_read(path, limit=MAX_FILE):
    path = unlinked(path)
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError('missing or oversized file: ' + str(path))
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('file exceeds budget: ' + str(path))
    return data


def archive_index(archive):
    infos = archive.infolist()
    if len(infos) > MAX_FILES or sum(info.file_size for info in infos) > MAX_ARCHIVE:
        raise ValueError('archive entry budget exceeded')
    result = {}
    for info in infos:
        name, directory = normalize_sma_member_name(info.filename)
        if directory:
            continue
        name = safe_path(name)
        key = name.casefold()
        if key in result:
            raise ValueError('ambiguous archive member: ' + name)
        if info.file_size > MAX_FILE or info.flag_bits & 1:
            raise ValueError('unsupported or oversized archive member: ' + name)
        result[key] = (name, info)
    return result


def archive_read(archive, info):
    with archive.open(info) as stream:
        data = stream.read(MAX_FILE + 1)
    if len(data) != info.file_size or len(data) > MAX_FILE:
        raise ValueError('archive member size mismatch')
    return data


def prepare(bundle, retail_sma, retail_root, output, *, allowed_output_root):
    bundle, retail_sma, retail_root = map(unlinked, (bundle, retail_sma, retail_root))
    output, allowed = unlinked(output), unlinked(allowed_output_root)
    if output == allowed or not output.is_relative_to(allowed) or output.exists():
        raise ValueError('choose a fresh output below the private build root')
    if any(output.is_relative_to(p) or p.is_relative_to(output) for p in (bundle, retail_sma, retail_root)):
        raise ValueError('output overlaps an input')
    resource_root = unlinked(bundle / 'resource-root')
    profile = json.loads(bounded_read(bundle / 'runtime-profile.json', 1024 * 1024))
    index_raw = bounded_read(bundle / 'resource-index.tsv', 4 * 1024 * 1024)
    if sha_bytes(index_raw) != profile.get('resource_index_sha256'):
        raise ValueError('resource index does not match runtime profile')
    entries = {}
    for line in index_raw.decode('utf-8').splitlines():
        fields = line.split('\t')
        if len(fields) != 3:
            raise ValueError('invalid indexed resource row')
        digest, size, name = fields
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('invalid resource hash')
        size = int(size)
        if size < 0 or size > (512 * 1024 * 1024 if name == 'Data.sma' else MAX_FILE):
            raise ValueError('indexed resource size budget exceeded')
        if name != 'Data.sma':
            safe_path(name)
        key = name.casefold()
        if key in entries:
            raise ValueError('duplicate indexed resource: ' + name)
        entries[key] = (name, digest, size)
    if len(entries) > MAX_FILES or 'data.sma' not in entries:
        raise ValueError('invalid resource index')
    # Verify all indexed sources, including ones later omitted as unchanged.
    for name, digest, size in entries.values():
        path = unlinked(resource_root.joinpath(*PurePosixPath(name).parts))
        if name.casefold() == 'datagame/options.xml':
            options = bounded_read(path, 64 * 1024)
            if not options:
                raise ValueError('editable options must not be empty')
            continue
        h = hashlib.sha256()
        if not path.is_file() or path.stat().st_size != size:
            raise ValueError('indexed resource missing or changed: ' + name)
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        if h.hexdigest() != digest:
            raise ValueError('indexed resource hash mismatch: ' + name)
    draft = {}
    total = 0
    def add(name, data, origin):
        nonlocal total
        name = safe_path(name)
        if name.casefold() in MUTABLE:
            return
        total += len(data)
        if total > MAX_OUTPUT:
            raise ValueError('draft output budget exceeded')
        draft[name.casefold()] = (name, data, origin)
    with _open_sma_archive(retail_sma) as baseline, _open_sma_archive(resource_root / 'Data.sma') as candidate:
        original, altered = archive_index(baseline), archive_index(candidate)
        missing = original.keys() - altered.keys()
        if missing:
            raise ValueError('archive member deletion cannot be represented by loose files')
        for key in sorted(altered):
            name, info = altered[key]
            data = archive_read(candidate, info)
            if key not in original or data != archive_read(baseline, original[key][1]):
                add(name, data, 'changed candidate archive member')
        for key in sorted(entries):
            name, _, _ = entries[key]
            if key == 'data.sma' or key in MUTABLE:
                continue
            data = bounded_read(resource_root.joinpath(*PurePosixPath(name).parts))
            # A loose candidate takes precedence over an archive member.
            source = unlinked(retail_root.joinpath(*PurePosixPath(name).parts))
            if source.is_file():
                original_data = bounded_read(source)
            elif key in original:
                original_data = archive_read(baseline, original[key][1])
            else:
                original_data = None
            if data != original_data:
                add(name, data, 'indexed candidate loose resource')
            else:
                draft.pop(key, None)
    rows = []
    for name, data, origin in sorted(draft.values(), key=lambda x: x[0].casefold()):
        installed = unlinked(retail_root.joinpath(*PurePosixPath(name).parts))
        existing = sha_bytes(bounded_read(installed)) if installed.is_file() else None
        rows.append({'path': name, 'size': len(data), 'sha256': sha_bytes(data), 'origin': origin,
                     'existing_loose_sha256': existing,
                     'review': 'existing loose file conflict' if existing and existing != sha_bytes(data)
                               else 'shared configuration' if name.casefold() in ('datagame/dev.xml', 'datagame/video.xml')
                               else 'unverified native resource'})
    report = {'schema': 'workshop-loose-package-draft/1', 'status': 'BLOCKED_NO_DLL_BOOTSTRAP',
              'installable': False, 'runtime_qualified': False, 'resources': rows,
              'source_index_sha256': sha_bytes(index_raw),
              'excluded_mutable': sorted(MUTABLE),
              'warning': 'Private resource draft only. No DLL, registry activation, version adapter or game validation.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.loose-draft-', dir=output.parent))
    try:
        for name, data, _ in draft.values():
            target = stage.joinpath('resources', *PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (stage / 'manifest.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        os.replace(stage, output)
    except Exception:
        shutil.rmtree(stage)
        raise
    return report
