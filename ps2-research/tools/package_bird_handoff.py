"""AMBIENT2 bounded handoff; reuse verified historical fixtures and CRC/SHA writer."""
import argparse
import json
from pathlib import Path
import shutil

import bird_runtime as b
import package_foliage_handoff as previous
import package_reflection_handoff as archive


def selected_files():
    # Retain TREEBLEND1 compact oracles needed by its tests, not all old reports.
    files=[p for p in previous.selected_files()
           if p.parent.name!='treeblend1' or p.suffix=='.json']
    files+=list((b.ROOT/'ambient2').glob('*.md'))
    files+=list((b.ROOT/'ambient2').glob('*.json'))
    files+=list((b.ROOT/'ambient2/validation-logs').glob('*.log'))
    if any(not p.is_file() or p.suffix not in {'.py','.md','.json','.log'} for p in files):
        raise ValueError('Missing or unexpected compact handoff dependency')
    return sorted(set(files),key=lambda p:p.relative_to(archive.REPO).as_posix())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-dir',type=Path);parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if not(args.check_dir or args.archive):parser.error('Provide --check-dir or --archive')
    files=selected_files();readme=(b.ROOT/'ambient2/HANDOFF.md').read_bytes()
    manifest=archive.metadata(files=files,readme=readme,phase='PS2-AMBIENT2')
    for field in ('check_dir','archive'):
        value=getattr(args,field)
        if value is not None:setattr(args,field,b.local_output(value))
    if args.check_dir:
        args.check_dir.mkdir(parents=True)
        for path in files:
            dest=args.check_dir/path.relative_to(archive.REPO)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        (args.check_dir/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
        (args.check_dir/'HANDOFF.md').write_bytes(readme)
        print(args.check_dir)
    if args.archive:
        receipt=args.archive.with_suffix('.receipt.json');b.local_output(receipt)
        print(json.dumps(archive.write_archive(args.archive,files,manifest,readme,receipt)))


if __name__=='__main__':main()
