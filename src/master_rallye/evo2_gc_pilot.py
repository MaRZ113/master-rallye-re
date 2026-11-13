"""4x4 Evo 2 GameCube exclusive trucks -> MR Classic native projects.

Same owner policy and pipeline as the TXR3/Total Drivin' pilots (txr3_classic_pilot.create_pilot),
but with the source's own wheels and true dimensions (feet -> metres, no donor rescale, source
track widths). Roles come from the SMF object names.
"""
from __future__ import annotations
from . import txr3_classic_pilot as base

OBJECT_ROLE={'BODY':'paint','BEDCOVR':'paint','GLASSE':'glass','COCKPIT':'interior','UNDBODY':'trim','MIRRORL':'trim','MIRRORR':'trim',
             'WIPERLT':'trim','WIPERRT':'trim','MUDFLPS':'trim','BUMPERF':'trim','BUMPERR':'trim','CLADRT':'trim','BIKINI':'trim',
             'SKID':'chrome','BUSHBAR':'chrome','ROLLBR1':'chrome','ROLLBR2':'chrome','WINCH':'chrome','RFRACK':'chrome','RACK':'chrome','STEPS':'chrome','SNORKEL':'trim','FFLARES':'paint','HSCOOP':'paint','VISOR':'trim','BUGSHLD':'trim','SPARE':'tyre','SPARE2':'tyre',
             'LIGHTBL':'brake','LIGHTBR':'brake','LIGHTBC':'brake','TIRE':'tyre','WHEEL':'chrome'}


def _role(material):
    name=material.get('object','').upper()
    if name.startswith('FOG'):return 'lamp'
    if name=='SUSP_SHOCKS':return 'chrome'
    if name.startswith(('SUSP_','AXLE')):return 'trim'
    return OBJECT_ROLE.get(name,'trim')


def _spec(family,name,make,model,results,donor,audio,cls,target):
    return {'family':family,'name':name+' (Evo 2 GC)','manufacturer':make,'model':model,'results':results,'donor':donor,'audio':audio,
            'class':cls,'target_class':target,'label':'Evo 2 GC','source_label':'4x4 Evo 2 (GameCube)',
            'source_format':'Evo 2 GC Universal Vehicle Scene','adapter_id':'evo2-gc-truck/1','long_axis':11,'role_fn':_role,
            'glass_key':'mat-body-glasse','keep_source_scale':True,'source_track':True,
            'brake_evidence':'Evo 2 rear lens quads LightBL/LightBR and high stop LightBC.'}


base.VEHICLES.update({
    'CFRT':_spec('CalminiFrontier','Calmini Nissan Frontier Race Truck','NISSAN','FRONTIER RACE','CALMINI FRONTIER','Navara',7,'T2','T5 RAID'),
    'WDRT':_spec('WarnDakota','Warn Dodge Dakota Race Truck','DODGE','DAKOTA RACE','WARN DAKOTA','Navara',7,'T2','T5 RAID'),
    'SMT':_spec('StillenSilverado','Stillen Silverado Monster Truck','CHEVROLET','SILVERADO MONSTER','STILLEN SILVERADO','Patrol',7,'T2','monster (owner to place)'),
    'JWR':_spec('JeepWrangler','Jeep Wrangler Rubicon','JEEP','WRANGLER RUBICON','JEEP WRANGLER','Pajero',1,'T1','T1 UNMODIFIED'),
})


def create_pilot(scene_path,truck,retail_sma,retail_root,output,**kw):
    return base.create_pilot(scene_path,truck,retail_sma,retail_root,output,**kw)
