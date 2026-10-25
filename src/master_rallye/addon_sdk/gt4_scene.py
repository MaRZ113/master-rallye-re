"""Source-command GT4 scene qualification, independent of legacy OBJ/YAML dumps."""
from __future__ import annotations
from collections import Counter
from .gt4_source import modelset,shape_geometry
from .gt4_commands import command_graph,binding_trace
from .gt4_materials import interpret,classify
from .gt4_textures import model_texture_sets


def reconstruct(data,*,model_index=0,lod=0,colour=0,callbacks=None,freeze_morphs=False,vm_tween_callback_profile=None):
    tween_callbacks=set()
    if vm_tween_callback_profile is not None:
        cfg=vm_tween_callback_profile
        if not isinstance(cfg,dict) or set(cfg)!={'engine_sha256','vm_context','callback_indices','evidence'} or cfg['engine_sha256']!='962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0' or cfg['vm_context']!='GT4Beta.CarModel.callback_vtable_006C15B8' or not isinstance(cfg['evidence'],str) or not cfg['evidence']:raise ValueError('unqualified VM callback engine semantics')
        if not isinstance(cfg['callback_indices'],list) or any(type(i)is not int or i not in (1,2,3,4) for i in cfg['callback_indices']) or len(set(cfg['callback_indices']))!=len(cfg['callback_indices']):raise ValueError('unqualified VM tween callback index')
        tween_callbacks=set(cfg['callback_indices'])
    m=modelset(data)
    if not 0<=model_index<len(m['models']):raise ValueError('model index out of source bounds')
    textures=model_texture_sets(data,m['base'],colour)
    geometries=[shape_geometry(s) for s in m['shapes']]
    graphs=[];account={i:[] for i in range(len(geometries))}
    for i,record in enumerate(m['models']):
        start=record['commands_offset']
        end=m['models'][i+1]['commands_offset'] if i+1<len(m['models']) else min(s['offset'] for s in m['shapes'] if s['offset']>start)
        graph=command_graph(data,start,end);graphs.append(graph)
        # Full reachable graph accounts for every stored shape, including
        # conditional lights/wheels and alternative LODs. It does not render them all.
        for node in graph['nodes']:
            if node['opcode'] in (4,5,53):
                index=node['operands'][0]
                if index not in account:raise ValueError('shape command outside source table')
                account[index].append({'model':i,'command_offset':node['offset'],'tween':node['opcode']==53})
    trace=binding_trace(graphs[model_index],lod=lod,callbacks=callbacks)
    if trace['blocked_at']:raise ValueError(f'unresolved selected source command path: {trace["blocked_at"]}')
    draws=[];unsupported=[]
    for call_no,call in enumerate(trace['draws']):
        g=geometries[call['shape']];state=interpret(call['commands'])
        for packet_no,p in enumerate(g['packets']):
            issues=[];tex=None
            morph=all(v.get('morph_target') for v in g['vertices'])
            frozen=freeze_morphs and morph and call['transforms'] and all(n.get('opcode') in (89,90) for n in call['transforms'])
            # Original Beta CarModel callback indices1..4 only set the shape
            # tween ratio (clamped scalar), never a spatial matrix. Their
            # persistence cannot move a following shape lacking morph channels.
            non_spatial=[n for n in call['transforms'] if n.get('opcode') in (89,90) and n.get('operands',[None])[0] in tween_callbacks]
            spatial=[n for n in call['transforms'] if n not in non_spatial]
            if spatial and not frozen:issues.append('unresolved instance transforms')
            if morph and non_spatial and not freeze_morphs:issues.append('unresolved tween weight')
            if call['tween'] is not None:issues.append('unresolved tween weight')
            if state['unknown']:issues.append('untranslated source state')
            external=call['texture_table']['kind']=='external'
            if p['texture'] not in (0,511) and not external:
                set_index=call['texture_table']['index']
                if set_index>=len(textures):raise ValueError('texture set index outside source table')
                tex=textures[set_index].texture(p['texture']-1)
            elif external or p['texture']==511:issues.append('runtime-generated external texture / texgen unavailable')
            if p['untranslated_attributes']:
                # Vertex colours are decoded, not unknown packed normals.
                other=[a for a in p['untranslated_attributes'] if not (a['address']==0xc080 and a.get('format')==[2,4])]
                if other:issues.append('untranslated packet attributes')
            triangles=g['triangles'][p['first_triangle']:p['first_triangle']+p['triangle_count']]
            item={'source_shape':call['shape'],'packet':packet_no,'call':call_no,'command_offset':call['command_offset'],
                  'state':state,'purpose':classify(call,state,p),'vertices':g['vertices'],'triangles':triangles,
                  'texture':tex,'gif':p['gif'],'material':m['materials'][p['material']-1] if p['material'] else None,
                  'issues':issues,'transforms':call['transforms'],'tween':call['tween'],
                  **({'qualified_tween_callbacks':non_spatial} if non_spatial else {}),
                  'pose_fallback':'explicit static first morph endpoint; original target retained; VM animation not reconstructed' if frozen else None}
            draws.append(item)
            if issues:unsupported.append({'shape':call['shape'],'packet':packet_no,'issues':issues})
    inventory=[]
    for i,g in enumerate(geometries):
        flags=m['shapes'][i]['flags']
        inventory.append({'shape':i,'triangles':len(g['triangles']),'vertices':len(g['vertices']),
            'source_flags':flags,'reachable_uses':account[i],'selected_calls':sum(c['shape']==i for c in trace['draws']),
            'attributes':dict(Counter(('normal' if v['normal'] is not None else 'no_normal') for v in g['vertices'])),
            'classification':'selected draw state' if any(c['shape']==i for c in trace['draws']) else
                             'alternate model/LOD/conditional pass' if account[i] else 'unreferenced stored shape; unresolved purpose'})
    return {'source_sha256':m['sha256'],'model_index':model_index,'lod':lod,'callbacks':callbacks or {},'draws':draws,
            'report':{'source_sha256':m['sha256'],'shape_inventory':inventory,'selected_model':model_index,'selected_lod':lod,
                      'selected_shapes':len(set(c['shape'] for c in trace['draws'])),'selected_packets':len(draws),
                      'unsupported':unsupported,'texture_sets':[{'textures':len(t.registers),'transfers':t.transfers} for t in textures],
                      'material_lighting':'source material/normal values retained; VU lighting program not reconstructed',
                      'geometry_accounted':all(account.values()),'source_unchanged':True}}
