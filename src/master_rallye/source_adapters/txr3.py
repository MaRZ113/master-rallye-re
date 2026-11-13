"""Tokyo Xtreme Racer 3 / Shutokou Battle 01 (PS2, SLPM-65308) car -> Universal Vehicle Scene v1.

Format research: branch research/source-formats, source-formats/txr3/README.md.
The car container is an unpacked BUILD.DAT entry (genki_unpack). TXR3 cars carry no
wheels in the body container, so the four wheel nodes are an explicit MR authoring
choice: the clean retail donor wheel.dx geometry/textures, recorded as such.
"""
from __future__ import annotations
import hashlib,math,struct
from pathlib import Path
from .. import universal_vehicle_scene as uvs
from . import txr3_formats as fmt
from .tim2 import read as read_tim2

VERSION='txr3-ps2-source/1'
# Source frame: +X front, +Y up, +Z vehicle left, metres, mirrored (badge text proves it).
# MR = (z, y, x); normalized (+X right, +Y up, -Z front) = (-z, y, -x). det -1 = the source mirror.
NORMALIZATION=[0.,0.,-1.,0., 0.,1.,0.,0., -1.,0.,0.,0., 0.,0.,0.,1.]
VEHICLES={
    'VEHICROSS':{'entry':355,'table_record':53,'body_code':'UGS250',
        'excluded_textures':{5,8,16,20,35,49,55},'excluded_materials':{70},
        'arches':{'front':[1.135,0.259],'rear':[-1.192,0.259],'radius':0.401}},
}
TEXTURED=0x20


def digest(b):return hashlib.sha256(b).hexdigest()


def material_records(s):
    out=[]
    for rec,tex in fmt.materials(s):
        flags=s[rec];blend=s[rec+1]&1
        out.append({'offset':rec,'textured':bool(flags&TEXTURED),'texture':tex,'flags':s[rec:rec+16].hex(),
                    'blend':bool(blend),'ambient':list(struct.unpack_from('<4f',s,rec+16)),'diffuse':list(struct.unpack_from('<4f',s,rec+32))})
    return out


def _solid(rgba):
    return bytes(rgba)*4


def create_scene(container,output,vehicle='VEHICROSS',*,donor_wheel=None,donor_textures=None,scale=1.0):
    """container: unpacked BUILD.DAT entry; donor_wheel: retail wheel.dx path (MR authoring)."""
    from ..dx import parse_dx_bytes
    from ..topology_writer import source_geometry
    from ..dxt import parse_dxt_bytes,decode_rgba_pixels,PNG_ROWS_PRESERVE_STORED
    spec=VEHICLES[vehicle];container=Path(container).absolute();uvs.unlinked(container)
    output=Path(output).absolute();protected=[container.parent]
    uvs.output_directory(output,protected)
    if output.exists():raise ValueError('Fresh source output required')
    raw=container.read_bytes();n=struct.unpack_from('<I',raw)[0]
    if n!=3:raise ValueError('TXR3 car container must have three sections')
    offs=list(struct.unpack_from('<3I',raw,4))+[len(raw)]
    s=raw[offs[0]:offs[1]]
    if s[:8]!=b'0IVX00.1':raise ValueError('TXR3 model section expected')
    tims=read_tim2(raw[offs[1]:offs[2]])
    mats=material_records(s);starts=[m['offset']for m in mats]
    import bisect
    batches=fmt.batches(s)
    assets={'original/'+container.name:raw};textures=[];materials=[];meshes=[];nodes=[]
    member={'member':container.name,'snapshot_path':'original/'+container.name,'bytes':len(raw),'sha256':digest(raw)}
    tex_ids={}
    def texture_for(key,rgba,w,h,channels,bound=True):
        if key in tex_ids:return tex_ids[key]
        path='textures/'+key+'.rgba';assets[path]=rgba
        row={'id':key,'width':w,'height':h,'rgba_path':path,'rgba_sha256':digest(rgba),'source_channels':channels}
        if bound:row['source']={'member':member['member'],'snapshot_path':member['snapshot_path'],'bytes':member['bytes'],'sha256':member['sha256']}
        textures.append(row)
        tex_ids[key]=key;return key
    groups={}
    for b in batches:
        k=bisect.bisect_left(starts,b['off'])-1
        if k<0:continue
        m=mats[k]
        if k in spec['excluded_materials'] or (m['textured'] and m['texture']in spec['excluded_textures']):continue
        groups.setdefault(k,[]).append(b)
    body_mesh_ids=[]
    for k,bs in sorted(groups.items()):
        m=mats[k];key='mat-%02d'%k
        if m['textured']:
            im=tims[m['texture']].convert('RGBA')
            tid=texture_for('tim-%03d'%m['texture'],im.tobytes(),im.size[0],im.size[1],
                {'mode':'TIM2 CLUT (CSM1 unswizzled), PS2 alpha 0x80 = opaque scaled to 255','tim_index':m['texture'],
                 'alpha':'source TIM alpha; runtime blend state from the material header'})
        else:
            c=[max(0,min(255,round(v*255)))for v in m['diffuse'][:3]]+[max(0,min(255,round(m['diffuse'][3]*255)))]
            tid=texture_for('solid-%02d'%k,_solid(c),2,2,{'mode':'derived 2x2 solid colour from the untextured material diffuse vec4',
                                                          'diffuse':m['diffuse'],'alpha':'material diffuse alpha'})
        P=[];N=[];U=[];T=[]
        for b in bs:
            base=len(P)
            for i,p in enumerate(b['pos']):
                P.append([float(v)for v in p])
                nr=b['nrm'][i] if b['nrm'] and i<len(b['nrm']) else (0,32767,0,32767)
                l=math.sqrt(nr[0]**2+nr[1]**2+nr[2]**2) or 1.
                N.append([nr[0]/l,nr[1]/l,nr[2]/l])
                U.append([float(v)for v in(b['uv'][i] if b['uv'] and i<len(b['uv']) else (0.,0.))])
            T.extend([list(t)for t in fmt.triangles(b,base)])
        if not T:continue
        materials.append({'id':key,'diffuse_texture_id':tid,
            'raw_fields':[{'material_offset':m['offset'],'header':m['flags'],'ambient':m['ambient'],'diffuse':m['diffuse'],'textured':m['textured'],'blend':m['blend']}],
            'unsupported':['GS blend/alpha-test/lighting registers','specular/emissive vec4 roles'],
            'flags':{'transparent_raw':'1'if m['blend']else'0','evidence':'TXR3 material header byte1 bit0 with alpha word 0x80 (observed on glass/translucent records).'},
            'preview':{'opacity':1.,'policy':'diffuse texture or material colour'}})
        meshes.append({'id':key,'material_id':key,'positions':P,'normals':N,'uvs':U,'triangles':T,
            'source':{'member':member['member'],'member_sha256':member['sha256'],'material_offset':m['offset'],
                      'batches':[b['off']for b in bs],'strip_policy':'one VIF batch = one triangle strip; normal w != 0x7FFF = restart'}})
        body_mesh_ids.append(key)
    nodes.append({'id':'body','name':'BODY','parent_id':None,'mesh_ids':body_mesh_ids,'visible':True,'source_visible':True,'role':'body',
        'local_transform':uvs.IDENTITY[:],'source_local_transform':uvs.IDENTITY[:],
        'transform_evidence':'TXR3 car model is authored in one frame; no hierarchy in the body container.'})
    wheel_report=None
    if donor_wheel is not None:
        wraw=Path(donor_wheel).read_bytes();wm=parse_dx_bytes(wraw);geo=source_geometry(wm)
        assets['donor/wheel.dx']=wraw
        wmeshes=[]
        for draw in wm.physical_draws:
            g=geo[draw.draw_index];name=draw.texture_tuple[0]
            dxt_path=Path(donor_textures)/(name+'.dxt')
            t=parse_dxt_bytes(dxt_path.read_bytes());rgba=decode_rgba_pixels(t,PNG_ROWS_PRESERVE_STORED)
            tid=texture_for('donor-'+name,rgba,t.width,t.height,{'mode':'MR retail DXT (BGRA) decoded, stored rows','donor_texture':name,
                                                               'alpha':'retail alpha'},bound=False)
            wmeshes.append((draw.draw_index,g,tid,name))
        # MR wheel.dx = right wheel (outward MR -X). Source frame s = (MRz, MRy, MRx); body scale is applied by the
        # authoring transform, so donor geometry is pre-divided to keep the retail size.
        for slot,side,(ax) in (('FL_WHEEL','left','front'),('FR_WHEEL','right','front'),('BL_WHEEL','left','rear'),('BR_WHEEL','right','rear')):
            ids=[]
            for di,g,tid,name in wmeshes:
                key='%s-d%02d'%(slot.lower(),di);ids.append(key)
                mirror=side=='left'
                P=[];N=[];U=[];T=[]
                for v in g.vertices:
                    x,y,z=v.position;nx,ny,nz=v.normal
                    if mirror:x,nx=-x,-nx
                    P.append([z/scale,y/scale,x/scale]);N.append([nz,ny,nx]);U.append(list(v.uvs[0]))
                for a,b_,c in g.triangles:
                    # source->MR has det -1 (compile reverses winding); a left mirror reverses once more.
                    T.append([a,b_,c]if mirror else[a,c,b_])
                materials.append({'id':key,'diffuse_texture_id':tid,'raw_fields':[{'donor_draw':di,'donor_texture':name}],
                    'unsupported':['donor native state words are re-authored by the MR role'],
                    'flags':{'transparent_raw':'0','evidence':'retail donor wheel draw'},'preview':{'opacity':1.,'policy':'donor texture'}})
                meshes.append({'id':key,'material_id':key,'positions':P,'normals':N,'uvs':U,'triangles':T,
                    'source':{'mr_authoring':'retail donor wheel.dx draw %d (%s), %s side'%(di,name,side)}})
            hx,hy=spec['arches'][ax]
            nodes.append({'id':slot.lower(),'name':slot,'parent_id':None,'mesh_ids':ids,'visible':True,'source_visible':False,'role':'wheel',
                'local_transform':[1.,0.,0.,hx, 0.,1.,0.,hy, 0.,0.,1.,0., 0.,0.,0.,1.],
                'source_local_transform':None,'transform_evidence':'MR authoring: hub at the fitted TXR3 arch centre; lateral position set by hub_overrides in the MR profile.'})
        wheel_report={'donor_wheel_sha256':digest(wraw),'draws':[(di,name)for di,_,_,name in wmeshes]}
    scene={'schema':uvs.SCHEMA,'metadata':{'adapter':VERSION,'display_name':'TXR3 '+vehicle,
            'qualification':'L1 structural recovery from BUILD.DAT entry; wheels are MR donor authoring, not source data',
            'neutral_preview':{'cull':'none','evidence':'strip winding alternates; MR pilot orients by normals'},
            'implementation_sha256':{Path(p).name:digest(Path(p).read_bytes())for p in(__file__,Path(__file__).with_name('txr3_formats.py'),Path(__file__).with_name('tim2.py'))}},
        'source':{'game':'Shutokou Battle 01 / Tokyo Xtreme Racer 3 (2003)','platform':'PS2','root':str(container.parent),'protected_roots':list(map(str,protected)),
                  'resources':[member],'catalog':'BUILD.DAT entry %d'%spec['entry'],'table_record':spec['table_record'],'body_code':spec['body_code'],
                  'donor_wheel':wheel_report},
        'coordinate_system':{'source_to_normalized':NORMALIZATION[:],'source':{'right_axis':[0,0,-1],'up_axis':[0,1,0],'forward_axis':[1,0,0],'units':'metres'},
            'normalized':{'right_axis':[1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,-1],'units':'metres'},
            'interpretation_status':'front from overhangs (rear spare wheel) and lamp textures; mirror from badge text; metres from the 2.33 m wheelbase',
            'evidence':['arch circle fit: wheelbase 2.327 m (VehiCROSS 2330 mm)','ISUZU badge reads correctly only after one axis flip']},
        'meshes':meshes,'materials':materials,'textures':textures,'nodes':nodes,
        'selection':{'member':container.name,'pose':'static','visibility':'flare sprites and the drop-shadow material excluded'},
        'unknown_semantics':[{'id':'renderer','status':'NOT TESTED','meaning':'GS blend/alpha/lighting registers not reproduced'},
                             {'id':'wheels','status':'MR AUTHORING','meaning':'source wheels live in a separate TXR3 library not decoded yet; retail donor wheels used'}]}
    result=uvs.save_scene(scene,output,assets,protected_roots=protected)
    return {**result,'vehicle':vehicle,'materials':len(materials)}
