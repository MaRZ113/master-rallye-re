"""Create a pinned donor-default profile or inventory user-supplied MR physics.

Profiles contain editable configuration, never bundled game XML or assets.
"""
import argparse,collections,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.vehicle_config_analysis import parse_vehicle_config_bytes
from master_rallye.vehicle_family_broker import BROKER_GROUP_PAIRS
from master_rallye.addon_sdk.physics_profile import compile_family,validate_profile

def inventory(raw):
    doc=parse_vehicle_config_bytes(raw,build='retail-2001-verified');by=collections.defaultdict(list)
    for family,fields in doc.families.items():
        for path,row in fields.items():by[(path,row['type'])].append((family,row['value']))
    rows=[]
    for (path,kind),values in sorted(by.items()):
        group='/'.join(path.split('/')[:2]) if path.startswith('Suspension/') else path.split('/')[0]
        pair=next((p for p in BROKER_GROUP_PAIRS if p.group==group),None)
        row={'path':path,'type':kind,'source_member':'DataGame/vehicles.xml','family_count':len(values),'reader':pair.reader if pair else None,'instance_writer':pair.writer if pair else None,'consumer_boundary':'reader/writer dataflow; per-field force semantics require separate native consumer evidence'}
        if kind in ('Float','Int','Vector2','Vector3'):
            vs=[[float(x) for x in v.split()] for _,v in values]
            if len({len(v) for v in vs})==1:row['observed_component_min_max']=[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(len(vs[0]))]
        rows.append(row)
    return {'source_sha256':hashlib.sha256(raw).hexdigest(),'parameters':rows,'families':sorted(doc.families),'excluded_namespaces':sorted(doc.excluded_families),'boundary':'observed stock ranges are not engine clamps or proven safe tuning bounds; includes XML-only named families as well as selectable records'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['init','inventory']);p.add_argument('--vehicles',type=Path,required=True);p.add_argument('--modifications',type=Path);p.add_argument('--donor');p.add_argument('--family');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('output already exists')
    raw=a.vehicles.read_bytes()
    if a.mode=='inventory':result=inventory(raw)
    else:
        if not (a.modifications and a.donor and a.family):p.error('init needs --modifications, --donor and --family')
        result={'profile_version':1,'donor_family':a.donor,'runtime_family':a.family,'source_sha256':{'DataGame/vehicles.xml':hashlib.sha256(raw).hexdigest(),'DataGame/Modifications.xml':hashlib.sha256(a.modifications.read_bytes()).hexdigest()},'overrides':{},'notes':'Donor-derived defaults. Add typed relative field edits under overrides. Validate/build with exact retail archive; no live edits.'}
        for member,data in [('DataGame/vehicles.xml',raw),('DataGame/Modifications.xml',a.modifications.read_bytes())]:compile_family(data,result,donor_family=a.donor,runtime_family=a.family,source_label=member)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output)
