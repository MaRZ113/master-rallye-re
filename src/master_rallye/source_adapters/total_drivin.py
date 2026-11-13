"""Total Drivin' (PS1, SLES-00307) car -> Universal Vehicle Scene v1.

Format research: branch research/source-formats, source-formats/total-drivin/README.md.
Inputs are two decompressed LEVELS.DAT chunks of one level: the object chunk (car nodes)
and the VRAM upload chunk (textures/CLUTs). Total Drivin' wheels are parameter records,
not meshes, so the four wheel nodes are an explicit MR authoring choice: retail donor wheel.dx.
"""
from __future__ import annotations
import hashlib,math,struct
from pathlib import Path
from .. import universal_vehicle_scene as uvs
from . import td_model,td_texture

VERSION='total-drivin-ps1-source/1'
# Source frame: +X vehicle left (FL wheel at +x), +Y up, +Z front; units = packed vertex x2.
# Normalized (+X right, +Y up, -Z front) = (-x, y, -z).
NORMALIZATION=[-1.,0.,0.,0., 0.,1.,0.,0., 0.,0.,-1.,0., 0.,0.,0.,1.]
UNIT=0.01  # source units -> scene units (the MR pilot rescales to the donor wheelbase)
VEHICLES={
    # Owner 2026-11-13: the Citroen ZX Rallye Raid is DAKAR1 or DAKAR2 (same body, different livery).
    'ZX_DAKAR1':{'car':'DAKAR1','level':10,'level_name':'ISLAND3'},
    'ZX_DAKAR2':{'car':'DAKAR2','level':10,'level_name':'ISLAND3'},
}
# Flat (untextured) material colours. Type 1 = body colour from the car header RGB; type 2 = dark trim;
# type 0x0a = glasshouse (sky reflection page in game).
FLAT_TYPES={1:'body',2:'trim',10:'glass'}
# 8 = textured 4-bit; 0x10 = textured with two buffer states (brake lamp off/on: first copy = off).
TEXTURED=(8,16)


def digest(b):return hashlib.sha256(b).hexdigest()


def _faces(d,car):
    a=d.find(car.encode()+b'\x00');j=d.find(b'BODY\x00',a)
    m=td_model.parse_mesh(d,j);p=j+0x20+49;nv=struct.unpack_from('<HHhHH',d,p)[3];f=p+10+4*nv+20
    recs=[struct.unpack_from('<4hHHII',d,f+20*k)for k in range(len(m['polys']))]
    header_rgb=list(d[a+0x24:a+0x27])
    wheels={}
    for nm in('FLWHEEL','FRWHEEL','BLWHEEL','BRWHEEL'):
        k=d.find(nm.encode()+b'\x00',a)
        h=k+0x20;wheels[nm]={'kind':d[h],'position':list(struct.unpack_from('<3i',d,h+1)),'radius':struct.unpack_from('<h',d,h+49)[0]}
    return m,recs,header_rgb,wheels


def _outward(pts,c):
    a,b,cc=pts[0],pts[1],pts[2]
    n=None
    for k in range(1,len(pts)-1):
        u=[pts[k][i]-a[i]for i in range(3)];v=[pts[k+1][i]-a[i]for i in range(3)]
        x=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        n=x if n is None else[n[i]+x[i]for i in range(3)]
    l=math.sqrt(sum(t*t for t in n))
    if l<1e-9:return None
    n=[t/l for t in n];m=[sum(p[i]for p in pts)/len(pts)-c[i]for i in range(3)]
    # fan (0,k,k+1) is counter-clockwise around n; flip the corner order when n points inward
    if sum(n[i]*m[i]for i in range(3))<0:return [-t for t in n],True
    return n,False


def create_scene(obj_chunk,vram_chunk,output,vehicle='ZX_DAKAR1',*,donor_wheel=None,donor_textures=None,scale=1.0):
    from ..dx import parse_dx_bytes
    from ..topology_writer import source_geometry
    from ..dxt import parse_dxt_bytes,decode_rgba_pixels,PNG_ROWS_PRESERVE_STORED
    spec=VEHICLES[vehicle];car=spec['car']
    obj_chunk=Path(obj_chunk).absolute();vram_chunk=Path(vram_chunk).absolute()
    for p in(obj_chunk,vram_chunk):uvs.unlinked(p)
    output=Path(output).absolute();protected=sorted({obj_chunk.parent,vram_chunk.parent})
    uvs.output_directory(output,protected)
    if output.exists():raise ValueError('Fresh source output required')
    d=obj_chunk.read_bytes();vbuf=vram_chunk.read_bytes();V=td_texture.vram(vbuf)
    mats=td_texture.materials(d,car);mesh,recs,header_rgb,src_wheels=_faces(d,car)
    assets={'original/'+obj_chunk.name:d,'original/'+vram_chunk.name:vbuf}
    members=[{'member':p.name,'snapshot_path':'original/'+p.name,'bytes':len(b),'sha256':digest(b)}for p,b in((obj_chunk,d),(vram_chunk,vbuf))]
    textures=[];materials=[];meshes=[];nodes=[];tex_ids={};boxes={}
    def texture_for(key,rgba,w,h,channels,source=None):
        if key in tex_ids:return key
        path='textures/'+key+'.rgba';assets[path]=rgba
        row={'id':key,'width':w,'height':h,'rgba_path':path,'rgba_sha256':digest(rgba),'source_channels':channels}
        if source:row['source']={k:source[k]for k in('member','snapshot_path','bytes','sha256')}
        textures.append(row);tex_ids[key]=key;return key
    groups={}
    for poly,r in zip(mesh['polys'],recs):groups.setdefault(r[6],[]).append((poly,r))
    body_ids=[]
    vs=mesh['V'];centre=[(min(v[k]for v in vs)+max(v[k]for v in vs))/2 for k in range(3)]
    for e,polys in sorted(groups.items()):
        m=mats[e];key='mat-%02d'%e
        if m['type']in TEXTURED:
            im,box=td_texture.texture(V,m);boxes[e]=box
            tid=texture_for('page%02d-clut%04x-w%06x'%(m['page_code']>>3,m['clut'],m['window']&0xffffff),im.tobytes(),im.size[0],im.size[1],
                {'mode':'4-bit VRAM page (page_code >> 3 on the y=256 row) through the material CLUT; E2 window crop','page_code':m['page_code'],
                 'clut':m['clut'],'window':m['window'],'alpha':'PS1 colour 0x0000 = transparent'},members[1])
        else:
            kind=FLAT_TYPES.get(m['type'],'trim')
            rgb=header_rgb if kind=='body'else([40,40,44]if kind=='trim'else[30,38,46])
            tid=texture_for('flat-%s'%kind,bytes(rgb+[255])*4,2,2,{'mode':'derived 2x2 flat colour','material_type':m['type'],
                'evidence':'type 1 = car header RGB %s; trim/glass colours are MR authoring (PS1 lighting table not reproduced)'%header_rgb})
        P=[];N=[];U=[];T=[]
        for (idx,uv,shade,_),r in polys:
            pts=[mesh['V'][i]for i in idx];n=_outward(pts,centre)
            if n is None:continue
            if n[1]:idx,uv=idx[::-1],uv[::-1]
            n=n[0];base=len(P)
            for vi,(u,v) in zip(idx,uv):
                P.append([c*UNIT for c in mesh['V'][vi]]);N.append(n)
                if e in boxes:
                    u0,v0,w,h=boxes[e];U.append([(u-u0+.5)/w,(v-v0+.5)/h])
                else:U.append([.5,.5])
            for k in range(1,len(idx)-1):T.append([base,base+k,base+k+1])
        materials.append({'id':key,'diffuse_texture_id':tid,
            'raw_fields':[{'entry':e,'type':m['type'],'page_code':m['page_code'],'clut':m['clut'],'window':m['window'],
                           'face_flags':sorted({hex(r[4])for _,r in polys})}],
            'unsupported':['PS1 per-corner lighting table','semi-transparency (abr) bits'],
            'flags':{'transparent_raw':'1'if m['type']==10 else'0','evidence':'material type byte (0x0a = glasshouse)'},
            'preview':{'opacity':1.,'policy':'VRAM texture or flat colour'}})
        meshes.append({'id':key,'material_id':key,'positions':P,'normals':N,'uvs':U,'triangles':T,
            'source':{'member':members[0]['member'],'member_sha256':members[0]['sha256'],'car':car,'material_entry':e,
                      'polygon_policy':'fan per face record; geometric face normal oriented away from the body bbox centre (record normals are not consistently outward)'}})
        body_ids.append(key)
    nodes.append({'id':'body','name':'BODY','parent_id':None,'mesh_ids':body_ids,'visible':True,'source_visible':True,'role':'body',
        'local_transform':uvs.IDENTITY[:],'source_local_transform':uvs.IDENTITY[:],'transform_evidence':'BODY node of the car; wheels are parameter records.'})
    wheel_report=None
    if donor_wheel is not None:
        wraw=Path(donor_wheel).read_bytes();wm=parse_dx_bytes(wraw);geo=source_geometry(wm)
        assets['donor/wheel.dx']=wraw;wmeshes=[]
        for draw in wm.physical_draws:
            g=geo[draw.draw_index];name=draw.texture_tuple[0]
            t=parse_dxt_bytes((Path(donor_textures)/(name+'.dxt')).read_bytes());rgba=decode_rgba_pixels(t,PNG_ROWS_PRESERVE_STORED)
            tid=texture_for('donor-'+name,rgba,t.width,t.height,{'mode':'MR retail DXT decoded, stored rows','donor_texture':name,'alpha':'retail alpha'})
            wmeshes.append((draw.draw_index,g,tid,name))
        # Source frame == MR frame here; MR wheel.dx = right wheel (outward -X). Body scale is applied by the
        # authoring transform, so donor geometry is pre-divided to keep the retail size.
        for slot,side,src in(('FL_WHEEL','left','FLWHEEL'),('FR_WHEEL','right','FRWHEEL'),('BL_WHEEL','left','BLWHEEL'),('BR_WHEEL','right','BRWHEEL')):
            ids=[];mirror=side=='left'
            for di,g,tid,name in wmeshes:
                key='%s-d%02d'%(slot.lower(),di);ids.append(key)
                P=[];N=[];U=[];T=[]
                for v in g.vertices:
                    x,y,z=v.position;nx,ny,nz=v.normal
                    if mirror:x,nx=-x,-nx
                    P.append([x/scale,y/scale,z/scale]);N.append([nx,ny,nz]);U.append(list(v.uvs[0]))
                for a,b_,c in g.triangles:T.append([a,c,b_]if mirror else[a,b_,c])
                materials.append({'id':key,'diffuse_texture_id':tid,'raw_fields':[{'donor_draw':di,'donor_texture':name}],
                    'unsupported':['donor native state words are re-authored by the MR role'],
                    'flags':{'transparent_raw':'0','evidence':'retail donor wheel draw'},'preview':{'opacity':1.,'policy':'donor texture'}})
                meshes.append({'id':key,'material_id':key,'positions':P,'normals':N,'uvs':U,'triangles':T,
                    'source':{'mr_authoring':'retail donor wheel.dx draw %d (%s), %s side'%(di,name,side)}})
            x,y,z=[c*UNIT for c in src_wheels[src]['position']]
            nodes.append({'id':slot.lower(),'name':slot,'parent_id':None,'mesh_ids':ids,'visible':True,'source_visible':False,'role':'wheel',
                'local_transform':[1.,0.,0.,x, 0.,1.,0.,y, 0.,0.,1.,z, 0.,0.,0.,1.],'source_local_transform':None,
                'transform_evidence':'MR authoring: hub at the Total Drivin wheel record position (%s).'%src})
        wheel_report={'donor_wheel_sha256':digest(wraw),'draws':[(di,name)for di,_,_,name in wmeshes],'source_wheel_records':src_wheels}
    scene={'schema':uvs.SCHEMA,'metadata':{'adapter':VERSION,'display_name':"Total Drivin' "+car,
            'qualification':'L1 structural recovery from LEVELS.DAT level %d (%s); wheels are MR donor authoring'%(spec['level'],spec['level_name']),
            'neutral_preview':{'cull':'none','evidence':'face winding not established; MR pilot orients by normals'},
            'implementation_sha256':{Path(p).name:digest(Path(p).read_bytes())for p in(__file__,Path(__file__).with_name('td_model.py'),Path(__file__).with_name('td_texture.py'))}},
        'source':{'game':"Total Drivin' / Grand Tour Racing '98 (Eutechnyx 1997)",'platform':'PS1','root':str(obj_chunk.parent),'protected_roots':list(map(str,protected)),
                  'resources':members,'catalog':'LEVELS.DAT level %d %s, node %s'%(spec['level'],spec['level_name'],car),'donor_wheel':wheel_report},
        'coordinate_system':{'source_to_normalized':NORMALIZATION[:],'source':{'right_axis':[-1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,1],'units':'packed units x2 / 100'},
            'normalized':{'right_axis':[1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,-1],'units':'source units / 100'},
            'interpretation_status':'front/left from the FLWHEEL record (+x, +z); scale set later from the donor wheelbase',
            'evidence':['FLWHEEL (117,-38,214), BRWHEEL (-138,-38,-213)']},
        'meshes':meshes,'materials':materials,'textures':textures,'nodes':nodes,
        'selection':{'member':car,'pose':'static','visibility':'LOD0 body only (A/B LODs ignored)'},
        'unknown_semantics':[{'id':'lighting','status':'NOT REPRODUCED','meaning':'corner byte 1 indexes a per-frame lighting/colour table'},
                             {'id':'wheels','status':'MR AUTHORING','meaning':'wheel records carry radius/size, not meshes; retail donor wheels used'}]}
    result=uvs.save_scene(scene,output,assets,protected_roots=protected)
    return {**result,'vehicle':vehicle,'materials':len(materials)}
