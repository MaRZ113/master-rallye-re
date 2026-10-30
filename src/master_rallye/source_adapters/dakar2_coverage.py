"""Original Dakar2 vehicle coverage/addressing rules, separate from shaders.

These are bounded static source rules, not an observed Xbox runtime snapshot.
The first pass inherits entry alpha state. Callers must supply that state and
the effective reference; a historical default never becomes runtime evidence.
No window/lamp role is guessed from a texture alpha channel or node name.
"""
from pathlib import Path
import struct
from .. import universal_vehicle_scene as u
from .dakar2 import PINS, VEHICLES, VERSION
from .dakar2_formats import RBB

SCHEMA = 'dakar2-source-coverage/1'


def _uint(value, label):
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError('Expected original uint32 ' + label)
    return value


def texture_addressing(flags):
    """8b590 calls8aed0(stage,texture,2), forcing the original flags branch.

    XTX8ac20 preserves source+0x10. Its two low bits choose U/V respectively:
    bit0 set ->1; clear ->3. bit1 set ->1; clear ->3. These are original
    source API values (1 wrap,3 clamp), not an invented secondary-UV alias.
    Other flag bits remain intact and uninterpreted here.
    """
    flags = _uint(flags, 'texture flags')
    return {'u': 1 if flags & 1 else 3, 'v': 1 if flags & 2 else 3,
            'source_flags': flags, 'uninterpreted_flags': flags & ~3,
            'evidence': '8b590 passes argument2 to8aed0; 8aed0 low-two-bit dispatch; 874a0 deferred per-stage U/V state'}


def alpha_rule(node_kind, lod_flags):
    """46ae0 applies the cutout predicate only in its second pass.

    node_kind is the first original HIR DWORD, copied to runtime node+0 by
    46da0; it is NOT the sequential UVS node ordinal or a name-based role.
    """
    node_kind = _uint(node_kind, 'HIR node kind')
    lod_flags = _uint(lod_flags, 'LOD flags')
    second = bool(lod_flags & 0x08000000)
    explicit = second and (0 < node_kind < 8 or bool(lod_flags & 0x10000000))
    return {'draw_pass': int(second), 'explicit_cutout': explicit,
            'draw_alpha': 'GREATER_EFFECTIVE_REFERENCE' if explicit else 'INHERITED',
            'post_node_alpha': 'DISABLED_ALWAYS_ZERO' if second else 'UNCHANGED',
            'evidence': '46ae0 second loop; predicate HIRkind1..7 or LODflag10000000; 86920(4,18eab4), then86920(7,0)+88100(0)'}


def trace_alpha(nodes, *, incoming_enabled, effective_reference):
    """Replay the qualified CPU state schedule with explicit context inputs.

    All submeshes of a node share one state, then second-pass state resets.
    An empty node still causes the second-pass CPU reset if its LOD exists;
    selection/visibility is external and must not be inferred from this trace.
    """
    if type(incoming_enabled) is not bool:
        raise ValueError('Explicit incoming alpha enable required')
    if type(effective_reference) is not int or not 0 <= effective_reference <= 255:
        raise ValueError('Explicit effective alpha reference required')
    if not isinstance(nodes, list) or len(nodes) > 256:
        raise ValueError('Vehicle node count budget')
    ids = [n['id'] for n in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate source coverage node')
    rows = []
    enabled = incoming_enabled
    # Disable alone does not prove a particular dormant compare/reference.
    comparison = 'INHERITED'
    reference = None
    for pass_ in (0, 1):
        for node in nodes:
            rule = alpha_rule(node['source_kind'], node['source_lod_flags'])
            if rule['draw_pass'] != pass_:
                continue
            if rule['explicit_cutout']:
                enabled, comparison, reference = True, 'GREATER', effective_reference
            rows.append({'node_id': node['id'], 'source_kind': node['source_kind'], 'source_lod_flags': node['source_lod_flags'],
                         **rule, 'enabled': enabled, 'comparison': comparison,
                         'reference': reference})
            if pass_:
                enabled, comparison, reference = False, 'ALWAYS', 0
    return rows


def scene_coverage(scene, root, *, incoming_enabled, effective_reference):
    """Read already retained original snapshots and bind rules to exact draws.

    The supplied entry enable/reference describe a controlled reconstruction
    context. They do not establish that an original running game used it.
    """
    if scene['metadata'].get('adapter') != VERSION:
        raise ValueError('Qualified Dakar2 source adapter required')
    catalog = scene['source']['catalog']
    name = next((n for n in VEHICLES if catalog == n + '_HI_0_0.LOD'), None)
    if name is None:
        raise ValueError('Unqualified Dakar2 coverage corpus')
    root = Path(root)
    blobs = {}
    for record in scene['source']['resources']:
        member = record['member']
        if member not in ('ALL.RBB', catalog):
            continue
        if member in blobs:
            raise ValueError('Duplicate source coverage snapshot')
        raw = u.read_bounded(root/u.relative_name(record['snapshot_path']), u.MAX_OUTPUT_BYTES)
        if len(raw) != record['bytes'] or u.sha(raw) != record['sha256']:
            raise ValueError('Coverage source snapshot provenance mismatch')
        if member == 'ALL.RBB' and record['sha256'] != PINS['ALL.RBB']:
            raise ValueError('Unqualified original ALL.RBB')
        blobs[member] = RBB(raw)
    if set(blobs) != {'ALL.RBB', catalog}:
        raise ValueError('Missing original coverage snapshots')
    hir = blobs['ALL.RBB']; lod = blobs[catalog]
    if scene['source']['hierarchy_resource']['id'] != VEHICLES[name]['hierarchy_resource']:
        raise ValueError('Coverage HIR vehicle ownership mismatch')
    hir_at = hir.resources[VEHICLES[name]['hierarchy_resource']]['offset']
    lod_at = lod.resources[0]['offset']
    if hir.u(hir_at+4) != len(scene['nodes']) or lod.u(lod_at) != len(scene['nodes']):
        raise ValueError('Coverage original node count mismatch')
    nodes = []
    for ordinal, node in enumerate(scene['nodes']):
        original = node['source_transform_record']; at = hir_at+0x20+ordinal*0xd4
        flags = lod.u(lod_at+8+ordinal*8)
        if (original['id'] != ordinal or original['offset'] != at or
                original['raw_record_sha256'] != u.sha(hir.slice(at, 0xd4)) or
                node['source_lod_flags'] != flags or node['render_pass'] != int(bool(flags & 0x08000000))):
            raise ValueError('Coverage original node identity or pass mismatch')
        nodes.append({'id': node['id'], 'source_kind': hir.u(at), 'source_lod_flags': flags})
    trace = {r['node_id']: r for r in trace_alpha(nodes, incoming_enabled=incoming_enabled,
                                                 effective_reference=effective_reference)}
    textures = []
    for texture in scene['textures']:
        original = texture['source']; index = original['resource_id']
        if index >= len(lod.resources) or index < 0:
            raise ValueError('Texture coverage source resource index')
        resource = lod.resources[index]
        if resource['type'] != 'XTX' or resource['offset'] != original['offset']:
            raise ValueError('Texture coverage ownership mismatch')
        flags = lod.u(resource['offset']+0x10)
        textures.append({'texture_id': texture['id'], 'source_offset': resource['offset'],
                         'source_member_sha256': u.sha(lod.data), **texture_addressing(flags)})
    node_by_mesh = {mid: n for n in scene['nodes'] for mid in n['mesh_ids']}
    draws = []
    for mesh in scene['meshes']:
        node = node_by_mesh[mesh['id']]
        draws.append({'mesh_id': mesh['id'], 'material_id': mesh['material_id'],
                      'node_name': node['name'], **trace[node['id']],
                      'source_semantic_role': 'UNKNOWN; alpha/cutout is not glass/lamp ownership'})
    return {'schema': SCHEMA, 'source_catalog': catalog, 'draws': draws, 'textures': textures,
            'entry_alpha_enabled': incoming_enabled, 'effective_reference_supplied': effective_reference,
            'runtime_evidence': 'NOT TESTED', 'native_material_readiness': 'BLOCKED',
            'context': 'Controlled static schedule; effective runtime state, visibility and original shader outputs remain separate',
            'source_mutated': False, 'native_fixture_allowed': False}
