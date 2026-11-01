"""Reproducible private v1/v2 icon comparison; no scene/native-material edits."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from generate_vehicle_ui_previews import render_sources
from master_rallye.addon_sdk.ui_preview import compose_preview
from master_rallye.texture_authoring import decode_rgba_png
from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels
from master_rallye.universal_vehicle_scene import output_directory


def compare(family,output,references=None):
    from PIL import Image,ImageDraw
    output=output_directory(output,[family,*[Path(p)for p in (references or {}).values()]])
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in family.iterdir()if p.suffix.casefold()in('.dx','.dxt')}
    output.mkdir(parents=True);sheet=Image.new('RGB',(720,260),'#6c622f');draw=ImageDraw.Draw(sheet);records={};images={}
    for col,style in enumerate(('mr-native-v1','mr-native-v2')):
        reports=render_sources(family,output/style,style=style)
        for row,role in enumerate(('vehicle_select_art','smallcarsheet')):
            raw,report=compose_preview(decode_rgba_png((output/style/(role+'.png')).read_bytes()),role,style=style)
            size=(128,128)if row==0 else(32,16);image=Image.frombytes('RGBA',size,raw);image.save(output/style/(role+'-native.png'));images[style,role]=raw
            if row:image=image.resize((128,64),Image.Resampling.NEAREST)
            sheet.paste(image,(col*240,row*150+25),image);draw.text((col*240+4,5),style,fill='white');records[style,role]={'render':reports[role],'composition':report}
    coverage={}
    for row,role in enumerate(('vehicle_select_art','smallcarsheet')):
        if references and role in references:
            t=parse_dxt_bytes(Path(references[role]).read_bytes());image=Image.frombytes('RGBA',(t.width,t.height),decode_rgba_pixels(t))
            if row:
                from master_rallye.addon_sdk.ui_assets import fit_rgba
                rgba=fit_rgba((t.width,t.height,image.tobytes()),32,16,padding=0)
                image=Image.frombytes('RGBA',(32,16),rgba).resize((128,64),Image.Resampling.NEAREST)
            sheet.paste(image,(480,row*150+25),image);draw.text((484,5),'Original game artwork',fill='white')
        a,b=images['mr-native-v1',role],images['mr-native-v2',role]
        same_camera=all(records['mr-native-v1',role]['render'][k]==records['mr-native-v2',role]['render'][k]for k in ('camera_azimuth','camera_elevation'))
        if same_camera and a[3::4]!=b[3::4]:raise ValueError('Icon lighting changed coverage at the same camera')
        coverage[role]={'same_camera':same_camera,'alpha_identical':a[3::4]==b[3::4],
                        'policy':'Independent alpha-only render; v1/v2 preserve flat side orthographic HUD and full-icon cameras'}
    if any(hashlib.sha256((family/n).read_bytes()).hexdigest()!=pin for n,pin in pins.items()):raise ValueError('Source icon resource changed')
    sheet.save(output/'comparison.png')
    report={'source_pins':pins,'coverage':coverage,'records':{style+'/'+role:value for (style,role),value in records.items()},
            'boundary':'UI studio approximation. Original texture/geometry/ordinary D3D9 scene materials unchanged; no original renderer parity claim.'}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--family',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--carsheet',type=Path);p.add_argument('--hud',type=Path);a=p.parse_args()
    compare(a.family,a.output,{k:str(v)for k,v in {'vehicle_select_art':a.carsheet,'smallcarsheet':a.hud}.items()if v})
