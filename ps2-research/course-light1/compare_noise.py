import sys,struct
from pathlib import Path
R=Path(r'D:\Game\Master Rallye\master-rallye-re-general\ps2-research')
sys.path[:0]=[str(R/'tools'),r'D:\Game\Master Rallye\master-rallye-re-course\src']
import tngtool as t, psbtool as p
from master_rallye.dxt import parse_dxt, decode_rgba_pixels
ps2root=Path(r'D:\Game\Master Rallye PS2')
manifest,_=t.load_pak(ps2root/'TNG.PAK')
B=chr(92)
def st(px,name):
    n=len(px)//4;vals=[(px[4*i]+px[4*i+1]+px[4*i+2])/3 for i in range(n)];al=[px[4*i+3] for i in range(n)]
    s=sorted(vals);print(name,n,'rgb mean %.1f p10 %d p50 %d p90 %d'%(sum(vals)/n,s[n//10],s[n//2],s[9*n//10]),'alpha mean %.1f min %d max %d'%(sum(al)/n,min(al),max(al)))
for course in ('FRANCE_S1','FRANCE1','TURKEY3','ITALY_S1'):
    path=B+'TNG'+B+'DATAPSM'+B+'COURSE'+B+course+B+'NOISE-TGA.GXI'
    es=[e for e in manifest['entries'] if e['path']==path]
    if not es: print('ps2 none',course);continue
    raw,_=t.read_payload(es[0],ps2root/'TNG.000');g=p.parse_gxi(raw);print('gxi',course,{k:g[k] for k in g if k in('width','height','format','psm')})
    st(raw[8:8+g['width']*g['height']*4],'PS2 '+course)
for c in ('France_S1','France1','Turkey3','Italy_S1'):
    f=Path(r'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked\DataGx\Course')/c/'noise-tga.dxt'
    if f.exists():
        tx=parse_dxt(f);px=decode_rgba_pixels(tx);st(bytes(px) if not isinstance(px,bytes) else px,'PC  '+c)
