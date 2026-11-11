"""Publish a built DLL set into the shared builds folder and register it.

D:\\Game\\Master Rallye\\_builds is the single place to take renderer/loader
builds from. Every entry is an immutable folder <component>/<date>_<name>_<sha8>
with the files, BUILD.json (hashes, source commit, dirty state, notes) and a
row in builds.json. --current marks the entry as the base to continue from.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, shutil, subprocess
from pathlib import Path

BUILDS = Path(r'D:\Game\Master Rallye\_builds')
COMPONENTS = ('renderer', 'loader', 'vehicles', 'tools')


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True).stdout.strip()


def publish(component, name, files, repo, notes, current=False, root=BUILDS):
    if component not in COMPONENTS: raise SystemExit('component must be one of ' + ', '.join(COMPONENTS))
    files = [Path(f) for f in files]
    main = files[0]; digest = sha(main)
    folder = root / component / f"{datetime.date.today():%Y-%m-%d}_{name}_{digest[:8]}"
    if folder.exists(): raise SystemExit('already published: ' + str(folder))
    folder.mkdir(parents=True)
    rows = []
    for f in files:
        shutil.copy2(f, folder / f.name)
        rows.append({'file': f.name, 'sha256': sha(folder / f.name), 'size': (folder / f.name).stat().st_size, 'source_path': str(f)})
    info = {'schema': 'mr-shared-build/1', 'component': component, 'name': name, 'published': datetime.datetime.now().isoformat(timespec='seconds'),
            'files': rows, 'notes': notes}
    if repo:
        info['source'] = {'worktree': str(repo), 'branch': git(repo, 'branch', '--show-current'), 'commit': git(repo, 'rev-parse', 'HEAD'),
                          'dirty': bool(git(repo, 'status', '--porcelain', '--untracked-files=no'))}
    (folder / 'BUILD.json').write_text(json.dumps(info, indent=1) + '\n', encoding='utf-8')
    index_path = root / 'builds.json'
    index = json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else {'schema': 'mr-shared-builds/1', 'current': {}, 'entries': []}
    entry = {'component': component, 'folder': str(folder.relative_to(root)), 'main_sha256': digest, 'name': name,
             'commit': info.get('source', {}).get('commit'), 'dirty': info.get('source', {}).get('dirty'), 'notes': notes}
    index['entries'].append(entry)
    if current: index['current'][component] = entry['folder']
    index_path.write_text(json.dumps(index, indent=1) + '\n', encoding='utf-8')
    return folder


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('component'); p.add_argument('name'); p.add_argument('files', nargs='+')
    p.add_argument('--repo'); p.add_argument('--notes', default=''); p.add_argument('--current', action='store_true')
    a = p.parse_args()
    print(publish(a.component, a.name, a.files, a.repo, a.notes, a.current))


if __name__ == '__main__':
    main()
