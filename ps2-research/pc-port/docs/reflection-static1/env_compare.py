import sys
sys.path[:0]=[sys.argv[1], sys.argv[2]]
import png, gsdump
w,h,px=png.load(sys.argv[3])
pc=[[px(192+4*x+1,16+4*y+1) for x in range(64)] for y in range(64)]
hdr,shot,state,regs,packets=gsdump.read_dump(sys.argv[4])
raw=gsdump.read_ct16(gsdump.vram_of(state),0x3d00,1,64,64)
ps=[[tuple(raw[(y*64+x)*4:(y*64+x)*4+3]) for x in range(64)] for y in range(64)]
def avg(img,y0,y1,x0=0,x1=64):
    s=[0,0,0];n=0
    for y in range(y0,y1):
        for x in range(x0,x1):
            for c in range(3): s[c]+=img[y][x][c]
            n+=1
    return tuple(round(v/n) for v in s)
print('rows   PC(all cols)      PS2(all cols)     PC(centre16)    PS2(centre16)')
for y0 in range(0,64,4):
    print('%2d-%2d'%(y0,y0+3), avg(pc,y0,y0+4), avg(ps,y0,y0+4), avg(pc,y0,y0+4,24,40), avg(ps,y0,y0+4,24,40))
print('whole', avg(pc,0,64), avg(ps,0,64))
open(sys.argv[5],'w').write(repr({'pc':pc,'ps2':ps}))
