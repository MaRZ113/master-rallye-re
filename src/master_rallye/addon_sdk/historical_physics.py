"""Transfer typed original MR-family values into an independent retail template.

Retail-only solver fields stay explicit. This does not emulate an older solver
or reinterpret foreign-game numbers. Original Broker rows remain provenance.
"""
import hashlib,xml.etree.ElementTree as ET
from .physics_profile import MEMBERS,compile_family,validate_player_defaults
from ..vehicle_family_broker import PLAYER_MODIFICATION_FIELDS


def _rows(raw,family):
    prefix='Vehicles/'+family+'/'
    pairs=[(n.get('Name')[len(prefix):],dict(n.attrib))for n in ET.fromstring(raw).iter('Value')if n.get('Name','').startswith(prefix)]
    if not pairs or len(dict(pairs))!=len(pairs):raise ValueError('Missing or duplicate historical physics rows')
    return dict(pairs)


def _value(row):
    kind=row['Type'];v=row['Value']
    if kind=='Float':return float(v)
    if kind=='Int':return int(v)
    if kind=='Bool':
        if v not in ('True','False'):raise ValueError('Invalid source Bool')
        return v=='True'
    if kind in ('Vector2','Vector3'):return [float(x)for x in v.split()]
    if kind=='String':return v
    raise ValueError('Unsupported source physics type '+kind)


def source_family_profile(source,retail_members,*,source_family,donor_family,runtime_family,source_only=None):
    original=_rows(source,source_family);donor=_rows(retail_members[MEMBERS[0]],donor_family)
    source_only={}if source_only is None else source_only
    if not isinstance(source_only,dict)or set(source_only)-set(original)or any(not isinstance(v,str)or not v.strip()for v in source_only.values()):raise ValueError('Source-only fields need existing names and explicit compatibility reasons')
    curve={n for n in original if n=='Engine/TorqueEntries'or n.startswith('Engine/TorqueEntry')}
    if curve&set(source_only)and not curve<=set(source_only):raise ValueError('A retained torque curve must include its count and every original point')
    base={};mods={};unmapped=[]
    for name,row in original.items():
        if name in source_only:continue
        if name in donor:
            if row['Type']!=donor[name]['Type']:raise ValueError('Historical physics type changed: '+name)
            base[name]=_value(row)
        elif name.startswith('Modifications/')and name[len('Modifications/'):]in PLAYER_MODIFICATION_FIELDS:
            for player in (1,2):mods[f'Player{player}/'+name]=_value(row)
        else:unmapped.append(name)
    if unmapped:raise ValueError('Unmapped original physics fields: '+', '.join(unmapped))
    profile={'profile_version':1,'donor_family':donor_family,'runtime_family':runtime_family,
             'source_sha256':{n:hashlib.sha256(retail_members[n]).hexdigest()for n in MEMBERS},
             'overrides':{MEMBERS[0]:base,MEMBERS[1]:mods},
             'notes':'Original MR historical family values in independently cloned retail schema. Retail-only fields retained explicitly; no older solver equivalence claimed.'}
    tyre_report=[]
    references={base[p]for p in ('Suspension/Front/TyreType','Suspension/Rear/TyreType')if p in base}
    retail_tyres_selected=all('Suspension/'+a+'/TyreType'in source_only for a in ('Front','Rear'))
    if len(references)!=1 and not retail_tyres_selected:raise ValueError('Historical tyre transfer requires one explicit shared source prefix')
    tyre=next(iter(references))if references else '';prefix='Vehicles/Tyres/'+tyre
    collect=lambda b:{n.get('Name')[len(prefix):]:dict(n.attrib)for n in ET.fromstring(b).iter('Value')if n.get('Name','').startswith(prefix)and n.get('Name')[len(prefix):][:1].isdigit()}
    source_tyres,retail_tyres=(collect(source),collect(retail_members[MEMBERS[0]]))if not retail_tyres_selected else({},{})
    changes=[k for k,v in source_tyres.items()if k not in retail_tyres or v['Type']!=retail_tyres[k]['Type']or _value(v)!=_value(retail_tyres[k])]
    if changes:
        if set(source_tyres)-set(retail_tyres)or any(source_tyres[k]['Type']!=retail_tyres[k]['Type']for k in source_tyres):raise ValueError('Historical tyre schema differs from retail')
        owned=runtime_family+'Tyre'
        profile['owned_tyres']={'donor_prefix':tyre,'runtime_prefix':owned,'overrides':{k:_value(v)for k,v in source_tyres.items()}}
        for axle in ('Front','Rear'):base['Suspension/'+axle+'/TyreType']=owned
        tyre_report={'source_prefix':tyre,'runtime_prefix':owned,'source_rows':len(source_tyres),'retail_only_rows':len(set(retail_tyres)-set(source_tyres)),
                     'different_source_fields':changes,'boundary':'Source tyre coefficients in an owned clone; additional retail solver fields inherited explicitly, stock tables untouched.'}
    compiled={n:compile_family(retail_members[n],profile,donor_family=donor_family,runtime_family=runtime_family,source_label=n)[0]for n in MEMBERS}
    validate_player_defaults(compiled[MEMBERS[0]],compiled[MEMBERS[1]],runtime_family)
    report={'source_sha256':hashlib.sha256(source).hexdigest(),'original_family':source_family,'source_row_count':len(original),
            'base_rows_transferred':len(base),'player_setup_rows':len(mods),
            'retail_only_fields':{k:v for k,v in donor.items()if k not in base},'unmapped':unmapped,'owned_tyres':tyre_report,
            'source_only_fields':{k:{'original':original[k],'reason':v,'retail_value':donor.get(k)}for k,v in source_only.items()},
            'boundary':'Source parameter preservation in retail solver; suspension, collision and complete gameplay remain owner-test gates.'}
    return profile,report
