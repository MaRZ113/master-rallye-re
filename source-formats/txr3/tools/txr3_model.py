"""TXR3 / Shutokou Battle 01 (Genki, PS2 SLPM-65308) car container -> OBJ + MTL + PNG (diagnostic).

Container: u32 n=3, u32 offsets[3]; section0 = model ('0IVX00.1' 'LDMX00.2' 'MRON00.2'),
section1 = TIM2 texture set, section2 = small table.
Model: material records (16-byte header, texture index = byte +14, then ambient/diffuse/
specular vec4, u32 0x32 ...) followed by DMA/VIF packets. Each draw batch is
  UNPACK V4-32 x4 (GIF tag + 3 qwords) | V3-32 positions | V2-32 UV | V4-16 normals
(normal w = 0x7FFF draws, any other w = strip restart / ADC). One batch = one triangle strip.
Axes: +Y up, metres. Car file order follows the body-code sort of the car table
(BUILD entry 26677), e.g. VehiCROSS UGS250 = BUILD entry 355."""
import struct,sys,os
MAT_PAT=b'\x00\x00\x80\x3f'*3+b'\x32\x00\x00\x00'
def usize(c,num):
    vn=(c>>2)&3;vl=c&3
    if vl==3:return (num*2+3)//4*4
    return (num*(vn+1)*[32,16,8,5][vl]//8+3)//4*4
def materials(s):
    out=[];i=0
    while True:
        i=s.find(MAT_PAT,i)
        if i<0:break
        rec=i-48
        if rec>=0:out.append((rec,s[rec+14]))
        i+=16
    return out
def batches(s):
    mats=materials(s);mi=0;o=0;cur=None;out=[]
    while o+4<=len(s):
        w=struct.unpack_from('<I',s,o)[0];c=(w>>24)&0x7f;num=(w>>16)&0xff
        if 0x60<=c<=0x7f and num>0 and (w&0x8000):
            n=usize(c&0x1f,num);data=s[o+4:o+4+n]
            if len(data)<n:break
            while mi+1<len(mats) and mats[mi+1][0]<o: mi+=1
            if c==0x6c and num==4:
                cur={'pos':None,'uv':None,'nrm':None,'off':o,'tex':mats[mi][1] if mats and mats[mi][0]<o else None};out.append(cur)
            elif cur is not None and c==0x68: cur['pos']=[struct.unpack_from('<3f',data,12*k) for k in range(num)]
            elif cur is not None and c==0x64: cur['uv']=[struct.unpack_from('<2f',data,8*k) for k in range(num)]
            elif cur is not None and c==0x6d: cur['nrm']=[struct.unpack_from('<4h',data,8*k) for k in range(num)]
            o+=4+n;continue
        o+=4
    return [b for b in out if b['pos']]
def triangles(b,base):
    nr=b['nrm'] or [];F=[]
    for k in range(2,len(b['pos'])):
        if k<len(nr) and nr[k][3]!=0x7fff: continue
        a,bb,c=base+k-2,base+k-1,base+k
        F.append((a,bb,c) if k%2==0 else (bb,a,c))
    return F
def export(path,outdir,stem):
    sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','..','common','tools'))
    from tim2 import read
    d=open(path,'rb').read();n=struct.unpack_from('<I',d)[0];offs=list(struct.unpack_from('<%dI'%n,d,4))+[len(d)]
    s=d[offs[0]:offs[1]];os.makedirs(outdir,exist_ok=True)
    texs=read(d[offs[1]:offs[2]],csm1_unswizzle=False) if d[offs[1]:offs[1]+4]==b'TIM2' else []
    for k,im in enumerate(texs): im.save(os.path.join(outdir,'%s_t%03d.png'%(stem,k)))
    B=batches(s);V=[];VT=[];groups={}
    for b in B:
        base=len(V);V+=b['pos'];VT+=b['uv'] if b['uv'] and len(b['uv'])==len(b['pos']) else [(0,0)]*len(b['pos'])
        groups.setdefault(b['tex'],[]).extend(triangles(b,base))
    with open(os.path.join(outdir,stem+'.mtl'),'w') as f:
        for t in groups:
            f.write('newmtl m%s\nKd 1 1 1\n'%t)
            if t is not None and t<len(texs): f.write('map_Kd %s_t%03d.png\n'%(stem,t))
    with open(os.path.join(outdir,stem+'.obj'),'w') as f:
        f.write('mtllib %s.mtl\n'%stem)
        # The source is mirrored in X (badge text reads backwards otherwise): negate X, flip winding.
        for v in V:f.write('v %.5f %.5f %.5f\n'%(-v[0],v[1],v[2]))
        for t in VT:f.write('vt %.5f %.5f\n'%(t[0],1-t[1]))
        for t,F in groups.items():
            f.write('usemtl m%s\n'%t)
            for a,b_,c in F:f.write('f %d/%d %d/%d %d/%d\n'%(a+1,a+1,c+1,c+1,b_+1,b_+1))
    return {'batches':len(B),'vertices':len(V),'triangles':sum(len(F) for F in groups.values()),'textures':len(texs),'materials':len(groups)}
if __name__=='__main__':print(export(sys.argv[1],sys.argv[2],sys.argv[3]))
