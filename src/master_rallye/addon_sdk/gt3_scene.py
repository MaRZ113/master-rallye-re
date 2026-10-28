"""GT3 ModelSet1 adapter over shared bounded VIF, GS and command readers.

Source bytes remain authoritative. GT3-only lighting opcodes and callback
transforms are retained as unresolved, never discarded by the GT4 interpreter.
"""
import math
from master_rallye.gt3_source import Reader,inspect_car
from .gt4_source import vif,shape_geometry
from .gt4_commands import command_graph,binding_trace
from .gt4_textures import TextureSet
from .gt3_materials import interpret

GT3_CORE_SHA256='fdcea2aa43231873592adee0fb96499f2e40979e0269191af1eafcf95da12b0b'

def packet_has_uvs(vertices,triangles):
    """An image binding requires original finite UVs on every used vertex."""
    ids={i for t in triangles for i in t}
    return bool(ids)and all(vertices[i]['uv']is not None and len(vertices[i]['uv'])==2 and all(math.isfinite(v)for v in vertices[i]['uv'])for i in ids)

def reconstruct(data,*,component='body',model_index=0,lod=0,colour=0,callbacks=None,engine_sha256=None,strict_textures=True,external_texture_bindings=None):
    source=inspect_car(data);r=Reader(data)
    if component not in ('body','wheel'):raise ValueError('GT3 component must be body or wheel')
    m=source[component];base=m['offset']
    if type(colour)is not int or not 0<=colour<m['source_colourway_count']:raise ValueError('GT3 colourway outside original variants')
    if type(model_index)is not int or not 0<=model_index<m['models']:raise ValueError('GT3 model index')
    mt,st,mat,tt,bt,vt,vm=r.unpack('<7I',base+32)
    if len(m['texture_sets'])>8:raise ValueError('GT3 decoded GS-memory budget')
    textures=[TextureSet(data,t['offset'],clut_variation=colour if t['source_clut_variants']else 0)for t in m['texture_sets']]
    bindings=external_texture_bindings or {}
    for key,binding in bindings.items():
        if not isinstance(key,str)or not key.isdecimal()or set(binding)!={'texture_set','texture','evidence'}or not isinstance(binding['evidence'],str)or not binding['evidence'].strip():raise ValueError('GT3 external binding requires explicit source evidence')
        ti,tx=binding['texture_set'],binding['texture']
        if type(ti)is not int or type(tx)is not int or not 0<=ti<len(textures)or not 0<=tx<len(textures[ti].registers):raise ValueError('GT3 external texture binding outside source tables')
    mo=base+mat
    if m['material_variants']:
        if colour>=len(m['material_variants']):raise ValueError('GT3 material variant table incomplete')
        mo=m['material_variants'][colour]['offset']
    materials=[]
    for i in range(m['material_count']):
        values=r.unpack('<16f',mo+i*80)
        if not all(math.isfinite(v)for v in values):raise ValueError('GT3 nonfinite source material')
        materials.append({'index':i+1,'ambient':values[:4],'diffuse':values[4:8],'specular':values[8:12],'unknown_colour':values[12:]})
    boundaries=sorted(set(m['model_command_offsets']+[s['offset']for s in m['shapes']]+[base+mat,base+tt,base+bt,len(data)]))
    graphs=[]
    for start in m['model_command_offsets']:
        end=next(p for p in boundaries if p>start)
        graphs.append(command_graph(data,start,end))
    trace=binding_trace(graphs[model_index],lod=lod,callbacks=callbacks,extra_state_opcodes=(40,49,50,51,54))
    if trace['blocked_at']:raise ValueError('GT3 selected source path unresolved: '+str(trace['blocked_at']))
    selected={c['shape']for c in trace['draws']};geometries={}
    vertex_budget=0
    for index in selected:
        if not 0<=index<len(m['shapes']):raise ValueError('GT3 shape call outside table')
        s=m['shapes'][index];off=s['offset'];packets=[]
        vertex_budget+=s['strip_vertices_header']
        if vertex_budget>200000:raise ValueError('GT3 selected geometry budget')
        for j in range(s['packets']):
            rel,qwords,flags=r.unpack('<IHH',off+16+j*8);start=off+rel;end=start+qwords*16
            packets.append({'offset':start,'end':end,'material':flags>>9,'texture':flags&511,'commands':vif(data,start,end)})
        # Original SCUS_971.02 CORE shape submitter 0x24e4a0 emits STMASK
        # 0xc0c0c0c0 before descriptor DMA: XY are DATA for every cycle row.
        # Unknown editions must recover their own prefix instead of guessing.
        mask=0xc0c0c0c0 if engine_sha256==GT3_CORE_SHA256 else None
        geometries[index]=shape_geometry({'packets':packets,'header_triangles':s['triangles_header'],'header_vertices':s['strip_vertices_header']},uv_mask=mask)
    draws=[];decoded_textures=set();decoded_bytes=0
    for c in trace['draws']:
        g=geometries[c['shape']];state=interpret(c['commands'])
        for pno,p in enumerate(g['packets']):
            issues=[];texture=None
            if c['transforms']:issues.append('unresolved source instance transforms')
            if state['unknown']:issues.append('GT3-specific source lighting state retained')
            if state['gt3_lighting_pending']:issues.append('GT3 VU lighting parameters require renderer translation')
            first=p['first_triangle'];triangles=g['triangles'][first:first+p['triangle_count']]
            external=p['texture']==511 or c['texture_table']['kind']=='external'
            requested=bindings.get(str(state['external_texture_index']))if external else None
            binding=requested if requested and packet_has_uvs(g['vertices'],triangles)else None
            if external and not binding:issues.append('runtime external environment texture')
            elif p['texture']:
                ti=binding['texture_set']if binding else c['texture_table']['index']
                if not 0<=ti<len(textures):raise ValueError('GT3 texture table index')
                key=(ti,binding['texture']if binding else p['texture']-1)
                if key not in decoded_textures:
                    if not 0<=key[1]<len(textures[ti].registers):raise ValueError('GT3 texture index')
                    reg=textures[ti].registers[key[1]];decoded_bytes+=reg['width']*reg['height']*4;decoded_textures.add(key)
                    if decoded_bytes>32*1024*1024:raise ValueError('GT3 decoded texture cache budget')
                try:texture=textures[ti].texture(key[1])
                except ValueError as e:
                    if strict_textures:raise
                    issues.append('unsupported source texture: '+str(e))
            if not 0<=p['material']<=len(materials):raise ValueError('GT3 packet material index outside original table')
            material=materials[p['material']-1]if p['material']else None
            draws.append({'source_shape':c['shape'],'packet':pno,'component':component,'command_offset':c['command_offset'],'commands':c['commands'],'transforms':c['transforms'],'texture_binding':{'set':c['texture_table'],'selector':p['texture'],'explicit_external_source':binding,**({'external_image_binding_rejected':'Source packet has no complete finite UVs; retain generated environment/effect semantics.'}if requested and binding is None else{})},'state':state,'vertices':g['vertices'],'triangles':triangles,'texture':texture,'material':material,'gif':p['gif'],'issues':issues})
    return {'draws':draws,'source_sha256':source['sha256'],'source_format':'GT3 ModelSet1','colourway':colour,'report':{'models':m['models'],'selected_model':model_index,'selected_lod':lod,'source_colourways':m['source_colourway_count'],'stored_shapes':len(m['shapes']),'selected_shapes':sorted(selected),'selected_triangles':sum(len(d['triangles'])for d in draws),'unsupported_draws':[{'shape':d['source_shape'],'packet':d['packet'],'issues':d['issues']}for d in draws if d['issues']],'boundary':'Direct GT3 VIF/GS source decoding. GT3 VU lighting, external reflections and callback transforms are not gameplay-qualified.'}}
