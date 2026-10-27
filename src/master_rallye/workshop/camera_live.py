"""Bounded owned-Previewer IPC; no game process or project writes."""
import ctypes,math,struct
from ctypes import wintypes

MAGIC=0x32434d52


def projected_bounds(pose,bounds,aspect):
    """NDC envelope of eight staged vehicle AABB corners, no diagnostic floor."""
    from itertools import product
    from master_rallye.game_camera import vertical_fov
    e,t=pose['eye'],pose['target'];f=[b-a for a,b in zip(e,t)];n=math.sqrt(sum(v*v for v in f));f=[v/n for v in f]
    r=[-f[2],0.,f[0]];n=math.hypot(r[0],r[2]);r=[v/n for v in r];up=[r[1]*f[2]-r[2]*f[1],r[2]*f[0]-r[0]*f[2],r[0]*f[1]-r[1]*f[0]]
    slope=math.tan(math.radians(vertical_fov(pose['source_fov_degrees'],aspect,1.))/2);out=[]
    for p in product(*zip(bounds['minimum'],bounds['maximum'])):
        d=[a-b for a,b in zip(p,e)];depth=sum(a*b for a,b in zip(d,f))
        if depth<=.001:return None
        out.append([sum(a*b for a,b in zip(d,r))/(depth*slope*aspect),sum(a*b for a,b in zip(d,up))/(depth*slope)])
    return {'minimum':[min(p[k]for p in out)for k in (0,1)],'maximum':[max(p[k]for p in out)for k in (0,1)]}


def fit_follow_draft(report,fields,aspect=16/9):
    """Explicit unsaved framing correction using supported Follow parameters.

    Source/Original is never changed. Retain height, prefer existing distance,
    and reduce forward look distance only as needed to keep the full staged car.
    """
    if report['mode']['kind']!='follow':raise ValueError('Vehicle framing applies to Follow views only')
    bounds=report.get('preview_bounds',{'minimum':report['identity']['minimum'],'maximum':report['identity']['maximum']})
    for back in [fields['Dist Back']+i*.25 for i in range(121)if fields['Dist Back']+i*.25<=30]:
        best=None
        for j in range(121):
            front=.1+(fields['Dist Front']-.1)*(120-j)/120;candidate={**fields,'Dist Front':front,'Dist Back':back}
            envelope=projected_bounds(draft_pose(report,candidate),bounds,aspect)
            if envelope and max(abs(v)for pair in envelope.values()for v in pair)<=.9:
                best=candidate;break
        if best is not None:return best
    raise ValueError('Cannot frame vehicle within qualified camera bounds; use free inspection')


def draft_pose(report,fields,view='modified'):
    import copy
    from master_rallye.game_camera import static_pose
    allowed=report['mode']['native_editable']
    if set(fields)!=set(allowed):raise ValueError('Draft fields differ from native editable scope')
    from master_rallye.addon_sdk.camera_profile import validate_mode_fields
    validate_mode_fields(report['mode']['kind']+str(report['mode']['index']),fields)
    params={**report['parameters'][view],**fields}
    if report['mode']['kind']=='follow':
        baseline=report['poses'][view];source=report['parameters'][view]
        ext={'half_length_m':-baseline['eye'][2]-source['Dist Back'],'height_m':baseline['eye'][1]-source['Dist Up']}
        pose=static_pose(ext,params)
    else:pose=copy.deepcopy(report['poses'][view]);pose['source_fov_degrees']=fields['FOV']
    packet(pose,mode=report['mode']['id'])
    return pose


def packet(pose,*,mode=0,revision=0,aspect=0.,capture=False,editable=True):
    from master_rallye.game_camera import gameplay_mode
    gameplay_mode(mode)
    values=[*pose['eye'],*pose['target'],pose['source_fov_degrees'],aspect]
    if len(values)!=8 or any(type(v)not in (float,int)or not math.isfinite(v)for v in values)or any(abs(v)>200 for v in values[:6])or not 20<=values[6]<=140 or not(aspect==0 or .5<=aspect<=4):raise ValueError('Invalid live camera packet')
    if sum((a-b)**2 for a,b in zip(values[:3],values[3:6]))<1e-6 or math.hypot(values[0]-values[3],values[2]-values[5])<1e-6:raise ValueError('Degenerate live camera pose')
    if type(revision)is not int or not 0<=revision<2**32:raise ValueError('Invalid camera revision')
    return struct.pack('<4I8f',1,(2 if capture else 1)+(0 if editable else 2),mode,revision,*values)


def owned_window(process):
    if process is None or process.poll()is not None:return None
    user=ctypes.windll.user32;windows=[]
    callback=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def enum(hwnd,lparam):
        pid=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value==process.pid and user.IsWindowVisible(hwnd):windows.append(hwnd)
        return True
    user.EnumWindows(callback(enum),0);return windows[0]if windows else None


def send(process,payload):
    hwnd=owned_window(process)
    if not hwnd:return False
    class CopyData(ctypes.Structure):_fields_=[('tag',ctypes.c_size_t),('size',wintypes.DWORD),('data',ctypes.c_void_p)]
    buf=ctypes.create_string_buffer(payload);msg=CopyData(MAGIC,len(payload),ctypes.cast(buf,ctypes.c_void_p))
    result=ctypes.c_size_t();user=ctypes.windll.user32
    user.SendMessageTimeoutW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM,wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)]
    user.SendMessageTimeoutW.restype=ctypes.c_size_t
    return bool(user.SendMessageTimeoutW(hwnd,0x4a,0,ctypes.addressof(msg),0x2,200,ctypes.byref(result))and result.value==1)
