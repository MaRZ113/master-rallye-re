import sys
from PIL import Image
import numpy as np
def ps2_output(img, ct16=True):
    a=np.asarray(img.convert('RGB').resize((640,512),Image.BILINEAR)).astype(np.float32)
    if ct16: a=np.floor(a/8)*8          # PSMCT16 render buffer, GS expands RGB5 by <<3
    def field(off):
        # sprite 640x512 -> 512x256, bilinear, sample centres at u=(x+.5)*1.25, v=(y+.5)*2+off
        xs=(np.arange(512)+.5)*1.25-.5; ys=(np.arange(256)+.5)*2-.5+off
        x0=np.clip(np.floor(xs).astype(int),0,639);x1=np.clip(x0+1,0,639);fx=(xs-np.floor(xs))[None,:,None]
        y0=np.clip(np.floor(ys).astype(int),0,511);y1=np.clip(y0+1,0,511);fy=(ys-np.floor(ys))[:,None,None]
        r0=a[y0][:,x0]*(1-fx)+a[y0][:,x1]*fx;r1=a[y1][:,x0]*(1-fx)+a[y1][:,x1]*fx
        return r0*(1-fy)+r1*fy
    f0,f1=field(0.0),field(0.5)          # packets 0x23f0 / 0x24f0 (+8/16 px)
    out=np.empty((512,512,3),np.float32);out[0::2]=f0;out[1::2]=f1   # weave both fields
    return Image.fromarray(np.clip(out,0,255).astype(np.uint8))
src,dst,w,h=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
ps2_output(Image.open(src)).resize((w,h),Image.BILINEAR).save(dst)
