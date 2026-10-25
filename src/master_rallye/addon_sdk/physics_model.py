"""Small exact-build parameter relations; no replacement physics simulation."""
import math

def effective_setup(fields,modifications=None,*,family=None,player=1,saved_state=None,reference=None):
    """Native 0044ED50 additive setup; 0044E490 saves Real minus base.

    The menu displays absolute Real*1000, not the saved delta. An optional SDK
    reference is applied only at participant publication, never to menu values.
    saved_state is XML bytes, read only; absent keys retain initial deltas.
    """
    import copy,xml.etree.ElementTree as ET
    from ..vehicle_family_broker import PLAYER_MODIFICATION_FIELDS
    if player not in (1,2):raise ValueError('player must be 1 or 2')
    result=copy.deepcopy(fields);deltas={};saved={}
    if saved_state is not None:
        if not family:raise ValueError('family is required for saved player state')
        prefix=f'Vehicles/{family}/Player{player}/Modifications/'
        for row in ET.fromstring(saved_state).iter('Value'):
            path=row.get('Name','')
            if path.startswith(prefix):
                key=path[len(prefix):]
                if key in saved:raise ValueError('duplicate saved setup field')
                if key in PLAYER_MODIFICATION_FIELDS:saved[key]=float(row.get('Value'))
    for key in PLAYER_MODIFICATION_FIELDS:
        initial=(modifications or {}).get(f'Player{player}/Modifications/'+key,{}).get('value','0')
        value=saved.get(key,float(initial))
        if not math.isfinite(value):raise ValueError('nonfinite player setup')
        deltas[key]=value
        if key=='Engine/GearRatioDiff':
            for k in result:
                if k.startswith('Engine/Gear') and k[len('Engine/Gear'):].isdigit():result[k]['value']=str(float(result[k]['value'])*(1+value))
        elif key in result:result[key]['value']=str(float(result[key]['value'])+value)
    menu={axle:float(result[f'Suspension/{axle}/RideHeight']['value'])*1000 for axle in ('Front','Rear')}
    for axle,value in (reference or {}).items():
        if axle not in ('Front','Rear') or not math.isfinite(value):raise ValueError('invalid ride reference')
        k=f'Suspension/{axle}/RideHeight';result[k]['value']=str(float(result[k]['value'])+value)
    return result,{'player':player,'deltas':deltas,'saved_fields':sorted(saved),'menu_ride_height_mm':menu,'ride_height_reference_m':reference or {},'boundary':'native configuration relations; no contact or equilibrium integration'}

def suspension_summary(fields):
    """Upright symmetric contact branch of 00446B10/00446D20.

    Native gravity preload makes jounce zero a force-balance datum at arm ratio
    one. This is a local force estimate, not a full vehicle equilibrium solve.
    """
    n=lambda k:float(fields[k]['value']);mass=n('Chassis/TotalMass');g=n('Chassis/Gravity');cgz=float(fields['Chassis/CentreOfGravity']['value'].split()[2]);rows=[]
    for axle,sign in [('Front',1),('Rear',-1)]:
        s='Suspension/'+axle+'/';u=n(s+'UnsprungMass');m=(1+sign*cgz/n('Dimensions/Length'))*mass/4-u
        r=n(s+'SpringArmRatio');k=n(s+'SpringRate');d=n(s+'DamperRate');dr=n(s+'DamperArmRatio')
        j=m*g*(1-r)/(k*r) # body spring branch, no roll and no relative velocity
        rows.append({'axle':axle,'sprung_corner_mass_kg':m,'preload_body_N':m*g,'preload_contact_N':(m*r+u)*g,
            'symmetric_jounce_estimate_m':j,'effective_body_spring_N_per_m':k*r,'contact_spring_N_per_m':k*r*r,
            'body_damping_Ns_per_m':d*dr,'contact_damping_Ns_per_m':d*dr*dr,
            'travel_m':[-n(s+'MaxDroop'),n(s+'MaxBounce')],
            'reference_hub_y_m':-n(s+'RideHeight'),'estimated_hub_y_m':-n(s+'RideHeight')+j})
    return {'rows':rows,'boundary':'upright symmetric native force branch with static contacts, no pitch/roll/tyre/contact solve; not gameplay telemetry'}

def wheel_attachments(fields):
    """004407FC..004408C0: native X/Z half-dimensions, Y=-RideHeight.

    These are unloaded attachment data, not tyre contact or settled hub poses.
    Native camber, toe, steering, spring jounce and deformation are not applied.
    """
    def number(path):
        value=float(fields[path]['value'])
        if not math.isfinite(value):raise ValueError('nonfinite wheel attachment parameter')
        return value
    wheelbase=number('Dimensions/WheelBase');rows=[]
    if wheelbase<=0:raise ValueError('wheelbase must be positive')
    for axle,front in [('Front',True),('Rear',False)]:
        track=number('Dimensions/TrackWidth'+axle);height=number('Suspension/'+axle+'/RideHeight')
        if track<=0:raise ValueError('track width must be positive')
        for side in (1,-1):rows.append({'translation':[side*track/2,-height,(1 if front else -1)*wheelbase/2],'rotation_y':math.pi if side==1 else 0.,'scale':[1.,1.,1.]})
    return {'race_wheel_instances':rows,'provenance':'exact retail native attachment formula at 004407FC..004408C0; static attachment diagnostic only, no contact solve, dynamic sag, toe/camber or steering'}
