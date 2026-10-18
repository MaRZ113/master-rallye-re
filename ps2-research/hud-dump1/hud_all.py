"""Every HUD-class primitive in a PS2 GS dump frame, from the first kick (hud_extract.py starts at the damage row).
HUD class: draw buffer FBP 0, ZMSK=1, attr 0x5c (textured STQ quads) or 0x14c (untextured), not a particle page.
usage: python hud_all.py <dir with gsdump.py> <out.json> <dump.gs>...
"""
import sys, struct, json, os
sys.path.insert(0, sys.argv[1]); import gsdump
G=gsdump.GS; orig=G.kick
def kick(self,x,y,z,f):
    orig(self,x,y,z,f)
    ptype,attr=self.prim_attr(); c=(attr>>9)&1
    self.kicks[-1]=self.kicks[-1]+({'tex0':self.r[0x06+c],'uv':self.r[0x03],'alpha':self.r[0x42+c],'xyoff':self.r[0x18+c],'ptype':ptype,'attr':attr,
                                    'seq':self.primseq,'zbuf':self.r[0x4e+c],'frame':self.r[0x4c+c]},)
G.kick=kick
PARTICLES={0x3810,0x3820,0x2e50}
def f32(v): return struct.unpack('<f',struct.pack('<I',v&0xffffffff))[0]
out={}
for path in sys.argv[3:]:
    _,_,gs,_=gsdump.replay(path,frames=1)
    prims=[]; cur=None
    for i,k in enumerate(gs.kicks):
        e=k[-1]
        if (e['frame']&0x1ff)!=0 or not (e['zbuf']>>32)&1 or e['attr'] not in (0x5c,0x14c): continue
        tme=(e['attr']>>4)&1; tbp=e['tex0']&0x3fff
        if tme and tbp in PARTICLES: continue
        if cur is None or cur['seq']!=e['seq']:
            cur={'seq':e['seq'],'first':i,'ptype':e['ptype'],'attr':e['attr'],'tbp':tbp if tme else None,
                 'tw':1<<((e['tex0']>>26)&0xf),'th':1<<((e['tex0']>>30)&0xf),'alpha':e['alpha'],'v':[]}
            prims.append(cur)
        xo=(e['xyoff']&0xffff)/16.0; yo=((e['xyoff']>>32)&0xffff)/16.0
        q=k[5] or 1.0; s_=f32(k[6])/q*cur['tw']; t_=f32(k[6]>>32)/q*cur['th']
        cur['v'].append({'x':round(k[3][0]-xo,3),'y':round(k[3][1]-yo,3),'rgba':k[1],'u':round(s_,3),'vv':round(t_,3)})
    keep=[]
    for p in prims:
        xs=[v['x'] for v in p['v']]; ys=[v['y'] for v in p['v']]
        p['rect']=[min(xs),min(ys),max(xs),max(ys)]
        if not (-64<p['rect'][0]<704 and -64<p['rect'][1]<576): continue
        if p['tbp'] is not None: p['st']=[min(v['u'] for v in p['v']),min(v['vv'] for v in p['v']),max(v['u'] for v in p['v']),max(v['vv'] for v in p['v'])]
        p['rgba']=sorted({tuple(v['rgba']) for v in p['v']})
        keep.append(p)
    out[os.path.basename(path)]={'kicks':len(gs.kicks),'prims':keep}
    print(os.path.basename(path),'hud-class prims',len(keep))
json.dump(out,open(sys.argv[2],'w'),indent=0)
