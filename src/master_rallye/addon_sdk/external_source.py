"""Structural OBJ/MTL input inspection shared by external vehicle adapters.

Material names and alpha bytes are evidence, never engine render-state classes.
No GT assets, executable tooling or model-specific material numbers are bundled.
"""
from pathlib import Path
from collections import Counter
import hashlib,math
from ..texture_authoring import decode_rgba_png

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inspect_obj(path):
    path=Path(path).resolve();root=path.parent;arrays={'v':[],'vt':[],'vn':[]};faces=[];materials={};obj='';material=None
    for line in path.with_suffix('.mtl').read_text(encoding='utf-8').splitlines():
        p=line.split()
        if not p:continue
        if p[0]=='newmtl':material=p[1];materials[material]={'coefficients':{},'texture':None}
        elif p[0] in ('Ka','Kd','Ks','Ke','d','Tr') and material:
            values=[float(x) for x in p[1:]]
            if not all(math.isfinite(x) for x in values):raise ValueError('nonfinite MTL coefficient')
            materials[material]['coefficients'][p[0]]=values
        elif p[0]=='map_Kd' and material:
            tex=(root/' '.join(p[1:])).resolve()
            if root not in tex.parents:raise ValueError('texture escapes source root')
            w,h,rgba=decode_rgba_png(tex.read_bytes());alpha=Counter(rgba[3::4])
            materials[material]['texture']={'relative_path':tex.relative_to(root).as_posix(),'sha256':digest(tex),'dimensions':[w,h],'alpha_histogram':dict(sorted(alpha.items()))}
    lines=path.read_text(encoding='utf-8').splitlines()
    for line in lines:
        p=line.split()
        if p and p[0] in arrays:
            tag=p[0];values=tuple(float(x) for x in p[1:3 if tag=='vt' else 4])
            if len(values)!=(2 if tag=='vt' else 3) or not all(math.isfinite(x) for x in values):raise ValueError('invalid source attribute')
            arrays[tag].append(values)
    material=None;seen=Counter();forward=0
    for line in lines:
        p=line.split()
        if not p:continue
        tag=p[0]
        if tag in arrays:
            seen[tag]+=1
        elif tag in ('o','g'):obj=' '.join(p[1:])
        elif tag=='usemtl':
            material=' '.join(p[1:])
            if material not in materials:raise ValueError('unresolved source material '+material)
        elif tag=='f':
            if material is None or len(p)<4:raise ValueError('face lacks material or corners')
            corners=[]
            for token in p[1:]:
                ids=token.split('/');corner=[]
                for k,key in enumerate(('v','vt','vn')):
                    value=int(ids[k]) if k<len(ids) and ids[k] else None
                    if value==0:raise ValueError('OBJ index zero')
                    idx=(value-1 if value and value>0 else seen[key]+value) if value else None
                    if idx is not None and not 0<=idx<len(arrays[key]):raise ValueError('OBJ index out of range')
                    if value and value>seen[key]:forward+=1
                    corner.append(idx)
                corners.append(corner)
            faces.extend((obj,material,(corners[0],corners[i],corners[i+1])) for i in range(1,len(corners)-1))
    if not faces:raise ValueError('empty source mesh')
    used=[arrays['v'][c[0]] for _,_,t in faces for c in t]
    return {'status':'STRUCTURE_VALIDATED_MATERIAL_SEMANTICS_UNQUALIFIED','obj_sha256':digest(path),'mtl_sha256':digest(path.with_suffix('.mtl')),
        'attributes':{k:len(v) for k,v in arrays.items()},'forward_attribute_references':forward,'triangles':len(faces),'objects':dict(Counter(o for o,m,t in faces)),
        'material_triangles':dict(Counter(m for o,m,t in faces)),'materials':materials,'bounds':[[min(p[k] for p in used),max(p[k] for p in used)] for k in range(3)],
        'corners_without_uv':sum(c[1] is None for _,_,t in faces for c in t),'corners_without_normal':sum(c[2] is None for _,_,t in faces for c in t),
        'uv_outside_unit_square':sum(not(0<=uv[0]<=1 and 0<=uv[1]<=1) for uv in arrays['vt']),
        'opacity_policy':'preserve source alpha histogram; material pass UNKNOWN until source render-state adapter qualifies it; no material-prefix inference'}
