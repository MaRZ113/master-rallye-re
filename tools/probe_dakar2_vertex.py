"""Bounded original Xbox vertex/linker proof and private material diagnostics.

No native fixtures, game/GPU emulation or automatic material approval. Original
program payloads stay in memory. Reports/diagnostics require a fresh private root.
"""
from pathlib import Path
import argparse
import struct
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_adapters import dakar2_vertex as v
from master_rallye.source_adapters.nv2a_vertex import decode_program,describe,evaluate_outputs
from master_rallye.source_adapters.dakar2_materials import native_evidence,qualify_closure,evaluate_pixel_definition,decode_pixel_definition
from master_rallye.source_adapters.dakar2_coverage import scene_coverage
from master_rallye.source_adapters.dakar2_formats import packed_normal

IDENTITY=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]


def transpose(matrix):return [matrix[c*4+r]for r in range(4)for c in range(4)]


def vertex_evidence(data):
    # Deliberately asymmetric, exactly representable fixtures distinguish W/V/P.
    world=IDENTITY[:];world[12:15]=[2,3,4]
    view=[0,1,0,0,-1,0,0,0,0,0,1,0,5,6,7,1]
    projection=[2,0,0,0,0,3,0,0,0,0,4,0,0,0,0,1]
    matrices=v.replay_constants(data,world=world,view=view,projection=projection)
    expected={0:view[12:16],6:transpose(world),10:projection,
              66:transpose(u.multiply(world,view)),14:transpose(u.multiply(u.multiply(world,view),projection))}
    if matrices['initial_constant65']['values']!=[0,.5,1,2]or {r['constant_index']:r['values']for r in matrices['matrix_uploads']}!=expected:
        raise ValueError('Original CPU/Python matrix ownership mismatch')
    contexts={
        'unlit':{'lighting':False,'lights':[None]*8,'fog':False,'texture_transforms':[False]*4},
        'directional0':{'lighting':True,'lights':[0]+[None]*7,'fog':False,'texture_transforms':[False]*4},
        'point0':{'lighting':True,'lights':[1]+[None]*7,'fog':False,'texture_transforms':[False]*4},
        'fog-and-texture-transforms':{'lighting':False,'lights':[None]*8,'fog':True,'texture_transforms':[True]*4}}
    programs={};private={}
    for address in v.BASE_PROGRAMS:
        for name,context in contexts.items():
            linked=v.compose_original(data,address,context);key=hex(address)+'/'+name
            private[key]=linked['program'];programs[key]={k:x for k,x in linked.items()if k!='program'}
            programs[key]['listing']=describe(decode_program(linked['program']))
    consumers={}
    for name,address,size in [('matrix-upload',0x8cda0,0x160),('base-init',0x86ba0,0x31),
                              ('c65-upload',0x86f3a,0x26),('fragment-select',0x8d800,0x129),
                              ('light-select',0x8cd40,0x60),('fragment-link',0xf85bb,0x180)]:
        consumers[name]={'va':address,'bytes':size,'sha256':u.sha(v.original(data,address,size))}
    return {'schema':'dakar2-vertex-evidence/1','xbe_sha256':u.sha(data),'native_linkers_match':True,
            'matrix_uploads_verified':True,'matrix_probe':matrices,'programs':programs,'consumers':consumers,
            'runtime_state':'NOT CAPTURED; all composition/matrix contexts explicit',
            'initial_r11':'Not established for lit program: CPU diagnostics require explicit accumulator',
            'static_bake_allowed':False,'native_fixture_allowed':False},private


def source_worlds(scene):
    nodes={n['id']:n for n in scene['nodes']};world={};active=set()
    def get(key):
        if key in world:return world[key]
        if key in active or len(active)>256:raise ValueError('Source transform cycle/budget')
        active.add(key);node=nodes[key];parent=node['parent_id']
        result=node['source_local_transform']if parent is None else u.multiply(get(parent),node['source_local_transform'])
        active.remove(key);world[key]=result;return result
    for key in nodes:get(key)
    return world


def material_diagnostics(scene,path,report,evidence,programs,folder):
    """Nearest-wrap point witnesses, not a rasterized source renderer."""
    from PIL import Image,ImageDraw
    textures={};nodes={mid:n for n in scene['nodes']for mid in n['mesh_ids']};worlds=source_worlds(scene)
    for texture in scene['textures']:
        raw=u.read_bounded(path.parent/u.relative_name(texture['rgba_path']),u.MAX_TEXTURE_BYTES)
        if u.sha(raw)!=texture['rgba_sha256']:raise ValueError('Diagnostic texture provenance mismatch')
        textures[texture['id']]=(texture['width'],texture['height'],raw)
    def sample(binding,uv):
        width,height,raw=textures[binding];x=int((uv[0]/uv[3]%1)*width);y=int((uv[1]/uv[3]%1)*height)
        return [x/255 for x in raw[(y*width+x)*4:(y*width+x)*4+4]]
    rows=[];sheet=Image.new('RGB',(1200,55+len(report['draws'])*28),(30,30,30));draw=ImageDraw.Draw(sheet)
    draw.text((8,8),'CONTROLLED CPU POINT SAMPLES - no filtering/raster/GPU parity; unlit explicit state',fill='white')
    draw.text((440,30),'T0*V0          T1.a           T2 contribution       sum             shifted-world sum',fill='white')
    for ordinal,(mesh,row)in enumerate(zip(scene['meshes'],report['draws'])):
        streams={}
        for key,record in mesh['source']['streams'].items():
            raw=u.read_bounded(path.parent/u.relative_name(record['path']),u.MAX_OUTPUT_BYTES)
            if u.sha(raw)!=record['sha256']:raise ValueError('Diagnostic vertex provenance mismatch')
            streams[key]=raw
        address=row['vertex_program_va'];decoded=decode_program(programs[hex(address)+'/unlit']);multi=address==0x192850
        definition=decode_pixel_definition(evidence['declarations'][str(row['declaration'])]['pixel_definition_words'])
        material_samples=[];node=nodes[mesh['id']];world=worlds[node['id']]
        for index in sorted({0,len(mesh['positions'])//2,len(mesh['positions'])-1}):
            position=list(struct.unpack_from('<3f',streams['0'],index*12))+[1]
            normal=packed_normal(struct.unpack_from('<I',streams['2'],index*4)[0])+[0]
            bgra=streams['3'][index*4:index*4+4];color=[bgra[2]/255,bgra[1]/255,bgra[0]/255,bgra[3]/255]
            inputs={0:position,2:normal,3:color,9:list(struct.unpack_from('<2f',streams['9'],index*8))+[0,1]}
            if multi:inputs[10]=list(struct.unpack_from('<2f',streams['10'],index*8))+[0,1]
            contexts=[]
            for shifted in(False,True):
                matrix=world[:]
                if shifted:matrix[3]+=1
                constants={65:[0,.5,1,2],-38:[1]*4,-37:[0]*4}
                for start in(6,14):
                    for i in range(4):constants[start+i]=matrix[i*4:i*4+4]
                outputs=evaluate_outputs(decoded,inputs,constants,outputs=('V0','T0','T1','T2')if multi else('V0','T0'))
                samples={'t'+str(stage['stage']):sample(stage['texture_id'],outputs['T'+str(stage['stage'])])for stage in row['texture_stages']if stage['mode']!='NONE'}
                rgba=evaluate_pixel_definition(definition,samples,[max(0,min(1,x))for x in outputs['V0']],runtime_constants={0:[0,0,0,89/255]})
                contexts.append({'shifted_world_x':shifted,'vertex_outputs':outputs,'texture_samples':samples,'result_rgba':rgba})
            material_samples.append({'vertex_index':index,'contexts':contexts})
        rows.append({'mesh_id':row['mesh_id'],'source_node':row['source_node'],'samples':material_samples})
        first=material_samples[0]['contexts'][0];samples=first['texture_samples']
        colors=[[samples['t0'][i]*first['vertex_outputs']['V0'][i]for i in range(3)],
                [samples.get('t1',[0,0,0,0])[3]]*3,
                [samples.get('t1',[0,0,0,0])[3]*samples.get('t2',[0]*4)[i]*89/255 for i in range(3)],
                first['result_rgba'][:3],material_samples[0]['contexts'][1]['result_rgba'][:3]]
        y=55+ordinal*28;draw.text((8,y+4),row['source_node']+' / '+row['mesh_id'],fill='white')
        for column,color_ in enumerate(colors):draw.rectangle((440+column*145,y,570+column*145,y+22),fill=tuple(round(255*max(0,min(1,x)))for x in color_))
    diagnostic={'scope':'Original source streams, source-rest node hierarchy, explicit unlit program, initialized c65, supplied world translation0/+1, supplied C0alpha89/255, nearest-wrap point samples; NOT effective original runtime or MR-native preview',
                'sampling_padding':'Explicit diagnostic FLOAT2 z=0/w=1; not an independent original vertex-fetch precision proof',
                'rows':rows,'native_fixture_allowed':False,'L2':'WARN'}
    sheet.save(folder/'controlled-stage-points.png');(folder/'controlled-stage-points.json').write_bytes(u.canonical(diagnostic))


def run(image,scenes,output,viewer=None):
    image=Path(image).absolute();paths=[Path(p).absolute()for p in scenes];loaded=[u.load_scene(p)for p in paths]
    if not 1<=len(paths)<=3:raise ValueError('Bounded selected three-vehicle corpus required')
    protected=[image.parent,*[p.parent for p in paths]]
    for scene in loaded:protected.extend(map(Path,scene['source'].get('protected_roots',[])))
    output=u.output_directory(Path(output).absolute(),protected)
    if output.exists():raise ValueError('Fresh vertex evidence output required')
    data=v.read_executable(image);vertex,programs=vertex_evidence(data);evidence=native_evidence(image)
    output.mkdir(parents=True);(output/'vertex-evidence.json').write_bytes(u.canonical(vertex));summaries=[]
    for path,scene in zip(paths,loaded):
        coverage=scene_coverage(scene,path.parent,incoming_enabled=False,effective_reference=100)
        report=qualify_closure(scene,evidence,coverage,vertex);folder=output/scene['source']['catalog'];folder.mkdir()
        blob=u.canonical(report)
        if blob!=u.canonical(qualify_closure(scene,evidence,coverage,vertex)):raise ValueError('Nondeterministic closure report')
        report_sha=u.sha(blob);(folder/'per-draw-qualification.json').write_bytes(blob)
        (folder/'controlled-coverage.json').write_bytes(u.canonical(coverage))
        material_diagnostics(scene,path,report,evidence,programs,folder)
        if viewer is not None:
            from master_rallye.source_scene_preview import stage_source_scene,capture_views
            preview=folder/'source-preview.mrpv';stage_source_scene(scene,preview,scene_root=path.parent,material_mode='original')
            capture_views(Path(viewer),preview,folder/'source-d3d9',cull='source',provenance='L2 WARN: unchanged single-stage neutral preview; multi-stage proof is separate CPU diagnostic')
        summaries.append({'source_catalog':scene['source']['catalog'],'source_scene_sha256':u.sha(path.read_bytes()),
                          'draws':len(report['draws']),'triangles':report['triangles'],'qualification_sha256':report_sha,
                          'simple_draws':sum(r['vertex_program_va']==0x192588 for r in report['draws']),
                          'L0':'PASS','L1':'PASS','L2':'WARN','L3':'BLOCKED','L4':'NOT TESTED'})
    summary={'schema':'dakar2-material-closure-corpus/1','vehicles':summaries,'vertex_evidence_sha256':u.sha(u.canonical(vertex)),
             'native_fixtures':0,'source_mutated':False,'runtime':'MISSING INPUT: original Xbox state/graphics trace'}
    (output/'summary.json').write_bytes(u.canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--xbox',type=Path,required=True)
    parser.add_argument('--scene',type=Path,action='append',required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--viewer',type=Path);args=parser.parse_args()
    print(run(args.xbox,args.scene,args.output,args.viewer))
