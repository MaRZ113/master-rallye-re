"""Diagnostic ground plane / alpha-support guides, never runtime geometry."""
import math
import struct


def shadow_guides(report, ground_y):
    keys = ('body_bounds_xz_m','native_alpha_support_xz_m','generated_alpha_support_xz_m')
    if set(report) != set(keys)|{'mode','evidence','preview'}:
        raise ValueError('Unknown shadow diagnostic fields')
    for key in keys:
        b=report[key]
        if len(b)!=2 or any(len(row)!=2 for row in b) or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>100 for row in b for v in row) or any(b[1][k]<=b[0][k] for k in range(2)):
            raise ValueError('Invalid shadow diagnostic rectangle')
    output=[]
    def strip(name,a,b,width,color):
        dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz)
        nx,nz=-dz/length*width/2,dx/length*width/2
        positions=[(a[0]+nx,ground_y,a[1]+nz),(a[0]-nx,ground_y,a[1]-nz),(b[0]+nx,ground_y,b[1]+nz),(b[0]-nx,ground_y,b[1]-nz)]
        vertices=b''.join(struct.pack('<6f4s2f',*p,0.,1.,0.,color,0.,0.) for p in positions)
        output.append((name,1,-1,-1,0,0,0,0,[(a[0]+b[0])/2,ground_y,(a[1]+b[1])/2],vertices,[0,1,2,2,1,3]))
    span=max(abs(v) for key in keys for row in report[key] for v in row)+.5
    for n in range(-math.ceil(span),math.ceil(span)+1):
        strip('ground:shadow-grid',(n,-span),(n,span),.006,b'\x47\x43\x3c\xff')
        strip('ground:shadow-grid',(-span,n),(span,n),.006,b'\x47\x43\x3c\xff')
    for key,color in zip(keys,(b'\x40\xb0\xff\xff',b'\x50\x50\xee\xff',b'\x70\xee\x60\xff')):
        (x0,z0),(x1,z1)=report[key];points=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
        for i in range(4):strip('diagnostic:shadow:'+key,points[i],points[(i+1)%4],.018,color)
    return output
