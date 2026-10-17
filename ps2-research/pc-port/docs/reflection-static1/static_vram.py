import sys
sys.path.insert(0, sys.argv[1]); import gsdump
hdr,shot,state,regs,packets=gsdump.read_dump(sys.argv[2])
g=open(sys.argv[3],'rb').read()[8:]
asset=[[tuple(g[(y*64+x)*4+c] for c in range(3)) for x in range(64)] for y in range(64)]
for off in (372,373):
    vram=state[off:off+4*1024*1024]
    for bw in (1,2):
        raw=gsdump.read_ct16(vram,0x3840,bw,64,64)
        v=[[tuple(raw[(y*64+x)*4+c] for c in range(3)) for x in range(64)] for y in range(64)]
        def err(a): return sum(abs(v[y][x][c]-a[y][x][c]) for y in range(64) for x in range(64) for c in range(3))/(64*64*3)
        print('off',off,'bw',bw,'asis',round(err(asset),1),'flipV',round(err(asset[::-1]),1),'flipH',round(err([r[::-1] for r in asset]),1))
vram=state[373:373+4*1024*1024]
raw=gsdump.read_ct16(vram,0x3840,1,64,64)
v=[[tuple(raw[(y*64+x)*4+c] for c in range(3)) for x in range(64)] for y in range(64)]
for name,a in (('asis',asset),('flipV',asset[::-1])):
    num=sum(v[y][x][c]*a[y][x][c] for y in range(64) for x in range(64) for c in range(3)); den=sum(a[y][x][c]**2 for y in range(64) for x in range(64) for c in range(3))
    k=num/den
    e=sum(abs(v[y][x][c]-k*a[y][x][c]) for y in range(64) for x in range(64) for c in range(3))/(64*64*3)
    tr=sum(abs(v[y][x][c]-(a[y][x][c]&0xf8)) for y in range(64) for x in range(64) for c in range(3))/(64*64*3)
    print(name,'scale',round(k,3),'err',round(e,2),'trunc err',round(tr,2))
print('VRAM rows avg', [round(sum(sum(v[y][x]) for x in range(64))/192) for y in range(0,64,8)])
print('asset rows avg', [round(sum(sum(asset[y][x]) for x in range(64))/192) for y in range(0,64,8)])
