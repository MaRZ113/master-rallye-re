"""Independent complete draw/state inventory bound to an existing demo census."""
import argparse
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from master_rallye import demo_vehicle_audit as audit
from master_rallye.addon_sdk import heritage_source as heritage
from master_rallye.universal_vehicle_scene import output_directory


def run(catalog,output):
    doc=json.loads(catalog.read_text(encoding='utf-8'));rows=[];cache={}
    output=output_directory(output,[catalog,*[Path(r['folder'])for r in doc['families']if 'folder'in r]])
    if not output.is_relative_to((ROOT/'.research-output').absolute()):raise ValueError('Private output required')
    for family in doc['families']:
        for name,model in family['models'].items():
            if model['format']!='DX':continue
            if 'folder'in family:raw=heritage.read(Path(family['folder'])/name)
            else:
                with zipfile.ZipFile(family['archive'])as archive:
                    member=family['relative_folder']+'/'+name
                    info=archive.getinfo(member)
                    if info.file_size>64*1024*1024:raise ValueError('Archive model budget')
                    raw=archive.read(info)
            if audit.sha(raw)!=model['sha256']:raise ValueError('Census source changed: '+family['id']+'/'+name)
            if model['sha256']not in cache:
                try:
                    state=audit.dx_evidence(raw,name)
                    if model.get('surface_sha256')and model['surface_sha256']!=state['surface_sha256']:raise ValueError('Decoded surface changed')
                    cache[model['sha256']]={k:state.get(k)for k in ('status','revision','native_draws','parser_errors','parser_warnings','collision_tags','collision_errors','collision_warnings','global_table_agrees')}
                except Exception as error:
                    if model['status']!='UNSUPPORTED':raise
                    cache[model['sha256']]={'status':'UNSUPPORTED','error':str(error)}
            rows.append({'family':family['id'],'model':name,'sha256':model['sha256'],'state':cache[model['sha256']]})
    result={'schema':'demo-native-state-inventory/1','models':rows,'unique_inputs':len(cache),
            'boundary':'Static original native groups/controllers and render flags; no behavior, damage event, glass zone or glow runtime newly tested.'}
    output.mkdir(parents=True);(output/'states.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.catalog,a.output);print('DX state inventories',len(r['models']))
