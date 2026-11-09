"""Offline Course/Race catalog and shared registry layout, not runtime admission.

Course keys are SDK identities. Retail has integer race registrations and
string scene/model paths, not a separately proven numeric CourseID registry.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import PurePosixPath

SCHEMA = 'mr-course-registry/1'


def resource_path(value):
    if not isinstance(value,str) or not value or '\\' in value or ':' in value:
        raise ValueError('Use a relative portable resource path')
    p=PurePosixPath(value)
    if p.is_absolute() or any(x in ('..','.') for x in value.split('/')):
        raise ValueError('Unsafe resource path')
    return str(p)


def storage_layout(vehicle_count, race_count):
    if type(vehicle_count) is not int or vehicle_count<26 or type(race_count) is not int or race_count<39:
        raise ValueError('Preserve original vehicle and race records')
    race_base=4+vehicle_count*52
    size=race_base+race_count*44
    if size>0x7fffffff:raise ValueError('Shared signed-x86 allocation arithmetic overflow')
    return {'vehicle_count':vehicle_count,'race_count':race_count,'vehicle_stride':52,'race_stride':44,
            'race_base':race_base,'allocation_size':size,
            'race_lifecycle_encoding':'push-imm32-required' if race_count>=128 else 'signed-imm8-representable'}


def validate_manifest(doc, baseline):
    if not isinstance(doc,dict) or doc.get('schema')!=SCHEMA:raise ValueError('Unsupported course registry schema')
    if len(baseline)!=39 or [r['id'] for r in baseline]!=list(range(39)):raise ValueError('Need extracted original registrations')
    result=copy.deepcopy(doc);courses=result['courses'];races=result['races'];keys={};ids={}
    for c in courses:
        key=c['key']
        if not isinstance(key,str) or not key or key in keys:raise ValueError('Duplicate/invalid stable course key')
        keys[key]=c
        model=resource_path(c['model']);folder=resource_path(c['folder'])
        if str(PurePosixPath(model).parent).lower()!=folder.lower():raise ValueError('Model is outside declared course folder')
    for r in races:
        i=r['id']
        if type(i) is not int or i<0 or i>0x7fffffff or i in ids:raise ValueError('Duplicate/invalid race registration ID')
        if r['course'] not in keys:raise ValueError('Missing course identity')
        resource_path(r['scene']);resource_path(r['icont'])
        if len(r['native_fields'])!=9 or any(type(v) is not int or not 0<=v<=0xffffffff for v in r['native_fields']):raise ValueError('Need nine native DWORD fields')
        if r['native_fields'][0]!=i:raise ValueError('Native ID differs from registration')
        ids[i]=r
    if sorted(ids)!=list(range(len(ids))):raise ValueError('Uninitialized registry holes are not qualified')
    for old in baseline:
        now=ids.get(old['id'])
        if now is None or now['scene']!=old['scene'] or now['native_fields']!=old['native_fields']:
            raise ValueError('Original race registration changed')
    for group in result.get('competitions',[]):
        if len(group['races'])!=len(set(group['races'])) or any(i not in ids for i in group['races']):raise ValueError('Invalid stage mapping')
        if group.get('runtime_enabled',False):raise ValueError('New competition runtime routes are not qualified by offline catalog')
    result['layout']=storage_layout(result['vehicle_count'],len(races))
    result['races']=sorted(races,key=lambda r:r['id'])
    result['status']='OFFLINE_CATALOG_ONLY'
    result['runtime_qualified']=False
    return result


def identity_contract(catalog):
    """Stable routes/identities; intentionally no texture/artwork hashes."""
    value={'courses':sorted((c['key'],c['folder'],c['model']) for c in catalog['courses']),
           'races':[(r['id'],r['course'],r['scene'],r['icont'],r['native_fields']) for r in catalog['races']],
           'competitions':catalog.get('competitions',[])}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def build_initializer(catalog, *, code_va=0x71000000, registry_va=0x02000000, strings_va=0x03000000):
    """Emit an offline native-call experiment; original 0045A330 owns field writes.

    Each scene argument represents an already constructed enString handle.
    Ownership/string assignment are mocked by the CPU harness, not qualified.
    This blob is never installed in an EXE or game process.
    """
    out=bytearray();strings=bytearray();rows=[]
    for r in catalog['races']:
        handle=strings_va+len(strings);strings.extend(r['scene'].removesuffix('.xml').removeprefix('DataScene/').encode('ascii')+b'\0')
        f=r['native_fields'];args=f[:7]+[handle]+f[7:]
        for value in reversed(args):out.extend(b'\x68'+value.to_bytes(4,'little'))
        target=registry_va+catalog['layout']['race_base']+r['id']*44
        out.extend(b'\xb9'+target.to_bytes(4,'little'))
        out.extend(b'\xe8'+(0x45a330-(code_va+len(out)+5)).to_bytes(4,'little',signed=True))
        rows.append({'id':r['id'],'address':target,'fields':f,'string':handle})
    out.extend(b'\xc3')
    return bytes(out),bytes(strings),rows
