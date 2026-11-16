"""Census of RCX archives (PC Rally Championship Xtreme): member names/types/sizes.

Usage: python -I rcx_census.py <Data dir> <out.json> [--extract <dir> <archive-stem>...]
Read-only on the source tree; extraction writes only into a fresh directory.
"""
import hashlib, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rcx_extract import read, unpack


def census(path):
    b, rows = read(path)
    members = []
    for r in rows:
        if r['type'] != 6:
            continue
        members.append({'name': r['name'], 'expanded': r['expanded'], 'stored': r['stored']})
    return {'file': path.name, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
            'members': members}


def extract(path, out):
    b, rows = read(path)
    out.mkdir(parents=True, exist_ok=False)
    for r in rows:
        if r['type'] != 6:
            continue
        raw = b[r['offset']:r['offset'] + r['stored']]
        data = unpack(raw, r['expanded']) if r['expanded'] else raw
        (out / r['name']).write_bytes(data)


def main():
    data, out = Path(sys.argv[1]), Path(sys.argv[2])
    if '--extract' in sys.argv:
        k = sys.argv.index('--extract'); dest = Path(sys.argv[k + 1])
        for stem in sys.argv[k + 2:]:
            src = next(p for p in data.rglob('*.rcx') if p.stem.lower() == stem.lower())
            extract(src, dest / src.stem)
            print('extracted', src.name)
        return
    result = {}
    for sub in ('Cars', 'Levels'):
        result[sub] = []
        for p in sorted((data / sub).glob('*.rcx')):
            try:
                result[sub].append(census(p))
            except Exception as e:  # keep going, record the failure
                result[sub].append({'file': p.name, 'error': str(e)})
    for p in sorted(data.glob('*.rcx')) + sorted(data.glob('*.RCX')):
        try:
            result.setdefault('Root', []).append(census(p))
        except Exception as e:
            result.setdefault('Root', []).append({'file': p.name, 'error': str(e)})
    out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf8')
    for sub, items in result.items():
        print(sub, len(items), 'archives', sum(1 for i in items if 'error' in i), 'errors')


if __name__ == '__main__':
    main()
