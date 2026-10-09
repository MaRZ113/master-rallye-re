"""PC-VISUAL-PILOT1 source fingerprints and read-only F10 correlation.

No output grants a runtime override. No original mesh arrays are exported.
Source mode uses the existing read-only Course SDK; audit mode needs no corpus.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
from trace_common import TARGET_SHA, read_jsonl, guarded_output

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
DX_SHA = 'a6bfcef97684f41154596f91fdfaa9522a8fdf6b65d181f4d1ac327b9caf07d5'
TXT_SHA = 'fbb4153afa20acab9230d33f258384bea1ade94231e4267239b10682f4df0958'
SCHEMA = 'france1-bush01-source-v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def face_hash(points):
    if len(points) != 3 or any(len(p) != 3 for p in points):
        raise ValueError('Expected three XYZ points')
    words = []
    for point in points:
        row = []
        for value in point:
            if not math.isfinite(value):
                raise ValueError('Non-finite source coordinate')
            f = struct.unpack('<f', struct.pack('<f', value))[0]
            if not math.isfinite(f):
                raise ValueError('Non-finite float32 coordinate')
            row.append(struct.unpack('<I', struct.pack('<f', 0.0 if f == 0 else f))[0])
        words.append(tuple(row))
    return sha(b''.join(struct.pack('<3I', *p) for p in sorted(words)))


def multiset_hash(hashes):
    if not hashes or any(not isinstance(h, str) or not re.fullmatch('[0-9a-f]{64}', h) for h in hashes):
        raise ValueError('Expected nonempty lowercase SHA256 face hashes')
    return sha(''.join(sorted(hashes)).encode('ascii'))


def source_signatures(pc_root, sdk_root, ps2_root=None):
    # Import the proved adapter, not another DX parser. Keep the reference tree read-only.
    sys.path.insert(0, str(REPO / 'ps2-research' / 'tools'))
    import geometry_delta as g
    geometry = g.pc_adapter(pc_root, sdk_root, 'FRANCE1')
    if geometry.source['sha256'] != DX_SHA or geometry.source['txt_sha256'] != TXT_SHA:
        raise ValueError('Noncanonical France1 DX/TXT')
    by_group = {}
    for face in geometry.faces:
        by_group.setdefault(face.group, []).append(face_hash(face.points))
    groups = geometry.groups
    target_id = next(k for k, v in groups.items() if v['draw_index'] == 54)
    target = groups[target_id]
    if (target['record_offset'], target['record_path'], target['vertex_base'],
        target['index_start'], target['index_count']) != (3261170, 'course.batch.1.21', 4299, 9792, 144):
        raise ValueError('Compiled target layout mismatch')
    target_hashes = sorted(by_group[target_id])
    if len(target_hashes) != 48 or len(set(target_hashes)) != 24 or set(Counter(target_hashes).values()) != {2}:
        raise ValueError('Compiled target multiplicity differs from TREEBLEND1')
    target_sha = multiset_hash(target_hashes)
    controls = []
    collisions = []
    for gid, metadata in sorted(groups.items(), key=lambda pair: pair[1]['draw_index']):
        hashes = by_group.get(gid, [])
        if not hashes:
            continue
        signature = multiset_hash(hashes)
        if gid != target_id and signature == target_sha:
            collisions.append(metadata['draw_index'])
        if 'bush01-tga' in metadata['textures']:
            controls.append({'draw_index': metadata['draw_index'], 'record_path': metadata['record_path'],
                'triangles': len(hashes), 'unique_unsigned_triangles': len(set(hashes)),
                'geometry_multiset_sha256': signature, 'is_target': gid == target_id})
    if collisions:
        raise ValueError('Ambiguous source geometry identity')
    output = {'schema': SCHEMA, 'course': 'FRANCE1', 'source': geometry.source,
        'target': target, 'target_face_hashes': target_hashes, 'geometry_multiset_sha256': target_sha,
        'unique_face_count': 24, 'source_groups_checked': len(groups), 'whole_geometry_collisions': collisions,
        'same_texture_controls': controls, 'hash_contract': 'Sort XYZ float32 LE uint32 words; normalize -0; sort three points; SHA256 of36bytes. Multiset SHA256 of sorted lowercase face hashes ASCII. Preserve multiplicity; ignore winding.',
        'source_frame': 'GAME_SOURCE', 'runtime_identity': 'NOT_ESTABLISHED',
        'evidence_grade': 'CONFIRMED_BY_BYTES', 'runtime_override_allowed': False}
    ownership = Counter(h for gid, hashes in by_group.items() if gid != target_id for h in hashes if h in set(target_hashes))
    output['target_faces_in_other_france_groups'] = sum(ownership.values())
    turkey = g.pc_adapter(pc_root, sdk_root, 'TURKEY3')
    output['other_course_control'] = {'course': 'TURKEY3', 'source_sha256': turkey.source['sha256'],
        'draws': len(turkey.groups), 'target_face_matches': sum(face_hash(f.points) in set(target_hashes) for f in turkey.faces)}
    if ps2_root:
        import water_runtime as w
        import dressing_runtime as dr
        import tngtool as t
        w.verify_inputs(ps2_root)
        resource = r'\TNG\DATAPSM\COURSE\FRANCE1\FRANCE1.PSM'
        payload, provenance = dr.payload_for(t.load_pak(ps2_root/'TNG.PAK')[0], ps2_root, resource)
        if t.sha(payload) != 'd0b9845218ddd1ff4f12b3b16e77eff43aa182ac73992b5cbea8d81be04f935d':
            raise ValueError('PS2 decoded model identity mismatch')
        scene = w.decode_scene(payload)
        mesh = next(m for m in scene.meshes if m['node_offset'] == 3509209)
        if mesh['material'] != 'bush $alphatest() $clamp(uv) $shader(treeblend)':
            raise ValueError('PS2 target material mismatch')
        triangles, excluded = w.mesh_triangles(scene, mesh)
        ps2_hashes = [face_hash(f) for f in triangles]
        match = w.match_geometry(triangles, [(f.points, 54) for f in geometry.faces if f.group == target_id], geometry.positions, tolerance=.001)
        if len(triangles) != 24 or match['triangle_matches'] != 24:
            raise ValueError('PS2/PC selected face identity mismatch')
        output['ps2_check'] = {'resource': resource, 'provenance': provenance,
            'node_offset': 3509209, 'material': mesh['material'], 'triangles': 24,
            'bitwise_float32_unique_faces_matched': len(set(ps2_hashes) & set(target_hashes)),
            'strict_correspondence': match, 'exclusions': excluded,
            'source_inputs': 'Fresh full canonical SHA256 checks', 'runtime_visibility': 'UNKNOWN'}
    return output


def audit(records, source, observed_course='UNKNOWN'):
    if source.get('schema') != SCHEMA or source.get('course') != 'FRANCE1' or source.get('source', {}).get('sha256') != DX_SHA:
        raise ValueError('Invalid/unsupported source manifest')
    expected = source.get('target_face_hashes')
    if len(expected or []) != 48 or len(set(expected)) != 24 or set(Counter(expected).values()) != {2} or multiset_hash(expected) != source.get('geometry_multiset_sha256'):
        raise ValueError('Invalid target fingerprint')
    headers = [r for r in records if r.get('type') == 'frame_begin']
    endings = [r for r in records if r.get('type') == 'frame_end']
    known = len(headers) == len(endings) == 1 and records[0] is headers[0] and records[-1] is endings[0] and headers[0].get('exe_sha256') == TARGET_SHA
    complete = known and endings[0].get('complete') is True and endings[0].get('truncated') is False and endings[0].get('frame') == headers[0].get('frame')
    target_counts = Counter(expected)
    candidates = []
    reasons = Counter()
    controls = 0
    for draw in records:
        if draw.get('type') != 'draw':
            continue
        probe = draw.get('ps2_foliage_probe')
        if not probe:
            continue
        if probe.get('schema') != 'foliage-probe-v1' or probe.get('override_applied') is not False:
            raise ValueError('Unexpected probe schema/override')
        reasons[probe.get('reason', 'UNKNOWN')] += 1
        hashes = probe.get('face_hashes', [])
        if probe.get('reason') != 'content_captured_identity_pending' or not hashes:
            continue
        args = draw.get('arguments', [])
        if draw.get('method') != 'DrawIndexedPrimitive' or len(args) < 5 or args[0] != 4 or len(hashes) != args[4] or multiset_hash(hashes) != probe.get('geometry_multiset_sha256'):
            raise ValueError('Draw/probe content mismatch')
        if not all(probe.get(key) for key in ('vertex_generation', 'index_generation')):
            raise ValueError('Missing resource creation identity')
        if probe.get('vertex_unlock_hresult') != 0 or probe.get('index_unlock_hresult') != 0:
            raise ValueError('Failed resource unlock')
        counts = Counter(hashes)
        overlap = sum((counts & target_counts).values())
        if not overlap:
            controls += 1
            continue
        full = counts == target_counts
        subset = all(count <= target_counts[h] for h, count in counts.items())
        candidates.append({'sequence': draw.get('sequence'), 'draw_index': draw.get('draw_index'),
            'arguments': args[:5], 'frame': draw.get('frame'), 'draw_hresult': draw.get('result'),
            'relation': 'EXACT_TARGET_CONTENT' if full else 'TARGET_SUBSET' if subset else 'MIXED_TARGET_AND_OTHER_GEOMETRY',
            'matched_triangle_records': overlap, 'native_rs': probe.get('native_rs'), 'native_tss': probe.get('native_tss'),
            'native_world_bits': probe.get('native_world_bits'), 'texture_generation': probe.get('texture_generation'),
            'vertex_generation': probe.get('vertex_generation'), 'index_generation': probe.get('index_generation'),
            'identity': 'UNPROVEN', 'override_allowed': False})
    return {'schema': 'foliage-trace-audit-v1', 'status': 'BLOCKED_ON_DRAW_IDENTITY',
        'identity': 'TARGET_IDENTITY_AMBIGUOUS' if candidates else 'TARGET_IDENTITY_NOT_FOUND',
        'exact_build': bool(known), 'complete_frame': bool(complete),
        'observed_course': observed_course, 'course_evidence': 'USER_RUNTIME_OBSERVATION; NOT INDEPENDENTLY READ FROM ENGINE',
        'content_matches': candidates, 'nonmatching_content_controls': controls,
        'probe_reasons': dict(sorted(reasons.items())), 'runtime_override_allowed': False,
        'limitations': ['Course/resource ownership and upload/revision lifecycle are not yet proved.',
            'F10 content equality is evidence for capture-time geometry only; no persistent activation token.',
            'Missing/unsupported/over-budget probes do not establish absence; transformed or split draws may need another correlation.',
            'Exact float32 content hashes do not perform tolerance matching or infer PS2 visual parity.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    s = commands.add_parser('source')
    s.add_argument('--pc-root', type=Path, required=True)
    s.add_argument('--sdk-root', type=Path, required=True)
    s.add_argument('--ps2-root', type=Path)
    s.add_argument('--output', type=Path, required=True)
    a = commands.add_parser('audit')
    a.add_argument('--source-manifest', type=Path, required=True)
    a.add_argument('--capture', type=Path, required=True)
    a.add_argument('--observed-course', default='UNKNOWN')
    a.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'source':
        result = source_signatures(args.pc_root, args.sdk_root, args.ps2_root)
    else:
        result = audit(read_jsonl(args.capture), json.loads(args.source_manifest.read_text(encoding='utf-8')), args.observed_course)
        result['capture'] = {'name': args.capture.name, 'sha256': file_sha(args.capture)}
    guarded_output(args.output).write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
