"""Read-only corpus measurements/contact sheets for the two native UI roles."""
from pathlib import Path
import argparse,json,statistics,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels
from master_rallye.addon_sdk.ui_assets import BANKS,archive_member,alpha_bounds
from master_rallye.vehicle_packaging import _open_sma_archive
import gtmat

def audit(archive,out):
    out.mkdir(parents=True,exist_ok=True);results={}
    with _open_sma_archive(archive) as z:
        for role,(prefix,count,template,size) in BANKS.items():
            w,h=size;cw,ch=(128,128) if w>32 else (128,64);sw=cw*8
            sheet=bytearray(bytes((90,96,104,255))*sw*(ch*((count+7)//8)));rows=[]
            for frame in range(count):
                raw=archive_member(z,f'{prefix}_{frame:03d}_000.dxt');t=parse_dxt_bytes(raw);px=decode_rgba_pixels(t)
                if not any(a>20 for a in px[3::4]):rows.append({'frame':frame,'empty':True});continue
                bounds=alpha_bounds((w,h,px));l=sorted(.2126*px[i]+.7152*px[i+1]+.0722*px[i+2] for i in range(0,len(px),4) if px[i+3]>200)
                rows.append({'frame':frame,'bounds':bounds,'luma_mean':statistics.mean(l),'luma_median':statistics.median(l),'luma_p90':l[int(.9*(len(l)-1))],'alpha_pixels':sum(a>20 for a in px[3::4])});scale=cw//w
                for y in range(h*scale):
                    for x in range(w*scale):
                        i=4*((y//scale)*w+x//scale);d=4*(((frame//8)*ch+y)*sw+(frame%8)*cw+x);a=px[i+3]/255
                        sheet[d:d+4]=bytes([round(px[i+k]*a+sheet[d+k]*(1-a)) for k in range(3)]+[255])
            (out/(role+'-stock-sheet.png')).write_bytes(gtmat.png_from_rgba(sw,ch*((count+7)//8),sheet));results[role]=rows
    (out/'stock-statistics.json').write_text(json.dumps(results,indent=2))
    return {k:{'visible_frames':sum('bounds' in r for r in v),'median_mean_luma':statistics.median(r['luma_mean'] for r in v if 'bounds' in r),'median_bounds':[statistics.median(r['bounds'][i] for r in v if 'bounds' in r) for i in range(4)]} for k,v in results.items()}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(audit(a.archive,a.output),indent=2))
