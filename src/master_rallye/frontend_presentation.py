"""Retail VehicleSelect presentation, separate from gameplay and icon cameras.

Source: immutable VehicleSelect.xml and aiStaticCamera 0052A6D0. Offsets
change the private look target only. No mesh, bounds or physics translation.
"""
import hashlib,math,re,struct

XML_SHA256='ec7fd6372fe5008b1039eb8e09890ef3b37396dad1581568af439cbb611b58e1'
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
EYE=tuple(map(f32,(10.,-1.,200.30)))
TARGET=(f32(f32(8.)+f32(-1.22)),f32(f32(-2.)+f32(2.18)),f32(189.))

def validate_offset(v):
    if type(v)not in(int,float)or not math.isfinite(v)or not -1.5<=v<=1.5:raise ValueError('Frontend offset outside SDK safety range [-1.5,1.5] m')
    return v

def validate_profile(p):
    if not isinstance(p,dict)or set(p)!={'version','car_id','runtime_family','source_model_sha256','vertical_offset_m'}:raise ValueError('Unsupported frontend profile')
    if type(p['version'])is not int or p['version']!=1 or type(p['car_id'])is not int or not 1<=p['car_id']<=29:raise ValueError('Unsupported frontend version/identity')
    if not isinstance(p['runtime_family'],str)or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,62}',p['runtime_family']):raise ValueError('Invalid frontend family')
    if not isinstance(p['source_model_sha256'],str)or not re.fullmatch('[0-9a-f]{64}',p['source_model_sha256']):raise ValueError('Invalid frontend source hash')
    validate_offset(p['vertical_offset_m'])
    return p

def bind_profile(p,raw):
    from .dx import parse_dx_bytes
    from .bounds import parse_bounds1339
    from .addon_sdk.vehicle_shadow import runtime_bounds
    validate_profile(p)
    if hashlib.sha256(raw).hexdigest()!=p['source_model_sha256']:raise ValueError('Frontend complete.dx source changed')
    m=parse_dx_bytes(raw);b=parse_bounds1339(m.collision.unparsed_data)
    if not m.diagnostics.validated or b is None:raise ValueError('Unqualified frontend bounds')
    return {'profile':p,'model_resource':'vehicles/'+p['runtime_family'].lower()+'/complete','native_bounds_values_hex':runtime_bounds(b.raw).hex()}

def pose(offset=0.):
    """Scene-relative camera; preview applies original CarModel matrix exactly."""
    validate_offset(offset)
    def relative(p):return [p[0]-8,p[1]+2,p[2]-189]
    target=list(TARGET);target[1]=f32(target[1]-offset)
    return {'eye':relative(EYE),'target':relative(target),'source_fov_degrees':45.}

def scene_transform(v,position=False):
    a,b=f32(.89),f32(.45);x,y,z=v;out=(a*x-b*z,y,b*x+a*z)
    if not position:
        # Inverse transpose for original XZ scale, followed by normalization.
        d=a*a+b*b;out=(out[0]/d,y,out[2]/d);n=math.sqrt(sum(t*t for t in out));out=tuple(t/n for t in out)if n else(0.,1.,0.)
    return out

def measure(raw,offset=0.,aspect=4/3):
    """Used draw vertices, not collision box. NDC extents include all source draws."""
    from .dx import parse_dx_bytes
    from .topology_writer import source_geometry
    from .workshop.camera_live import projected_bounds
    if type(aspect)not in(int,float)or not math.isfinite(aspect)or not .5<=aspect<=4:raise ValueError('Unsupported frontend inspection aspect')
    if len(raw)>128*1024*1024:raise ValueError('Frontend inspection byte budget exceeded')
    model=parse_dx_bytes(raw);points=[]
    for g in source_geometry(model).values():
        used={i for tri in g.triangles for i in tri}
        if len(points)+len(used)>100000:raise ValueError('Frontend inspection vertex budget exceeded')
        points.extend(scene_transform(g.vertices[i].position,True)for i in used)
    if not points:raise ValueError('Empty complete model')
    if not all(math.isfinite(v)for p in points for v in p):raise ValueError('Nonfinite frontend geometry')
    bounds={'minimum':[min(p[k]for p in points)for k in range(3)],'maximum':[max(p[k]for p in points)for k in range(3)]}
    # Degenerate AABBs project individual vertices through the same arithmetic.
    projected=[projected_bounds(pose(offset),{'minimum':p,'maximum':p},aspect)for p in points]
    if any(p is None for p in projected):raise ValueError('Frontend geometry behind camera')
    lo=[min(p['minimum'][k]for p in projected)for k in (0,1)];hi=[max(p['maximum'][k]for p in projected)for k in (0,1)]
    return {'geometry_bounds':bounds,'ndc':{'minimum':lo,'maximum':hi},'bottom_ndc':lo[1],'clipped':any(abs(v)>1 for v in lo+hi),'vertices':len(points),'aspect':aspect,'offset_m':offset,'wheel_baseline':'lowest used geometry; wheel-only ownership is not inferred'}

def auto_frame(raw,reference,aspect=4/3):
    """Match a stock reference's lower visible geometry baseline, not scale."""
    target=measure(reference,0.,aspect)['bottom_ndc'];lo,hi=-1.5,1.5
    for _ in range(24):
        mid=(lo+hi)/2
        if measure(raw,mid,aspect)['bottom_ndc']<target:lo=mid
        else:hi=mid
    value=round((lo+hi)/2,6);report=measure(raw,value,aspect)
    if abs(report['bottom_ndc']-target)>.002 or report['clipped']:raise ValueError('Reference baseline cannot be matched safely with vertical-only framing')
    return value

def wheel_baseline(resources):
    """Use the existing exact repeated-wheel proof, never infer wheel ownership."""
    from .dx import parse_dx_bytes
    from .preview_scene import presentation_wheels,preview_transform
    car,complete,wheel=[parse_dx_bytes(resources[n])for n in('car.dx','complete.dx','wheel.dx')]
    proof=presentation_wheels(car,complete,wheel,diagnostics=True);delta=proof['body_translation'];points=[]
    used={v for d in wheel.physical_draws for v in wheel.draw_global_indices(d)}
    for inst in proof['race_wheel_instances']:
        vec,_=preview_transform(inst);points.extend(vec(wheel.vertices.positions[i],True)[1]+delta[1]for i in used)
    return {'minimum_y_m':min(points),'provenance':proof['provenance'],'body_translation':delta,'boundary':'Source frontend rest pose only; not suspension travel or gameplay ground contact'}
