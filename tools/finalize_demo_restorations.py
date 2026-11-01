"""Copy-on-write V-DEF4.1 build using accepted authors and Workshop services.

No source geometry compiler, vehicle registry or HUD writer is duplicated here.
All source/reference inputs remain private, immutable and independently pinned.
"""
from pathlib import Path
import argparse,copy,hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject
from master_rallye.addon_sdk.marker_colour import analyze
from master_rallye.addon_sdk.demo_restoration import restoration_physics,verify_retail_clone
from master_rallye.addon_sdk.project import read_sma_member
from master_rallye.addon_sdk.physics_profile import MEMBERS
from master_rallye.universal_vehicle_scene import output_directory
from audit_demo_identity import run as identity_audit


def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare(config_path,roots,output):
    config=json.loads(config_path.read_text());protected=[config_path,*map(Path,roots.values())]
    for entry in config['projects']:protected.extend(Path(entry[k])for k in('project','build'))
    output=output_directory(output,protected)
    if not output.is_relative_to(ROOT/'.research-output'):raise ValueError('Private output required')
    output.mkdir(parents=True)
    corpus=json.loads((ROOT/'research/vehicles/sdk/restorations/demo-identity-corpus.json').read_text())
    evidence=identity_audit(corpus,Path('C:/msys64/ucrt64/bin/objdump.exe'));write(output/'historical-evidence.json',evidence)
    ps2=[r for r in evidence['sources']['ps2']['registration']if r['family']=='Forester']
    if len(ps2)!=1:raise ValueError('Ambiguous original PS2 Forester marker')
    historical={30:{'status':'PROVEN','value':ps2[0]['rgba'],'bits':ps2[0]['rgba_bits'],'source_version':'PS2 SLES_509.06','source_sha256':corpus['sources']['ps2']['sha256'],
                    'evidence':'Original PS2 registration Forester ID8; same qualified Demo/PS2 Forester identity/body/art family. Cross-platform original colour, not a recovered PC931 RGBA record.'},
                31:{'status':'UNKNOWN','value':None,'evidence':'Retired Demo Rav4 absent from named931/PS2 table; Newrav is a distinct vehicle.'},
                32:{'status':'UNKNOWN','value':None,'evidence':'PC841 stride36 has no RGBA. Later PS2 Wildcat ID15 has exact colour but early841 identity association is unproven.'}}
    write(output/'historical-markers.json',historical)
    members={name:read_sma_member(Path(roots['retail'])/'Data.sma',name)for name in MEMBERS}
    m=json.loads((ROOT/'research/vehicles/sdk/restorations/tomcat-841.json').read_text());reports={};previous=config_path.parent
    for entry in config['projects']:
        car=entry['physical_id']
        if car not in historical:continue
        folder=output/str(car);folder.mkdir();source=folder/'author';shutil.copytree(entry['project'],source)
        history=json.loads((source/'historical-identity.json').read_text())if (source/'historical-identity.json').exists()else{};history['runtime_class']=entry.get('vehicle_class','T2');history['race_marker_audit']=historical[car];write(source/'historical-identity.json',history)
        if car==32:
            profile=json.loads((source/'physics-profile.json').read_text());profile={k:profile[k]for k in('profile_version','donor_family','runtime_family','source_sha256','overrides','notes')};profile['overrides']={}
            profile,physics=restoration_physics(m['physics'],profile,{'physics':(Path(roots['demo'])/'DataGame/vehicles.xml').read_bytes()},members,runtime_family=profile['runtime_family'])
            write(source/'physics-profile.json',profile);write(folder/'physics-evidence.json',physics);write(source/'restoration-manifest.json',m)
            heritage=source/'heritage-art';heritage.mkdir();shutil.copyfile(source/'ui/smallcarsheet.png',heritage/'original-isometric-smallcarsheet.png')
            for key in ('smallcarsheet','smallcarsheet_bank'):
                item=m['inputs'][key];original=Path(roots[item['root']])/item['path']
                if digest(original)!=item['sha256']:raise ValueError('Original heritage artwork source differs')
                shutil.copyfile(original,heritage/original.name)
        mode='HISTORICAL'if historical[car]['status']=='PROVEN'else'AUTO_DOMINANT'
        restoration_name={30:'forester-931',31:'rav4-931',32:'tomcat-841'}[car]
        manifest=json.loads((ROOT/'research/vehicles/sdk/restorations'/(restoration_name+'.json')).read_text())
        policy=copy.deepcopy(manifest['identity']['race_marker_policy']);policy['mode']=mode
        write(source/'race-marker.json',{'version':1,'historical':historical[car],'policy':policy})
        write(source/'restoration-manifest.json',manifest)
        p=WorkshopProject.create(source,folder/'workshop',kind='addon')
        p.configure_build({'roster_candidate':str(previous),'retail_sma':str(Path(roots['retail'])/'Data.sma'),'retail_root':str(Path(roots['retail'])/'Data.sma_unpacked')})
        analysis=p.marker_recalculate();p.marker_select(mode,analysis=analysis)
        info=p.ai_inspect();enabled={key:key in info['supported_modes']for key in info['eligibility']};p.ai_update(enabled)
        if car==32:
            hud=p.art_generate(role='smallcarsheet',azimuth=-90.,elevation=0.);p.art_apply(hud)
            write(folder/'hud-reconstruction.json',{'status':'RECONSTRUCTED','role':'smallcarsheet','historical_menu_preserved':True,'heritage_isometric_preserved':True,'render':hud})
        p.build(folder/'workshop/builds/first',sdk_root=ROOT,log=print)
        previous=folder/'workshop/builds/first/candidate'
        reports[str(car)]={'workshop':str(p.root),'marker':p.marker_inspect(),'analysis':analysis,'ai':p.ai_inspect(),'candidate':str(previous)}
        if car==32:
            reports[str(car)]['retail_clone']=verify_retail_clone(members,{name:(previous/'runtime/resource-root'/name).read_bytes()for name in MEMBERS},donor_family='Wildcat',runtime_family='DefTomcat')
    write(output/'result.json',{'status':'OFFLINE_CANDIDATE_OWNER_TEST_PENDING','vehicles':reports,'candidate':str(previous),'previous_roster':str(config_path)})
    for car,report in reports.items():
        project=Path(report['workshop']);(output/f'Open-{car}-Workshop.cmd').write_text('@echo off\n"'+sys.executable+'" "'+str(ROOT/'tools/rally_workshop.py')+'" --project "'+str(project)+'" --workspace "'+str(output/'workspace')+'"\nif errorlevel 1 pause\n')
    return previous


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('previous','roots','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();print(prepare(args.previous.resolve(),json.loads(args.roots.read_text()),args.output.resolve()))
