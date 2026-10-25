"""Ordered GT4 GS fragment diagnostic. Optional numpy/Pillow, no Blender.

Real textures, source tests, DATE, FBMSK, GIF blending and depth writes are
implemented. VU lighting, generated environment/texgen and effect callbacks
remain explicit unsupported inputs. This is not a claim of native PS2 parity.
"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from PIL import Image
from master_rallye.addon_sdk.gt4_scene import reconstruct


def sample(texture,uv):
    t=texture['registers'];w,h=texture['width'],texture['height'];coords=[]
    for axis,(size,mode) in enumerate(((w,t['wrap_s']),(h,t['wrap_t']))):
        x=np.floor(uv[:,axis]*size).astype(np.int64)
        if mode==0:x%=size
        elif mode==1:x=np.clip(x,0,size-1)
        elif mode==2:x=np.clip(x,t['min_u' if axis==0 else 'min_v'],t['max_u' if axis==0 else 'max_v'])
        elif mode==3:x=(x&t['min_u' if axis==0 else 'min_v'])|t['max_u' if axis==0 else 'max_v']
        if np.any((x<0)|(x>=size)):raise ValueError('region sampler addresses outside decoded texture')
        coords.append(x)
    return np.frombuffer(texture['rgba_ps2'],np.uint8).reshape(h,w,4)[coords[1],coords[0]].astype(np.int32)


def compare(a,fn,b):return (np.zeros_like(a,dtype=bool),np.ones_like(a,dtype=bool),a<b,a<=b,a==b,a>=b,a>b,a!=b)[fn]


def compose(frame,zbuffer,xy,z,rgba,state,blend):
    x,y=xy;old=frame[y,x].astype(np.int32)
    enabled=np.ones(len(x),bool)
    if state['depth_test']:
        # Diagnostic camera depth grows away; GS reverse Z uses >=/>, so
        # source GS methods 2/3 become <=/< in this representation.
        fn=state['depth_func'];enabled &= (np.zeros(len(x),bool),np.ones(len(x),bool),z<=zbuffer[y,x]+1e-6,z<zbuffer[y,x])[fn]
    if state['date']:enabled &= ((old[:,3]>=128)==bool(state['datm']))
    passed=compare(rgba[:,3],state['alpha_func'],state['alpha_ref']) if state['alpha_test'] else np.ones(len(x),bool)
    colour=enabled.copy();depth=enabled&state['depth_write'];mask=np.full(len(x),state['fbmask'],np.uint32)
    failed=~passed
    if state['alpha_fail']==0:colour &= passed;depth &= passed
    elif state['alpha_fail']==1:depth &= passed
    elif state['alpha_fail']==2:colour &= passed
    elif state['alpha_fail']==3:depth &= passed;mask[failed]|=0xff000000
    result=rgba.copy()
    if blend:
        a,b,c,d,fix=state['blend'];rgb=[rgba[:,:3],old[:,:3],np.zeros((len(x),3),np.int32)]
        factor=[rgba[:,3],old[:,3],np.full(len(x),fix)][c]
        result[:,:3]=np.clip(((rgb[a]-rgb[b])*factor[:,None])//128+rgb[d],0,255)
    bits=np.array([1,256,65536,16777216],np.uint32)
    new=(result.astype(np.uint32)*bits).sum(axis=1,dtype=np.uint32);previous=(old.astype(np.uint32)*bits).sum(axis=1,dtype=np.uint32)
    packed=(previous&mask)|(new&~mask)
    out=((packed[:,None]>>np.array([0,8,16,24],np.uint32))&255).astype(np.uint8)
    frame[y[colour],x[colour]]=out[colour];zbuffer[y[depth],x[depth]]=z[depth]


def render(scene,azimuth,elevation,width=900,height=600,*,unlit=False,isolated=None):
    az,el=map(math.radians,(azimuth,elevation));eye=np.array([math.sin(az)*math.cos(el),math.sin(el),math.cos(az)*math.cos(el)])
    right=np.cross([0.,1.,0.],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
    points=np.array([v['position'] for d in scene['draws'] if not d['issues'] for v in d['vertices']])
    lo,hi=points.min(0),points.max(0);centre=(lo+hi)/2;radius=np.linalg.norm(hi-lo)/2;distance=radius*4
    frame=np.zeros((height,width,4),np.uint8);frame[:,:,:3]=[190,196,202];depth=np.full((height,width),np.inf)
    used=[];skipped=[]
    for index,draw in enumerate(scene['draws']):
        if isolated is not None and index!=isolated:continue
        if draw['issues']:skipped.append(index);continue
        used.append(index);vs=draw['vertices'];ps=np.array([v['position'] for v in vs])-centre
        z=distance-ps@eye;perspective=height/(2*math.tan(.3));screen=np.stack([width/2+ps@right*perspective/z,height/2-ps@up*perspective/z],1)
        colours=np.array([v['rgba_ps2'] or [128,128,128,128] for v in vs],np.float64)
        # Keep source colour as-is. Optional directional lighting is explicitly
        # diagnostic only, never the default proof of material reconstruction.
        if not unlit:
            normals=np.array([v['normal'] or [0,1,0] for v in vs]);light=np.array([-.4,.8,-.4]);light/=np.linalg.norm(light)
            colours[:,:3]*=(.6+.4*np.clip(normals@light,0,1))[:,None]
        uv=np.array([v['uv'] or [0.,0.] for v in vs]);texture=draw['texture'];state=draw['state']
        for ids in draw['triangles']:
            ids=np.array(ids);tri=screen[ids];zz=z[ids]
            if min(zz)<=0:continue
            minimum=np.maximum(np.floor(tri.min(0)).astype(int),[0,0]);maximum=np.minimum(np.ceil(tri.max(0)).astype(int),[width-1,height-1])
            if np.any(maximum<minimum):continue
            a,b,c=tri;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-10:continue
            xx,yy=np.meshgrid(np.arange(minimum[0],maximum[0]+1),np.arange(minimum[1],maximum[1]+1));x=xx.ravel();y=yy.ravel();px=x+.5;py=y+.5
            w0=((b[1]-c[1])*(px-c[0])+(c[0]-b[0])*(py-c[1]))/den;w1=((c[1]-a[1])*(px-c[0])+(a[0]-c[0])*(py-c[1]))/den;w2=1-w0-w1
            inside=(w0>=-1e-8)&(w1>=-1e-8)&(w2>=-1e-8)
            if not np.any(inside):continue
            x,y=x[inside],y[inside];weights=np.stack([w0[inside],w1[inside],w2[inside]],1)/zz;inv=weights.sum(1);weights/=inv[:,None];fragment_z=1/inv
            cf=np.clip(np.rint(weights@colours[ids]),0,255).astype(np.int32)
            if texture:
                tex=sample(texture,weights@uv[ids]);reg=texture['registers'];tfx=reg['tfx'];tcc=reg['tcc']
                if tfx==0:
                    src=np.clip(tex*cf//128,0,255)
                    if not tcc:src[:,3]=cf[:,3]
                elif tfx==1:
                    src=tex.copy()
                    if not tcc:src[:,3]=cf[:,3]
                else:
                    src=tex.copy();src[:,:3]=np.clip(tex[:,:3]*cf[:,:3]//128+cf[:,3,None],0,255)
                    src[:,3]=(np.clip(tex[:,3]+cf[:,3],0,255) if tfx==2 else tex[:,3]) if tcc else cf[:,3]
            else:src=cf
            compose(frame,depth,(x,y),fragment_z,src,state,bool(draw['gif'] and draw['gif']['blend']))
    return frame,{'used_packets':used,'unsupported_packets':skipped,'lighting':'source vertex colours, neutral lighting' if unlit else 'diagnostic directional approximation; not VU lighting',
                  'camera':{'azimuth':azimuth,'elevation':elevation,'centre':centre.tolist(),'distance':distance},
                  'limitations':['no VU lighting/clip/fog program','no runtime generated environment/texgen','no source culling qualification','point sampling; no GS mip filtering','shared-edge coverage is diagnostic, not GS subpixel rasterization']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--model',type=int,default=0);p.add_argument('--lod',type=int,default=0);p.add_argument('--callbacks',type=Path);p.add_argument('--unlit',action='store_true');a=p.parse_args()
    if a.output.exists():raise ValueError('output exists; preserve previous diagnostic evidence')
    choices=json.loads(a.callbacks.read_text()) if a.callbacks else {'0':0,'7':0,'11':1,'12':1,'13':1,'14':1}
    raw=a.source.read_bytes();scene=reconstruct(raw,model_index=a.model,lod=a.lod,callbacks=choices);a.output.mkdir(parents=True)
    reports={}
    for name,az,el in [('front',180,5),('rear',0,5),('side',90,0),('top',180,89),('three-quarter',145,12)]:
        pixels,report=render(scene,az,el,unlit=a.unlit);Image.fromarray(pixels[:,:,:3]).save(a.output/(name+'.png'));reports[name]=report
    (a.output/'source-qualification.json').write_text(json.dumps(scene['report'],indent=2)+'\n')
    (a.output/'render-report.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(json.dumps({'shapes':len(scene['report']['shape_inventory']),'accounted':scene['report']['geometry_accounted'],'packets':len(scene['draws']),'unsupported':len(scene['report']['unsupported']),'source_unchanged':a.source.read_bytes()==raw}))

if __name__=='__main__':main()
