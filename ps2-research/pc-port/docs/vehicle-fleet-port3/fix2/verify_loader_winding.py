"""Verify the retail loader winding rule against every non-private fleet-damage dump."""
import importlib.util,struct,json,glob,collections,sys
from pathlib import Path
PORT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('a',PORT/'docs/full-coverage/vehicles/audit.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
cache={};stats=collections.Counter();fams=collections.Counter()
LOGS=sys.argv[1] if len(sys.argv)>1 else 'D:/Game/Master Rallye Pristine/MRRRenderer/logs'
files=[];import hashlib
for fn in sorted(glob.glob(LOGS+'/fleet-damage-*.bin')):
    b=open(fn,'rb').read()
    if b[:8]!=b'FDCAR001':continue
    ml,rl=struct.unpack_from('<II',b,8);meta=json.loads(b[16:16+ml]);raw=b[16+ml:];fam=meta['family'];files.append({'file':Path(fn).name,'sha256':hashlib.sha256(b).hexdigest(),'family':fam,'proxy_sha256':meta.get('proxy_sha256'),'private_tree':meta.get('private_tree')})
    if meta.get('private_tree'):stats['skipped_private_tree_dump']+=1;continue
    if fam not in cache:
        p=a.PC/fam/'car.dx'
        if not p.exists():stats['no_dx_'+fam]+=1;cache[fam]=None;continue
        pc=a.parse_dx(p);cache[fam]=pc
    pc=cache[fam]
    if pc is None:continue
    uv=pc.uv_sets[0].values;pos=pc.vertices.positions
    at=0
    for rec in meta['records']:
        vb=raw[at:at+rec['vertex_bytes']];at+=rec['vertex_bytes'];ib=raw[at:at+rec['index_bytes']];at+=rec['index_bytes']
        st=rec['stride'];n=rec['vertices'];t=rec['triangles'];w=2 if rec['index_format']==101 else 4
        rt=[struct.unpack_from('<3f',vb,i*st) for i in range(n)]
        ridx=[x-rec['min'] for x in struct.unpack(f"<{t*3}{'H' if w==2 else 'I'}",ib)]
        d=pc.physical_draws[rec['node']] if rec['node']<len(pc.physical_draws) else None
        if d is None:stats['no_node']+=1;continue
        ids=pc.draw_global_indices(d);first=min(ids)
        if max(ids)-first+1!=n or len(ids)!=t*3:stats['shape_mismatch']+=1;continue
        if rt!=[tuple(pos[first+i]) for i in range(n)]:stats['vertex_order_differs_or_deformed']+=1;continue
        didx=[i-first for i in ids];flipped=[]
        for k in range(0,len(didx),3):x,y,z=didx[k:k+3];flipped+=[y,x,z]
        key='flip_rule_holds' if ridx==flipped else ('dx_order_holds' if ridx==didx else 'other_order')
        stats[key]+=1;fams[(fam,rec['fvf'],key)]+=1
out={'schema':1,'rule':'retail loader submits car.dx triangle (a,b,c) as (b,a,c); vertex order unchanged','records':dict(stats),'by_family_fvf':[{'family':f,'fvf':v,'result':k,'records':c} for (f,v,k),c in sorted(fams.items())],'dumps':files}
(Path(__file__).parent/'flip_rule_evidence.json').write_text(json.dumps(out,indent=2)+chr(10),encoding='utf-8')
print(json.dumps(out['records']))
if set(stats)-{'flip_rule_holds','skipped_private_tree_dump'}:raise SystemExit('loader winding rule violated')
