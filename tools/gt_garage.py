"""Read-only GT3 garage inventory. Private source paths; no bundled game data.

L0 = source association / bounded structural spans, never a render acceptance.
Checkpoint reuse requires the exact streaming SHA256 of the complete volume.
"""
import argparse
import collections
import hashlib
import json
import struct
from pathlib import Path
from gt3_ui_icon import inventory, read_indexed_member
from gt3_sound_lab import _strings, _tables, vehicle_mapping
from master_rallye.gt3_source import inspect_car
from master_rallye.gt3_colourways import catalog as colour_catalog

SCHEMA = 'gt-garage-inventory/1'

def implementation_identity():
    root=Path(__file__).resolve().parents[1]
    return {p:file_hash(root/p)for p in ('tools/gt_garage.py','tools/gt3_ui_icon.py','tools/gt3_sound_lab.py','src/master_rallye/gt3_source.py','src/master_rallye/gt3_colourways.py')}

def file_hash(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    tmp.replace(path)

def catalog(volume,rows,region='us'):
    """Verified GTAR30@48 -> GTAR5 key -> GTAR5@24 -> IDDB model code.

    This records physical offsets, without importing GT4 header names/units.
    Every association must resolve to an exact original cars/day member.
    """
    suffix='' if region=='jp' else '_'+region
    index={r['path']:r for r in rows};sources={}
    def member(name):
        key='database/'+name+suffix+'.db'
        b,s=read_indexed_member(volume,index[key],len(rows));sources[key]=s;return b
    db=_tables(member('paramdb'));labels=_strings(member('.id_db_str'));idsraw=member('.id_db_idx')
    if idsraw[:4]!=b'IDDB' or len(idsraw)!=8+16*struct.unpack_from('<I',idsraw,4)[0]:raise ValueError('GT3 IDDB span')
    ids={}
    for p in range(8,len(idsraw),16):
        key,i=struct.unpack_from('<Qq',idsraw,p)
        if key in ids or not 0<=i<len(labels):raise ValueError('GT3 IDDB key/index')
        ids[key]=labels[i]
    if db[5]['row_size']!=72 or db[30]['row_size']!=264:raise ValueError('unqualified GT3 source association rows')
    parts={}
    for at,row in db[5]['rows']:
        k=struct.unpack_from('<Q',row)[0]
        if k in parts:raise ValueError('duplicate GT3 model-part key')
        parts[k]=(at,row)
    result=vehicle_mapping(volume,region)
    cars={int(c['car_key'],16):c for c in result['vehicles']}
    mapped=[]
    for at,row in db[30]['rows']:
        key,part=struct.unpack_from('<Q',row)[0],struct.unpack_from('<Q',row,48)[0]
        c=dict(cars[key]);c['association_status']='MISSING INPUT'
        if part in parts:
            pat,pr=parts[part];mk=struct.unpack_from('<Q',pr,24)[0];code=ids.get(mk)
            c.update(model_code=code,association_evidence={'car_offset':at,'car_reference_offset':48,'table':5,'part_offset':pat,'model_reference_offset':24,'model_key':hex(mk)})
            if code and 'cars/day/'+code in index:c['association_status']='PASS'
        mapped.append(c)
    return {'region':region,'vehicles':mapped,'sources':{**result['sources'],**sources},'association_rule':'GTAR30@48 -> GTAR5 key@0 -> GTAR5@24 -> IDDB -> exact cars/day member'}

def scan(volume,output,limit=None,*,resume=False):
    volume=volume.resolve();before=volume.stat();identity={'path':str(volume),'bytes':before.st_size,'sha256':file_hash(volume)}
    identity['edition_files']={n:{'sha256':file_hash(volume.parent/n),'bytes':(volume.parent/n).stat().st_size}for n in ('SYSTEM.CNF','SCUS_971.02','CORE.GT3')if (volume.parent/n).is_file()}
    rows=inventory(volume);sources=[r for r in rows if r['path'].startswith(('cars/day/','cars/night/'))]
    result={'schema':SCHEMA,'source':identity,'implementation':implementation_identity(),'members':{},'levels':{'L0':'IN PROGRESS','L1':'NOT TESTED','L2':'NOT TESTED'},'boundary':'L0 structure is not selected-LOD, material, conversion, preview or gameplay qualification.'}
    if output.exists():
        if not resume:raise ValueError('output exists; use --resume for the same qualified source')
        old=json.loads(output.read_text(encoding='utf-8'))
        if any(old.get(k)!=result[k] for k in ('schema','source','implementation')):raise ValueError('checkpoint source/reader changed; choose a new output')
        result=old
    if 'catalogs' not in result:
        result['catalogs']={region:catalog(volume,rows,region)for region in ('us','eu','jp')}
        index={r['path']:r for r in rows}
        if all(n in index for n in ('database/carcolor.db','database/carcolor.sdb')):
            raw,cp=read_indexed_member(volume,index['database/carcolor.db'],len(rows));strings,sp=read_indexed_member(volume,index['database/carcolor.sdb'],len(rows));colours=colour_catalog(raw,strings)
            result['colour_sources']={'catalog':cp,'strings':sp}
            for c in result['catalogs'].values():
                for v in c['vehicles']:
                    key=int(v.get('association_evidence',{}).get('model_key','0'),16)
                    v['source_colourways']=colours['models'].get(key,{}).get('source_colourways',[])
    completed=0
    for row in sources:
        if row['path'] in result['members']:continue
        if limit is not None and completed>=limit:break
        try:
            raw,provenance=read_indexed_member(volume,row,len(rows))
            if not raw:item={'status':'MISSING INPUT','reason':'Original volume member decompresses to zero bytes','provenance':provenance}
            else:item=inspect_car(raw);item['provenance']=provenance
        except (ValueError,struct.error,UnicodeError) as e:
            item={'status':'UNSUPPORTED','reason':str(e),'L1':'NOT TESTED','L2':'NOT TESTED'}
        result['members'][row['path']]=item;completed+=1
        if completed%32==0:atomic_json(output,result)
    if (before.st_size,before.st_mtime_ns)!=(volume.stat().st_size,volume.stat().st_mtime_ns):raise ValueError('source changed during inventory')
    members=result['members'];result['levels']['L0']='PASS' if len(members)==len(sources) and all(x['status']=='PASS'for x in members.values()) else 'WARN'
    for c in result['catalogs'].values():
        for v in c['vehicles']:
            entry=members.get('cars/day/'+str(v.get('model_code')))
            v['model_status']=entry['status']if entry else 'MISSING INPUT'if v['association_status']!='PASS'else 'NOT TESTED'
            v['colourway_status']='PASS'if entry and entry['status']=='PASS'and len(v.get('source_colourways',[]))==entry['body']['source_colourway_count']else 'WARN'
            v['L1']=v['L2']='NOT TESTED'
    result['summary']={'volume_members':len(rows),'model_members':len(sources),'inspected':len(members),'status_counts':dict(collections.Counter(x['status']for x in members.values())),'unique_decoded_model_hashes':len({x['sha256']for x in members.values()if x['status']=='PASS'}),'catalog_entries':{r:len(c['vehicles'])for r,c in result['catalogs'].items()},'association_status':{r:dict(collections.Counter(v['association_status']for v in c['vehicles']))for r,c in result['catalogs'].items()}}
    atomic_json(output,result);return result['summary']

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vol',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--limit',type=int);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.limit is not None and a.limit<1:p.error('limit must be positive')
    print(json.dumps(scan(a.vol,a.output,a.limit,resume=a.resume),indent=2))

if __name__=='__main__':main()
