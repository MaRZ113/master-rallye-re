"""Explicit, hash-pinned redistribution into existing native pane alternatives.

No pane is guessed from material names or numeric draw IDs. The editable profile
accounts for every input triangle, including static glass such as lamp lenses.
Broken UV projection is an explicit MR adaptation, not recovered GT damage data.
"""
from dataclasses import replace
import hashlib
from .dx import parse_dx_bytes
from .topology_writer import source_geometry,DrawGeometry,rebuild_topology


def subset(geometry,indices,axes=None):
    used=sorted({v for i in indices for v in geometry.triangles[i]});mapping={v:i for i,v in enumerate(used)}
    vertices=[replace(geometry.vertices[i],source_vertex_id=None,parent_source_vertex_id=geometry.vertices[i].source_vertex_id) for i in used]
    if axes is not None:
        if len(axes)!=2 or axes[0]==axes[1] or any(type(a)is not int or a not in (0,1,2) for a in axes):raise ValueError('Invalid broken UV projection')
        lo=[min(v.position[a] for v in vertices) for a in axes];hi=[max(v.position[a] for v in vertices) for a in axes]
        if min(hi[i]-lo[i] for i in range(2))<=1e-8:raise ValueError('Degenerate pane projection')
        vertices=[replace(v,uvs=(tuple((v.position[a]-lo[k])/(hi[k]-lo[k]) for k,a in enumerate(axes)),),source_vertex_id=None,parent_source_vertex_id=v.parent_source_vertex_id) for v in vertices]
    return DrawGeometry(tuple(vertices),tuple(tuple(mapping[v] for v in geometry.triangles[i]) for i in indices))


def redistribute_glass(raw,profile):
    if hashlib.sha256(raw).hexdigest()!=profile['source_sha256']:raise ValueError('Glass profile source SHA256 mismatch')
    m=parse_dx_bytes(raw);geometry=source_geometry(m);source_id=profile['source_draw'];source=geometry[source_id]
    allocated=[];targets=[]
    for pane in profile['panes']:
        allocated.extend(pane['triangles']);targets.extend([pane['intact_draw'],pane['broken_draw']])
        group=next((g for g in m.draw_groups if g.root.group_label==pane['label']),None)
        if group is None or set(group.draw_indices)!={pane['intact_draw'],pane['broken_draw']}:raise ValueError('Profile does not match native pane group')
        if group.root.control_words[:3]!=(2,2,8):raise ValueError('Unsupported native glass switch')
        for d in (m.physical_draws[pane['intact_draw']],m.physical_draws[pane['broken_draw']]):
            case=d.control_words[3] if d.tag==7 else d.control_words[0]
            if case!=(1 if d.draw_index==pane['intact_draw'] else 2):raise ValueError('Native pane case mismatch')
    static=profile['static'];allocated.extend(static['triangles']);targets.append(static['draw'])
    if any(type(i)is not int for i in allocated+targets):raise ValueError('Triangle/draw identifiers must be integers')
    if sorted(allocated)!=list(range(len(source.triangles))) or len(targets)!=len(set(targets)):raise ValueError('Glass allocation must cover every triangle exactly once with independent target draws')
    # Only replace explicit hidden fillers; source draw is the intentional exception.
    for target in targets:
        if target!=source_id and len(geometry[target].triangles)!=1:raise ValueError('Refusing to replace non-filler geometry')
    destination=m.physical_draws[static['draw']];prototype=m.physical_draws[source_id]
    if destination.tag!=2:raise ValueError('Static glass target must be an ordinary independent draw')
    # Native records hold inline length-prefixed strings. Copy the complete
    # qualified material tail; preserve target tag and geometric span fields.
    material=raw[prototype.core_offset+20:prototype.terminal_offset+4]
    prepared=raw[:destination.core_offset+20]+material+raw[destination.terminal_offset+4:]
    if not parse_dx_bytes(prepared).diagnostics.validated:raise ValueError('Static material copy failed validation')
    edits={static['draw']:subset(source,static['triangles'])}
    for pane in profile['panes']:
        edits[pane['intact_draw']]=subset(source,pane['triangles'])
        edits[pane['broken_draw']]=subset(source,pane['triangles'],pane['broken_uv_axes'])
    result=rebuild_topology(prepared,edits,bounds_mode='preserve')
    after=source_geometry(result.output_model)
    for d,g in geometry.items():
        if d not in targets:
            # Source IDs change with repacking; compare actual attributes/triangles.
            if [(v.position,v.normal,v.color,v.uvs) for v in after[d].vertices]!=[(v.position,v.normal,v.color,v.uvs) for v in g.vertices] or after[d].triangles!=g.triangles:raise ValueError('Unrelated geometry changed')
    return result.data,{'source_sha256':profile['source_sha256'],'output_sha256':hashlib.sha256(result.data).hexdigest(),'input_triangles':len(source.triangles),'static_triangles':len(static['triangles']),'panes':[{k:v for k,v in pane.items() if k!='triangles'}|{'triangles':len(pane['triangles'])} for pane in profile['panes']],'outside_target_geometry_preserved':True,'approximation':'MR stock broken texture with per-pane planar UVs; not GT cracked-glass reconstruction','runtime_qualified':False}
