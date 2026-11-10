"""Dakar 2 Xbox vehicle -> MR Classic native project (geometry/textures from source, materials from MR).

Owner policy (2026-11-11): the vehicle keeps the original Dakar 2 geometry and
diffuse textures, while every surface uses a stock Master Rallye material
(flags plus MR secondary environment texture) chosen by an explicit semantic
role. The strict Xbox combiner equivalence documented in
DAKAR2_NATIVE_MATERIAL_QUALIFICATION.md is intentionally NOT claimed: this is
the MR Classic authoring mode from MASTER_PLAN section 3.

Source draws use cull NONE with mixed winding. MR renders native car draws
single-sided, with (b-a)x(c-a) pointing along the vertex normals (stock
Pajero: 2190 of 2191 triangles). Each derived triangle is oriented against
its own source normals; triangles whose normals do not decide a side are
emitted twice (front and back, back copy with negated normals).
"""
from __future__ import annotations

import copy
import json
import math
from dataclasses import replace
from pathlib import Path
import shutil

from . import universal_vehicle_scene as uvs
from .universal_scene_bridge import compile_scene
from .scene_dx_writer import ScenePart, write_scene_dx
from .topology_writer import CompiledVertex, DrawGeometry
from .source_garage_pilot import ROOT, _admit_output, _copy_scene, _json, _renderer

BASIS = [-1., 0., 0., 0., 0., 1., 0., 0., 0., 0., -1., 0., 0., 0., 0., 1.]
RIDE_HEIGHT = .05          # retail Pajero RideHeight; hub Y = -RideHeight
AMBIGUOUS_COS = .2         # |cos(face normal, vertex normals)| below this -> two-sided

# Stock MR material per semantic role, read from retail Pajero car.dx:
# (secondary environment texture or None, alpha mode)
MR_MATERIALS = {
    'paint': 'whitepaint-tga',     # pdoor/bon/pfront draws, flags 0x7
    'trim': 'rubber-tga',          # black-tga + rubber-tga draws
    'chrome': 'chrome-tga',        # pwheelrim/pswheel64_2 draws
    'lamp': 'perspex-tga',         # plight64 draws
    'glass': 'glass-tga',          # windscreen draws
    'tyre': 'rubber-tga',          # pstread/pswheel64 draws
    'interior': None,              # underdash/chair/suit draws, flags 0x3
}

COMMON_NODE_ROLES = {
    'DRIVER': 'interior', 'CODRIVER': 'interior', 'INTERIOR': 'interior', 'ROLLCAGE': 'interior',
    'REARROLLCAGE': 'interior', 'L_EXHAUST': 'chrome', 'R_EXHAUST': 'chrome', 'EXHAUST': 'chrome',
    **{f'{c}_{part}': 'trim' for c in ('FL', 'FR', 'BL', 'BR') for part in ('AXLE', 'HUB', 'MUDFLAP')},
}
VEHICLES = {
    'PAJERO': {
        'catalog': 'PAJERO_HI_0_0.LOD', 'prefix': 'PAJ_', 'family': 'D2Pajero',
        'name': 'Dakar 2 Mitsubishi Pajero #205', 'manufacturer': 'MITSUBISHI', 'model': 'PAJERO DAKAR 2',
        'results': 'PAJERO D2 205', 'donor': 'Pajero', 'audio': 1, 'marker': [.85, .12, .1],
        'textures': {'xtx-043': 'paint', 'xtx-046': 'paint', 'xtx-048': 'lamp', 'xtx-050': 'glass',
                     'xtx-052': 'chrome', 'xtx-053': 'tyre'},
        'paint_textures': ('xtx-043', 'xtx-046'), 'wheel_face': 'xtx-052',
        'nodes': {'FL_HEADLIGHT': 'lamp', 'FR_HEADLIGHT': 'lamp'},
        'windscreen': 'WINDSCREEN', 'side_windows': 'SIDEWINDOWS', 'rear_lamps': ('RREARLIGHTS', 'LREARLIGHTS'),
        'shell': ('BODY', 'BACKDOOR', 'BONNET', 'FRONT_BUMPER', 'REAR_BUMPER', 'GRILL'),
    },
    'NISSAN': {
        'catalog': 'NISSAN_HI_0_0.LOD', 'prefix': 'MID_', 'family': 'D2Pickup',
        'name': 'Dakar 2 Nissan Pickup', 'manufacturer': 'NISSAN', 'model': 'PICKUP DAKAR 2',
        'results': 'NISSAN PICKUP D2', 'donor': 'Navara', 'audio': 7, 'marker': [.95, .55, .1],
        'textures': {'xtx-040': 'paint', 'xtx-043': 'paint', 'xtx-045': 'lamp', 'xtx-047': 'glass',
                     'xtx-049': 'chrome', 'xtx-051': 'tyre'},
        'paint_textures': ('xtx-040', 'xtx-043'), 'wheel_face': 'xtx-049',
        'nodes': {'TOPRLIGHTS': 'lamp', 'DIFF': 'trim', 'DIFFAXLE': 'trim', 'LRSHOCK': 'trim', 'RRSHOCK': 'trim'},
        'windscreen': 'WINDSCREEN', 'side_windows': 'SIDESCREEN', 'rear_lamps': ('RLIGHT',),
        'shell': ('MAINBODY', 'BONNET'),
    },
}
# Stock MR material textures are always taken from the retail Pajero family.
MATERIAL_FAMILY = 'Pajero'

WHEEL_NODES = {'front_left': 'FL_WHEEL', 'front_right': 'FR_WHEEL', 'rear_left': 'BL_WHEEL', 'rear_right': 'BR_WHEEL'}
SLOTS = ('front_left', 'front_right', 'rear_left', 'rear_right')


def _short(node, prefix):
    return node['name'][len(prefix):] if node['name'].startswith(prefix) else node['name']


def mesh_roles(scene, spec):
    nodes = {n['id']: n for n in scene['nodes']}
    mats = {m['id']: m for m in scene['materials']}
    node_roles = {**COMMON_NODE_ROLES, **spec['nodes']}
    roles = {}
    for mesh in scene['meshes']:
        node = nodes[mesh['id'].rsplit('-sub', 1)[0]]
        texture = mats[mesh['material_id']]['diffuse_texture_id']
        role = spec['textures'].get(texture)
        if texture in spec['paint_textures']:
            role = node_roles.get(_short(node, spec['prefix']), 'paint')
        if role is None:
            raise ValueError('no semantic MR role for source texture ' + texture)
        roles[mesh['material_id']] = role
    return roles


def pilot_profile(scene_path, vehicle, fit=None):
    path = Path(scene_path); scene = uvs.load_scene(path); spec = VEHICLES[vehicle]
    if scene['source'].get('catalog') != spec['catalog']:
        raise ValueError('scene is not the reviewed ' + spec['catalog'])
    roles = mesh_roles(scene, spec)
    materials = {}
    for key, role in roles.items():
        rule = {'interpretation': 'mr_authoring', 'role': 'MR Classic ' + role,
                'evidence': 'Dakar 2 diffuse texture with the stock MR ' + role + ' material (owner policy: source textures, MR materials); Xbox combiner not reproduced.'}
        if role == 'glass':
            rule['mode'] = 'alpha_blend'
        elif role == 'chrome' and scene_mesh_texture(scene, key) == spec['wheel_face']:
            rule.update(mode='alpha_test', alpha_ref=100)   # wheel face spoke holes; Xbox GREATER 100
        else:
            rule.update(mode='opaque', allow_alpha_flatten=True)
        materials[key] = rule
    from .scene_semantics import features
    used = {mid for n in scene['nodes'] for mid in n['mesh_ids']}
    policy = {row['id']: {'disposition': 'mr_classic_material',
                          'evidence': 'Owner policy 2026-11-11: Dakar 2 geometry and diffuse textures with stock MR materials.',
                          'impact': 'Xbox ' + row['kind'] + ' replaced by the MR role material; no Source Fidelity claim.'}
              for row in features(scene, used)}
    nodes = scene['nodes']; by_short = {_short(n, spec['prefix']): n['id'] for n in nodes}
    wheels = {slot: by_short[name] for slot, name in WHEEL_NODES.items()}
    profile = {'schema': 'universal-scene-mr-profile/1', 'source_scene_sha256': uvs.sha(uvs.read_bounded(path, uvs.MAX_JSON_BYTES)),
               'normalized_to_mr': BASIS, 'authoring_transform': fit or uvs.IDENTITY[:],
               'transform_evidence': 'Normalized +X right/+Y up/-Z front -> MR +X left/+Y up/+Z front. 1 source unit = 1 MR metre (authoring choice). Common translation centres the axles and puts the mean hub at Y=-RideHeight.',
               'body_node_ids': [n['id'] for n in nodes if n.get('role') == 'body' and n.get('visible') and n['mesh_ids']],
               'wheel_slots': wheels, 'canonical_wheel_slot': 'front_right', 'materials': materials,
               'texture_row_policy': 'preserve', 'uv_v_policy': 'preserve', 'source_feature_policy': policy}
    return profile, roles


def scene_mesh_texture(scene, material_id):
    return next(m['diffuse_texture_id'] for m in scene['materials'] if m['id'] == material_id)


def axle_fit(result):
    """Translation that centres axles and puts the mean hub at Y=-RideHeight; symmetric hubs."""
    hubs = {s: result['report']['hubs'][s]['derived_hub_mr'] for s in SLOTS}
    xc = sum(h[0] for h in hubs.values()) / 4
    zc = (sum(hubs[s][2] for s in SLOTS if s.startswith('front')) / 2 + sum(hubs[s][2] for s in SLOTS if s.startswith('rear')) / 2) / 2
    yc = sum(h[1] for h in hubs.values()) / 4
    fit = uvs.IDENTITY[:]; fit[3] = -xc; fit[7] = -RIDE_HEIGHT - yc; fit[11] = -zc
    return fit


def symmetric_hubs(result):
    hubs = {s: result['report']['hubs'][s]['derived_hub_mr'] for s in SLOTS}
    front = (abs(hubs['front_left'][0]) + abs(hubs['front_right'][0])) / 2
    rear = (abs(hubs['rear_left'][0]) + abs(hubs['rear_right'][0])) / 2
    zf = (hubs['front_left'][2] + hubs['front_right'][2]) / 2; zr = (hubs['rear_left'][2] + hubs['rear_right'][2]) / 2
    out = {'front_left': [front, -RIDE_HEIGHT, zf], 'front_right': [-front, -RIDE_HEIGHT, zf],
           'rear_left': [rear, -RIDE_HEIGHT, zr], 'rear_right': [-rear, -RIDE_HEIGHT, zr]}
    return out, {'front_track': 2 * front, 'rear_track': 2 * rear, 'wheelbase': zf - zr,
                 'residual_m': {s: [out[s][i] - hubs[s][i] for i in range(3)] for s in SLOTS}}


def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def orient(geometry):
    """Orient every triangle along its source normals; ambiguous -> two-sided."""
    vertices = list(geometry.vertices); triangles = []; back = {}; stats = {'kept': 0, 'flipped': 0, 'two_sided': 0}
    def back_vertex(i):
        if i not in back:
            v = vertices[i]
            back[i] = len(vertices)
            vertices.append(replace(v, normal=tuple(-n for n in v.normal)))
        return back[i]
    for a, b, c in geometry.triangles:
        pa, pb, pc = (geometry.vertices[k].position for k in (a, b, c))
        face = _cross(_sub(pb, pa), _sub(pc, pa))
        normal = tuple(sum(geometry.vertices[k].normal[j] for k in (a, b, c)) for j in range(3))
        fl, nl = math.sqrt(_dot(face, face)), math.sqrt(_dot(normal, normal))
        cos = _dot(face, normal) / (fl * nl) if fl > 1e-12 and nl > 1e-9 else 0.
        if abs(cos) < AMBIGUOUS_COS:
            triangles.append((a, b, c)); triangles.append((back_vertex(a), back_vertex(c), back_vertex(b)))
            stats['two_sided'] += 1
        elif cos < 0:
            triangles.append((a, c, b)); stats['flipped'] += 1
        else:
            triangles.append((a, b, c)); stats['kept'] += 1
    return DrawGeometry(tuple(vertices), tuple(triangles)), stats


def mr_part(part, role):
    env = MR_MATERIALS[role]
    textures = (part.textures[0], env or 'Null', 'Null')
    return replace(part, textures=textures, environment=env is not None)


def adapt(parts, maps, roles, ledger):
    out = []
    for part, record in zip(parts, maps):
        role = roles[record['material_id']]
        geometry, stats = orient(part.geometry)
        out.append(mr_part(replace(part, geometry=geometry), role))
        ledger.append({'mesh_id': record['mesh_id'], 'kind': record['kind'], 'slot': record.get('wheel_slot'), 'role': role,
                       'mr_secondary_texture': MR_MATERIALS[role], **stats})
    return out


def _split_x(part, sign):
    from .glass_authoring import subset
    g = part.geometry
    ids = [i for i, t in enumerate(g.triangles) if sign * sum(g.vertices[k].position[0] for k in t) > 0]
    return replace(part, geometry=subset(g, ids)) if ids else None


def _merge(parts):
    vertices = []; triangles = []
    for p in parts:
        base = len(vertices); vertices.extend(p.geometry.vertices)
        triangles.extend(tuple(base + i for i in t) for t in p.geometry.triangles)
    return replace(parts[0], geometry=DrawGeometry(tuple(vertices), tuple(triangles)))


def semantic_body(body, maps, nodes, spec):
    """Ordinary draws + windscreen/left/right panes + one rear brake draw."""
    names = [_short(nodes[m['node_id']], spec['prefix']) for m in maps]
    ordinary = []; core = []; lamps = []; panes = {}
    for part, name in zip(body, names):
        if name == spec['windscreen']:
            panes['screenfront'] = part
        elif name == spec['side_windows']:
            panes['screenleft'] = _split_x(part, +1)    # MR +X = vehicle left
            panes['screenright'] = _split_x(part, -1)
        elif name in spec['rear_lamps']:
            lamps.append(part)
        else:
            if name in spec['shell']:
                core.append(len(ordinary))
            ordinary.append(part)
    parts = list(ordinary); pane_index = {}
    for label in ('screenfront', 'screenleft', 'screenright'):
        if panes.get(label) is None:
            raise ValueError('missing glass pane ' + label)
        pane_index[label] = len(parts); parts.append(panes[label])
    brake = len(parts); parts.append(_merge(lamps))
    return parts, pane_index, brake, core


def _physics(retail_sma, family, donor, dims):
    from .addon_sdk.physics_profile import MEMBERS
    from .addon_sdk.project import read_sma_member
    m = MEMBERS[0]
    return {'profile_version': 1, 'donor_family': donor, 'runtime_family': family,
            'source_sha256': {p: uvs.sha(read_sma_member(retail_sma, p)) for p in MEMBERS},
            'overrides': {m: {'Dimensions/Length': round(dims['length'], 5), 'Dimensions/Width': round(dims['width'], 5),
                              'Dimensions/Height': round(dims['height'], 5), 'Dimensions/WheelBase': round(dims['wheelbase'], 5),
                              'Dimensions/TrackWidthFront': round(dims['front_track'], 5), 'Dimensions/TrackWidthRear': round(dims['rear_track'], 5),
                              'Dimensions/WheelRadiusFront': round(dims['wheel_radius'], 5), 'Dimensions/WheelRadiusRear': round(dims['wheel_radius'], 5)}},
            'notes': 'Clean retail ' + donor + ' physics family; only measured Dakar 2 dimensions (1 unit = 1 m) override it. Mass, engine, tyres, springs and damping are retail. Gameplay settlement not qualified.'}


def _bounds(parts):
    pts = [v.position for p in parts for v in p.geometry.vertices]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def _wheel_radius(parts):
    return max(math.hypot(v.position[1], v.position[2]) for p in parts for v in p.geometry.vertices)


def create_pilot(scene_path, vehicle, retail_sma, retail_root, output, *, render_ui=None):
    from .addon_sdk.project import _physics_family_overlays, read_sma_member
    from .addon_sdk.manifest import load_capabilities
    from .addon_sdk.native_states import author_states
    from .addon_sdk.auto_features import procedural_cracks, lamp_textures
    from .addon_sdk.wheel_orientation import orient_parts
    from .addon_sdk.import_project import prepare
    from .addon_sdk.physics_collision import fit_collision
    from .dxt import parse_dxt_bytes
    spec = VEHICLES[vehicle]; family = spec['family']
    path = Path(scene_path).absolute(); retail_sma = Path(retail_sma).absolute(); retail_root = Path(retail_root).absolute()
    donor = retail_root / 'DataGx/Vehicles' / spec['donor']
    scene = uvs.load_scene(path)
    output = _admit_output(output, scene, [path.parent, donor, retail_sma, retail_root])
    capabilities, _ = load_capabilities(ROOT / 'research/vehicles/sdk/capabilities/retail-2001.json')
    _physics_family_overlays(data_sma=retail_sma, retail_data_root=retail_root, capabilities=capabilities,
                             donor_family=spec['donor'], runtime_family=family)
    for item in donor.iterdir():
        if item.is_file() and item.suffix.lower() in ('.dx', '.dxt'):
            if item.read_bytes() != read_sma_member(retail_sma, f"DataGx/Vehicles/{spec['donor']}/{item.name}"):
                raise ValueError('donor differs from clean retail SMA: ' + item.name)
    # Pass 1 measures source hubs; pass 2 applies the common axle datum and symmetric hubs.
    probe, roles = pilot_profile(path, vehicle)
    fit = axle_fit(compile_scene(path, probe))
    profile, roles = pilot_profile(path, vehicle, fit)
    first = compile_scene(path, profile)
    hubs, hub_report = symmetric_hubs(first)
    profile.update(hub_overrides=hubs, hub_evidence='MR symmetric axles from the mean of measured Dakar 2 rest hub origins; per-hub residuals recorded in the pilot report.')
    result = compile_scene(path, profile)
    output.mkdir(parents=True)
    copied = _copy_scene(path, output / 'inputs/source-scene')
    _json(output / 'source-profile.json', profile); _json(output / 'conversion-report.json', result['report'])
    nodes = {n['id']: n for n in scene['nodes']}
    ledger = []
    report = result['report']
    body = adapt(result['body_parts'], report['body_draws'], roles, ledger)
    complete_wheels = adapt(result['complete_parts'][len(result['body_parts']):], report['complete_draws'][len(result['body_parts']):], roles, ledger)
    wheel_slots = {s: adapt(result['wheel_parts_by_slot'][s], report['wheel_template_draws'][s], roles, ledger) for s in SLOTS}
    assets = output / 'converted/assets'; assets.mkdir(parents=True)
    for name, raw in result['textures'].items():
        (assets / name).write_bytes(raw)
    for env in sorted({e for e in MR_MATERIALS.values() if e}):
        (assets / (env + '.dxt')).write_bytes(read_sma_member(retail_sma, f'DataGx/Vehicles/{MATERIAL_FAMILY}/{env}.dxt'))
    parts, panes, lamp, core = semantic_body(body, report['body_draws'], nodes, spec)
    lit, glow, _ = lamp_textures(parse_dxt_bytes((assets / (parts[lamp].textures[0] + '.dxt')).read_bytes()))
    names = (f'{family.lower()}-stop-lit-tga', f'{family.lower()}-stop-glow-tga', f'{family.lower()}-cracks-tga')
    for name, raw in zip(names, (lit, glow, procedural_cracks())):
        (assets / (name + '.dxt')).write_bytes(raw)
    raw = write_scene_dx((donor / 'car.dx').read_bytes(), parts)
    recipe = {'source_sha256': uvs.sha(raw),
              'panes': [{'label': label, 'source_draw': i, 'triangles': list(range(len(parts[i].geometry.triangles))),
                         'broken_uv_axes': [0, 1] if label == 'screenfront' else [2, 1], 'broken_texture': names[2]}
                        for label, i in panes.items()],
              'brake': {'source_draw': lamp, 'triangles': list(range(len(parts[lamp].geometry.triangles))),
                        'lit_texture': names[0], 'glow_texture': names[1],
                        'evidence': 'Complete Dakar 2 rear lamp meshes ' + ', '.join(spec['rear_lamps']) + '.'}}
    car, states = author_states(raw, recipe)
    (assets / 'car.dx').write_bytes(car)
    (assets / 'complete.dx').write_bytes(write_scene_dx((donor / 'complete.dx').read_bytes(), parts + complete_wheels))
    (assets / 'wheel.dx').write_bytes(write_scene_dx((donor / 'wheel.dx').read_bytes(), wheel_slots['front_right']))
    _json(output / 'native-state-recipe.json', recipe)
    wheel_resources = {}
    for i, slot in enumerate(SLOTS):
        slot_parts = wheel_slots[slot]
        if slot.endswith('left'):
            slot_parts = orient_parts(slot_parts, source_outward_x=1, target_outward_x=-1)
        wheel_resources[f'wheel-source{i}.dx'] = write_scene_dx((donor / 'wheel.dx').read_bytes(), slot_parts)
    for name, data in wheel_resources.items():
        (assets / name).write_bytes(data)
    _json(assets / 'preview-profile.json', {
        'race_wheel_instances': [{'translation': hubs[s], 'rotation_y': math.pi if s.endswith('left') else 0., 'scale': [1., 1., 1.]} for s in SLOTS],
        'race_wheel_resources': list(wheel_resources), 'provenance': 'Dakar 2 per-slot wheel meshes; symmetric MR hubs.'})
    lo, hi = _bounds([p for p in parts])
    dims = {**hub_report, 'length': hi[2] - lo[2], 'width': hi[0] - lo[0], 'height': hi[1] - lo[1],
            'wheel_radius': _wheel_radius(wheel_slots['front_right'])}
    _json(output / 'identity.json', {'addon': {'name': spec['name'], 'family': family, 'manufacturer': spec['manufacturer'], 'model': spec['model']}})
    author = prepare(output / 'converted', donor, output / 'identity.json', output / 'author', render_ui=render_ui or _renderer,
                     source_format='Dakar 2 Xbox Universal Vehicle Scene', vehicle_class='T2')
    project = json.loads((author / 'vehicle-project.json').read_text()); folder = Path(project['source_vehicle_dir'])
    if not folder.is_absolute():
        folder = (author / folder).resolve()
    for name, data in wheel_resources.items():
        (folder / name).write_bytes(data)
    physics = _physics(retail_sma, family, spec['donor'], dims)
    physics['collision_fit'] = {'source_sha256': uvs.sha(car), 'core_draw_indices': core, 'padding_m': [0., 0., 0.],
                                'evidence': 'Dakar 2 structural shell nodes ' + ', '.join(spec['shell']) + '; affine fit of the retail donor hull.'}
    _, collision = fit_collision(car, physics['collision_fit'])
    _json(output / 'collision-fit-report.json', collision); _json(author / 'physics-profile.json', physics)
    addon = json.loads((author / 'addon.json').read_text())
    addon['audio']['stock_audio_profile_id'] = spec['audio']
    addon['assets']['required_roles'].extend(wheel_resources)
    addon['results']['display_name'] = spec['results']
    addon['description'] = ('Private Dakar 2 (Xbox) ' + spec['name'] + ' in MR Classic mode: original geometry and diffuse textures, '
                            'stock Master Rallye materials by semantic role, retail ' + spec['donor'] + ' physics with measured dimensions. '
                            'Xbox shader parity and gameplay are not claimed.')
    _json(author / 'addon.json', addon)
    from .workshop.service import WorkshopProject
    workshop = WorkshopProject.create(author, output / 'workshop', kind='addon', car_id=29)
    workshop.data['universal_source'] = {'scene_path': str(copied), 'scene_sha256': uvs.sha(copied.read_bytes()),
        'manifest_sha256': uvs.sha((copied.parent / 'manifest.json').read_bytes()),
        'conversion_report': str(output / 'conversion-report.json'),
        'conversion_report_sha256': uvs.sha((output / 'conversion-report.json').read_bytes()),
        'adapter': 'dakar2-xbox/1', 'baseline': 'MR Classic'}
    workshop.save()
    summary = {'schema': 'dakar2-classic-pilot/1', 'vehicle': vehicle, 'family': family, 'output': str(output),
               'author': str(author), 'workshop': str(workshop.root), 'dimensions': dims, 'hub_fit': fit,
               'orientation_ledger': ledger, 'native_states': states, 'collision_core_draws': core,
               'material_policy': {'mode': 'MR Classic', 'secondary_textures': MR_MATERIALS,
                                   'boundary': 'Source diffuse textures only; Xbox masks/env maps (UV1, T1, T2) replaced by MR materials.'},
               'gameplay': 'NOT TESTED'}
    _json(output / 'pilot-report.json', summary)
    return summary
