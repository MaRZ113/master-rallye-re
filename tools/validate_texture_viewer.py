"""Windows-only display zoom acceptance using private textures and an original generated atlas."""
from pathlib import Path
import argparse,hashlib,json,sys,tkinter as tk
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from PIL import Image,ImageDraw
from master_rallye.dxt import parse_dxt_bytes,DxtTexture,encode_png
from master_rallye.workshop.texture_view import TextureView
from master_rallye.workshop.branding import apply_icon,taskbar_identity
from validate_rally_workshop import screenshot

def main():
 p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 cases={}
 for folder in json.loads(a.library.read_text()):
  for path in (Path(folder)/'baseline').glob('*.dxt'):
   t=parse_dxt_bytes(path.read_bytes());key=(t.width,t.height)
   if key in ((64,64),(128,128),(1024,256)) and key not in cases:cases[key]=(t,str(path))
 im=Image.new('RGBA',(2048,2048));draw=ImageDraw.Draw(im)
 for y in range(2048):draw.line((0,y,2047,y),fill=(y//8,255-y//8,90,y//8))
 for y in range(0,2048,128):
  draw.text((15,y+15),'RALLY WORKSHOP 0123456789 / ALPHA / ATLAS',fill=(255,255,255,255),stroke_width=1)
  draw.line((0,y,2047,y+127),fill=(0,0,0,255),width=1);draw.rectangle((700,y+30,850,y+95),fill=(255,170,30,180))
 native=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes('raw','BGRA');cases[(2048,2048)]=(DxtTexture('original generated test atlas',1,0,2048,2048,native,b''),'generated fixture, not a GT/MR texture')
 taskbar_identity();root=tk.Tk();root.title('Rally Workshop — embedded texture zoom acceptance');root.geometry('1000x760');apply_icon(root);popup=tk.Toplevel(root);popup.title('Rally Workshop — detached texture zoom acceptance');popup.geometry('1000x760+60+60');apply_icon(popup)
 selected=[None];views=[TextureView(root,lambda original:selected[0]),TextureView(popup,lambda original:selected[0])]
 for view in views:view.pack(fill='both',expand=True)
 errors=[];root.report_callback_exception=lambda *args:errors.append(str(args));report={'boundary':'Real Windows Tk display only; original native resources never written','cases':[]}
 for size,(texture,source) in cases.items():
  selected[0]=texture;before=hashlib.sha256(texture.bgra).hexdigest();png=encode_png(texture)
  for v in views:v.channel.set('RGBA');v.load()
  root.update()
  for scale in (.25,.5,.75,1,1.25,2,4):
   for i,v in enumerate(views):
    v.fit=False;v.scale=scale;v.canvas.xview_moveto(0);v.canvas.yview_moveto(0);v.draw();root.update();screenshot(root if i==0 else popup,a.output/f'{size[0]}x{size[1]}-{scale}-{i}.png')
    assert v.last_raster.width*v.last_raster.height<=4*1024*1024
   if errors:raise ValueError(errors)
  for v in views:
   v.actual();root.update();v.pixel.set(True);v.zoom(2);v.draw();v.canvas.xview_moveto(.2);v.canvas.yview_moveto(.2);v.draw()
   x,y=200,150;old=(v.canvas.canvasx(x)/round(size[0]*v.scale),v.canvas.canvasy(y)/round(size[1]*v.scale));v.zoom(1.25,type('Event',(),{'x':x,'y':y})());v.draw();new=(v.canvas.canvasx(x)/round(size[0]*v.scale),v.canvas.canvasy(y)/round(size[1]*v.scale))
   if size[0]*v.scale>v.canvas.winfo_width() and size[1]*v.scale>v.canvas.winfo_height():assert max(abs(old[k]-new[k])*size[k] for k in range(2))<2
   for ch in ('RGB','Alpha','RGBA'):v.channel.set(ch);v.load();v.draw();root.update()
   v.original.set(True);v.load();v.draw();v.original.set(False);v.pixel.set(False)
  assert hashlib.sha256(texture.bgra).hexdigest()==before and encode_png(texture)==png
  report['cases'].append({'dimensions':size,'source':source,'bgra_sha256_unchanged':before,'zoom_levels':[.25,.5,.75,1,1.25,2,4],'windows':2,'channels':['RGB','RGBA','Alpha'],'pixel_mode':True,'cursor_anchor':True})
 (a.output/'validation.json').write_text(json.dumps(report,indent=2));root.destroy()
if __name__=='__main__':main()
