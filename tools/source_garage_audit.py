"""Bounded, read-only external source census. No game or tool code is executed.

Full file metadata stays in --inventory outside source roots. The small report
pins that inventory plus executable/archive/vehicle candidates; names are leads,
never decoded model identities. No asset contents are serialized.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct

ARCHIVES = {'.pod','.cod','.dta','.big','.pak','.grp','.zap','.bnk','.tc','.sbf','.pssg','.nfs','.jpk'}
MODELS = {'.bin','.smf','.mdl','.pdo','.pdt','.rcx','.p3d','.bgx','.coc','.tbf','.scn','.vmf','.rbb','.sbb'}
TEXTURES = {'.dds','.txr','.tex','.raw','.act','.opa','.tga','.bmp','.t2x','.t0x','.t1x'}
AUDIO = {'.wav','.aif','.aiff','.mp3','.ogg','.bnk','.sfx','.str'}
LEAD = re.compile(r'vehicl|cars?[\\/_.]|truck|pajero|mits|rav4|megane|renault|toyota|hilux|suv', re.I)


def linked(path: Path) -> bool:
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def signature(head: bytes) -> str:
    for magic, name in ((b'MZ','DOS/PE candidate'),(b'\x7fELF','ELF'),(b'POD2','POD2'),
                        (b'POD3','POD3'),(b'POD4','POD4'),(b'EPD1','EPD1'),
                        (b'DDS ','DDS'),(b'PSSG','PSSG'),(b'PK\x03\x04','ZIP'),
                        (b'RIFF','RIFF'),(b'\x1f\x8b','gzip'),(b'BIGF','BIGF')):
        if head.startswith(magic): return name
    return 'UNKNOWN'


def identity(path: Path, root: Path, max_bytes: int) -> dict:
    if linked(path): raise ValueError('linked/reparse source rejected')
    before = path.stat()
    if not stat.S_ISREG(before.st_mode): raise ValueError('non-regular source')
    if before.st_size > max_bytes: raise ValueError('file size budget exceeded')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        head = stream.read(64); digest.update(head)
        if head.startswith(b'MZ') and len(head) == 64:
            peoff = struct.unpack_from('<I',head,60)[0]
            if peoff <= before.st_size - 6:
                stream.seek(peoff); pe = stream.read(6)
            else: pe = b''
            stream.seek(len(head))
        else: pe = b''
        for chunk in iter(lambda: stream.read(1024*1024), b''): digest.update(chunk)
    after = path.stat()
    if (before.st_size,before.st_mtime_ns,before.st_ino) != (after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError('source changed during read')
    name = path.relative_to(root).as_posix()
    ext = path.suffix.lower()
    roles = []
    if pe.startswith(b'PE\0\0'): roles.append('executable' if ext == '.exe' else 'PE-library')
    if ext in ARCHIVES: roles.append('container-candidate')
    if ext in MODELS: roles.append('model-candidate')
    if ext in TEXTURES: roles.append('texture-candidate')
    if ext in AUDIO: roles.append('audio-candidate')
    if LEAD.search(name): roles.append('vehicle-name-lead')
    result = {'path':name,'size':before.st_size,'sha256':digest.hexdigest(),'signature':signature(head),'roles':roles}
    if pe.startswith(b'PE\0\0'): result['pe_machine'] = hex(struct.unpack_from('<H',pe,4)[0])
    if head.startswith(b'\x7fELF') and len(head)>=20:
        result['elf_machine'] = int.from_bytes(head[18:20], 'little' if head[5]==1 else 'big')
    return result


def scan_game(game: dict, base: Path, *, max_files=100000, max_file_bytes=4*1024**3, max_total_bytes=100*1024**3) -> dict:
    root = Path(game['path'])
    if not root.is_absolute(): root = base / root
    result = dict(game, root=str(root.absolute()), edition='UNKNOWN', region='UNKNOWN',
                  archive_version='UNKNOWN; see signatures and format smoke evidence',
                  executable_version='UNKNOWN; exact hashes identify this installation',
                  missing_inputs=[], errors=[], files=[])
    if not root.exists():
        result.update(status='MISSING INPUT', missing_inputs=['configured source directory absent'],
                      levels={'L0':'MISSING INPUT','L1':'MISSING INPUT','L2':'MISSING INPUT','Gameplay':'NOT TESTED'})
        return result
    # Reject a link in ANY ancestor before resolve() could hide its presence.
    if any(linked(p) for p in (root,*root.parents)):
        raise ValueError('source root/ancestor is a link/reparse point')
    if not root.is_dir():
        result.update(status='FAIL',errors=[{'path':str(root),'error':'configured root is not a directory'}],
                      levels={'L0':'FAIL','L1':'NOT TESTED','L2':'NOT TESTED','Gameplay':'NOT TESTED'})
        return result
    total = 0; paths = []
    def walk_error(error):
        result['errors'].append({'path':str(error.filename),'error':'directory enumeration failed: '+str(error)})
    for parent, dirs, names in os.walk(root, followlinks=False,onerror=walk_error):
        for dirname in list(dirs):
            p = Path(parent)/dirname
            if linked(p):
                result['errors'].append({'path':p.relative_to(root).as_posix(),'error':'linked directory excluded'})
                dirs.remove(dirname)
        for name in sorted(names):
            p = Path(parent)/name
            if linked(p):
                result['errors'].append({'path':p.relative_to(root).as_posix(),'error':'linked file excluded'}); continue
            size = p.stat().st_size
            total += size; paths.append(p)
            if len(paths)>max_files or total>max_total_bytes: raise ValueError('source census budget exceeded')
    for p in sorted(paths):
        try: result['files'].append(identity(p,root,max_file_bytes))
        except (OSError, ValueError) as error: result['errors'].append({'path':p.relative_to(root).as_posix(),'error':str(error)})
    result['status'] = 'WARN' if result['errors'] else 'PASS'
    result['platform_observed'] = sorted(set('Windows PE '+f['pe_machine'] if 'pe_machine' in f else 'ELF machine '+str(f['elf_machine']) for f in result['files'] if 'pe_machine' in f or 'elf_machine' in f))
    result['directories'] = sorted(set(str(Path(f['path']).parent).replace('\\','/') for f in result['files']))
    result['extension_counts'] = dict(Counter(Path(f['path']).suffix.lower() or '<none>' for f in result['files']).most_common())
    result['signature_counts'] = dict(Counter(f['signature'] for f in result['files']).most_common())
    result['file_count'] = len(result['files']); result['total_bytes'] = sum(f['size'] for f in result['files'])
    result['tree_sha256'] = hashlib.sha256(json.dumps(result['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    result['levels'] = {'L0':result['status'],'L1':'NOT TESTED','L2':'NOT TESTED','Gameplay':'NOT TESTED'}
    return result


def output_guard(output: Path, roots: list[Path]):
    target = output.resolve()
    if any(target == r.resolve() or r.resolve() in target.parents for r in roots):
        raise ValueError('output must be outside every source root')
    if output.exists(): raise ValueError('output already exists; choose a fresh path')


def run(config: Path, inventory: Path, summary: Path, workers=2):
    cfg = json.loads(config.read_text(encoding='utf-8'))
    if cfg.get('schema') != 'source-garage-roots/1': raise ValueError('unsupported config schema')
    games = cfg['games']; base=Path(cfg['base'])
    if len(games)>64 or len({g['id'] for g in games}) != len(games): raise ValueError('invalid game IDs/count')
    roots = [Path(g['path']) if Path(g['path']).is_absolute() else base/g['path'] for g in games]
    for out in (inventory,summary): output_guard(out,roots)
    if inventory.resolve()==summary.resolve(): raise ValueError('outputs must differ')
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda g: scan_game(g,base),games))
    payload = {'schema':'source-garage-corpus/1','date':date.today().isoformat(),'reader_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'config_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),
               'scope':'all regular files in configured roots; no execution; filename roles are candidates only','games':results}
    inventory.parent.mkdir(parents=True,exist_ok=True)
    inventory.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    small = dict(payload, full_inventory={'path':str(inventory.resolve()),'sha256':hashlib.sha256(inventory.read_bytes()).hexdigest(),'size':inventory.stat().st_size})
    small['games']=[]
    for entry in results:
        game = {k:v for k,v in entry.items() if k not in ('files','directories')}
        files = entry['files']
        game['top_directories']=sorted(set(f['path'].split('/')[0] for f in files if '/' in f['path']))
        game['executables']=[f for f in files if 'executable' in f['roles'] or f['signature']=='ELF']
        game['representative_candidates']=[f for f in files if any(r in f['roles'] for r in ('vehicle-name-lead','container-candidate','model-candidate','texture-candidate','audio-candidate'))][:100]
        game['candidate_coverage']='first 100 lexical candidates; complete paths/hashes in full_inventory'
        small['games'].append(game)
    summary.parent.mkdir(parents=True,exist_ok=True)
    summary.write_text(json.dumps(small,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return small


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--summary',type=Path,required=True)
    parser.add_argument('--workers',type=int,choices=range(1,5),default=2)
    args=parser.parse_args()
    result=run(args.config,args.inventory,args.summary,args.workers)
    print(json.dumps({'games':len(result['games']),'files':sum(g.get('file_count',0) for g in result['games']),'inventory':result['full_inventory']}))
