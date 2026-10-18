"""Rasterise the PS2 HUD draws of a GS dump (flat 2D prims) with VRAM textures; research helper."""
import sys, struct, zlib, json
sys.path.insert(0, sys.argv[1]); import gsdump
G=gsdump.GS; orig=G.kick
def kick(self,x,y,z,f):
    orig(self,x,y,z,f)
    ptype,attr=self.prim_attr(); ctxt=(attr>>9)&1
    self.kicks[-1]=self.kicks[-1]+({'tex0':self.r[0x06+ctxt],'uv':self.r[0x03],'alpha':self.r[0x42+ctxt],'xyoff':self.r[0x18+ctxt],'clamp':self.r[0x08+ctxt],'tex1':self.r[0x14+ctxt],'prim':self.r[0x00],'ptype':ptype,'attr':attr,'seq':self.primseq},)
G.kick=kick
path=sys.argv[2]; start=int(sys.argv[3]); out=sys.argv[4]; skip={int(t,16) for t in sys.argv[5].split(',')} if len(sys.argv)>5 and sys.argv[5] else set()
hdr,shot,state,regs,packets=gsdump.read_dump(path)
_,_,gs,_=gsdump.replay(path,frames=1)
vram=gsdump.vram_of(state)   # CT16 offset; CT32 uses 372
vram32=state[372:372+4*1024*1024]
W,H=640,512
img=[[0.0]*(W*4) for _ in range(H)]
cache={}
def texture(t):
    tbp=t&0x3fff; tbw=(t>>14)&0x3f; psm=(t>>20)&0x3f; tw=1<<((t>>26)&0xf); th=1<<((t>>30)&0xf)
    k=(tbp,tbw,psm,tw,th)
    if k not in cache:
        if psm==0: raw=gsdump.read_ct32(vram32,tbp,max(1,tbw),tw,th)
        elif psm==2: raw=gsdump.read_ct16(vram,tbp,max(1,tbw),tw,th)
        else: raw=None
        cache[k]=(raw,tw,th)
    return cache[k]
def edge(a,b,p): return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def tri(v,e,used):
    t=e['tex0']; tme=(e['attr']>>4)&1; abe=(e['attr']>>6)&1; fst=(e['attr']>>8)&1; tcc=(t>>34)&1; tfx=(t>>35)&3
    raw,tw,th=texture(t) if tme else (None,0,0)
    if tme and raw is None: return
    xs=[p[0] for p in v]; ys=[p[1] for p in v]
    area=edge(v[0],v[1],v[2])
    if area==0: return
    a=e['alpha']; A=a&3; B=(a>>2)&3; C=(a>>4)&3; D=(a>>6)&3; FIX=(a>>32)&0xff
    for y in range(max(0,int(min(ys))),min(H,int(max(ys))+1)):
        for x in range(max(0,int(min(xs))),min(W,int(max(xs))+1)):
            p=(x+.5,y+.5); w0=edge(v[1],v[2],p)/area; w1=edge(v[2],v[0],p)/area; w2=1-w0-w1
            if w0<-1e-6 or w1<-1e-6 or w2<-1e-6: continue
            col=[sum(w*vv[3][c] for w,vv in zip((w0,w1,w2),v)) for c in range(4)]
            if tme:
                u=sum(w*vv[4] for w,vv in zip((w0,w1,w2),v)); vv_=sum(w*vv[5] for w,vv in zip((w0,w1,w2),v))
                tx=min(tw-1,max(0,int(u))); ty=min(th-1,max(0,int(vv_)))
                o=(ty*tw+tx)*4; tc=list(raw[o:o+4])
                if tcc==0: tc[3]=128
                if tfx==0: col=[min(255,tc[c]*col[c]/128) for c in range(3)]+[min(255,tc[3]*col[3]/128) if tcc else col[3]]
                elif tfx==1: col=tc[:3]+[tc[3] if tcc else col[3]]
            row=img[y]; d=row[x*4:x*4+3]
            if abe:
                cs=col[:3]; cd=d; As=col[3]/128.0
                sel=lambda s:(cs,cd,[0,0,0])[s] if s<3 else None
                aa=(As,d and row[x*4+3]/128.0,FIX/128.0)[C] if C<3 else 0
                res=[(sel(A)[c]-sel(B)[c])*aa+sel(D)[c] for c in range(3)]
            else: res=col[:3]
            for c in range(3): row[x*4+c]=max(0,min(255,res[c]))
            row[x*4+3]=max(row[x*4+3],min(128,col[3]))
            used.add((x,y))
K=gs.kicks
groups=[]
queue=[]
for i in range(start,len(K)):
    k=K[i]; e=k[-1]
    if (e['tex0']&0x3fff) in skip and (e['attr']>>4)&1: queue=[]; continue
    xo=(e['xyoff']&0xffff)/16.0; yo=((e['xyoff']>>32)&0xffff)/16.0
    if (e['attr']>>8)&1:
        uv=e['uv']; u=(uv&0x3fff)/16.0; vv=((uv>>16)&0x3fff)/16.0
    else:
        st=k[6]; s_=struct.unpack('<f',struct.pack('<I',st&0xffffffff))[0]; t_=struct.unpack('<f',struct.pack('<I',(st>>32)&0xffffffff))[0]; q=k[5] or 1.0
        tex0=e['tex0']; u=s_/q*(1<<((tex0>>26)&0xf)); vv=t_/q*(1<<((tex0>>30)&0xf))
    vert=(k[3][0]+2048-xo-2048+0, k[3][1]+2048-yo-2048, None, k[1], u, vv)
    # k[3] already /16 absolute coords; screen = abs - xyoffset
    vert=(k[3][0]-xo, k[3][1]-yo, None, k[1], u, vv)
    pt=e['ptype']
    if e['seq']!=globals().get('_lastseq'): queue=[]; globals()['_lastseq']=e['seq']
    queue.append(vert)
    used=set()
    if pt==3 and len(queue)==3: tri(queue,e,used); queue=[]
    elif pt==4 and len(queue)>=3: tri(queue[-3:],e,used)
    elif pt==5 and len(queue)>=3: tri([queue[0]]+queue[-2:],e,used)
    elif pt==6 and len(queue)==2:
        a,b=queue; q=[(a[0],a[1],None,b[3],a[4],a[5]),(b[0],a[1],None,b[3],b[4],a[5]),(a[0],b[1],None,b[3],a[4],b[5]),(b[0],b[1],None,b[3],b[4],b[5])]
        tri(q[:3],e,used); tri(q[1:],e,used); queue=[]
    if pt in (3,6) and len(queue)>=3: queue=[]
    if used:
        if groups and groups[-1]['tex0']==e['tex0'] and groups[-1]['rgba']==k[1]:
            g=groups[-1]
        else:
            g={'first':i,'tex0':e['tex0'],'rgba':k[1],'alpha':e['alpha'],'bbox':[W,H,0,0]}; groups.append(g)
        for x,y in used:
            b=g['bbox']; b[0]=min(b[0],x); b[1]=min(b[1],y); b[2]=max(b[2],x); b[3]=max(b[3],y)
        g['last']=i
    # reset strips on new prim (PRIM write resets queue in GS; approximate by kick count tracking)
rows=[]
for y in range(H):
    line=bytearray()
    for x in range(W):
        r,g_,b,a=img[y][x*4:x*4+4]
        bg=60 if ((x//16+y//16)&1) else 90
        line+=bytes(int(c) if a>0 or c>0 else bg for c in (r,g_,b))
    rows.append(b'\0'+bytes(line))
def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d))
open(out,'wb').write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))
for g in groups:
    t=g['tex0']; print('kicks %5d-%5d tbp=%#06x psm=%d tw=%d th=%d tcc=%d rgba=%s alpha=%#x bbox=%s'%(g['first'],g['last'],t&0x3fff,(t>>20)&0x3f,1<<((t>>26)&0xf),1<<((t>>30)&0xf),(t>>34)&1,g['rgba'],g['alpha'],g['bbox']))
