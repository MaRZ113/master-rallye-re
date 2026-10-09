"""RIGID1 compact handoff with historical test dependencies, CRC and SHA checks."""
import argparse
import json
from pathlib import Path
import shutil

import rigid_runtime as r
import package_bird_handoff as previous
import package_reflection_handoff as archive


def selected_files():
    # Preserve compact AMBIENT2 oracles used by its tests; current phase reports
    # replace its narrative. The prior dependency closure includes UI2 fixtures.
    files=[p for p in previous.selected_files()
           if p.parent.name!='ambient2' or p.suffix=='.json']
    files+=list((r.ROOT/'rigid1').glob('*.md'))
    files+=list((r.ROOT/'rigid1').glob('*.json'))
    files+=list((r.ROOT/'rigid1/validation-logs').glob('*.log'))
    if any(not p.is_file() or p.suffix not in {'.py','.md','.json','.log'} for p in files):
        raise ValueError('Missing or unexpected compact handoff dependency')
    return sorted(set(files),key=lambda p:p.relative_to(archive.REPO).as_posix())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-dir',type=Path)
    parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if not(args.check_dir or args.archive):parser.error('Provide --check-dir or --archive')
    files=selected_files();readme=(r.ROOT/'rigid1/HANDOFF.md').read_bytes()
    manifest=archive.metadata(files=files,readme=readme,phase='PS2-RIGID1')
    for field in ('check_dir','archive'):
        value=getattr(args,field)
        if value is not None:setattr(args,field,r.local_output(value))
    if args.check_dir:
        args.check_dir.mkdir(parents=True)
        for path in files:
            dest=args.check_dir/path.relative_to(archive.REPO)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        (args.check_dir/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
        (args.check_dir/'HANDOFF.md').write_bytes(readme)
        print(args.check_dir)
    if args.archive:
        receipt=args.archive.with_suffix('.receipt.json');r.local_output(receipt)
        print(json.dumps(archive.write_archive(args.archive,files,manifest,readme,receipt)))


if __name__=='__main__':main()
