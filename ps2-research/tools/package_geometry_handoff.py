"""Bounded GEOM1 handoff using the existing CRC/SHA archive writer."""
import argparse
import json
from pathlib import Path
import shutil
import package_reflection_handoff as p
import geometry_delta as g


def selected_files():
    files=list((g.ROOT/'geom1').glob('*.md'))+list((g.ROOT/'geom1').glob('*.json'))
    files+=list((g.ROOT/'tools').glob('*.py'))+list((g.ROOT/'tests').glob('test_*.py'))
    dependencies={'ui2':['elf-hud-functions.json','hud-runtime-map.json','hud-runtime-structures.json','minimap-format.json'],
        'water1':['render-contract.json','elf-functions.json','case-evidence.json'],
        'refl1':['render-contract.json','elf-functions.json','vehicle-evidence.json','resource-evidence.json'],
        'cdelta1':['course-pairs.json']}
    files+=[g.ROOT/folder/name for folder,names in dependencies.items() for name in names]
    if any(not f.is_file() for f in files):raise ValueError('Missing small historical fixture')
    return sorted(set(files),key=lambda f:f.relative_to(p.REPO).as_posix())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check-dir',type=Path);ap.add_argument('--archive',type=Path)
    args=ap.parse_args()
    if not(args.check_dir or args.archive):ap.error('Provide --check-dir or --archive')
    files=selected_files();readme=(g.ROOT/'geom1/HANDOFF.md').read_bytes()
    manifest=p.metadata(files=files,readme=readme,phase='PS2-GEOM1')
    for option in ('check_dir','archive'):
        if getattr(args,option) is not None:
            path=g.local_output(getattr(args,option))
            if path.exists():raise ValueError('Existing handoff output preserved')
            setattr(args,option,path)
    if args.check_dir:
        args.check_dir.mkdir(parents=True)
        for f in files:
            target=args.check_dir/f.relative_to(p.REPO)
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
        (args.check_dir/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        (args.check_dir/'HANDOFF.md').write_bytes(readme)
        print(args.check_dir)
    if args.archive:
        print(json.dumps(p.write_archive(args.archive,files,manifest,readme,g.ROOT/'data/geom1/ZIP_SHA256.json')))


if __name__=='__main__':main()
