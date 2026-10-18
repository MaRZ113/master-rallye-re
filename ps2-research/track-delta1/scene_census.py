"""Scene-logic census over all 36 paired courses (PS2 XML versus PC XML): splits, copies, limit lists, controllers, checkpoint models."""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE))
import course_delta as cd  # noqa: E402
import tngtool as t  # noqa: E402

SLASH = chr(92)


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def split_differences(a, b, position_tolerance=0.01):
    """Numeric comparison of (id, radius, extra_time, position) tuples; returns {field: (ps2, pc)} for real differences."""
    out = {}
    for name, x, y in zip(('id', 'radius', 'extra_time'), a[:3], b[:3]):
        if num(x) != num(y):
            out[name] = (num(x), num(y))
    if a[3] and b[3]:
        d = max(abs(p - q) for p, q in zip(a[3], b[3]))
        if d > position_tolerance:
            out['position_max_axis_shift'] = round(d, 3)
    return out


def splits(rows):
    out = {}
    for r in rows:
        if 'gaRaceSplitTimeAI' not in r['owners']:
            continue
        vals = {v['name']: v['value'] for p in r['parameters'] for v in p['values']}
        out[r['egg']] = (vals.get('Split Time ID'), vals.get('Radius'), vals.get('ExtraTime'),
                         tuple(round(x, 2) for x in r['position']) if r['position'] else None)
    return out


def main(ps2_root, pc_root, sdk_path, output):
    root = Path(ps2_root)
    man, _ = t.load_pak(root / 'TNG.PAK')
    sdk, _ = cd.sdk_modules(Path(sdk_path))
    pairs = json.loads((HERE.parent / 'cdelta1/course-pairs.json').read_text(encoding='utf-8'))
    rows = []
    for pair in pairs:
        entry = [e for e in man['entries'] if e['kind'] == 'file' and e['path'].upper() == pair['ps2'].upper()][0]
        ps2_xml = t.read_payload(entry, root / 'TNG.000')[0]
        pc_xml = (Path(pc_root) / pair['pc']).read_bytes()
        a, ra = cd.parse_scene(ps2_xml, 'ps2', sdk)
        b, rb = cd.parse_scene(pc_xml, 'pc', sdk)
        sa, sb = splits(ra), splits(rb)
        shared = sorted(set(sa) & set(sb))
        ctl_a, ctl_b = a['controller_egg_counts'], b['controller_egg_counts']
        rows.append({
            'course': pair['ps2'].replace(SLASH, '/').split('/')[-1][:-4],
            'splits_ps2': len(sa), 'splits_pc': len(sb),
            'splits_shared_by_name': len(shared),
            'shared_splits_identical': sum(not split_differences(sa[n], sb[n]) for n in shared),
            'split_differences': {n: split_differences(sa[n], sb[n]) for n in shared if split_differences(sa[n], sb[n])},
            'pc_only_splits': sorted(set(sb) - set(sa)), 'ps2_only_splits': sorted(set(sa) - set(sb)),
            'copy_of_eggs_pc': sorted(r['egg'] for r in rb if (r['egg'] or '').startswith('Copy of')),
            'copy_of_eggs_ps2': sorted(r['egg'] for r in ra if (r['egg'] or '').startswith('Copy of')),
            'ps2_controllers': ctl_a, 'pc_controllers': ctl_b,
            'ps2_checkpoint_models': {k: v for k, v in a['model_references'].items() if 'checkpoint' in k},
            'pc_checkpoint_models': {k: v for k, v in b['model_references'].items() if 'checkpoint' in k},
            'marker_lists_ps2_only': sorted(set(a['marker_lists']) - set(b['marker_lists'])),
            'marker_lists_pc_only': sorted(set(b['marker_lists']) - set(a['marker_lists'])),
            'entities': [a['entity_count'], b['entity_count']],
        })
    Path(output).write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8')
    print('course | splits ps2/pc | shared identical | pc-only | copy-of pc | rigid/birds/emitters/splines (ps2) | limit lists ps2-only')
    for r in rows:
        c = r['ps2_controllers']
        print(r['course'], f"{r['splits_ps2']}/{r['splits_pc']}", f"{r['shared_splits_identical']}/{r['splits_shared_by_name']}",
              r['pc_only_splits'], len(r['copy_of_eggs_pc']), (c['gaAiRigidBody'], c['gaAnimals_BirdManager'], c['aiSpawnParticle'], c['gaEntitySpline']),
              [m for m in r['marker_lists_ps2_only'] if 'Limit' in m])


if __name__ == '__main__':
    main(*sys.argv[1:5])
