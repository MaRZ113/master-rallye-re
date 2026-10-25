"""Qualified draw-scoped diffuse modulation through the existing attribute writer.

Never splits topology, invents material types or changes diffuse alpha ownership.
Texture bindings and unknown native states remain read-only in this editor.
"""
import hashlib
import math
from .dx import parse_dx_bytes
from .r4e_writer import patch_dx_attributes

def surface_capabilities(raw,draw_id):
    m=parse_dx_bytes(raw)
    if not m.diagnostics.validated:raise ValueError('Invalid source DX')
    draws={d.draw_index:d for d in m.physical_draws}
    if type(draw_id) is not int or draw_id not in draws:raise ValueError('Unknown physical draw ID')
    d=draws[draw_id];vertices=set(m.draw_global_indices(d))
    overlap=[other.draw_index for other in m.physical_draws if other.draw_index!=draw_id and vertices.intersection(m.draw_global_indices(other))]
    return {'draw_id':draw_id,'record_path':list(d.record_path),'core_offset':d.core_offset,
            'vertices':len(vertices),'shared_vertex_draws':overlap,'diffuse_rgb_editable':bool(d.flags_0x20[2]) and bool(vertices) and not overlap,
            'reflection_disable_editable':bool(d.unknown_0x24&4),'alpha':'read-only: preserved native damage/reflection ownership',
            'texture_slots':'read-only: length-changing binding/resource-allocation authoring is not qualified by this editor',
            'reason':'Vertex colors disabled' if not d.flags_0x20[2] else 'Shared vertex ownership with draws '+str(overlap) if overlap else 'Independent vertex RGB; baked texture remains untouched'}

def apply_surface_edits(raw,edits,*,source_sha256):
    if hashlib.sha256(raw).hexdigest()!=source_sha256:raise ValueError('Surface source SHA256 mismatch')
    m=parse_dx_bytes(raw);colors=bytearray(m.vertices.colors);env={};seen=set()
    for edit in edits:
        if not isinstance(edit,dict) or set(edit)-{'draw_id','rgb','disable_reflection'}:raise ValueError('Unsupported surface property')
        draw_id=edit['draw_id'];caps=surface_capabilities(raw,draw_id)
        if draw_id in seen:raise ValueError('Duplicate surface edit')
        seen.add(draw_id);draw=next(d for d in m.physical_draws if d.draw_index==draw_id)
        if 'rgb' in edit:
            rgb=edit['rgb']
            if not caps['diffuse_rgb_editable']:raise ValueError(caps['reason'])
            if len(rgb)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=2 for v in rgb):raise ValueError('RGB multipliers must be finite in 0..2')
            for index in set(m.draw_global_indices(draw)):
                for c,gain in ((2,rgb[0]),(1,rgb[1]),(0,rgb[2])):colors[index*4+c]=min(255,round(m.vertices.colors[index*4+c]*gain))
        if 'disable_reflection' in edit:
            if type(edit['disable_reflection']) is not bool:raise ValueError('Reflection selection requires boolean')
            if not caps['reflection_disable_editable']:raise ValueError('Source draw has no qualified environment pass')
            env[draw_id]=not edit['disable_reflection']
    result=patch_dx_attributes(raw,colors=bytes(colors),material_env=env)
    parsed=parse_dx_bytes(result.data)
    if parsed.vertices.colors[3::4]!=m.vertices.colors[3::4]:raise ValueError('Unexpected alpha mutation')
    return result
