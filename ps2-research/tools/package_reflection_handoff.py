"""Create the bounded REFL1 research handoff; no assets or repository repack."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRATCH = ROOT/'data'/'refl1'


def selected_files():
    files = list((ROOT/'refl1').glob('*.md'))+list((ROOT/'refl1').glob('*.json'))
    files += list((ROOT/'tools').glob('*.py'))+list((ROOT/'tests').glob('test_*.py'))
    files += [ROOT/'ui2'/name for name in ('elf-hud-functions.json', 'hud-runtime-map.json',
              'hud-runtime-structures.json', 'minimap-format.json')]
    files += [ROOT/'water1'/name for name in ('render-contract.json', 'elf-functions.json')]
    if any(not path.is_file() for path in files):
        raise ValueError('Missing small handoff dependency')
    return sorted(set(files), key=lambda path: path.relative_to(REPO).as_posix())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def metadata(files=None, readme=None, phase='PS2-REFL1'):
    head = subprocess.check_output(['git', '-c', 'safe.directory='+REPO.as_posix(),
                                    'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    rows = [{'path': path.relative_to(REPO).as_posix(), 'size': path.stat().st_size,
             'sha256': digest(path.read_bytes())} for path in (selected_files() if files is None else files)]
    if readme is None:
        readme = (ROOT/'refl1'/'HANDOFF.md').read_bytes()
    rows.append({'path': 'HANDOFF.md', 'size': len(readme), 'sha256': digest(readme)})
    return {'schema': 1, 'phase': phase, 'source_commit': head,
            'manifest_self_hash': 'Covered by external ZIP receipt, no recursive self-entry',
            'external_inputs': {'PS2': 'D:/Game/Master Rallye PS2',
                'PC': 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked',
                'CourseSDK': 'D:/Game/Master Rallye/master-rallye-re-course',
                'HUD': 'External ignored original HUD PSB/GXI',
                'UI2_XML': 'Optional ignored original ITALYS1.XML'}, 'files': rows}


def destination(path):
    result = path.resolve()
    if not result.is_relative_to(SCRATCH.resolve()) or result.exists():
        raise ValueError('New output must stay in ignored data/refl1/')
    return result


def write_archive(target, files, manifest, readme, receipt):
    """Shared archive/CRC/SHA writer; callers enforce their phase output root."""
    if receipt.exists():
        raise ValueError('Existing receipt preserved; select a new output directory')
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(REPO).as_posix())
        bundle.writestr('MANIFEST.json', json.dumps(manifest, indent=2)+'\n')
        bundle.writestr('HANDOFF.md', readme)
    with zipfile.ZipFile(target) as bundle:
        if bundle.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        for row in manifest['files']:
            data = bundle.read(row['path'])
            if digest(data) != row['sha256'] or len(data) != row['size']:
                raise ValueError('Bundle SHA/size mismatch: '+row['path'])
    result = {'archive': str(target), 'size': target.stat().st_size,
              'sha256': digest(target.read_bytes()), 'source_commit': manifest['source_commit'],
              'payloads': len(manifest['files']), 'integrity': 'PASS', 'proprietary_assets': 'EXCLUDED'}
    with receipt.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-dir', type=Path)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    if not (args.check_dir or args.archive):
        parser.error('Provide --check-dir or --archive')
    manifest = metadata()
    text = json.dumps(manifest, indent=2)+'\n'
    readme = (ROOT/'refl1'/'HANDOFF.md').read_bytes()
    if args.check_dir:
        target = destination(args.check_dir)
        target.mkdir(parents=True, exist_ok=False)
        for path in selected_files():
            output = target/path.relative_to(REPO)
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, output)
        (target/'MANIFEST.json').write_text(text, encoding='utf-8', newline='\n')
        (target/'HANDOFF.md').write_bytes(readme)
        print(target)
    if args.archive:
        target = destination(args.archive)
        result = write_archive(target, selected_files(), manifest, readme, SCRATCH/'ZIP_SHA256.json')
        print(json.dumps(result))


if __name__ == '__main__':
    main()
