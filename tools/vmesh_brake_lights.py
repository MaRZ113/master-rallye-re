"""Bind source lit surfaces to an existing, verified native brake switch.

No new switch records, controller hooks, timer, physics or permanent emission.
The current admitted stock layout is blight: case1 one draw, case2 two draws
(opaque light plus alpha halo). Physical-parser parentage alone omits that
last material draw; stock TXT and case material counts are also required.
"""
from __future__ import annotations
import dataclasses
import math
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import CompiledVertex,DrawGeometry,source_geometry,rebuild_topology


def switch_layout(model,label='blight'):
    matches=[d for d in model.physical_draws if d.group_label==label]
    if len(matches)!=1:raise ValueError('requires one native brake switch')
    root=matches[0];draws=model.physical_draws;i=root.draw_index
    if root.tag!=7 or root.control_words!=(2,2,8,1,1):raise ValueError('unverified brake switch root layout')
    if len(draws)<=i+2:raise ValueError('brake state material draws absent')
    lit,glow=draws[i+1:i+3]
    if lit.tag!=8 or lit.control_words!=(2,2) or glow.tag!=2:raise ValueError('unverified brake state2 material span')
    if [lit.texture_slots[0].value,glow.texture_slots[0].value]!=['breaklightson-tga','breaklightsonglow-tga']:
        raise ValueError('unverified stock brake materials')
    if tuple(lit.flags_0x20[:2])!=(0,0) or tuple(glow.flags_0x20[:2])!=(1,0):raise ValueError('native brake material gates changed')
    return {'label':label,'case1':[i],'case2':[i+1,i+2],
            'logical_span_evidence':'stock case2 material count2 and TXT BRAKELIGHTSon mesh span',
            'native_controller':'gaSFXBrakeLights selects case2 above brake threshold0.1, otherwise case1'}


def bind(data,stock_bytes,faces,transform,*,label='blight',surface_offset=.001):
    if not math.isfinite(surface_offset) or not 0<surface_offset<=.003:
        raise ValueError('brake lens offset must be finite and in (0,.003]')
    model,stock=parse_dx_bytes(data),parse_dx_bytes(stock_bytes)
    layout=switch_layout(stock,label)
    if switch_layout(model,label)['case2']!=layout['case2']:raise ValueError('candidate brake layout differs')
    source=[(fi,t) for fi,(o,m,t) in enumerate(faces) if '_tail_lamp_on' in o and 'reflection' not in o and m.startswith('Mat2')]
    if not source:raise ValueError('no explicit source lit lamp geometry')
    groups={-1:[],1:[]}
    for fi,t in source:
        sign=-1 if sum(transform(c[0])[0] for c in t)<0 else 1;groups[sign].append((fi,t))
    if any(not group for group in groups.values()):raise ValueError('requires paired source brake lamps')
    old=source_geometry(model);reference=source_geometry(stock);lit_id,halo_id=layout['case2']
    verts,tris=[],[];targets={};source_faces=[]
    for sign,group in groups.items():
        points=[transform(c[0]) for fi,t in group for c in t]
        lo=[min(p[k] for p in points) for k in range(3)];hi=[max(p[k] for p in points) for k in range(3)]
        if min(hi[k]-lo[k] for k in (0,1))<.005:raise ValueError('source brake patch has insufficient area')
        targets[sign]=(lo,hi)
        for fi,t in group:
            off=len(verts);ps=[transform(c[0]) for c in t]
            for corner,p in zip(t,ps):
                uv=((p[0]-lo[0])/(hi[0]-lo[0]),(p[1]-lo[1])/(hi[1]-lo[1]))
                # Native rear is -Z. Offset outward from the existing tail lens.
                if corner[1] is not None:
                    origin=transform((0,0,0));nn=transform(corner[1]);normal=tuple(a-b for a,b in zip(nn,origin))
                    length=math.sqrt(sum(v*v for v in normal));normal=tuple(v/length for v in normal) if length>1e-12 else (0,0,-1)
                else:normal=(0,0,-1)
                verts.append(CompiledVertex((p[0],p[1],p[2]-surface_offset),normal,bytes((255,255,255,255)),(uv,)))
            tris.append((off,off+1,off+2));source_faces.append(fi)
    hv=[];ref_lit=reference[lit_id]
    for v in reference[halo_id].vertices:
        sign=-1 if v.position[0]<0 else 1
        rp=[p.position for p in ref_lit.vertices if p.position[0]*sign>0]
        rl=[min(p[k] for p in rp) for k in range(3)];rh=[max(p[k] for p in rp) for k in range(3)]
        lo,hi=targets[sign]
        scales=[(hi[k]-lo[k])/(rh[k]-rl[k]) for k in (0,1)]
        scales.append(min(scales))
        pos=tuple((lo[k]+hi[k])/2+(v.position[k]-(rl[k]+rh[k])/2)*scales[k] for k in range(3))
        normal=tuple(v.normal[k]/scales[k] for k in range(3))
        length=math.sqrt(sum(n*n for n in normal))
        normal=tuple(n/length for n in normal) if length>1e-12 else (0,0,-1)
        hv.append(dataclasses.replace(v,position=(pos[0],pos[1],pos[2]-surface_offset),normal=normal,source_vertex_id=None,parent_source_vertex_id=None))
    edits={lit_id:DrawGeometry(tuple(verts),tuple(tris)),halo_id:DrawGeometry(tuple(hv),reference[halo_id].triangles)}
    result=rebuild_topology(data,edits,bounds_mode='recompute')
    if switch_layout(parse_dx_bytes(result.data),label)!=layout:raise ValueError('brake switch metadata drift')
    return result.data,{'method':'source lit patches plus stock halo mapped into existing native case2',
                        'switch':layout,'source_lit_faces':source_faces,'surface_offset_m':surface_offset,
                        'lit_triangles':len(tris),'halo_triangles':len(reference[halo_id].triangles),
                        'case1':'existing static tail lamp remains; switch filler retained',
                        'runtime_status':'native controller binding verified statically; human braking test pending',
                        'rebuild':result.to_dict()}
