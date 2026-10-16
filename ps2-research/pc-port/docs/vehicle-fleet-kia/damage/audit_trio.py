"""Strict read-only FDCAR001 Kia native damage cohort audit."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import struct

HERE = Path(__file__).resolve().parent
EXE = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def integer(row, key, minimum=0, maximum=0xffffffff):
    value = row[key]
    require(type(value) is int and minimum <= value <= maximum, 'Invalid integer ' + key)
    return value


def unique_json(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_bytes(data):
    require(len(data) >= 16 and data[:8] == b'FDCAR001', 'Invalid capture header')
    metadata_size, raw_size = struct.unpack_from('<II', data, 8)
    require(0 < metadata_size <= 32768 and raw_size <= 512 * 1024, 'Capture exceeds bounded format')
    require(len(data) == 16 + metadata_size + raw_size, 'Truncated or trailing capture bytes')
    metadata = json.loads(data[16:16 + metadata_size].decode('utf-8'),
                          object_pairs_hook=unique_json,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    require(integer(metadata, 'schema') == 1 and metadata['family'] == 'KiaSportage', 'Wrong schema/family')
    require(metadata['exe_sha256'] == EXE, 'Wrong original executable')
    require(re.fullmatch('[0-9a-f]{64}', metadata['proxy_sha256']) is not None, 'Invalid proxy SHA')
    for key in ('instance', 'packet', 'model'):
        pointer = integer(metadata, key, 0x10000, 0x7ffffffc)
        require(pointer % 4 == 0, 'Unaligned current owner pointer')
    integer(metadata, 'frame', maximum=0xffffffffffffffff)
    require(type(metadata['private_tree']) is bool, 'Invalid tree selector')
    require(re.fullmatch('[0-9a-f]{128}', metadata['world_le_hex']) is not None, 'Invalid WORLD bytes')
    require(all(math.isfinite(v) for v in struct.unpack('<16f', bytes.fromhex(metadata['world_le_hex']))), 'Nonfinite WORLD')
    require(isinstance(metadata['records'], list) and 0 < len(metadata['records']) <= 64, 'Invalid record count')
    raw = data[16 + metadata_size:]
    cursor = 0
    seen_meshes, seen_nodes = set(), set()
    records = []
    for record in metadata['records']:
        row = dict(record)
        node = integer(row, 'node', maximum=63)
        mesh = integer(row, 'mesh', 0x10000, 0x7ffffffc)
        require(mesh % 4 == 0 and mesh not in seen_meshes and node not in seen_nodes, 'Duplicate/unaligned leaf')
        seen_meshes.add(mesh)
        seen_nodes.add(node)
        require(integer(row, 'material_vector', 0x10000, 0x7ffffffc) % 4 == 0,
                'Invalid material-vector pointer')
        # Clone evidence proves the vector OBJECT pointer is retained. Its
        # first word is only an exact identity token here; do not infer a
        # pointer/handle type without proving the material consumer contract.
        integer(row, 'material')
        fvf, stride = integer(row, 'fvf'), integer(row, 'stride')
        uv_offset = {0x142: (24, 16), 0x152: (36, 28), 0x112: (32, 24)}
        require(fvf in uv_offset and stride == uv_offset[fvf][0], 'Unsupported vertex layout')
        uv_at = uv_offset[fvf][1]
        vertices = integer(row, 'vertices', 1, 8192)
        triangles = integer(row, 'triangles', 1, 8192)
        minimum = integer(row, 'min')
        width = {101: 2, 102: 4}.get(integer(row, 'index_format'))
        require(width is not None, 'Unsupported index format')
        for key in ('vb_generation', 'ib_generation', 'vb_revision', 'ib_revision'):
            integer(row, key, 1, 0xffffffffffffffff)
        require(integer(row, 'offset') == cursor, 'Noncontiguous/overlapping source ranges')
        vertex_bytes = integer(row, 'vertex_bytes')
        index_bytes = integer(row, 'index_bytes')
        require(vertex_bytes == vertices * stride and index_bytes == triangles * 3 * width, 'Invalid byte counts')
        require(cursor + vertex_bytes + index_bytes <= len(raw), 'Source range outside capture')
        vb = raw[cursor:cursor + vertex_bytes]
        ib = raw[cursor + vertex_bytes:cursor + vertex_bytes + index_bytes]
        cursor += vertex_bytes + index_bytes
        xyz, uv, positions = bytearray(), bytearray(), []
        for vertex in range(vertices):
            point = struct.unpack_from('<3f', vb, vertex * stride)
            coords = struct.unpack_from('<2f', vb, vertex * stride + uv_at)
            require(all(math.isfinite(v) for v in point + coords), 'Nonfinite position/UV')
            positions.append(point)
            xyz.extend(vb[vertex * stride:vertex * stride + 12])
            uv.extend(vb[vertex * stride + uv_at:vertex * stride + uv_at + 8])
        normalized = []
        for at in range(0, len(ib), width):
            index = int.from_bytes(ib[at:at + width], 'little')
            require(minimum <= index < minimum + vertices, 'Index outside native source range')
            normalized.append(index - minimum)
        row.update(positions=positions, ordered_xyz=sha(xyz),
                   uv_winding=sha(uv + struct.pack('<' + 'I' * len(normalized), *normalized)))
        records.append(row)
    require(cursor == len(raw), 'Unclaimed raw capture bytes')
    return metadata, records


def read_capture(path):
    match = re.fullmatch(r'fleet-damage-(\d+)-d(\d+)-f(\d+)\.bin', path.name)
    require(match is not None, 'Capture filename lacks process/device/frame identity')
    data = path.read_bytes()
    metadata, records = parse_bytes(data)
    require(metadata['frame'] == int(match[3]), 'Filename/frame mismatch')
    return dict(path=path.name, sha256=sha(data), process=int(match[1]), device=int(match[2]),
                metadata=metadata, records=records)


def join_sources(capture, profiles, healthy=None):
    result = []
    used = set()
    for slot, profile in enumerate(profiles):
        matching = [r for r in capture['records'] if
                    r['vertices'] == profile['vertices'] and r['triangles'] == profile['faces'] and
                    r['uv_winding'] == profile['native_uv_winding_sha256'] and
                    (r['ordered_xyz'] == profile['ordered_position_sha256'] if healthy is None else
                     r['material_vector'] == healthy[slot]['material_vector'] and
                     r['material'] == healthy[slot]['material'])]
        # Original material objects can be shared across different source
        # records. Resolve that ambiguity only with the exact unchanged
        # healthy ordered XYZ certificate, never root order or proximity.
        if healthy is not None and len(matching) > 1:
            matching = [r for r in matching if r['ordered_xyz'] == profile['ordered_position_sha256']]
        require(len(matching) == 1, 'Missing/ambiguous source slot ' + str(slot))
        row = matching[0]
        require(row['mesh'] not in used, 'One native leaf joined to multiple sources')
        used.add(row['mesh'])
        result.append(row)
    return result


def delta_consensus(mapping, static, healthy, current, epsilon=1e-6):
    disagreement = []
    moved = 0
    max_delta = 0.0
    for row in mapping:
        candidates = row['candidates']
        if not candidates:
            require(row['vertex'] in static, 'Unmapped private body vertex')
            continue
        deltas = [tuple(current[slot]['positions'][index][axis] - healthy[slot]['positions'][index][axis]
                        for axis in range(3)) for slot, index in candidates]
        require(all(math.isfinite(v) for d in deltas for v in d), 'Nonfinite deformation delta')
        difference = max(abs(d[axis] - deltas[0][axis]) for d in deltas for axis in range(3))
        if difference > epsilon:
            disagreement.append(dict(vertex=row['vertex'], candidate_count=len(candidates), maximum_difference=difference))
        magnitude = max(abs(v) for v in deltas[0])
        moved += magnitude > epsilon
        max_delta = max(max_delta, magnitude)
    return dict(mapped_private_vertices=len(mapping) - len(static), static_original_ps2_vertices=len(static),
                moved_private_vertices=moved, maximum_delta=max_delta,
                disagreement=disagreement, agreement_pass=not disagreement)


def audit(paths):
    require(len(paths) == 3, 'Exactly healthy/damaged/further-damaged captures required')
    data = json.loads((HERE / 'kia-source-correspondence.json').read_text())
    captures = [read_capture(Path(path)) for path in paths]
    first = captures[0]
    require(not first['metadata']['private_tree'], 'Healthy reference must use original native tree')
    healthy = join_sources(first, data['source_profiles'])
    report = []
    previous = -1
    for capture in captures:
        metadata = capture['metadata']
        require(metadata['frame'] > previous, 'Capture frames must increase')
        previous = metadata['frame']
        for key in ('process', 'device'):
            require(capture[key] == first[key], 'Different process/device: ' + key)
        for key in ('instance', 'packet', 'model', 'exe_sha256', 'proxy_sha256'):
            require(metadata[key] == first['metadata'][key], 'Changed owner/build identity: ' + key)
        joined = healthy if capture is first else join_sources(capture, data['source_profiles'], healthy)
        changed = [i for i, row in enumerate(joined) if row['ordered_xyz'] != data['source_profiles'][i]['ordered_position_sha256']]
        require(not changed or metadata['private_tree'], 'Deformed positions without selected private tree')
        consensus = delta_consensus(data['mapping'], set(data['static_unmatched_crew_interior_vertices']), healthy, joined)
        report.append(dict(path=capture['path'], sha256=capture['sha256'], frame=metadata['frame'],
            private_tree=metadata['private_tree'], current_sources_verified=len(joined), changed_sources=changed,
            source_nodes_diagnostic_only=[row['node'] for row in joined],
            ordered_uv_winding_and_material_identity=True, **consensus))
    deformation_observed = any(r['changed_sources'] for r in report[1:])
    return dict(schema=1, family='KiaSportage', same_process_current_owner=True,
        observed_only=True, implementation_authorized=False, captures=report,
        damage_deformation_observed=deformation_observed,
        correspondence_pass=all(r['agreement_pass'] for r in report),
        limitations=['No native damaged normal reconstruction', 'Static source PS2 crew/interior retained',
                     'Captured frames do not prove every possible native damage state'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', nargs=3, type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.captures)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Correspondence', 'PASS' if result['correspondence_pass'] else 'FAIL')


if __name__ == '__main__':
    main()
