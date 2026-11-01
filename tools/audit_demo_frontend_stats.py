"""Original registration stats for the reviewed shortlist, never physics values."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from audit_demo_identity import pc_records
from master_rallye.addon_sdk.demo_identity import localized_tables,localized_value

TARGETS={'Forester':'Forester','Rav4':'Rav4','Tomcat':'Wildcat','Newrav':'Newrav',
         'Landcruiser':'Landcruiser','Megane':'Megane','Tata':'Tata','Rav4Alpha':'Rav4Alpha'}


def audit(config,objdump):
    result={'schema':'demo-frontend-stats/1','field_order':['Speed','Acceleration','Handling','Endurance'],
            'boundary':'Original catalog display ratings, not measured performance or physics edits. No cross-family RAV4/Newrav transfer.',
            'sources':{},'vehicles':{name:{}for name in TARGETS}}
    for label in ('pc841','pc931'):
        spec=config['sources'][label];p=Path(spec['path']);raw=p.read_bytes();pin=hashlib.sha256(raw).hexdigest()
        if pin!=spec['sha256']:raise ValueError('Original executable differs: '+label)
        rows=pc_records(p,raw,spec['registration'],objdump);tables=localized_tables(raw)
        result['sources'][label]={'sha256':pin,'registration_range':spec['registration'],'records':len(rows)}
        for target,family in TARGETS.items():
            matches=[r for r in rows if (r['family']or'').casefold()==family.casefold()]
            if not matches:
                # Some Demo entries with unresolved names retain ratings and localized names
                # but use an unresolved model-family string. Only an exact unique
                # full catalog label establishes this narrower association.
                full={'Forester':'SUBARU FORESTER','Tata':'TATA SAFARI','Newrav':'TOYOTA RAV4'}.get(target)
                if full:
                    matches=[r for r in rows if r['family'] is None and localized_value(tables,53,r['id']).get('value')==full
                             and (target!='Newrav' or localized_value(tables,52,r['id']).get('value')=='RAV4 PICKUP')]
            if len(matches)!=1:
                result['vehicles'][target][label]={'status':'UNKNOWN','value':None,'reason':'No unique original named registration; do not substitute another vehicle or Alpha variant'};continue
            row=matches[0];value=row['stats']
            if len(value)!=4 or any(type(v)is not int or not 0<=v<=10 for v in value):raise ValueError('Original stats outside supported display schema')
            result['vehicles'][target][label]={'status':'PROVEN','value':value,'record':row,
                'localized':{str(c):localized_value(tables,c,row['id'])for c in (52,53)},
                'association':'named family'if row['family']else'exact localized catalog identity; model-family string is not resolved from file-backed bytes',
                'source_sha256':pin}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--objdump',type=Path,default=Path('C:/msys64/ucrt64/bin/objdump.exe'));a=p.parse_args()
    if a.output.exists():raise ValueError('Choose a fresh report')
    report=audit(json.loads(a.config.read_text()),a.objdump);a.output.write_text(json.dumps(report,indent=2)+'\n')
