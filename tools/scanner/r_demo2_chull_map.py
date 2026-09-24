"""Read-only same-build GXM $chull -> regenerated demo DX tag101 comparison."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from master_rallye.demo_dx import inspect_demo_dx
from master_rallye.gxm import (parse_gxm_geometry_prefix_bytes,
                                parse_gxm_prefix_bytes,
                                parse_gxm_triangle_prefix_bytes)
from master_rallye.sidecar import parse_sidecar
try:
    from tools.scanner.r_demo_collision_compare import hull_vertex_ids
except ModuleNotFoundError:  # direct script execution
    from r_demo_collision_compare import hull_vertex_ids

ROOT = Path(__file__).resolve().parents[2] / '.research-output' / 'r-demo2'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mapping_report(gxm: bytes, sidecar_path: Path, dx: bytes,
                   directive: str = '$chull(Trooper)') -> dict:
    prefix = parse_gxm_prefix_bytes(gxm, 'source GXM')
    geometry = parse_gxm_geometry_prefix_bytes(gxm, prefix)
    records = parse_gxm_triangle_prefix_bytes(gxm, prefix, geometry)
    sidecar = parse_sidecar(sidecar_path)
    meshes = [mesh for mesh in sidecar.meshes if mesh.name == directive]
    if len(meshes) != 1 or sidecar.mesh_span != records.record_count:
        raise ValueError('one exact sidecar hull and matching record span are required')
    mesh = meshes[0]
    if mesh.index < 0 or mesh.size <= 0 or mesh.index + mesh.size > records.record_count:
        raise ValueError('hull record range outside GXM')
    triples = []
    for i in range(mesh.index, mesh.index + mesh.size):
        words = struct.unpack_from('<10I', gxm, records.record_offset + i * 52)
        triples.append(tuple(words[4:7]))
    source_ids = sorted({index for triple in triples for index in triple})
    source = {}
    for index in source_ids:
        x, y, z = struct.unpack_from('<3f', gxm, records.vector_c_offset + index * 12)
        source[index] = (x, z, -y)
    points = [source[index] for index in source_ids]
    convex_local_ids = hull_vertex_ids(points)
    convex_ids = [source_ids[i] for i in sorted(convex_local_ids)]
    convex = [source[index] for index in convex_ids]
    parsed = inspect_demo_dx(dx, 'regenerated demo DX')
    tag = parsed.collision.convex_hull
    if tag is None or not convex:
        raise ValueError('regenerated DX has no tag101 B or source hull is empty')
    target = tag.representation_b.geometry_a.vertices
    if len(target) != len(convex):
        raise ValueError('source convex and target B vertex counts differ')
    nearest = [min(convex_ids, key=lambda index: math.dist(point, source[index]))
               for point in target]
    errors = [math.dist(point, source[index]) for point, index in zip(target, nearest)]
    if len(set(nearest)) != len(target):
        raise ValueError('source-to-B nearest mapping is not bijective')
    target_triples = {tuple(sorted(nearest[i] for i in face))
                      for face in tag.representation_b.geometry_a.triangles}
    source_triples = {tuple(sorted(face)) for face in triples}
    source_extrema = [[min(point[axis] for point in points), max(point[axis] for point in points)]
                      for axis in range(3)]
    box = tag.representation_a.geometry_a.vertices
    box_extrema = [[min(point[axis] for point in box), max(point[axis] for point in box)]
                   for axis in range(3)]
    box_radius = max(math.dist(tag.base_geometry.vertices[0], point) for point in box)
    return {'source_gxm_sha256': digest(gxm), 'target_dx_sha256': digest(dx),
            'directive': directive, 'source_record_start': mesh.index,
            'source_record_count': mesh.size, 'source_unique_position_count': len(source_ids),
            'source_convex_vertex_count': len(convex),
            'target_tag101_b_vertex_count': len(target),
            'target_tag101_b_triangle_count': len(target_triples),
            'max_mapped_vertex_distance': max(errors),
            'source_triangle_count': len(source_triples),
            'source_target_triangle_overlap': len(source_triples & target_triples),
            'source_extrema_xyz': source_extrema,
            'tag101_a_extrema_xyz': box_extrema,
            'max_aabb_axis_difference': max(abs(a-b) for x,y in zip(source_extrema, box_extrema)
                                            for a,b in zip(x,y)),
            'tag101_base_scalar': tag.base_scalar,
            'aabb_corner_radius': box_radius,
            'aabb_corner_radius_difference': abs(tag.base_scalar-box_radius),
            'status': 'SAME_BUILD_NUMERIC_MAPPING; runtime collision mutation unproven'}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--gxm', type=Path, required=True)
    ap.add_argument('--sidecar', type=Path, required=True)
    ap.add_argument('--regenerated-dx', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    gxm = args.gxm.resolve(strict=True)
    sidecar = args.sidecar.resolve(strict=True)
    target = args.regenerated_dx.resolve(strict=True)
    output = args.output.resolve()
    if gxm.parent != sidecar.parent or ROOT.resolve() not in output.parents or output.suffix.lower() != '.json':
        ap.error('sidecar must be a sibling of GXM; output must be ignored R-DEMO2 JSON')
    report = mapping_report(gxm.read_bytes(), sidecar, target.read_bytes())
    report.update({'source_gxm': str(gxm), 'source_sidecar': str(sidecar),
                   'target_regenerated_dx': str(target)})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('source_convex_vertex_count',
                                                  'target_tag101_b_vertex_count',
                                                  'max_mapped_vertex_distance',
                                                  'source_target_triangle_overlap')}))


if __name__ == '__main__':
    main()
