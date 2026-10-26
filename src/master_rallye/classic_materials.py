"""Explicit stock-referenced rubber/glass pilot, separate from texture guessing.

Profiles pin source draws, atlases and native reference records. No material name
heuristics, controller creation, global alpha rewrite or source mutation.
"""
import hashlib
import copy
import math
import re
import struct
from dataclasses import replace
from .dx import parse_dx_bytes
from .dxt import parse_dxt_bytes,encode_dxt_pixels,PNG_ROWS_PRESERVE_STORED


def sha(raw):return hashlib.sha256(raw).hexdigest()


def references(recipe, stock_root):
    from pathlib import Path
    result={}
    for name,spec in recipe.get('semantic_materials',{}).get('references',{}).items():
        relative=spec['path']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}/[A-Za-z0-9_-]+\.(dx|dxt)',relative):raise ValueError('Invalid Classic material reference path')
        raw=(Path(stock_root)/relative).read_bytes()
        if sha(raw)!=spec['sha256']:raise ValueError('Classic material reference changed: '+name)
        result[name]=raw
    return result


def _tail(raw, source, reference, target, diffuse, environment):
    """Copy a verified native material record, retaining target draw/controller."""
    m=parse_dx_bytes(raw);d=m.physical_draws[target];r=parse_dx_bytes(reference).physical_draws[source]
    if tuple(d.flags_0x20[:2])!=tuple(r.flags_0x20[:2]):raise ValueError('Classic material cannot change opacity mode')
    tail=reference[r.core_offset+20:r.terminal_offset+4]
    if not r.flags_0x20[2] and d.flags_0x20[2]:
        # Imported scene qualification retains explicit diffuse ownership.
        # White source colour is mathematically identical to stock's disabled
        # diffuse modulation; do not drop native damage's ownership flag.
        if any(m.vertices.colors[i*4:i*4+4]!=b'\xff'*4 for i in set(m.draw_global_indices(d))):raise ValueError('Stock uncoloured material requires white imported vertices')
        tail=bytearray(tail);tail[14]=1
        struct.pack_into('<I',tail,16,struct.unpack_from('<I',tail,16)[0]|2)
        tail=bytes(tail)
    if environment=='Null':
        tail=bytearray(tail);struct.pack_into('<I',tail,16,struct.unpack_from('<I',tail,16)[0]&~4);tail=bytes(tail)
    for slot,value in reversed(list(zip(r.texture_slots,(diffuse,environment,'Null')))):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',value):raise ValueError('Unsafe Classic material texture name')
        a=slot.length_offset-(r.core_offset+20);b=slot.data_offset+len(slot.raw)-(r.core_offset+20)
        encoded=value.encode('ascii');tail=tail[:a]+struct.pack('<I',len(encoded))+encoded+tail[b:]
    output=raw[:d.core_offset+20]+tail+raw[d.terminal_offset+4:]
    n=parse_dx_bytes(output)
    if not n.diagnostics.validated or m.vertices!=n.vertices or m.local_indices!=n.local_indices or raw[m.trailing.offset:]!=output[n.trailing.offset:]:raise ValueError('Classic native material replacement changed geometry or suffix')
    if [(x.root.tag,x.root.group_label,x.root.control_words,x.draw_indices)for x in m.draw_groups]!=[(x.root.tag,x.root.group_label,x.root.control_words,x.draw_indices)for x in n.draw_groups]:raise ValueError('Classic changed native controller ownership')
    return output


def native_tyres(output, source, rule, refs, maps):
    """Stock tyre UV law over unchanged imported tyre geometry and instances."""
    from statistics import median
    from .topology_writer import source_geometry,DrawGeometry,rebuild_topology
    from .classic_wheels import map_embedded_wheels
    config=rule['native_mapping'];wheel=parse_dx_bytes(source['wheel.dx']);g=source_geometry(wheel)
    reference=refs[rule['reference_model']];rm=parse_dx_bytes(reference);rg=source_geometry(rm)
    side=rg[config['sidewall_reference_draw']];tread=rg[rule['reference_draw']]
    # Stock sidewall has one affine radial UV law. Qualify it numerically.
    u=median((v.uvs[0][0]-.5)/v.position[2]for v in side.vertices if abs(v.position[2])>1e-5)
    vv=median((v.uvs[0][1]-.5)/v.position[1]for v in side.vertices if abs(v.position[1])>1e-5)
    if any(abs(v.uvs[0][0]-(.5+u*v.position[2]))>2e-5 or abs(v.uvs[0][1]-(.5+vv*v.position[1]))>2e-5 for v in side.vertices):raise ValueError('Unknown stock radial tyre UV convention')
    rr=[math.hypot(v.position[1],v.position[2])for v in side.vertices];rlo,rhi=min(rr),max(rr)
    ids=config['sidewall_source_draws'];radii=[math.hypot(v.position[1],v.position[2])for i in ids for v in g[i].vertices];lo,hi=min(radii),max(radii)
    if hi-lo<.01 or rhi-rlo<.01:raise ValueError('No qualified sidewall annulus')
    edits={};roles={i:'sidewall'for i in ids};roles.update({i:'tread'for i in config['tread_source_draws']});roles.update({i:'inner'for i in config['inner_backing_source_draws']})
    if len(roles)!=sum(len(config[k])for k in ('sidewall_source_draws','tread_source_draws','inner_backing_source_draws')) or set(roles)!=set(rule['draws']['wheel.dx']):raise ValueError('Tyre parts overlap or are incomplete')
    tlo=min(v.uvs[0][0]for v in tread.vertices);thi=max(v.uvs[0][0]for v in tread.vertices);vlo=min(v.uvs[0][1]for v in tread.vertices);vhi=max(v.uvs[0][1]for v in tread.vertices)
    for i,role in roles.items():
        old=g[i];vertices=[];ul=min(v.uvs[0][0]for v in old.vertices);uh=max(v.uvs[0][0]for v in old.vertices);xl=min(v.position[0]for v in old.vertices);xh=max(v.position[0]for v in old.vertices)
        for v in old.vertices:
            if role=='sidewall':
                radius=math.hypot(v.position[1],v.position[2]);scale=(rlo+(radius-lo)/(hi-lo)*(rhi-rlo))/radius
                uv=(.5+u*v.position[2]*scale,.5+vv*v.position[1]*scale)
            elif role=='tread':
                if uh-ul<.1 or xh-xl<.01:raise ValueError('Unknown tread UV/width convention')
                uv=(tlo+(v.uvs[0][0]-ul)/(uh-ul)*(thi-tlo),vlo+(v.position[0]-xl)/(xh-xl)*(vhi-vlo))
            else:uv=(0.,0.)
            vertices.append(replace(v,uvs=(uv,),source_vertex_id=None))
        edits[i]=DrawGeometry(tuple(vertices),old.triangles)
    embedded,evidence=map_embedded_wheels(source['wheel.dx'],source['complete.dx'],config['embedded_groups'],edits)
    output=dict(output);output['wheel.dx']=rebuild_topology(output['wheel.dx'],edits,bounds_mode='preserve').data
    output['complete.dx']=rebuild_topology(output['complete.dx'],{maps['complete.dx'][i]:v for i,v in embedded.items()},bounds_mode='preserve').data
    env=refs[rule['reference_environment']];envname='classic-rubber-env-'+sha(env)[:16]+'-tga';output[envname+'.dxt']=env
    textures={'tread':refs[rule['reference_diffuse']],'sidewall':refs[config['sidewall_diffuse']]}
    # Existing opaque inner face stays dark, without painting a false rim there.
    textures['inner']=refs[config['inner_diffuse']]
    names={k:'classic-tyre-'+k+'-'+sha(raw)[:16]+'-tga'for k,raw in textures.items()}
    for k,raw in textures.items():
        if set(parse_dxt_bytes(raw).bgra[3::4])!={255}:raise ValueError('Stock tyre diffuse must be opaque')
        output[names[k]+'.dxt']=raw
    records=[]
    for model,selected in [('wheel.dx',[(i,i)for i in roles]),('complete.dx',[(i,maps['complete.dx'][group['draws'][i]])for group in config['embedded_groups']for i in roles])]:
        raw=output[model]
        for i,target in selected:
            if wheel.physical_draws[i].texture_tuple[0]+'.dxt'!=rule['texture'] or any(wheel.physical_draws[i].flags_0x20[:2]):raise ValueError('Unqualified source tyre owner')
            role=roles[i];ref_draw=config['sidewall_reference_draw']if role=='sidewall'else rule['reference_draw']
            raw=_tail(raw,ref_draw,reference,target,names[role],envname);records.append({'model':model,'draw':target,'role':role})
        output[model]=raw
    return output,{'status':'APPLIED_NATIVE_TYRE_UV_MAPPING','records':records,'reference_sha256':sha(reference),'stock_annulus_radius_m':[rlo,rhi],'source_annulus_radius_m':[lo,hi],'radial_uv_coefficients':[u,vv],'stock_tread_uv_range':[tlo,thi,vlo,vhi],'embedded_instances':evidence,'geometry_and_rim_preserved':True,'approximation':'Stock radial UV law fitted to imported annulus; existing opaque inner backing retained. No tyre/rim geometry or hub movement.'}


def apply_materials(resources, source_resources, plan, refs, maps):
    if plan.get('version')!=1 or set(plan)-{'version','references','tyres','glass'}:raise ValueError('Unsupported Classic semantic material recipe')
    output=dict(resources);audit={};from .r4e_writer import patch_dx_attributes
    for role in ('tyres','glass'):
        rule=plan.get(role)
        if rule is None or rule.get('enabled',True) is False:
            audit[role]={'status':'SOURCE_RETAINED','reason':'Explicit role reset / absent qualified recipe'};continue
        if rule.get('enabled',True) is not True:raise ValueError('Material role enabled must be Boolean')
        if role=='tyres' and rule.get('native_mapping'):
            if sha(source_resources[rule['texture']])!=rule['source_sha256']:raise ValueError('Tyre source atlas changed')
            output,audit[role]=native_tyres(output,source_resources,rule,refs,maps);continue
        variants=rule.get('model_textures',{})
        if set(variants)-set(rule['draws']):raise ValueError('Texture variant has no qualified draws')
        declared=rule
        rule=copy.deepcopy(rule);rule['draws']={k:v for k,v in rule['draws'].items() if k not in variants}
        expected=(0,0)if role=='tyres'else(1,0)
        source_name=rule['texture'];source=source_resources[source_name]
        if sha(source)!=rule['source_sha256']:raise ValueError('Classic semantic source atlas changed')
        texture=parse_dxt_bytes(source);pixels=bytearray(texture.bgra)
        ref=refs[rule['reference_model']];rd=parse_dx_bytes(ref).physical_draws[rule['reference_draw']]
        if tuple(rd.flags_0x20[:2])!=expected:raise ValueError('Stock semantic reference opacity differs')
        diffuse_ref=parse_dxt_bytes(refs[rule['reference_diffuse']]);envraw=refs[rule['reference_environment']]
        envname='classic-'+role+'-env-'+sha(envraw)[:16]+'-tga';output[envname+'.dxt']=envraw
        if role=='tyres':
            if set(texture.bgra[3::4])!={255}:raise ValueError('Opaque tyre atlas must be explicitly opaque')
            a,b=rule['tread_v_range']
            if not 0<=a<b<=1:raise ValueError('Invalid tread UV range')
            median=[sorted(diffuse_ref.bgra[k::4])[diffuse_ref.width*diffuse_ref.height//2]for k in range(3)]
            for y in range(texture.height):
                v=(y+.5)/texture.height
                for x in range(texture.width):
                    pixel=median
                    if a<=v<b:
                        rx=x*diffuse_ref.width//texture.width;ry=min(diffuse_ref.height-1,int((v-a)/(b-a)*diffuse_ref.height));start=(ry*diffuse_ref.width+rx)*4;pixel=diffuse_ref.bgra[start:start+3]
                    start=(y*texture.width+x)*4;pixels[start:start+4]=bytes(pixel)+b'\xff'
            boundary='Explicit stored-UV tread band; neutral sidewall from stock tread median, no copied GT lettering. Source UV wrapping retained.'
        else:
            alpha=rule['window_alpha_value']
            if type(alpha)is not int or not 1<=alpha<255:raise ValueError('Explicit glass opacity-owner byte required')
            if set(texture.bgra[3::4])!={alpha,255}:raise ValueError('Mixed or changed glass atlas requires requalification')
            if len(rule['reference_rgb'])!=3 or any(type(v)is not int or not 0<=v<=255 for v in rule['reference_rgb']):raise ValueError('Invalid stock glass tint')
            # Only qualified optical texels; opaque border pixels stay exact.
            target_alpha=rule['reference_alpha']
            if type(target_alpha)is not int or not 1<=target_alpha<255 or target_alpha not in diffuse_ref.bgra[3::4]:raise ValueError('Glass opacity is not present in stock reference')
            rgb=rule['reference_rgb'];bgra=bytes(reversed(rgb))+bytes([target_alpha])
            if bgra not in (diffuse_ref.bgra[i:i+4] for i in range(0,len(diffuse_ref.bgra),4)):raise ValueError('Glass RGB/alpha is not an exact stock texel')
            rm=parse_dx_bytes(ref);ri=set(rm.draw_global_indices(rd))
            if not any(rm.vertices.colors[i*4:i*4+3]==bytes([rule['vertex_rgb']]*3) for i in ri):raise ValueError('Glass vertex tint is not present in reference draw')
            optical=rule.get('optical_bgra')
            if optical is not None and (len(optical)!=4 or any(type(v)is not int or not 0<=v<=255 for v in optical) or optical[3]!=alpha):raise ValueError('Invalid qualified optical colour mask')
            selected=bytearray(old==alpha and (optical is None or texture.bgra[i*4:i*4+4]==bytes(optical)) for i,old in enumerate(texture.bgra[3::4]))
            if not any(selected):raise ValueError('Qualified optical colour has no texels')
            for i,visible in enumerate(selected):
                if visible:pixels[i*4:i*4+4]=bgra
            if rule.get('optical_sampling')=='stock_connected_regions':
                from collections import deque
                count=texture.width*texture.height
                if count>1024*1024:raise ValueError('Optical sampling exceeds qualified working-set budget')
                visited=bytearray(count);mask=selected
                for start in range(count):
                    if visited[start] or not mask[start]:continue
                    visited[start]=1;queue=deque([start]);component=[]
                    while queue:
                        i=queue.popleft();component.append(i);x,y=i%texture.width,i//texture.width
                        neighbours=[]
                        if x:neighbours.append(i-1)
                        if x+1<texture.width:neighbours.append(i+1)
                        if y:neighbours.append(i-texture.width)
                        if y+1<texture.height:neighbours.append(i+texture.width)
                        for n in neighbours:
                            if not visited[n] and mask[n]:visited[n]=1;queue.append(n)
                    xs=[i%texture.width for i in component];ys=[i//texture.width for i in component];x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys)
                    for i,x,y in zip(component,xs,ys):
                        rx=min(diffuse_ref.width-1,int((x-x0)/max(1,x1-x0)*(diffuse_ref.width-1)))
                        ry=min(diffuse_ref.height-1,int((y-y0)/max(1,y1-y0)*(diffuse_ref.height-1)))
                        j=(ry*diffuse_ref.width+rx)*4;pixels[i*4:i*4+4]=diffuse_ref.bgra[j:j+4]
                boundary='Source-qualified optical alpha regions sampled from original stock windscreen texture, with original UVs and opaque labels/frames retained. Native zones unchanged; no new Lancer broken controllers.'
            if rule.get('optical_sampling')!='stock_connected_regions':boundary='Only source-qualified uniform optical texels replaced by explicit stock glass RGB/alpha; other pixels and existing native zones remain exact. Lancer has no qualified broken-glass controllers.'
            if rule.get('preserve_overlay_colour'):boundary+=' Mixed front banner retains source vertex RGB and non-environment pass; no independent reflection mask is claimed.'
        # Author buffer is stored/native BGRA; the shared encoder accepts RGBA.
        # Keep orientation explicit and verify every output native texel.
        rgba=bytearray(pixels);rgba[0::4]=pixels[2::4];rgba[2::4]=pixels[0::4]
        generated=encode_dxt_pixels(texture,bytes(rgba),texture.width,texture.height,row_policy=PNG_ROWS_PRESERVE_STORED)
        if parse_dxt_bytes(generated).bgra!=bytes(pixels):raise ValueError('Classic material encoding changed channel order or orientation')
        import zlib
        generated=generated[:8]+struct.pack('<I',zlib.crc32(generated[20:])&0xffffffff)+generated[12:]
        name='classic-'+role+'-'+sha(generated)[:16]+'-tga';output[name+'.dxt']=generated
        records=[]
        for model,ids in rule['draws'].items():
            original=parse_dx_bytes(source_resources[model]);raw=output[model]
            mapping=maps.get(model,{i:i for i in range(len(original.physical_draws))})
            for source_id in ids:
                d=original.physical_draws[source_id]
                if d.texture_tuple[0]+'.dxt'!=source_name or tuple(d.flags_0x20[:2])!=expected:raise ValueError('Semantic draw source/opacity ownership differs')
                target=mapping[source_id]
                # Mixed banner/glass retains its qualified non-environment
                # path; both native binding and presence mask stay consistent.
                raw=_tail(raw,rule['reference_draw'],ref,target,name,'Null'if rule.get('preserve_overlay_colour')else envname)
                records.append({'model':model,'source_draw':source_id,'output_draw':target})
            if role=='glass' and not rule.get('preserve_overlay_colour'):
                m=parse_dx_bytes(raw);colors=bytearray(m.vertices.colors)
                for source_id in ids:
                    target=mapping[source_id];used=set(m.draw_global_indices(m.physical_draws[target]))
                    if any(used.intersection(m.draw_global_indices(other))for other in m.physical_draws if other.draw_index!=target):raise ValueError('Glass vertex RGB shares unrelated draws')
                    for i in used:colors[i*4:i*4+3]=bytes([rule['vertex_rgb']]*3)
                raw=patch_dx_attributes(raw,colors=bytes(colors)).data
            output[model]=raw
        audit[role]={'status':'APPLIED_QUALIFIED_STOCK_SEMANTICS','source_atlas_sha256':sha(source),'generated_atlas_sha256':sha(generated),'native_reference_sha256':sha(ref),'records':records,'boundary':boundary,'vertex_alpha_preserved':True}
        for model,variant in variants.items():
            child={**declared,'texture':variant['texture'],'source_sha256':variant['sha256'],'draws':{model:declared['draws'][model]}}
            child.pop('model_textures',None);child.pop('additional_atlases',None)
            output,detail=apply_materials(output,source_resources,{'version':1,role:child},refs,maps)
            audit[role].setdefault('variants',{})[model]=detail[role]
        for variant in declared.get('additional_atlases',[]):
            child={**declared,**variant};child.pop('model_textures',None);child.pop('additional_atlases',None)
            output,detail=apply_materials(output,source_resources,{'version':1,role:child},refs,maps)
            audit[role].setdefault('additional_atlases',[]).append(detail[role])
    return output,audit
