import sys,struct,json,statistics as st
from pathlib import Path
R=Path(r'D:\Game\Master Rallye\master-rallye-re-general\ps2-research')
sys.path[:0]=[str(R/'tools'),r'D:\Game\Master Rallye\master-rallye-re-course\src']
import tngtool as t, water_runtime as w, geometry_delta as g
from master_rallye.dx_course import parse_course_dx
ps2root=Path(r'D:\Game\Master Rallye PS2');pcroot=Path(r'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked')
manifest,_=t.load_pak(ps2root/'TNG.PAK')
out={}
for course in sys.argv[1:]:
    B=chr(92);path=B+'TNG'+B+'DATAPSM'+B+'COURSE'+B+course+B+course+'.PSM'
    e=[x for x in manifest['entries'] if x['path']==path][0]
    payload,_=t.read_payload(e,ps2root/'TNG.000')
    sc=w.decode_scene(payload)
    nv=sc.vertex_count
    ps2col=[struct.unpack_from('<4B',payload,32+i*52+16) for i in range(nv)]
    ps2n=[struct.unpack_from('<3f',payload,32+i*52) for i in range(nv)]
    ps2pos=[sc.position(i) for i in range(nv)]
    dx=sorted((pcroot/'DataGx'/'Course'/w.CASES[course]).glob('*.dx'))[0]
    m=parse_course_dx(dx);data=dx.read_bytes();v=m.vertices
    pcn=len(v.positions)
    pccol=[struct.unpack_from('<4B',data,v.color_offset+4*i) for i in range(pcn)]  # D3DCOLOR BGRA bytes
    key=lambda p:tuple(round(c,3) for c in p)
    idx={}
    for i,p in enumerate(v.positions):idx.setdefault(key(p),i)
    pairs=[(i,idx[key(p)]) for i,p in enumerate(ps2pos) if key(p) in idx]
    def stats(vals):
        vals=sorted(vals);n=len(vals);return [round(vals[int(n*q)],1) for q in (.1,.5,.9)]+[round(sum(vals)/n,1)]
    # PS2 bytes RGBA, PC bytes B,G,R,A
    pr=[ps2col[a][0] for a,b in pairs];pg=[ps2col[a][1] for a,b in pairs];pb=[ps2col[a][2] for a,b in pairs];pa=[ps2col[a][3] for a,b in pairs]
    cr=[pccol[b][2] for a,b in pairs];cg=[pccol[b][1] for a,b in pairs];cb=[pccol[b][0] for a,b in pairs];ca=[pccol[b][3] for a,b in pairs]
    ratio=[ (ps2col[a][0]+ps2col[a][1]+ps2col[a][2])/max(1,pccol[b][0]+pccol[b][1]+pccol[b][2]) for a,b in pairs if pccol[b][0]+pccol[b][1]+pccol[b][2]>30]
    res={'ps2_vertices':nv,'pc_vertices':pcn,'matched':len(pairs),
         'ps2_rgba_p10_50_90_mean':[stats(pr),stats(pg),stats(pb),stats(pa)],
         'pc_rgba_p10_50_90_mean':[stats(cr),stats(cg),stats(cb),stats(ca)],
         'ps2_over_pc_sum_ratio_p10_50_90':stats(ratio)[:3],
         'ps2_all_rgb_mean':[round(sum(c[k] for c in ps2col)/nv,1) for k in range(4)],
         'pc_all_rgb_mean':[round(sum(c[k] for c in pccol)/pcn,1) for k in (2,1,0,3)],
         'ps2_normal_y_mean':round(sum(n[1] for n in ps2n)/nv,3)}
    out[course]=res;print(course,json.dumps(res))
