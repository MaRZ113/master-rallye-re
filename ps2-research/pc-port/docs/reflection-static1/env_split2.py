import sys, ast
d=ast.literal_eval(open(sys.argv[1]).read()); pc=d['pc']; ps=d['ps2']
g=open(sys.argv[2],'rb').read()[8:]
st=[[tuple(g[(y*64+x)*4+c]*80//128 for c in range(3)) for x in range(64)] for y in range(64)]
variants={'asis':st,'flipV':st[::-1],'flipH':[r[::-1] for r in st],'rot180':[r[::-1] for r in st[::-1]]}
def avg(img,y0,y1,x0=0,x1=64):
    s=[0,0,0];n=0
    for y in range(y0,y1):
        for x in range(x0,x1):
            for c in range(3): s[c]+=img[y][x][c]
            n+=1
    return [v/n for v in s]
# residual: PS2 target - static must be >=0 and smooth-ish; count negative texels
for name,v in variants.items():
    neg=sum(1 for y in range(64) for x in range(64) for c in range(3) if ps[y][x][c]-v[y][x][c]<-8)
    negpc=sum(1 for y in range(64) for x in range(64) for c in range(3) if pc[y][x][c]-v[y][x][c]<-8)
    print(name,'PS2 negatives',neg,'PC negatives',negpc)
v=variants['flipV']
print('rows  PS2 frame est with flipV static [centre]')
for y0 in range(0,64,4):
    s=avg(v,y0,y0+4,24,40); q=avg(ps,y0,y0+4,24,40)
    print('%2d-%2d'%(y0,y0+3), tuple(round(v) for v in s), tuple(round((q[c]-s[c])/0.375) for c in range(3)))
