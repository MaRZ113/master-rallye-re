"""Qualified draw-scoped diffuse modulation through the existing attribute writer.

Never splits topology, invents material types or changes diffuse alpha ownership.
Texture bindings use a separately qualified length-prefixed record writer.
Unknown native states remain read-only.
"""
import hashlib
import math
from dataclasses import dataclass
from .dx import parse_dx_bytes
from .r4e_writer import patch_dx_attributes

@dataclass(frozen=True)
class StructuralBindingAudit:
    """Record-splice evidence; shifted suffix bytes are not a binary diff."""
    attributes: dict
    bindings: tuple
    def to_dict(self):
        return {'kind':'validated_native_record_splices','attribute_diff':self.attributes,
                'bindings':list(self.bindings),'geometry_and_suffix_preserved':True}

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
            'reflection_strength_editable':d.unknown_0x24==7 and len(d.texture_slots)==3 and d.texture_slots[1].value.casefold()!='null' and not any(d.flags_0x20[:2]) and bool(d.flags_0x20[2]) and bool(vertices) and not overlap,
            'texture_slots':'Existing owned diffuse or opaque environment slot; variable names/resolution; alpha compatibility checked per native state',
            'reason':'Vertex colors disabled' if not d.flags_0x20[2] else 'Shared vertex ownership with draws '+str(overlap) if overlap else 'Independent vertex RGB; baked texture remains untouched'}

def apply_surface_edits(raw,edits,*,source_sha256,texture_provider=None):
    if hashlib.sha256(raw).hexdigest()!=source_sha256:raise ValueError('Surface source SHA256 mismatch')
    m=parse_dx_bytes(raw);colors=bytearray(m.vertices.colors);env={};seen=set()
    for edit in edits:
        if not isinstance(edit,dict) or set(edit)-{'draw_id','rgb','disable_reflection','bindings','reflection_strength'}:raise ValueError('Unsupported surface property')
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
        if 'reflection_strength' in edit:
            gain=edit['reflection_strength']
            if not caps['reflection_strength_editable']:raise ValueError('Reflection strength requires independent opaque environment vertices; blend/test alpha stays read-only')
            if type(gain) not in (int,float) or not math.isfinite(gain) or not 0<=gain<=2:raise ValueError('Reflection strength multiplier must be finite in 0..2')
            for index in set(m.draw_global_indices(draw)):colors[index*4+3]=min(255,round(m.vertices.colors[index*4+3]*gain))
    result=patch_dx_attributes(raw,colors=bytes(colors),material_env=env)
    from dataclasses import replace
    from .texture_binding import binding_patch,binding_compatibility
    from .r4e_writer import FieldChange
    data=result.data;receipts=[];changes=list(result.changes)
    for edit in edits:
        bindings=edit.get('bindings',{})
        if not isinstance(bindings,dict):raise ValueError('Invalid texture bindings')
        for slot,target in bindings.items():
            if slot not in ('0','1') or texture_provider is None:raise ValueError('Qualified binding requires slot 0/1 and owned texture provider')
            current=parse_dx_bytes(data);d=next(d for d in current.physical_draws if d.draw_index==edit['draw_id']);s=d.texture_slots[int(slot)]
            receipt=binding_compatibility(current,edit['draw_id'],int(slot),target,texture_provider)
            receipt.update(source_sha256=hashlib.sha256(data).hexdigest(),offset=s.length_offset)
            data=binding_patch(data,edit['draw_id'],int(slot),target,texture_provider)
            receipt.update(output_sha256=hashlib.sha256(data).hexdigest());receipts.append(receipt)
            changes.append(FieldChange('texture_slot_'+slot,edit['draw_id'],s.data_offset,s.raw.hex(),target.encode('ascii').hex()))
    if receipts:
        result=replace(result,data=data,output_sha256=hashlib.sha256(data).hexdigest(),changes=tuple(changes),diff=StructuralBindingAudit(result.diff.to_dict(),tuple(receipts)),classification='MULTIPLE_SAFE_CHANGES')
    parsed=parse_dx_bytes(result.data)
    allowed={i for edit in edits if 'reflection_strength' in edit for i in m.draw_global_indices(next(d for d in m.physical_draws if d.draw_index==edit['draw_id']))}
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(parsed.vertices.colors[3::4],m.vertices.colors[3::4]))):raise ValueError('Unexpected alpha mutation')
    return result
