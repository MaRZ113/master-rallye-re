"""Bounded transfer of an inspected native brake halo, never body geometry.

The donor's switch, topology, UVs, colors and material flags are preserved.
Two disconnected lamp components are fitted independently with uniform scale
in the unchanged MR frame. This is explicit authoring, not donor provenance.
"""
from dataclasses import replace
import hashlib
from ..dx import parse_dx_bytes
from ..topology_writer import source_geometry,DrawGeometry
from ..scene_dx_writer import ScenePart
from ..preview_scene import logical_cases
from ..glass_authoring import subset


def _components(g):
    owners={};parent=list(range(len(g.triangles)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,t in enumerate(g.triangles):
        for v in t:
            p=g.vertices[v].position
            if p in owners:parent[find(i)]=find(owners[p])
            owners[p]=i
    groups={}
    for i in range(len(parent)):groups.setdefault(find(i),[]).append(i)
    return [subset(g,ids)for ids in groups.values()]


def _bounds(g):
    return [[min(v.position[k]for v in g.vertices)for k in range(3)],
            [max(v.position[k]for v in g.vertices)for k in range(3)]]


def reference_brake_glow(source,donor,selection,*,texture_aliases=None):
    a=parse_dx_bytes(source);b=parse_dx_bytes(donor)
    if not a.diagnostics.validated or not b.diagnostics.validated:raise ValueError('Reference effects need valid native inputs')
    cases,_=logical_cases(b);bg=source_geometry(b);ag=source_geometry(a)
    off=[d for d in b.physical_draws if cases.get(d.draw_index)==(1,1)]
    halos=[d for d in b.physical_draws if cases.get(d.draw_index)==(1,2)and d.flags_0x20[0]and not d.flags_0x20[2]]
    lit=[d for d in b.physical_draws if cases.get(d.draw_index)==(1,2)and not d.flags_0x20[0]and not d.flags_0x20[2]]
    if len(off)!=1 or len(halos)!=1 or len(lit)!=1:raise ValueError('Unsupported native brake reference span')
    halo=halos[0]
    prefix=lambda d:(d.unknown_0x14,d.unknown_0x18,d.unknown_0x1c_float)
    if any(prefix(d)!=prefix(a.physical_draws[0])for d in (halo,lit[0],off[0])):raise ValueError('Unqualified donor/source material prefix difference')
    if halo.triangle_count>128 or off[0].triangle_count>128:raise ValueError('Reference effect geometry budget')
    draw=selection['source_draw'];ids=selection['triangles']
    if len(ids)>256 or len(set(ids))!=len(ids)or draw not in ag:raise ValueError('Invalid source lens selection')
    target=_components(subset(ag[draw],ids));lenses=_components(bg[off[0].draw_index]);glows=_components(bg[halo.draw_index])
    if any(len(parts)!=2 for parts in (target,lenses,glows)):raise ValueError('Reference requires exactly two disconnected lenses and halos')
    key=lambda g:sum(v.position[0]for v in g.vertices)/len(g.vertices)
    target.sort(key=key);lenses.sort(key=key);glows.sort(key=key)
    if any(not key(parts[0])<0<key(parts[1])for parts in (target,lenses,glows)):raise ValueError('Ambiguous lamp side ownership')
    vertices=[];triangles=[];measurements=[]
    for dst,lens,glow in zip(target,lenses,glows):
        db,lb=_bounds(dst),_bounds(lens)
        spans=[lb[1][k]-lb[0][k]for k in (0,1)]
        if min(spans)<=1e-6:raise ValueError('Degenerate donor lens projection')
        scale=min((db[1][k]-db[0][k])/spans[k]for k in (0,1))
        if not .25<=scale<=4:raise ValueError('Reference lens fit outside explicit authoring budget')
        anchor=lambda box:[(box[0][k]+box[1][k])/2 if k<2 else box[0][k]for k in range(3)]
        da,la=anchor(db),anchor(lb);start=len(vertices)
        vertices.extend(replace(v,position=tuple(da[k]+scale*(v.position[k]-la[k])for k in range(3)))for v in glow.vertices)
        triangles.extend(tuple(start+i for i in t)for t in glow.triangles)
        measurements.append({'source_lens_bounds':db,'donor_lens_bounds':lb,'uniform_scale':scale,'source_anchor':da,'donor_anchor':la})
    aliases=texture_aliases or {}
    if not isinstance(aliases,dict)or 'Null'in aliases or any(not isinstance(k,str)or not isinstance(v,str)for k,v in aliases.items()):raise ValueError('Invalid reference texture aliases')
    textures=tuple(aliases.get(n,n)for n in halo.texture_tuple)
    part=ScenePart(DrawGeometry(tuple(vertices),tuple(triangles)),textures,
                   bool(halo.flags_0x20[0]),bool(halo.flags_0x20[1]),bool(halo.unknown_0x24&4),bool(halo.flags_0x20[2]))
    return part,{'donor_sha256':hashlib.sha256(donor).hexdigest(),'donor_off_draw':off[0].draw_index,'donor_glow_draw':halo.draw_index,
                 'donor_textures':list(halo.texture_tuple),'output_textures':list(textures),'triangles':len(triangles),'fits':measurements,
                 'donor_lit_draw':lit[0].draw_index,
                 'lit_material':{'alpha':bool(lit[0].flags_0x20[0]),'alpha_test':bool(lit[0].flags_0x20[1]),'environment':bool(lit[0].unknown_0x24&4),'diffuse':bool(lit[0].flags_0x20[2]),'secondary_texture':aliases.get(lit[0].texture_tuple[1],lit[0].texture_tuple[1])},
                 'preserved':['glow topology','UV','normal','vertex color','material flags'],'boundary':'Explicit uniform lens-fit MR adaptation; not original donor-game or source vehicle glow equivalence.'}


def reference_brake_lit(donor,report,*,texture_aliases=None):
    """Transfer the actual ON core with the halo's SAME qualified per-side fit.

    Keep the source OFF lens below this separate native core. A brightened
    source atlas cannot reproduce a donor ON texture's white hot centre.
    """
    if hashlib.sha256(donor).hexdigest()!=report['donor_sha256']:raise ValueError('Reference lamp donor changed')
    model=parse_dx_bytes(donor);draw=model.physical_draws[report['donor_lit_draw']]
    cases,_=logical_cases(model)
    if cases.get(draw.draw_index)!=(1,2)or draw.flags_0x20[0]or draw.flags_0x20[2]:raise ValueError('Reference ON core must be opaque/unlit')
    parts=_components(source_geometry(model)[draw.draw_index]);parts.sort(key=lambda g:sum(v.position[0]for v in g.vertices)/len(g.vertices))
    if len(parts)!=2 or len(report['fits'])!=2:raise ValueError('Ambiguous reference ON core components')
    vertices=[];triangles=[]
    for part,fit in zip(parts,report['fits']):
        scale=fit['uniform_scale'];a,b=fit['source_anchor'],fit['donor_anchor'];start=len(vertices)
        if not .25<=scale<=4:raise ValueError('Reference core fit outside budget')
        vertices.extend(replace(v,position=tuple(a[k]+scale*(v.position[k]-b[k])for k in range(3)))for v in part.vertices)
        triangles.extend(tuple(start+i for i in t)for t in part.triangles)
    aliases=texture_aliases or {}
    return ScenePart(DrawGeometry(tuple(vertices),tuple(triangles)),tuple(aliases.get(n,n)for n in draw.texture_tuple),
                     bool(draw.flags_0x20[0]),bool(draw.flags_0x20[1]),bool(draw.unknown_0x24&4),bool(draw.flags_0x20[2]))
