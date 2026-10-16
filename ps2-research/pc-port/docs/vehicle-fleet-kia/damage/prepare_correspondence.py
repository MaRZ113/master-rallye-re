"""Pinned Kia source-only index correspondence; no runtime deformation grant."""
from pathlib import Path
import collections
import hashlib
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
sys.path.insert(0, str(ROOT.parent / 'master-rallye-re-course/src'))
from master_rallye.dx import parse_dx


def sha(data):
    return hashlib.sha256(data).hexdigest()


def key(point):
    return struct.pack('<3f', *(0.0 if v == 0 else v for v in point))


def main():
    source = PORT / 'docs/vehicle-continuity2/fleet-car/race-profiles.json'
    profile = next(p for p in json.loads(source.read_text())['profiles'] if p['family'] == 'KiaSportage')
    pc_path = ROOT.parent / 'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/KiaSportage/car.dx'
    asset_path = PORT / '.assets/vehicles' / profile['filename']
    assert sha(pc_path.read_bytes()) == profile['original_pc_source_sha256']
    asset = asset_path.read_bytes()
    assert sha(asset) == profile['sha256']
    pc = parse_dx(pc_path)
    by_path = {d.record_path: d for d in pc.physical_draws}
    native = collections.defaultdict(list)
    tolerance = 0.00001
    original_points = []
    certificates = []
    native_faces = []
    for slot, source in enumerate(profile['pc_sources']):
        draw = by_path[source['record_path']]
        points = pc.vertices.positions[draw.vertex_base:draw.vertex_base + source['vertices']]
        assert sha(b''.join(struct.pack('<3f', *p) for p in points)) == source['ordered_position_sha256']
        original_points.append(points)
        raw_ids = [i - draw.vertex_base for i in pc.draw_global_indices(draw)]
        for face in range(0, len(raw_ids), 3):
            native_faces.append((slot, face // 3, raw_ids[face:face + 3]))
        for i, point in enumerate(points):
            native[key(point)].append([slot, i])
        certificates.append({k: source[k] for k in ('record_path', 'vertices', 'faces',
            'ordered_position_sha256', 'native_uv_winding_sha256', 'geometry_sha256')})
    _, version, metadata, meshes, vertices, indices, textures, _ = struct.unpack_from('<8s6I32s', asset)
    assert version == 2
    at = 64 + metadata
    mesh_rows = [struct.unpack_from('<7I', asset, at + i * 28) for i in range(meshes)]
    at += meshes * 28
    points = [struct.unpack_from('<3f', asset, at + i * 36) for i in range(vertices)]
    at += vertices * 36
    ids = struct.unpack_from('<' + 'I' * indices, asset, at)
    referenced = sorted(set(ids))
    mapping = []
    unmatched = []
    for vertex in referenced:
        candidates = native.get(key(points[vertex]), [])
        if not candidates:
            candidates = [[slot, i] for slot, values in enumerate(original_points)
                          for i, point in enumerate(values)
                          if max(abs(point[j] - points[vertex][j]) for j in range(3)) <= tolerance]
        mapping.append(dict(vertex=vertex, candidates=candidates))
        if not candidates:
            unmatched.append(vertex)
    summary_meshes = []
    body_unmatched = []
    candidates_by_vertex = {m['vertex']: {tuple(p) for p in m['candidates']} for m in mapping}
    for i, row in enumerate(mesh_rows):
        used = sorted(set(ids[row[5]:row[5] + row[6]]))
        missing = [v for v in used if v in unmatched]
        if i not in (17, 18, 19):
            for vertex in missing:
                distance, slot, native_vertex = min(
                    (max(abs(point[j] - points[vertex][j]) for j in range(3)), slot, index)
                    for slot, values in enumerate(original_points) for index, point in enumerate(values))
                body_unmatched.append(dict(mesh=i, vertex=vertex,
                    nearest_distance_for_diagnosis_only=distance,
                    nearest_source_slot_for_diagnosis_only=slot,
                    nearest_native_vertex_for_diagnosis_only=native_vertex,
                    mapping_authorized=False))
        summary_meshes.append(dict(mesh=i, node=row[0], mode=row[1], faces=row[6] // 3,
                                   referenced_vertices=len(used), unmatched_vertices=missing))
    # Diagnostic topology evidence for small authored revisions. Do not promote
    # a nearest point to an authorized candidate: require two already mapped
    # neighboring vertices to identify the original native source triangle.
    for diagnostic in body_unmatched:
        vertex = diagnostic['vertex']
        row = mesh_rows[diagnostic['mesh']]
        proofs = []
        for first in range(row[5], row[5] + row[6], 3):
            tri = ids[first:first + 3]
            if vertex not in tri or tri.count(vertex) != 1:
                continue
            other = [v for v in tri if v != vertex]
            if len(other) != 2 or not all(candidates_by_vertex[v] for v in other):
                continue
            for slot, face, native_tri in native_faces:
                for corner in range(3):
                    remain = [native_tri[k] for k in range(3) if k != corner]
                    if (((slot, remain[0]) in candidates_by_vertex[other[0]] and
                         (slot, remain[1]) in candidates_by_vertex[other[1]]) or
                        ((slot, remain[1]) in candidates_by_vertex[other[0]] and
                         (slot, remain[0]) in candidates_by_vertex[other[1]])):
                        candidate = native_tri[corner]
                        distance = max(abs(original_points[slot][candidate][j] - points[vertex][j]) for j in range(3))
                        if distance <= 0.005:
                            proofs.append(dict(ps2_face=(first - row[5]) // 3,
                                native_source_slot=slot, native_face=face,
                                candidate_vertex=candidate, position_difference=distance))
        diagnostic['adjacent_triangle_proofs'] = proofs
    by_vertex = {m['vertex']: m for m in mapping}
    for diagnostic in body_unmatched:
        proofs = diagnostic['adjacent_triangle_proofs']
        if proofs:
            row = by_vertex[diagnostic['vertex']]
            row['candidates'] = [list(p) for p in sorted({
                (proof['native_source_slot'], proof['candidate_vertex']) for proof in proofs})]
            row['source_rule'] = 'TWO_VERIFIED_NEIGHBORS_IDENTIFY_ORIGINAL_NATIVE_TRIANGLE'
    static_vertices = sorted({v for m in summary_meshes if m['mesh'] in (17, 18, 19)
                              for v in m['unmatched_vertices']})
    pending = [m['vertex'] for m in mapping if not m['candidates'] and m['vertex'] not in static_vertices]
    assert not pending
    header = ['#pragma once', '#include <cstdint>',
        '// Kia ORIGINAL SOURCE INDICES ONLY. No original position/UV/texture bytes.',
        '// Source correspondence only; verified healthy/current native references mandatory.',
        'namespace gfx2::ps2port::kia_damage_draft {',
        'struct Candidate { uint16_t slot,vertex; };',
        'struct Mapping { uint32_t vertex,first,count; };']
    candidates = []
    rows = []
    for m in mapping:
        rows.append((m['vertex'], len(candidates), len(m['candidates'])))
        candidates.extend(m['candidates'])
    header.append('inline constexpr Candidate candidates[]={'+','.join('{%su,%su}' % tuple(p) for p in candidates)+'};')
    header.append('inline constexpr Mapping mapping[]={'+','.join('{%su,%su,%su}' % p for p in rows)+'};')
    header.append('inline constexpr uint32_t static_source_vertices[]={'+','.join(str(v)+'u' for v in static_vertices)+'};')
    header.append('}')
    (HERE / 'kia_damage_draft.hpp').write_text('\n'.join(header)+'\n')
    output = dict(schema=1, family='KiaSportage', original_pc_sha256=profile['original_pc_source_sha256'],
        original_ps2_sha256=profile['original_ps2_source_sha256'], private_asset_sha256=profile['sha256'],
        source_profiles=certificates, meshes=summary_meshes, mapping=mapping,
        asset_vertex_count=vertices,
        unused_asset_vertices=sorted(set(range(vertices)) - set(referenced)),
        referenced_vertices=len(referenced), mapped_vertices=len(referenced) - len(unmatched),
        source_correspondence_tolerance=tolerance,
        body_unmatched_diagnostics=body_unmatched,
        topology_proved_additional_vertices=len(body_unmatched),
        static_unmatched_crew_interior_vertices=static_vertices,
        static_unmatched_roots=[17, 18, 19],
        unresolved_body_vertices=pending,
        unmatched_vertices=unmatched,
        runtime_policy='EXACT_INDEX_ONLY; VERIFIED_HEALTHY_REFERENCES_REQUIRED; CURRENT_ALL26_OWNER_UV_WINDING; ALL_CANDIDATE_DELTAS_AGREE; UNMAPPED_NOT_AUTHORIZED',
        runtime_grant=False)
    (HERE / 'kia-source-correspondence.json').write_text(json.dumps(output, indent=2) + '\n')
    print('Source-tolerance mapped', output['mapped_vertices'], '/', len(referenced))
    print('Unmatched per mesh', [(m['mesh'], len(m['unmatched_vertices'])) for m in summary_meshes])


if __name__ == '__main__':
    main()
