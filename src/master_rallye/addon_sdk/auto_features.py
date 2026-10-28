"""Automatic native MR feature recipes: brake glow (blight) and breakable glass.

Produces the same `native_states.author_states` recipe that was previously
written by hand (Heritage Trooper pilot), so every existing conservation proof
(intact/off geometry, materials and collision unchanged) still runs.

Evidence order, strongest first:
1. Original sidecars (MR Demo/retail): `car.txt` mesh names (`blight`,
   `brakelight`, `glass`, `windows` ...) + `car.gxm` triangle records, matched
   to DX triangles by exact positions under an automatically found axis map.
2. Geometric fallback for sources without sidecars (GT imports): glass =
   translucent blended draws; brake lamps = rear-facing red texels at the tail.

Zones follow MR native labels: +Z front, -Z rear, -X left, +X right.
"""
from __future__ import annotations
import hashlib,itertools,math,re,struct,zlib
from collections import Counter,defaultdict
from ..dx import parse_dx_bytes
from ..dxt import parse_dxt_bytes
from ..topology_writer import source_geometry

BRAKE_RE=re.compile(r'^(?:blight\d*|brake\w*|bl\d*|stop\w*)$',re.I)
GLASS_RE=re.compile(r'^(?:glass\d*|windows?\d*|backwin\d*|bswin\d*|windscreen\w*|screen\w*|sidewin\w*)$',re.I)
LAMP_TEXTURE_RE=re.compile(r'light|lamp|lite|lens',re.I)
GLASS_TEXTURE_RE=re.compile(r'glass|screen|window|perspex',re.I)
ZONES=('screenfront','screenrear','screenleft','screenright')
AXES={'screenfront':[0,1],'screenrear':[0,1],'screenleft':[2,1],'screenright':[2,1]}
# Native pane/brake repack admits only these ordinary material families.
PANE_FLAGS={(0,0,1,1),(1,0,1,1),(1,1,1,1)}


def feed(bgra,width,height):
    return struct.pack('<5I',0xfeed,1,zlib.crc32(bgra)&0xffffffff,width,height)+bytes(bgra)


def sidecar_meshes(text):
    """[(mesh_name, material_tag, first_record, count)] from an original car.txt."""
    out=[]
    for name,index,size in re.findall(r'moMesh\(Name \[([^\]]*)\] Index (\d+) Size (\d+)\)',text):
        base,_,tag=name.strip().partition(' ')
        out.append((base.strip(),tag.strip(),int(index),int(size)))
    return out


def gxm_triangles(raw):
    from ..gxm import parse_gxm_prefix_bytes,parse_gxm_geometry_prefix_bytes,parse_gxm_triangle_prefix_bytes
    pre=parse_gxm_prefix_bytes(raw);geo=parse_gxm_geometry_prefix_bytes(raw,pre);tri=parse_gxm_triangle_prefix_bytes(raw,pre,geo)
    out=[]
    for i in range(tri.record_count):
        row=struct.unpack_from('<10I',raw,tri.record_offset+i*52)
        out.append(tuple(struct.unpack_from('<3f',raw,tri.vector_c_offset+v*12)for v in row[4:7]))
    return out


def _normal(points):
    a,b,c=points;u=[b[k]-a[k]for k in range(3)];v=[c[k]-a[k]for k in range(3)]
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);l=math.sqrt(sum(x*x for x in n))
    return tuple(x/l for x in n)if l>1e-12 else (0.,0.,0.)


def _triangles(model):
    """{draw: [(points, triangle_index)]} for ordinary drawable records."""
    geometry=source_geometry(model);out={}
    for d,g in geometry.items():
        out[d]=[tuple(g.vertices[v].position for v in t)for t in g.triangles]
    return out


def map_records(model,records,wanted,*,tolerance=1e-4,nearest=.01):
    """Map GXM record ids -> {draw: [triangle ids]} with an automatically
    discovered signed axis permutation. Only a complete unique match passes."""
    tris=_triangles(model);index=defaultdict(list)
    q=lambda p:tuple(round(x/tolerance)for x in p)
    for d,items in tris.items():
        for i,pts in enumerate(items):index[tuple(sorted(q(p)for p in pts))].append((d,i))
    sample=[records[i]for i in wanted]
    best=None
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((-1,1),repeat=3):
            # Double-sided panes repeat identical positions: consume each DX
            # triangle once, in order, instead of rejecting the duplicate.
            hits=[];used=Counter()
            for pts in sample:
                key=tuple(sorted(q(tuple(p[perm[k]]*signs[k]for k in range(3)))for p in pts))
                found=index.get(key,[]);n=used[key];used[key]+=1
                hits.append(found[n]if n<len(found)else found[0]if found else None)
            score=sum(h is not None for h in hits)
            if best is None or score>best[0]:best=(score,perm,signs,hits)
    score,perm,signs,hits=best
    flat=[(d,i,pts)for d,items in tris.items()for i,pts in enumerate(items)]
    if not score:
        # No exact hit at all: choose the axis map by nearest-centroid error.
        centres=[tuple(sum(p[k]for p in pts)/3 for k in range(3))for _,_,pts in flat]
        def error(perm,signs):
            return sum(min(math.dist(tuple(sum(p[perm[k]]*signs[k]for p in pts)/3 for k in range(3)),c)for c in centres)for pts in sample)
        perm,signs=min(((p,s)for p in itertools.permutations(range(3))for s in itertools.product((-1,1),repeat=3)),key=lambda ps:error(*ps))
    # Shipped DX files were sometimes cooked from a slightly edited scene:
    # admit the nearest unused triangle within `nearest` metres (corner sum).
    taken={h for h in hits if h is not None};near=0
    if flat:
        for n,h in enumerate(hits):
            if h is not None:continue
            r=[tuple(p[perm[k]]*signs[k]for k in range(3))for p in sample[n]]
            cands=sorted((sum(min(math.dist(p,q)for q in pts)for p in r),d,i)for d,i,pts in flat if (d,i)not in taken)
            if cands and cands[0][0]<=nearest and (len(cands)<2 or cands[1][0]>cands[0][0]*1.5+1e-6):
                hits[n]=cands[0][1:];taken.add(hits[n]);near+=1
        score+=near
    result=defaultdict(list)
    for h in hits:
        if h is not None:result[h[0]].append(h[1])
    return {d:sorted(set(v))for d,v in result.items()},{'axis_permutation':list(perm),'axis_signs':list(signs),'matched':score,'nearest_matches':near,'requested':len(sample)}


def _texture(textures,stem):
    if stem is None or stem.casefold()=='null':return None
    raw=textures.get(stem.casefold()+'.dxt')
    return parse_dxt_bytes(raw)if raw else None


def _sample(texture,uv):
    x=min(texture.width-1,max(0,int((uv[0]%1.)*texture.width)));y=min(texture.height-1,max(0,int((uv[1]%1.)*texture.height)))
    i=(y*texture.width+x)*4;return texture.bgra[i:i+4]


def _redness(texture,geometry,tri):
    """Mean (r-max(g,b)) of texels under triangle corners + centroid."""
    uvs=[geometry.vertices[v].uvs[0]for v in tri];c=tuple(sum(u[k]for u in uvs)/3 for k in range(2))
    vals=[]
    for uv in uvs+[c]:
        b,g,r,a=_sample(texture,uv);vals.append(r-max(g,b))
    return sum(vals)/len(vals)


def zone_glass(points_by_tri):
    """Assign glass triangles to native zones by normal and lateral position."""
    if not points_by_tri:return {}
    width=max(abs(p[0])for pts in points_by_tri.values()for p in pts) or 1.
    zones=defaultdict(list)
    for key,pts in points_by_tri.items():
        n=_normal(pts);cx=sum(p[0]for p in pts)/3
        lateral=abs(cx)>=.72*width and abs(n[2])<.9
        if not lateral and abs(n[2])>=abs(n[0])*.75 and abs(n[2])>.2:zone='screenfront'if n[2]>0 else'screenrear'
        else:zone='screenright'if (n[0] if abs(n[0])>.15 else cx)>0 else'screenleft'
        zones[zone].append(key)
    return zones


def lamp_textures(texture):
    """Lit/glow DXTs from a lamp atlas: boost red texels; glow alpha from red."""
    lit=bytearray(texture.bgra);glow=bytearray(len(texture.bgra));red_texels=0
    for i in range(0,len(lit),4):
        b,g,r,a=lit[i:i+4];mask=r>g*1.3 and r>b*1.3 and r>30
        red_texels+=mask
        if mask:lit[i:i+4]=bytes([min(120,int(b*1.5)),min(120,int(g*1.5)),min(255,int(r*2.8)),a])
        glow[i:i+4]=bytes([10,20,255,round(min(140,r*.6))if mask else 0])
    if not red_texels:
        # Lens atlas without red source texels (e.g. a plain perspex map):
        # the selected rear-lens triangles are the whole lamp.
        for i in range(0,len(lit),4):
            b,g,r,a=texture.bgra[i:i+4];lum=max(r,g,b)
            lit[i:i+4]=bytes([min(90,b//2),min(90,g//2),min(255,64+lum),a]);glow[i:i+4]=bytes([10,20,255,120])
    return feed(lit,texture.width,texture.height),feed(glow,texture.width,texture.height),red_texels


def procedural_cracks(size=64,seed=1):
    """Fallback cracked windscreen when no stock cracked texture is supplied."""
    import random
    rnd=random.Random(seed);px=bytearray([60,52,44,150]*(size*size))
    for _ in range(9):
        x,y=rnd.uniform(0,size),rnd.uniform(0,size);a=rnd.uniform(0,2*math.pi)
        for _ in range(int(size*1.2)):
            a+=rnd.uniform(-.5,.5);x=(x+math.cos(a))%size;y=(y+math.sin(a))%size
            i=(int(y)*size+int(x))*4;px[i:i+4]=bytes([205,205,205,235])
    return feed(px,size,size)


def _pane_draw_ok(d):
    return len(d.texture_tuple)==3 and tuple(d.flags_0x20)in PANE_FLAGS and d.unknown_0x24 in (3,7) and d.texture_tuple[2]=='Null' and d.tag==2


def derive(car_raw,textures,*,sidecar_text=None,gxm_raw=None,cracked_stem='mr-auto-cracked-tga',glass=True,brake=True):
    """Return (states recipe, {new texture name: bytes}, report).

    `textures` maps lower-case `<stem>.dxt` -> bytes of the vehicle's own DXTs.
    """
    m=parse_dx_bytes(car_raw);geometry=source_geometry(m);report={'evidence':[],'warnings':[]}
    if any(d.tag!=2 for d in m.physical_draws):raise ValueError('Model already has native controls; keep its existing features')
    selected={'glass':{},'brake':{}}
    if sidecar_text and gxm_raw:
        meshes=sidecar_meshes(sidecar_text);records=gxm_triangles(gxm_raw)
        for kind,pattern in (('brake',BRAKE_RE),('glass',GLASS_RE)):
            wanted=[i for name,tag,first,size in meshes if pattern.match(name)for i in range(first,first+size)if i<len(records)]
            if not wanted:continue
            mapping,proof=map_records(m,records,wanted)
            names=sorted({name for name,tag,first,size in meshes if pattern.match(name)})
            report['evidence'].append({'kind':kind,'source':'car.txt mesh names + car.gxm records','meshes':names,**proof})
            if proof['matched']!=proof['requested']:report['warnings'].append(f'{kind}: {proof["requested"]-proof["matched"]} sidecar triangles not uniquely matched')
            selected[kind]=mapping
    tris=_triangles(m)
    if glass and not selected['glass']:
        for d in m.physical_draws:
            t=_texture(textures,d.texture_tuple[0])
            name=' '.join(d.texture_tuple)
            if d.flags_0x20[0] and not d.flags_0x20[1] and (GLASS_TEXTURE_RE.search(name) or (t and 40<=sum(t.bgra[3::4])/max(1,len(t.bgra)//4)<=235)):
                selected['glass'][d.draw_index]=list(range(len(geometry[d.draw_index].triangles)))
        if selected['glass']:report['evidence'].append({'kind':'glass','source':'geometric fallback: translucent blended draws','draws':sorted(selected['glass'])})
    if brake and not selected['brake']:
        zs=[p[2]for d in tris.values()for pts in d for p in pts];zmin,zmax=min(zs),max(zs);tail=zmin+.15*(zmax-zmin)
        for d in m.physical_draws:
            t=_texture(textures,d.texture_tuple[0])
            if t is None or d.draw_index in selected['glass']:continue
            g=geometry[d.draw_index];ids=[]
            for i,tri in enumerate(g.triangles):
                pts=tris[d.draw_index][i];n=_normal(pts)
                if max(p[2]for p in pts)<=tail and n[2]<-.1 and _redness(t,g,tri)>18:ids.append(i)
            if ids:selected['brake'][d.draw_index]=ids
        if selected['brake']:report['evidence'].append({'kind':'brake','source':'geometric fallback: rear-facing red texels in tail 15%','draws':{str(k):len(v)for k,v in selected['brake'].items()}})
    states={'source_sha256':hashlib.sha256(car_raw).hexdigest()};extra={}
    if glass and selected['glass']:
        points={(d,i):tris[d][i]for d,ids in selected['glass'].items()for i in ids}
        panes=[]
        for zone,keys in zone_glass(points).items():
            per_draw=Counter(d for d,_ in keys);draw=per_draw.most_common(1)[0][0]
            if not _pane_draw_ok(m.physical_draws[draw]):report['warnings'].append(f'{zone}: draw {draw} material family not repackable');continue
            ids=sorted(i for d,i in keys if d==draw)
            if len(per_draw)>1:report['warnings'].append(f'{zone}: glass spans draws {sorted(per_draw)}; draw {draw} becomes breakable, others stay intact')
            panes.append({'label':zone,'source_draw':draw,'triangles':ids,'broken_uv_axes':AXES[zone],'broken_texture':cracked_stem})
        if panes:states['panes']=sorted(panes,key=lambda p:ZONES.index(p['label']))
    if brake and selected['brake']:
        draw,ids=max(selected['brake'].items(),key=lambda kv:len(kv[1]))
        d=m.physical_draws[draw];texture=_texture(textures,d.texture_tuple[0])
        if not _pane_draw_ok(d):report['warnings'].append(f'brake: draw {draw} material family not repackable')
        elif texture is None:report['warnings'].append(f'brake: draw {draw} texture {d.texture_tuple[0]} missing')
        else:
            lit,glow,red=lamp_textures(texture);key=hashlib.sha256(lit+glow).hexdigest()[:12]
            extra[f'mr-auto-stop-lit-{key}-tga.dxt']=lit;extra[f'mr-auto-stop-glow-{key}-tga.dxt']=glow
            ev=next((e for e in report['evidence']if e['kind']=='brake'),{})
            states['brake']={'source_draw':draw,'triangles':ids,'lit_texture':f'mr-auto-stop-lit-{key}-tga','glow_texture':f'mr-auto-stop-glow-{key}-tga',
                'evidence':f'Automatic: {ev.get("source","unknown")}; {len(ids)} lens triangles in draw {draw}; {red} red source texels drive lit/glow.'}
            if len(selected['brake'])>1:report['warnings'].append(f'brake: lamp triangles span draws {sorted(selected["brake"])}; draw {draw} (largest) is switched')
    report['zones']={p['label']:len(p['triangles'])for p in states.get('panes',[])}
    report['brake_triangles']=len(states['brake']['triangles'])if 'brake'in states else 0
    return states,extra,report
