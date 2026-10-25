"""Assemble source GT4 body, native brake callbacks, menu rims and CAR4 tyres."""
from __future__ import annotations
import copy,hashlib,math,struct
from .gt4_scene import reconstruct
from .gt4_rig import recover_spec,wheel_point

def component(data,field):
    if data[:4]!=b'CAR4' or field not in (0x20,0x2c,0x30,0x34):raise ValueError('unqualified CAR4 component')
    offsets=[struct.unpack_from('<I',data,i)[0] for i in range(16,56,4)]
    start=struct.unpack_from('<I',data,field)[0]
    if not 0<start<len(data) or data[start:start+4]!=b'MDLS':raise ValueError('CAR4 model component absent')
    end=min([p for p in offsets if start<p<=len(data)]+[len(data)])
    return data[start:end],{'header_field':hex(field),'source_offset':start,'bytes':end-start,'sha256':hashlib.sha256(data[start:end]).hexdigest()}

def normal_at(v,wheel,kind,radial_range,max_x):
    n=v['normal']
    if n is None:return None
    if kind=='tyre':
        x,y,z=v['position'];r=math.hypot(y,z);lo,hi=radial_range
        a=wheel['sidewall']/(hi-lo);b=wheel['rim_radius']-a*lo;f=a+b/r
        j00=f-b*y*y/r**3;j11=f-b*z*z/r**3;j01=-b*y*z/r**3;det=j00*j11-j01*j01
        nx=n[0]*max_x/wheel['width'];ny=(j11*n[1]-j01*n[2])/det;nz=(-j01*n[1]+j00*n[2])/det
        n=(nx,ny,nz)
    if kind!='brake' and wheel['side']>0:n=(-n[0],n[1],-n[2])
    length=math.sqrt(sum(x*x for x in n));return tuple(x/length for x in n) if length else None

def transformed(draw,wheel,kind,radial_range=None,max_x=None):
    out=dict(draw);out['vertices']=[{**v,'position':wheel_point(v['position'],wheel,kind=kind,radial_range=radial_range,max_x=max_x),
                                   'normal':normal_at(v,wheel,kind,radial_range,max_x)} for v in draw['vertices']]
    out['component']=kind;out['wheel_index']=wheel['index']
    return out

def assemble(body_bytes,menu_bytes,spec_folder,profile,*,race=False):
    required=profile['body_race_sha256' if race else 'body_menu_sha256']
    if hashlib.sha256(body_bytes).hexdigest()!=required or hashlib.sha256(menu_bytes).hexdigest()!=profile['body_menu_sha256']:raise ValueError('source does not match profile provenance')
    rig=recover_spec(spec_folder,profile['spec_labels']);selection=profile['selection'];callbacks=profile['body_callbacks']
    source=reconstruct(body_bytes,model_index=selection['race_model' if race else 'menu_model'],lod=selection.get('race_lod',0) if race else 0,callbacks=callbacks,
                       freeze_morphs=bool(profile.get('freeze_dynamic_morphs',False)),vm_tween_callback_profile=profile.get('vm_tween_callback_profile'))
    result=dict(source);result['draws']=list(source['draws']);reports={'body':source['report'],'rig':rig,'components':[]}
    # Recover native body-local brake shapes through callback use, not shape IDs.
    choices={**callbacks,**{str(i):0 for i in range(11,19)}}
    with_wheels=reconstruct(body_bytes,model_index=source['model_index'],lod=source['lod'],callbacks=choices,vm_tween_callback_profile=profile.get('vm_tween_callback_profile'))
    for draw in with_wheels['draws']:
        transforms=draw['transforms']
        if len(transforms)==1 and 'callback' in transforms[0] and 11<=transforms[0]['callback']<=14:
            d=dict(draw);d['issues']=[i for i in d['issues'] if i!='unresolved instance transforms'];d['transforms']=[]
            result['draws'].append(transformed(d,rig['wheels'][transforms[0]['callback']-11],'brake'))
    rim_bytes,rim_evidence=component(menu_bytes,0x20);rim=reconstruct(rim_bytes,model_index=selection['wheel_model'])
    reports['components'].append({'kind':'menu rim','source':rim_evidence,'qualification':rim['report']})
    tyres={}
    for axle,field in enumerate((0x2c,0x30)):
        raw,evidence=component(menu_bytes,field);tyre=reconstruct(raw,model_index=0);tyres[axle]=tyre
        reports['components'].append({'kind':'front tyre' if axle==0 else 'rear tyre','source':evidence,'qualification':tyre['report']})
    extra,evidence=component(menu_bytes,0x34);supplement=reconstruct(extra)
    reports['components'].append({'kind':'supplemental component; runtime purpose/instance unresolved',
        'source':evidence,'qualification':supplement['report'],
        'assembly':'kept separate; not assumed body geometry, shadow, driver or spare wheel'})
    wheel_templates=[]
    for w in rig['wheels']:
        parts=[transformed(d,w,'rim') for d in rim['draws']]
        ts=tyres[w['axle']];ps=[v['position'] for d in ts['draws'] for v in d['vertices']]
        radial=(min(math.hypot(p[1],p[2]) for p in ps),max(math.hypot(p[1],p[2]) for p in ps));max_x=max(abs(p[0]) for p in ps)
        parts += [transformed(d,w,'tyre',radial,max_x) for d in ts['draws']]
        result['draws'].extend(parts)
        if w['index']==0:
            # Standalone MR wheel remains relative to its actual source hub.
            h=w['hub']
            for d in parts:
                local=dict(d);local['vertices']=[{**v,'position':tuple(v['position'][k]-h[k] for k in range(3))} for v in d['vertices']];wheel_templates.append(local)
    result['report']=reports;result['wheel_template']=wheel_templates
    result['report']['assembly_limitations']=['high-detail menu rims/tyres intentionally reused for MR race representation; source race-wheel LODs remain separately accounted',
        'zero steering/spin rest pose; source camber/toe dynamic provider not yet applied','root ground/pitch transform omitted consistently for body and wheels; relative source frame retained']
    return result
