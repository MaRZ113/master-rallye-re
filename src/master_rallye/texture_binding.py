"""Variable-length native texture references; texture pixels remain untouched.

The 135/1337 loader reads length-prefixed strings sequentially. Rebuild only
the selected descriptor, retain the suffix verbatim, then verify native semantics.
"""
import re
import struct
from .dx import parse_dx_bytes
from .dxt import parse_dxt_bytes


def alpha_kind(texture):
    alpha=texture.bgra[3::4]
    if all(v==255 for v in alpha):return 'opaque'
    if any(0<v<255 for v in alpha):return 'continuous'
    return 'binary'


def binding_compatibility(model,draw_id,slot_id,target,texture_provider):
    if type(slot_id)is not int or slot_id not in (0,1):raise ValueError('Only diffuse slot 0 and existing opaque environment slot 1 are qualified')
    if not isinstance(target,str) or not re.fullmatch(r'[A-Za-z0-9_ -]{1,255}',target) or target.casefold()=='null':raise ValueError('Target must be a local existing texture stem')
    draw=next((d for d in model.physical_draws if d.draw_index==draw_id),None)
    if draw is None or type(draw_id)is not int:raise ValueError('Unknown physical draw ID')
    slot=draw.texture_slots[slot_id]
    if not slot.value or slot.value.casefold()=='null':raise ValueError('Cannot activate an absent native texture stage')
    if draw.unknown_0x24&~7:raise ValueError('Special shader feature bits are not qualified for rebinding')
    if slot_id==0 and not (draw.unknown_0x24&1 and draw.flags_0x20[3]):raise ValueError('Source has no qualified textured UV diffuse stage')
    if slot_id==1 and (not draw.unknown_0x24&4 or draw.flags_0x20[0]):raise ValueError('Environment rebinding requires an existing opaque environment stage')
    if any(draw_id in g.draw_indices and g.root.tag==7 for g in model.draw_groups):raise ValueError('Native switch-owned light/glass requires coordinated state authoring')
    old,new=(parse_dxt_bytes(texture_provider(name)) for name in (slot.value,target))
    if old.word_0x04!=new.word_0x04 or new.word_0x04!=1:raise ValueError('Unqualified FEED format/version')
    if new.width&(new.width-1) or new.height&(new.height-1):raise ValueError('Qualified SDK texture dimensions must be powers of two')
    if new.width*new.height*4>16*1024*1024:raise ValueError('Target exceeds the SDK 16 MiB per-texture authoring budget; not a claimed engine limit')
    warnings=[]
    if draw.flags_0x20[0]:
        if draw.flags_0x20[1]:
            if min(old.bgra[3::4])<=128<max(old.bgra[3::4]) and not min(new.bgra[3::4])<=128<max(new.bgra[3::4]):raise ValueError('Cutout target must retain discarded and visible coverage at native threshold 128')
            warnings.append('Cutout coverage changes; native threshold and UVs stay unchanged')
        else:
            if alpha_kind(old)!=alpha_kind(new):raise ValueError('Blended target changes opacity class; use explicit coverage authoring')
            warnings.append('Blended opacity distribution changes; alpha/depth flags stay unchanged')
    elif draw.unknown_0x24&4:warnings.append('Opaque environment material: target alpha can change reflection weighting, not enable transparency')
    else:warnings.append('Opaque diffuse material: target alpha does not enable blend/test')
    if (old.width,old.height)!=(new.width,new.height):warnings.append('Different resolution; normalized UVs preserved without resampling')
    return {'draw':draw_id,'slot':slot_id,'current':slot.value,'target':target,'width':new.width,'height':new.height,'alpha_kind':alpha_kind(new),'warnings':warnings}


def binding_patch(raw,draw_id,slot_id,target,texture_provider):
    model=parse_dx_bytes(raw)
    if not model.diagnostics.validated or (model.word_0x04,model.word_0x08)!=(135,1337):raise ValueError('Requires qualified revision 135/1337 DX')
    draw=next((d for d in model.physical_draws if d.draw_index==draw_id),None)
    if draw is None or type(slot_id)is not int or slot_id not in (0,1):raise ValueError('Unknown draw or unsupported native slot')
    slot=draw.texture_slots[slot_id];start=slot.length_offset;end=slot.data_offset+len(slot.raw)
    for other in model.physical_draws:
        for descriptor in other.texture_slots:
            if other.draw_index==draw_id and descriptor.slot==slot_id:continue
            if max(start,descriptor.length_offset)<min(end,descriptor.data_offset+len(descriptor.raw)):raise ValueError('Shared or aliased native slot descriptor: assignment rejected')
    binding_compatibility(model,draw_id,slot_id,target,texture_provider)
    encoded=target.encode('ascii');output=raw[:start]+struct.pack('<I',len(encoded))+encoded+raw[end:]
    after=parse_dx_bytes(output)
    if not after.diagnostics.validated or after.diagnostics.warnings!=model.diagnostics.warnings:raise ValueError('Rebuilt DX did not validate')
    if after.vertices!=model.vertices or after.local_indices!=model.local_indices or [u.values for u in after.uv_sets]!=[u.values for u in model.uv_sets]:raise ValueError('Rebinding changed geometry attributes')
    if raw[model.trailing.offset:]!=output[after.trailing.offset:]:raise ValueError('Rebinding changed collision/damage suffix')
    fields=('tag','record_path','group_label','control_words','declared_child_count','vertex_base','local_vertex_max','index_start','index_count','unknown_0x14','unknown_0x18','unknown_0x1c_float','flags_0x20','unknown_0x24')
    if len(after.physical_draws)!=len(model.physical_draws):raise ValueError('Rebinding changed draw count')
    for a,b in zip(model.physical_draws,after.physical_draws):
        expected=list(a.texture_tuple)
        if a.draw_index==draw_id:expected[slot_id]=target
        if any(getattr(a,f)!=getattr(b,f) for f in fields) or tuple(expected)!=b.texture_tuple:raise ValueError('Rebinding changed an unrelated native record')
    return output
