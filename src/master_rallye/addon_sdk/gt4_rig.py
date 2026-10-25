"""Source-backed normal-four-wheel GT4 rest-pose assembly.

Uses recovered DBT bytes and the traced ModelSet2 wheel constructors. This is
an admitted layout, not an arch-fitting algorithm or a physics adjustment.
"""
from __future__ import annotations
import math,struct
from .gt4_spec import DatabaseTable,label_id

def recover_spec(folder,labels):
    raw={};evidence={}
    for table,label in labels.items():
        idi=(folder/(table+'.idi')).read_bytes();db=DatabaseTable((folder/(table+'.dbt')).read_bytes());index=label_id(idi,label)
        raw[table]=db.row(index);evidence[table]={**db.evidence(index),'label':label}
    chassis=raw['CHASSIS'];modify=raw['RACINGMODIFY'];suspension=raw['SUSPENSION']
    if len(chassis)!=37 or len(modify)!=29 or len(suspension)!=111:raise ValueError('unqualified GT4 spec row grammar')
    if chassis[31]!=0:raise ValueError('wheel layout other than native normal-four not yet qualified')
    wheelbase=struct.unpack_from('<h',chassis,4)[0]*.001
    tracks=[struct.unpack_from('<h',modify,2+2*i)[0]*.001-struct.unpack_from('<b',modify,19+i)[0]*.002 for i in range(2)]
    ride=[struct.unpack_from('<h',suspension,4+6*i)[0]*.001 for i in range(2)]
    sizes=[]
    for table in ('FRONTTIRE','REARTIRE'):
        row=raw[table];index,kind=struct.unpack_from('<ii',row)
        if kind!=31:raise ValueError('unqualified tire-size table binding')
        db=DatabaseTable((folder/'TIRESIZE.dbt').read_bytes());tyre=db.row(index)
        if len(tyre)!=4:raise ValueError('tire-size record grammar')
        flat,category,diameter,width=tyre
        if category!=0:raise ValueError('unqualified tire-size category')
        # FUN_0020C898: rim-radius and sidewall, before optional size changes.
        rim=diameter*.0254*.5 if diameter<61 else (diameter/10*.0254*.5 if diameter%10==0 else diameter*.0254*.05)
        w=(width*5 if width else 10)*.001;sidewall=w*flat*.05
        sizes.append({'width':w,'rim_radius':rim,'sidewall':sidewall,'radius':rim+sidewall})
        evidence[table]['tire_size']=db.evidence(index)
    if any(not .05<s['rim_radius']<1 or not .05<s['width']<1 for s in sizes) or not .5<wheelbase<10:raise ValueError('implausible source wheel dimensions')
    wheels=[]
    for i in range(4):
        axle=i//2;sign=-1 if i%2==0 else 1;s=sizes[axle]
        wheels.append({'index':i,'axle':axle,'side':sign,'hub':[sign*tracks[axle]/2,s['radius']-ride[axle],(-1 if axle==0 else 1)*wheelbase/2],**s})
    return {'wheels':wheels,'wheelbase':wheelbase,'tracks':tracks,'ride_height':ride,'source_evidence':evidence,
            'pose':'GT4 normal-four menu rest pose relative to body; zero steering and spin; no MR physics edits',
            'native_evidence':['00301458 chassis wheelbase -> parameter1A','00302138 racing-modify tracks/offsets -> parameters1C/1E/96/97',
                '002252D8 metre conversion and half-track','00205E80 front/rear Z = signed half-wheelbase',
                '00224600 plus 00228608/00205E08 Y = tyre radius - ride height; spring deflection cancels',
                '0020C898 tire-size radius/width formula','002F5B48 / 002F5CB8 tire radial deformation; 002F3C40 rim-radius scale'],
            'limitations':['nonzero steering/spin not simulated','GT4 live suspension pose differs from this source rest pose','VU normal lighting not reconstructed']}

def wheel_point(point,wheel,*,kind='rim',radial_range=None,max_x=None):
    x,y,z=point;r=math.hypot(y,z)
    if kind=='rim':x*=wheel['rim_radius'];y*=wheel['rim_radius'];z*=wheel['rim_radius']
    elif kind=='tyre':
        lo,hi=radial_range
        if hi-lo<1e-6 or not max_x or r<1e-8:raise ValueError('unqualified normalized tyre geometry')
        radius=wheel['rim_radius']+(r-lo)*wheel['sidewall']/(hi-lo)
        x=x*wheel['width']/max_x;y*=radius/r;z*=radius/r
    elif kind!='brake':raise ValueError('unknown wheel layer')
    # Native callback15 scales rim then rotates the right wheel 180 degrees;
    # the preceding callback11 has already applied the half-width translation.
    if wheel['side']>0 and kind!='brake':x,z=-x,-z
    h=wheel['hub'];shift=wheel['side']*wheel['width']/2
    return (x+h[0]+shift,y+h[1],z+h[2])
