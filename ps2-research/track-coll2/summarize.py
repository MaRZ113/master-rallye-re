"""Markdown tables from collision-36.json and object-collision-36.json (W1 report)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    rows = json.loads((HERE / 'collision-36.json').read_text())
    print('| Course | random points mismatch | columns | new vs PS2 differ | horizontal rays / differ | fallback plane steep on new only / other plane | retail vs PS2 differ | plane nodes new / retail | tree MB new / retail | codes same-plane / path / default / PS2 splitter | contact code = retail | surface type changes |')
    print('|---|---:|---:|---:|---|---|---:|---|---|---|---|---:|')
    tot = {'cols': 0, 'diff': 0, 'pts': 0, 'mis': 0, 'rays': 0, 'rdiff': 0, 'fb': 0, 'steep': 0, 'fother': 0}
    for name, r in rows.items():
        if 'error' in r:
            print(f'| {name} | error: {r["error"][:60]} |')
            continue
        b, v = r['build'], r['validation']
        t, c, cc_ = b['tree'], v['columns'], v['contact_codes']
        prov = t['code_provenance']
        same = cc_.get('same_code_as_retail', 0)
        other = cc_.get('other_code_than_retail', 0)
        tot['cols'] += c['columns']
        tot['diff'] += c.get('new_differs', 0)
        tot['pts'] += v['random_points']['points']
        tot['mis'] += v['random_points']['mismatch']
        h, f = v.get('horizontal_rays', {}), v.get('fallback_planes', {})
        tot['rays'] += h.get('rays', 0)
        tot['rdiff'] += h.get('new_differs', 0)
        tot['fb'] += f.get('points', 0)
        tot['steep'] += f.get('steep_on_new_only', 0)
        tot['fother'] += f.get('other_plane', 0)
        print(f"| {name} | {v['random_points']['mismatch']} | {c['columns']} | {c.get('new_differs', 0)} | {h.get('rays', 0)} / {h.get('new_differs', 0)} | "
              f"{f.get('steep_on_new_only', 0)} / {f.get('other_plane', 0)} of {f.get('points', 0)} | {c.get('retail_differs', 0)} | "
              f"{t['new_plane_nodes']} / {t['retail_plane_nodes']} | {t['new_tree_bytes'] / 1e6:.2f} / {t['retail_tree_bytes'] / 1e6:.2f} | "
              f"{prov.get('pc_same_plane', 0)} / {prov.get('pc_ground_path', 0)} / {prov.get('default', 0)} / {prov.get('ps2_splitter', 0)} | {same} of {same + other} | "
              f"{v['surface_types'].get('ps2_vs_retail_differs', 0)} |")
    print(f"\nTotals: {len(rows)} courses, {tot['pts']} random points with {tot['mis']} mismatches, {tot['cols']} columns with {tot['diff']} differing from the PS2 BSP, "
          f"{tot['rays']} horizontal rays with {tot['rdiff']} differing, {tot['fb']} fallback points with {tot['steep']} steep on the new tree only "
          f"and {tot['fother']} with another plane.")
    inv = HERE / 'object-collision-36.json'
    if inv.exists():
        data = json.loads(inv.read_text())
        print('\n| Course | static objects solid in both / PS2 only / PC only / neither | Egg models with own collision (side: model) |')
        print('|---|---|---|')
        for name, r in data.items():
            s = r['summary']
            eggs = ', '.join(f"{e['side']}: {e['model'].split(chr(92))[-1]}" for e in r['egg_models'] if e['collision'].startswith('tags'))
            print(f"| {name} | {s.get('both', 0)} / {s.get('ps2_only', 0)} / {s.get('pc_only', 0)} / {s.get('neither', 0)} | {eggs} |")


if __name__ == '__main__':
    main()
