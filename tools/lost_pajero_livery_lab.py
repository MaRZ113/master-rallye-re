"""Read-only MR Pajero texture audit and private, explicitly partial livery probe."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.pajero_livery_forensics import inventory,badge_experiment,OverlayHistory
from master_rallye.dxt import parse_dxt,decode_rgba_pixels
from master_rallye.dx import parse_dx
from master_rallye.source_scene_preview import stage_source_scene,capture_views


def reference_sheet(experiment,references,output):
    from PIL import Image,ImageDraw
    references=Path(references).absolute();output=u.output_directory(Path(output).absolute(),[references,Path(experiment).absolute()])
    output.mkdir(parents=True,exist_ok=False);rows=[]
    for filename in ('m_rallye_05.jpg','m_rallye_07.jpg'):
        p=references/filename;u.unlinked(p);raw=u.read_bounded(p,16*1024*1024)
        canvas=Image.new('RGB',(1080,780),(35,35,35));draw=ImageDraw.Draw(canvas)
        with Image.open(p)as im:
            size=im.size;im=im.convert('RGB');im.thumbnail((720,510));canvas.paste(im,(0,30))
        draw.text((10,8),filename+' | owner-local historical image; capture build/camera UNKNOWN',fill='white')
        for i,key in enumerate(('pdoor128','pajeror128','mastersticker')):
            im=Image.open(Path(experiment)/'atlases'/(key+'-tga-upright.png')).convert('RGB');im.thumbnail((230,230));im=im.resize((210,210),Image.Resampling.NEAREST)
            canvas.paste(im,(i*250,555));draw.text((i*250,535),'Original MR '+key,fill='white')
        draw.text((735,60),'Visual correspondence only',fill='white');draw.text((735,85),'Not an original MR mesh recovery',fill='white')
        canvas.save(output/(p.stem+'-texture-evidence.png'));rows.append({'path':str(p),'sha256':u.sha(raw),'bytes':len(raw),'dimensions':size,'classification':'historical reference, not source mesh or runtime proof'})
    (output/'references.json').write_bytes(u.canonical(rows))


def run(corpus,source,output,viewer):
    from PIL import Image,ImageDraw
    corpus,source=Path(corpus).absolute(),Path(source).absolute()
    output=u.output_directory(Path(output).absolute(),[corpus,source.parent])
    if output.exists():raise ValueError('Fresh experiment output required')
    report=inventory(corpus);output.mkdir(parents=True)
    (output/'texture-inventory.json').write_bytes(u.canonical(report))
    folder=output/'atlases';folder.mkdir()
    family=corpus/'retail/Data.sma_unpacked/DataGx/Vehicles/Pajero'
    for row in report['textures']:
        t=parse_dxt(Path(row['path']));raw=decode_rgba_pixels(t,'preserve-stored')
        im=Image.frombytes('RGBA',(t.width,t.height),raw);im.save(folder/(Path(row['path']).stem+'-stored.png'))
        Image.frombytes('RGBA',(t.width,t.height),decode_rgba_pixels(t,'flip-vertical')).save(folder/(Path(row['path']).stem+'-upright.png'))
    # Existing original MR UV0, not inferred from texture names. Draw ownership
    # remains in the inventory; overlays display stored GPU row convention.
    for model_path in family.glob('*.dx'):
        m=parse_dx(model_path)
        for stem in sorted({d.texture_tuple[0]for d in m.physical_draws if d.texture_tuple[0].lower()!='null'}):
            path=family/(stem.lower()+'.dxt')
            if not path.is_file():continue
            t=parse_dxt(path);im=Image.frombytes('RGBA',(t.width,t.height),decode_rgba_pixels(t,'preserve-stored')).convert('RGB').resize((512,512));draw=ImageDraw.Draw(im)
            for d in m.physical_draws:
                if d.texture_tuple[0]!=stem:continue
                ids=m.draw_global_indices(d)
                for i in range(0,len(ids),3):
                    uv=[m.uv_sets[0].values[k]for k in ids[i:i+3]]
                    draw.line([(p[0]*512,p[1]*512)for p in uv+[uv[0]]],fill=(0,255,255),width=1)
            im.save(folder/(model_path.stem+'-'+stem+'-uv0.png'))
    scene=u.load_scene(source);texture_by_id={t['id']:t for t in scene['textures']};materials={m['id']:m for m in scene['materials']}
    uv_report=[]
    for mesh in scene['meshes']:
        mat=materials[mesh['material_id']];uv=mesh['uvs']
        uv_report.append({'mesh':mesh['id'],'material':mesh['material_id'],'diffuse':mat['diffuse_texture_id'],
            'uv0_sha256':u.sha(u.canonical(uv)),'uv0_bounds':[[min(p[k]for p in uv),max(p[k]for p in uv)]for k in range(2)],
            'uv1_stream':mesh['source']['streams'].get('10'),'source_state':mat.get('source_render_state'),
            'original_color_stream':mesh['source']['streams']['3']})
    for key in ('xtx-043','xtx-046'):
        t=texture_by_id[key];im=Image.frombytes('RGBA',(t['width'],t['height']),(source.parent/t['rgba_path']).read_bytes()).convert('RGB').resize((768,768));draw=ImageDraw.Draw(im)
        for mesh in scene['meshes']:
            if materials[mesh['material_id']]['diffuse_texture_id']!=key:continue
            for tri in mesh['triangles']:
                uv=[mesh['uvs'][i]for i in tri];draw.line([(p[0]*768,p[1]*768)for p in uv+[uv[0]]],fill=(0,255,255),width=1)
        im.save(folder/(key+'-uv0.png'))
    (output/'uv-compatibility.json').write_bytes(u.canonical({'source_draws':uv_report,'direct_assignment':'UNSUPPORTED_NO_VERIFIED_CROSS_ATLAS_CORRESPONDENCE',
        'reason':'MR splits door/front/rear/sticker images across separate materials; Xbox body atlas combines opposed side islands, interior and decals. Equal UV ranges or red paint are not atlas identity.',
        'B':'NOT GENERATED; assigning an incompatible whole MR texture would distort surfaces',
        'C':'PARTIAL original203 badge atlas patch only, no full red livery claim'}))
    for label,path in [('A',source)]:
        target=output/label;target.mkdir();stage_source_scene(scene,target/'preview.mrpv',scene_root=source.parent)
        capture_views(viewer.absolute(),(target/'preview.mrpv').absolute(),target/'views',cull='source')
    h=OverlayHistory();h.apply(True);h.save(output/'overlay-history.json')
    result=badge_experiment(source,output/'C/scene',family,h)
    c=u.load_scene(output/'C/scene/scene.json');stage_source_scene(c,output/'C/preview.mrpv',scene_root=output/'C/scene')
    capture_views(viewer.absolute(),(output/'C/preview.mrpv').absolute(),output/'C/views',cull='source')
    (output/'experiment-result.json').write_bytes(u.canonical(result))
    for view in ('front','rear','left','right','top','isometric'):
        canvas=Image.new('RGB',(1080,405),(30,30,30));draw=ImageDraw.Draw(canvas)
        for x,label in [(0,'A'),(540,'C')]:
            im=Image.open(output/label/'views'/(view+'.png'));im.thumbnail((540,375));canvas.paste(im,(x,30));draw.text((x+8,8),'A Xbox original'if label=='A'else'C PARTIAL MR203 badge only; other art Xbox',fill='white')
        canvas.save(output/(view+'-A-C.png'))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('corpus','source','output','viewer'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--references',type=Path)
    a=p.parse_args();run(a.corpus,a.source,a.output,a.viewer)
    if a.references:reference_sheet(a.output,a.references,a.output/'historical-evidence')
