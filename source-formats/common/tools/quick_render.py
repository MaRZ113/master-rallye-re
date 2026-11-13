"""Tiny dependency-light OBJ preview renderer (PIL + numpy painter's algorithm).
usage: quick_render.py <in.obj> <out.png> [--size 512]; draws 4 views (front-left, rear-right, side, top)."""
import sys,math,numpy as np
from PIL import Image,ImageDraw
def load(p):
    V=[];F=[]
    for l in open(p):
        if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('f '): F.append([int(t.split('/')[0])-1 for t in l.split()[1:4]])
    return np.array(V),np.array(F)
def view(V,F,yaw,pitch,size):
    c=V.mean(0);P=V-c
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch)
    R1=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);R2=np.array([[1,0,0],[0,cp,-sp],[0,sp,cp]])
    Q=P@R1.T@R2.T
    s=size*0.45/max(1e-6,np.abs(Q[:,:2]).max())
    img=Image.new('RGB',(size,size),(235,235,240));dr=ImageDraw.Draw(img)
    T=Q[F];n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);ln=np.linalg.norm(n,axis=1)+1e-9
    shade=np.abs(n[:,2]/ln)*0.75+0.25
    order=np.argsort(T[:,:,2].mean(1))[::-1]
    for i in order:
        pts=[(size/2+T[i,k,0]*s,size/2-T[i,k,1]*s) for k in range(3)]
        g=int(60+170*shade[i]);dr.polygon(pts,fill=(g,g,int(g*1.05) if g<240 else g),outline=None)
    return img
def main():
    V,F=load(sys.argv[1]);size=512
    views=[(math.radians(35),math.radians(-15)),(math.radians(215),math.radians(-15)),(math.radians(90),0),(0,math.radians(-89))]
    out=Image.new('RGB',(size*2,size*2))
    for k,(y,p) in enumerate(views): out.paste(view(V,F,y,p,size),((k%2)*size,(k//2)*size))
    out.save(sys.argv[2])
if __name__=='__main__':main()
