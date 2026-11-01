"""Separate serialization/cooker differences from recovered source geometry."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.demo_dx import compare_demo_dx
from master_rallye.addon_sdk import heritage_source as h
from master_rallye.universal_vehicle_scene import output_directory


def run(catalog,output):
    doc=json.loads(catalog.read_text(encoding='utf-8'));rows=doc['families'];result=[];seen=set()
    protected=[catalog,*[Path(r['folder'])for r in rows if 'folder'in r]]
    output=output_directory(output,protected)
    if not output.is_relative_to((ROOT/'.research-output').absolute()):raise ValueError('Private output required')
    for row in rows:
        if row['label']not in('pcg-rebaked','nov-local'):continue
        for name,model in row['models'].items():
            if model['format']!='DX'or model['role']not in('car','complete','wheel'):continue
            gxms=[m['sha256']for m in row['models'].values()if m['format']=='GXM'and m['role']==model['role']]
            for original in rows:
                if not original['label'].startswith('shipped'):continue
                source_gxm=[m['sha256']for m in original['models'].values()if m['format']=='GXM'and m['role']==model['role']]
                common=set(gxms)&set(source_gxm)
                if not common:continue
                source_dx=next(((n,m)for n,m in original['models'].items()if m['format']=='DX'and m['role']==model['role']),None)
                record={'candidate':row['id']+'/'+name,'original':original['id'],'role':model['role'],'identical_gxm_source_sha256':sorted(common)}
                if not source_dx:record.update(status='MISSING_INPUT',boundary='Same source GXM, no shipped DX counterpart for this role')
                else:
                    n,m=source_dx;pair=(record['candidate'],original['id']+'/'+n)
                    if pair in seen:continue
                    seen.add(pair)
                    first=h.read(Path(original['folder'])/n);second=h.read(Path(row['folder'])/name)
                    if h.sha(first)!=m['sha256']or h.sha(second)!=model['sha256']:raise ValueError('Census input changed')
                    try:
                        diff=compare_demo_dx(first,second,first_source=pair[1],second_source=pair[0])
                        record.update(status='COMPARED_ORIGINAL_BUFFERS',difference=diff,
                                      boundary='Legacy structurally-different verdict includes format headers. It must not be equated with new vehicle geometry; consult positions, UVs and decoded surface evidence.')
                    except Exception as e:record.update(status='UNSUPPORTED',error=str(e))
                result.append(record)
    report={'schema':'demo-cooker-source-differences/1','pairs':result,'boundary':'Same original GXM bytes establish input correspondence, not proof of which executable performed the bake.'}
    output.mkdir(parents=True);(output/'cooker-differences.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalog',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();r=run(a.catalog,a.output);print('Original/candidate pairs',len(r['pairs']))
