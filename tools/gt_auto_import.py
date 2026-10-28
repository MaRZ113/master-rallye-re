"""One-command GT3 import: automatic profile -> MR build -> Workshop author project.

Standard mode (default): LOD0 geometry fitted to the donor wheelbase, donor
MR tyres, GT rims (rim/tyre 0.80), stock seated crew, automatic breakable
glass and brake glow. Full mode: every decoded pass and GT tyre imagery.

Examples:
  python tools/gt_auto_import.py --source <gt3>/cars/day/sb0097.gz --donor <retail>/DataGx/Vehicles/Navara --output out/sb0097
  python tools/gt_auto_import.py --source sb0097.gz --donor ... --rank-donors <retail>/DataGx/Vehicles --profile-only --output out/p
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.gt_auto_profile import derive,rank_donors,detect_arches,body_triangles,resolve_callbacks,read_source
from master_rallye.gt3_vehicle import build


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--source',type=Path,required=True,help='GT3 cars/day member (.gz or decompressed)')
    p.add_argument('--donor',type=Path,required=True,help='retail MR family folder (physics/template donor)')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mode',choices=['standard','full'],default='standard')
    p.add_argument('--colour',type=int,default=0)
    p.add_argument('--rank-donors',type=Path,help='retail DataGx/Vehicles folder: print donor suggestions by wheelbase/track')
    p.add_argument('--profile-only',action='store_true',help='write auto-profile.json without building')
    p.add_argument('--author',action='store_true',help='also create a Workshop author project (needs --name/--manufacturer/--model)')
    p.add_argument('--name');p.add_argument('--manufacturer');p.add_argument('--model');p.add_argument('--family')
    p.add_argument('--class',dest='vehicle_class',choices=['T1','T2'],default='T2')
    a=p.parse_args()
    if a.output.exists():raise SystemExit('output exists: '+str(a.output))
    profile,report=derive(a.source,a.donor,mode=a.mode)
    result={'arches':report['arches'],'body_scale':report['body_scale'],'tyre_radius':report['tyre_radius'],'warnings':report['warnings']}
    if a.rank_donors:result['donor_ranking']=rank_donors(report['arches'],a.rank_donors)[:8]
    a.output.mkdir(parents=True);(a.output/'auto-profile.json').write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
    if not a.profile_only:
        built=build(a.source,a.donor,profile,a.output/'converted',colour=a.colour)
        result.update(outputs=built['outputs'],crew=built['crew'],native_features={k:built['native_features'].get(k)for k in ('status','zones','brake_triangles','reason')}if built['native_features']else None)
        if a.author:
            from master_rallye.addon_sdk.import_project import prepare
            from generate_vehicle_ui_previews import render_sources
            if not (a.name and a.manufacturer and a.model):raise SystemExit('--author needs --name, --manufacturer and --model')
            identity=a.output/'identity.json'
            identity.write_text(json.dumps({'addon':{'name':a.name,'family':a.family or ''.join(c for c in a.name.title()if c.isalnum())[:39],'manufacturer':a.manufacturer,'model':a.model}},indent=2))
            result['author_project']=str(prepare(a.output/'converted',a.donor,identity,a.output/'authoring',render_ui=render_sources,source_format='GT3 ModelSet1',vehicle_class=a.vehicle_class))
    (a.output/'auto-import-report.json').write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,default=str))


if __name__=='__main__':main()
