"""Explicit, hash-qualified Classic conversions of immutable imported resources.

No source-name heuristics, global polygon targets, or retail writes. Recipes
declare every lossy operation. Unknown surfaces survive unchanged.
"""
import copy
import hashlib
import json
from pathlib import Path
from dataclasses import replace
from .dx import parse_dx_bytes
from .dxt import parse_dxt_bytes,encode_png,encode_dxt_pixels,PNG_ROWS_FLIP_VERTICAL
from .topology_writer import source_geometry,rebuild_topology
from .scene_dx_writer import ScenePart,write_scene_dx
from .classic_geometry import simplify_radial_cover
from .classic_wheels import classic_rim,map_embedded_wheels
from .surface_authoring import apply_surface_edits
from .preview_scene import logical_cases
from .addon_sdk.native_brakes import write_brake_scene


def digest(raw):return hashlib.sha256(raw).hexdigest()


def json_bytes(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')


def draw_attributes(g):
    return (tuple((v.position,v.normal,v.color,v.uvs)for v in g.vertices),g.triangles)


def draw_material(d):
    return (d.texture_tuple,tuple(d.flags_0x20),d.unknown_0x14,d.unknown_0x18,d.unknown_0x1c_float,d.unknown_0x24)


def prune_overlays(raw,ids,stock):
    """Remove only explicitly selected ordinary blended overlays, retain cases."""
    m=parse_dx_bytes(raw);g=source_geometry(m);cases,_=logical_cases(m);ids=set(ids)
    if any(i not in g or i in cases or m.physical_draws[i].tag!=2 or m.physical_draws[i].control_words or tuple(m.physical_draws[i].flags_0x20)!=(1,0,1,1) for i in ids):
        raise ValueError('Only explicit ordinary blended decal draws may be omitted')
    parts={d.draw_index:ScenePart(g[d.draw_index],d.texture_tuple,bool(d.flags_0x20[0]),bool(d.flags_0x20[1]),bool(d.unknown_0x24&4),bool(d.flags_0x20[2]))for d in m.physical_draws}
    kept=[i for i in g if i not in ids];mapping={old:new for new,old in enumerate(kept)}
    if cases:
        sm=parse_dx_bytes(stock);template=stock[:sm.trailing.offset]+raw[m.trailing.offset:]
        body=[p for i,p in parts.items()if i not in ids and i not in cases]
        off=[p for i,p in parts.items()if i in cases and cases[i][1]==1]
        on=[p for i,p in parts.items()if i in cases and cases[i][1]==2]
        output=write_brake_scene(template,body,off,on[:-1],on[-1:])
    else:output=write_scene_dx(raw,[parts[i]for i in kept])
    n=parse_dx_bytes(output);ng=source_geometry(n)
    if not n.diagnostics.validated:raise ValueError('Overlay removal failed native validation')
    if raw[m.trailing.offset:m.collision.unparsed_offset]!=output[n.trailing.offset:n.collision.unparsed_offset]:raise ValueError('Overlay removal changed collision')
    for old,new in mapping.items():
        if draw_attributes(g[old])!=draw_attributes(ng[new])or draw_material(m.physical_draws[old])!=draw_material(n.physical_draws[new]):raise ValueError('Retained draw changed while pruning')
    return output,mapping


def rebase_mechanics(before,after,definition,mapping):
    """A separate strict path for topology changes outside selected mechanics."""
    from .addon_sdk.visual_fitment import _selection
    a,_=_selection(before,definition);b=parse_dx_bytes(after);ga=source_geometry(a);gb=source_geometry(b)
    if before[a.trailing.offset:a.collision.unparsed_offset]!=after[b.trailing.offset:b.collision.unparsed_offset]:raise ValueError('Classic changed collision')
    result=copy.deepcopy(definition)
    for group in result['groups']:
        new=[]
        for old in group['draw_indices']:
            target=mapping[old]
            if draw_attributes(ga[old])!=draw_attributes(gb[target])or draw_material(a.physical_draws[old])!=draw_material(b.physical_draws[target]):raise ValueError('Classic changed protected mechanics')
            new.append(target)
        group['draw_indices']=new
    result['source_sha256']=digest(after);_selection(after,result)
    return result


def metrics(resources):
    models={};names=set()
    for name,raw in resources.items():
        if not name.endswith('.dx'):continue
        m=parse_dx_bytes(raw)
        models[name]={'triangles':m.triangle_count,'draws':len(m.physical_draws),'vertices':m.vertex_count,'sha256':digest(raw)}
        names.update(s.value+'.dxt' for d in m.physical_draws for s in d.texture_slots if s.value and s.value.casefold()!='null')
    textures={n:parse_dxt_bytes(resources[n])for n in sorted(names)}
    return {'models':models,'textures':len(textures),'texture_disk_bytes':sum(len(resources[n])for n in textures),'native_rgba_cache_bytes':sum(t.width*t.height*4 for t in textures.values()),'texture_dimensions':{n:[t.width,t.height]for n,t in textures.items()},'cache_note':'Measured unique referenced resources; original FEED loader charges width*height*4. Not an FPS claim.'}


def paint_texture(raw,rule):
    """Regenerate explicitly qualified paint rectangles, preserving all others."""
    from PIL import Image,ImageDraw
    from io import BytesIO
    t=parse_dxt_bytes(raw)
    if digest(raw)!=rule['source_sha256']:raise ValueError('Paint atlas changed')
    if t.width*t.height*4>16*1024*1024 or len(rule['rectangles'])>64 or len(rule.get('graphics',[]))>64:raise ValueError('Classic paint working-set or region budget exceeded')
    if len(rule['base_rgb'])!=3 or any(type(c)is not int or not 0<=c<=255 for c in rule['base_rgb'])or type(rule['paint_reflection_alpha'])is not int or not 0<=rule['paint_reflection_alpha']<=255:raise ValueError('Paint RGB/reflection alpha must be explicit bytes')
    size=rule['opaque_size']
    if len(size)!=2 or any(type(n)is not int or not 1<=n<=16384 or n&(n-1)for n in size)or size[0]*size[1]*4>16*1024*1024:raise ValueError('Classic opaque target exceeds bounded power-of-two texture budget')
    im=Image.open(BytesIO(encode_png(t))).convert('RGBA');px=im.load();changed=0
    mask=Image.new('1',im.size);mask_draw=ImageDraw.Draw(mask)
    for box in rule['rectangles']:
        x0,y0,x1,y1=box
        if any(type(n)is not int for n in box):raise ValueError('Paint rectangles require integer texel coordinates')
        if not 0<=x0<x1<=t.width or not 0<=y0<y1<=t.height:raise ValueError('Paint rectangle outside atlas')
        mask_draw.rectangle((x0,y0,x1-1,y1-1),fill=1)
        for y in range(y0,y1):
            for x in range(x0,x1):px[x,y]=(*rule['base_rgb'],px[x,y][3]);changed+=1
    # Characteristic paint graphics are explicit editable source-space polygons,
    # independently regenerated from small sponsor/decal texture ownership.
    for graphic in rule.get('graphics',[]):
        color=graphic['rgb'];points=graphic['polygon']
        if len(color)!=3 or any(type(c)is not int or not 0<=c<=255 for c in color)or not 3<=len(points)<=64 or any(len(q)!=2 or not 0<=q[0]<=t.width or not 0<=q[1]<=t.height for q in points):raise ValueError('Invalid qualified livery polygon')
        field=Image.new('1',im.size);ImageDraw.Draw(field).polygon([tuple(q)for q in points],fill=1)
        for y in range(t.height):
            for x in range(t.width):
                if mask.getpixel((x,y))and field.getpixel((x,y)):px[x,y]=(*color,px[x,y][3])
    outputs={};audit=[]
    for role,size in [('opaque',rule['opaque_size']),('cutout',[t.width,t.height])]:
        target=im.copy()
        if role=='opaque':
            # Opaque environment alpha means reflection weighting. Normalize
            # only author-qualified painted texels; never glass/cutout coverage.
            for box in rule['rectangles']:
                for y in range(box[1],box[3]):
                    for x in range(box[0],box[2]):
                        p=target.getpixel((x,y));target.putpixel((x,y),(*p[:3],rule['paint_reflection_alpha']))
        if tuple(size)!=target.size:target=Image.merge('RGBA',[c.resize(size,Image.Resampling.LANCZOS)for c in target.split()])
        # FEED header supports new power-of-two sizes via the existing budget
        # resizer; conversion itself never rewrites the retail source.
        template=t
        if tuple(size)!=(t.width,t.height):
            import struct
            w,h=size
            if any(type(n)is not int or n<1 or n&(n-1)for n in size):raise ValueError('Classic dimensions must be powers of two')
            template=replace(t,width=w,height=h,header=struct.pack('<5I',0xfeed,t.word_0x04,0,w,h))
        output=encode_dxt_pixels(template,target.tobytes(),*target.size,row_policy=PNG_ROWS_FLIP_VERTICAL)
        import zlib,struct
        output=output[:8]+struct.pack('<I',zlib.crc32(output[20:])&0xffffffff)+output[12:]
        if role=='cutout' and parse_dxt_bytes(output).bgra[3::4]!=t.bgra[3::4]:raise ValueError('Classic changed cutout coverage')
        outputs[role]=output;audit.append({'role':role,'size':size,'sha256':digest(output),'paint_rectangles':rule['rectangles'],'base_rgb':rule['base_rgb'],'source_alpha_exact':role=='cutout'})
    return outputs,{'operation':'regenerated clean paint fields and explicit characteristic livery polygons, not texture shrink alone','source':digest(raw),'qualified_rectangles':rule['rectangles'],'graphics':rule.get('graphics',[]),'protected_pixels':'all texels outside these explicit rectangles; cutout alpha exact','outputs':audit}


def prepare_paint(resources,rule):
    """Keep source shading independent from the Classic decal selection."""
    mode=rule.get('mode','regenerate_fields')
    if mode not in ('regenerate_fields','preserve_source'):raise ValueError('Unknown Classic paint mode')
    raw=resources[rule['texture']]
    if digest(raw)!=rule['source_sha256']:raise ValueError('Paint atlas changed')
    if mode=='preserve_source':
        return {},{'mode':mode,'source':digest(raw),'operation':'Preserve original imported paint RGB, baked shading, alpha and environment bindings. Simplify only separately qualified decal overlays. No new GT rendering claims.','outputs':[]}
    generated,audit=paint_texture(raw,rule);audit['mode']=mode
    return generated,audit


def convert(resources,recipe,stock_wheel,stock_brake,material_references=None):
    """Pure deterministic stage. Input is the original qualified import only."""
    if recipe.get('version')!=1:raise ValueError('Unknown Classic recipe version')
    for name,h in recipe['source_models'].items():
        if digest(resources[name])!=h:raise ValueError('Classic requires immutable source-import baseline: '+name)
    if digest(stock_wheel)!=recipe['stock_wheel_sha256'] or digest(stock_brake)!=recipe['stock_brake_sha256']:raise ValueError('Stock reference changed')
    original=dict(resources);output=dict(resources);audit={'recipe_sha256':digest(json_bytes(recipe)),'source':recipe['source_models'],'geometry':{},'bindings':{},'materials':'Original qualified shader families retained; explicit paint reflection weighting, opaque rim insert; all glass/rubber/lights and unknown draws retained.'}
    wheel=recipe['wheel'];edits,texture,wreport=classic_rim(resources['wheel.dx'],stock_wheel,resources[wheel['texture']],wheel)
    output[wheel['texture']]=texture;output['wheel.dx']=rebuild_topology(resources['wheel.dx'],edits,bounds_mode='recompute').data
    embedded,evidence=map_embedded_wheels(resources['wheel.dx'],resources['complete.dx'],wheel['embedded_groups'],edits)
    audit['wheel']={**wreport,'instances':evidence};maps={}
    generated,paudit=prepare_paint(resources,recipe['paint'])
    audit['paint']=paudit
    env=recipe['paint']['environment_texture']
    preserve_paint=paudit['mode']=='preserve_source'
    if not preserve_paint and digest(resources[env])!=recipe['paint']['environment_sha256']:raise ValueError('Qualified stock paint environment changed')
    for role,raw in generated.items():output[recipe['paint']['targets'][role]+'.dxt']=raw
    for name,plan in recipe['models'].items():
        raw=resources[name];m=parse_dx_bytes(raw);g=source_geometry(m);changes=dict(embedded)if name=='complete.dx' else {};reports=[]
        for i in plan['radial_covers']:
            d=m.physical_draws[i]
            if d.tag!=2 or d.control_words or tuple(d.flags_0x20)!=(0,0,1,1):raise ValueError('Cover is not ordinary opaque bodywork')
            changes[i],report=simplify_radial_cover(g[i]);reports.append({'draw':i,**report})
        raw=rebuild_topology(raw,changes).data
        # Texture Binding v2 validates native opacity ownership on every owner.
        bindings=[]
        for i in plan['paint_draws']:
            d=m.physical_draws[i]
            if d.texture_tuple[0]+'.dxt'!=recipe['paint']['texture']:raise ValueError('Paint ownership differs from recipe')
            if preserve_paint:continue
            role='cutout'if d.flags_0x20[0] else'opaque';target=recipe['paint']['targets'][role]
            slots={'0':target}
            if role=='opaque':slots['1']=env.removesuffix('.dxt')
            edit={'draw_id':i,'bindings':slots}
            if role=='opaque':edit['reflection_strength']=recipe['paint'].get('reflection_strength',1.)
            bindings.append(edit)
        def provider(stem):return output[stem+'.dxt']
        if bindings:raw=apply_surface_edits(raw,bindings,source_sha256=digest(raw),texture_provider=provider).data
        output[name],maps[name]=prune_overlays(raw,plan['omit_decal_draws'],stock_brake)
        audit['geometry'][name]={'covers':reports,'omitted_ordinary_overlay_draws':plan['omit_decal_draws'],'omitted_decal_roles':plan['omitted_decal_roles'],'draw_map':maps[name]}
        audit['bindings'][name]=bindings
    if recipe.get('semantic_materials'):
        from .classic_materials import apply_materials
        output,audit['semantic_materials']=apply_materials(output,original,recipe['semantic_materials'],material_references or {},maps)
        audit['materials']='Versioned source-qualified paint, rim, rubber and optical glass recipe. Unknown surfaces and all native controller records retained; see semantic material boundaries.'
    if preserve_paint:
        for name,plan in recipe['models'].items():
            old,new=parse_dx_bytes(original[name]),parse_dx_bytes(output[name]);a,b=source_geometry(old),source_geometry(new)
            for i in plan['paint_draws']:
                j=maps[name][i]
                if draw_attributes(a[i])!=draw_attributes(b[j])or draw_material(old.physical_draws[i])!=draw_material(new.physical_draws[j]):raise ValueError('Classic changed protected source paint')
        if output.get(recipe['paint']['texture'])!=original[recipe['paint']['texture']]:raise ValueError('Classic changed protected source paint atlas')
        audit['paint']['source_draws_attributes_and_materials_exact']=True
    # Deliberate closure, not a copy of all source atlases/donor resources.
    required=set()
    for n in ('car.dx','complete.dx','wheel.dx'):
        required.add(n);m=parse_dx_bytes(output[n]);required.update(s.value+'.dxt'for d in m.physical_draws for s in d.texture_slots if s.value and s.value.casefold()!='null')
    required.update(n for n in resources if not n.endswith(('.dx','.dxt')))
    output={n:output[n]for n in sorted(required)}
    audit['before']=metrics(original);audit['after']=metrics(output)
    audit['limitations']=recipe['limitations'];audit['runtime_qualified']=False
    return output,audit,maps
