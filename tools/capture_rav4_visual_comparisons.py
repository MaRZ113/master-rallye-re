"""Fixed native D3D9 OFF/ON/oblique wheel evidence, with no game launch."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.source_scene_preview import capture_views,viewer_command,capture_startup_info
from master_rallye import universal_vehicle_scene as u
from PIL import Image,ImageDraw


def run(root,viewer):
    root=root.absolute();viewer=viewer.absolute();report={}
    for label in ('A','B','C','D'):
        folder=root/label;preview=folder/'vehicle.mrpv';out=folder/'final-views'
        if out.exists():raise ValueError('Fresh captures required')
        out.mkdir()
        capture_views(viewer,preview,folder/'six-views-final',basis='source',cull='cw',model='race',
                      provenance=f'{label}: staged MR coordinates +Z front; authoring, no source runtime equivalence')
        records={}
        for name,view,extra in [('rear-off','rear',[]),('rear-on','rear',['--brake']),
            ('quarter-off','isometric',['--azimuth','225']),('quarter-on','isometric',['--azimuth','225','--brake']),
            ('wheel-oblique','isometric',['--model','wheel','--azimuth','-65','--elevation','12'])]:
            path=out/(name+'.bmp');cmd=viewer_command(viewer,preview,view=view,basis='source',cull='cw',capture=path,
                provenance=f'RAV4 {label} {name}: D3D9 MR approximation; D3D8 owner pending')+['--model','race']+extra
            subprocess.run(cmd,check=True,timeout=45,startupinfo=capture_startup_info(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            with Image.open(path)as im:im.convert('RGB').save(path.with_suffix('.png'))
            records[name]={'file':str(path.with_suffix('.png')),'sha256':u.sha(path.with_suffix('.png').read_bytes())}
        report[label]=records
    for title,names in [('lamp-comparison',('rear-off','rear-on','quarter-off','quarter-on')),('wheel-comparison',('wheel-oblique',))]:
        canvas=Image.new('RGB',(480*len(names),350*4),(30,30,30));draw=ImageDraw.Draw(canvas)
        for row,label in enumerate(('A','B','C','D')):
            for col,name in enumerate(names):
                im=Image.open(report[label][name]['file']);im.thumbnail((480,320));canvas.paste(im,(col*480,row*350+25));draw.text((col*480+5,row*350+5),label+' '+name,fill='white')
        canvas.save(root/(title+'.png'))
    (root/'capture-validation.json').write_bytes(u.canonical({'schema':'rav4-d3d9-visuals/1','captures':report,
        'view_convention':'Explicit native race model, staged+Z front; final-views/six-views-final replace earlier frontend/default/opposite-front diagnostics',
        'D3D8':'OWNER TEST PENDING'}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True)
    a=p.parse_args();run(a.root,a.viewer)
