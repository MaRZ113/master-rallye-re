"""Owner-local Stable / independent upper brake validation; never launches D3D8."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.universal_vehicle_scene import sha,canonical,output_directory,load_scene
from master_rallye.workshop.service import WorkshopProject
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.preview_scene import stage_vehicle,logical_cases
from master_rallye.source_garage_pilot import compile_scene,pilot_profile,_enhance
from validate_fourrunner_visual_polish import pane,attrs


def hashes(folder):
    return {p.name:sha(p.read_bytes())for p in folder.iterdir()if p.suffix.lower()in('.dx','.dxt')}


def validate(previous,stable,upper,viewer,output,*,captures=True):
    projects={name:WorkshopProject(Path(path).absolute())for name,path in [('accepted-fixes',previous),('stable',stable),('upper-only',upper)]}
    protected=[]
    for p in projects.values():
        p.verify_inputs();s=Path(p.data['universal_source']['scene_path']);scene=load_scene(s)
        protected.extend([p.root,Path(p.data['source']),s.parent,scene['source']['root'],*scene['source'].get('protected_roots',[]),
                          Path(p.data['build_settings']['retail_sma']).parent,Path(p.data['build_settings']['retail_root'])])
    output=output_directory(Path(output).absolute(),protected);output.mkdir(parents=True)
    report={'schema':'fourrunner-stable-validation/1','checks':[],'captures':[],
        'owner_approval':'PENDING_NEW_STABLE_AND_UPPER_CANDIDATE_D3D8_TEST',
        'owner_previous_findings':['front side glass improved','lower rear brakes correct','windshield already good','playable/deformation/glass damage'],
        'exact_owner_tested_previous_candidate':'UNKNOWN: owner did not supply a path/manifest; findings are not generalized to every old preset.'}
    roots={k:Path(p.data['source_baseline']['assets']).parent.parent for k,p in projects.items()}
    old=projects['accepted-fixes'];base=projects['stable']
    assert hashes(roots['accepted-fixes']/'converted/assets')==hashes(roots['stable']/'converted/assets')
    assert hashes(old.assets)==hashes(base.assets)
    report['stable_exact_native_resources']=hashes(base.assets)
    report['checks'].append('Stable entire native DX/DXT assembly byte-identical to fixed-final, including original mirrors/rear glass/cockpit/crew/underbody and accepted pane/lower-lamp states')
    source={name:sha(Path(p.data['universal_source']['scene_path']).read_bytes())for name,p in projects.items()}
    assert len(set(source.values()))==1;report['source_scene_sha256']=source
    raws={name:(p.assets/'car.dx').read_bytes()for name,p in projects.items()}
    def case_geometries(raw,label,case):
        m=parse_dx_bytes(raw);g=source_geometry(m);cases,_=logical_cases(m)
        group=next(v for v in m.draw_groups if v.root.group_label==label)
        return [(g[i],m.physical_draws[i])for i in group.draw_indices if cases[i][1]==case]
    for name,p in projects.items():
        if name!='accepted-fixes':
            visual=json.loads((roots[name]/'mr-visual-kit.json').read_text())
            assert not any(visual['options'].values())and not visual['components']
        for label in ('screenfront','screenleft','screenright'):
            for case in (1,2):assert attrs(pane(raws[name],label,case))==attrs(pane(raws['accepted-fixes'],label,case)),(name,label,case)
        for resource in ('wheel.dx',*[f'wheel-source{i}.dx'for i in range(4)]):
            assert (p.assets/resource).read_bytes()==(old.assets/resource).read_bytes()
        physics=json.loads((Path(p.data['source'])/'physics-profile.json').read_text())
        previous_physics=json.loads((Path(old.data['source'])/'physics-profile.json').read_text())
        assert {k:v for k,v in physics.items()if k!='collision_fit'}=={k:v for k,v in previous_physics.items()if k!='collision_fit'}
        native=p.native_model_resources()['car.dx'];m=parse_dx_bytes(native)
        original=old.native_model_resources()['car.dx'];om=parse_dx_bytes(original)
        assert native[m.trailing.offset:m.collision.unparsed_offset]==original[om.trailing.offset:om.collision.unparsed_offset]
        a=case_geometries(raws['accepted-fixes'],'blight',1)[0][0];n=len(a.triangles)
        for case in (1,2):
            original_case=case_geometries(raws['accepted-fixes'],'blight',case);actual_case=case_geometries(raws[name],'blight',case)
            assert len(original_case)==len(actual_case)
            for (g,d),(gg,dd)in zip(original_case,actual_case):
                assert attrs(g)==attrs(type(gg)(gg.vertices,gg.triangles[:n]))
                assert d.texture_tuple==dd.texture_tuple and d.flags_0x20==dd.flags_0x20 and d.unknown_0x24==dd.unknown_0x24
    report['checks'].append('All three intact/broken glass zones; lower OFF/lit/glow attributes/materials; five original wheels; physics values and fitted collision identical in both new candidates')
    upper_report=json.loads((roots['upper-only']/'upper-brake-lamp.json').read_text());assert upper_report['enabled']
    report['upper_brake_lamp']=upper_report
    # The untouched Body faces retain exact attributes and winding even though
    # only the two original upper spoiler faces are partitioned for the option.
    old_ledger=json.loads((roots['stable']/'semantic-apertures.json').read_text())['body_partition_ledger']
    stable_body=source_geometry(parse_dx_bytes(raws['stable']))[0]
    new_body=source_geometry(parse_dx_bytes(raws['upper-only']))[0]
    expected=type(stable_body)(stable_body.vertices,tuple(t for t,row in zip(stable_body.triangles,old_ledger)if row['source_triangle']not in (595,596)))
    actual=type(new_body)(new_body.vertices,tuple(t for t,row in zip(new_body.triangles,upper_report['source_ledger']['outside'])if row['source_triangle']not in (595,596)))
    assert attrs(expected)==attrs(actual)
    report['checks'].append('Upper option partitions only original Body595/596; all other body faces/UVs/normals/winding remain exact')
    scene_path=Path(base.data['universal_source']['scene_path']);compiled=compile_scene(scene_path,pilot_profile(scene_path))
    for name in ('stable','upper-only'):
        p=projects[name];repeat=output/('determinism-'+name);repeat.mkdir();assets=repeat/'assets'
        shutil.copytree(Path(p.data['source_baseline']['assets']),assets)
        settings=p.data['build_settings'];_enhance(assets,compiled,Path(settings['retail_root']),repeat,
            retail_sma=Path(settings['retail_sma']),upper_brake_lamp=name=='upper-only')
        assert hashes(assets)==hashes(roots[name]/'converted/assets')
    report['checks'].append('Both complete source-to-native DX/DXT regenerations byte-identical')
    views=[('front',1,()),('rear-off',2,()),('rear-on',2,('--brake',)),('left',3,()),('right',6,()),('iso',4,()),
        ('mirror-left',4,('--target','.8','.94','.57','--azimuth','125','--elevation','10','--zoom','.16')),
        ('mirror-right',4,('--target','-.8','.94','.57','--azimuth','-125','--elevation','10','--zoom','.16')),
        ('cabin',4,('--target','.28','.92','.3','--zoom','.3','--azimuth','25','--elevation','8')),
        ('underbody',4,('--elevation','-24','--azimuth','140')),
        ('front-broken',1,()),('left-broken',3,()),('right-broken',6,()),
        ('upper-close-off',2,('--target','0','1.32','-2.1','--zoom','.22')),
        ('upper-close-on',2,('--target','0','1.32','-2.1','--zoom','.22','--brake'))]
    from PIL import Image,ImageChops
    viewer=Path(viewer).absolute();report['viewer_sha256']=sha(viewer.read_bytes())
    info=subprocess.STARTUPINFO();info.dwFlags|=subprocess.STARTF_USESHOWWINDOW;info.wShowWindow=0
    for name,p in (projects.items()if captures else []):
        folder=output/name;folder.mkdir()
        for label,preset,extra in views:
            profile=p.preview_profile()
            if label.endswith('broken'):profile['glass_states']={'screenfront':2,'screenleft':2,'screenright':2}
            profile_file=folder/(label+'-profile.json');profile_file.write_bytes(canonical(profile))
            scene_file=folder/(label+'.mrpv');source_file=p.assets/'car.dx';stage_vehicle(source_file,scene_file,profile=profile_file)
            bitmap=folder/(label+'.bmp');png=folder/(label+'.png')
            subprocess.run([str(viewer),'--scene',str(scene_file),'--source',str(source_file),'--model','race','--preset',str(preset),
                '--zoom','.68','--capture',str(bitmap),*extra],check=True,timeout=60,startupinfo=info)
            with Image.open(bitmap)as im:im.save(png)
            report['captures'].append({'variant':name,'view':label,'path':str(png),'sha256':sha(png.read_bytes())})
    if captures:
        for label,_,_ in views:
            assert (output/'stable'/(label+'.png')).read_bytes()==(output/'accepted-fixes'/(label+'.png')).read_bytes(),('Stable GPU comparison',label)
        report['checks'].append('All15 Stable D3D9 captures pixel-identical to fixed-final from the same camera/state')
        for label in ('upper-close-off','upper-close-on','rear-on'):
            a=Image.open(output/'stable'/(label+'.png')).convert('RGB');b=Image.open(output/'upper-only'/(label+'.png')).convert('RGB')
            report.setdefault('upper_gpu_difference_boxes',{})[label]=ImageChops.difference(a,b).getbbox()
    (output/'validation.json').write_bytes(canonical(report));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('previous','stable','upper','viewer','output'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--skip-captures',action='store_true');a=parser.parse_args()
    result=validate(a.previous,a.stable,a.upper,a.viewer,a.output,captures=not a.skip_captures)
    print(json.dumps({'checks':result['checks'],'captures':len(result['captures']),'owner_approval':result['owner_approval']},indent=2))
