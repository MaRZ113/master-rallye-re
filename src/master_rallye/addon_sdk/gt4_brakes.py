"""Source callback qualification and confined native lamp surfaces.

Uses an explicitly selected GT4 callback, actual branch commands/textures and
the user-supplied stock MR glow image. No MatN names or fixed lamp coordinates.
"""
from dataclasses import replace
import hashlib,math,struct,zlib
from .gt4_scene import reconstruct
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.scene_dx_writer import ScenePart
from master_rallye.topology_writer import DrawGeometry


def source_key(d):return d['command_offset'],d['source_shape'],d['packet']


def source_states(data,profile):
    cfg=profile['native_brakes']
    if set(cfg)-{'callback','off_case','on_case','alpha_ref','halo_offset','source_shapes','halo_max_edge'}:raise ValueError('unknown native brake source option')
    cb=str(cfg['callback']);off=cfg['off_case'];on=cfg['on_case']
    if off==on or profile['body_callbacks'].get(cb)!=off:raise ValueError('brake reference is not the selected off state')
    kw={'model_index':profile['selection']['race_model'],'lod':profile['selection'].get('race_lod',0),
        'freeze_morphs':bool(profile.get('freeze_dynamic_morphs',False)),
        'vm_tween_callback_profile':profile.get('vm_tween_callback_profile')}
    a=reconstruct(data,callbacks={**profile['body_callbacks'],cb:off},**kw)
    b=reconstruct(data,callbacks={**profile['body_callbacks'],cb:on},**kw)
    ak={source_key(d) for d in a['draws']};bk={source_key(d) for d in b['draws']}
    removed=[d for d in a['draws'] if source_key(d) not in bk];added=[d for d in b['draws'] if source_key(d) not in ak]
    if 'source_shapes' in cfg:
        selection=cfg['source_shapes']
        if not isinstance(selection,dict) or set(selection)!={'off','on'} or any(not isinstance(selection[k],list) or not selection[k] or any(type(x)is not int or x<0 for x in selection[k]) or len(set(selection[k]))!=len(selection[k]) for k in selection):raise ValueError('invalid explicit brake shape selection')
        for key,draws in [('off',removed),('on',added)]:
            if set(selection[key])-{d['source_shape'] for d in draws}:raise ValueError('brake shape absent from source branch difference')
        removed=[d for d in removed if d['source_shape'] in selection['off']]
        added=[d for d in added if d['source_shape'] in selection['on']]
    if not removed or not added or any(d['issues'] for d in added):raise ValueError('unqualified source brake branch')
    for d in added:
        if not d['texture'] or (d['gif']['blend'] and d['state']['blend'][:4]!=[0,1,0,1]):raise ValueError('unsupported source lit surface')
    return removed,added,{'source_sha256':hashlib.sha256(data).hexdigest(),'callback':int(cb),'off_case':off,'on_case':on,
        'off_commands':[list(source_key(d)) for d in removed],'on_commands':[list(source_key(d)) for d in added],
        'boundary':'source conditional geometry; mapping this callback to MR braking is explicit profile data, not a numeric material-name heuristic'}


def _texture(output,width,height,pixels,prefix):
    name=prefix+hashlib.sha256(struct.pack('<II',width,height)+pixels).hexdigest()[:20]+'-tga'
    data=struct.pack('<5I',0xfeed,1,zlib.crc32(pixels)&0xffffffff,width,height)+pixels
    (output/(name+'.dxt')).write_bytes(data);parse_dxt_bytes(data);return name


def native_surfaces(parts,output,stock_glow,*,alpha_ref=32,offset=.001,halo_max_edge=None):
    if not parts:raise ValueError('expected at least one blended source lens')
    if not 0<=alpha_ref<128 or not math.isfinite(offset) or not 0<offset<=.003:raise ValueError('unqualified lens coverage/offset')
    if halo_max_edge is not None and (type(halo_max_edge) is not int or halo_max_edge<16 or halo_max_edge>1024 or halo_max_edge&(halo_max_edge-1)):raise ValueError('invalid generated halo ceiling')
    ref=parse_dxt_bytes(stock_glow);lit=[];textures=[]
    for p in parts:
        if not p.alpha or p.environment:raise ValueError('expected original source-alpha lens surface')
        t=parse_dxt_bytes((output/(p.textures[0]+'.dxt')).read_bytes());raw=bytearray(t.bgra)
        for i,a in enumerate(raw[3::4]):raw[i*4+3]=255 if a>alpha_ref*255//128 else 0
        name=_texture(output,t.width,t.height,bytes(raw),'gt4-brake-lit-')
        lit.append(replace(p,textures=(name,'Null','Null'),alpha=True,alpha_test=True,diffuse=False));textures.append((t,raw))
    # One packed halo material, with the original source mask intersected with
    # the stock glow falloff. Meshes are lens-conforming, never expanded quads.
    width=1<<math.ceil(math.log2(sum(t.width for t,_ in textures)));height=1<<math.ceil(math.log2(max(t.height for t,_ in textures)))
    pixels=bytearray(width*height*4);vertices=[];triangles=[];xoff=0
    for p,(t,mask) in zip(parts,textures):
        for y in range(t.height):
            for x in range(t.width):
                source=(y*t.width+x)*4;rx=min(ref.width-1,x*ref.width//t.width);ry=min(ref.height-1,y*ref.height//t.height);ri=(ry*ref.width+rx)*4
                dest=(y*width+xoff+x)*4;pixels[dest:dest+3]=ref.bgra[ri:ri+3]
                pixels[dest+3]=(ref.bgra[ri+3]*t.bgra[source+3]//255) if mask[source+3] else 0
        base=len(vertices)
        for v in p.geometry.vertices:
            pos=tuple(v.position[k]+v.normal[k]*offset for k in range(3));u,w=v.uvs[0]
            vertices.append(replace(v,position=pos,color=b'\xff'*4,uvs=(((xoff+u*t.width)/width,w*t.height/height),)))
        triangles.extend(tuple(base+i for i in tri) for tri in p.geometry.triangles);xoff+=t.width
    if halo_max_edge is not None and max(width,height)>halo_max_edge:
        scale=halo_max_edge/max(width,height);nw=max(1,int(width*scale));nh=max(1,int(height*scale))
        # Only the generated MR glow effect is bounded; original lens/core
        # textures and normalized UVs are untouched. Deterministic nearest.
        pixels=bytes(pixels[((y*height//nh)*width+x*width//nw)*4+k] for y in range(nh) for x in range(nw) for k in range(4))
        width,height=nw,nh
    name=_texture(output,width,height,bytes(pixels),'gt4-brake-glow-')
    glow=ScenePart(DrawGeometry(tuple(vertices),tuple(triangles)),(name,'Null','Null'),alpha=True,diffuse=False)
    return lit,[glow],{'lit_draws':len(lit),'glow_draws':1,'lit_triangles':sum(len(p.geometry.triangles) for p in lit),
        'glow_triangles':len(triangles),'halo_offset_m':offset,'generated_halo_dimensions':[width,height],'generated_halo_max_edge':halo_max_edge,'source_lens_geometry_preserved':True,
        'mask':'stock native glow falloff intersected with source lit alpha coverage; no enlarged halo geometry',
        'approximation':'native GREATER128 cutout lens cores; source-alpha edge coverage quantized at explicit profile threshold'}
