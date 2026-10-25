"""Explicit source-derived occluder keepouts for controlled diagnostic adaptation.

Subtract connected protected-surface AABBs from explicitly selected occluders.
No model IDs, guessed positions, inflated bounds, or automatic shape selection.
"""
from __future__ import annotations
import math


EPS=1e-7

def _interpolate(a,b,t):
    out=dict(a)
    for key in ('position','normal','uv','rgba_ps2'):
        av,bv=a.get(key),b.get(key)
        if av is None and bv is None:continue
        if av is None or bv is None:raise ValueError('keepout cannot interpolate mixed attribute ownership')
        value=tuple(x+(y-x)*t for x,y in zip(av,bv))
        if key=='normal':
            length=math.sqrt(sum(x*x for x in value));value=tuple(x/length for x in value) if length else value
        if key=='rgba_ps2':value=tuple(round(x) for x in value)
        out[key]=value
    return out


def _split(poly,axis,bound,direction):
    inside=[];outside=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da=(a['position'][axis]-bound)*direction;db=(b['position'][axis]-bound)*direction
        ai=da<=EPS;bi=db<=EPS
        (inside if ai else outside).append(a)
        if ai!=bi:
            v=_interpolate(a,b,da/(da-db));inside.append(v);outside.append(v)
    return inside,outside


def _boxes(draw):
    components=[]
    for tri in draw['triangles']:
        points={tuple(draw['vertices'][i]['position']) for i in tri};touch=[i for i,c in enumerate(components) if points&c]
        for i in reversed(touch):points|=components.pop(i)
        components.append(points)
    return [(tuple(min(p[k] for p in c) for k in range(3)),tuple(max(p[k] for p in c) for k in range(3))) for c in components]


def apply_keepouts(draws,selections,source_sha256):
    if not isinstance(selections,list):raise ValueError('visibility keepouts must be an explicit list')
    if not isinstance(source_sha256,str) or len(source_sha256)!=64 or any(c not in '0123456789abcdef' for c in source_sha256):raise ValueError('keepout original source SHA256 required')
    result=list(draws);reports=[]
    for item in selections:
        if not isinstance(item,dict) or set(item)!={'source_sha256','target','protect','role'} or item['source_sha256']!=source_sha256 or not isinstance(item['role'],str) or not item['role']:raise ValueError('keepout needs matching original source pin and explicit role')
        found={}
        for kind in ('target','protect'):
            selector=item[kind]
            if not isinstance(selector,dict) or set(selector)!={'shape','packet'} or any(type(v)is not int or v<0 for v in selector.values()):raise ValueError('invalid keepout source selector')
            matches=[i for i,d in enumerate(result) if d.get('component','body')=='body' and d['source_shape']==selector['shape'] and d['packet']==selector['packet']]
            if len(matches)!=1:raise ValueError('keepout source selector must resolve uniquely')
            found[kind]=matches[0]
        if found['target']==found['protect']:raise ValueError('keepout cannot clip the protected surface')
        target=result[found['target']];protect=result[found['protect']]
        if target['issues'] or protect['issues']:raise ValueError('keepout requires qualified geometry')
        if any(v.get('morph_target') for d in (target,protect) for v in d['vertices']):raise ValueError('keepout morph interpolation is not qualified')
        boxes=_boxes(protect)
        if any(any(hi[k]-lo[k]<=EPS for k in range(3)) for lo,hi in boxes):raise ValueError('keepout protected volume is not closed in all three axes')
        vertices=list(target['vertices']);triangles=[];changed=0
        for tri in target['triangles']:
            pieces=[[target['vertices'][i] for i in tri]];touched=False
            for lo,hi in boxes:
                next_pieces=[]
                for poly in pieces:
                    if any(max(v['position'][k] for v in poly)<lo[k]-EPS or min(v['position'][k] for v in poly)>hi[k]+EPS for k in range(3)):
                        next_pieces.append(poly);continue
                    remainder=poly;outside=[]
                    for axis in range(3):
                        for bound,direction in ((lo[axis],-1),(hi[axis],1)):
                            remainder,piece=_split(remainder,axis,bound,direction)
                            if len(piece)>=3:outside.append(piece)
                            if len(remainder)<3:break
                        if len(remainder)<3:break
                    if len(remainder)>=3:touched=True
                    next_pieces.extend(outside)
                pieces=next_pieces
            if not touched:
                triangles.append(tri);continue
            changed+=1
            for poly in pieces:
                base=len(vertices);vertices.extend(poly)
                for k in range(1,len(poly)-1):triangles.append((base,base+k,base+k+1))
        if not changed:raise ValueError('keepout does not intersect selected source occluder')
        if not triangles:raise ValueError('keepout would remove entire source occluder')
        report={'role':item['role'],'source_sha256':source_sha256,'target':item['target'],'protect':item['protect'],
                'source_triangles':len(target['triangles']),'intersecting_source_triangles':changed,'output_triangles':len(triangles),
                'protected_component_boxes':[{'min':lo,'max':hi} for lo,hi in boxes],
                'boundary':'Explicit diagnostic MR adaptation: only occluder geometry inside source-derived closed lamp bounds is subtracted. Original source is retained; no claimed original GT4 renderer parity.'}
        result[found['target']]={**target,'vertices':vertices,'triangles':triangles,'_mr_visibility_keepout':report};reports.append(report)
    return result,reports


def append_source_housings(draws,selections,source_sha256):
    """Explicit dark housings or rear-only caps from aperture/interior bounds.

    This creates documented MR occlusion geometry, not recovered GT geometry.
    """
    if not isinstance(selections,list):raise ValueError('source housings require explicit selections')
    if not isinstance(source_sha256,str) or len(source_sha256)!=64 or any(c not in '0123456789abcdef' for c in source_sha256):raise ValueError('source housing original source SHA256 required')
    result=list(draws);reports=[]
    faces=[(0,False,(0,2,6,4)),(0,True,(1,5,7,3)),(1,False,(0,4,5,1)),(1,True,(2,3,7,6)),(2,False,(0,1,3,2)),(2,True,(4,6,7,5))]
    for item in selections:
        if not isinstance(item,dict) or set(item)-{'mode'}!={'source_sha256','aperture','interior','front_axis','front_sign','role'} or item.get('mode','open_box') not in ('open_box','rear_cap') or item['source_sha256']!=source_sha256 or type(item['front_axis'])is not int or item['front_axis'] not in (0,1,2) or type(item['front_sign'])is not int or item['front_sign'] not in (-1,1) or not isinstance(item['role'],str) or not item['role']:raise ValueError('invalid source housing declaration')
        selected={}
        for kind in ('aperture','interior'):
            selector=item[kind]
            if not isinstance(selector,dict) or set(selector)!={'shape','packet'} or any(type(v)is not int or v<0 for v in selector.values()):raise ValueError('invalid source housing selector')
            matches=[d for d in draws if d.get('component','body')=='body' and d['source_shape']==selector['shape'] and d['packet']==selector['packet']]
            if len(matches)!=1 or matches[0]['issues']:raise ValueError('source housing geometry is not uniquely qualified')
            selected[kind]=matches[0]
            if any(v.get('morph_target') for v in matches[0]['vertices']):raise ValueError('source housing morph geometry is not qualified')
        interiors=_boxes(selected['interior']);boxes=[];axis=item['front_axis']
        for lo,hi in _boxes(selected['aperture']):
            matches=[(il,ih) for il,ih in interiors if all(min(hi[k],ih[k])-max(lo[k],il[k])>EPS for k in range(3) if k!=axis)]
            if len(matches)!=1:raise ValueError('source housing component correspondence is ambiguous')
            il,ih=matches[0];boxes.append((tuple(min(lo[k],il[k]) for k in range(3)),tuple(max(hi[k],ih[k]) for k in range(3))))
        vertices=[];triangles=[]
        for lo,hi in boxes:
            if any(hi[k]-lo[k]<=EPS for k in range(3)):raise ValueError('source housing has no closed depth')
            corners=[tuple((hi[k] if (i>>k)&1 else lo[k]) for k in range(3)) for i in range(8)]
            for face_axis,high,ids in faces:
                if face_axis==axis and high==(item['front_sign']>0):continue
                if item.get('mode','open_box')=='rear_cap' and face_axis!=axis:continue
                normal=tuple(((-1 if high else 1) if k==face_axis else 0) for k in range(3));base=len(vertices)
                vertices.extend({'position':corners[i],'normal':normal,'uv':None,'rgba_ps2':(0,0,0,128)} for i in ids)
                triangles.extend(((base,base+1,base+2),(base,base+2,base+3)))
        report={'role':item['role'],'source_sha256':source_sha256,'aperture':item['aperture'],'interior':item['interior'],
                'mode':item.get('mode','open_box'),'source_component_boxes':[{'min':lo,'max':hi} for lo,hi in boxes],'generated_triangles':len(triangles),
                'boundary':'Explicit MR occlusion approximation from source glass and lens bounds. rear_cap retains only the rear plane, preventing AABB sidewalls from protruding through sloped fascia. No source asset edits or renderer-parity claim.'}
        source=selected['interior'];state={**source['state'],'alpha_test':False,'depth_write':True,'fbmask':0,'date':False}
        result.append({**source,'component':'derived_housing','vertices':vertices,'triangles':triangles,'texture':None,'gif':{**source['gif'],'blend':False,'textured':False},'state':state,'issues':[],'_mr_source_housing':report});reports.append(report)
    return result,reports
