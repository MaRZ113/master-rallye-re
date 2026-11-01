"""Private D3D9 neutral-source/restored/retail-reference inspection."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.demo_restoration import verify_inputs
from master_rallye.addon_sdk.heritage_source import stage_family
from master_rallye.preview_scene import stage_vehicle,presentation_wheels
from master_rallye.dx import parse_dx
from master_rallye.source_scene_preview import capture_views,viewer_command,capture_startup_info
from master_rallye.universal_vehicle_scene import output_directory
from PIL import Image,ImageDraw


def run(restoration,roots,viewer,output):
    m=json.loads((restoration/'restoration-manifest.json').read_text());source,*_=verify_inputs(m,roots)
    output=output_directory(output,[restoration,source,viewer]);output.mkdir(parents=True)
    original=stage_family(Path(roots['demo']),m['source_family'],output/'baseline',family_folder=source)
    reference_member=m['references'][m['frontend_reference']['car.dx']]['member']
    folders={'source':Path(original['package']),'restored':restoration/('workshop/builds/first/candidate/runtime/resource-root/DataGx/Vehicles/'+m['runtime_family']),
             'retail-reference':Path(roots['retail'])/'Data.sma_unpacked'/Path(reference_member).parent}
    report={};sheet=Image.new('RGB',(1600,990),'#24272c');draw=ImageDraw.Draw(sheet)
    for row,(label,folder)in enumerate(folders.items()):
        dest=output/label;dest.mkdir();models=[parse_dx(folder/n)for n in ('car.dx','complete.dx','wheel.dx')];profile=presentation_wheels(*models)
        labels=[g.root.group_label for g in models[0].draw_groups if g.root.tag==7 and g.root.group_label.startswith('screen')]
        profile['glass_states']={s:1 for s in labels};pp=dest/'profile.json';pp.write_text(json.dumps(profile));scene=dest/'scene.mrpv';stage_vehicle(folder/'car.dx',scene,profile=pp)
        views=capture_views(viewer,scene,dest/'six-views',basis='source',cull='cw',model='race',provenance=label+' original MR frame; offline D3D9, no gameplay claim');extra={}
        captures=[('frontend','isometric',['--model','frontend'])]
        if labels:captures.extend([('rear-on','rear',['--brake']),('quarter-on','isometric',['--brake','--azimuth','225'])])
        for name,view,flags in captures:
            target=dest/(name+'.bmp');cmd=viewer_command(viewer,scene,view=view,basis='source',cull='cw',capture=target,provenance=label+' neutral restoration; native state selected manually')+['--model','race']+flags
            subprocess.run(cmd,check=True,timeout=45,startupinfo=capture_startup_info(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));extra[name]=str(target)
        if labels:
            profile['glass_states']={s:2 for s in labels};pp=dest/'broken.json';pp.write_text(json.dumps(profile));broken=dest/'broken.mrpv';stage_vehicle(folder/'car.dx',broken,profile=pp)
            for view in ('front','left','right'):
                target=dest/('broken-'+view+'.bmp');cmd=viewer_command(viewer,broken,view=view,basis='source',cull='cw',capture=target,provenance='manual broken state, not an original damage trigger test')+['--model','race']
                subprocess.run(cmd,check=True,timeout=45,startupinfo=capture_startup_info(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));extra['broken-'+view]=str(target)
        for col,name in enumerate(('isometric','left','rear','rear-on')):
            path=Path(extra[name])if name in extra else dest/'six-views'/(name+'.bmp');draw.text((col*400+4,row*330+4),label+' '+name,fill='white')
            if path.exists():im=Image.open(path);im.thumbnail((395,300));sheet.paste(im,(col*400,row*330+25))
        report[label]={'views':views,'extra':extra,'wheel_proof':profile}
    sheet.save(output/'comparison.png');(output/'capture-report.json').write_text(json.dumps({'vehicles':report,'boundary':'Each source view auto-framed. Original versus derived material fidelity and rest pose only; no actual D3D8 gameplay.'},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('restoration','roots','viewer','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.restoration,json.loads(a.roots.read_text()),a.viewer,a.output)
