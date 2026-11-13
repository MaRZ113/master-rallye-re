"""Compare 4x4 Evolution 2 truck rosters: PC TRUCK.POD vs GameCube TRUCK.pod (from rvz.py)."""
import sys,re,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','decoders'))
from evo2_formats import pod2_members,member_bytes
BS=chr(92)
def trucks(path):
    d=open(path,'rb').read();M=pod2_members(d);out={}
    for m in M:
        n=m.name.upper().replace(BS,'/')
        if n.endswith('.TRK'):
            b=member_bytes(d,m)
            names=re.findall(rb'[A-Za-z0-9][A-Za-z0-9 \-\.\'/&]{5,60}',b[:600])
            out[n.split('/')[-1]]=[x.decode('latin1') for x in names[:3]]
    return out,M
if __name__=='__main__':
    pc,Mpc=trucks(sys.argv[1]);gc,Mgc=trucks(sys.argv[2])
    print('PC trk',len(pc),'GC trk',len(gc),'members',len(Mpc),len(Mgc))
    print('GC-only:')
    for k in sorted(set(gc)-set(pc)):print(' ',k,gc[k])
    print('PC-only:')
    for k in sorted(set(pc)-set(gc)):print(' ',k,pc[k])
