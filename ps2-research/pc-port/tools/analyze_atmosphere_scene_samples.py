"""Compare bounded runtime source samples with exact original DX course arrays.

This produces diagnostic evidence only, never an admission rule or new atlas.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from master_rallye.dx_course import parse_course_dx
from master_rallye.dxt import parse_dxt


def corners(model, draw):
    result = []
    for index in model.local_indices[draw.index_start:draw.index_start + draw.index_count]:
        v = draw.vertex_base + index
        result.append(struct.pack('<3f', *model.vertices.positions[v]) +
                      model.vertices.colors[v * 4:v * 4 + 4] +
                      struct.pack('<2f', *model.uv_sets[0].values[v]))
    return result


def triangles(values):
    if len(values) % 3:
        raise ValueError('incomplete triangle')
    return Counter(tuple(sorted(values[i:i + 3])) for i in range(0, len(values), 3))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    models = {}
    reports = []
    for line in args.session.read_text(encoding='utf-8').splitlines():
        sample = json.loads(line)
        if sample.get('type') != 'atmosphere_scene_source_sample':
            continue
        course = sample['course']
        if course not in ('France1', 'Turkey2', 'Turkey3'):
            raise ValueError('unexpected course')
        if course not in models:
            folder = args.source / course
            model = parse_course_dx(folder / (course.lower() + '.dx'))
            if not model.course_render_validated:
                raise ValueError('source draw validation failed')
            textures = defaultdict(list)
            for draw in model.physical_draws:
                if draw.index_count:
                    textures[draw.texture_tuple[0]].append(draw)
            materials = {}
            for name, draws in textures.items():
                path = folder / (name + '.dxt')
                if not path.exists():
                    continue
                tex = parse_dxt(path)
                opaque = bytearray(tex.bgra)
                opaque[3::4] = bytes([255]) * (len(opaque) // 4)
                for pixels in (tex.bgra, opaque):
                    materials[hashlib.sha256(pixels).hexdigest()] = (name, draws)
            models[course] = model, materials
        model, materials = models[course]
        raw = bytes.fromhex(sample['expanded_corners_hex'])
        if len(raw) != sample['triangles'] * 72 or hashlib.sha256(raw).hexdigest() != sample['geometry_sha256']:
            raise ValueError('runtime sample hash/length mismatch')
        live = [raw[i:i + 24] for i in range(0, len(raw), 24)]
        material = materials.get(sample['texture_sha256'])
        row = {k: sample[k] for k in ('course', 'texture_sha256', 'geometry_sha256', 'triangles', 'vertices', 'frame')}
        if not material:
            row['status'] = 'UNKNOWN_SOURCE_TEXTURE'
            reports.append(row)
            continue
        name, draws = material
        values = [corners(model, draw) for draw in draws]
        source_corners = {v for draw in values for v in draw}
        position_map = defaultdict(set)
        for v in source_corners:
            position_map[v[:12]].add(v)
        live_triangles = triangles(live)
        source_triangles = Counter()
        for draw in values:
            # Presence only: repetitions across source records do not create
            # evidence for duplicates in one runtime batch.
            source_triangles |= triangles(draw)
        exact = sum(v in source_corners for v in live)
        positions = sum(v[:12] in position_map for v in live)
        row.update(material=name, exact_corners=exact, position_corners=positions,
                   total_corners=len(live),
                   exact_source_triangles=sum((live_triangles & source_triangles).values()),
                   whole_record_reordered_matches=[d.record_path for d, v in zip(draws, values) if triangles(v) == live_triangles],
                   source_records=[d.record_path for d, v in zip(draws, values) if not (live_triangles - triangles(v))])
        row['component_differences'] = [
            {'live_xyz': struct.unpack('<3f', v[:12]), 'live_bgra': v[12:16].hex(), 'live_uv': struct.unpack('<2f', v[16:]),
             'source_at_same_xyz': [{'bgra': w[12:16].hex(), 'uv': struct.unpack('<2f', w[16:])} for w in sorted(position_map[v[:12]])[:6]]}
            for v in live if v not in source_corners and v[:12] in position_map][:4]
        row['status'] = 'EXACT_CORNERS' if exact == len(live) else 'SOURCE_COMPONENT_MISMATCH'
        reports.append(row)
    result = {'schema': 1, 'evidence': 'READ_ONLY_RUNTIME_VS_ORIGINAL_SOURCE_COMPARISON',
              'session_sha256': hashlib.sha256(args.session.read_bytes()).hexdigest(), 'samples': reports}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f'{len(reports)} samples: {args.output}')


if __name__ == '__main__':
    main()
