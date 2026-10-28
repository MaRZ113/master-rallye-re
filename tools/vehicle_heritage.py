"""Native MR edition catalog, read-only preview staging and independent authoring."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.heritage_source import inventory,compare_editions,create_author,stage_family,apply_features


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('catalog');c.add_argument('--source',type=Path,action='append',required=True);c.add_argument('--retail',type=Path,required=True);c.add_argument('--output',type=Path,required=True)
    for mode in ('preview','create'):
        a=sub.add_parser(mode);a.add_argument('--source',type=Path,required=True);a.add_argument('--family',required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--family-folder',type=Path,help='explicit family folder for nested layouts, e.g. DataGx/Vehicles/841/Forester')
        if mode=='create':
            for field in ('name','runtime-family'):a.add_argument('--'+field,required=True)
            a.add_argument('--physics-donor',default='auto',help="retail physics family, or 'auto' = same-named retail family")
            a.add_argument('--audio-profile',type=int,required=True);a.add_argument('--class',dest='vehicle_class',choices=['T1','T2'],default='T2');a.add_argument('--features',type=Path,help='explicit native feature recipe (overrides automatic features)');a.add_argument('--no-auto-features',action='store_true',help='plain native import without automatic brake glow / breakable glass');a.add_argument('--strict-edition',action='store_true',help='reject executables/assets without an original fingerprint');a.add_argument('--retail-sma',type=Path,required=True)
    a=p.parse_args()
    if a.command=='catalog':
        if a.output.exists():raise ValueError('Fresh catalog output required')
        catalogs=[inventory(root)for root in a.source];retail=inventory(a.retail,retail=True);value={'catalog_version':1,'sources':catalogs,'retail':retail,'crosswalk':compare_editions(catalogs,retail)};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(value,indent=2)+'\n');print('PASS_EDITION_CATALOG',len(value['crosswalk']))
    elif a.command=='preview':print(json.dumps(stage_family(a.source,a.family,a.output,family_folder=a.family_folder),indent=2))
    else:
        value=create_author(a.source,a.family,a.output,name=a.name,runtime_family=a.runtime_family,physics_donor=a.physics_donor,stock_audio_profile_id=a.audio_profile,vehicle_class=a.vehicle_class,retail_sma=a.retail_sma,features=None if (a.features or a.no_auto_features) else 'auto',allow_unqualified_edition=not a.strict_edition,family_folder=a.family_folder)
        if a.features:value['features']=apply_features(a.output,a.features)
        print(json.dumps(value,indent=2))


if __name__=='__main__':main()
