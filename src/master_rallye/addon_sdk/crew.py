"""Fit a hash-qualified stock MR seated pair into an imported vehicle.

Only explicit draw selectors are admitted. Each person receives a rigid
translation/yaw; stock geometry, UVs, colours and material layers are retained.
No retail mesh or texture is shipped with this module.
"""
from dataclasses import replace
from pathlib import Path
import hashlib,math,shutil
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.scene_dx_writer import ScenePart
from master_rallye.topology_writer import source_geometry,DrawGeometry
from master_rallye.assets import AssetResolver


def bounds(points):return [[f(p[k] for p in points) for k in range(3)] for f in (min,max)]


def fit_crew(source_root,config,model,output):
    if model not in config['placements']:return [],[]
    if set(config)-{'source','source_sha256','draws','people','placements','seat_pair_preset'}:raise ValueError('unknown crew setting')
    name=config['source']
    if Path(name).name!=name or name!='car.dx':raise ValueError('crew requires an explicit local stock race model')
    data=(source_root/name).read_bytes()
    if hashlib.sha256(data).hexdigest()!=config['source_sha256']:raise ValueError('stock crew source hash changed')
    m=parse_dx_bytes(data)
    if not m.diagnostics.validated or len(m.uv_sets)!=1:raise ValueError('invalid crew source')
    geometry=source_geometry(m);parts=[];records=[];seen=set();all_points={who:[] for who in config['people']}
    if {p['side'] for p in config['people'].values()}!={-1,1} or len(config['people'])!=2:raise ValueError('crew requires an explicit seated pair')
    textures={}
    def texture(value):
        if value=='Null':return value
        if value in textures:return textures[value]
        src=AssetResolver(source_root).resolve_texture(value)
        if src is None:raise ValueError('missing stock crew texture: '+value)
        raw=src.read_bytes();parse_dxt_bytes(raw);stem='mr-crew-'+hashlib.sha256(raw).hexdigest()[:20]+'-tga';dest=output/(stem+'.dxt')
        if dest.exists() and dest.read_bytes()!=raw:raise ValueError('crew texture collision')
        dest.write_bytes(raw);textures[value]=stem;return stem
    for item in config['draws']:
        if not {'index','textures','role'}<=set(item) or set(item)-{'index','textures','role','triangles'} or type(item['index']) is not int or item['index'] in seen:raise ValueError('invalid or duplicate stock crew selector')
        seen.add(item['index'])
        if not 0<=item['index']<len(m.physical_draws):raise ValueError('stock crew draw outside source')
        d=m.physical_draws[item['index']]
        if list(d.texture_tuple)!=item['textures'] or d.tag!=2 or d.control_words or tuple(d.flags_0x20)!=(0,0,1,1) or d.unknown_0x24 not in (3,7):raise ValueError('stock crew material/grammar changed')
        g=geometry[d.draw_index];selected={who:[] for who in config['people']}
        # Some stock families batch harnesses with the dashboard and helmet
        # lining with seats. Select source triangles explicitly under the
        # whole-file hash, rather than copying a donor cockpit or guessing
        # components from texture names/bounds.
        ids=item.get('triangles',list(range(len(g.triangles))))
        if not isinstance(ids,list) or not ids or any(type(i) is not int or not 0<=i<len(g.triangles) for i in ids) or ids!=sorted(set(ids)):raise ValueError('invalid stock crew triangle selection')
        for tri in (g.triangles[i] for i in ids):
            sides={1 if g.vertices[i].position[0]>0 else -1 if g.vertices[i].position[0]<0 else 0 for i in tri}
            if len(sides)!=1 or 0 in sides:raise ValueError('crew triangle crosses seat split; explicit source segmentation required')
            who=next(k for k,v in config['people'].items() if v['side']==next(iter(sides)));selected[who].append(tri)
        for who,triangles in selected.items():
            if not triangles:continue
            placement=config['placements'][model][who]
            if set(placement)!={'lateral','vertical','longitudinal','yaw_degrees'}:raise ValueError('crew placement needs XYZ offsets and yaw')
            values=[placement[k] for k in ('lateral','vertical','longitudinal','yaw_degrees')];pivot=config['people'][who]['pivot']
            if len(pivot)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in values+list(pivot)):raise ValueError('crew transform must be finite')
            if any(abs(v)>3 for v in values[:3]) or abs(values[3])>180:raise ValueError('crew transform outside authoring bounds')
            yaw=math.radians(values[3]);c,s=math.cos(yaw),math.sin(yaw)
            def rotate(p):return (c*p[0]+s*p[2],p[1],-s*p[0]+c*p[2])
            used=sorted({i for t in triangles for i in t});remap={k:i for i,k in enumerate(used)};vertices=[]
            for i in used:
                v=g.vertices[i];q=rotate(tuple(v.position[k]-pivot[k] for k in range(3)))
                vertices.append(replace(v,position=tuple(q[k]+pivot[k]+values[k] for k in range(3)),normal=rotate(v.normal)))
            all_points[who].extend(v.position for v in vertices)
            part=ScenePart(DrawGeometry(tuple(vertices),tuple(tuple(remap[i] for i in t) for t in triangles)),tuple(texture(x) for x in d.texture_tuple),environment=bool(d.unknown_0x24&4))
            parts.append(part);records.append({'route':'MR stock crew','component':'crew','shape':None,'source_draw':d.draw_index,'person':who,'role':item['role'],
                'triangles':len(triangles),'vertices':len(vertices),'source_triangle_indices':[i for i in ids if g.triangles[i] in triangles],'source_sha256':config['source_sha256'],'source_textures':list(d.texture_tuple),
                'textures':list(part.textures),'placement':placement,'bbox':bounds([v.position for v in vertices]),'rigid_fit':True,
                'limitation':'static stock seated pose, no steering animation or GT4 attachment transform claimed'})
    if not parts or any(not ps for ps in all_points.values()):raise ValueError('crew selection did not supply both people')
    for r in records:r['person_bbox']=bounds(all_points[r['person']])
    return parts,records
