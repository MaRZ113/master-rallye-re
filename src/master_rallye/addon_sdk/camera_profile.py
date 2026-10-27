"""Camera-only extent calibration contract. Runtime adapter is intentionally gated."""
import math


def validate_mode_fields(mode,fields):
    if mode not in ('follow0','follow1','follow2','fixed0','fixed1'):raise ValueError('Unsupported camera mode override')
    limits={'FOV':(20.,140.)}
    if mode.startswith('follow'):limits.update({'Dist Front':(.1,50.),'Dist Back':(.1,30.),'Dist Up':(-5.,10.)})
    if not isinstance(fields,dict)or not fields or set(fields)-set(limits):raise ValueError('Unsupported camera parameter override')
    for name,value in fields.items():
        if type(value)not in (int,float)or not math.isfinite(value)or not limits[name][0]<=value<=limits[name][1]:raise ValueError('Camera parameter outside SDK authoring safety bounds')
    return fields

def validate_camera_profile(profile):
    if set(profile)!={'version','car_id','policy','follow_extents'}: raise ValueError('unknown/missing camera profile fields')
    if profile['version']!=1 or type(profile['car_id']) is not int or not 0<=profile['car_id']<=29: raise ValueError('unsupported version/CarID')
    if profile['policy']!='diagnostic_only': raise ValueError('runtime per-CarID camera owner binding is not qualified')
    ext=profile['follow_extents']
    if set(ext)!={'half_length_m','height_m'}: raise ValueError('unsupported camera fields')
    for v in ext.values():
        if type(v) not in (int,float) or not math.isfinite(v) or not 0<v<=20: raise ValueError('camera extents outside SDK diagnostic bounds')
    return profile

def camera_extent_comparison(profile,car_id,native_half_length,native_height):
    validate_camera_profile(profile)
    # This dispatch models profile isolation only; it never writes engine memory.
    selected=(profile['follow_extents']['half_length_m'],profile['follow_extents']['height_m']) if car_id==profile['car_id'] else (native_half_length,native_height)
    return {'car_id':car_id,'native':[native_half_length,native_height],'diagnostic':list(selected),'runtime_override_installed':False}


def bind_camera_profile(profile, model_data):
    """Bind an explicit experimental follow-only calibration to immutable DX."""
    import hashlib,re,struct
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.bounds import parse_bounds1339
    from .vehicle_shadow import runtime_bounds
    required={'version','car_id','policy','runtime_family','source_model_sha256','follow_extents'}
    if set(profile)-{'mode_overrides'}!=required or type(profile['version']) is not int or profile['version']!=1 or profile['policy']!='native_follow_extents':raise ValueError('unsupported native camera profile')
    modes=profile.get('mode_overrides',{})
    if not isinstance(modes,dict)or set(modes)-{'follow0','follow1','follow2','fixed0','fixed1'}:raise ValueError('Unsupported camera mode override')
    for mode,fields in modes.items():
        validate_mode_fields(mode,fields)
    if profile['car_id']==0:raise ValueError('CarID0 camera override requires separate missing-key qualification')
    family=profile['runtime_family']
    if not isinstance(family,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,62}',family):raise ValueError('invalid camera runtime family')
    validate_camera_profile({k:('diagnostic_only' if k=='policy' else v) for k,v in profile.items() if k not in ('runtime_family','source_model_sha256','mode_overrides')})
    if hashlib.sha256(model_data).hexdigest()!=profile['source_model_sha256']:raise ValueError('camera source model hash mismatch')
    model=parse_dx_bytes(model_data)
    if not model.diagnostics.validated:raise ValueError('camera source model invalid')
    bounds=parse_bounds1339(model.collision.unparsed_data)
    if bounds is None:raise ValueError('camera source has no qualified bounds')
    original=runtime_bounds(bounds.raw);replacement=bytearray(original)
    for axis,span in ((1,profile['follow_extents']['height_m']),(2,profile['follow_extents']['half_length_m']*2)):
        center=(bounds.minimum[axis]+bounds.maximum[axis])/2
        struct.pack_into('<f',replacement,0x14+4*axis,center-span/2)
        struct.pack_into('<f',replacement,0x20+4*axis,center+span/2)
    return {'car_id':profile['car_id'],'model_resource':'vehicles/'+family.lower()+'/car','native_bounds_values_hex':original.hex(),'camera_bounds_hex':replacement.hex(),'profile':profile}
