"""Read-only original Evo2 nine-color CPU reconstruction, private derived UVS."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_adapters import evo2, evo2_color as c


def run(source, executable, output, viewer=None):
    from PIL import Image,ImageDraw
    scene=u.load_scene(source);before=u.sha(source.read_bytes())
    exe=u.read_bounded(executable,16*1024*1024)
    out=u.output_directory(output,[source.parent,executable.parent,*map(Path,scene['source'].get('protected_roots',[]))])
    out.mkdir(parents=True)
    texture=next(t for t in scene['textures']if t['source']['member'].casefold()=='art/4runnersr5.tif')
    ch=texture['source_channels'];raw=u.read_bounded(source.parent/ch['raw_samples_path'],1024*1024)
    pal=u.read_bounded(source.parent/ch['palette_path'],1536);size=texture['width']
    sheet=Image.new('RGB',(size*3,size*3+32*3),(40,40,40));draw=ImageDraw.Draw(sheet);rows=[]
    for index,record in enumerate(scene['source']['catalog_original']['color_records']):
        variant=c.derive_scene(source,out/f'color-{index:02d}',exe,index)
        reopened=u.load_scene(Path(variant['scene']))
        t=next(t for t in reopened['textures']if t['id']==texture['id'])
        rgba=u.read_bounded(Path(variant['scene']).parent/t['rgba_path'],size*size*4)
        repeat=c.reconstruct(exe,raw,pal,size,[float(v)for v in record['value'].split(',')[:3]])
        if rgba!=repeat['rgba']:raise ValueError('nondeterministic Evo2 color')
        if any(reopened[k]!=scene[k]for k in ('source','meshes','nodes','materials','coordinate_system')):raise ValueError('source scene changed')
        x=(index%3)*size;y=(index//3)*(size+32)
        image=Image.frombytes('RGBA',(size,size),rgba);image.save(out/f'color-{index:02d}.png')
        sheet.paste(image.convert('RGB'),(x,y+32));draw.text((x+4,y+8),f'{index+1}: {record["value"]}',fill='white')
        if viewer is not None:
            from master_rallye.source_scene_preview import stage_source_scene,capture_views,preview_cull
            preview=out/f'color-{index:02d}.mrpv'
            stage_source_scene(reopened,preview,scene_root=Path(variant['scene']).parent)
            capture_views(viewer,preview,out/f'color-{index:02d}-views',cull=preview_cull(reopened),
                          provenance=f'Evo2 original color {index+1}: exact pre-gloss CPU RGB; opaque neutral GPU approximation; L2 WARN')
        rows.append({'index':index,'scene_sha256':variant['scene_sha256'],'reopen':'PASS','deterministic_rgba':'PASS',**repeat['evidence']})
    sheet.save(out/'nine-colors.png')
    planes=Image.new('RGB',(size*3,size))
    planes.paste(Image.frombytes('L',(size,size),raw[::2]).convert('RGB'),(0,0))
    planes.paste(Image.frombytes('L',(size,size),raw[1::2]).convert('RGB'),(size,0))
    base=u.read_bounded(source.parent/texture['rgba_path'],size*size*4)
    planes.paste(Image.frombytes('RGBA',(size,size),base).convert('RGB'),(size*2,0));planes.save(out/'index-auxiliary-base.png')
    if u.sha(source.read_bytes())!=before:raise ValueError('source scene mutated')
    report={'schema':c.SCHEMA,'source_scene_sha256':before,'source_unchanged':True,'variants':rows,
            'raw_samples_sha256':u.sha(raw),'palette_sha256':u.sha(pal),
            'second_sample_counts':{'0..128':sum(v<=128 for v in raw[1::2]),'129..254':sum(129<=v<=254 for v in raw[1::2]),'255':raw[1::2].count(255)},
            'status':'PASS original CPU pre-gloss color reconstruction; L2 WARN GPU/runtime parity',
            'native_projects_modified':False,'gpu_alpha':'UNQUALIFIED; preview remains opaque'}
    (out/'validation.json').write_bytes(u.canonical(report));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--viewer',type=Path)
    p.add_argument('--scene',type=Path,required=True);p.add_argument('--executable',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.scene,a.executable,a.output,a.viewer);print(r['status']);print(a.output/'validation.json')
