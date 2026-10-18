"""TRACK-DELTA1 T1b: classify the non-exact PS2 Turkey3 source groups against PC draws.

Read-only. For every PS2 visual group that has any non-exact triangle:
  * texture family: does PC have a draw that uses the same texture basename?
  * object-like groups: congruent rigid fit (whole group, then edge components)
    against the PC draws of the same texture family (tools/dressing_runtime.py);
  * ground-like groups: vertical relation of each extra triangle to the PC surface under it.
Fits cover only the non-exact faces of a group; candidate PC draws are those with the same texture
basename plus those that exactly matched other faces with that texture. Per-face relations come from geometry_delta.compare (baseline profile).
Fitted transforms are diagnostics, not authored or runtime placements.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dressing_runtime as d  # noqa: E402
import geometry_delta as g  # noqa: E402
from turkey3_delta import categorize  # noqa: E402

GROUND_CELL = 16.0
GAP_COINCIDENT = 0.02
GAP_OVERLAY = 0.5
MIN_COMPONENT = 4
SEARCH_TOLERANCE = .001
SEARCH_BUDGET = 20000
MAX_TARGET_FACES = 60000


def family(textures):
    return {g.texture_key(x) for x in textures if x and x.lower() != 'null' and 'noise' not in x.lower()}


class SurfaceIndex:
    """XZ grid over PC faces for 'what surface is under this point' queries."""

    def __init__(self, faces):
        self.grid = defaultdict(list)
        for f in faces:
            xs = [p[0] for p in f.points]
            zs = [p[2] for p in f.points]
            x0, x1 = int(min(xs) // GROUND_CELL), int(max(xs) // GROUND_CELL)
            z0, z1 = int(min(zs) // GROUND_CELL), int(max(zs) // GROUND_CELL)
            for cx in range(x0, x1 + 1):
                for cz in range(z0, z1 + 1):
                    self.grid[cx, cz].append(f)

    @staticmethod
    def height_at(f, x, z):
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = f.points
        den = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
        if abs(den) < 1e-9:
            return None
        l1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / den
        l2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / den
        l3 = 1 - l1 - l2
        if min(l1, l2, l3) < -1e-6:
            return None
        return l1 * ay + l2 * by + l3 * cy

    def heights(self, x, z):
        return [h for f in self.grid.get((int(x // GROUND_CELL), int(z // GROUND_CELL)), ())
                if (h := self.height_at(f, x, z)) is not None]


def ground_relation(face, index):
    cx = sum(p[0] for p in face.points) / 3
    cy = sum(p[1] for p in face.points) / 3
    cz = sum(p[2] for p in face.points) / 3
    hs = index.heights(cx, cz)
    if not hs:
        return 'NO_PC_SURFACE_UNDER'
    gap = min((cy - h for h in hs), key=abs)
    if abs(gap) <= GAP_COINCIDENT:
        return 'COINCIDENT_WITH_PC_SURFACE'
    if 0 < gap <= GAP_OVERLAY:
        return 'OVERLAY_ABOVE_PC_SURFACE'
    if -GAP_OVERLAY <= gap < 0:
        return 'SLIGHTLY_BELOW_PC_SURFACE'
    return 'FAR_ABOVE_PC_SURFACE' if gap > 0 else 'FAR_BELOW_PC_SURFACE'


def fit(faces, target):
    """Whole-group rigid fit, then per edge component. Returns a compact verdict."""
    if len(faces) < MIN_COMPONENT:
        return {'verdict': 'TOO_SMALL_TO_FIT', 'faces': len(faces)}
    if len(target) > MAX_TARGET_FACES:
        return {'verdict': 'TARGET_TOO_LARGE', 'target_faces': len(target)}
    try:
        whole = d.rigid_shape_search(faces, target, tolerance=SEARCH_TOLERANCE, budget=SEARCH_BUDGET)
    except g.t.FormatError:
        return {'verdict': 'BUDGET_EXCEEDED', 'faces': len(faces)}
    if whole['matches']:
        m = whole['matches'][0]
        return {'verdict': 'WHOLE_GROUP_CONGRUENT', 'faces': len(faces), 'fits': len(whole['matches']),
                'target_draws': m['target_groups'][:4], 'residual': m['maximum_vertex_residual']}
    fitted = total = 0
    for ids in d.components(faces):
        comp = [faces[i] for i in ids]
        if len(comp) < MIN_COMPONENT:
            continue
        total += len(comp)
        try:
            r = d.rigid_shape_search(comp, target, tolerance=SEARCH_TOLERANCE, budget=SEARCH_BUDGET)
        except g.t.FormatError:
            continue
        if r['matches']:
            fitted += len(comp)
    if fitted:
        return {'verdict': 'COMPONENTS_CONGRUENT', 'faces': len(faces), 'fitted_faces': fitted, 'component_faces': total}
    return {'verdict': 'NO_CONGRUENT_FIT', 'faces': len(faces)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, required=True)
    ap.add_argument('--pc-root', type=Path, required=True)
    ap.add_argument('--sdk', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    a, b, _ = g.load_pair(args.ps2_root, args.pc_root, args.sdk, 'TURKEY3')
    _, forward, _ = g.compare(a, b)  # same baseline profile as the GEOM1 report
    relation_by_group = defaultdict(Counter)
    face_relation = {}
    exact_peers = defaultdict(set)  # PS2 texture key -> PC draws that exactly matched faces with that texture
    for r in forward:
        relation_by_group[r['group']][r['geometry_relation']] += 1
        face_relation[r['source']] = r['geometry_relation']
        if r['geometry_relation'] == 'EXACT_TRIANGLE_MATCH':
            for key in family(a.groups[r['group']]['textures']):
                exact_peers[key].update(r['other_groups'])
    pc_by_family = defaultdict(set)
    for gid, v in b.groups.items():
        for key in family(v['textures']):
            pc_by_family[key].add(gid)
    faces_by_group = defaultdict(list)
    for f in a.faces:
        faces_by_group[f.group].append(f)
    pc_faces_by_group = defaultdict(list)
    for f in b.faces:
        pc_faces_by_group[f.group].append(f)
    surface = SurfaceIndex(b.faces)
    rows = []
    for gid, rels in sorted(relation_by_group.items()):
        nonexact = sum(n for r, n in rels.items() if r != 'EXACT_TRIANGLE_MATCH')
        if not nonexact:
            continue
        info = a.groups[gid]
        cat = categorize(info['material'])
        keys = family(info['textures'])
        same_texture = {x for k in keys for x in pc_by_family.get(k, ())}
        peers = {x for k in keys for x in exact_peers.get(k, ())}
        pc_groups = sorted(same_texture | peers)
        all_faces = faces_by_group[gid]
        faces = [f for f in all_faces if face_relation.get(f.identifier) != 'EXACT_TRIANGLE_MATCH']
        row = {'category': cat, 'node_offset': info['node_offset'], 'material': re.sub(r'\s+', ' ', info['material'])[:90],
               'textures': sorted(keys), 'faces': len(faces), 'group_faces': len(all_faces), 'non_exact': nonexact,
               'exact_peer_textures': sorted({t for x in peers for t in family(b.groups[x]['textures'])}),
               'relations': dict(sorted(rels.items())),
               'pc_texture_family_draws': len(pc_groups)}
        if cat in ('ground', 'puddle', 'other'):
            counts = Counter(ground_relation(f, surface) for f in faces)
            row['ground_relation'] = dict(sorted(counts.items()))
        else:
            if not pc_groups:
                row['fit'] = {'verdict': 'NO_PC_TEXTURE_FAMILY'}
            else:
                target = [f for gid2 in pc_groups for f in pc_faces_by_group[gid2]]
                row['fit'] = fit(faces, target)
        rows.append(row)
    summary = defaultdict(lambda: defaultdict(int))
    for r in rows:
        cat = r['category']
        if 'fit' in r:
            summary[cat][r['fit']['verdict'] + '_faces'] += r['faces']
            summary[cat][r['fit']['verdict'] + '_groups'] += 1
        if 'ground_relation' in r:
            for k, v in r['ground_relation'].items():
                summary[cat][k] += v
    out = {'schema': 1, 'course': 'TURKEY3',
           'method': {'fit_tolerance': SEARCH_TOLERANCE, 'fit_budget': SEARCH_BUDGET, 'min_component_faces': MIN_COMPONENT,
                      'ground_cell': GROUND_CELL, 'coincident_gap': GAP_COINCIDENT, 'overlay_gap': GAP_OVERLAY},
           'limitations': ['Fits are diagnostics, not authored or runtime transforms',
                           'A failed fit is not proof of absence (changed topology is not searched)',
                           'Ground relation uses face centroids against PC faces under the same XZ'],
           'summary': {k: dict(sorted(v.items())) for k, v in sorted(summary.items())}, 'groups': rows}
    args.output.write_text(json.dumps(out, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(out['summary'], indent=1))


if __name__ == '__main__':
    main()
