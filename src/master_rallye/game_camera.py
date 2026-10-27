"""Native-informed static follow framing, explicitly separate from dynamics.

The flat first-update rule is checked against original 0052C6D0 instructions.
No terrain, velocity, interpolation or acceleration-helper simulation is claimed.
"""
import math,xml.etree.ElementTree as ET

# 004B8170 cycles [manager+1E0, manager+1DC] using XML counts 3/2.
GAMEPLAY_MODES=tuple({'id':i,'kind':'follow' if i<3 else 'fixed',
    'index':i if i<3 else i-3,'label':f'{i+1}: '+('Follow '+str(i) if i<3 else 'Fixed '+str(i-3)),
    'constructor':'0052C310' if i<3 else '0052BC30',
    'native_editable':('FOV','Dist Front','Dist Back','Dist Up') if i<3 else ('FOV',)}for i in range(5))


def gameplay_mode(mode):
    if type(mode)is not int or not 0<=mode<5:raise ValueError('Unknown native gameplay mode')
    return dict(GAMEPLAY_MODES[mode])


def fixed_preset(raw,index=0,split=False):
    if type(index)is not int or index not in (0,1)or type(split)is not bool:raise ValueError('Unsupported fixed preset')
    rows=camera_settings(raw)['Camera/SplitSetup'if split else'Camera/Setup'];prefix=f'FixedCamera {index}  '
    values={k[len(prefix):]:v for k,v in rows.items()if k.startswith(prefix)}
    required={'Type','Dist forward/back','Dist up/down','Dist right/left','InvertLook','FlattenDir','FOV'}
    if set(values)!=required:raise ValueError('Unqualified fixed camera layout')
    out={}
    for name,row in values.items():
        expected='Bool'if name in ('InvertLook','FlattenDir')else'Int'if name=='Type'else'Float'
        if row['type']!=expected:raise ValueError('Unqualified fixed field type')
        if expected=='Bool':
            if row['value']not in ('True','False'):raise ValueError('Invalid fixed flag')
            out[name]=row['value']=='True'
        else:
            out[name]=(int if expected=='Int'else float)(row['value'])
            if not math.isfinite(out[name]):raise ValueError('Nonfinite fixed field')
    if out['Type']not in (0,1):raise ValueError('Unsupported source fixed type')
    return out


def vertical_fov(fov,width,height):
    if any(type(v)not in (int,float)or not math.isfinite(v)or v<=0 for v in (fov,width,height))or not 1<fov<179:raise ValueError('Invalid projection input')
    # ORIGINAL 004F2350: stored degrees * min(1, viewportHeight/viewportWidth).
    return fov*min(1.,height/width)


def fixed_pose(bounds,parameters,position=(0.,0.,0.),yaw_degrees=0.):
    lo,hi=bounds['minimum'],bounds['maximum']
    if len(lo)!=3 or len(hi)!=3 or any(not math.isfinite(v)for v in (*lo,*hi))or any(a>=b for a,b in zip(lo,hi)):raise ValueError('Invalid camera model bounds')
    if len(position)!=3 or any(not math.isfinite(v)for v in position)or not math.isfinite(yaw_degrees):raise ValueError('Invalid fixed target frame')
    kind=parameters['Type'];forward=(hi[2]-lo[2])*.5-.12
    up=hi[1]-(hi[1]-lo[1])*.05 if kind==0 else (hi[1]-lo[1])*.25
    a=math.radians(yaw_degrees);direction=(math.sin(a),0.,math.cos(a))
    eye=[position[i]+direction[i]*forward for i in range(3)];eye[1]+=up
    return {'eye':eye,'target':[eye[i]+direction[i]for i in range(3)],'up':[0.,1.,0.],
        'source_fov_degrees':parameters['FOV'],'scenario':'Native fixed type0/1 bounds initializer; flat upright target',
        'pose_evidence':'0052BEC0 / 0052C090; source XML offsets are replaced by native bounds initialization.',
        'projection_evidence':'004F2350 aspect rule; D3D9 fixed-function preview, D3D8 presentation pending owner'}


def camera_settings(raw):
    if len(raw)>1024*1024 or b'<!'in raw:raise ValueError('bounded plain Cameras XML required')
    root=ET.fromstring(raw);records={}
    for value in root.findall('./Broker/Value'):
        name=value.get('Name')
        if name not in ('Camera/Setup','Camera/SplitSetup'):continue
        if name in records:raise ValueError('duplicate camera setup')
        entries=value.findall('./gaCameraManagerParams/Value')
        if len({v.get('Name')for v in entries})!=len(entries):raise ValueError('duplicate camera setting')
        records[name]={v.get('Name'):{'type':v.get('Type'),'value':v.get('Value')}for v in entries}
    if not records:raise ValueError('native camera setups absent')
    return records


def follow_preset(raw,index=0,split=False):
    if type(index)is not int or index not in (0,1,2)or type(split)is not bool:raise ValueError('Unsupported native follow preset')
    rows=camera_settings(raw)['Camera/SplitSetup'if split else'Camera/Setup'];prefix=f'FollowCamera {index}  '
    values={k[len(prefix):]:v for k,v in rows.items()if k.startswith(prefix)}
    required={'Dist Front','Dist Back','Dist Up','FOV','Smooth Camera Multi','Body Dir Multi','UsePitchSystem','Pitch Limit deg','Min Rot deg','Max Rot deg','Accel'}
    if set(values)!=required:raise ValueError('Unqualified native follow parameter layout')
    out={}
    for name,row in values.items():
        expected='Bool'if name in ('UsePitchSystem','Accel')else'Float'
        if row['type']!=expected:raise ValueError('Unqualified native camera field type')
        if row['type']=='Bool':
            if row['value']not in ('True','False'):raise ValueError('Invalid native camera flag')
            out[name]=row['value']=='True'
        elif row['type']=='Float':
            out[name]=float(row['value'])
            if not math.isfinite(out[name]):raise ValueError('Nonfinite native camera value')
        else:raise ValueError('Unqualified native camera type')
    return out


def static_pose(extents,parameters,position=(0.,0.,0.),yaw_degrees=0.):
    if set(extents)!={'half_length_m','height_m'}or any(type(v)not in (int,float)or not math.isfinite(v)or not 0<v<=20 for v in extents.values()):raise ValueError('Qualified finite follow extents required')
    if len(position)!=3 or any(type(v)not in (int,float)or not math.isfinite(v)or abs(v)>10000 for v in position)or type(yaw_degrees)not in (int,float)or not math.isfinite(yaw_degrees):raise ValueError('Invalid static camera transform')
    front,back,up,fov=[parameters[k]for k in ('Dist Front','Dist Back','Dist Up','FOV')]
    if any(type(v)not in (float,int)or not math.isfinite(v)for v in (front,back,up,fov))or any(abs(v)>100 for v in (front,back,up))or not 1<fov<179:raise ValueError('Invalid source camera parameters')
    a=math.radians(yaw_degrees);direction=(math.sin(a),0.,math.cos(a));distance=back+extents['half_length_m']
    eye=[position[i]-direction[i]*distance for i in range(3)];eye[1]+=up+extents['height_m']
    target=[position[i]+direction[i]*front for i in range(3)]
    if sum((a-b)**2 for a,b in zip(eye,target))<1e-8:raise ValueError('Degenerate static camera pose')
    return {'eye':eye,'target':target,'up':[0.,1.,0.],'source_fov_degrees':fov,'scenario':'Static first update, flat upright target; no acceleration, terrain or smoothing history','pose_evidence':'Original x86 first-update replay under controlled source structures; pitch-disabled flat rule. Follow1 pitch dynamics are NOT simulated.','projection_evidence':'D3D9 preview projection / source FOV value; final D3D8 presentation remains unqualified'}
