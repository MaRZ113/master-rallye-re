"""Private, profile-driven decal composition and bounded placeholder binding.

No proprietary pixels, texture numbers or vehicle-specific coordinates live here.
Compositions/inputs belong in an ignored authoring directory.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import gtmat


def compose(profile, output: Path):
    w,h=profile['size'];px=bytearray(w*h*4);provenance=[]
    if not 1<=w<=2048 or not 1<=h<=2048:raise ValueError('invalid authored decal dimensions')
    for layer in profile['layers']:
        path=Path(layer['source']);tex=gtmat.GtTexture(path.read_bytes())
        x0,y0,x1,y1=layer.get('crop',[0,0,tex.w,tex.h]);dx,dy,dw,dh=layer['rect']
        if not 0<=x0<x1<=tex.w or not 0<=y0<y1<=tex.h or min(dx,dy)<0 or dx+dw>w or dy+dh>h:raise ValueError('decal crop/placement outside image')
        for y in range(dh):
            for x in range(dw):
                fx=(x+.5)/dw
                if layer.get('flip_x'):fx=1-fx
                sx,sy=min(x1-1,int(x0+fx*(x1-x0))),min(y1-1,int(y0+(y+.5)/dh*(y1-y0)))
                i=(sy*tex.w+sx)*4;r,g,b,a=tex.rgba[i:i+4]
                if layer.get('mask')=='yellow':a=255 if r>95 and g>110 and b<110 else 0
                radius=layer.get('bridge_vertical_pixels',0)
                if layer.get('mask')=='yellow' and not a and radius:
                    matches=[]
                    for direction in (-1,1):
                        found=None
                        for step in range(1,radius+1):
                            yy=sy+direction*step
                            if not y0<=yy<y1:continue
                            q=tex.rgba[(yy*tex.w+sx)*4:(yy*tex.w+sx)*4+3]
                            if q[0]>95 and q[1]>110 and q[2]<110:found=q;break
                        matches.append(found)
                    if all(q is not None for q in matches):
                        r,g,b=(round(sum(q[k] for q in matches)/2) for k in range(3));a=255
                if a>128:
                    if 'tint' in layer:r,g,b=layer['tint']
                    j=((dy+y)*w+dx+x)*4;px[j:j+4]=bytes((r,g,b,255))
        provenance.append({'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                           'crop':[x0,y0,x1,y1],'rect':[dx,dy,dw,dh],'flip_x':bool(layer.get('flip_x')),
                           'mask':layer.get('mask','source alpha'),'tint':layer.get('tint'),
                           'bridge_vertical_pixels':layer.get('bridge_vertical_pixels',0)})
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(gtmat.png_from_rgba(w,h,px))
    return {'method':'explicit private composition of existing source artwork; not an original recovered texture',
            'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'layers':provenance}


def bind_rear_placeholder(gt,classifier,decal:Path):
    grouped={}
    for o,m,t in gt['faces']:
        if classifier._decide(o,m)[0]=='paint':grouped.setdefault(m,[]).extend(c[0] for c in t)
    candidates=[]
    for m,points in grouped.items():
        tex=gtmat.GtTexture(gt['textures'][m].read_bytes())
        if tex.w*tex.h!=1 or tex.alpha!=bytes([0]):continue
        if min(p[2] for p in points)<classifier.z_front+.85*classifier.length:continue
        if not min(p[0] for p in points)<0<max(p[0] for p in points):continue
        candidates.append(m)
    if len(candidates)!=1:raise ValueError(f'rear decal needs one clear central rear placeholder; found {candidates}')
    m=candidates[0];old=gt['textures'][m];gt['textures'][m]=decal
    return {'material':m,'original_texture_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
            'authored_texture_sha256':hashlib.sha256(decal.read_bytes()).hexdigest(),
            'geometry_uvs':'original source placeholder retained'}
