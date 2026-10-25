"""Rigid rest-pose editing of explicitly qualified existing MR crew components.

Selectors are exact global vertex IDs under a model hash. Native control records,
UVs, colours, collision, draw ordering and skeletal/animation data are untouched.
"""
import hashlib
import math
from .dx import parse_dx_bytes
from .r4e_writer import patch_dx_attributes


def qualify_converted_crew(raw, report, model):
    """Recover selectors from an exact matching existing converter ledger.

    Requires the converter's full output hash and unique part geometry matches;
    names or convenient bounding boxes alone never qualify unknown geometry.
    """
    digest=hashlib.sha256(raw).hexdigest()
    if report['outputs'][model]['sha256']!=digest:raise ValueError('Conversion report does not identify this exact model revision')
    m=parse_dx_bytes(raw);people={};used=set()
    records=[r for r in report['conversion'][model]if r.get('component')=='crew']
    if not records:raise ValueError('Conversion report contains no qualified stock crew')
    for record in records:
        if record.get('route')!='MR stock crew' or not record.get('rigid_fit'):raise ValueError('Unsupported crew provenance')
        candidates=[]
        for d in m.physical_draws:
            ids=sorted(set(m.draw_global_indices(d)))
            if d.draw_index in used or len(ids)!=record['vertices'] or d.index_count//3!=record['triangles'] or list(d.texture_tuple)!=record['textures']:continue
            box=[[f(m.vertices.positions[i][k]for i in ids)for k in range(3)]for f in (min,max)]
            if max(abs(box[a][k]-record['bbox'][a][k])for a in range(2)for k in range(3))<1e-5:candidates.append((d.draw_index,ids))
        if len(candidates)!=1:raise ValueError('Crew component geometry is absent or ambiguous: '+record['role'])
        draw,ids=candidates[0];used.add(draw);who=record['person']
        entry=people.setdefault(who,{'vertices':[],'draws':[],'pivot':[sum(record['person_bbox'][a][k]for a in range(2))/2 for k in range(3)],'role':'stock MR seated '+who,'components':[]})
        entry['vertices'].extend(ids);entry['draws'].append(draw)
        entry['components'].append({'draw':draw,'role':record['role'],'source_draw':record['source_draw'],'source_sha256':record['source_sha256']})
    for p in people.values():p['vertices']=sorted(set(p['vertices']))
    definition={'model_sha256':digest,'people':people,'preset':'Existing stock seated pair from exact converter ledger',
                'evidence':'Full model SHA256 equals converter output; each MR stock crew part uniquely matches textures, vertex/triangle counts and all bounds. Original report SHA256: '+hashlib.sha256(__import__('json').dumps(report,sort_keys=True).encode()).hexdigest()}
    apply_crew_fit(raw,definition,{},source_sha256=digest)
    return definition


def apply_crew_fit(raw, definition, placements, *, source_sha256):
    if hashlib.sha256(raw).hexdigest()!=source_sha256:raise ValueError('Crew source SHA256 mismatch')
    if set(definition)-{'model_sha256','people','evidence','envelope','preset'}:raise ValueError('Unsupported crew definition')
    if not isinstance(definition.get('evidence'),str) or len(definition['evidence'])<12:raise ValueError('Crew needs source qualification evidence')
    people=definition.get('people',{})
    if not people or set(placements)-set(people):raise ValueError('Unknown crew person')
    m=parse_dx_bytes(raw); positions=list(m.vertices.positions); normals=list(m.vertices.normals)
    owners={};reports=[]
    for who,person in people.items():
        if set(person)-{'vertices','pivot','draws','role','components'} or not {'vertices','pivot','draws','role'}<=set(person):raise ValueError('Crew requires vertices, pivot, draws and role')
        ids=person['vertices'];draws=person['draws'];pivot=person['pivot']
        if not isinstance(ids,list) or not ids or ids!=sorted(set(ids)) or any(type(i)is not int or not 0<=i<m.vertex_count for i in ids):raise ValueError('Invalid crew vertex selector')
        if not draws or any(type(d)is not int or d<0 or d>=len(m.physical_draws) for d in draws):raise ValueError('Invalid crew draw selector')
        selected=set(ids);allowed=set()
        for d in m.physical_draws:
            used=set(m.draw_global_indices(d))
            if d.draw_index in draws:
                if d.tag!=2 or d.control_words:raise ValueError('Switch/animation-owned crew is read-only')
                allowed.update(used)
            elif selected & used:raise ValueError('Crew shares vertices with unrelated draw')
        if not selected<=allowed:raise ValueError('Crew vertex outside declared draws')
        if selected & owners.keys():raise ValueError('Crew people share vertices')
        owners.update({i:who for i in ids})
        p=placements.get(who,{'lateral':0,'vertical':0,'longitudinal':0,'yaw_degrees':0})
        if set(p)!={'lateral','vertical','longitudinal','yaw_degrees'}:raise ValueError('Crew placement requires XYZ/yaw')
        values=[p[k] for k in ('lateral','vertical','longitudinal','yaw_degrees')]
        if len(pivot)!=3 or any(type(v)not in (int,float) or not math.isfinite(v) for v in values+list(pivot)):raise ValueError('Nonfinite crew transform')
        if any(abs(v)>.5 for v in values[:3]) or abs(values[3])>45:raise ValueError('Crew correction limited to 0.5 m / 45 degrees')
        a=math.radians(values[3]);c,s=math.cos(a),math.sin(a)
        def rotate(q):return (c*q[0]+s*q[2],q[1],-s*q[0]+c*q[2])
        for i in ids:
            if not any(values):continue
            q=rotate(tuple(m.vertices.positions[i][k]-pivot[k] for k in range(3)))
            positions[i]=tuple(q[k]+pivot[k]+values[k] for k in range(3))
            if all(math.isfinite(x) for x in normals[i]):normals[i]=rotate(normals[i])
        box=[[f(positions[i][k] for i in ids) for k in range(3)] for f in (min,max)]
        envelope=definition.get('envelope');outside=[]
        if envelope:
            if len(envelope)!=2 or any(len(q)!=3 for q in envelope) or any(not math.isfinite(v) for q in envelope for v in q) or any(envelope[0][k]>=envelope[1][k] for k in range(3)):raise ValueError('Invalid crew envelope')
            outside=[i for i in ids if any(not envelope[0][k]<=positions[i][k]<=envelope[1][k] for k in range(3))]
        reports.append({'person':who,'role':person['role'],'components':person.get('components',[]),'vertices':len(ids),'draws':draws,'bbox':box,
                        'outside_envelope_vertices':len(outside),'intersection':'Envelope check only; no seat/roof triangle collision guarantee'})
    result=patch_dx_attributes(raw,positions=positions,normals=[q if all(math.isfinite(x)for x in q)else None for q in normals])
    return result.data,reports
