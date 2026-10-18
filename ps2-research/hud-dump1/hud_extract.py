"""PS2 HUD primitive extractor (GS dump): one record per PRIM (strip/sprite/untextured shape)."""
import sys, struct, json, os
sys.path.insert(0, sys.argv[1]); import gsdump
G=gsdump.GS; orig=G.kick
def kick(self,x,y,z,f):
    orig(self,x,y,z,f)
    ptype,attr=self.prim_attr(); ctxt=(attr>>9)&1
    self.kicks[-1]=self.kicks[-1]+({'tex0':self.r[0x06+ctxt],'uv':self.r[0x03],'alpha':self.r[0x42+ctxt],'xyoff':self.r[0x18+ctxt],'ptype':ptype,'attr':attr,'seq':self.primseq,'test':self.r[0x47+ctxt],'zbuf':self.r[0x4e+ctxt],'frame':self.r[0x4c+ctxt],'tex1':self.r[0x14+ctxt],'clamp':self.r[0x08+ctxt]},)
G.kick=kick
PARTICLES={0x3810,0x3820,0x2e50}
def f32(v): return struct.unpack('<f',struct.pack('<I',v&0xffffffff))[0]
out={}
for path in sys.argv[3:]:
    _,_,gs,_=gsdump.replay(path,frames=1)
    K=gs.kicks
    start=min(i for i,k in enumerate(K) if (k[-1]['tex0']&0x3fff) in (0x30c0,0x3100) and k[-1]['attr']&0x10 and (k[-1]['frame']&0x1ff)==0 and (k[-1]['zbuf']>>32)&1)
    prims=[]; cur=None
    for i in range(start,len(K)):
        k=K[i]; e=k[-1]
        if (e['frame']&0x1ff)!=0: continue
        tme=(e['attr']>>4)&1; tbp=e['tex0']&0x3fff
        if tme and tbp in PARTICLES: continue
        if cur is None or cur['seq']!=e['seq']:
            cur={'seq':e['seq'],'first':i,'ptype':e['ptype'],'attr':e['attr'],'tme':tme,'tbp':tbp if tme else None,
                 'psm':(e['tex0']>>20)&0x3f,'tw':1<<((e['tex0']>>26)&0xf),'th':1<<((e['tex0']>>30)&0xf),'tcc':(e['tex0']>>34)&1,'tfx':(e['tex0']>>35)&3,
                 'alpha':e['alpha'],'test':e['test']&0xffffffff,'tex1':e['tex1'],'clamp':e['clamp'],'v':[]}
            prims.append(cur)
        xo=(e['xyoff']&0xffff)/16.0; yo=((e['xyoff']>>32)&0xffff)/16.0
        st=k[6]; q=k[5] or 1.0
        s_=f32(st)/q*cur['tw']; t_=f32(st>>32)/q*cur['th']
        if (e['attr']>>8)&1: s_=(e['uv']&0x3fff)/16.0; t_=((e['uv']>>16)&0x3fff)/16.0
        cur['v'].append({'x':round(k[3][0]-xo,3),'y':round(k[3][1]-yo,3),'z':k[3][2],'rgba':k[1],'u':round(s_,3),'vv':round(t_,3)})
    for p in prims:
        xs=[v['x'] for v in p['v']]; ys=[v['y'] for v in p['v']]
        p['rect']=[min(xs),min(ys),max(xs),max(ys)]
        if p['tme']: p['st']=[min(v['u'] for v in p['v']),min(v['vv'] for v in p['v']),max(v['u'] for v in p['v']),max(v['vv'] for v in p['v'])]
        p['rgba']=sorted({tuple(v['rgba']) for v in p['v']})
    out[os.path.basename(path)]={'start':start,'kicks':len(K),'prims':prims}
    print(os.path.basename(path),'start',start,'hud prims',len(prims))
json.dump(out,open(sys.argv[2],'w'),indent=0)
