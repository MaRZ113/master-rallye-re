"""Bounded, deterministic staging of real DX/DXT for the native D3D previewer.

This is an inspection format, not a replacement vehicle format. Texture rows
and DX UVs stay unchanged; the viewer uses the SDK right-handed camera frame.
"""
from __future__ import annotations
import hashlib
import json
import math
import struct
from pathlib import Path

from .assets import AssetResolver
from .dx import parse_dx
from .dxt import parse_dxt
from .material_semantics import MaterialSemantics
from .addon_sdk.texture_budget import RETAIL_TEXTURE_CACHE_BYTES,DEFAULT_VEHICLE_TEXTURE_BUDGET

MAX_SCENE_BYTES=256*1024*1024

def preview_transform(transform):
    """Shared explicit presentation-instance transform (never physics fitting)."""
    if not transform:return (lambda v,position=False:v),[1.,1.,1.]
    if not {'translation','rotation_y'}<=set(transform) or set(transform)-{'translation','rotation_y','scale'}:raise ValueError('unsupported wheel transform')
    tr=transform['translation'];angle=float(transform['rotation_y']);scale=transform.get('scale',[1.,1.,1.])
    if len(scale)!=3 or not all(math.isfinite(v) and .1<=abs(v)<=10 for v in scale):raise ValueError('invalid visual wheel scale')
    if len(tr)!=3 or not all(math.isfinite(v) and abs(v)<100 for v in [*tr,angle]):raise ValueError('invalid wheel transform')
    ca,sa=math.cos(angle),math.sin(angle)
    def vec(v,position=False):
        x,y,z=(v[k]*(scale[k] if position else 1/scale[k]) for k in range(3));out=(ca*x+sa*z,y,-sa*x+ca*z)
        if not position:
            length=math.sqrt(sum(n*n for n in out));out=tuple(n/length for n in out) if length else (0.,1.,0.)
        return tuple(out[k]+(tr[k] if position else 0) for k in range(3))
    return vec,scale


def preview_bgra(texture):
    """GPU cache convention: retain rows, unlike an upright PNG export.

    The first viewer used a left-handed camera on the SDK's right-handed
    geometry, mirroring all lettering. Correct the camera, not the texture.
    """
    return texture.bgra


def presentation_wheels(car,complete,wheel):
    """Recover only exact repeated wheel geometry from a frontend rest pose.

    No arch fitting, donor draw IDs or physics parameters. A transform must
    reproduce every vertex in a complete wheel part, and at least two distinct
    parts must agree. Race body frame is recovered by exact translated draws.
    """
    def positions(m,d):return m.vertices.positions[d.vertex_base:d.vertex_base+d.local_vertex_max+1]
    offsets=[]
    for a in car.physical_draws:
        matches=[b for b in complete.physical_draws if (a.texture_tuple,a.triangle_count,a.local_vertex_max)==(b.texture_tuple,b.triangle_count,b.local_vertex_max)]
        if len(matches)!=1 or a.triangle_count<20:continue
        ps,qs=positions(car,a),positions(complete,matches[0]);delta=tuple(qs[0][k]-ps[0][k] for k in range(3))
        if all(abs(q[k]-p[k]-delta[k])<2e-5 for p,q in zip(ps,qs) for k in range(3)):offsets.append(delta)
    if len(offsets)<2:raise ValueError('no qualified race/frontend body-frame correspondence')
    delta=tuple(sorted(p[k] for p in offsets)[len(offsets)//2] for k in range(3))
    if any(abs(p[k]-delta[k])>2e-5 for p in offsets for k in range(3)):raise ValueError('inconsistent body frame translation')
    recovered=[]
    for a in wheel.physical_draws:
        ps=positions(wheel,a);n=len(ps)
        matches=[b for b in complete.physical_draws if b.texture_tuple==a.texture_tuple and b.triangle_count==4*a.triangle_count and b.local_vertex_max+1==4*n]
        if len(matches)!=1:continue
        qs=positions(complete,matches[0]);group=[]
        for j in range(4):
            target=qs[j*n:(j+1)*n];scale=[];shift=[]
            for k in range(3):
                pm=sum(p[k] for p in ps)/n;qm=sum(q[k] for q in target)/n
                variance=sum((p[k]-pm)**2 for p in ps)
                if variance<1e-10:break
                factor=sum((p[k]-pm)*(q[k]-qm) for p,q in zip(ps,target))/variance
                scale.append(factor);shift.append(qm-factor*pm)
            if len(scale)!=3 or any(not .5<abs(v)<2 for v in scale):break
            if any(abs(q[k]-p[k]*scale[k]-shift[k])>2e-5 for p,q in zip(ps,target) for k in range(3)):break
            group.append({'translation':[round(shift[k]-delta[k],6) for k in range(3)],'rotation_y':0.,'scale':[round(v,6) for v in scale]})
        if len(group)==4:recovered.append(sorted(group,key=lambda v:tuple(round(x,3) for x in v['translation'])))
    if len(recovered)<2 or any(abs(g[j][field][k]-recovered[0][j][field][k])>2e-5 for g in recovered for j in range(4) for field in ('translation','scale') for k in range(3)):
        raise ValueError('wheel parts do not prove four coherent transforms')
    return {'race_wheel_instances':recovered[0],
            'provenance':f'exact repeated frontend wheel vertices in {len(recovered)} independent parts; {len(offsets)} exact body translations; rest pose only, not race physics'}


def logical_cases(model):
    """Retain switch alternatives, including the stock brake case2 halo span.

    Generic two-case controls are exposed for manual inspection. Only the
    qualified brake switch gets an automatic brake-state interpretation.
    """
    out={};warnings=[]
    for group in model.draw_groups:
        root=group.root
        if root.tag!=7:continue
        if root.group_label=='blight' and root.control_words[:3]==(2,2,8) and root.control_words[3] in (1,2):
            # Decode native case material spans, independently of the legacy
            # flattened parser parentage and independently of texture names.
            i=root.draw_index;n=root.control_words[4];j=i+n;draws=model.physical_draws
            if not 1<=n<=16 or j>=len(draws):raise ValueError('invalid native brake case1')
            second=draws[j]
            first_case=root.control_words[3]
            if second.tag!=8 or second.control_words[0] not in (1,2) or second.control_words[0]==first_case:raise ValueError('invalid native brake case2')
            count=second.control_words[1]
            if not 1<=count<=17 or j+count>len(draws):raise ValueError('invalid native brake material span')
            for k in range(i,j):out[k]=(1,first_case)
            for k in range(j,j+count):out[k]=(1,second.control_words[0])
            continue
        if (root.control_words[:3]!=(2,2,8) or root.control_words[3] not in (1,2)
                or root.control_words[4]!=1 or len(root.children)!=1):
            raise ValueError(f'unsupported switch layout: {root.group_label}')
        child=root.children[0]
        if child.control_words not in ((1,1),(2,1),(2,2)):
            raise ValueError(f'unsupported case selector: {root.group_label}')
        c2=child.control_words[0];c1=root.control_words[3]
        if c1==c2:raise ValueError('duplicate switch case')
        kind=1 if root.group_label=='blight' else 2
        out[root.draw_index]=(kind,c1);out[child.draw_index]=(kind,c2)
        if kind==1:
            # A physical top-level draw may belong to the preceding logical case.
            draws=model.physical_draws;i=root.draw_index
            if c2!=2 or i+2>=len(draws):raise ValueError('unsupported brake case span')
            halo=draws[i+2]
            if (child.texture_tuple[0]!='breaklightson-tga' or
                halo.texture_tuple[0]!='breaklightsonglow-tga' or halo.tag!=2):
                raise ValueError('unqualified brake material span')
            out[halo.draw_index]=(1,2)
        else:warnings.append(f'{root.group_label}: case1 default; case2 manually inspectable, controller not emulated')
    return out,warnings


def stage_vehicle(source:Path, output:Path, *, profile:Path|None=None):
    source=source.resolve(strict=True)
    if profile is None and (source.parent/'preview-profile.json').is_file():profile=source.parent/'preview-profile.json'
    paths=[source]
    if source.name.casefold() in ('car.dx','complete.dx'):
        paths=[p for n in ('car.dx','complete.dx','wheel.dx') if (p:=source.parent/n).is_file()]
    config=json.loads(profile.read_text(encoding='utf-8')) if profile else {}
    if not profile and len(paths)==3:
        try:config=presentation_wheels(*(parse_dx(source.parent/n) for n in ('car.dx','complete.dx','wheel.dx')))
        except ValueError as exc:config={'provenance':f'automatic rest-pose assembly unavailable: {exc}'}
    if set(config)-{'race_wheel_instances','provenance','mechanical_debug','attached_models','glass_states'}:raise ValueError('unknown viewer profile field')
    glass_states=config.get('glass_states',{})
    if not isinstance(glass_states,dict) or any(k not in ('screenfront','screenrear','screenleft','screenright') or type(v)is not int or v not in (1,2) for k,v in glass_states.items()):raise ValueError('Glass diagnostics require named source groups and case 1 or 2')
    instances=config.get('race_wheel_instances',[])
    if instances and not config.get('provenance'):raise ValueError('wheel transforms require provenance')
    if len(instances)>16:raise ValueError('too many wheel instances')
    attached={}
    for item in config.get('attached_models',[]):
        if (not isinstance(item,dict) or set(item)!={'resource','wheel_index'} or type(item['wheel_index']) is not int
            or not 0<=item['wheel_index']<len(instances) or not isinstance(item['resource'],str)
            or Path(item['resource']).name!=item['resource'] or '\\' in item['resource'] or ':' in item['resource']
            or not item['resource'].endswith('.dx') or item['resource'] in ('car.dx','complete.dx','wheel.dx')):
            raise ValueError('invalid attached preview model')
        path=source.parent/item['resource']
        if path in attached or len(attached)>=16:raise ValueError('duplicate or excessive attached preview models')
        attached[path]=instances[item['wheel_index']];paths.append(path)
    embedded=False
    if (source.parent/'car.dx').exists() and (source.parent/'wheel.dx').exists():
        try:
            body=parse_dx(source.parent/'car.dx');presentation_wheels(body,body,parse_dx(source.parent/'wheel.dx'));embedded=True
        except ValueError:pass
    if embedded and instances:
        instances=[] # Exact source geometry already contains all four wheels.
    textures=[];texture_ids={};draws=[];points=[];reports=[];wheel_votes=[]
    def texture(value):
        if value.strip().casefold()=='null':return -1
        path=AssetResolver(source.parent).resolve_texture(value)
        if path is None:raise ValueError(f'missing referenced texture: {value}')
        key=str(path.resolve()).casefold()
        if key not in texture_ids:
            t=parse_dxt(path)
            if t.width*t.height>16*1024*1024:raise ValueError('preview texture pixel budget exceeded')
            if sum(len(t[3]) for t in textures)+len(t.bgra)>MAX_SCENE_BYTES//2:raise ValueError('texture aggregate budget exceeded')
            texture_ids[key]=len(textures);textures.append((path.name,t.width,t.height,preview_bgra(t)))
        return texture_ids[key]
    for path in paths:
        m=parse_dx(path)
        if not m.diagnostics.validated:raise ValueError(f'invalid DX {path}: {m.diagnostics.errors}')
        if m.vertex_count>1000000 or len(m.physical_draws)>8192:raise ValueError('preview mesh budget exceeded')
        cases,warnings=logical_cases(m)
        selected_glass={}
        if path.name.casefold()=='car.dx':
            labels={g.root.group_label for g in m.draw_groups if g.root.tag==7}
            if set(glass_states)-labels:raise ValueError('Requested glass group is absent from source model')
            for g in m.draw_groups:
                if g.root.group_label in glass_states:
                    for index in g.draw_indices:selected_glass[index]=glass_states[g.root.group_label]
        model_kind={'car.dx':1,'complete.dx':2,'wheel.dx':3}.get(path.name.casefold(),0)
        if model_kind==3:
            wheel_votes=[m.vertices.normals[k][0] for d in m.physical_draws for k in sorted(set(m.draw_global_indices(d))) if abs(m.vertices.normals[k][0])>.7]
        transforms=[None]
        if path in attached:model_kind=4;transforms=[attached[path]]
        # Race rest-pose instances are explicit, never synthesized from physics.
        if model_kind==3 and instances:transforms=[None]+instances
        for instance_no,transform in enumerate(transforms):
            target_model=1 if instance_no or model_kind==4 else model_kind
            vec,scale=preview_transform(transform)
            for d in m.physical_draws:
                if d.index_count==0:continue
                if d.draw_index in selected_glass and cases[d.draw_index][1]!=selected_glass[d.draw_index]:continue
                sem=MaterialSemantics.from_draw(d)
                if len(d.texture_slots)!=3:raise ValueError('requires evidenced three texture slots')
                flags=list(d.flags_0x20)
                # (base mask bits & 3) must be retained separately from env capability.
                base=texture(d.texture_tuple[0]) if d.unknown_0x24&3 else -1
                env=texture(d.texture_tuple[1]) if d.unknown_0x24&4 else -1
                ids=m.draw_global_indices(d);used=sorted(set(ids));remap={v:i for i,v in enumerate(used)}
                vertices=bytearray()
                for k in used:
                    p=vec(m.vertices.positions[k],True);normal=vec(m.vertices.normals[k]);colour=m.vertices.colors[k*4:k*4+4] if flags[2] else b'\xff'*4
                    uv=m.uv_sets[0].values[k] if m.uv_sets and flags[3] else (0.,0.)
                    if not all(math.isfinite(v) for v in (*p,*normal,*uv)):raise ValueError('nonfinite preview vertex')
                    vertices.extend(struct.pack('<6f4s2f',*p,*normal,colour,*uv))
                    if target_model!=3:points.append(p)
                ps=[vec(m.vertices.positions[k],True) for k in used]
                centre=[sum(p[k] for p in ps)/len(ps) for k in range(3)]
                switch,case=cases.get(d.draw_index,(0,0))
                if d.draw_index in selected_glass:switch,case=0,0
                name=f'{path.name}:{d.draw_index}:{d.group_label or d.texture_tuple[0]}'
                staged_indices=[remap[v] for v in ids]
                # A reflected position transform reverses triangle handedness.
                # Preserve outward faces with the inverse-transpose normals.
                if transform and math.prod(scale)<0:
                    for j in range(0,len(staged_indices),3):staged_indices[j+1],staged_indices[j+2]=staged_indices[j+2],staged_indices[j+1]
                if instance_no:name+=f'@wheel{instance_no-1}'
                draws.append((name,5 if instance_no or model_kind==4 else target_model,base,env,flags[0],flags[1],switch,case,centre,bytes(vertices),staged_indices))
        reports.append({'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'model':model_kind,
                        'draws':len(m.physical_draws),'vertices':m.vertex_count,'warnings':warnings,
                        'materials':[MaterialSemantics.from_draw(d).to_dict() for d in m.physical_draws]})
    mechanics=None
    if 'mechanical_debug' in config:
        from .addon_sdk.visual_fitment import diagnose_mechanics
        car=next((p for p in paths if p.name.casefold()=='car.dx'),None)
        if car is None:raise ValueError('mechanical debug requires car.dx')
        mechanics=diagnose_mechanics(car.read_bytes(),config['mechanical_debug'])
        # Explicit source and target hubs, displayed through geometry by the
        # viewer. These glyphs are diagnostics, never exported into game DXs.
        for group in mechanics['groups']:
            for key,colour,radius in (('source_hub_m',b'\x30\x50\xff\xff',.055),
                                      ('target_hub_m',b'\x60\xff\x30\xff',.035)):
                centre=group[key];vertices=bytearray();indices=[]
                for axis in range(3):
                    other=(axis+1)%3
                    for side in (-1,1):
                        for direction in (-1,1):
                            p=list(centre);p[axis]+=side*radius;p[other]+=direction*.003
                            vertices.extend(struct.pack('<6f4s2f',*p,0.,1.,0.,colour,0.,0.))
                    start=len(vertices)//36-4
                    indices.extend(start+i for i in (0,1,2,2,1,3))
                draws.append((f'diagnostic:mechanical:{group["name"]}:{key}',1,-1,-1,0,0,0,0,
                              centre,bytes(vertices),indices))
    if not points:points=[p for p in m.vertices.positions]
    lo=[min(p[k] for p in points) for k in range(3)];hi=[max(p[k] for p in points) for k in range(3)]
    data=bytearray(struct.pack('<4sIII6f',b'MRPV',1,len(textures),len(draws),*lo,*hi))
    def string(s):
        b=s.encode('utf-8')
        if len(b)>4096:raise ValueError('scene string budget exceeded')
        return struct.pack('<I',len(b))+b
    for name,w,h,pixels in textures:data.extend(string(name)+struct.pack('<II',w,h)+pixels)
    for name,kind,base,env,alpha,test,switch,case,centre,vertices,indices in draws:
        data.extend(string(name)+struct.pack('<Iii4I3fII',kind,base,env,alpha,test,switch,case,*centre,len(vertices)//36,len(indices))+vertices+struct.pack(f'<{len(indices)}I',*indices))
        if len(data)>MAX_SCENE_BYTES:raise ValueError('preview scene byte budget exceeded')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(data)
    cache_bytes=sum(w*h*4 for _,w,h,_ in textures)
    report={'schema_version':1,'status':'OFFLINE_MR_RESOURCE_SCENE','sources':reports,'textures':len(textures),'draws':len(draws),
            'native_texture_residency':{'family_cache_bytes':cache_bytes,'retail_cache_bytes':RETAIL_TEXTURE_CACHE_BYTES,
                'authoring_budget_bytes':DEFAULT_VEHICLE_TEXTURE_BUDGET,
                'warning':cache_bytes>DEFAULT_VEHICLE_TEXTURE_BUDGET,
                'scope':'all staged family textures; native MR eviction is not simulated by the D3D9 viewer'},
            'instance_handedness':[{'index':i,'determinant':math.prod(t.get('scale',[1.,1.,1.])),
                'mirrored':math.prod(t.get('scale',[1.,1.,1.]))<0} for i,t in enumerate(instances)],
            'embedded_four_wheel_match':embedded,
            'wheel_outside_camera':{'axial_normal_votes':len(wheel_votes),'mean_axial_vote':sum(wheel_votes)/len(wheel_votes) if wheel_votes else 0,
                'rule':'dominant axial source normals; 1 outside / 2 inside; ambiguous votes retain generic camera. No mesh flip.'},
            'wheel_geometry':[{'draw':d[0],'centre':d[8],'vertices_sha256':hashlib.sha256(d[9]).hexdigest(),
                'indices_sha256':hashlib.sha256(struct.pack(f'<{len(d[10])}I',*d[10])).hexdigest()} for d in draws if d[1]==5],
            'scene_sha256':hashlib.sha256(data).hexdigest(),'bounds':[lo,hi],
            'texture_raster':'stored BGRA rows and original UVs preserved; right-handed view/projection',
            'race_wheel_assembly':'explicit profile' if instances else 'not inferred; frontend embedded wheels and standalone wheel available',
            'approximations':['D3D9 fixed-function equivalent, not native D3D8 runtime','neutral background, no world fog or runtime vertex lighting',
                              'alpha sorted by draw centre; native composite queue key not fully reproduced','CW culling calibrated for stored-global/RH camera frame (wire corners 0/1 are swapped); inherited culling overrides remain unresolved',
                              'ZWrite defaults to the native instance constructor ON override; Z/--depth-write shader exposes shader-only states; caller-specific overrides remain a runtime boundary',
                              'wrap addressing and full-resolution bilinear textures; per-instance/native options not emulated','generic switch case1 default, manual case2'],
            'profile':config}
    if mechanics is not None:
        report['mechanical_debug']=mechanics
        report['approximations'].append('red source/green target hub markers are depth-independent diagnostic overlays; no dynamic suspension is simulated')
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
