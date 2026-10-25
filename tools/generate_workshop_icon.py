"""Build original Rally Workshop vector and Windows icon; no game input required."""
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
BODY=[(65,295),(123,269),(179,221),(217,164),(329,164),(391,225),(454,267),(449,335),(65,335)]
GLASS=[(190,222),(231,181),(316,181),(358,224)]
def build(folder=ROOT/'assets/workshop'):
 folder.mkdir(parents=True,exist_ok=True)
 points=lambda values:' '.join(f'{x},{y}' for x,y in values)
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Rally Workshop original rally prototype icon">
<rect x="12" y="12" width="488" height="488" rx="96" fill="#252930"/>
<polygon points="{points(BODY)}" fill="#edb34d"/>
<polygon points="{points(GLASS)}" fill="#252930"/>
<path d="M273 179V225M99 287H159M379 239H422" fill="none" stroke="#252930" stroke-width="14"/>
<path d="M214 157H333" stroke="#ece5d5" stroke-width="12" stroke-linecap="round"/>
<path d="M90 343H430" stroke="#ece5d5" stroke-width="12"/>
<g fill="#15191f" stroke="#252930" stroke-width="14"><circle cx="157" cy="335" r="65"/><circle cx="369" cy="335" r="65"/></g>
<g fill="#edb34d"><circle cx="157" cy="335" r="29"/><circle cx="369" cy="335" r="29"/></g>
</svg>'''
 (folder/'rally-workshop.svg').write_text(svg,encoding='utf-8')
 im=Image.new('RGBA',(1024,1024));d=ImageDraw.Draw(im);s=2
 polygon=lambda ps,fill:d.polygon([(x*s,y*s) for x,y in ps],fill=fill)
 d.rounded_rectangle((24,24,1000,1000),radius=192,fill='#252930');polygon(BODY,'#edb34d');polygon(GLASS,'#252930')
 for line in ((273,179,273,225),(99,287,159,287),(379,239,422,239)):d.line(tuple(v*s for v in line),fill='#252930',width=28)
 d.line((428,314,666,314),fill='#ece5d5',width=24);d.line((180,686,860,686),fill='#ece5d5',width=24)
 for x in (157,369):
  d.ellipse(((x-65)*s,270*s,(x+65)*s,400*s),fill='#15191f',outline='#252930',width=28)
  d.ellipse(((x-29)*s,306*s,(x+29)*s,364*s),fill='#edb34d')
 im.resize((256,256),Image.Resampling.LANCZOS).save(folder/'rally-workshop.png')
 im.save(folder/'rally-workshop.ico',format='ICO',sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
 return folder
if __name__=='__main__':print(build())
