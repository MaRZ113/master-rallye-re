"""Author opt-in regional atmosphere data from Course SDK scene provenance."""
from pathlib import Path
import argparse,collections,hashlib,html,json,re

def canonical(s):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,63}',s):raise ValueError('unsafe scene/region identifier: '+s)
    return s.casefold()

def infer_region(folders,regions):
    votes=[]
    for folder in folders:
        name=canonical(folder)
        if name.startswith('inv'):name=name[3:]
        found=[region for region in regions if name.startswith(canonical(region))]
        if len(found)!=1:return None
        votes.append(found[0])
    return votes[0] if votes and len(set(votes))==1 else None

def export(bindings,presets,output,stock=False):
    if output.exists():raise ValueError('fresh output required')
    if presets.get('schema')!=1 or not presets.get('regions'):raise ValueError('preset schema')
    regions=presets['regions'];lines=['; ATMOSPHERE2.8 process snapshot. No automatic material admission.','[Regions]'];report=[];seen=set()
    for row in bindings['bindings']:
        scene=row['scene'];key=canonical(scene)
        if key in seen:raise ValueError('duplicate scene')
        seen.add(key);region=infer_region(row['folders'],regions)
        if region:lines.append(scene+'='+region)
        report.append(dict(scene=scene,folders=row['folders'],region=region,status='AUTHORED_CANDIDATE_RUNTIME_PENDING' if region else 'BASE_SETTINGS_FALLBACK_MIXED_OR_UNKNOWN',binding_evidence='SDK_SOURCE_FOLDER_COUNTRY_PREFIX_NOT_VISUAL_CONFIRMATION',scene_xml_sha256=row.get('scene_xml_sha256')))
    for region,row in regions.items():
        canonical(region);lines+=['','[Region:'+region+']']
        values=dict(row['settings'])
        if stock:values['SkyPreset']=str(row['stock_sky'])
        lines += [k+'='+str(v) for k,v in values.items()]
    output.mkdir(parents=True);data=('\n'.join(lines)+'\n').encode();(output/'regions.ini').write_bytes(data)
    result=dict(schema=1,status='OFFLINE_AUTHORING_GAMEPLAY_PENDING',sky_mode='ORIGINAL_STOCK_FIXED_PRESETS' if stock else 'EXISTING_UNMODIFIED_GT3_BASE3',catalog_sha256=hashlib.sha256(data).hexdigest(),counts=dict(collections.Counter(r['region'] or 'Base fallback' for r in report)),scenes=report,regions=regions,geometry_hash_allowlist=False)
    (output/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rows=''.join('<tr><td>'+html.escape(r['scene'])+'</td><td>'+html.escape(r['region'] or 'Base fallback')+'</td><td>'+html.escape(', '.join(r['folders']))+'</td><td>NOT TESTED</td></tr>' for r in report)
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Regional atmospheres</title><style>body{font:16px system-ui;background:#18202a;color:#ddd;margin:30px}td,th{padding:9px;text-align:left;border-bottom:1px solid #536}</style><h1>ATMOSPHERE2.8</h1><p>Authoring candidates. No gameplay/visual parity claim. Sky textures are not recolored.</p><table><tr><th>Scene</th><th>Region</th><th>Source folders</th><th>Game</th></tr>'+rows+'</table>',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bindings',type=Path,required=True);p.add_argument('--presets',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--stock-skies',action='store_true');a=p.parse_args()
    r=export(json.loads(a.bindings.read_text()),json.loads(a.presets.read_text()),a.output,a.stock_skies);print(json.dumps(r['counts']))
