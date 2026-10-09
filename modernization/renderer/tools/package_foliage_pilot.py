"""Source/test-only PC-VISUAL-PILOT1 handoff, no binaries or game payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory='+REPO.as_posix(), *args], cwd=REPO, text=True).strip()


def package(output):
    output = output.resolve()
    if not output.is_relative_to(ROOT/'.analysis') or output.suffix != '.zip':
        raise ValueError('Handoff must be an ignored renderer/.analysis/*.zip')
    paths = set(git('ls-files', '--cached', '--others', '--exclude-standard', '--', 'modernization/renderer').splitlines())
    paths.update(git('ls-files', '--', 'ps2-research/tools').splitlines())
    # Existing renderer tests import the unchanged general-checkout library.
    # Its package initializer loads several modules; retain the complete small
    # Python package rather than replacing that initializer in the handoff.
    paths.update(git('ls-files', '--', 'src/master_rallye/*.py').splitlines())
    paths.update({'ps2-research/water1/case-evidence.json',
        'modernization/renderer-recon/data/d3d8-callmap.json',
        'modernization/renderer-recon/data/vertex-formats.json',
        'modernization/renderer-recon/data/material-state-map.json'})
    allowed = {'.py', '.hpp', '.h', '.cpp', '.md', '.json', '.txt', '.tsv', '.def', '.ini', '.example'}
    payload = {}
    for relative in sorted(paths):
        if not relative:
            continue
        path = REPO/relative
        if not path.is_file() or '.analysis' in path.parts or '.build-msvc' in path.parts:
            raise ValueError('Invalid handoff source: '+relative)
        if path.suffix.lower() not in allowed and path.name not in ('.gitignore', '.gitattributes', 'CMakeLists.txt', 'COPYING', 'LICENSE'):
            raise ValueError('Unexpected file type: '+relative)
        if path.stat().st_size > 2*1024*1024:
            raise ValueError('Unbounded file: '+relative)
        payload[relative] = path.read_bytes()
    payload['HANDOFF.md'] = (ROOT/'research/pc-visual-pilot1/HANDOFF.md').read_bytes()
    manifest = {'schema': 'pc-visual-pilot1-handoff-v1', 'source_commit': git('rev-parse', 'HEAD'),
        'status': 'BLOCKED_ON_DRAW_IDENTITY', 'contains_binaries': False, 'contains_game_assets': False,
        'files': [{'path': p, 'size': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for p, b in sorted(payload.items())]}
    payload['MANIFEST.json'] = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    payload['SHA256SUMS.txt'] = ''.join(hashlib.sha256(b).hexdigest()+'  '+p+'\n' for p, b in sorted(payload.items())).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(zipfile.ZipInfo('modernization/renderer/.analysis/', (2026, 10, 9, 0, 0, 0)), b'')
        for p, b in sorted(payload.items()):
            info = zipfile.ZipInfo(p, (2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, b)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        for row in manifest['files']:
            if hashlib.sha256(archive.read(row['path'])).hexdigest() != row['sha256']:
                raise ValueError('ZIP SHA mismatch')
    receipt = {'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'size': output.stat().st_size, 'payload_files': len(manifest['files']), 'source_commit': manifest['source_commit'],
        'crc': 'PASS', 'payload_sha256': 'PASS'}
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n', newline='\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'.analysis/PC-VISUAL-PILOT1-handoff.zip')
    print(json.dumps(package(parser.parse_args().output), indent=2))


if __name__ == '__main__':
    main()
