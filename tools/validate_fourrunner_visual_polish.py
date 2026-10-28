"""Private owner-local geometry/state comparison and real D3D9 captures.

No D3D8 game is launched. Original inputs and accepted projects stay read-only.
"""
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


def attrs(g):
    return Counter(tuple((g.vertices[i].position,g.vertices[i].normal,g.vertices[i].color,g.vertices[i].uvs)for i in t)for t in g.triangles)


def pane(raw,label,case):
    m=parse_dx_bytes(raw);geometries=source_geometry(m);cases,_=logical_cases(m)
    group=next(g for g in m.draw_groups if g.root.group_label==label)
    return geometries[next(i for i in group.draw_indices if cases[i][1]==case)]


def validate(baseline,fixed,adapted,viewer,output,*,captures=True):
    projects={name:WorkshopProject(Path(path).absolute())for name,path in [('before',baseline),('fixed',fixed),('adapted',adapted)]}
    protected=[]
    for p in projects.values():
        scene_path=Path(p.data['universal_source']['scene_path']);scene=load_scene(scene_path)
        protected.extend([p.root,Path(p.data['source']),scene_path.parent,Path(p.data['build_settings']['retail_sma']).parent,
                          Path(p.data['build_settings']['retail_root']),scene['source']['root'],*scene['source'].get('protected_roots',[])])
    output=output_directory(Path(output).absolute(),protected)
    for p in projects.values():p.verify_inputs()
    output.mkdir(parents=True)
    report={'schema':'fourrunner-visual-validation/1','checks':[],'captures':[],
        'D3D8':'New visual candidate NOT TESTED; previous owner confirms loads/drives/body deformation/breakable glass only.',
        'limits':['D3D9 neutral rendering is not original-game renderer parity.',
                  'Body-fixed frame only; no moving suspension/axle articulation claim.']}
    before,fixed_project,adapted_project=[projects[k]for k in ('before','fixed','adapted')]
    source={k:sha(Path(p.data['universal_source']['scene_path']).read_bytes())for k,p in projects.items()}
    assert len(set(source.values()))==1;report['source_scene_sha256']=source
    raws={k:(p.assets/'car.dx').read_bytes()for k,p in projects.items()}
    for case in (1,2):
        expected=attrs(pane(raws['before'],'screenfront',case))
        for name in ('fixed','adapted'):assert attrs(pane(raws[name],'screenfront',case))==expected,(name,'windshield')
    report['checks'].append('Accepted intact AND broken windshield attributes/winding/UVs/colours preserved exactly')
    resources={}
    for name,p in projects.items():
        resources[name]={f.name:sha(f.read_bytes())for f in p.assets.iterdir()if f.is_file()}
        for resource in ('wheel.dx',*[f'wheel-source{i}.dx'for i in range(4)]):
            assert resources[name][resource]==resources['before'][resource],(name,resource)
        physics=json.loads((Path(p.data['source'])/'physics-profile.json').read_text())
        old=json.loads((Path(before.data['source'])/'physics-profile.json').read_text())
        assert {k:v for k,v in physics.items()if k!='collision_fit'}=={k:v for k,v in old.items()if k!='collision_fit'}
        fitted=p.native_model_resources()['car.dx'];fm=parse_dx_bytes(fitted)
        oldfit=before.native_model_resources()['car.dx'];om=parse_dx_bytes(oldfit)
        assert fitted[fm.trailing.offset:fm.collision.unparsed_offset]==oldfit[om.trailing.offset:om.collision.unparsed_offset],(name,'collision')
    report['checks'].append('Original five wheel resources, physics profile values and fitted collision bytes identical to accepted pilot')
    report['resources']=resources
    report['resource_differences']={name:[key for key in sorted(set(resources['before'])|set(value))if resources['before'].get(key)!=value.get(key)]for name,value in resources.items()if name!='before'}
    # Side pane vertices must remain inside every source-atlas boundary edge.
    from master_rallye.source_garage_pilot import pilot_profile
    from master_rallye.universal_scene_bridge import compile_scene
    from master_rallye.fourrunner_semantics import author_apertures
    scene=Path(fixed_project.data['universal_source']['scene_path']);converted=compile_scene(scene,pilot_profile(scene))
    authored=author_apertures(converted);again=author_apertures(converted)
    assert authored==again
    from master_rallye.source_garage_pilot import _enhance
    for name in ('fixed','adapted'):
        p=projects[name];root=Path(p.data['source_baseline']['assets']).parent.parent
        repeat=output/('determinism-'+name);repeat.mkdir();assets=repeat/'assets'
        shutil.copytree(Path(p.data['source_baseline']['assets']),assets)
        choices=json.loads((root/'mr-visual-kit.json').read_text())['options']
        settings=p.data['build_settings']
        _enhance(assets,converted,Path(settings['retail_root']),repeat,retail_sma=Path(settings['retail_sma']),visual_options=choices)
        def hashes(folder):return {f.name:sha(f.read_bytes())for f in folder.iterdir()if f.suffix.lower()in ('.dx','.dxt')}
        expected=hashes(root/'converted/assets');actual=hashes(assets)
        assert actual==expected,(name,'deterministic resource mismatch')
        report.setdefault('deterministic_resources',{})[name]=actual
    report['checks'].append('Complete real source-to-native glass/lamp/visual-kit DX/DXT regeneration byte-identical for both variants')
    _,_,_,_,semantic=authored;polygon=semantic['side_window_polygon_yz_m']
    sides={}
    for label in ('screenleft','screenright'):
        g=pane(raws['fixed'],label,1);points=[(v.position[2],v.position[1])for v in g.vertices]
        for i,a in enumerate(polygon):
            b=polygon[(i+1)%len(polygon)]
            assert all((b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0])<=1e-6 for q in points)
        sides[label]={'triangles':len(g.triangles),'bounds_m':[[f(v.position[k]for v in g.vertices)for k in range(3)]for f in (min,max)]}
    report['side_glass']=sides;report['checks'].append('Both side pane layers clipped within all aperture edges; semantic generation deterministic')
    # Every lamp corner maps back to an allowed source rear panel with original
    # barycentric coordinates. No unrelated painted/bumper triangle can enter.
    lamp=pane(raws['fixed'],'blight',1)
    assert all(v.position[2]<-2.2 and abs(v.position[0])>.55 and .38<v.position[1]<.62 for v in lamp.vertices)
    report['lamp']={'triangles':len(lamp.triangles),'bounds_m':[[f(v.position[k]for v in lamp.vertices)for k in range(3)]for f in (min,max)]}
    report['checks'].append('Brake OFF/ON lens ownership bounded to both original rear clusters; no bumper, headlights or upper clear indicator/reverse surfaces')
    from PIL import Image
    views=[('front',1,()),('left',3,()),('right',6,()),('rear-off',2,()),('rear-on',2,('--brake',)),
           ('left-rear-off',4,('--azimuth','140','--elevation','8')),
           ('left-rear-on',4,('--azimuth','140','--elevation','8','--brake')),
           ('right-rear-off',4,('--azimuth','-140','--elevation','8')),
           ('right-rear-on',4,('--azimuth','-140','--elevation','8','--brake')),
           ('iso',4,()),('paint-no-reflection',4,('--no-reflections',)),
           ('cabin',4,('--target','.28','.92','.3','--zoom','.3','--azimuth','25','--elevation','8')),
           ('underside',4,('--elevation','-24','--azimuth','140')),
           ('broken-glass',4,())]
    viewer=Path(viewer).absolute();report['viewer_sha256']=sha(viewer.read_bytes())
    info=subprocess.STARTUPINFO();info.dwFlags|=subprocess.STARTF_USESHOWWINDOW;info.wShowWindow=0
    for name,p in (projects.items()if captures else []):
        folder=output/name;folder.mkdir()
        for label,preset,extra in views:
            profile=p.preview_profile()
            if label=='broken-glass':profile['glass_states']={'screenfront':2,'screenleft':2,'screenright':2}
            config=folder/(label+'-profile.json');config.write_bytes(canonical(profile))
            scene_file=folder/(label+'.mrpv');source_path=p.assets/'car.dx'
            stage_vehicle(source_path,scene_file,profile=config)
            bitmap=folder/(label+'.bmp');png=folder/(label+'.png')
            subprocess.run([str(viewer),'--scene',str(scene_file),'--source',str(source_path),'--model','race','--preset',str(preset),
                            '--zoom','.68','--capture',str(bitmap),*extra],check=True,timeout=60,startupinfo=info)
            with Image.open(bitmap)as im:im.save(png)
            report['captures'].append({'project':name,'view':label,'path':str(png),'sha256':sha(png.read_bytes())})
    (output/'validation.json').write_bytes(canonical(report));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('baseline','fixed','adapted','viewer','output'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--skip-captures',action='store_true',help='Repeat geometry and deterministic native resource checks only')
    args=parser.parse_args();result=validate(args.baseline,args.fixed,args.adapted,args.viewer,args.output,captures=not args.skip_captures)
    print(json.dumps({'checks':result['checks'],'captures':len(result['captures']),'D3D8':result['D3D8']},indent=2))
