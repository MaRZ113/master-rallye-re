"""4x4 Evo 2 procedural suspension, rebuilt as static geometry (rest pose).

Reverse-engineered from 4x42.exe (PC, sha256 ab8286e6...; Ghidra 12.1.4):
* FUN_005f7820 (truck draw) calls the full-detail builder FUN_005fdad0 + drawer FUN_006006d0 when
  the suspension detail setting is high and the truck is not "bigfoot"; otherwise the simplified
  FUN_005ff4d0 / FUN_00600eb0 / FUN_00601510 path. Axle beams are the SMF objects AxleF/AxleR,
  drawn with the axle transform (rest pose = their modelled position).
* FUN_005fdad0(truck, frontAxle(xyz), cos, sin, rearAxle(xyz), cos, sin) fills a point table
  (12-byte points at 0xd651c0; front indices 0.., rear indices +48). Truck fields: frontSuspType
  +0x12a4, rearSuspType +0x12a8, frontSuspSpringType +0x12ac, rearSuspSpringType +0x12b0;
  right tyre x +0x90, y +0x94, tyre width +0xd4 (front) / x +0x348, y +0x34c, width +0x38c (rear).
* FUN_006006d0 draws: FUN_005ffc00(a, b) = camera-facing ribbon a->b of half-width W (0xd6574c)
  with a UV rect (0xd6564c, tables set by FUN_005fd690 in SUSP.RAW quadrants);
  FUN_00600110(a, b, c, d) = two-sided quad (leaf spring) with one fixed texel (1/64, 63/64).

Constants (feet): arm rods W=0.11, arm edges W=0.13, shocks W=0.12, driveshaft W=0.14; chassis
pivot x=+-1.0, y=tyre y+0.8; wheel box +-0.15; chassis box z+-0.32, y -0.032/+0.48; shock top
(+-1.4, 1.0, z) [rear z+0.6], bottom (+-1.7, axle y+0.07, z-+0.15); leaf at x 1.4+-0.18,
z -1.7..+1.7 step 0.85, y 0.4 / 0.6*(Ay-0.12) / Ay-0.12; driveshaft (0,0.2,1.0) -> (0, rear y,
rear z+0.2) only for a solid rear axle. Coil/torsion spring types draw nothing.

Here the camera-facing ribbons become 6-sided tubes of radius W (static MR geometry).
"""
from __future__ import annotations
import math

SIDES=6
UV={'rod':(1/64,31/64,1/64,31/64),'edge':(33/64,63/64,1/64,31/64),'shock':(33/64,63/64,33/64,63/64)}
LEAF_UV=(1/64,63/64)


def _tube(a,b,r,uv,out):
    d=[b[i]-a[i]for i in range(3)];l=math.sqrt(sum(t*t for t in d))
    if l<1e-6:return
    d=[t/l for t in d];h=[0,1,0]if abs(d[1])<.9 else[1,0,0]
    u=[d[1]*h[2]-d[2]*h[1],d[2]*h[0]-d[0]*h[2],d[0]*h[1]-d[1]*h[0]];ul=math.sqrt(sum(t*t for t in u));u=[t/ul for t in u]
    v=[d[1]*u[2]-d[2]*u[1],d[2]*u[0]-d[0]*u[2],d[0]*u[1]-d[1]*u[0]]
    u0,u1,v0,v1=uv;P,N,T,U=out;base=len(P)
    for k in range(SIDES+1):
        ang=2*math.pi*k/SIDES;n=[math.cos(ang)*u[i]+math.sin(ang)*v[i]for i in range(3)]
        t=abs((k/SIDES)*2-1)   # ping-pong across the strip: the source texture is a lit half-cylinder
        uu=u0+(u1-u0)*t
        for p,vv in((a,v0),(b,v1)):
            P.append([p[i]+r*n[i]for i in range(3)]);N.append(n);U.append([uu,vv])
    for k in range(SIDES):
        i=base+2*k;T.extend([[i,i+2,i+1],[i+1,i+2,i+3]])


def _quad(a,b,c,d,out):
    P,N,T,U=out
    for normal,order in(((0,-1,0),(0,1,2,3)),((0,1,0),(0,3,2,1))):
        base=len(P)
        for q in(a,b,c,d):P.append(list(q));N.append(list(normal));U.append(list(LEAF_UV))
        o=[base+k for k in order];T.extend([[o[0],o[1],o[2]],[o[0],o[2],o[3]]])


def build(trk:dict,tyre_width:dict)->dict:
    """trk: parsed TRK (wheel_positions, susp types). tyre_width: {'front': ft, 'rear': ft}.
    Returns {group: (positions, normals, triangles, uvs)} in the SMF body frame (feet)."""
    wp=trk['wheel_positions'];groups={}
    def g(name):
        if name not in groups:groups[name]=([],[],[],[])
        return groups[name]
    st={'front':int(trk['frontSuspType']),'rear':int(trk['rearSuspType'])}
    sp={'front':int(trk['frontSuspSpringType']),'rear':int(trk['rearSuspSpringType'])}
    for axle,key,sign in(('front','faxle.rtire',-1),('rear','raxle.rtire',1)):
        tx,ty,tz=wp[key];Ay=ty;Az=tz
        if st[axle]==0:
            f=tx-tyre_width[axle]*.5
            for s in(1,-1):
                w=[s*f,Ay,Az];c=[s*1.0,ty+.8,Az]
                _tube(c,w,.11,UV['rod'],g('arm_rods'))
                wbox=[[w[0],w[1]-.15,w[2]-.15],[w[0],w[1]-.15,w[2]+.15],[w[0],w[1]+.15,w[2]+.15],[w[0],w[1]+.15,w[2]-.15]]
                cbox=[[c[0],c[1]-.032,c[2]-.32],[c[0],c[1]-.032,c[2]+.32],[c[0],c[1]+.48,c[2]+.32],[c[0],c[1]+.48,c[2]-.32]]
                for p,q in zip(cbox,wbox):_tube(p,q,.13,UV['edge'],g('arm_edges'))
        top_z=Az if axle=='front'else Az+.6
        for s in(1,-1):
            _tube([s*1.4,1.0,top_z],[s*1.7,Ay+.07,Az+sign*.15],.12,UV['shock'],g('shocks'))
        if sp[axle]==2:
            ys=[.4,.6*(Ay-.12),Ay-.12,.6*(Ay-.12),.4];zs=[Az-1.7+.85*k for k in range(5)]
            for s in(1,-1):
                outer=[[s*1.58,y,z]for y,z in zip(ys,zs)];inner=[[s*1.22,y,z]for y,z in zip(ys,zs)]
                for k in range(4):_quad(outer[k],inner[k],inner[k+1],outer[k+1],g('leaf_springs'))
    if st['rear']==1:
        rx,ry,rz=wp['raxle.rtire'];_tube([0,.2,1.0],[0,ry,rz+.2],.14,UV['shock'],g('driveshaft'))
    return groups
