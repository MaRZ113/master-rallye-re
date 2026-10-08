"""DRESSING1 handoff: reuse CRC/SHA writer, with complete small test fixtures."""
import argparse
import json
from pathlib import Path
import shutil
import package_geometry_handoff as previous
import package_reflection_handoff as archive
import dressing_runtime as d


def selected_files():
    files=previous.selected_files()
    # GEOM1 docs are context; only its small regression anchors are mandatory.
    files=[p for p in files if p.parent.name!='geom1']
    files+=list((d.ROOT/'dressing1').glob('*.md'))+list((d.ROOT/'dressing1').glob('*.json'))
    files+=[d.ROOT/'geom1'/name for name in ('nonwater-anchors.json','reproducibility.json')]
    if any(not p.is_file() for p in files):raise ValueError('Missing small historical regression fixture')
    return sorted(set(files),key=lambda p:p.relative_to(archive.REPO).as_posix())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check-dir',type=Path);ap.add_argument('--archive',type=Path)
    args=ap.parse_args()
    if not(args.check_dir or args.archive):ap.error('Provide --check-dir or --archive')
    files=selected_files();readme=(d.ROOT/'dressing1/HANDOFF.md').read_bytes()
    manifest=archive.metadata(files=files,readme=readme,phase='PS2-DRESSING1')
    for option in ('check_dir','archive'):
        value=getattr(args,option)
        if value is not None:
            path=d.local_output(value)
            if path.exists():raise ValueError('Existing handoff output preserved')
            setattr(args,option,path)
    if args.check_dir:
        args.check_dir.mkdir(parents=True)
        for file in files:
            dest=args.check_dir/file.relative_to(archive.REPO)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
        (args.check_dir/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
        (args.check_dir/'HANDOFF.md').write_bytes(readme)
        print(args.check_dir)
    if args.archive:
        print(json.dumps(archive.write_archive(args.archive,files,manifest,readme,d.ROOT/'data/dressing1/ZIP_SHA256.json')))


if __name__=='__main__':main()
