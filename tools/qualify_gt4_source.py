"""Read-only GT4 qualification, packet-local intermediate and MR DX probes.

No CarID, physics tuning, wheel placement, source patch or runtime packaging.
"""
import argparse,json,re,sys,struct,zlib,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.gt4_source import modelset,shape_geometry,translate_pass
from master_rallye.addon_sdk.gt4_commands import command_graph,binding_trace,translate_invocation
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import CompiledVertex,DrawGeometry,rebuild_topology,source_geometry
from master_rallye.r4e_writer import patch_dx_attributes
from master_rallye.texture_authoring import decode_rgba_png
import vmesh_raster as raster
from generate_vehicle_ui_previews import frame_camera

def snapshots(path):
    out={};current=None;model=None
    for line in path.read_text().splitlines():
        group=re.match(r'^      (model[^:]+):',line)
        if group:model=group[1]
        m=re.match(r'^          (shape\d+[^:]*):',line)
        if m:current=m[1];out[current]={'commands':[],'shadow':False,'external':False,'model':model}
        elif current and line.startswith('            - '):out[current]['commands'].append(line.strip()[2:])
        elif current and 'UseUnknownShadowFlag: true' in line:out[current]['shadow']=True
        elif current and 'UseExternalTexture: true' in line:out[current]['external']=True
        elif line.strip() and len(line)-len(line.lstrip())<=10:current=None
    return out

def run(source,dump,out,donor,active_model='model0',command_profile=None):
    if out.exists():raise ValueError('output exists')
    out.mkdir(parents=True);data=source.read_bytes();sha=hashlib.sha256(data).hexdigest();m=modelset(data);states=snapshots(dump/'model_set.yaml');items=[];report=[];ir=[];probes=0
    for shape in m['shapes']:
        names=[n for n in states if re.match(r'shape(\d+)',n)[1]==str(shape['index'])]
        state=states[names[0]] if len(names)==1 else None
        try:g=shape_geometry(shape)
        except ValueError as e:report.append({'shape':shape['index'],'status':'UNSUPPORTED_GEOMETRY','error':str(e)});ir.append({'shape':shape,'error':str(e)});continue
        ext=any(p['texture']==511 for p in g['packets'])
        translation=translate_pass(state['commands'],shadow=state['shadow'],external_texture=ext or state['external']) if state else {'route':'unresolved_invocation'}
        ir.append({'shape_index':shape['index'],'names':names,'flags':shape['flags'],'geometry':g,'translation':translation})
        report.append({'shape':shape['index'],'names':names,'triangles':len(g['triangles']),'vertices':len(g['vertices']),'route':translation['route'],'source_normals':sum(v['normal'] is not None for v in g['vertices']),'source_uvs':sum(v['uv'] is not None for v in g['vertices'])})
        if translation['route'] not in ('alpha_test','source_alpha'):continue
        if state['model']!=active_model:continue
        for packet_no,p in enumerate(g['packets']):
            texture_id=p['texture'];texture=None
            if texture_id not in (0,511):
                texpath=dump/'Textures'/f'0.{texture_id-1}.png'
                if not texpath.exists():raise ValueError('texture mapping unavailable')
                texture=decode_rgba_png(texpath.read_bytes())
            triangles=g['triangles'][p['first_triangle']:p['first_triangle']+p['triangle_count']];vs=g['vertices'];drawtris=[]
            for ids in triangles:
                uv=[vs[k]['uv'] for k in ids]
                if texture and any(v is None for v in uv):continue
                positions=[(vs[k]['position'][0],vs[k]['position'][1],-vs[k]['position'][2]) for k in ids]
                drawtris.append((*positions,*(tuple((v[0],1-v[1])) if v else (.5,.5) for v in uv),(255,255,255),(255,255,255),(255,255,255)))
            # Presentation uses source RGBA; special passes are not folded into
            # RGB. Exact GS reference/mask semantics remain in the IR.
            reg=m['texture_sets'][0][texture_id-1] if texture_id not in (0,511) else None
            if reg and (3 in (reg['wrap_s'],reg['wrap_t']) or reg['min_u'] or reg['min_v']):
                report[-1].setdefault('unsupported_sampler_packets',[]).append(packet_no);continue
            modes=(reg['wrap_s'],reg['wrap_t']) if reg else (0,0)
            if reg and reg['tfx']!=0:
                report[-1].setdefault('unsupported_texture_function_packets',[]).append(packet_no);continue
            if reg and reg['tcc']==0 and texture:
                w,h,rgba=texture;rgba=bytearray(rgba);rgba[3::4]=bytes([255])*(w*h);texture=(w,h,bytes(rgba))
            state=translation['state'];test=state['alpha_test'];ref=round(state['alpha_ref']*255/128)
            items.append(raster.DrawItem(f'shape{shape["index"]}/packet{packet_no}',drawtris,texture,not test,test,modes,ref))
            if donor and texture and probes<3 and all(vs[k]['normal'] is not None and vs[k]['uv'] is not None for t in triangles for k in t):
                make_probe(donor,out/f'probe-{probes}',g,triangles,texture);probes+=1
    graphs=[]
    for index,model in enumerate(m['models']):
        start=model['commands_offset'];end=m['models'][index+1]['commands_offset'] if index+1<len(m['models']) else min(s['offset'] for s in m['shapes'] if s['offset']>start)
        try:
            graph=command_graph(data,start,end)
            trace=binding_trace(graph,lod=0,callbacks=command_profile)
            invocations=[]
            for draw in trace['draws']:
                if not 0<=draw['shape']<len(m['shapes']):raise ValueError('shape invocation out of range')
                s=m['shapes'][draw['shape']]
                invocations.append({'draw':draw,'translation':translate_invocation(draw,shadow=bool(s['flags'][0]&16),packet_external=any(p['texture']==511 for p in s['packets']))})
            graphs.append({'model_index':index,'graph':graph,'trace':trace,'invocations':invocations})
        except ValueError as exc:graphs.append({'model_index':index,'unsupported':str(exc)})
    (out/'source-commands.json').write_text(json.dumps({'source_sha256':sha,'callback_diagnostic_choices':command_profile,'models':graphs,'policy':'original byte control-flow/texture/state trace; unknown VM or callback transforms remain unsupported; not native PS2 rendering'},indent=2))
    (out/'source-intermediate.json').write_text(json.dumps({'source_sha256':sha,'modelset_base':m['base'],'source_model_records':m['models'],'source_materials':m['materials'],'texture_registers':m['texture_sets'],'shapes':ir,'anchors':None,'anchor_policy':'UNRESOLVED; model origins are retained, never treated as car wheel-instance transforms'},indent=2))
    result={'status':'OFFLINE_PARTIAL_SOURCE_CANDIDATE_NOT_RUNTIME','source_sha256':sha,'source_unchanged':source.read_bytes()==data,'active_preview_model':active_model,'shapes':report,'dx_packet_probes':probes,'unresolved':['CAR4 wheel-instance transforms','external texture-table bindings','GT4 destination-alpha/colour-mask effects','packed normal semantics retained without an invented scale'],'source_snapshot_policy':'PDTools exported command snapshots; not a complete original command interpreter'}
    result['source_command_graphs']=[{'model_index':g['model_index'],'nodes':len(g.get('graph',{}).get('nodes',[])),'unsupported':g.get('unsupported'),'source_trace_draws':len(g.get('invocations',[])),'trace_blocked':g.get('trace',{}).get('blocked_at') is not None} for g in graphs]
    result['diagnostic_preview_routes']='Legacy exported YAML snapshots; direct byte traces are retained separately and are more conservative about unresolved state'
    (out/'qualification.json').write_text(json.dumps(result,indent=2))
    if items and any(i.tris for i in items):
        points=[p for i in items for t in i.tris for p in t[:3]];centre=tuple((min(p[k] for p in points)+max(p[k] for p in points))/2 for k in range(3))
        for name,az,el in [('front',180,5),('rear',0,5),('side',-90,0),('three-quarter',138,10)]:
            cam=raster.Camera(az,el,1,centre,7 if name=='three-quarter' else None);frame_camera(points,cam,640,400,20);(out/(name+'.png')).write_bytes(raster.png_rgb(640,400,raster.render(items,cam,640,400)))
    print(json.dumps({'source':str(source),'shapes':len(report),'decoded_shapes':sum('error' not in r for r in report),'dx_probes':probes},indent=2));return result

def make_probe(donor,out,g,triangles,texture):
    out.mkdir();template=donor.read_bytes();model=parse_dx_bytes(template);used=sorted({k for t in triangles for k in t});lookup={k:i for i,k in enumerate(used)};verts=[]
    for k in used:
        v=g['vertices'][k];x,y,z=v['position'];nx,ny,nz=v['normal'];u,w=v['uv'];verts.append(CompiledVertex((x,y,-z),(nx,ny,-nz),bytes((255,255,255,255)),((u,1-w),)))
    geom=DrawGeometry(tuple(verts),tuple(tuple(lookup[k] for k in t[::-1]) for t in triangles));fill=DrawGeometry(tuple(CompiledVertex(p,(0,1,0),bytes((255,255,255,255)),((.5,.5),)) for p in ((0,0,0),(.001,0,0),(0,0,.001))),((0,1,2),))
    edits={d.draw_index:geom if d.draw_index==3 else fill for d in model.physical_draws};rebuilt=rebuild_topology(template,edits,bounds_mode='recompute')
    patched=patch_dx_attributes(rebuilt.data,material_env={3:False},material_alpha={3:True},material_alpha_test={3:True}).data
    (out/'component.dx').write_bytes(patched);w,h,rgba=texture;pixels=bytearray()
    for y in range(h-1,-1,-1):
        for x in range(w):r,g,b,a=rgba[4*(y*w+x):4*(y*w+x)+4];pixels.extend((b,g,r,a))
    (out/'colour-tga.dxt').write_bytes(struct.pack('<5I',0xfeed,1,zlib.crc32(pixels)&0xffffffff,w,h)+pixels)
    after=source_geometry(parse_dx_bytes(patched))[3]
    if after.vertices!=source_geometry(parse_dx_bytes(rebuilt.data))[3].vertices:raise ValueError('attribute translation regression')
    (out/'NOTE.txt').write_text('Packet-local DX/DXT probe only. Other native draws are fillers; stock collision retained for file validity. Not a complete vehicle. Source UV/normals preserved with explicit Z/V convention change. MR alpha-test threshold is not asserted equal to GT4 GS threshold.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--dump',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--donor',type=Path);p.add_argument('--active-model',default='model0');p.add_argument('--command-profile',type=Path);a=p.parse_args();run(a.source,a.dump,a.output,a.donor,a.active_model,json.loads(a.command_profile.read_text()) if a.command_profile else None)
