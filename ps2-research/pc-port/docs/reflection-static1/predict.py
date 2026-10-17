import sys, ast
d=ast.literal_eval(open(sys.argv[1]).read()); pc=d['pc']; ps=d['ps2']
g=open(sys.argv[2],'rb').read()[8:]
st=[[tuple(g[(y*64+x)*4+c]*80//128 for c in range(3)) for x in range(64)] for y in range(64)]
fl=st[::-1]
new=[[tuple(max(0,min(255,pc[y][x][c]-st[y][x][c]+fl[y][x][c])) for c in range(3)) for x in range(64)] for y in range(64)]
def avg(img,y0,y1,x0=24,x1=40):
    s=[0,0,0];n=0
    for y in range(y0,y1):
        for x in range(x0,x1):
            for c in range(3): s[c]+=img[y][x][c]
            n+=1
    return tuple(round(v/n) for v in s)
print('rows  PC now          PC fixed (pred)   PS2   [centre cols]')
for y0 in range(0,64,8): print('%2d-%2d'%(y0,y0+7),avg(pc,y0,y0+8),avg(new,y0,y0+8),avg(ps,y0,y0+8))
lum=lambda p:.299*p[0]+.587*p[1]+.114*p[2]
for name,img in (('PC now',pc),('PC fixed',new),('PS2',ps)):
    print(name,'top-half lum',round(sum(lum(img[y][x]) for y in range(32) for x in range(64))/2048,1),'bottom-half lum',round(sum(lum(img[y][x]) for y in range(32,64) for x in range(64))/2048,1))
open(sys.argv[3],'w').write(repr({'pc':new,'ps2':ps}))
