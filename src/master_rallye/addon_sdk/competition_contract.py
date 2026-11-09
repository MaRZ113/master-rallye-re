"""Gameplay dependencies of a saved competition, excluding visual authoring."""
import hashlib
import json
import xml.etree.ElementTree as ET
from .roster_identity import validate_catalog


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def values(raw):
    root=ET.fromstring(raw)
    rows=[dict(v.attrib) for v in root.iter('Value')]
    names=[r.get('Name') for r in rows]
    if len(names)!=len(set(names)):raise ValueError('Duplicate competition dependency key')
    return sorted(rows,key=lambda r:r.get('Name',''))


def build_contract(identity,resources,addons,*,collision_fingerprints):
    entries=validate_catalog(identity);deps={}
    for path in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
        if path not in resources:raise ValueError('Missing gameplay dependency: '+path)
        deps[path]=digest(values(resources[path]))
    for path in ('DataGame/MasterRallye.xml','DataGame/RallyeCup.xml','DataGame/Race.xml','DataGame/RaceTest.xml'):
        if path in resources:deps[path]=digest(values(resources[path]))
    deps['collision']=digest(collision_fingerprints)
    mode_rows=[{'physical_id':r['physical_id'],'class':r['vehicle_class'],'modes':sorted(k for k,v in r['ai_eligibility'].items() if v['enabled'])} for r in addons]
    payload={'schema':'mr-competition-contract/1','native_rules_abi':'stock-x86-39x44-3classes-v1','namespace':identity['namespace'],
             'identities':[{'physical_id':i,'family':e['family'],'vehicle_class':e['vehicle_class'],'retired':e.get('retired',False)} for i,e in sorted(entries.items())],
             'ai_eligibility':sorted(mode_rows,key=lambda e:e['physical_id']),'dependencies':deps}
    return {**payload,'sha256':digest(payload)}


def validate_contract(doc):
    if not isinstance(doc,dict) or doc.get('schema')!='mr-competition-contract/1':raise ValueError('Unsupported competition contract')
    if (set(doc)!={'schema','native_rules_abi','namespace','identities','ai_eligibility','dependencies','sha256'}
        or not isinstance(doc['identities'],list) or not isinstance(doc['ai_eligibility'],list)
        or not isinstance(doc['dependencies'],dict) or not all(isinstance(k,str) and isinstance(v,str) and len(v)==64 for k,v in doc['dependencies'].items())):
        raise ValueError('Malformed competition identity/dependency contract')
    validate_catalog({'schema':'mr-roster-identity/1','namespace':doc['namespace'],'entries':doc['identities']})
    if doc.get('sha256')!=digest({k:v for k,v in doc.items() if k!='sha256'}):raise ValueError('Competition contract content differs from fingerprint')
    return doc


def require_compatible(previous,current,*,active):
    validate_contract(current)
    if not active:return
    if previous is None:raise ValueError('Active competition has no identity/dependency baseline; finish it in the original package or supply its original contract')
    validate_contract(previous)
    if previous['sha256']!=current['sha256']:
        changes=[k for k in set(previous['dependencies'])|set(current['dependencies']) if previous['dependencies'].get(k)!=current['dependencies'].get(k)]
        if previous['identities']!=current['identities']:changes.append('stable vehicle identities/classes')
        if previous['ai_eligibility']!=current['ai_eligibility']:changes.append('mode eligibility')
        raise ValueError('Active competition dependencies changed: '+', '.join(sorted(changes))+'; save left unchanged')
