"""Owner-local conservation, repeat and capture checks for Michelin scenes."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_adapters import michelin as m
from master_rallye.source_scene_preview import stage_source_scene,capture_views


def run(source,scenes,output,viewer):
    from PIL import Image,ImageDraw
    output=u.output_directory(output,[source,scenes]);output.mkdir(parents=True)
    rows=[]
    for archive in m.QUALIFIED:
        name=archive[:-4];root=scenes/name
        for selection in ['assembly',*['LOD%d'%i for i in range(4)]]:
            p=root/selection/'scene/scene.json';s=u.load_scene(p)
            repeat=output/'repeat'/name/selection
            r=m.assemble(source,archive,repeat,tyre_choice=0) if selection=='assembly' else m.recover(source,archive,int(selection[-1]),repeat)
            assert u.sha(u.read_bounded(p,u.MAX_JSON_BYTES))==r['scene_sha256']
            assert (p.parent/'manifest.json').read_bytes()==(repeat/'manifest.json').read_bytes()
            first=output/'preview-repeat'/name/(selection+'.mrpv');stage_source_scene(s,first,scene_root=p.parent)
            assert first.read_bytes()==(p.parent.parent/'preview.mrpv').read_bytes()
            for resource in s['source']['resources']:
                assert u.sha(u.read_bounded(p.parent/resource['snapshot_path'],u.MAX_OUTPUT_BYTES))==resource['sha256']
            rows.append({'car':name,'selection':selection,'scene_sha256':r['scene_sha256'],'counts':r['counts'],
                         'exact_repeat':True,'preview_repeat':True,'original_sidecars_exact':True,
                         'normal_fallback_corners':sum(len(x['source'].get('face_normal_fallbacks',[]))for x in s['meshes'])})
        # Six measured neutral views, no independent per-view scale changes.
        canvas=Image.new('RGB',(1440,750),(30,30,30));draw=ImageDraw.Draw(canvas)
        for i,view in enumerate(('front','rear','left','right','top','isometric')):
            with Image.open(root/'assembly/views'/(view+'.png')) as im:
                im=im.convert('RGB');im.thumbnail((480,340));x=(i%3)*480;y=(i//3)*375
                canvas.paste(im,(x,y+25));draw.text((x+8,y+5),name+' '+view+' | static assembly; L2 WARN',fill='white')
        canvas.save(output/(name+'-six-views.png'))
        canvas=Image.new('RGB',(1200,800),(30,30,30));draw=ImageDraw.Draw(canvas)
        for i in range(4):
            with Image.open(root/('LOD%d'%i)/'views/isometric.png') as im:
                im=im.convert('RGB');im.thumbnail((600,370));x=i%2*600;y=i//2*400;canvas.paste(im,(x,y+25))
                draw.text((x+8,y+5),name+' original LOD%d; separate resource, automatic framing'%i,fill='white')
        canvas.save(output/(name+'-LOD-comparison.png'))
        s=u.load_scene(root/'assembly/scene/scene.json')
        for n in s['nodes']:
            if n['id']!='wheel-0':n['mesh_ids']=[]
        preview=output/(name+'-wheel.mrpv');stage_source_scene(s,preview,scene_root=root/'assembly/scene')
        capture_views(viewer,preview,output/(name+'-wheel'),provenance='Original selected Michelin wheel, native keyed coverage; neutral pose')
    report={'schema':'michelin-scene-validation/1','scenes':rows,'status':'PASS structural/conservation; L2 WARN renderer/runtime',
            'native_candidate':'NOT CREATED','source_hashes':{a:u.sha(u.read_bounded(source/'Data/Objects'/a,m.f.MAX_FILE))for a in m.QUALIFIED}}
    (output/'validation.json').write_bytes(u.canonical(report));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--scenes',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--viewer',type=Path,required=True);a=p.parse_args();run(a.source_root,a.scenes,a.output,a.viewer)
