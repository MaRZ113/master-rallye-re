"""Read original Xbox shader/material evidence; never emit playable resources."""
from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_adapters.dakar2_materials import native_evidence,qualify_scene


def run(image,scenes,output):
    image=Path(image).absolute();scenes=[Path(p).absolute()for p in scenes]
    loaded=[u.load_scene(p)for p in scenes]
    protected=[image.parent,*[p.parent for p in scenes]]
    for scene in loaded:protected.extend(map(Path,scene['source'].get('protected_roots',[])))
    output=u.output_directory(Path(output).absolute(),protected)
    if output.exists():raise ValueError('Fresh material evidence output required')
    evidence=native_evidence(image);output.mkdir(parents=True)
    (output/'native-material-evidence.json').write_bytes(u.canonical(evidence))
    results=[]
    from PIL import Image,ImageDraw
    for path,scene in zip(scenes,loaded):
        report=qualify_scene(scene,evidence);report['source_scene_sha256']=u.sha(u.read_bounded(path,u.MAX_JSON_BYTES))
        name=scene['source']['catalog'];folder=output/name;folder.mkdir()
        textures={t['id']:t for t in scene['textures']}
        bindings=sorted({tuple(stage['texture_id']for stage in row['texture_stages'])for row in report['draws']},key=str)
        if len(bindings)>256:raise ValueError('Material diagnostic allocation budget')
        sheet=Image.new('RGB',(4*200,max(1,len(bindings))*180),(45,45,45));draw=ImageDraw.Draw(sheet)
        for y,group in enumerate(bindings):
            for stage,binding in enumerate(group):
                title='stage'+str(stage)+' '+str(binding);draw.text((stage*200+5,y*180+4),title,fill='white')
                if binding is None:continue
                texture=textures[binding];rgba=u.read_bounded(path.parent/texture['rgba_path'],u.MAX_TEXTURE_BYTES)
                if u.sha(rgba)!=texture['rgba_sha256']:raise ValueError('Texture diagnostic provenance mismatch')
                image_=Image.frombytes('RGBA',(texture['width'],texture['height']),rgba);image_.thumbnail((185,150))
                sheet.paste(image_,(stage*200+5,y*180+24),image_)
        sheet.save(folder/'stage-bindings.png')
        report['diagnostic']='Raw original texture bindings, original decoded alpha over grey; no inferred runtime sampler, shader or lighting.'
        blob=u.canonical(report)
        if blob!=u.canonical({**qualify_scene(scene,evidence),'source_scene_sha256':report['source_scene_sha256'],'diagnostic':report['diagnostic']}):
            raise ValueError('Nondeterministic material qualification')
        (folder/'qualification.json').write_bytes(blob)
        results.append({'vehicle':name,'draws':report['draw_count'],'triangles':report['triangles'],
                        'uv1_present':report['uv1_present'],'uv1_exact_aliases':report['uv1_exact_aliases'],
                        'native_material_readiness':report['native_material_readiness'],
                        'qualification_sha256':u.sha(blob)})
    summary={'schema':'dakar2-material-corpus/1','vehicles':results,'source_mutated':False,
             'native_fixtures':0,'reason':'Source-dependent additive stages, runtime vertex-program outputs and coverage remain required; no silent diffuse fallback.'}
    (output/'summary.json').write_bytes(u.canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xbox',type=Path,required=True);parser.add_argument('--scene',type=Path,action='append',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    print(run(args.xbox,args.scene,args.output))
