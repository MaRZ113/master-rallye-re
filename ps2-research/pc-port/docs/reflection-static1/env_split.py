import sys, ast
d=ast.literal_eval(open(sys.argv[1]).read()); pc=d['pc']; ps=d['ps2']
g=open(sys.argv[2],'rb').read()[8:]
st=[[tuple(g[(y*64+x)*4+c]*80//128 for c in range(3)) for x in range(64)] for y in range(64)]
def avg(img,y0,y1,x0=0,x1=64):
    s=[0,0,0];n=0
    for y in range(y0,y1):
        for x in range(x0,x1):
            for c in range(3): s[c]+=img[y][x][c]
            n+=1
    return [v/n for v in s]
print('rows  static(.625)     PC frame est (/0.376)    PS2 frame est (/0.375)   [centre cols 24..39]')
for y0 in range(0,64,4):
    s=avg(st,y0,y0+4,24,40); p=avg(pc,y0,y0+4,24,40); q=avg(ps,y0,y0+4,24,40)
    f=lambda a:tuple(round((a[c]-s[c])/0.375) for c in range(3))
    print('%2d-%2d'%(y0,y0+3), tuple(round(v) for v in s), f(p), f(q))
