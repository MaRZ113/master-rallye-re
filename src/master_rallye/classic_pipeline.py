"""Semantic, opt-in Classic stage plan for independently qualified source imports.

Version 1 remains the frozen Lancer oracle. Version 2 composes the existing
geometry, wheel, overlay and native material kernels, without requiring a
particular paint atlas, vehicle name or a lossy operation on every import.
"""
from .dx import parse_dx_bytes
from .topology_writer import source_geometry,rebuild_topology
from .classic_geometry import simplify_radial_cover
from .classic_wheels import classic_rim,map_embedded_wheels

ROLES={'paint','trim','decal','glass','tyre','rim','lamp','brake','crew','collision','shadow','environment','unknown'}

def convert(resources,recipe,stock_wheel,stock_brake,material_references=None):
    from .classic_style import digest,json_bytes,metrics,prune_overlays
    if recipe.get('version')!=2 or recipe.get('source_format')not in ('GT3 ModelSet1','GT4 ModelSet2'):raise ValueError('Unsupported semantic Classic recipe')
    if set(recipe)-{'version','source_format','source_identity','class_reference','source_models','stock_wheel_sha256','stock_brake_sha256','stock_wheel_family','stock_brake_family','limitations','roles','geometry','wheel','omit_decal_draws','semantic_materials'}:raise ValueError('Unknown semantic Classic stage')
    if not recipe.get('source_identity')or not recipe.get('class_reference')or not recipe.get('limitations'):raise ValueError('Classic source/class reference and limits required')
    for name,expected in recipe['source_models'].items():
        if name not in resources or digest(resources[name])!=expected:raise ValueError('Classic requires immutable source-import baseline: '+name)
    if any(n not in recipe['source_models']for n in ('car.dx','complete.dx','wheel.dx')):raise ValueError('Classic source model identities incomplete')
    if any(n not in recipe['source_models']for n in resources if n.endswith(('.dx','.dxt'))):raise ValueError('Classic immutable texture/model identities incomplete')
    if digest(stock_wheel)!=recipe['stock_wheel_sha256']or digest(stock_brake)!=recipe['stock_brake_sha256']:raise ValueError('Stock reference changed')
    output=dict(resources);roles={};maps={}
    for name in ('car.dx','complete.dx','wheel.dx'):
        m=parse_dx_bytes(resources[name]);maps[name]={d.draw_index:d.draw_index for d in m.physical_draws}
    for approval in recipe.get('roles',[]):
        if set(approval)!={'resource','draw','role','evidence'}or approval['role']not in ROLES or not isinstance(approval['evidence'],str)or not approval['evidence'].strip():raise ValueError('Invalid semantic role approval')
        name,i=approval['resource'],approval['draw']
        if type(i)is not int or name not in maps or i not in maps[name]or (name,i)in roles:raise ValueError('Invalid/duplicate approved draw identity')
        roles[name,i]=approval['role']
    def require(name,ids,allowed):
        if len(set(ids))!=len(ids)or any(roles.get((name,i),'unknown')not in allowed for i in ids):raise ValueError('Operation lacks explicit qualified semantic roles')
    audit={'recipe_sha256':digest(json_bytes(recipe)),'source':recipe['source_models'],'source_identity':recipe['source_identity'],'class_reference':recipe['class_reference'],'geometry':{},'stages':[],'before':metrics(resources),'limitations':recipe['limitations'],'runtime_qualified':False}
    changes={n:{}for n in maps}
    for step in recipe.get('geometry',[]):
        if set(step)!={'resource','draw','operation','expected_boundary'}or step['operation']!='radial_cover':raise ValueError('Unsupported geometry stage')
        name,i=step['resource'],step['draw'];require(name,[i],{'paint','trim'})
        d=parse_dx_bytes(resources[name]).physical_draws[i]
        if d.control_words or d.tag!=2 or tuple(d.flags_0x20)!=(0,0,1,1)or i in changes[name]:raise ValueError('Geometry stage cannot modify native controllers or alpha surfaces')
        changes[name][i],report=simplify_radial_cover(source_geometry(parse_dx_bytes(resources[name]))[i],expected_boundary=step['expected_boundary'])
        audit['stages'].append({'stage':'geometry','resource':name,'draw':i,**report})
    if recipe.get('wheel'):
        cfg=recipe['wheel'];require('wheel.dx',cfg['rim_draws'],{'rim'})
        for group in cfg['embedded_groups']:require('complete.dx',[group['draws'][i]for i in cfg['rim_draws']],{'rim'})
        if cfg.get('mode')=='stock_insert':
            from .classic_wheels import replace_source_rim
            refs=material_references or {}
            if cfg['environment_reference']not in refs:raise ValueError('Pinned rim environment reference required')
            output,report=replace_source_rim(output,stock_wheel,cfg,refs[cfg['environment_reference']])
            audit['stages'].append({'stage':'wheel','report':report})
        else:
            edits,texture,report=classic_rim(resources['wheel.dx'],stock_wheel,resources[cfg['texture']],cfg)
            embedded,evidence=map_embedded_wheels(resources['wheel.dx'],resources['complete.dx'],cfg['embedded_groups'],edits)
            changes['wheel.dx'].update(edits);changes['complete.dx'].update(embedded);output[cfg['texture']]=texture
            audit['stages'].append({'stage':'wheel','report':report,'instances':evidence})
    for name,edits in changes.items():
        if edits:output[name]=rebuild_topology(resources[name],edits,bounds_mode='recompute').data
    for name,ids in recipe.get('omit_decal_draws',{}).items():
        require(name,ids,{'decal'});output[name],maps[name]=prune_overlays(output[name],ids,stock_brake)
        audit['stages'].append({'stage':'livery','resource':name,'explicit_omitted_overlays':ids})
    if recipe.get('semantic_materials'):
        from .classic_materials import apply_materials
        for role,rule in recipe['semantic_materials'].items():
            if role in ('version','references') or not rule.get('enabled',True):continue
            if role not in ('tyres','glass'):raise ValueError('Unsupported semantic material role')
            for name,ids in rule['draws'].items():require(name,ids,{'tyre'}if role=='tyres'else{'glass'})
            for variant in rule.get('additional_atlases',[]):
                for name,ids in variant['draws'].items():require(name,ids,{'tyre'}if role=='tyres'else{'glass'})
        # Native material operations retain their own source/vertex/alpha proofs.
        output,audit['semantic_materials']=apply_materials(output,resources,recipe['semantic_materials'],material_references or {},maps)
        audit['stages'].append({'stage':'materials','report':'native role-specific opacity/ownership checks retained'})
    for name in maps:
        audit['geometry'][name]={'draw_map':maps[name]}
        a,b=parse_dx_bytes(resources[name]),parse_dx_bytes(output[name])
        if not b.diagnostics.validated or resources[name][a.trailing.offset:a.collision.unparsed_offset]!=output[name][b.trailing.offset:b.collision.unparsed_offset]:raise ValueError('Classic native validation/collision preservation failed')
    audit['stages'].append({'stage':'paint','mode':'preserve_source','report':'Original source colorway RGB/UV retained; livery removal is independent and explicit.'})
    audit['after']=metrics(output)
    return output,audit,maps
