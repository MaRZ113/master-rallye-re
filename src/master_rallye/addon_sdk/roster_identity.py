"""Portable physical identity catalog and read-only save preflight.

Texture/model hashes are deliberately absent: repainting is not an ID change.
This checks mapping, not the qualification of every native persistence path.
"""
import re
import hashlib
import json
import xml.etree.ElementTree as ET

SCHEMA='mr-roster-identity/1'


def catalog(entries,namespace='master-rallye-retail-sdk33'):
    result={'schema':SCHEMA,'namespace':namespace,'entries':sorted(entries,key=lambda e:e['physical_id'])}
    validate_catalog(result)
    return result


def validate_catalog(doc):
    if doc.get('schema')!=SCHEMA or not isinstance(doc.get('namespace'),str) or not doc['namespace']:
        raise ValueError('Unsupported roster identity catalog')
    entries=doc.get('entries')
    if not isinstance(entries,list):raise ValueError('Roster entries must be a list')
    result={}
    for e in entries:
        i=e.get('physical_id');family=e.get('family');cls=e.get('vehicle_class')
        if type(i)is not int or not 0<=i<=0x7fffffff or i in result:raise ValueError('Invalid/duplicate physical identity')
        if not isinstance(family,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',family):raise ValueError('Invalid native family')
        if not isinstance(cls,str) or not re.fullmatch(r'T[1-9][0-9]*',cls) or type(e.get('retired',False)) is not bool:raise ValueError('Invalid class/tombstone')
        result[i]=e
    return result


def identity_digest(doc):
    validate_catalog(doc)
    return hashlib.sha256(json.dumps(doc,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def preserve_reservations(previous,current,*,migration=None):
    old,new=validate_catalog(previous),validate_catalog(current)
    if previous['namespace']!=current['namespace']:raise ValueError('Roster namespace changed')
    reactivated={i for i,e in old.items() if e.get('retired',False) and i in new and not new[i].get('retired',False)}
    if migration is not None:
        if (not isinstance(migration,dict) or set(migration)!={'schema','previous_identity_sha256','reactivate','reason'}
                or migration['schema']!='mr-roster-reactivation/1'
                or migration['previous_identity_sha256']!=identity_digest(previous)
                or not isinstance(migration['reason'],str) or not migration['reason'].strip()
                or not isinstance(migration['reactivate'],list)
                or any(type(i)is not int for i in migration['reactivate'])
                or len(set(migration['reactivate']))!=len(migration['reactivate'])
                or set(migration['reactivate'])!=reactivated):
            raise ValueError('Invalid or stale explicit roster reactivation migration')
    elif reactivated:
        raise ValueError('Retired physical IDs require an explicit reactivation migration: '+str(sorted(reactivated)))
    for i,e in old.items():
        if i not in new or any(e[k]!=new[i][k] for k in ('family','vehicle_class')):
            raise ValueError('Physical ID deleted or rebound: '+str(i)+'; retain a tombstone')
    return old,new


def preflight_player_state(raw,previous,current,*,migration=None):
    old,new=preserve_reservations(previous,current,migration=migration)
    if not isinstance(raw,bytes) or not 1<=len(raw)<=4*1024*1024:raise ValueError('Bounded player-state bytes required')
    text=raw.decode('utf-8-sig')
    if '\0' in text or '<!' in text:raise ValueError('Unsupported save declarations')
    root=ET.fromstring(text)
    if root.tag!='Game' or root.find('Broker') is None:raise ValueError('Expected Game/Broker player state')
    selected={};inactive=[];active=[];classes={};seen=set()
    for v in root.iter('Value'):
        name=v.get('Name','');key=name.casefold();value=v.get('Value','')
        if key in seen:raise ValueError('Duplicate saved key: '+name)
        seen.add(key)
        if key.endswith('/gamesaved') and value.casefold() not in ('false','0',''):active.append(name)
        class_field=(key in ('masterrallye/vehicleclass','rallyecup/currentclass','frontend/rallyecup/currentclass') or re.fullmatch(r'masterrallye/car[0-5]/carclass',key))
        if class_field:
            if v.get('Type','').casefold()!='int' or not re.fullmatch(r'[0-2]',value):raise ValueError('Unsupported native saved class: '+name)
            classes[key]=int(value)
        identity=(re.fullmatch(r'frontend/(?:quickrace/car[01]|network/car0|network/selectedcar)',key)
            or re.fullmatch(r'(?:masterrallye|rallyecup)/playert[123]car[01]',key)
            or re.fullmatch(r'masterrallye/car[0-5]/carid',key))
        if not identity:
            if (not class_field and (key.startswith(('frontend/quickrace/car','frontend/network/selectedcar','frontend/network/car','masterrallye/playert','rallyecup/playert'))
                    or key.startswith('masterrallye/car') and key.endswith(('/carid','/carclass')))):
                raise ValueError('Unsupported saved vehicle identity field: '+name)
            continue
        if v.get('Type','').casefold()!='int' or not re.fullmatch(r'-?[0-9]+',value):raise ValueError('Invalid saved integer identity: '+name)
        i=int(value)
        if i==-1 and key.startswith('frontend/'):
            inactive.append(name);continue
        if i not in old or i not in new or new[i].get('retired',False):raise ValueError('Saved vehicle is unknown or retired: '+name+'='+value)
        player_class=re.search(r'/playert([123])car[01]$',key)
        if player_class and new[i]['vehicle_class']!='T'+player_class[1]:raise ValueError('Saved player class/CarID mismatch: '+name)
        selected[name]=i
    for name,i in selected.items():
        key=name.casefold()
        if re.fullmatch(r'masterrallye/car[0-5]/carid',key):
            paired=key[:-5]+'carclass'
            if paired in classes and new[i]['vehicle_class']!='T'+str(classes[paired]+1):raise ValueError('Saved CarClass/CarID mismatch: '+name)
    blocked=bool(active) and identity_digest(previous)!=identity_digest(current)
    return {'status':'BLOCKED_ACTIVE_CHAMPIONSHIP_REQUIRES_QUALIFICATION' if blocked else 'PASS_IDENTITY_MAPPING_ONLY',
        'selected_physical_ids':selected,'inactive_selection_keys':inactive,'active_competitions':active,
        'native_class_fields':classes,
        'save_bytes_modified':False,'runtime_qualified':False,
        'boundary':'Physical identity preservation; no save migration, native parser or gameplay proof'}
