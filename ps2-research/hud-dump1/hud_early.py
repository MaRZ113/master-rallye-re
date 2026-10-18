import sys, struct
sys.path.insert(0, sys.argv[1]); import gsdump
G=gsdump.GS; orig=G.kick
def kick(self,x,y,z,f):
    orig(self,x,y,z,f); ptype,attr=self.prim_attr(); c=(attr>>9)&1
    self.kicks[-1]=self.kicks[-1]+((attr,self.r[0x06+c],self.primseq,self.r[0x18+c],self.r[0x4e+c]),)
G.kick=kick
_,_,gs,_=gsdump.replay(sys.argv[2],frames=1)
K=gs.kicks; start=int(sys.argv[3]); seen={}
for i,k in enumerate(K[:start]):
    attr,tex0,seq,xyoff,zbuf=k[-1]
    if attr!=0x5c: continue
    xo=(xyoff&0xffff)/16; yo=((xyoff>>32)&0xffff)/16; x=k[3][0]-xo; y=k[3][1]-yo
    r=seen.setdefault(seq,[i,tex0&0x3fff,x,y,x,y,k[1]]); r[2]=min(r[2],x); r[3]=min(r[3],y); r[4]=max(r[4],x); r[5]=max(r[5],y)
for seq,r in seen.items():
    if -50<r[2]<700 and -50<r[3]<560: print('kick %d tbp=%#06x rect=[%.1f,%.1f,%.1f,%.1f] rgba=%s'%(r[0],r[1],r[2],r[3],r[4],r[5],r[6]))
