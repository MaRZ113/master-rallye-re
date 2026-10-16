"""PS2 content fixes package (CREW-FACE1 + window fixes): opt-in corrections of defects present in original PS2 data.

Default run: verify every pin, build each corrected asset in memory, re-check it with the renderer's PS2MDL02
decode rules and write evidence/<FIX>.json + evidence/package.json. Assets are written only with `--write`,
always under NEW filenames next to the originals, which are never opened for writing. `--write` skips
CANDIDATE fixes unless `--include-candidates` is also given.

Fix kinds (no vertex, normal, colour, UV or texture byte ever changes; header counts never change):
- rebind:  move a contiguous triangle range from one mesh to the end of another (index reorder + row ranges).
- retire_overlay: turn every triangle of an unconditional cracked-glass overlay mesh into a zero-area triangle
  (same index count, same referenced vertex set, mesh row untouched), so only the coincident intact glass draws.
"""
from pathlib import Path
import collections, hashlib, json, math, struct, sys
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]; VEH=PORT/'.assets/vehicles'
NONE=0xffffffff
digest=lambda b:hashlib.sha256(b).hexdigest()

FIXES=[
 dict(id='NAVARA-CREWFACE1',status='USER_REPORTED',kind='rebind',role='race',family='Navara',registry='renderer/race_fleet_registry.hpp:677',
      source='NAVARA-CAR-FLEET.ps2model',sha='336318a5cc30f0cd7bf3c6f9addcf7e10848a1d762f5e7e88abee7f2f8caee0e',size=372926,
      output='NAVARA-CAR-FLEET-CREWFACE1.ps2model',
      dst=0,dst_row=(217868,1,0,NONE,NONE,0,1767),src=15,src_row=(221636,3,18,19,NONE,5673,93),tris=27,vertices=(3482,3519),
      driver_face=list(range(519,552))+[568,569],
      references=[('NEWRAV','root.0'),('KIASPORTAGE','root.17'),('LANDCRUISER','root.0'),('FRONTERA','root.0'),('CHEVYBLAZER','root.0'),
                  ('KAMAZ','root.0'),('KANGOO','root.14'),('JUMP','root.0'),('BRUNO','root.0'),('ASTERO','root.0')]),
 dict(id='TATA-WINDOW1',status='USER_REPORTED',kind='retire_overlay',role='race',family='Tata',registry='renderer/race_fleet_registry.hpp:684',
      source='TATA-CAR-FLEET.ps2model',sha='20262ea17be8ef15e0faea7b70dc1ae2cff47df9aec2410fe3538587a5d18660',size=420088,
      output='TATA-CAR-FLEET-WINDOW1.ps2model',overlay='root.22',intact='root.21',intact_tris=[0,1,2,3],
      ps2_source='TATA-CAR-SOURCE.ps2vehicle'),
 dict(id='KAMAZ-COMPLETE-WINDOW1',status='USER_REPORTED',kind='retire_overlay',role='frontend',family='Kamaz',registry='renderer/frontend_fleet_registry.hpp:689',
      source='KAMAZ-COMPLETE-FLEET.ps2model',sha='df3d58336f6596cc4915b055820c5d0008b116b33091cca6915abdf971d3826c',size=827015,
      output='KAMAZ-COMPLETE-FLEET-WINDOW1.ps2model',overlay='root.20',intact='root.19',intact_tris=[0,1,2,3],mirror_tris=[4,5,6,7],
      ps2_source=None),
 dict(id='KAMAZ-CAR-WINDOW1',status='CANDIDATE_NOT_USER_OBSERVED',kind='retire_overlay',role='race',family='Kamaz',registry='renderer/race_fleet_registry.hpp:671',
      source='KAMAZ-CAR-FLEET.ps2model',sha='1807d3e68bf080ad6c793ee548cad86d0846706bac8418b38495705196d401fa',size=463264,
      output='KAMAZ-CAR-FLEET-WINDOW1.ps2model',overlay='root.18',intact='root.17',intact_tris=[0,1,2,3],
      ps2_source='KAMAZ-CAR-SOURCE.ps2vehicle'),
]

def parse(blob):
    magic,version,meta,meshes,nv,ni,nt,src=struct.unpack_from('<8s6I32s',blob); assert magic==b'PS2MDL02' and version==2
    raw=blob[64:64+meta]; metadata=json.loads(raw); at=64+meta
    assert json.dumps(metadata,sort_keys=True,separators=(',',':')).encode()==raw, 'metadata serialization differs; refusing to rewrite'
    rows=[struct.unpack_from('<7I',blob,at+i*28) for i in range(meshes)]; at+=meshes*28
    vat=at; at+=nv*36; idx=list(struct.unpack_from('<%dI'%ni,blob,at)); at+=ni*4; tex_at=at; tex=[]
    for _ in range(nt):
        w,h,n=struct.unpack_from('<3I',blob,at); tex.append((w,h,blob[at+12:at+12+n])); at+=12+n
    assert at==len(blob)
    vertex=lambda i:struct.unpack_from('<3f3fI2f',blob,vat+i*36)
    return dict(header=(meta,meshes,nv,ni,nt,src),meta=metadata,rows=rows,vat=vat,idx=idx,tex=tex,tex_at=tex_at,vertex=vertex)

def mesh_index(a,path): return [k for k,me in enumerate(a['meta']['meshes']) if me['path']==path][0]
def slots(me): return me.get('source_texture_slots') or me.get('textures')
def texname(a,k): return slots(a['meta']['meshes'][k])[0]['name']
def triangles(a,row): return [tuple(a['idx'][row[5]+k:row[5]+k+3]) for k in range(0,row[6],3)]
def uvkey(a,t): return tuple(sorted((round(a['vertex'](i)[7],3),round(a['vertex'](i)[8],3)) for i in t))
def corners(a,t): return sorted(tuple(a['vertex'](i)[:3]) for i in t)

def footprint(a,tri,texture):
    """Texels covered by the triangle under the runtime orientation v' = 1 - v (metadata primary_orientation), clamp addressing."""
    w,h,px=a['tex'][texture]; uv=[(a['vertex'](i)[7]*w,(1-a['vertex'](i)[8])*h) for i in tri]; hit=collections.Counter()
    for sy in range(h*4):
        for sx in range(w*4):
            p=((sx+.5)/4,(sy+.5)/4); e=[(q[0]-o[0])*(p[1]-o[1])-(q[1]-o[1])*(p[0]-o[0]) for o,q in zip(uv,uv[1:]+uv[:1])]
            if (all(x>=0 for x in e) or all(x<=0 for x in e)) and any(e): hit[(min(w-1,int(p[0])),min(h-1,int(p[1])))]+=1
    return hit

def texel_stats(a,tris,texture):
    w,h,px=a['tex'][texture]; hit=collections.Counter()
    for t in tris: hit.update(footprint(a,t,texture))
    n=sum(hit.values()); acc=[0,0,0,0]
    for (x,y),c in hit.items():
        for j in range(4): acc[j]+=px[(y*w+x)*4+j]*c
    xs=[x for x,_ in hit]; ys=[y for _,y in hit]
    # Stored bytes are D3DFMT_A8R8G8B8 little-endian (B,G,R,A); reported as RGBA.
    b,g,r,al=(round(v/n,1) for v in acc)
    return {'texel_bbox_xy':[min(xs),min(ys),max(xs),max(ys)],'texture_size':[w,h],'mean_rgba':[r,g,b,al],
            'min_alpha':min(px[(y*w+x)*4+3] for x,y in hit),'samples':n}

def decode_like_renderer(blob,meshes,nv,ni,nt):
    """Python port of decode_frontend_asset() structural checks in renderer/frontend_model.cpp (profile path)."""
    _,version,meta,m,v,i,t,_=struct.unpack_from('<8s6I32s',blob); assert blob[:8]==b'PS2MDL02' and version==2 and (m,v,i,t)==(meshes,nv,ni,nt)
    at=64+meta; rows=[struct.unpack_from('<7I',blob,at+k*28) for k in range(m)]; at+=m*28
    for node,mode,t0,t1,t2,first,count in rows:
        assert all(x==NONE or x<t for x in (t0,t1,t2)) and t0!=NONE and first<=i and count<=i-first and count%3==0 and count and mode in (0,1,2,3,5,20,21)
    at+=v*36; assert all(x<v for x in struct.unpack_from('<%dI'%i,blob,at)); at+=i*4
    for _ in range(t):
        w,h,n=struct.unpack_from('<3I',blob,at); assert w and h and w<=1024 and h<=1024 and w*h*4==n; at+=12+n
    assert at==len(blob); return rows

def assemble(a,blob,metadata,rows,idx):
    meta,meshes,nv,ni,nt,src=a['header']; mj=json.dumps(metadata,sort_keys=True,separators=(',',':')).encode()
    out=struct.pack('<8s6I32s',b'PS2MDL02',2,len(mj),meshes,nv,ni,nt,src)+mj+b''.join(struct.pack('<7I',*r) for r in rows)
    return out+blob[a['vat']:a['vat']+nv*36]+struct.pack('<%dI'%ni,*idx)+blob[a['tex_at']:]

def common_after(fix,a,b,out):
    decode_like_renderer(out,*a['header'][1:5])
    assert all(b['vertex'](i)==a['vertex'](i) for i in range(a['header'][2])) and b['tex']==a['tex'] and b['header'][1:]==a['header'][1:]
    assert collections.Counter(b['idx'])==collections.Counter(a['idx']) or fix['kind']=='retire_overlay'
    assert set(b['idx'])==set(a['idx']), 'referenced vertex set changed'
    return {'file':fix['output'],'sha256':digest(out),'size':len(out),'header_counts':dict(zip(['meshes','vertices','indices','textures'],a['header'][1:5])),
            'renderer_decode_checks':'PASS (python port of decode_frontend_asset structural rules)','written':False}

# ---------------------------------------------------------------- rebind (Navara co-driver face)
def fix_rebind(fix,blob,a):
    rows=a['rows']; idx=a['idx']; d,s=fix['dst'],fix['src']; n=fix['tris']*3; verts=set(range(*fix['vertices']))
    assert rows[d]==fix['dst_row'] and rows[s]==fix['src_row'], 'mesh rows changed; refusing'
    assert d==0 and s>d, 'index layout assumption'
    s0=rows[s][5]; face=idx[s0:s0+n]; assert set(face)==verts, 'face vertex set changed'
    assert all(s0<=k<s0+n for k,x in enumerate(idx) if x in verts), 'face vertices shared outside the moved range'
    end0=rows[d][5]+rows[d][6]
    new_idx=idx[:end0]+face+idx[end0:s0]+idx[s0+n:]
    new_rows=[]
    for k,r in enumerate(rows):
        r=list(r)
        if k==d: r[6]+=n
        elif d<k<s: r[5]+=n
        elif k==s: r[5]+=n; r[6]-=n
        new_rows.append(tuple(r))
    m=json.loads(json.dumps(a['meta']))
    for k,me in enumerate(m['meshes']):
        assert (me['first_index'],me['index_count'])==rows[k][5:7]
        me['first_index'],me['index_count']=new_rows[k][5:7]; me['faces']=new_rows[k][6]//3
    m['deliberate_deviations']=[{'id':'CREW-FACE1','scope':'NAVARA co-driver face only',
        'change':'27 triangles (37 vertices %d..%d) moved from root.15 [mlamp32+glass, carshiny mode 3] to the end of root.0 [underdash2, carflat mode 1]'%(fix['vertices'][0],fix['vertices'][1]-1),
        'unchanged':'all vertex bytes (xyz, normals, colour, UV), all textures, all other triangles and their order within each mesh, header counts',
        'reason':'source binds the co-driver face to the lamp material; UVs address the second face in underdash2-tga exactly as in 10 other PS2 families; original PS2 shows the same white face',
        'source_asset_sha256':fix['sha'],'source_root15_index_range':[s0,s0+n]}]
    out=assemble(a,blob,m,new_rows,new_idx); b=parse(out)
    face_t=triangles(a,rows[s])[:fix['tris']]; lamps=triangles(a,rows[s])[fix['tris']:]
    assert triangles(b,new_rows[d])[rows[d][6]//3:]==face_t and triangles(b,new_rows[s])==lamps
    assert all(triangles(b,new_rows[k])==triangles(a,rows[k]) for k in range(1,len(rows)) if k!=s)
    output=common_after(fix,a,b,out)
    names=[t['path'].split('\\')[-1] for t in a['meta']['texture_upload']]
    drv=[triangles(a,rows[d])[k] for k in fix['driver_face']]
    cod_sig=collections.Counter(uvkey(a,t) for t in face_t); drv_sig=collections.Counter(uvkey(a,t) for t in drv)
    refs=[]
    for fam,path in fix['references']:
        p=VEH/(fam+'-CAR-FLEET.ps2model')
        if not p.exists(): refs.append({'family':fam,'present':False}); continue
        r=parse(p.read_bytes()); k=mesh_index(r,path); c=collections.Counter(uvkey(r,t) for t in triangles(r,r['rows'][k]))
        refs.append({'family':fam,'mesh':path,'texture':texname(r,k),'mode':r['rows'][k][1],
                     'codriver_face_uv_triangles_matched':sum((c&cod_sig).values()),'driver_face_uv_triangles_matched':sum((c&drv_sig).values()),
                     'texture_argb_sha256':r['meta']['texture_upload'][r['rows'][k][2]]['argb_sha256']})
    assert all(r.get('codriver_face_uv_triangles_matched')==27 for r in refs if r.get('present',True))
    vs=sorted(verts)
    evidence={
     'diagnosis':'WRONG_MATERIAL_SLOT_NOT_UV: co-driver face UVs already address the second face of underdash2-tga; the triangles sit in root.15 whose primary texture is mlamp32-tga',
     'mhelmet32':{'mesh':'root.18','texture_index':23,'size':list(a['tex'][23][:2]),'argb_sha256':a['meta']['texture_upload'][23]['argb_sha256'],
       'contains_face':False,'note':'helmet shell only; visor triangles 140-143 (driver) and 144-147 (co-driver) have identical UVs; the 16 per-seat UV-asymmetric side triangles are identical in NEWRAV root.3, so root.18 is not the cause',
       'visor_driver_texels':texel_stats(a,[triangles(a,rows[18])[k] for k in range(140,144)],23),'visor_codriver_texels':texel_stats(a,[triangles(a,rows[18])[k] for k in range(144,148)],23)},
     'codriver_face':{'mesh':'root.15','local_triangles':[0,fix['tris']-1],'global_index_range':[s0,s0+n],'vertices':[vs[0],vs[-1]],'triangles':[list(t) for t in face_t],
       'bbox_xyz':[[round(min(a['vertex'](i)[j] for i in vs),3) for j in range(3)],[round(max(a['vertex'](i)[j] for i in vs),3) for j in range(3)]],
       'as_drawn_now':dict(texture=names[rows[s][2]],mode=rows[s][1],secondary='mixed reflection capture (root.15 mixed=true)',**texel_stats(a,face_t,rows[s][2])),
       'after_fix':dict(texture=names[rows[d][2]],mode=rows[d][1],secondary=None,**texel_stats(a,face_t,rows[d][2]))},
     'driver_face':{'mesh':'root.0','local_triangles':fix['driver_face'],'texture':names[rows[d][2]],'mode':rows[d][1],**texel_stats(a,drv,rows[d][2])},
     'lamps_remaining_in_root15':{'local_triangles_before':[fix['tris'],fix['tris']+len(lamps)-1],'triangles':[list(t) for t in lamps]},
     'reference_families':refs,
     'mesh_rows':{'before':{'root.0':list(rows[d]),'root.15':list(rows[s])},'after':{'root.0':list(new_rows[d]),'root.15':list(new_rows[s])},
       'shifted_first_index':'root.1..root.14 first_index +%d; root.16..root.20 unchanged'%n}}
    return out,evidence,output

# ---------------------------------------------------------------- retire_overlay (cracked right side window)
def source_switches(name):
    """Named screen* switches of the original PS2 CAR.PSM (from the private PS2VEH01 source extract) and their child meshes."""
    blob=(VEH/name).read_bytes(); n=struct.unpack_from('<I',blob,12)[0]; m=json.loads(blob[56:56+n])
    paths=[me['path'] for me in m['meshes']]; out={}
    for e in m['extra_nodes']:
        if e.get('name','').startswith('screen'):
            kids=[c for c in m['extra_nodes'] if c['path'].rsplit('.',1)[0]==e['path'] and 'selector' in c]
            out[e['name']]={'path':e['path'],'children':{('selector_%d'%c['selector']):[{'path':p,'texture':slots(me)[0]['name']} for me in m['meshes'] for p in [me['path']] if p.startswith(c['path']+'.')] for c in kids}}
    return {'file':name,'sha256':digest(blob),'source_resource':m.get('source_resource'),'screen_switches':out,'unconditional_mesh_paths':[p for p in paths if p.count('.')==1]}

def fix_retire_overlay(fix,blob,a):
    rows=a['rows']; idx=a['idx']; ko=mesh_index(a,fix['overlay']); ki=mesh_index(a,fix['intact'])
    assert texname(a,ko).lower().endswith('windscreenc32-tga') and texname(a,ki).lower().endswith('windscreen32-tga'), 'overlay/intact textures changed'
    assert rows[ko][1]==20 and rows[ki][1]==20, 'expected carglass mode 20 on both meshes'
    over=triangles(a,rows[ko]); intact=triangles(a,rows[ki]); pairs=[]
    for k,t in enumerate(over):
        best=min(((max(min(math.dist(p,q) for q in corners(a,u)) for p in corners(a,t)),j) for j,u in enumerate(intact)))
        pairs.append({'overlay_triangle':k,'intact_triangle':best[1],'max_corner_distance':round(best[0],5)})
    assert [p['intact_triangle'] for p in pairs]==fix['intact_tris'] and all(p['max_corner_distance']<0.02 for p in pairs), 'overlay is not coincident with the intact right window'
    uniq=list(dict.fromkeys(i for t in over for i in t)); ntri=len(over)
    assert len(uniq)<=2*ntri and all(rows[ko][5]<=k<rows[ko][5]+rows[ko][6] for k,x in enumerate(idx) if x in set(uniq)), 'overlay vertices shared outside the overlay mesh'
    # Zero-area triangles (u,u,v) that keep every overlay vertex referenced (damage contracts count referenced vertices).
    degenerate=[(uniq[(2*k)%len(uniq)],uniq[(2*k)%len(uniq)],uniq[(2*k+1)%len(uniq)]) for k in range(ntri)]
    assert set(i for t in degenerate for i in t)==set(uniq)
    new_idx=list(idx); new_idx[rows[ko][5]:rows[ko][5]+rows[ko][6]]=[i for t in degenerate for i in t]
    m=json.loads(json.dumps(a['meta']))
    m['deliberate_deviations']=[{'id':fix['id'],'scope':'%s %s right side window (model -x) only'%(fix['family'].upper(),fix['role']),
        'change':'%s [%s] %d triangles replaced by zero-area triangles over the same %d vertices; the coincident intact glass %s triangles %s is unchanged'%(fix['overlay'],texname(a,ko),ntri,len(uniq),fix['intact'],fix['intact_tris']),
        'unchanged':'all vertex bytes, all textures, every mesh row (mode, textures, first, count), index count, all other triangles',
        'reason':'original PS2 draws the cracked windscreenc32 overlay unconditionally on top of the intact right window, so it is broken from the start; the left window and windscreen switch between intact and cracked',
        'source_asset_sha256':fix['sha']}]
    out=assemble(a,blob,m,rows,new_idx); b=parse(out)
    assert b['rows']==rows and all(triangles(b,rows[k])==triangles(a,rows[k]) for k in range(len(rows)) if k!=ko)
    for t in triangles(b,rows[ko]):
        p=[b['vertex'](i)[:3] for i in t]; u=[p[1][j]-p[0][j] for j in range(3)]; v=[p[2][j]-p[0][j] for j in range(3)]
        assert all(abs(u[(j+1)%3]*v[(j+2)%3]-u[(j+2)%3]*v[(j+1)%3])==0 for j in range(3)), 'triangle not zero-area'
    output=common_after(fix,a,b,out)
    names=[t['path'].split('\\')[-1] for t in a['meta']['texture_upload']]
    evidence={
     'diagnosis':'UNCONDITIONAL_CRACKED_OVERLAY: %s (%s) duplicates the intact right side window of %s and is drawn every frame on top of it'%(fix['overlay'],names[rows[ko][2]],fix['intact']),
     'side_convention':'model -x = vehicle right (driver sits at +x in these left-hand-drive models; see NAVARA-CREWFACE1 driver x=+0.31)',
     'overlay':{'mesh':fix['overlay'],'row':list(rows[ko]),'texture':names[rows[ko][2]],'texture_argb_sha256':a['meta']['texture_upload'][rows[ko][2]]['argb_sha256'],
                'triangles':[list(t) for t in over],'vertices':uniq,'x_range':[round(min(a['vertex'](i)[0] for i in uniq),3),round(max(a['vertex'](i)[0] for i in uniq),3)],
                'texels':texel_stats(a,over,rows[ko][2])},
     'intact':{'mesh':fix['intact'],'row':list(rows[ki]),'texture':names[rows[ki][2]],'texture_argb_sha256':a['meta']['texture_upload'][rows[ki][2]]['argb_sha256'],
               'right_window_triangles':fix['intact_tris'],'texels':texel_stats(a,[intact[k] for k in fix['intact_tris']],rows[ki][2])},
     'coincidence':pairs,
     'after_fix':{'overlay_triangles':[list(t) for t in degenerate],'note':'zero-area: rasterize no pixels; mesh row, mode and textures unchanged'}}
    if fix.get('mirror_tris'):
        evidence['left_window_mirror']={'mesh':fix['intact'],'triangles':fix['mirror_tris'],
            'x_range':[round(min(a['vertex'](i)[0] for k in fix['mirror_tris'] for i in intact[k]),3),round(max(a['vertex'](i)[0] for k in fix['mirror_tris'] for i in intact[k]),3)],
            'cracked_overlay_present':False}
    if fix.get('ps2_source'):
        src=source_switches(fix['ps2_source']); evidence['ps2_source']=src
        sw=src['screen_switches']
        assert all(not v for v in sw['screenright']['children'].values()), 'screenright switch is not empty in source'
        assert fix['overlay'] in src['unconditional_mesh_paths'] and fix['intact'] in src['unconditional_mesh_paths']
        evidence['ps2_source_reading']=('screenright switch has no child meshes; screenleft/screenfront switch between windscreen32 and windscreenc32; '
            'the right window pair (%s intact, %s cracked) is authored as unconditional root children instead'%(fix['intact'],fix['overlay']))
        evidence['asset_excluded_conditional_paths']=a['meta'].get('excluded_source_conditional_paths')
    else:
        evidence['ps2_source']={'note':'COMPLETE (frontend) model: metadata source has %d extra_nodes, i.e. no window switches; every mesh is unconditional'%len(a['meta'].get('source',{}).get('extra_nodes',[]))}
    return out,evidence,output

def run(write,include_candidates):
    (HERE/'evidence').mkdir(exist_ok=True); package=[]
    for fix in FIXES:
        blob=(VEH/fix['source']).read_bytes(); assert len(blob)==fix['size'] and digest(blob)==fix['sha'], '%s: source pin mismatch'%fix['id']
        a=parse(blob)
        out,evidence,output=(fix_rebind if fix['kind']=='rebind' else fix_retire_overlay)(fix,blob,a)
        if write and (fix['status']=='USER_REPORTED' or include_candidates):
            target=VEH/fix['output']; assert target.resolve()!=(VEH/fix['source']).resolve()
            if target.exists() and target.read_bytes()!=out: sys.exit('refusing to overwrite a different %s'%fix['output'])
            target.write_bytes(out); output['written']=True
        evidence=dict(id=fix['id'],status=fix['status'],kind=fix['kind'],role=fix['role'],family=fix['family'],
                      source={'file':fix['source'],'sha256':fix['sha'],'size':fix['size']},output=output,**evidence)
        (HERE/'evidence'/(fix['id']+'.json')).write_text(json.dumps(evidence,indent=1,sort_keys=True)+'\n')
        package.append({'id':fix['id'],'status':fix['status'],'role':fix['role'],'family':fix['family'],'registry_line':fix['registry'],
                        'original':{'file':fix['source'],'sha256':fix['sha'],'size':fix['size']},
                        'fixed':{'file':fix['output'],'sha256':output['sha256'],'size':output['size']},
                        'unchanged_counts':output['header_counts'],'written':output['written']})
        print('%-24s %-22s %s %s %s'%(fix['id'],fix['status'],output['file'],output['sha256'],output['size']),'written' if output['written'] else '')
    (HERE/'evidence'/'package.json').write_text(json.dumps({'ini_key':'PS2ContentFixes','default':0,'fixes':package},indent=1,sort_keys=True)+'\n')

if __name__=='__main__': run('--write' in sys.argv[1:],'--include-candidates' in sys.argv[1:])
