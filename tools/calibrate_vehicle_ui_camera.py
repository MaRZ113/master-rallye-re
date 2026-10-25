"""Offline silhouette-fit authoring camera against a supplied stock UI frame.

This estimates a projection; it does not recover native camera source settings.
Only stock model geometry and a user-owned texture are read.
"""
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.dxt import parse_dxt,decode_rgba_pixels
from master_rallye.addon_sdk.ui_assets import alpha_bounds
import gtmat,vmesh_raster as raster

def mask(points,tris,az,el,target,W=128,H=128,distance=None):
    centre=tuple((min(p[k] for p in points)+max(p[k] for p in points))/2 for k in range(3))
    projected=[raster._project(p,raster.Camera(az,el,1,centre,distance),0,0) for p in points]
    x0=min(p[0] for p in projected);x1=max(p[0] for p in projected);y0=min(p[1] for p in projected);y1=max(p[1] for p in projected)
    a,b,c,d=target;scale=(c-a)/(x1-x0);cx=(a+c)/2;cy=(b+d)/2
    ps=[((x-(x0+x1)/2)*scale+cx,(y-(y0+y1)/2)*scale+cy) for x,y,z in projected];out=bytearray(W*H)
    for ids in tris:
        triangle=[ps[i] for i in ids];lo=max(0,math.floor(min(p[1] for p in triangle)));hi=min(H,math.ceil(max(p[1] for p in triangle)))
        for y in range(lo,hi):
            crossings=[];yy=y+.5
            for p,q in zip(triangle,triangle[1:]+triangle[:1]):
                if p[1]<=yy<q[1] or q[1]<=yy<p[1]:crossings.append(p[0]+(yy-p[1])*(q[0]-p[0])/(q[1]-p[1]))
            if len(crossings)>=2:
                left=max(0,math.ceil(min(crossings)-.5));right=min(W,math.ceil(max(crossings)-.5))
                if left<right:out[y*W+left:y*W+right]=b'\x01'*(right-left)
    return out

def calibrate(family,frame,out):
    out.mkdir(parents=True,exist_ok=True);model=parse_dx_bytes((family/'complete.dx').read_bytes());geometry=source_geometry(model);points=[];tris=[]
    for g in geometry.values():
        offset=len(points);points.extend(v.position for v in g.vertices);tris.extend(tuple(offset+i for i in t) for t in g.triangles)
    t=parse_dxt(frame);rgba=decode_rgba_pixels(t);reference=bytes(int(a>128) for a in rgba[3::4]);bounds=alpha_bounds((t.width,t.height,rgba),128);rank=[]
    def evaluate(az,el,distance):
        m=mask(points,tris,az,el,bounds,t.width,t.height,distance);union=sum(bool(a or b) for a,b in zip(m,reference));intersection=sum(bool(a and b) for a,b in zip(m,reference));return {'azimuth':az,'elevation':el,'distance_m':distance,'silhouette_iou':intersection/union}
    for distance in (None,6,8,10,14,20,30):
        for az in range(110,161,5):
            for el in range(5,31,5):rank.append(evaluate(az,el,distance))
    best=max(rank,key=lambda x:x['silhouette_iou'])
    for az in range(best['azimuth']-4,best['azimuth']+5):
        for el in range(max(0,best['elevation']-4),best['elevation']+5):rank.append(evaluate(az,el,best['distance_m']))
    best=max(rank,key=lambda x:x['silhouette_iou'])
    if best['distance_m']:
        for step in range(-4,5):
            for az in range(best['azimuth']-2,best['azimuth']+3):
                for el in range(max(0,best['elevation']-2),best['elevation']+3):rank.append(evaluate(az,el,best['distance_m']+step*.5))
    rank.sort(key=lambda x:-x['silhouette_iou']);best=rank[0];m=mask(points,tris,best['azimuth'],best['elevation'],bounds,t.width,t.height,best['distance_m'])
    overlay=bytearray()
    for a,b in zip(m,reference):overlay.extend((235,235,235,255) if a and b else (255,80,70,255) if a else (60,150,255,255) if b else (45,50,56,255))
    (out/'silhouette-fit.png').write_bytes(gtmat.png_from_rgba(t.width,t.height,overlay))
    import hashlib
    result={'reference_model':str(family),'reference_frame':str(frame),'model_sha256':hashlib.sha256((family/'complete.dx').read_bytes()).hexdigest(),'frame_sha256':hashlib.sha256(frame.read_bytes()).hexdigest(),'alpha_threshold':128,'method':'width-normalized projected triangle silhouette; azimuth/elevation/distance IoU fit; no native camera claim','target_bounds':bounds,'best':best,'orthographic_best':max((r for r in rank if r['distance_m'] is None),key=lambda x:x['silhouette_iou']),'top':rank[:12]};(out/'camera-fit.json').write_text(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vehicle-family',type=Path,required=True);p.add_argument('--frame',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(calibrate(a.vehicle_family,a.frame,a.output),indent=2))
