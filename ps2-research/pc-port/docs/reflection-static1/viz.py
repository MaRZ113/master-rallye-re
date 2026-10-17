import sys, zlib, struct, ast
sys.path[:0]=[sys.argv[1]]; import gsdump
def save(path, imgs, scale=4):
    W=sum(len(i[0]) for i in imgs)*scale+8*(len(imgs)-1); H=max(len(i) for i in imgs)*scale
    rows=[]
    for y in range(H):
        line=bytearray()
        for k,img in enumerate(imgs):
            for x in range(len(img[0])*scale):
                line+=bytes(img[y//scale][x//scale]) if y//scale<len(img) else b'\0\0\0'
            if k<len(imgs)-1: line+=b'\xff\x00\xff'*8
        rows.append(b'\0'+bytes(line))
    def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d))
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))
hdr,shot,state,regs,packets=gsdump.read_dump(sys.argv[2])
vram=state[373:373+4*1024*1024]
raw=gsdump.read_ct16(vram,0x3840,1,64,64)
v=[[tuple(raw[(y*64+x)*4+c] for c in range(3)) for x in range(64)] for y in range(64)]
raw=gsdump.read_ct16(vram,0x3d00,1,64,64)
t=[[tuple(raw[(y*64+x)*4+c] for c in range(3)) for x in range(64)] for y in range(64)]
g=open(sys.argv[3],'rb').read()[8:]
a=[[tuple(g[(y*64+x)*4+c] for c in range(3)) for x in range(64)] for y in range(64)]
pc=ast.literal_eval(open(sys.argv[4]).read())['pc']
b=lambda img,k:[[tuple(min(255,int(c*k)) for c in p) for p in r] for r in img]
save(sys.argv[5],[b(a,1.5),b(v,1.5),b(t,1.5),b(pc,1.5)])
