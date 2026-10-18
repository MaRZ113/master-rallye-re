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


def channels(visual='N_A', spawn='N_A', physics='N_A', logic='N_A'):
    return {'visual': visual, 'spawn': spawn, 'physics': physics, 'logic': logic}


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
            'channels': channels('A_RENDER_OVERLAY' if puddle else 'UNDECIDED', physics='UNDECIDED'),
            'pcsx2_verification': 'REQUIRED_PENDING',
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
        'layer': 'geometry', 'delta_class': 'SAME', 'channels': channels('NONE', physics='NONE'),
        'pcsx2_verification': 'NOT_REQUIRED', 'evidence': 'STATIC_INFERENCE',
        'sources': ['data/geom1/TURKEY3-cli.json (reverse direction)'],
        'metrics': {'groups': len(pc_only), 'triangles': sum(g['source_triangles'] for g in pc_only)},
        'status': 'RESEARCHED',
        'blocker': 'PC compiled draws with no PS2 source match; kept untouched by the delta-port (delta-port never removes PC content)',
    })
    return out, exact


SUBKEYS = (('rustic hut', 'hut'), ('fence hut', 'fence'), ('house', 'house'), ('red caravan', 'caravan'),
           ('caravan', 'caravan'), ('boat', 'boats'), ('tyres', 'tyres'), ('turshrub', 'shrub'))


def subkey(row):
    low = row['material'].lower()
    for needle, name in SUBKEYS:
        if needle in low:
            return name
    return row['category'].split('_', 1)[-1]


def t1b_elements(t1b):
    """Refined, evidence-backed elements for every non-puddle geometry group (T1b)."""
    buckets = defaultdict(list)
    for row in t1b['groups']:
        if row['category'] == 'puddle':
            continue
        buckets[row['category'], subkey(row)].append(row)
    out = []
    for (cat, sub), rows in sorted(buckets.items()):
        verdicts = defaultdict(int)
        for r in rows:
            verdicts[r.get('fit', {}).get('verdict', 'GROUND_ANALYSIS')] += 1
        faces = sum(r['non_exact'] for r in rows)
        metrics = {'groups': len(rows), 'non_exact_triangles': faces, 'fit_verdict_groups': dict(sorted(verdicts.items())),
                   'textures': sorted({t for r in rows for t in r['textures']})[:6],
                   'pc_texture_family_draws': sorted({r['pc_texture_family_draws'] for r in rows})}
        fitted = sum(r['fit'].get('fitted_faces', 0) or (r['faces'] if r['fit']['verdict'] == 'WHOLE_GROUP_CONGRUENT' else 0)
                     for r in rows if 'fit' in r)
        if fitted:
            metrics['faces_with_congruent_pc_counterpart'] = fitted
            metrics['group_faces'] = sum(r['faces'] for r in rows)
        if cat in ('ground', 'other'):
            rel = defaultdict(int)
            for r in rows:
                for k, v in r['ground_relation'].items():
                    rel[k] += v
            metrics['vertical_relation_to_pc_surface'] = dict(sorted(rel.items()))
        keys = set(verdicts)
        if keys == {'NO_PC_TEXTURE_FAMILY'}:
            cls, channel, status = 'MISSING_ON_PC', 'A_RENDER_OVERLAY', 'RESEARCHED'
            note = 'No PC draw uses these textures, so the model has no PC twin by texture; PC-side substitute not searched'
        elif keys <= {'WHOLE_GROUP_CONGRUENT', 'COMPONENTS_CONGRUENT'}:
            cls, channel, status = 'PLACEMENT_DIFFERS', 'UNDECIDED', 'RESEARCHED'
            note = ('PC holds congruent geometry at another pose (fitted diagnostic, not authored); decide whether PS2 adds '
                    'instances or merely places existing meshes differently')
        elif sub == 'tyres':
            cls, channel, status = 'DIFFERENT_MATERIAL', 'UNDECIDED', 'RESEARCHED'
            note = 'Most tyre faces match exactly; the non-exact part differs in texture binding'
        else:
            cls, channel, status = 'UNCLASSIFIED', 'UNDECIDED', 'RESEARCHED'
            note = 'Mixed or no congruent fit; manual inspection needed'
        cov = {'total_area': 0.0, 'coplanar_pc_area': 0.0, 'near_parallel_pc_area': 0.0}
        plan = defaultdict(float)
        for r in rows:
            for k in cov:
                cov[k] += r['surface_coverage'][k]
            for k, v in r['plan_view_area'].items():
                plan[k] += v
        total = cov['total_area'] or 1.0
        metrics['area_coverage_percent'] = {
            'coplanar_pc': round(100 * cov['coplanar_pc_area'] / total, 1),
            'near_parallel_pc': round(100 * cov['near_parallel_pc_area'] / total, 1),
            'plan_view': {k: round(100 * v / total, 1) for k, v in sorted(plan.items())}}
        out.append({'id': f'TURKEY3:geometry:{cat}:{sub}', 'layer': 'geometry', 'delta_class': cls,
                    'channels': channels(channel, physics='UNDECIDED'), 'pcsx2_verification': 'REQUIRED_PENDING',
                    'evidence': 'STATIC_INFERENCE', 'status': status, 'blocker': note, 'metrics': metrics,
                    'sources': ['track-delta1/turkey3-t1b.json (tools/dressing_runtime.py rigid_shape_search, tolerance .001)',
                                'dressing1/pc-counterpart-search.md']})
    return out


def scene_elements(ps2, pc, ps2_rows, pc_rows):
    els = []

    def add(eid, layer, cls, chans, ev, sources, metrics, status, blocker=None, intent=None, gates=None):
        e = {'id': eid, 'layer': layer, 'delta_class': cls, 'channels': chans, 'evidence': ev,
             'sources': sources, 'metrics': metrics, 'status': status, 'pcsx2_verification': 'REQUIRED_PENDING'}
        if blocker:
            e['blocker'] = blocker
        if intent:
            e['behavior_intent'] = intent
        if gates:
            e['gates'] = gates
        els.append(e)

    pcc = pc['controller_egg_counts']
    ctl = ps2['controller_egg_counts']
    add('TURKEY3:rigid_prop:tumbleweed', 'rigid_prop', 'MISSING_ON_PC',
        channels('UNDECIDED', 'B_DATA_COPY', 'C_NATIVE_HOOK', 'UNDECIDED'), 'CONFIRMED_BY_BYTES',
        ['rigid1/turkey1-tumbleweed.md', 'pc-port/docs/rigid-port1.3/final-report.md'],
        {'ps2_eggs': ctl['gaAiRigidBody'], 'pc_eggs': pcc['gaAiRigidBody']},
        'BLOCKED', 'RIGID-PORT1.3 NO-GO for private admission; needs new gate G-PROP')
    add('TURKEY3:bird:manager', 'bird', 'MISSING_ON_PC',
        channels('A_RENDER_OVERLAY', 'UNDECIDED', 'N_A', 'UNDECIDED'), 'CONFIRMED_BY_BYTES',
        ['ambient2/final-report.md'],
        {'ps2_managers': ctl['gaAnimals_BirdManager'], 'pc_managers': pcc['gaAnimals_BirdManager'],
         'ps2_bird_marker_lists': sorted(k for k in ps2['marker_lists'] if k in ('FlightList', 'MillingList'))},
        'RESEARCHED', 'Live bird counts UNKNOWN; controller not implemented')
    add('TURKEY3:emitter:smoke', 'emitter', 'MISSING_ON_PC',
        channels('UNDECIDED', 'UNDECIDED', 'N_A', 'UNDECIDED'), 'CONFIRMED_BY_BYTES',
        ['cdelta1/course-dressing-survey.md'],
        {'ps2_eggs': ctl['aiSpawnParticle'], 'pc_eggs': pcc['aiSpawnParticle']},
        'NOT_STARTED', 'aiSpawnParticle effect binding UNKNOWN (plan T8)')
    ps2_split = [r for r in ps2_rows if 'gaRaceSplitTimeAI' in r['owners']]
    pc_split = [r for r in pc_rows if 'gaRaceSplitTimeAI' in r['owners']]

    def split_params(r):
        vals = {v['name']: v['value'] for p in r['parameters'] for v in p['values']}
        return {'egg': r['egg'], 'position': r['position'], 'id': vals.get('Split Time ID'),
                'radius': vals.get('Radius'), 'extra_time': vals.get('ExtraTime')}

    ps2_names = {r['egg'] for r in ps2_split}
    pc_only = [split_params(r) for r in pc_split if r['egg'] not in ps2_names]
    copies = [r['egg'] for r in pc_rows if (r['egg'] or '').startswith('Copy of')]
    add('TURKEY3:trigger:split', 'trigger', 'DIFFERENT_LOGIC',
        channels('NONE', 'NONE', 'N_A', 'B_DATA_COPY'), 'CONFIRMED_BY_BYTES',
        ['cdelta1/checkpoint-survey.md', 'src/master_rallye/course_race_authoring.py'],
        {'ps2_split_eggs': [split_params(r) for r in ps2_split], 'pc_split_eggs': [split_params(r) for r in pc_split],
         'pc_only_split_eggs': pc_only, 'pc_eggs_named_copy_of': copies},
        'RESEARCHED', 'PC-only Egg "Copy of SplitTime1" reuses Split Time ID 1 (radius 10, ExtraTime 85) with four checkpoint '
        'models at another place; looks like an authoring leftover but whether it triggers is UNKNOWN. The three shared splits '
        'have identical IDs, radii, ExtraTime and positions', intent='UNCHANGED_FROM_PC')
    ml = {}
    for name in sorted(set(ps2['marker_lists']) | set(pc['marker_lists'])):
        a, b = ps2['marker_lists'].get(name), pc['marker_lists'].get(name)
        ml[name] = {'ps2': a and a['count'], 'pc': b and b['count'],
                    'identical_ordered_xyz': bool(a and b and a['ordered_xyz_f32_sha256'] == b['ordered_xyz_f32_sha256'])}
    add('TURKEY3:trigger:marker_lists', 'trigger', 'DIFFERENT_LOGIC',
        channels('NONE', 'NONE', 'N_A', 'UNDECIDED'), 'CONFIRMED_BY_BYTES',
        ['src/master_rallye/course_xml.py', 'cdelta1/course-pairs.md'], {'marker_lists': ml},
        'RESEARCHED', 'Limit lists are named differently on PS2 (...Limit2, Boom/StaticCameras); semantic mapping UNKNOWN',
        intent='UNDECIDED')
    ma, mb = ps2['model_references'], pc['model_references']
    diff = {k: [ma.get(k, 0), mb.get(k, 0)] for k in sorted(set(ma) | set(mb)) if ma.get(k, 0) != mb.get(k, 0)}
    add('TURKEY3:checkpoint:model', 'checkpoint', 'DIFFERENT_MATERIAL',
        channels('B_DATA_COPY', 'NONE', 'UNDECIDED', 'N_A'), 'CONFIRMED_BY_BYTES',
        ['cdelta1/checkpoint-survey.md'], {'model_reference_count_diff_ps2_pc': diff},
        'RESEARCHED', 'Checkpoint asset differs (PS2 drum vs PC legacy); knockability owner UNKNOWN')
    return els


def collision_elements(here):
    """Collision elements from the T2 measurements (static; PC and PCSX2 runtime probes still pending)."""
    solid_map = json.loads((here / 'turkey3-ps2-solid-map.json').read_text(encoding='utf-8'))
    columns = json.loads((here / 'gcoll-columns-turkey3.json').read_text(encoding='utf-8'))
    c = solid_map['counts']
    near = columns['exact_match_ground_within_30_of_route']
    far = columns['exact_match_ground_beyond_30_of_route']
    common = {'layer': 'collision', 'evidence': 'STATIC_INFERENCE', 'status': 'RESEARCHED', 'pcsx2_verification': 'REQUIRED_PENDING',
              'gates': []}
    return [
        dict(common, id='TURKEY3:collision:corridor_ground', delta_class='SAME', channels=channels('N_A', 'N_A', 'NONE', 'N_A'),
             sources=['track-delta1/T2-QUERIES.md', 'track-delta1/gcoll-columns-turkey3.json'],
             metrics={'columns_within_30_of_route': near['columns'], 'ps2_matches_pc_within_0.05': near['within_0.05']},
             blocker='Static agreement only; PC and PCSX2 runtime check pending'),
        dict(common, id='TURKEY3:collision:solid_exterior', delta_class='DIFFERENT_LOGIC',
             channels=channels('N_A', 'N_A', 'UNDECIDED', 'UNDECIDED'),
             sources=['track-delta1/T2-SOLID-SHELL.md', 'track-delta1/turkey3-ps2-solid-map.json', 'track-delta1/gcoll-census-36.json'],
             metrics={'pc_ground_cells': c['pc_ground'], 'ps2_solid_at_3_cells': c['solid_at_3'], 'ps2_solid_at_100_cells': c['solid_at_100'],
                      'exact_match_columns_beyond_30': far['columns'], 'ps2_matches_pc_within_0.05_beyond_30': far['within_0.05']},
             blocker='PS2 collision is solid outside the corridor, PC tag100 is open; whether the engine blocks cars there is UNKNOWN until the runtime probes in T2-SOLID-SHELL.md are done; compile of the PS2 tree into PC tag100 needs the tag100 writer (none exists)'),
        dict(common, id='TURKEY3:collision:ps2_only_ground', delta_class='DIFFERENT_LOGIC', channels=channels('N_A', 'N_A', 'UNDECIDED', 'N_A'),
             sources=['track-delta1/T2-QUERIES.md'],
             metrics={'columns_within_30_of_route': columns['non_exact_ground_within_30_of_route']['columns'],
                      'ps2_matches_pc_within_0.05': columns['non_exact_ground_within_30_of_route']['within_0.05'],
                      'columns_beyond_30': columns['non_exact_ground_beyond_30_of_route']['columns'],
                      'ps2_matches_pc_within_0.05_beyond_30': columns['non_exact_ground_beyond_30_of_route']['within_0.05']},
             blocker='PS2-only visual ground has different collision contact heights than PC; confirm with a runtime probe'),
        dict(common, id='TURKEY3:surface:type_ids', layer='surface', delta_class='UNCLASSIFIED', channels=channels('N_A', 'N_A', 'UNDECIDED', 'N_A'),
             sources=['track-delta1/T2-BSP-FORMAT.md'], evidence='UNKNOWN',
             metrics={'bsp_plane_codes': 'not tag103 triangle indices (6 of 41,245 planes match)'},
             blocker='Mapping from BSP plane code to material or $surfacetype not found; PC side surfaces come from $grnd in the TXT sidecar'),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--geometry-report', type=Path, default=ROOT / 'data/geom1/TURKEY3-cli.json')
    ap.add_argument('--ps2-scene', type=Path, default=ROOT / 'data/cdelta1/cache/TNG/DATASCENE/RACETEST/TURKEY3.XML')
    ap.add_argument('--pc-scene', type=Path, required=True)
    ap.add_argument('--sdk', type=Path, required=True)
    ap.add_argument('--pc-dx', type=Path, required=True)
    ap.add_argument('--t1b', type=Path, help='turkey3-t1b.json: replaces the coarse non-puddle geometry elements')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    report = json.loads(args.geometry_report.read_text(encoding='utf-8'))
    sdk, _ = cd.sdk_modules(args.sdk)
    ps2, ps2_rows = cd.parse_scene(args.ps2_scene.read_bytes(), 'ps2', sdk)
    pc, pc_rows = cd.parse_scene(args.pc_scene.read_bytes(), 'pc', sdk)
    geom, exact = geometry_elements(report)
    if args.t1b:
        t1b = json.loads(args.t1b.read_text(encoding='utf-8'))
        keep = [e for e in geom if e['id'] in ('TURKEY3:geometry:puddle', 'TURKEY3:geometry:pc_only')]
        puddle_ground = t1b['summary'].get('puddle')
        for e in keep:
            if e['id'].endswith(':puddle') and puddle_ground:
                e['metrics']['vertical_relation_to_pc_surface'] = puddle_ground
                t = puddle_ground['area_total'] or 1.0
                e['metrics']['area_coverage_percent'] = {
                    'coplanar_pc': round(100 * puddle_ground['area_coplanar_pc'] / t, 1),
                    'near_parallel_pc': round(100 * puddle_ground['area_near_parallel_pc'] / t, 1)}
        geom = keep + t1b_elements(t1b)
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
            'pcsx2_required': True,
            'elements': geom + scene_elements(ps2, pc, ps2_rows, pc_rows) + collision_elements(Path(__file__).resolve().parent)}],
    }
    args.output.write_text(json.dumps(registry, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'elements': len(registry['courses'][0]['elements']), 'exact_ps2_triangles': exact}))


if __name__ == '__main__':
    main()
