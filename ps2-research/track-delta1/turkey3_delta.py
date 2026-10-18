"""TRACK-DELTA1: build the Turkey3 Course Delta Registry v2 record.

Read-only. Inputs: a geometry_delta report for TURKEY3 (local, ignored data/geom1),
the PS2 and PC Turkey3 scene XML, and the Course SDK reference checkout.
Writes only the registry JSON; originals are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import course_delta as cd  # noqa: E402

GEOM_CATEGORIES = (  # (category, regex on lower-cased material string)
    ('puddle', r'\$shader\(puddle\)'),
    ('foliage_treeblend', r'\$shader\(treeblend\)'),
    ('foliage_tree', r'\$shader\(tree\)'),
    ('object_building', r'rustic hut|fence hut|house'),
    ('object_vehicle_prop', r'caravan|boat|tyres'),
    ('ground', r'\$shader\(ground\)'),
)


def categorize(material):
    low = material.lower()
    for name, pattern in GEOM_CATEGORIES:
        if re.search(pattern, low):
            return name
    return 'other'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry_elements(report):
    buckets = defaultdict(lambda: {'groups': 0, 'triangles': 0, 'area': 0.0,
                                   'materials': set(), 'relations': defaultdict(int)})
    exact = 0
    for g in report['groups']:
        src = g['source']
        if src.get('representation') != 'PS2_VISUAL_SOURCE_MESH':
            continue
        rel = g['geometry_relation']
        if rel == 'EXACT_TRIANGLE_MATCH':
            exact += g['source_triangles']
            continue
        b = buckets[categorize(src['material'])]
        b['groups'] += 1
        b['triangles'] += g['source_triangles']
        b['area'] += g['area']
        b['materials'].add(re.sub(r'\s+', ' ', src['material'])[:80])
        b['relations'][rel] += g['source_triangles']
    out = []
    for name, b in sorted(buckets.items()):
        puddle = name == 'puddle'
        element = {
            'id': f'TURKEY3:geometry:{name}',
            'layer': 'geometry',
            'delta_class': 'MISSING_ON_PC' if puddle else 'UNCLASSIFIED',
            'channel': 'A_RENDER_OVERLAY' if puddle else 'UNDECIDED',
            'evidence': 'CONFIRMED_BY_BYTES' if puddle else 'STATIC_INFERENCE',
            'sources': ['data/geom1/TURKEY3-cli.json (tools/geometry_delta.py, baseline profile)',
                        'geom1/final-report.md']
                       + (['water1/turkey3-delta.md', 'pc-port/docs/course-objects1/final-report.md'] if puddle else []),
            'metrics': {'groups': b['groups'], 'non_exact_triangles': b['triangles'],
                        'ps2_extra_triangles': b['relations'].get('PS2_EXTRA_VISUAL_SOURCE', 0),
                        'relations': dict(sorted(b['relations'].items())),
                        'area': round(b['area'], 3), 'materials': sorted(b['materials'])[:6]},
            'status': 'IMPLEMENTED_PENDING_USER_RUNTIME' if puddle else 'RESEARCHED',
        }
        if not puddle:
            element['blocker'] = ('Extra PS2 source is not proved visible or absent on PC (LOD, re-triangulation, '
                                  'existing PC counterpart); needs per-group matching')
        out.append(element)
    pc_only = [g for g in report['groups'] if g['geometry_relation'] == 'PC_EXTRA_COMPILED_DRAW']
    out.append({
        'id': 'TURKEY3:geometry:pc_only',
        'layer': 'geometry', 'delta_class': 'SAME', 'channel': 'NONE', 'evidence': 'STATIC_INFERENCE',
        'sources': ['data/geom1/TURKEY3-cli.json (reverse direction)'],
        'metrics': {'groups': len(pc_only), 'triangles': sum(g['source_triangles'] for g in pc_only)},
        'status': 'RESEARCHED',
        'blocker': 'PC compiled draws with no PS2 source match; kept untouched by the delta-port (delta-port never removes PC content)',
    })
    return out, exact


def scene_elements(ps2, pc, ps2_rows, pc_rows):
    els = []

    def add(eid, layer, cls, channel, ev, sources, metrics, status, blocker=None):
        e = {'id': eid, 'layer': layer, 'delta_class': cls, 'channel': channel, 'evidence': ev,
             'sources': sources, 'metrics': metrics, 'status': status}
        if blocker:
            e['blocker'] = blocker
        els.append(e)

    pcc = pc['controller_egg_counts']
    ctl = ps2['controller_egg_counts']
    add('TURKEY3:rigid_prop:tumbleweed', 'rigid_prop', 'MISSING_ON_PC', 'C_NATIVE_HOOK', 'CONFIRMED_BY_BYTES',
        ['rigid1/turkey1-tumbleweed.md', 'pc-port/docs/rigid-port1.3/final-report.md'],
        {'ps2_eggs': ctl['gaAiRigidBody'], 'pc_eggs': pcc['gaAiRigidBody']},
        'BLOCKED', 'RIGID-PORT1.3 NO-GO for private admission; needs new gate G-PROP')
    add('TURKEY3:bird:manager', 'bird', 'MISSING_ON_PC', 'A_RENDER_OVERLAY', 'CONFIRMED_BY_BYTES',
        ['ambient2/final-report.md'],
        {'ps2_managers': ctl['gaAnimals_BirdManager'], 'pc_managers': pcc['gaAnimals_BirdManager'],
         'ps2_bird_marker_lists': sorted(k for k in ps2['marker_lists'] if k in ('FlightList', 'MillingList'))},
        'RESEARCHED', 'Live bird counts UNKNOWN; controller not implemented')
    add('TURKEY3:emitter:smoke', 'emitter', 'MISSING_ON_PC', 'UNDECIDED', 'CONFIRMED_BY_BYTES',
        ['cdelta1/course-dressing-survey.md'],
        {'ps2_eggs': ctl['aiSpawnParticle'], 'pc_eggs': pcc['aiSpawnParticle']},
        'NOT_STARTED', 'aiSpawnParticle effect binding UNKNOWN (plan T8)')
    ps2_split = [r for r in ps2_rows if 'gaRaceSplitTimeAI' in r['owners']]
    pc_split = [r for r in pc_rows if 'gaRaceSplitTimeAI' in r['owners']]
    add('TURKEY3:trigger:split', 'trigger', 'DIFFERENT_LOGIC', 'B_DATA_COPY', 'CONFIRMED_BY_BYTES',
        ['cdelta1/checkpoint-survey.md', 'src/master_rallye/course_race_authoring.py'],
        {'ps2_split_eggs': len(ps2_split), 'pc_split_eggs': len(pc_split),
         'ps2_positions': [r['position'] for r in ps2_split], 'pc_positions': [r['position'] for r in pc_split]},
        'RESEARCHED', 'Why PC has one more split Egg is UNKNOWN; compare Split Time ID/Radius before any edit')
    ml = {}
    for name in sorted(set(ps2['marker_lists']) | set(pc['marker_lists'])):
        a, b = ps2['marker_lists'].get(name), pc['marker_lists'].get(name)
        ml[name] = {'ps2': a and a['count'], 'pc': b and b['count'],
                    'identical_ordered_xyz': bool(a and b and a['ordered_xyz_f32_sha256'] == b['ordered_xyz_f32_sha256'])}
    add('TURKEY3:trigger:marker_lists', 'trigger', 'DIFFERENT_LOGIC', 'B_DATA_COPY', 'CONFIRMED_BY_BYTES',
        ['src/master_rallye/course_xml.py', 'cdelta1/course-pairs.md'], {'marker_lists': ml},
        'RESEARCHED', 'Limit lists are named differently on PS2 (...Limit2, Boom/StaticCameras); semantic mapping UNKNOWN')
    ma, mb = ps2['model_references'], pc['model_references']
    diff = {k: [ma.get(k, 0), mb.get(k, 0)] for k in sorted(set(ma) | set(mb)) if ma.get(k, 0) != mb.get(k, 0)}
    add('TURKEY3:checkpoint:model', 'checkpoint', 'DIFFERENT_MATERIAL', 'B_DATA_COPY', 'CONFIRMED_BY_BYTES',
        ['cdelta1/checkpoint-survey.md'], {'model_reference_count_diff_ps2_pc': diff},
        'RESEARCHED', 'Checkpoint asset differs (PS2 drum vs PC legacy); knockability owner UNKNOWN')
    return els


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--geometry-report', type=Path, default=ROOT / 'data/geom1/TURKEY3-cli.json')
    ap.add_argument('--ps2-scene', type=Path, default=ROOT / 'data/cdelta1/cache/TNG/DATASCENE/RACETEST/TURKEY3.XML')
    ap.add_argument('--pc-scene', type=Path, required=True)
    ap.add_argument('--sdk', type=Path, required=True)
    ap.add_argument('--pc-dx', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    report = json.loads(args.geometry_report.read_text(encoding='utf-8'))
    sdk, _ = cd.sdk_modules(args.sdk)
    ps2, ps2_rows = cd.parse_scene(args.ps2_scene.read_bytes(), 'ps2', sdk)
    pc, pc_rows = cd.parse_scene(args.pc_scene.read_bytes(), 'pc', sdk)
    geom, exact = geometry_elements(report)
    registry = {
        'schema_version': 2,
        'inputs': {'ps2_provenance': 'cdelta1/input-provenance.json',
                   'pc_provenance': 'cdelta1/input-provenance.json#pc_source_sha256'},
        'courses': [{
            'course': 'TURKEY3',
            'ps2_scene': '/TNG/DATASCENE/RACETEST/TURKEY3.XML',
            'pc_scene': 'DataScene/RaceTest/Turkey3.xml',
            'ps2_psm_sha256': report['ps2_source']['decoded_sha256'],
            'pc_dx_sha256': sha(args.pc_dx),
            'elements': geom + scene_elements(ps2, pc, ps2_rows, pc_rows)}],
    }
    args.output.write_text(json.dumps(registry, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'elements': len(registry['courses'][0]['elements']), 'exact_ps2_triangles': exact}))


if __name__ == '__main__':
    main()
