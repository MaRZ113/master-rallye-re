"""Illustrative camera markers/frusta for free inspection, never game geometry."""
import math,struct


def camera_guides(report,ground=-.02):
    if set(report)!={'original','modified'}:raise ValueError('Invalid camera guide roles')
    output=[]
    def line(name,a,b,color):
        delta=[b[i]-a[i]for i in range(3)];length=math.sqrt(sum(v*v for v in delta))
        if length<1e-7:return
        normal=[-delta[2],0,delta[0]];norm=math.hypot(normal[0],normal[2])
        if norm<1e-7:normal=[.02,0,0]
        else:normal=[v*.012/norm for v in normal]
        points=[[p[i]+sign*normal[i]for i in range(3)]for p,sign in [(a,1),(a,-1),(b,1),(b,-1)]]
        vertices=b''.join(struct.pack('<6f4s2f',*p,0,1,0,color,0,0)for p in points)
        output.append(('diagnostic:camera:'+name,1,-1,-1,0,0,0,0,[(a[i]+b[i])/2 for i in range(3)],vertices,[0,1,2,2,1,3,2,1,0,3,1,2]))
    for role,color in [('original',b'\x60\x60\xee\xff'),('modified',b'\x70\xee\x60\xff')]:
        pose=report[role]
        if set(pose)!={'eye','target','source_fov_degrees'}or any(not isinstance(pose[k],list)or len(pose[k])!=3 or any(type(v)not in(int,float)or not math.isfinite(v)or abs(v)>200 for v in pose[k])for k in ('eye','target')):raise ValueError('Invalid camera guide points')
        fov=pose['source_fov_degrees']
        if type(fov)not in (float,int)or not math.isfinite(fov)or not 1<fov<179:raise ValueError('Invalid camera source FOV')
        eye,target=pose['eye'],pose['target'];forward=[target[i]-eye[i]for i in range(3)];length=math.sqrt(sum(v*v for v in forward))
        if length<1e-7:raise ValueError('Camera guide eye equals target')
        forward=[v/length for v in forward];right=[forward[2],0,-forward[0]];n=math.hypot(right[0],right[2])
        if n<1e-7:raise ValueError('Vertical camera guide unsupported')
        right=[v/n for v in right];up=[right[1]*forward[2]-right[2]*forward[1],right[2]*forward[0]-right[0]*forward[2],right[0]*forward[1]-right[1]*forward[0]]
        line(role+':aim',eye,target,color)
        for point,key in [(eye,'eye'),(target,'target')]:
            for axis in range(3):
                a=list(point);b=list(point);a[axis]-=.12;b[axis]+=.12;line(role+':'+key,a,b,color)
        # Preview aspect1.5 and range1.5m are diagnostic choices, not native clips.
        height=math.tan(math.radians(fov/1.5)/2)*1.5;width=height*1.5
        corners=[[eye[i]+forward[i]*1.5+right[i]*sx*width+up[i]*sy*height for i in range(3)]for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        for i,p in enumerate(corners):line(role+':frustum',eye,p,color);line(role+':frustum',p,corners[(i+1)%4],color)
    if not math.isfinite(ground)or abs(ground)>200:raise ValueError('Invalid illustrative ground height')
    floor=b''.join(struct.pack('<6f4s2f',x,ground-.005,z,0,1,0,b'\x61\x5b\x56\xff',0,0)for x,z in [(-80,-80),(-80,80),(80,80),(80,-80)])
    output.append(('diagnostic:camera:floor',1,-1,-1,0,0,0,0,[0,ground,0],floor,[0,1,2,0,2,3,2,1,0,3,2,0]))
    for x in range(-20,21):line('ground',[x,ground,-20],[x,ground,60],b'\xa0\x98\x88\xff')
    for z in range(-20,61):line('ground',[-20,ground,z],[20,ground,z],b'\xa0\x98\x88\xff')
    return output
