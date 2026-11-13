"""Total Drivin' (PS1) Citroen ZX Rallye Raid -> MR Classic native project.

Same owner policy and pipeline as the TXR3 VehiCROSS pilot (txr3_classic_pilot.create_pilot):
source geometry and VRAM textures, stock MR materials by semantic role, retail Pajero donor
wheels and physics with measured dimensions. Roles come from the Total Drivin' material type:
0x0a glasshouse -> glass, 1 car header colour -> paint, 2 -> trim, 8 textured livery -> paint,
0x10 two-state textured (rear lamps, off/on per frame buffer) -> brake.
"""
from __future__ import annotations
from . import txr3_classic_pilot as base

TYPE_ROLE={10:'glass',1:'paint',2:'trim',8:'paint',16:'brake'}


def _role(material):
    raw=material['raw_fields'][0]
    return TYPE_ROLE.get(raw['type'],'trim')


def _spec(car,livery):
    return {'family':'ZXRallyeRaid','name':"Citroen ZX Rallye Raid (Total Drivin' %s)"%car,'manufacturer':'CITROEN','model':'ZX RALLYE RAID',
            'results':'CITROEN ZX RALLYE RAID','donor':'Pajero','audio':1,'class':'T2','target_class':'T5 RAID (CLASSES.md); author project limited to T1/T2',
            'label':"Total Drivin'",'source_label':"Total Drivin' (PS1)",'source_format':"Total Drivin' PS1 Universal Vehicle Scene",
            'adapter_id':'total-drivin-ps1/1','long_axis':11,'role_fn':_role,'glass_material':0,
            'brake_evidence':"Total Drivin' two-state lamp material (type 0x10, off/on CLUT per buffer) at the rear; first state used.",
            'livery':livery}


base.VEHICLES['ZX_DAKAR1']=_spec('DAKAR1','red')
base.VEHICLES['ZX_DAKAR2']=_spec('DAKAR2','blue/white')


def create_pilot(scene_path,vehicle,retail_sma,retail_root,output,**kw):
    return base.create_pilot(scene_path,vehicle,retail_sma,retail_root,output,**kw)
