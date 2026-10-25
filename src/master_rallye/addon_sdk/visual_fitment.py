"""Explicit mechanical draw fitment, independent of vehicle physics.

Selections and hub frames must come from qualified source/build evidence.
Neither bounds nor an asymmetric caliper is used to guess an attachment.
Static translation fixes one rest pose only. Runtime suspension/steering needs
an unsprung, non-spinning attachment matrix; a spinning wheel is unsuitable
for a caliper. No native attachment layout is asserted by this module.
"""
from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Mapping, Sequence

from ..bounds import compute_bounds1339, replace_bounds1339
from ..dx import parse_dx_bytes


def _vector(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 3 or any(
        type(x) not in (int, float) or not math.isfinite(x) for x in value
    ):
        raise ValueError(f'{label}: expected three finite numbers')
    return tuple(float(x) for x in value)


def _bounds(points):
    return [[f(p[k] for p in points) for k in range(3)] for f in (min, max)]


def _selection(raw, definition):
    if not isinstance(definition, Mapping) or set(definition) != {
        'profile_version', 'source_sha256', 'groups', 'provenance'
    } or type(definition['profile_version']) is not int or definition['profile_version'] != 1:
        raise ValueError('unsupported visual fitment profile')
    if hashlib.sha256(raw).hexdigest() != definition['source_sha256']:
        raise ValueError('mechanical source hash differs')
    if not isinstance(definition['provenance'], str) or not definition['provenance'].strip():
        raise ValueError('mechanical provenance is required')
    model = parse_dx_bytes(raw)
    if not model.diagnostics.validated:
        raise ValueError('invalid mechanical DX')
    groups = definition['groups']
    if not isinstance(groups, list) or not groups or len(groups) > 64:
        raise ValueError('invalid mechanical groups')
    seen_draws = set()
    seen_names = set()
    selected = []
    by_index = {d.draw_index: d for d in model.physical_draws}
    owners = {}
    for d in model.physical_draws:
        for vertex in set(model.draw_global_indices(d)):
            owners.setdefault(vertex, set()).add(d.draw_index)
    for group in groups:
        if not isinstance(group, Mapping) or set(group) != {
            'name', 'draw_indices', 'source_hub_m', 'target_hub_m', 'provenance'
        }:
            raise ValueError('unsupported mechanical group')
        name = group['name']
        if not isinstance(name, str) or not name.strip() or name in seen_names:
            raise ValueError('invalid or duplicate mechanical group name')
        seen_names.add(name)
        if not isinstance(group['provenance'], str) or not group['provenance'].strip():
            raise ValueError('group provenance is required')
        ids = group['draw_indices']
        if not isinstance(ids, list) or not ids or any(
            type(i) is not int or i not in by_index for i in ids
        ) or len(set(ids)) != len(ids) or seen_draws.intersection(ids):
            raise ValueError('invalid or overlapping mechanical draw selection')
        source = _vector(group['source_hub_m'], 'source hub')
        target = _vector(group['target_hub_m'], 'target hub')
        delta = tuple(target[k] - source[k] for k in range(3))
        if math.dist(source, target) > .25:
            raise ValueError('mechanical translation exceeds 0.25 m guard')
        vertices = set()
        for index in ids:
            d = by_index[index]
            # Nested controls own semantics, so move only ordinary material leaves.
            if d.tag != 2 or d.group_label is not None or d.control_words:
                raise ValueError('mechanical selection must contain material leaves')
            vertices.update(model.draw_global_indices(d))
        if any(not owners[i].issubset(set(ids)) for i in vertices):
            raise ValueError('mechanical vertices shared with another draw/group')
        seen_draws.update(ids)
        selected.append((group, source, target, delta, vertices))
    return model, selected


def diagnose_mechanics(raw: bytes, definition: Mapping) -> dict:
    """Measure explicitly identified mechanical draws against declared hubs."""
    model, groups = _selection(raw, definition)
    rows = []
    for group, source, target, delta, vertices in groups:
        points = [model.vertices.positions[i] for i in sorted(vertices)]
        draws = []
        for index in group['draw_indices']:
            draw = model.physical_draws[index]
            ps = [model.vertices.positions[i] for i in set(model.draw_global_indices(draw))]
            box = _bounds(ps)
            centre = [(box[0][k] + box[1][k]) / 2 for k in range(3)]
            draws.append({'draw_index': index, 'textures': list(draw.texture_tuple),
                          'aabb_m': box, 'aabb_centre_m': centre,
                          'aabb_centre_minus_source_hub_m': [centre[k] - source[k] for k in range(3)],
                          'note': 'AABB centre is descriptive; asymmetric caliper bounds are not a hub detector'})
        rows.append({'name': group['name'], 'source_hub_m': list(source),
                     'target_hub_m': list(target), 'translation_m': list(delta),
                     'hub_difference_m': math.dist(source, target),
                     'draw_indices': group['draw_indices'], 'vertex_count': len(vertices),
                     'aabb_m': _bounds(points), 'draws': draws,
                     'provenance': group['provenance']})
    return {'status': 'OFFLINE_MECHANICAL_FITMENT_DIAGNOSTIC',
            'source_sha256': definition['source_sha256'], 'groups': rows,
            'provenance': definition['provenance'], 'runtime_qualified': False,
            'boundary': 'declared rest-frame hubs only; no contact solve, equilibrium, jounce, steering or spin'}


def translate_mechanics(raw: bytes, definition: Mapping) -> tuple[bytes, dict]:
    """Translate selected mechanics only, preserving all other DX payload bytes."""
    model, groups = _selection(raw, definition)
    positions = list(model.vertices.positions)
    permitted = set()
    for _, _, _, delta, vertices in groups:
        for i in vertices:
            positions[i] = tuple(positions[i][k] + delta[k] for k in range(3))
            start = model.vertices.position_offset + i * model.vertices.position_stride
            permitted.update(range(start, start + 12))
    # Existing position-only writer deliberately requires warning parity before
    # bounds are refreshed. Fitment can enlarge bounds, so write positions and
    # bounds as one transaction, then audit the exact permitted byte ranges.
    patched = bytearray(raw)
    for _, _, _, _, vertices in groups:
        for i in vertices:
            struct.pack_into('<3f', patched, model.vertices.position_offset + i * model.vertices.position_stride,
                             *positions[i])
    parsed = parse_dx_bytes(bytes(patched))
    if parsed.collision.unparsed_offset + 44 != len(raw):
        raise ValueError('mechanical correction requires qualified terminal bounds1339')
    if bytes(patched) == raw:
        output = raw
    else:
        bounds = compute_bounds1339(parsed.vertices.positions, parsed.collision.convex_hull,
                                   offset=parsed.collision.unparsed_offset)
        output = replace_bounds1339(bytes(patched), bounds, footer_offset=parsed.collision.unparsed_offset)
    permitted.update(range(parsed.collision.unparsed_offset, len(output)))
    if len(raw) != len(output) or any(a != b and i not in permitted for i, (a, b) in enumerate(zip(raw, output))):
        raise ValueError('mechanical correction changed bytes outside selected positions/bounds')
    after = parse_dx_bytes(output)
    if not after.diagnostics.validated:
        raise ValueError('mechanical correction invalid after reparse')
    report = diagnose_mechanics(raw, definition)
    report.update({'status': 'PASS_STATIC_MECHANICAL_TRANSLATION',
                   'output_sha256': hashlib.sha256(output).hexdigest(),
                   'changed_vertex_count': sum(a != b for a, b in zip(model.vertices.positions, after.vertices.positions)),
                   'preserved': ['unselected positions', 'normals', 'UVs', 'vertex colours',
                                 'indices', 'draw/control/material records', 'collision'],
                   'boundary': 'rest-pose visual correction only; body-owned mechanics still do not follow suspension/steering'})
    return output, report


def attachment_point(point: Sequence[float], source_hub: Sequence[float],
                     current_hub: Sequence[float], rotation: Sequence[Sequence[float]]) -> tuple[float, float, float]:
    """Pure rigid attachment math for caller-supplied unsprung non-spin poses.

    Point and source_hub share the body rest frame. Current hub and matrix are
    in the caller's output frame. A rotor's spinning matrix and a caliper's
    non-spinning matrix must be supplied separately when spin is represented.
    This function neither reads native memory nor changes a DX resource.
    """
    p = _vector(point, 'point')
    source = _vector(source_hub, 'source hub')
    target = _vector(current_hub, 'current hub')
    if not isinstance(rotation, (list, tuple)) or len(rotation) != 3:
        raise ValueError('attachment rotation must be a proper orthonormal 3x3 matrix')
    rows = [_vector(row, 'rotation row') for row in rotation]
    if any(abs(sum(rows[i][k] * rows[j][k] for k in range(3)) - (i == j)) > 1e-5
           for i in range(3) for j in range(3)):
        raise ValueError('attachment rotation must be a proper orthonormal 3x3 matrix')
    determinant = sum(rows[0][i] * (rows[1][(i+1)%3]*rows[2][(i+2)%3] - rows[1][(i+2)%3]*rows[2][(i+1)%3]) for i in range(3))
    if abs(determinant - 1) > 1e-5:
        raise ValueError('attachment rotation must be proper; reflection is unsupported')
    local = [p[k] - source[k] for k in range(3)]
    return tuple(target[i] + sum(rows[i][k] * local[k] for k in range(3)) for i in range(3))
