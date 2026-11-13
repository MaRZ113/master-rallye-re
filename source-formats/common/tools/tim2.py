"""PS2 TIM2 reader -> list of PIL images (4/8-bit CLUT with CSM1 unswizzle, 16/24/32-bit)."""
import struct
from PIL import Image
def _col(b,o,t):
    if t==3: r,g,bb,a=b[o:o+4];return (r,g,bb,min(255,a*2))
    if t==2: r,g,bb=b[o:o+3];return (r,g,bb,255)
    v=struct.unpack_from('<H',b,o)[0];return ((v&31)<<3,((v>>5)&31)<<3,((v>>10)&31)<<3,255 if v>>15 else 0)
def read(buf):
    assert buf[:4]==b'TIM2';fmt=buf[5];n=struct.unpack_from('<H',buf,6)[0];o=128 if fmt==1 else 16;out=[]
    for _ in range(n):
        tot,cs,isz,hs,cc,pf,mm,ct,it,w,h=struct.unpack_from('<IIIHHBBBBHH',buf,o)
        img=buf[o+hs:o+hs+isz];clut=buf[o+hs+isz:o+hs+isz+cs]
        ctype=ct&0x3f;csm2=ct&0x80;bpp={1:2,2:3,3:4}.get(ctype,2)
        pal=[_col(clut,k*bpp,ctype) for k in range(cc)]
        if it==5 and not csm2 and cc==256:
            p2=[]
            for k in range(256):
                b_=k&0xe7;
                if (k&0x18)==0x08:b_|=0x10
                elif (k&0x18)==0x10:b_|=0x08
                p2.append(pal[b_])
            pal=p2
        im=Image.new('RGBA',(w,h));px=[]
        if it==5: px=[pal[x] for x in img[:w*h]]
        elif it==4:
            for x in img[:w*h//2]: px+= [pal[x&15],pal[x>>4]]
        elif it in(1,2,3):
            bp={1:2,2:3,3:4}[it];px=[_col(img,k*bp,it) for k in range(w*h)]
        im.putdata(px[:w*h]);out.append(im);o+=tot
    return out
