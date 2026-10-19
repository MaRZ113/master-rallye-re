"""TRACK-GROUND1 package validation: structural checks of a ps2_course_objects.py output tree against the retail corpus. Read-only.

Checks: (1) every converted model parses, texture slots resolve to files in the model folder and the DXT headers carry the payload CRC;
(2) the XML parses, Egg names are unique, every Egg model has a DX in the package; (3) the loose turkey3.dx differs from retail only in the local index
array (neutralised triangles) and the tag100 suffix; (4) neutralised triangles are exactly the ones in the report and nothing else changed; (5) z-fighting:
added PS2 ground triangles that are coplanar (0.03) and overlapping with a remaining PC ground triangle; (6) object hull brushes are solid inside;
(7) tag100 invariants. Prints one JSON document.
"""
import argparse
import json
import struct
import sys
import zlib
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TD1 = HERE.parent / 'track-delta1'
sys.path.insert(0, str(TD1))
sys.path.insert(0, str(TD1.parent / 'tools'))
sys.path.insert(0, str(TD1.parent.parent / 'src'))
import tag100_tree as tt  # noqa: E402
import ps2_terrain as terrain  # noqa: E402
import ground_clusters as gcl  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--package', type=Path, required=True)
    ap.add_argument('--pc-root', type=Path, required=True)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    pkg = a.package
    report = json.loads((pkg / 'report.json').read_text())
    out = {'package': str(pkg)}
    # 1. models and textures
    models, problems = 0, []
    for dx in sorted((pkg / 'DataGx/Misc/PS2Port').rglob('*.dx')):
        models += 1
        m = parse_dx_bytes(dx.read_bytes())
        if not m.diagnostics.validated:
            problems.append(f'{dx.name}: not validated')
        for slot in m.physical_draws[0].texture_slots:
            if slot.value != 'Null' and not (dx.parent / (slot.value + '.dxt')).exists():
                problems.append(f'{dx.name}: texture {slot.value} missing in the model folder')
    for dxt in sorted((pkg / 'DataGx/Misc/PS2Port').rglob('*.dxt')):
        data = dxt.read_bytes()
        t = parse_dxt_bytes(data)
        if struct.unpack_from('<I', data, 8)[0] != zlib.crc32(data[20:]) & 0xFFFFFFFF:
            problems.append(f'{dxt.name}: header word is not the payload CRC32')
    out['models'] = models
    out['model_problems'] = problems
    # 2. XML
    xml_bytes = (pkg / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    root = ET.fromstring(xml_bytes)
    names, eggs = [], []
    for egg in root.iter('Egg'):
        names.append(egg.get('Name'))
        for v in egg.findall('Value'):
            if v.get('Name') == 'en3d Model Name' and v.get('Value', '').lower().startswith('misc' + chr(92) + 'ps2port'):
                eggs.append(v.get('Value'))
    dup = {n for n in names if names.count(n) > 1}
    missing = [e for e in eggs if not (pkg / 'DataGx' / (e.replace(chr(92), '/') + '.dx')).exists()]
    out['eggs'] = {'ps2port_eggs': len(eggs), 'duplicate_egg_names': sorted(dup), 'models_missing': missing}
    # 3/4. course DX against retail
    retail = (a.pc_root / 'DataGx/Course/Turkey3/turkey3.dx').read_bytes()
    patched = (pkg / 'DataGx/Course/Turkey3/turkey3.dx').read_bytes()
    model = parse_course_dx_bytes(retail, 'retail')
    tag = extract_tag100_from_dx_bytes(retail, 'retail').tag_offset
    lo, hi = model.local_index_offset, model.local_index_offset + 2 * len(model.local_indices)
    changed = [i for i in range(min(tag, len(patched))) if retail[i] != patched[i]]
    outside = [i for i in changed if not lo <= i < hi]
    neutral_reported = report['terrain']['pc_non_exact_ground_neutralised'] if report.get('terrain') else 0
    degenerate = 0
    new_model = parse_course_dx_bytes(patched, 'patched')
    for d in new_model.physical_draws:
        for k in range(d.triangle_count):
            f = d.index_start + 3 * k
            idx = new_model.local_indices[f:f + 3]
            if idx[0] == idx[1] == idx[2]:
                degenerate += 1
    retail_degenerate = sum(1 for d in model.physical_draws for k in range(d.triangle_count)
                            if len(set(model.local_indices[d.index_start + 3 * k:d.index_start + 3 * k + 3])) == 1)
    out['course_dx'] = {'retail_bytes': len(retail), 'patched_bytes': len(patched), 'render_prefix_changed_bytes_outside_local_indices': len(outside),
                        'local_index_bytes_changed': len(changed), 'triangles_neutralised_in_report': neutral_reported,
                        'degenerate_triangles_retail': retail_degenerate, 'degenerate_triangles_patched': degenerate,
                        'newly_degenerate': degenerate - retail_degenerate, 'tag100_offset_equal': tag == extract_tag100_from_dx_bytes(patched, 'p').tag_offset}
    # 7. tag100
    tree = tt.Tree(extract_tag100_from_dx_bytes(patched, 'p').raw)
    out['tag100'] = {'invariants_ok': tree.counts_ok(), 'header': list(tree.serialize()[4:24] and struct.unpack_from('<5I', tree.serialize(), 4))}
    # 6. object hulls solid
    objs = []
    if report.get('models'):
        for m in report['models']:
            for inst in m['instances']:
                c = inst['translation']
                solid = tree.f0[tree.classify((c[0], c[1], c[2]))] == tt.SOLID
                objs.append({'egg': inst['egg'], 'centroid_solid': bool(solid)})
    out['object_hulls'] = objs
    # 5. z-fighting between added PS2 ground and remaining PC ground
    if report.get('terrain'):
        _, _, ps2_non, pc_non, pc_all = terrain.load_delta(Path('D:/Game/Master Rallye PS2'), a.pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
        replace, candidates, _ = terrain.refine(ps2_non, pc_non, pc_all)
        neutral, kept = terrain.with_replacement(candidates, replace)
        gone = {(t['draw'], t['first_index']) for t in neutral}
        remaining = [t for t in pc_all if t['ground'] and (t['draw'], t['first_index']) not in gone]
        grid = defaultdict(list)
        C = 8.0
        for t in remaining:
            xs, zs = [p[0] for p in t['p']], [p[2] for p in t['p']]
            for cx in range(int(min(xs) // C), int(max(xs) // C) + 1):
                for cz in range(int(min(zs) // C), int(max(zs) // C) + 1):
                    grid[cx, cz].append(t['p'])
        def height(p3, x, z):
            (ax, ay, az), (bx, by, bz), (cx2, cy, cz2) = p3
            den = (bz - cz2) * (ax - cx2) + (cx2 - bx) * (az - cz2)
            if abs(den) < 1e-9:
                return None
            w1 = ((bz - cz2) * (x - cx2) + (cx2 - bx) * (z - cz2)) / den
            w2 = ((cz2 - az) * (x - cx2) + (ax - cx2) * (z - cz2)) / den
            w3 = 1 - w1 - w2
            return w1 * ay + w2 * by + w3 * cy if min(w1, w2, w3) >= -1e-6 else None
        zf = 0
        for t in replace:
            x = sum(p[0] for p in t['p']) / 3
            z = sum(p[2] for p in t['p']) / 3
            y = sum(p[1] for p in t['p']) / 3
            for p3 in grid.get((int(x // C), int(z // C)), []):
                h = height(p3, x, z)
                if h is not None and abs(h - y) < 0.03:
                    zf += 1
                    break
        out['z_fighting'] = {'added_ps2_triangles': len(replace), 'coplanar_with_a_remaining_pc_triangle_at_centroid': zf,
                             'pc_triangles_kept_without_replacement': len(kept)}
    print(json.dumps(out, indent=1))
    if a.out:
        a.out.write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
