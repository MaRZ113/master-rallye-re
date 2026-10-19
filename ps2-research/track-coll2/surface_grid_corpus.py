"""Check the tag1400 rule on every retail course DX: rebuilding bounds, dimensions and cells from the records must give the retail bytes."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent.parent / 'src'))
import surface_grid as sg, tag1400_io as io
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes
from master_rallye.course_tag1400 import parse_course_tag1400_bytes

def main(root, out):
    res = {}
    for dx in sorted(Path(root).glob('DataGx/Course/*/*.dx')):
        try:
            _, _, u, rest = io.split_suffix(extract_tag100_from_dx_bytes(dx.read_bytes(), dx.name).raw)
        except Exception as e:
            res[dx.name] = {'error': str(e)[:120]}; continue
        t = parse_course_tag1400_bytes(u, dx.name)
        same = sg.rebuild_from_parsed(t) == u
        res[dx.name] = {'records': len(t.records), 'strings': len(t.strings), 'cell': t.scalar, 'dims': [t.dimension_0, t.dimension_1],
                        'rebuild_identical': same, 'roundtrip_identical': io.from_parsed(t) == u, 'tag1500_bytes': len(rest)}
        print(dx.name, res[dx.name])
    Path(out).write_text(json.dumps(res, indent=1))
    print(sum(1 for v in res.values() if v.get('rebuild_identical')), 'of', len(res), 'rebuild identical')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
