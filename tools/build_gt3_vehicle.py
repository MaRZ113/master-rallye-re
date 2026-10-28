"""Build a private GT3 MR inspection package from an explicit editable profile."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.gt3_vehicle import build

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','donor','profile','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--colour',type=int,default=0);p.add_argument('--colour-database',type=Path);p.add_argument('--colour-strings',type=Path)
    a=p.parse_args();report=build(a.source,a.donor,json.loads(a.profile.read_text(encoding='utf-8')),a.output,colour=a.colour,colour_database=a.colour_database,colour_strings=a.colour_strings)
    print(json.dumps({'outputs':report['outputs'],'texture_budget_bytes':report['texture_budget']['cache_bytes'],'colourway':{k:report['colourway'][k]for k in ('source_index','latin_name')if k in report['colourway']}},indent=2))

if __name__=='__main__':main()
