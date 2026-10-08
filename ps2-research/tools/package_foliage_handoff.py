"""TREEBLEND1 handoff with existing CRC/SHA writer and small test dependencies."""
import argparse
import json
from pathlib import Path
import shutil

import foliage_runtime as f
import package_dressing_handoff as previous
import package_reflection_handoff as archive


def selected_files():
    # Keep historical compact fixtures, not a repository-wide documentation pack.
    files = [path for path in previous.selected_files()
             if path.parent.name != 'dressing1' or path.suffix == '.json']
    files += list((f.ROOT/'treeblend1').glob('*.md'))
    files += list((f.ROOT/'treeblend1').glob('*.json'))
    files += list((f.ROOT/'treeblend1/validation-logs').glob('*.log'))
    if any(not path.is_file() for path in files):
        raise ValueError('Missing compact historical regression dependency')
    if any(path.suffix not in {'.py', '.md', '.json', '.log'} for path in files):
        raise ValueError('Unexpected handoff payload type')
    return sorted(set(files), key=lambda path: path.relative_to(archive.REPO).as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-dir', type=Path)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    if not (args.check_dir or args.archive):
        parser.error('Provide --check-dir or --archive')
    files = selected_files()
    readme = (f.ROOT/'treeblend1/HANDOFF.md').read_bytes()
    manifest = archive.metadata(files=files, readme=readme, phase='PS2-TREEBLEND1')
    for option in ('check_dir', 'archive'):
        value = getattr(args, option)
        if value is not None:
            setattr(args, option, f.local_output(value))
    if args.check_dir:
        args.check_dir.mkdir(parents=True)
        for path in files:
            target = args.check_dir/path.relative_to(archive.REPO)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        (args.check_dir/'MANIFEST.json').write_text(json.dumps(manifest, indent=2)+'\n',
                                                   encoding='utf-8', newline='\n')
        (args.check_dir/'HANDOFF.md').write_bytes(readme)
        print(args.check_dir)
    if args.archive:
        receipt = args.archive.with_suffix('.receipt.json')
        f.local_output(receipt)
        print(json.dumps(archive.write_archive(args.archive, files, manifest, readme, receipt)))


if __name__ == '__main__':
    main()
