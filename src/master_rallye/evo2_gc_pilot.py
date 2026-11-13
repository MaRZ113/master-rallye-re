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

# Evo 2 collection (owner 2026-11-13: Evo 1 / Evo 2 / GC comparison, docs/sdk/EVO_COLLECTION.md): the rally-prepared
# SUVs, race trucks and the ARB monster, all from the GC TRUCK.pod (same meshes and textures as the PC game).
# Author class T1/T2 only (SDK); the target is a separate Evo class until the owner places them.
EVO='EVO (separate class, owner to place)'
for key,family,name,make,model,results,donor,audio in (
    ('T4R4','Evo2Toyota4RunnerRally','Toyota 4Runner Rally Edition','TOYOTA','4RUNNER RALLY','TOYOTA 4RUNNER','Pajero',1),
    ('JGCRSUV','Evo2JeepCherokeeRace','Jeep Grand Cherokee Race SUV','JEEP','GRAND CHEROKEE RACE','JEEP CHEROKEE','Pajero',1),
    ('DDRE4','Evo2DodgeDurangoRally','Dodge Durango Rally Edition','DODGE','DURANGO RALLY','DODGE DURANGO','Pajero',1),
    ('JLRE4','Evo2JeepLibertyRally','Jeep Liberty Rally Edition','JEEP','LIBERTY RALLY','JEEP LIBERTY','Pajero',1),
    ('LLX470RE','Evo2LexusLX470Rally','Lexus LX 470 Rally Edition','LEXUS','LX 470 RALLY','LEXUS LX 470','Pajero',1),
    ('IQX4RE4','Evo2InfinitiQX4Rally','Infiniti QX4 Rally Edition','INFINITI','QX4 RALLY','INFINITI QX4','Pajero',1),
    ('XTERRT','Evo2NissanXterraRace','Nissan Xterra Race SUV','NISSAN','XTERRA RACE','NISSAN XTERRA','Pajero',1),
    ('CBRE4','Evo2ChevyBlazerRally','Chevrolet Blazer Rally Edition','CHEVROLET','BLAZER RALLY','CHEVROLET BLAZER','Pajero',1),
    ('CTTT2','Evo2ChevyTrailBlazerRace','Chevrolet TrailBlazer Race SUV','CHEVROLET','TRAILBLAZER RACE','CHEVROLET TRAILBLAZER','Pajero',1),
    ('MPRT2D','Evo2MitsubishiMonteroRally','Mitsubishi Montero Rally','MITSUBISHI','MONTERO RALLY','MITSUBISHI MONTERO','Pajero',1),
    ('AJWS','Evo2JeepARBWrangler','Jeep ARB Wrangler Rally Edition','JEEP','ARB WRANGLER','JEEP ARB WRANGLER','Pajero',1),
    ('DDRT','Evo2DodgeDakotaRace','Dodge Dakota Race Truck','DODGE','DAKOTA RACE','DODGE DAKOTA','Navara',7),
    ('DRTT','Evo2DodgeRamRace','Dodge Ram Race Truck','DODGE','RAM RACE','DODGE RAM','Navara',7),
    ('GS1TT','Evo2GMCSierraTrophy','GMC Sierra 1500 Trophy Truck','GMC','SIERRA TROPHY','GMC SIERRA','Navara',7),
    ('TTTT2','Evo2ToyotaTundraRace','Toyota Tundra Race Truck','TOYOTA','TUNDRA RACE','TOYOTA TUNDRA','Navara',7),
    ('FRRT','Evo2NissanFrontierRace','Nissan Frontier Race Truck','NISSAN','FRONTIER RACE','NISSAN FRONTIER','Navara',7),
    ('AMT','Evo2GMCARBMonster','GMC ARB Sierra Monster Truck','GMC','ARB SIERRA MONSTER','GMC ARB MONSTER','Patrol',7)):
    base.VEHICLES[key]=_spec(family,name,make,model,results,donor,audio,'T2',EVO)
    base.VEHICLES[key]['label']='Evo 2'



def create_pilot(scene_path,truck,retail_sma,retail_root,output,**kw):
    return base.create_pilot(scene_path,truck,retail_sma,retail_root,output,**kw)
