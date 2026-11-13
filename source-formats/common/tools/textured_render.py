"""Z-buffered textured preview of an OBJ+MTL (numpy + PIL), four views in one PNG.
usage: textured_render.py <in.obj> <out.png> [size] [--up y|z] [--flipv]"""
import sys,os,math,numpy as np
from PIL import Image
def load(p):
    V=[];T=[];F=[];mat=None;mtl={}
    d=os.path.dirname(p)
    for l in open(p):
        a=l.split()
        if not a:continue
        if a[0]=='v':V.append([float(x) for x in a[1:4]])
        elif a[0]=='vt':T.append([float(x) for x in a[1:3]])
        elif a[0]=='usemtl':mat=a[1]
        elif a[0]=='mtllib':
            cur=None
            for m in open(os.path.join(d,a[1])):
                b=m.split()
                if not b:continue
                if b[0]=='newmtl':cur=b[1]
                elif b[0]=='map_Kd':mtl[cur]=np.asarray(Image.open(os.path.join(d,b[1])).convert('RGBA'),dtype=np.float32)/255
        elif a[0]=='f':
            idx=[t.split('/') for t in a[1:4]]
            F.append(([int(x[0])-1 for x in idx],[int(x[1])-1 if len(x)>1 and x[1] else 0 for x in idx],mat))
    return np.array(V),np.array(T) if T else np.zeros((1,2)),F,mtl
def render(V,T,F,mtl,yaw,pitch,size,flipv):
    c=(V.max(0)+V.min(0))/2;P=V-c
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch)
    R=np.array([[1,0,0],[0,cp,-sp],[0,sp,cp]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Q=P@R.T;s=size*0.46/np.abs(Q[:,:2]).max()
    X=size/2+Q[:,0]*s;Y=size/2-Q[:,1]*s;Z=Q[:,2]
    img=np.full((size,size,3),0.92,np.float32);zb=np.full((size,size),1e9,np.float32)
    L=np.array([0.3,0.5,-0.8]);L/=np.linalg.norm(L)
    for vi,ti,m in F:
        x=X[vi];y=Y[vi];z=Z[vi]
        x0,x1=int(max(0,math.floor(x.min()))),int(min(size-1,math.ceil(x.max())));y0,y1=int(max(0,math.floor(y.min()))),int(min(size-1,math.ceil(y.max())))
        if x0>x1 or y0>y1:continue
        den=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
        if abs(den)<1e-9:continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        w0=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/den;w1=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/den;w2=1-w0-w1
        msk=(w0>=0)&(w1>=0)&(w2>=0)
        if not msk.any():continue
        zz=w0*z[0]+w1*z[1]+w2*z[2];sub=zb[y0:y1+1,x0:x1+1];msk&=zz<sub
        if not msk.any():continue
        tex=mtl.get(m)
        n=np.cross(Q[vi[1]]-Q[vi[0]],Q[vi[2]]-Q[vi[0]]);n/=np.linalg.norm(n)+1e-9;sh=0.45+0.55*abs(n@L)
        if tex is not None and len(T)>max(ti):
            uv=T[ti];u=w0*uv[0,0]+w1*uv[1,0]+w2*uv[2,0];v=w0*uv[0,1]+w1*uv[1,1]+w2*uv[2,1]
            if flipv: v=1-v
            h,w,_=tex.shape;px=tex[np.clip(((1-v)%1.0)*h,0,h-1).astype(int),np.clip((u%1.0)*w,0,w-1).astype(int)]
            msk&=px[...,3]>0.1;col=px[...,:3]*sh
        else: col=np.full(gx.shape+(3,),0.7*sh,np.float32)
        sub[msk]=zz[msk];img[y0:y1+1,x0:x1+1][msk]=col[msk]
    return Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8))
def main():
    a=sys.argv;size=int(a[3]) if len(a)>3 and a[3].isdigit() else 512;flipv='--flipv' in a
    V,T,F,mtl=load(a[1])
    views=[(35,-12),(215,-12),(90,0),(270,0)]
    out=Image.new('RGB',(size*2,size*2))
    for k,(y,p) in enumerate(views): out.paste(render(V,T,F,mtl,math.radians(y),math.radians(p),size,flipv),((k%2)*size,(k//2)*size))
    out.save(a[2])
if __name__=='__main__':main()
