"""Deterministic exterior colour suggestions, separate from native HUD writing.

Samples source triangles through UV0, not the unused area of whole atlases.
Results are authoring suggestions, never historical or renderer equivalence.
"""
from pathlib import Path
import hashlib,math,re

MODES=('HISTORICAL','AUTO_DOMINANT','AUTO_AVERAGE','MANUAL')
EXCLUDE=re.compile(r'glass|perspex|screen|window|tyre|tire|tread|wheel|rim|light|lamp|glow|chrome|chair|seat|helmet|driver|crew|suit|skin|dcambell|drichard|interior|underdash|underbody|undertray|shadow|diagnostic|placeholder',re.I)


def rgba(value):
    if not isinstance(value,(list,tuple))or len(value)!=4 or any(type(x)not in(int,float)or not math.isfinite(x)or not 0<=x<=1 for x in value):raise ValueError('Expected finite normalized RGBA')
    return list(value)


def linear(x):return x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4
def srgb(x):return 12.92*x if x<=.0031308 else 1.055*max(x,0)**(1/2.4)-.055


def oklab(rgb):
    r,g,b=map(linear,rgb)
    l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3)
    m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3)
    s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
    return(.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s)


def summarize(samples):
    """Bounded, deterministic OKLab bins; weighted RGB means remain source-based."""
    bins={};total=0;avg=[0.,0.,0.];count=0
    for rgb,weight in samples:
        count+=1
        if count>120000:raise ValueError('Colour sample budget exceeded')
        rgba([*rgb,1])
        if type(weight)not in(int,float)or not math.isfinite(weight)or weight<=0:raise ValueError('Invalid colour area weight')
        key=tuple(round(x/step)for x,step in zip(oklab(rgb),(.08,.06,.06)))
        entry=bins.setdefault(key,[0.,[0.,0.,0.]])
        entry[0]+=weight;total+=weight
        for i,x in enumerate(rgb):entry[1][i]+=x*weight;avg[i]+=linear(x)*weight
    if not total:raise ValueError('No qualified exterior colour samples; choose an explicit material/texture fallback or manual colour')
    ordered=sorted(bins.items(),key=lambda x:(-x[1][0],x[0]))
    candidates=[{'rgb':[round(x/w,8)for x in sums],'weight':round(w/total,8)}for _,(w,sums)in ordered[:6]]
    return {'dominant':candidates[0]['rgb'],'average':[round(min(1,max(0,srgb(x/total))),8)for x in avg],'swatches':candidates,'samples':count}


def analyze(family,*,paint_draws=None,paint_textures=None,fallback_texture=None):
    from ..dx import parse_dx_bytes
    from ..topology_writer import source_geometry
    from ..preview_scene import logical_cases
    from ..assets import AssetResolver
    from ..dxt import parse_dxt_bytes,decode_rgba_pixels
    family=Path(family);path=family/'car.dx';raw=path.read_bytes()
    if len(raw)>32*1024*1024:raise ValueError('Colour model byte budget')
    model=parse_dx_bytes(raw);geometry=source_geometry(model);cases,_=logical_cases(model)
    if sum(len(g.triangles)for g in geometry.values())>60000:raise ValueError('Colour triangle budget')
    if paint_draws is not None and (not isinstance(paint_draws,list)or not paint_draws or len(set(paint_draws))!=len(paint_draws)or any(type(x)is not int or x not in geometry for x in paint_draws)):raise ValueError('Invalid explicit exterior draw ownership')
    if paint_textures is not None and (not isinstance(paint_textures,list)or not paint_textures or len(paint_textures)>64 or any(not isinstance(x,str)or not re.fullmatch('[A-Za-z0-9_-]{1,96}',x)for x in paint_textures)):raise ValueError('Invalid explicit paint material references')
    resolver=AssetResolver(family);textures={};pins={'car.dx':hashlib.sha256(raw).hexdigest()};samples=[];used=[];excluded=[]
    def texture(stem):
        p=resolver.resolve_texture(stem)
        if p is None:raise ValueError('Missing exterior texture: '+stem)
        if p.name not in textures:
            data=p.read_bytes();t=parse_dxt_bytes(data)
            if t.width*t.height>4*1024*1024 or len(textures)>=64:raise ValueError('Colour texture budget')
            textures[p.name]=(t.width,t.height,decode_rgba_pixels(t));pins[p.name]=hashlib.sha256(data).hexdigest()
        return textures[p.name]
    # Seven deterministic barycentric taps per face. Equal tap weights sum to
    # its actual 3D area; large unused atlas regions have no statistical weight.
    taps=((1/3,1/3,1/3),(.7,.15,.15),(.15,.7,.15),(.15,.15,.7),(.45,.45,.1),(.45,.1,.45),(.1,.45,.45))
    for d in model.physical_draws:
        if d.draw_index not in geometry:continue
        stem=d.texture_tuple[0];reason=None
        if d.draw_index in cases and cases[d.draw_index][1]!=1:reason='non-intact/ON state'
        elif paint_draws is not None and d.draw_index not in paint_draws:reason='outside explicit exterior ownership'
        elif paint_textures is not None and stem not in paint_textures:reason='outside explicit exterior material ownership'
        elif EXCLUDE.search(' '.join(d.texture_tuple)):reason='glass/wheel/cabin/lamp/auxiliary material'
        elif any(d.flags_0x20[:2]):reason='blend/cutout material; explicit opaque paint required'
        elif stem.casefold()=='null':reason='no diffuse'
        if reason:excluded.append({'draw':d.draw_index,'reason':reason});continue
        w,h,pixels=texture(stem);g=geometry[d.draw_index];n=0;area_sum=0.
        for triangle in g.triangles:
            vs=[g.vertices[i]for i in triangle];p=[v.position for v in vs]
            a=[p[1][i]-p[0][i]for i in range(3)];b=[p[2][i]-p[0][i]for i in range(3)]
            cross=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]);area=math.sqrt(sum(x*x for x in cross))/2
            if not math.isfinite(area):raise ValueError('Nonfinite exterior geometry')
            if area<1e-10:continue
            if paint_draws is None and sum(v.normal[1]for v in vs)/3<-.45:continue
            for tap in taps:
                uv=[sum(tap[j]*vs[j].uvs[0][i]for j in range(3))for i in range(2)]
                if not all(math.isfinite(x)for x in uv):raise ValueError('Nonfinite UV')
                # Native DX diffuse UV0 follows the existing preview convention.
                x=min(w-1,int((uv[0]%1)*w));y=min(h-1,int(((1-uv[1])%1)*h));offset=4*(y*w+x)
                if pixels[offset+3]<128:continue
                rgb=[x/255 for x in pixels[offset:offset+3]]
                samples.append((rgb,area/len(taps)));n+=1
            area_sum+=area
        if n:used.append({'draw':d.draw_index,'texture':stem,'samples':n,'area':area_sum})
    level='EXPLICIT_EXTERIOR'if paint_draws is not None else'EXPLICIT_MATERIALS_UV_AREA'if paint_textures is not None else'UV_AREA_HEURISTIC'
    limitations=['Exterior ownership is an authoring heuristic unless explicitly selected; paint, decals and neutral trim may share one atlas. Lighting/reflections are excluded.']
    if not samples and fallback_texture:
        w,h,pixels=texture(fallback_texture)
        for i in range(0,len(pixels),4*max(1,(w*h+59999)//60000)):
            if pixels[i+3]>=128:samples.append(([x/255 for x in pixels[i:i+3]],1.))
        level='EXPLICIT_TEXTURE_FALLBACK';limitations.append('No reliable exterior draws; explicitly selected whole texture sampled without surface-area weighting.')
    result=summarize(samples)
    return {'schema':'vehicle-marker-analysis/1',**result,'confidence':'MEDIUM'if used else'LOW','method':level,'used_draws':used,'excluded_draws':excluded,'source_pins':pins,'limitations':limitations}


def select(policy,analysis=None,historical=None):
    if not isinstance(policy,dict)or policy.get('mode')not in MODES or set(policy)-{'mode','rgba','contrast','analysis_settings'}:raise ValueError('Invalid marker selection policy')
    mode=policy['mode'];contrast=policy.get('contrast',False)
    if type(contrast)is not bool:raise ValueError('Contrast must be explicit boolean')
    if mode=='HISTORICAL':
        if not historical or historical.get('status')!='PROVEN' or not historical.get('evidence'):raise ValueError('Verified historical marker unavailable')
        value=rgba(historical['value'])
    elif mode=='MANUAL':value=rgba(policy.get('rgba'))
    else:
        if not analysis or analysis.get('schema')!='vehicle-marker-analysis/1':raise ValueError('Recalculate qualified exterior colour suggestions first')
        value=rgba([*analysis['dominant'if mode=='AUTO_DOMINANT'else'average'],1.])
    # Restrained optional lift preserves hue ratios, never touches ORIGINAL.
    if contrast and mode!='HISTORICAL':
        top=max(value[:3]);gain=min(1.35,.65/top)if top and top<.65 else 1.
        value=[*[min(1,x*gain)for x in value[:3]],value[3]]
    return value
