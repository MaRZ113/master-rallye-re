"""Compile explicitly selected body mechanics into unsprung visual resources.

Native wheel matrices include the proper positive-side half turn. Auxiliary
geometry uses the inverse rest basis, so its source outboard plane and caliper
orientation survive. Physics dimensions and source frontend stay independent.
"""
from dataclasses import replace
import hashlib
import struct

from ..dx import parse_dx_bytes
from ..scene_dx_writer import ScenePart, write_scene_dx
from ..topology_writer import DrawGeometry, source_geometry
from ..preview_scene import logical_cases
from .native_brakes import write_brake_scene, validate_brake_scene
from .visual_fitment import _selection


def build_mechanical_resources(raw, wheel_template, definition, *, stock_brake_template):
    """Return new car.dx and mechanics0..3.dx from a pinned four-wheel profile.

    Existing native blight cases and all unselected draw attributes survive.
    Mechanics become independent unsprung visuals, analogous to native wheels;
    the remaining body keeps native CPU damage ownership.
    """
    model, groups = _selection(raw, definition)
    validate_brake_scene(stock_brake_template, raw)
    if len(groups) != 4:
        raise ValueError('native mechanical attachment needs four wheel groups')
    geometry = source_geometry(model)
    parts = {}
    for draw in model.physical_draws:
        parts[draw.draw_index] = ScenePart(
            geometry[draw.draw_index], draw.texture_tuple,
            bool(draw.flags_0x20[0]), bool(draw.flags_0x20[1]),
            bool(draw.unknown_0x24 & 4), bool(draw.flags_0x20[2]))
    selected = set()
    outputs = {}
    report_groups = []
    expected_order = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    for index, (group, hub, _, _, _) in enumerate(groups):
        if (1 if hub[0] > 0 else -1, 1 if hub[2] > 0 else -1) != expected_order[index]:
            raise ValueError('mechanical groups must follow native front+/front-/rear+/rear- order')
        compiled = []
        for draw in group['draw_indices']:
            part = parts[draw]
            if not part.diffuse:
                raise ValueError('mechanical leaves cannot take native lamp/glow ownership')
            positive = hub[0] > 0
            def basis(v):
                return (-v[0], v[1], -v[2]) if positive else tuple(v)
            vertices = tuple(replace(v,
                position=basis(tuple(v.position[k]-hub[k] for k in range(3))),
                normal=basis(v.normal)) for v in part.geometry.vertices)
            compiled.append(replace(part, geometry=DrawGeometry(vertices, part.geometry.triangles)))
        name = f'mechanics{index}.dx'
        outputs[name] = write_scene_dx(wheel_template, compiled)
        selected.update(group['draw_indices'])
        report_groups.append({'resource': name, 'source_draw_indices': group['draw_indices'],
                              'source_hub_m': list(hub), 'positive_side_inverse_half_turn': hub[0] > 0,
                              'output_sha256': hashlib.sha256(outputs[name]).hexdigest()})
    cases, _ = logical_cases(model)
    body = [p for i,p in parts.items() if i not in selected and i not in cases]
    off = [p for i,p in parts.items() if i in cases and cases[i][1] == 1]
    on = [p for i,p in parts.items() if i in cases and cases[i][1] == 2]
    if not off or len(on) < 2:
        raise ValueError('mechanical extraction needs qualified native blight cases')
    # Reference the original stock switch grammar while retaining the selected
    # body's actual collision suffix, including explicitly fitted donor hulls.
    stock = parse_dx_bytes(stock_brake_template)
    template = stock_brake_template[:stock.trailing.offset] + raw[model.trailing.offset:]
    outputs['car.dx'] = write_brake_scene(template, body, off, on[:-1], on[-1:])
    result = parse_dx_bytes(outputs['car.dx'])
    if raw[model.trailing.offset:model.collision.unparsed_offset] != outputs['car.dx'][result.trailing.offset:result.collision.unparsed_offset]:
        raise ValueError('mechanical extraction changed body collision')
    audit = verify_mechanical_resources(raw, outputs, definition, stock_brake_template=stock_brake_template)
    return outputs, {'source_sha256': definition['source_sha256'], 'groups': report_groups,
                     'body_sha256': hashlib.sha256(outputs['car.dx']).hexdigest(),
                     'remaining_body_vertices': result.vertex_count,
                     'removed_mechanical_draws': sorted(selected),
                     'physics_changed': False, 'frontend_changed': False,
                     'damage': 'remaining body retains native damage; unsprung mechanics are independent visual instances',
                     'attribute_audit': audit,
                     'runtime_qualified': False}


def verify_mechanical_resources(raw, outputs, definition, *, stock_brake_template):
    """Compare every retained draw attribute and logical lamp case exactly."""
    old, groups = _selection(raw, definition)
    new = parse_dx_bytes(outputs['car.dx'])
    selected = {i for group, *_ in groups for i in group['draw_indices']}
    retained = [d for d in old.physical_draws if d.draw_index not in selected]
    if len(retained) != len(new.physical_draws):
        raise ValueError('mechanics body lost or gained an unselected draw')
    a, b = source_geometry(old), source_geometry(new)
    old_cases, _ = logical_cases(old)
    new_cases, _ = logical_cases(new)
    def attributes(g):
        return (b''.join(struct.pack('<3f', *v.position) for v in g.vertices),
                b''.join(struct.pack('<3f', *v.normal) for v in g.vertices),
                b''.join(v.color for v in g.vertices),
                tuple(v.uvs for v in g.vertices), g.triangles)
    def material(d):
        return (d.texture_tuple, bytes(d.flags_0x20), d.unknown_0x14,
                d.unknown_0x18, d.unknown_0x1c_float, d.unknown_0x24,
                d.tag, d.group_label, d.control_words)
    for before, after in zip(retained, new.physical_draws):
        if material(before) != material(after) or attributes(a[before.draw_index]) != attributes(b[after.draw_index]):
            raise ValueError(f'unselected body draw attributes differ at {before.draw_index}')
        case_a = old_cases.get(before.draw_index, (None, None))[1]
        case_b = new_cases.get(after.draw_index, (None, None))[1]
        if case_a != case_b:
            raise ValueError('unselected body draw changed logical brake-light case')
    if raw[old.trailing.offset:old.collision.unparsed_offset] != outputs['car.dx'][new.trailing.offset:new.collision.unparsed_offset]:
        raise ValueError('mechanical extraction changed body collision bytes')
    aux_vertices = 0
    for index, (group, hub, _, _, _) in enumerate(groups):
        aux = parse_dx_bytes(outputs[f'mechanics{index}.dx'])
        aux_g = source_geometry(aux)
        if len(aux.physical_draws) != len(group['draw_indices']):
            raise ValueError('mechanical extraction changed auxiliary material count')
        positive = hub[0] > 0
        def basis(v): return (-v[0],v[1],-v[2]) if positive else tuple(v)
        for source_id, draw in zip(group['draw_indices'], aux.physical_draws):
            g = a[source_id]
            expected = DrawGeometry(tuple(replace(v,
                position=basis(tuple(v.position[k]-hub[k] for k in range(3))),
                normal=basis(v.normal)) for v in g.vertices),g.triangles)
            # Auxiliary leaves intentionally shed the body's switch ancestry;
            # mechanical selections were already confined to ordinary leaves.
            if material(old.physical_draws[source_id]) != material(draw) or attributes(expected) != attributes(aux_g[draw.draw_index]):
                raise ValueError('auxiliary local basis, geometry or material attributes differ')
        aux_vertices += aux.vertex_count
    lamps = validate_brake_scene(stock_brake_template, outputs['car.dx'])
    return {'status':'PASS_EXACT_MECHANICAL_EXTRACTION_ATTRIBUTES',
            'retained_body_draws':len(retained),'retained_body_vertices':new.vertex_count,
            'auxiliary_vertices':aux_vertices,'body_triangle_attributes_identical':True,
            'positions_normals_uv_rgba_textures_material_words_flags_identical':True,
            'logical_blight_cases_identical':True,'collision_bytes_identical':True,
            'native_blight_validation':lamps,'runtime_qualified':False}
