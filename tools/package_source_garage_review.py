"""Package committed text sources only; never traverse external game roots."""
from __future__ import annotations
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE_EXTENSIONS={'.py','.md','.json','.txt','.java','.ps1','.cpp','.c','.html','.cmd','.sha256','.svg','.toml','.tsv','.in','.gitignore'}


def git(*args):
    return subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}',*args],cwd=ROOT)


def package(baseline: str, revision: str, output: Path):
    allowed_roots=[(ROOT/'.research-output/vehicles'/name).resolve()for name in ('source-garage','source-garage-evo2','cross-game-4runner','4runner-polish','4runner-stable','paris-dakar-source','paris-dakar-silver-native','dakar2-source')]
    if not any(output.resolve()==allowed or allowed in output.resolve().parents for allowed in allowed_roots):
        raise ValueError('output must stay in ignored repository source-garage evidence')
    revision=git('rev-parse','--verify',revision+'^{commit}').decode().strip()
    baseline=git('rev-parse','--verify',baseline+'^{commit}').decode().strip()
    if output.exists(): raise ValueError('choose a new output directory')
    changed=set(git('diff','--name-only','--diff-filter=ACMR',baseline,revision).decode().splitlines())
    data=git('archive','--format=zip',revision)
    files={}; excluded=[]
    with zipfile.ZipFile(io.BytesIO(data)) as source:
        for info in source.infolist():
            if info.is_dir(): continue
            p=PurePosixPath(info.filename)
            if p.is_absolute() or '..' in p.parts: raise ValueError('unsafe archive path')
            if p.suffix.lower() not in SOURCE_EXTENSIONS and p.name not in ('.gitignore','.gitattributes'):
                excluded.append(info.filename); continue
            # symlinks are never copied as apparent source text.
            if (info.external_attr >> 16) & 0o170000 == 0o120000: raise ValueError('symlink source rejected')
            blob=source.read(info)
            blob.decode('utf-8-sig')  # no binary payload silently admitted
            if p.suffix=='.py': ast.parse(blob,filename=info.filename)
            files[info.filename]=blob
    output.mkdir(parents=True)
    manifest={'schema':'source-garage-review/1','revision':revision,'baseline':baseline,
              'excluded_nontext_paths':excluded,'archives':[]}
    for label,selection in [('source-review',files),('changed-files',{k:v for k,v in files.items() if k in changed})]:
        hashes={k:hashlib.sha256(v).hexdigest() for k,v in sorted(selection.items())}
        member_manifest=json.dumps({'revision':revision,'baseline':baseline,'files':hashes},indent=2).encode()
        path=output/(label+'.zip')
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for name,blob in sorted(selection.items()): archive.writestr(name,blob)
            archive.writestr('SOURCE_REVIEW_MANIFEST.json',member_manifest)
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None: raise ValueError('ZIP CRC check failed')
            for name,digest in hashes.items():
                if hashlib.sha256(archive.read(name)).hexdigest()!=digest: raise ValueError('archive hash mismatch')
        manifest['archives'].append({'path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                    'bytes':path.stat().st_size,'source_members':len(selection),'verified_hashes':len(hashes),
                                    'python_syntax_checked':sum(k.endswith('.py') for k in selection)})
    (output/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',required=True)
    parser.add_argument('--revision',default='HEAD')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(package(args.baseline,args.revision,args.output),indent=2))
