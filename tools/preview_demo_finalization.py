"""Private native icon/marker comparisons; no source texture writes."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from PIL import Image,ImageDraw
from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels
from master_rallye.addon_sdk.project import read_sma_member
from master_rallye.addon_sdk.ui_assets import BANKS
from master_rallye.workshop.race_marker import tinted_marker
from master_rallye.universal_vehicle_scene import output_directory


def image(raw):
    t=parse_dxt_bytes(raw);return Image.frombytes('RGBA',(t.width,t.height),decode_rgba_pixels(t))


def preview(delivery,previous,sma,output):
    result=json.loads((delivery/'result.json').read_text());candidate=Path(result['candidate']);root=candidate/'runtime/resource-root';old=previous/'runtime/resource-root'
    output=output_directory(output,[delivery,previous,sma]);output.mkdir(parents=True)
    plan=json.loads((candidate/'runtime/addon-plan.json').read_text());row=next(x for x in plan['addons']if x['physical_id']==32)
    path=lambda role:f"{BANKS[role][0]}_{row['frontend'][role]['frame']:03d}_000.dxt"
    menu=image((root/path('vehicle_select_art')).read_bytes());a=image((old/path('smallcarsheet')).read_bytes());b=image((root/path('smallcarsheet')).read_bytes())
    sheet=Image.new('RGB',(900,245),'#6c622f');draw=ImageDraw.Draw(sheet)
    for x,title,im in [(8,'Historical Vehicle Select (unchanged)',menu),(305,'Original isometric HUD (heritage)',a.resize((256,128),Image.Resampling.NEAREST)),(610,'RECONSTRUCTED flat HUD',b.resize((256,128),Image.Resampling.NEAREST))]:
        draw.text((x,8),title,fill='white');sheet.paste(im,(x,45),im)
    sheet.save(output/'tomcat-hud.png')
    marker=image(read_sma_member(sma,'DataGx/Hud/hud-template_003_000.dxt'))
    sheet=Image.new('RGB',(1000,420),'#232b32');draw=ImageDraw.Draw(sheet)
    for row,(car,entry)in enumerate(result['vehicles'].items()):
        y=140*row;analysis=entry['analysis'];rgba=entry['marker']['current']['rgba'];mode=entry['marker']['policy']['policy']['mode']
        draw.text((8,y+8),f"CarID {car}: {mode}; selected {rgba}",fill='white')
        for x,bg in ((8,'#343a42'),(160,'#dddddd')):
            draw.rectangle((x,y+30,x+140,y+105),fill=bg);im=tinted_marker(marker,rgba).resize((96,48),Image.Resampling.NEAREST);sheet.paste(im,(x+20,y+42),im)
        for col,item in enumerate([{'rgb':analysis['dominant'],'label':'Dominant'},{'rgb':analysis['average'],'label':'Average'}]+[{'rgb':s['rgb'],'label':f"{s['weight']:.0%}"}for s in analysis['swatches']]):
            x=330+col*82;color=tuple(round(v*255)for v in item['rgb']);draw.rectangle((x,y+35,x+68,y+85),fill=color);draw.text((x,y+92),item['label'],fill='white')
    sheet.save(output/'marker-comparison.png')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in('delivery','previous','retail-sma','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();preview(a.delivery,a.previous,a.retail_sma,a.output)
