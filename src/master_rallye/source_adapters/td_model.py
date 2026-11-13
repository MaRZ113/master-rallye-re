"""Total Drivin' (PS1) level object file -> OBJ (geometry; diagnostic).

Level object chunk (3rd LZW chunk of a LEVELS.DAT entry) holds named nodes:
name[32]; u8 kind; i32 pos[3]; i32 rot[9] (4096 = 1.0); u16 a, u16 b, i16 c, u16 nverts, u16 0;
nverts x u32 packed vertex (x = signed 10 bits, y = signed 11, z = signed 11; units x2 in
the bbox that follows); i16 bbox[6] + 8 bytes; face records (20 bytes:
i16 normal[3], i16 d, u16 flags, u16 material, u32 colour/texture id, u32 first corner)
until the corner count word; u32 ncorners; ncorners x (u8 vertex, u8 page, u8 u, u8 v).
Cars: <CLASS><n> node with BODY + FLWHEEL/FRWHEEL/BLWHEEL/BRWHEEL, plus <CLASS>A<n> /
<CLASS>B<n> lower LODs."""
import struct,sys,re
def sx(v,n): return v-(1<<n) if v>>(n-1) else v
def parse_mesh(d,name_off):
    h=name_off+0x20;kind=d[h];pos=struct.unpack_from('<3i',d,h+1);rot=struct.unpack_from('<9i',d,h+13)
    p=h+49;a,b,c,nv,_=struct.unpack_from('<HHhHH',d,p);v0=p+10
    V=[]
    for k in range(nv):
        w=struct.unpack_from('<I',d,v0+4*k)[0]
        V.append((sx(w&0x3ff,10)*2,sx((w>>10)&0x7ff,11)*2,sx(w>>21,11)*2))
    f=v0+4*nv+20;F=[];prev=-1;k=0
    while True:
        r=struct.unpack_from('<4hHHII',d,f+20*k)
        if r[7]<=prev or r[7]>65535:break
        F.append(r);prev=r[7];k+=1
    e=f+20*len(F)
    # find corner count: first u32 after faces equal to plausible total
    q=e
    while q<e+64:
        n=struct.unpack_from('<I',d,q)[0]
        if F and F[-1][7]<n<=F[-1][7]+4: break
        q+=4
    C=[struct.unpack_from('<4B',d,q+4+4*k) for k in range(n)]
    polys=[]
    for i,r in enumerate(F):
        s=r[7];t=F[i+1][7] if i+1<len(F) else n
        polys.append(([C[j][0] for j in range(s,t)],[(C[j][2],C[j][3]) for j in range(s,t)],C[s][1],r[5]))
    return {'pos':pos,'rot':rot,'V':V,'polys':polys,'end':q+4+4*n}
def find_car(d,car):
    i=d.find(car.encode()+b'\x00')
    parts={}
    for nm in ('BODY','FLWHEEL','FRWHEEL','BLWHEEL','BRWHEEL'):
        j=d.find(nm.encode()+b'\x00',i)
        if j>=0 and j-i<60000 and d[j+0x20]==3: parts[nm]=parse_mesh(d,j)  # kind 2 = wheel record (not a mesh)
    return parts
def to_obj(parts,out):
    V=[];F=[]
    for nm,m in parts.items():
        base=len(V);px,py,pz=m['pos'] if nm!='BODY' else (0,0,0)
        V+=[(x+px,y+py,z+pz) for x,y,z in m['V']]
        for idx,_,_,_ in m['polys']:
            idx=[i for i in idx if i<len(m['V'])]
            for k in range(1,len(idx)-1): F.append((base+idx[0],base+idx[k],base+idx[k+1]))
    with open(out,'w') as f:
        for v in V:f.write('v %.3f %.3f %.3f\n'%(v[0]/100.0,v[1]/100.0,v[2]/100.0))
        for t in F:f.write('f %d %d %d\n'%(t[0]+1,t[1]+1,t[2]+1))
    return len(V),len(F)
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read();print(to_obj(find_car(d,sys.argv[2]),sys.argv[3]))
