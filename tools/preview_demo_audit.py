"""Private actual D3D9 captures of complete source models; no native authoring."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk import heritage_source as h
from master_rallye import demo_vehicle_audit as audit
from master_rallye.dx import parse_dx_bytes
from master_rallye.gxi import parse_gxi_bytes,encode_gxi_as_observed_dxt
from master_rallye.preview_scene import stage_vehicle
from master_rallye.source_scene_preview import capture_startup_info
from master_rallye.universal_vehicle_scene import output_directory


def run(catalog,viewer,output):
    doc=json.loads(catalog.read_text(encoding='utf-8'));rows=doc['families']
    selected=[r for r in rows if r['label']in('pcg-rebaked','nov-local','shipped931')and len(r['native_roles'])==3]
    # Same-named retail references are independently captured; no forced alignment.
    names={r['family'].casefold()for r in selected}
    selected += [r for r in rows if r['kind']=='retail'and r['family'].casefold()in names]
    output=output_directory(output,[catalog,viewer,*[Path(r['folder'])for r in selected]])
    if not output.is_relative_to((ROOT/'.research-output').absolute()):raise ValueError('Private output required')
    output.mkdir(parents=True);reports=[];cache={};pins={}
    for i,row in enumerate(selected):
        record={'family':row['id'],'status':'NOT TESTED','renderer_sha256':audit.sha(viewer.read_bytes()),'boundary':'Complete model as supplied; no inferred wheel transforms. Neutral D3D9, not original-game parity.'}
        try:
            folder=Path(row['folder']);name=next(n for n,m in row['models'].items()if m['role']=='complete'and m['format']=='DX')
            raw=h.read(folder/name)
            if audit.sha(raw)!=row['files'][name]['sha256']:raise ValueError('Source model changed')
            pins[str(folder/name)]=audit.sha(raw)
            converted,detail=h.compatible_model(raw,str(folder/name));model=parse_dx_bytes(converted)
            refs=sorted({s for d in model.physical_draws for s in d.texture_tuple if s.lower()!='null'})
            textures={}
            for stem in refs:
                if Path(stem).name!=stem or any(c in stem for c in '/\\:'):raise ValueError('Unsafe native texture reference')
                spec=row['textures'].get(stem.casefold())
                if not spec or spec['status']!='PASS_LOCAL':raise FileNotFoundError('Missing local texture '+stem)
                source=next((t for t in spec['candidates']if t['file'].lower().endswith('.dxt')and 'decoded_bgra_sha256'in t),None)
                source=source or next(t for t in spec['candidates']if 'decoded_bgra_sha256'in t)
                path=folder/source['file'];data=h.read(path)
                if audit.sha(data)!=source['sha256']:raise ValueError('Source texture changed')
                pins[str(path)]=audit.sha(data)
                if path.suffix.lower()=='.gxi':data=encode_gxi_as_observed_dxt(parse_gxi_bytes(data))
                textures[stem+'.dxt']=data
            key=audit.sha(converted+b''.join(name.encode()+textures[name]for name in sorted(textures)))
            record['conversion']=detail
            if key in cache:
                record.update(status='CAPTURED_SHARED_EXACT_INPUT',captures=cache[key]);reports.append(record);continue
            dest=output/(str(i).zfill(2));dest.mkdir();(dest/'model.dx').write_bytes(converted)
            for name,data in textures.items():(dest/name).write_bytes(data)
            scene=dest/'preview.mrpv';stage_vehicle(dest/'model.dx',scene)
            captures={}
            for view,preset,cull in [('isometric',4,'cw'),('left',6,'cw'),('isometric-ccw',4,'ccw')]:
                target=dest/(view+'.bmp')
                command=[str(viewer),'--scene',str(scene),'--model','race','--preset',str(preset),'--capture',str(target),'--cull',cull,'--provenance','Read-only Demo audit; complete source geometry; D3D8 NOT TESTED']
                p=subprocess.Popen(command,startupinfo=capture_startup_info(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                try:
                    if p.wait(timeout=45):raise ValueError('Previewer failed')
                finally:
                    if p.poll()is None:p.terminate();p.wait(timeout=5)
                from PIL import Image
                with Image.open(target)as image:image.verify()
                captures[view]=str(target.absolute())
            cache[key]=captures;record.update(status='CAPTURED_D3D9_WARN',captures=captures)
        except Exception as e:record.update(status='MISSING_INPUT'if isinstance(e,FileNotFoundError)else'WARN',error=str(e))
        reports.append(record);print(row['id'],record['status'],flush=True)
    from PIL import Image,ImageDraw
    image=Image.new('RGB',(1200,260*((len(reports)+3)//4)),'#20262e');draw=ImageDraw.Draw(image)
    for i,row in enumerate(reports):
        x=i%4*300;y=i//4*260;draw.text((x+6,y+4),row['family'][:46],fill='white')
        if row.get('captures'):
            with Image.open(row['captures']['isometric'])as im:
                im.thumbnail((292,218));image.paste(im,(x+4,y+22))
        else:draw.text((x+7,y+95),row.get('error','No capture')[:42],fill='#ef9898')
        draw.text((x+6,y+243),row['status'],fill='#dcbf89')
    image.save(output/'textured-contact.png')
    changed=[name for name,sha in pins.items()if audit.sha(h.read(Path(name)))!=sha]
    result={'schema':'demo-audit-previews/1','captures':reports,'source_files_checked':len(pins),'changed':changed,'L2':'WARN','gameplay':'NOT TESTED'}
    (output/'previews.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if changed:raise ValueError('Read-only source changed')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.catalog,a.viewer,a.output)
