"""Course SDK LSM1 exporter for stock and custom layouts; no Proxy rebuild."""
import argparse
import json
from pathlib import Path
import sys

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,action='append',required=True)
    parser.add_argument('--course',action='append',required=True)
    parser.add_argument('--roles',type=Path,help='Optional JSON: course -> exact material label -> road/terrain/vegetation/static/exclude')
    parser.add_argument('--base',type=Path,help='Existing materials.lsm to retain stock/other layouts without re-reading their SDK sources')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
    from master_rallye.course_lighting import export_lighting_metadata
    r=export_lighting_metadata(args.source,args.course,args.output,json.loads(args.roles.read_text()) if args.roles else None,args.base.read_bytes() if args.base else None)
    print(f"{r['records']} material capabilities, 0 geometry records; {r['metadata_sha256']}")

if __name__=='__main__':main()
