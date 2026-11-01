"""Private fixed-view D3D9 source/restoration/technical-donor comparisons."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.heritage_source import stage_family
from master_rallye.preview_scene import stage_vehicle,presentation_wheels
from master_rallye.dx import parse_dx
from master_rallye.source_scene_preview import capture_views,viewer_command,capture_startup_info
from master_rallye.universal_vehicle_scene import output_directory
from PIL import Image,ImageDraw


def run(restoration,demo,rebaked,retail,viewer,output):
    output=output_directory(output,[restoration,demo,rebaked,retail,viewer]);output.mkdir(parents=True)
    original=stage_family(demo,'Forester',output/'baseline',family_folder=rebaked)
    folders={'Demo-original':Path(original['package']),'Demo-restored':restoration/'workshop/builds/first/candidate/runtime/resource-root/DataGx/Vehicles/DefForester','WOOLDAND-technical':retail/'DataGx/Vehicles/Forester'}
    report={}
    for label,folder in folders.items():
        dest=output/label;dest.mkdir();scene=dest/'vehicle.mrpv'
        models=[parse_dx(folder/n)for n in ('car.dx','complete.dx','wheel.dx')]
        config=presentation_wheels(*models)
        labels=[g.root.group_label for g in models[0].draw_groups if g.root.tag==7 and g.root.group_label.startswith('screen')]
        config['glass_states']={name:1 for name in labels};profile=dest/'profile.json';profile.write_text(json.dumps(config))
        staged=stage_vehicle(folder/'car.dx',scene,profile=profile)
        views=capture_views(viewer,scene,dest/'six-views',basis='source',cull='cw',model='race',provenance=label+' native MR frame +Z front; D3D9 offline; owner D3D8 pending')
        extra={}
        captures=[('frontend','isometric',['--model','frontend'])]
        if labels:captures += [('rear-on','rear',['--brake']),('quarter-on','isometric',['--brake','--azimuth','225'])]
        for name,view,flags in captures:
            target=dest/(name+'.bmp');cmd=viewer_command(viewer,scene,view=view,basis='source',cull='cw',capture=target,provenance=label+' '+name+' offline')+['--model','race']+flags
            subprocess.run(cmd,check=True,timeout=45,startupinfo=capture_startup_info(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));extra[name]=str(target)
        if labels:
            config['glass_states']={name:2 for name in labels};broken=dest/'broken-profile.json';broken.write_text(json.dumps(config));broken_scene=dest/'broken.mrpv';stage_vehicle(folder/'car.dx',broken_scene,profile=broken)
            for view in ('front','left','right'):
                target=dest/('broken-'+view+'.bmp');cmd=viewer_command(viewer,broken_scene,view=view,basis='source',cull='cw',capture=target,provenance=label+' manual broken state; no damage trigger emulation')+['--model','race']
                subprocess.run(cmd,check=True,timeout=45,startupinfo=capture_startup_info(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));extra['broken-'+view]=str(target)
        report[label]={'views':views,'extra':extra,'assembly':staged['profile'],'bounds':staged['bounds']}
    canvas=Image.new('RGB',(1600,3*330),'#24272c');draw=ImageDraw.Draw(canvas)
    for row,(label,r)in enumerate(report.items()):
        for col,name in enumerate(('isometric','left','rear','rear-on')):
            path=r['extra'].get(name)if name=='rear-on'else r['views'].get('captures',{}).get(name)
            if not path:
                # capture_views retains hashes and paths together in its view rows.
                path=output/label/'six-views'/(name+'.bmp')
            if isinstance(path,dict):path=path.get('path',path.get('file'))
            draw.text((col*400+5,row*330+5),label+' '+name,fill='white')
            if path and Path(path).is_file():
                with Image.open(path)as image:image.thumbnail((395,300));canvas.paste(image,(col*400,row*330+25))
            elif label=='Demo-original'and name=='rear-on':draw.text((col*400+5,row*330+135),'Original Demo: no native ON switch',fill='#c7b897')
    canvas.save(output/'comparison.png')
    (output/'capture-report.json').write_text(json.dumps({'schema':'vdef1-d3d9/1','vehicles':report,'boundary':'Source geometry unchanged; each view auto-framed. Bounds/measurements, not equal-sized panels, determine dimensional differences. Manual broken/ON states do not test native triggers.'},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('restoration','demo','rebaked','retail','viewer','output'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();run(a.restoration,a.demo,a.rebaked,a.retail,a.viewer,a.output)
