"""Fixed-camera private owner revision comparisons, using the existing D3D9 viewer."""
from pathlib import Path
import argparse,json,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.preview_scene import stage_vehicle,presentation_wheels
from master_rallye.dx import parse_dx
from master_rallye.source_scene_preview import viewer_command,capture_startup_info
from master_rallye.frontend_presentation import measure
from master_rallye.universal_vehicle_scene import output_directory
from PIL import Image,ImageDraw


def run(previous,current,retail,viewer,output):
    output=output_directory(output,[previous,current,retail,viewer]);output.mkdir(parents=True)
    roots={'previous':previous/'workshop/builds/first/candidate/runtime/resource-root/DataGx/Vehicles/DefForester',
           'corrected':current/'workshop/builds/first/candidate/runtime/resource-root/DataGx/Vehicles/DefForester',
           'WOOLDAND':retail/'DataGx/Vehicles/Forester'}
    report={};canvas=Image.new('RGB',(1500,900),'#24272c');text=ImageDraw.Draw(canvas)
    for row,(name,folder)in enumerate(roots.items()):
        dest=output/name;dest.mkdir();models=[parse_dx(folder/n)for n in ('car.dx','complete.dx','wheel.dx')]
        profile={**presentation_wheels(*models),'native_frontend_presentation':1};pp=dest/'profile.json';pp.write_text(json.dumps(profile))
        scene=dest/'scene.mrpv';stage_vehicle(folder/'car.dx',scene,profile=pp);captures={}
        for col,view in enumerate(('rear-on','quarter-on','frontend-fixed')):
            path=dest/(view+'.bmp')
            cmd=viewer_command(viewer,scene,view='rear',basis='source',cull='cw',capture=path,provenance=name+' owner correction; offline D3D9, not gameplay')
            if view=='frontend-fixed':
                # Fixed inspection camera: do not auto-frame away the Y change
                # or claim this is the animated original Vehicle Select view.
                cmd+=['--model','frontend','--camera-aspect','1.3333333333333333','--game-camera','0','2','-10','0','.7','0','45']
            else:
                cmd+=['--model','race','--brake','--zoom','2.3','--target','0','0.57','-2.25']
                if view=='quarter-on':cmd+=['--azimuth','225']
            subprocess.run(cmd,check=True,timeout=45,startupinfo=capture_startup_info(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            captures[view]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            im=Image.open(path);im.thumbnail((495,275));canvas.paste(im,(col*500,row*300+25));text.text((col*500+4,row*300+4),name+' '+view,fill='white')
        report[name]={'captures':captures,'frontend_projection':measure((folder/'complete.dx').read_bytes())}
    canvas.save(output/'comparison.png');(output/'capture-report.json').write_text(json.dumps({'vehicles':report,'boundary':'Same fixed frontend inspection camera and source scale, not the original animated menu camera; native projection metrics recorded separately. D3D9 material approximation. Actual corrected D3D8 effects pending owner.'},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('previous','current','retail','viewer','output'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();run(a.previous,a.current,a.retail,a.viewer,a.output)
