"""Typed, family-scoped physics edits over immutable retail Broker templates.

This authors initialization data, not live writes or a replacement solver.
Limits below are SDK authoring guards, not claimed native engine limits.
"""
from __future__ import annotations
import hashlib,json,math,re,struct
import xml.etree.ElementTree as ET
from .manifest import AddonValidationError,canonical_json
from .physics import clone_vehicle_family_xml
from ..vehicle_config_analysis import parse_vehicle_config_bytes
from ..vehicle_config_schema import analyze_vehicle_base_schema
from ..vehicle_family_broker import PLAYER_MODIFICATION_FIELDS

MEMBERS=('DataGame/vehicles.xml','DataGame/Modifications.xml')
FAMILY=re.compile(r'^[A-Za-z][A-Za-z0-9_]{1,39}$')
POSITIVE={'Chassis/TotalMass','Chassis/Gravity','Engine/DriveShaftInertia','Engine/EngineInertia','Engine/RevLimit','Engine/IdleRevs','Engine/MaxClutchTorque'}
NONNEGATIVE={'Chassis/BrakeTorqueFront','Chassis/BrakeTorqueRear','Chassis/HandBrakeTorque','Engine/PeakTorque','Engine/ClutchSwitchTime','Engine/EngineDamping','Engine/LiftOffEngineDamping'}
for axle in ('Front','Rear'):
    POSITIVE.update('Suspension/'+axle+'/'+k for k in ('UnsprungMass','WheelMOI','SpringRate','SpringArmRatio','DamperArmRatio'))
    NONNEGATIVE.update('Suspension/'+axle+'/'+k for k in ('DamperRate','MaxBounce','MaxDroop','WheelDamping','WaterDamping'))

def validate_profile(profile,*,donor_family,runtime_family):
    required={'profile_version','donor_family','runtime_family','source_sha256','overrides','notes'}
    if not isinstance(profile,dict) or not required<=set(profile) or set(profile)-required-{'ride_height_reference_m','ride_height_reference_binding','collision_fit'}:raise AddonValidationError('physics profile keys/version are invalid')
    if type(profile['profile_version']) is not int or profile['profile_version']!=1:raise AddonValidationError('unsupported physics profile version')
    for value in (donor_family,runtime_family):
        if not isinstance(value,str) or not FAMILY.fullmatch(value):raise AddonValidationError('invalid physics family')
    if donor_family.casefold()==runtime_family.casefold() or runtime_family.casefold()=='tyres' or re.fullmatch(r'Car\d+',runtime_family,re.I):raise AddonValidationError('physics target must be an independent named addon family')
    if (profile['donor_family'],profile['runtime_family'])!=(donor_family,runtime_family):raise AddonValidationError('physics profile identity differs from addon/donor')
    pins=profile['source_sha256']
    if not isinstance(pins,dict) or set(pins)!=set(MEMBERS) or any(not isinstance(v,str) or not re.fullmatch('[0-9a-f]{64}',v) for v in pins.values()):raise AddonValidationError('physics profile requires both exact retail member hashes')
    if not isinstance(profile['overrides'],dict) or set(profile['overrides'])-set(MEMBERS):raise AddonValidationError('unsupported physics resource')
    if not isinstance(profile['notes'],str) or len(profile['notes'])>8192:raise AddonValidationError('physics profile notes must be bounded text')
    if 'ride_height_reference_binding' in profile:
        if profile['ride_height_reference_binding']!='registry_name' or 'ride_height_reference_m' not in profile:
            raise AddonValidationError('ride reference binding requires registry_name and an explicit reference')
    if 'ride_height_reference_m' in profile:
        reference=profile['ride_height_reference_m']
        if not isinstance(reference,dict) or set(reference)!={'Front','Rear'}:raise AddonValidationError('ride height reference requires Front and Rear')
        for value in reference.values():
            _number(value)
            if abs(value)>.5:raise AddonValidationError('ride height reference exceeds SDK +/-0.5 m guard')
    if 'collision_fit' in profile:
        c=profile['collision_fit']
        if not isinstance(c,dict) or set(c)!={'source_sha256','core_draw_indices','padding_m','evidence'}:raise AddonValidationError('invalid collision fit declaration')
        if not isinstance(c['source_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',c['source_sha256']):raise AddonValidationError('collision source pin required')
        ids=c['core_draw_indices']
        if not isinstance(ids,list) or not ids or len(ids)>512 or any(type(i) is not int or i<0 or i>8192 for i in ids) or len(set(ids))!=len(ids):raise AddonValidationError('collision core draw selection invalid')
        if not isinstance(c['padding_m'],list) or len(c['padding_m'])!=3:raise AddonValidationError('collision padding must be XYZ')
        for x in c['padding_m']:
            _number(x)
            if not 0<=x<=.1:raise AddonValidationError('collision padding exceeds SDK guard')
        if not isinstance(c['evidence'],str) or not 1<=len(c['evidence'])<=2048:raise AddonValidationError('collision selection evidence required')
    for member,values in profile['overrides'].items():
        if not isinstance(values,dict) or len(values)>512:raise AddonValidationError('physics override map is invalid')
        for path in values:
            if not isinstance(path,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*(?:/[A-Za-z][A-Za-z0-9]*){1,5}',path):raise AddonValidationError('invalid relative physics path')
            if member==MEMBERS[0] and path.split('/')[0] not in ('Dimensions','Chassis','Steering','Engine','Suspension','DamageParams'):raise AddonValidationError('physics path outside vehicle base groups')
            if member==MEMBERS[1] and not re.fullmatch(r'Player[12]/Modifications/(?:Suspension/(?:Front|Rear)/[A-Za-z]+|Engine/[A-Za-z]+)',path):raise AddonValidationError('invalid player setup path')
    return profile

def _number(value):
    if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e9:raise AddonValidationError('physics number must be finite and within SDK bounds')
    try:rounded=struct.unpack('<f',struct.pack('<f',value))[0]
    except (OverflowError,struct.error) as exc:raise AddonValidationError('physics number is not float32') from exc
    if value and not rounded:raise AddonValidationError('physics number underflows float32')
    return format(value,'.9g')

def _encode(value,kind):
    if kind=='Float':return _number(value)
    if kind=='Int':
        if type(value) is not int or not -2147483648<=value<=2147483647:raise AddonValidationError('physics Int outside signed 32-bit range')
        return str(value)
    if kind=='Bool':
        if type(value) is not bool:raise AddonValidationError('physics Bool must be true/false')
        return 'True' if value else 'False'
    if kind in ('Vector2','Vector3'):
        if not isinstance(value,list) or len(value)!=int(kind[-1]):raise AddonValidationError('physics vector arity mismatch')
        return ' '.join(_number(v) for v in value)
    if kind=='String':
        if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,39}',value):raise AddonValidationError('physics string must be a safe existing tyre prefix')
        return value
    raise AddonValidationError('unsupported physics value type '+kind)

def _base_validate(data,family,additions=None):
    doc=parse_vehicle_config_bytes(data,build='retail-2001-verified',source='physics-profile')
    fields=doc.families.get(family,{})
    for path,delta in (additions or {}).items():
        if path not in PLAYER_MODIFICATION_FIELDS or path not in fields:raise AddonValidationError('unsupported effective player setup field')
        fields[path]['value']=_number(float(fields[path]['value'])+delta)
    audit=analyze_vehicle_base_schema(fields)
    if audit.compatibility_class!='COMPATIBLE':raise AddonValidationError('physics family schema is not compatible: '+audit.compatibility_class)
    def f(k):return float(fields[k]['value'])
    for k in POSITIVE:
        if f(k)<=0:raise AddonValidationError(k+' must be positive')
    for k in NONNEGATIVE:
        if f(k)<0:raise AddonValidationError(k+' must be nonnegative')
    for k in fields:
        if k.startswith('Dimensions/') and not 0<f(k)<=20:raise AddonValidationError('dimensions outside SDK (0,20] metre authoring bound')
        if k.endswith('/RideHeight') and abs(f(k))>2:raise AddonValidationError('ride-height origin outside SDK +/-2 m guard')
        if any(k.endswith('/'+n) for n in ('MaxBounce','MaxDroop')) and f(k)>2:raise AddonValidationError('suspension travel exceeds SDK 2 m guard')
    if f('Chassis/TotalMass')<=2*(f('Suspension/Front/UnsprungMass')+f('Suspension/Rear/UnsprungMass')):raise AddonValidationError('nonpositive native sprung mass')
    if any(float(v)<=0 for v in fields['Chassis/MomentOfInertia']['value'].split()):raise AddonValidationError('inertia radius vector must be positive')
    if fields['Engine/DriveType']['value'] not in ('0','1','2'):raise AddonValidationError('unknown native DriveType')
    if not 0<=f('Engine/BrakeBias')<=1:raise AddonValidationError('brake bias outside [0,1]')
    # 0043D6A0 uses bias+1 as a divisor and as a traction-ratio ceiling.
    # Conservative authoring policy; the engine itself does not clamp here.
    for key in ('CentreLSDBias','FrontLSDBias','RearLSDBias'):
        if not 1<=f('Engine/'+key)<=20:raise AddonValidationError('LSD torque bias outside SDK [1,20] guard')
    if not f('Engine/IdleRevs')<f('Engine/RevLimit'):raise AddonValidationError('idle must be below rev limit')
    # No array-size growth in phase 1: existing native counts/allocations remain.
    revs=[float(fields[f'Engine/TorqueEntry{i}']['value'].split()[0]) for i in range(int(fields['Engine/TorqueEntries']['value']))]
    if any(b<=a for a,b in zip(revs,revs[1:])):raise AddonValidationError('torque curve abscissae must increase')
    prefixes={n.get('Name','').split('/')[2].rstrip('0123456789') for n in ET.fromstring(data).iter('Value') if n.get('Name','').startswith('Vehicles/Tyres/')}
    for axle in ('Front','Rear'):
        if fields[f'Suspension/{axle}/TyreType']['value'] not in prefixes:raise AddonValidationError('unresolved shared tyre prefix')
    return audit.to_dict()

def apply_profile(data,profile,*,donor_family,runtime_family,source_label):
    """Edit only existing target rows. Caller first makes the independent clone.

    Project generation checks source hashes before cloning; runtime composition
    reapplies this exact typed profile to its separately sealed base tree.
    """
    validate_profile(profile,donor_family=donor_family,runtime_family=runtime_family)
    if source_label not in MEMBERS:raise AddonValidationError('unsupported physics member')
    prefix='Vehicles/'+runtime_family+'/'
    root=ET.fromstring(data);rows={n.get('Name','')[len(prefix):]:n for n in root.iter('Value') if n.get('Name','').startswith(prefix)}
    overrides=profile['overrides'].get(source_label,{})
    output=data;edits=[]
    for path,value in sorted(overrides.items()):
        if path not in rows:raise AddonValidationError('unknown physics field '+path)
        row=rows[path];kind=row.get('Type');encoded=_encode(value,kind)
        if source_label==MEMBERS[0] and path in ('Engine/Gears','Engine/TorqueEntries') and encoded!=row.get('Value'):raise AddonValidationError('array count edits require a future qualified schema revision')
        pattern=rb'(<Value\s+Name="'+re.escape((prefix+path).encode())+rb'"[^>]*\bValue=")([^"]*)(")'
        matches=list(re.finditer(pattern,output))
        if len(matches)!=1:raise AddonValidationError('ambiguous physics row serialization')
        match=matches[0];a,b=match.span(2)
        edits.append({'path':path,'type':kind,'before':row.get('Value'),'after':encoded})
        output=output[:a]+encoded.encode('ascii')+output[b:]
    if source_label==MEMBERS[0]:audit=_base_validate(output,runtime_family)
    else:
        audit=None
        for p,v in overrides.items():
            # 0044ED50 adds these deltas directly in the native field units.
            # Frontend fader values are a different namespace/presentation.
            path=p.split('/Modifications/',1)[1]
            if path not in PLAYER_MODIFICATION_FIELDS:raise AddonValidationError('unsupported player setup field')
            limit=2 if path.endswith('/RideHeight') else 1 if path.endswith('Bias') else 20 if path.endswith('/GearRatioDiff') else 1e6
            if type(v) not in (int,float) or abs(v)>limit:raise AddonValidationError('player setup delta exceeds SDK authoring guard')
    before_other=[dict(n.attrib) for n in root.iter('Value') if not n.get('Name','').startswith(prefix)]
    after_other=[dict(n.attrib) for n in ET.fromstring(output).iter('Value') if not n.get('Name','').startswith(prefix)]
    if before_other!=after_other:raise AddonValidationError('physics edit escaped target family')
    return output,{'profile_sha256':hashlib.sha256(canonical_json(profile)).hexdigest(),'edits':edits,'schema':audit,'other_families_unchanged':True,'semantic_delta':any(e['before']!=e['after'] for e in edits)}

def validate_player_defaults(vehicles,modifications,family,reference=None):
    """Check additive default setups without changing base or player data."""
    d=parse_vehicle_config_bytes(modifications,build='retail-2001-verified',source='player physics defaults').families.get(family,{})
    for player in (1,2):
        deltas={}
        for path in PLAYER_MODIFICATION_FIELDS:
            key=f'Player{player}/Modifications/{path}'
            if key not in d:raise AddonValidationError('missing player setup field '+key)
            delta=float(d[key]['value']);_number(delta);deltas[path]=delta
        _base_validate(vehicles,family,deltas)
        if reference:
            translated=dict(deltas)
            for axle,value in reference.items():translated['Suspension/'+axle+'/RideHeight']+=value
            _base_validate(vehicles,family,translated)

def compile_family(data,profile,*,donor_family,runtime_family,source_label):
    validate_profile(profile,donor_family=donor_family,runtime_family=runtime_family)
    if hashlib.sha256(data).hexdigest()!=profile['source_sha256'].get(source_label):raise AddonValidationError('physics retail member SHA256 mismatch')
    cloned,report=clone_vehicle_family_xml(data,donor_family=donor_family,runtime_family=runtime_family,source_label=source_label)
    output,delta=apply_profile(cloned,profile,donor_family=donor_family,runtime_family=runtime_family,source_label=source_label)
    return output,{**report,**delta}
