"""Explicit source-hash-qualified native lamp/pane state authoring.

No vehicle-name heuristics: callers select every source triangle and texture.
Intact/off geometry, attributes and native collision are checked independently.
"""
from collections import Counter
from dataclasses import replace
import hashlib,struct
from ..dx import parse_dx_bytes
from ..topology_writer import source_geometry
from ..glass_authoring import subset
from ..scene_dx_writer import ScenePart,write_scene_dx


def wrap_states(template,items):
    """Items are SceneParts or (qualified native label, case1, case2)."""
    parts=[];starts={};labels=set()
    for item in items:
        if isinstance(item,ScenePart):parts.append(item);continue
        label,off,on=item
        if label not in ('blight','screenfront','screenrear','screenleft','screenright')or label in labels:raise ValueError('Unqualified/duplicate native state label')
        if not off or not on or max(len(off),len(on))>17:raise ValueError('Unqualified native state span')
        if label!='blight' and (len(off)!=1 or len(on)!=1):raise ValueError('Glass zones require one draw per case')
        labels.add(label);starts[len(parts)]=(label,len(off));starts[len(parts)+len(off)]=(None,len(on));parts+=off+on
    flat=write_scene_dx(template,parts,allow_unlit=True);m=parse_dx_bytes(flat);records=[]
    for index,d in enumerate(m.physical_draws):
        core=flat[d.core_offset:d.offset+d.own_size]
        if index in starts:
            label,count=starts[index]
            if label is None:core=struct.pack('<3I',8,2,count)+core
            else:
                text=label.encode('ascii');core=struct.pack('<II',7,len(text))+text+struct.pack('<5I',2,2,8,1,count)+core
        records.append(core)
    data=flat[:m.draw_table_offset]+struct.pack('<2I',1,len(items))+b''.join(records)+flat[m.global_index_table.preamble_offset:]
    output=parse_dx_bytes(data)
    if not output.diagnostics.validated or output.declared_top_level_record_count!=len(items):raise ValueError('Native state serialization failed')
    from ..preview_scene import logical_cases
    logical_cases(output)
    return data


def author_states(raw,profile):
    if not isinstance(profile,dict) or 'source_sha256'not in profile or set(profile)-{'source_sha256','panes','brake'}:raise ValueError('Unknown native state recipe keys')
    if hashlib.sha256(raw).hexdigest()!=profile['source_sha256']:raise ValueError('Native feature source SHA256 mismatch')
    m=parse_dx_bytes(raw);geometry=source_geometry(m)
    if any(d.tag!=2 for d in m.physical_draws):raise ValueError('Native source already has controls; preserve/inspect instead of layering twice')
    prototype=m.physical_draws[0]
    state_words=lambda d:(d.unknown_0x14,d.unknown_0x18,d.unknown_0x1c_float)
    if any(state_words(d)!=state_words(prototype)or raw[d.terminal_offset:d.terminal_offset+4]!=b'\0'*4 for d in m.physical_draws):raise ValueError('Unqualified differing native material prefix/terminal words')
    def part(index,triangles=None):
        if type(index)is not int or not 0<=index<len(m.physical_draws):raise ValueError('Native feature source draw outside bounds')
        d=m.physical_draws[index]
        if len(d.texture_tuple)!=3 or tuple(d.flags_0x20)not in ((0,0,1,1),(1,0,1,1),(1,1,1,1))or d.unknown_0x24 not in (3,7)or d.texture_tuple[2]!='Null':raise ValueError('Unqualified source material for native state repack')
        g=geometry[index];g=subset(g,list(range(len(g.triangles)))if triangles is None else triangles)
        return ScenePart(g,d.texture_tuple,bool(d.flags_0x20[0]),bool(d.flags_0x20[1]),bool(d.unknown_0x24&4),True)
    allocations={};special=[];off_parts=[];reports={}
    for pane in profile.get('panes',[]):
        if set(pane)!={'label','source_draw','triangles','broken_uv_axes','broken_texture'}:raise ValueError('Invalid native pane recipe')
        label=pane['label'];index=pane['source_draw'];ids=pane['triangles']
        part(index,ids)
        if label not in ('screenfront','screenrear','screenleft','screenright'):raise ValueError('Unknown pane zone')
        allocated=allocations.setdefault(index,[])
        if not ids or any(type(i)is not int or not 0<=i<len(geometry[index].triangles)for i in ids)or set(allocated)&set(ids)or len(ids)!=len(set(ids)):raise ValueError('Invalid/overlapping native pane selection')
        allocated+=ids;intact=part(index,ids);broken=replace(intact,geometry=subset(geometry[index],ids,pane['broken_uv_axes']),textures=(pane['broken_texture'],intact.textures[1],'Null'))
        special.append((label,[intact],[broken]));off_parts.append(intact);reports[label]={'source_draw':index,'triangles':ids,'broken_uv':'Explicit planar native MR approximation'}
    lamp=profile.get('brake')
    if lamp:
        required={'source_draw','triangles','lit_texture','glow_texture','evidence'}
        if not required<=set(lamp) or set(lamp)-required-{'mode'} or not isinstance(lamp['evidence'],str)or not lamp['evidence'].strip():raise ValueError('Native lamp source evidence required')
        mode=lamp.get('mode','replace')
        if mode not in ('replace','masked_overlay'):raise ValueError('Unknown native lamp rendering mode')
        index=lamp['source_draw'];ids=lamp['triangles'];part(index,ids);allocated=allocations.setdefault(index,[])
        if not ids or len(ids)!=len(set(ids))or any(type(i)is not int or not 0<=i<len(geometry[index].triangles)for i in ids)or set(allocated)&set(ids):raise ValueError('Invalid native lamp selection')
        allocated+=ids;off=part(index,ids);lit=replace(off,textures=(lamp['lit_texture'],'Null','Null'),environment=False,diffuse=False)
        glow=replace(lit,textures=(lamp['glow_texture'],'Null','Null'),alpha=True,alpha_test=False)
        # Explicit masked overlay keeps the underlying original surface lit by
        # the ordinary body pipeline, including large triangles shared by a
        # lens and painted panel. Only the derived atlas coverage emits light.
        on=[lit,glow] if mode=='replace' else [off,replace(lit,alpha=True,alpha_test=True),glow]
        special.append(('blight',[off],on));off_parts.append(off);reports['blight']={'source_draw':index,'triangles':ids,'evidence':lamp['evidence'],'mode':mode,'halo':'Source lens geometry only; no enlargement/body spill'}
    body=[]
    for index in range(len(m.physical_draws)):
        remaining=sorted(set(range(len(geometry[index].triangles)))-set(allocations.get(index,[])))
        if remaining:body.append(part(index,remaining))
    if not special:raise ValueError('No explicit native features requested')
    def fingerprints(parts):
        result=Counter()
        for p in parts:
            for t in p.geometry.triangles:
                attrs=tuple((p.geometry.vertices[v].position,p.geometry.vertices[v].normal,p.geometry.vertices[v].color,p.geometry.vertices[v].uvs)for v in t)
                result[(attrs,p.textures,p.alpha,p.alpha_test,p.environment,p.diffuse)]+=1
        return result
    if fingerprints(body+off_parts)!=fingerprints([part(i)for i in range(len(m.physical_draws))]):raise ValueError('Native feature adaptation lost original intact/off triangles or materials')
    output=wrap_states(raw,body+special);new=parse_dx_bytes(output)
    if raw[m.trailing.offset:m.collision.unparsed_offset]!=output[new.trailing.offset:new.collision.unparsed_offset]:raise ValueError('Native feature adaptation changed collision')
    return output,{'status':'PASS_SOURCE_OFF_STATE_EQUIVALENCE','source_sha256':profile['source_sha256'],'output_sha256':hashlib.sha256(output).hexdigest(),'original_triangles':m.triangle_count,'serialized_alternative_triangles':new.triangle_count,'collision_preserved':True,'intact_off_geometry_normals_uv_materials_identical':True,'states':reports,'runtime_qualified':False}


def validate_state_scene(template,data):
    """Admit a writer scene wrapped by `wrap_states` (blight + glass zones).

    Control prefixes are stripped and the flat scene is validated with the
    shared imported-scene rules; logical cases must decode. Collision and
    suffix bytes are checked by the flat validator against the template.
    """
    from ..scene_dx_writer import validate_scene_dx
    from ..preview_scene import logical_cases
    m=parse_dx_bytes(data)
    if not m.diagnostics.validated:raise ValueError('invalid native state scene')
    labels=[g.root.group_label for g in m.draw_groups if g.root.tag==7]
    if not labels or len(set(labels))!=len(labels) or set(labels)-{'blight','screenfront','screenrear','screenleft','screenright'}:raise ValueError('unqualified native state labels')
    records=[]
    for d in m.physical_draws:
        if d.tag not in (2,7,8):raise ValueError('unexpected native scene control')
        records.append(data[d.core_offset:d.offset+d.own_size])
    flat=data[:m.draw_table_offset]+struct.pack('<2I',1,len(records))+b''.join(records)+data[m.global_index_table.preamble_offset:]
    result=validate_scene_dx(template,flat,allow_unlit=True);logical_cases(m)
    return {**result,'grammar':'native state scene','labels':sorted(labels),'runtime_qualified':False}
