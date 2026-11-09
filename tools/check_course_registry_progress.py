"""Read-only owner check after finishing new QuickRace registrations."""
import argparse
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


def values(path):
    entries={}
    for value in ET.parse(path).iter('Value'):
        key=value.get('Name')
        if key in entries:raise ValueError('Ambiguous duplicate save key: '+str(key))
        raw=value.get('Value');kind=value.get('Type','').lower()
        if kind=='float':
            raw=float(raw)
            if not math.isfinite(raw):raise ValueError('Nonfinite saved value: '+str(key))
        elif kind=='int':raw=int(raw)
        elif kind=='bool':
            if raw.lower() not in ('true','false','0','1'):raise ValueError('Invalid saved Bool')
            raw=raw.lower() in ('true','1')
        entries[key]=raw
    return entries


def check(before,after,catalog,*,require_new_record=False):
    old,new=values(before),values(after)
    protected=[k for k in old if k.startswith('Progress/BestTimes/') and '/CourseRegistryV1/' not in k
               or k.startswith('Progress/Won/') or k.startswith('Won/')]
    changed=[k for k in protected if old[k]!=new.get(k)]
    if changed:raise ValueError('Original progress changed during new-QuickRace-only test: '+', '.join(changed))
    results=[]
    for r in catalog['races'][39:]:
        key='Progress/BestTimes/CourseRegistryV1/'+r['progress_key']
        if key not in new:raise ValueError('New progress key missing after save: '+key)
        results.append({'race_id':r['id'],'key':key,'before':float(old[key]),'after':float(new[key]),'record_improved':float(new[key])<float(old[key])})
    if require_new_record and not any(r['record_improved'] for r in results):raise ValueError('No new record persisted; gameplay/save qualification still pending')
    return {'status':'PASS_NEW_QUICKRACE_PROGRESS_KEYS','original_progress_keys_unchanged':len(protected),
            'new_records':results,'boundary':'Save comparison only; does not establish driving/AI correctness'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['before','after','catalog']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--require-new-record',action='store_true');a=p.parse_args()
    print(json.dumps(check(a.before,a.after,json.loads(a.catalog.read_text()),require_new_record=a.require_new_record),indent=2))
