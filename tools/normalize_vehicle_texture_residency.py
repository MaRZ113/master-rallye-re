"""Optional deterministic private texture-size normalization; geometry is copied intact.

No assets are bundled. This is a lossy authoring option, not GT source decoding.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.addon_sdk.texture_budget import texture_working_set


def box_resize(raw,width,height,target_width,target_height):
    """Integer area average, independent of Pillow or GPU sampling versions."""
    if width%target_width or height%target_height:raise ValueError('normalization requires integer reduction factors')
    sx,sy=width//target_width,height//target_height;area=sx*sy;out=bytearray(target_width*target_height*4)
    for y in range(target_height):
        for x in range(target_width):
            sums=[0,0,0,0]
            for yy in range(y*sy,(y+1)*sy):
                for xx in range(x*sx,(x+1)*sx):
                    at=(yy*width+xx)*4
                    for c in range(4):sums[c]+=raw[at+c]
            at=(y*target_width+x)*4
            out[at:at+4]=bytes((s+area//2)//area for s in sums)
    return bytes(out)


def normalize(source,output,max_edge=None,*,preset=None,profile=None):
    if (max_edge is None)==(preset is None):raise ValueError('select explicit max_edge or quality preset')
    if max_edge is not None and max_edge not in (64,128,256,512,1024):raise ValueError('max_edge must be an admitted power-of-two authoring limit')
    if output.exists():raise ValueError('output exists; original authoring assets must be preserved')
    if output.resolve().is_relative_to(source.resolve()):raise ValueError('output must be outside the immutable source directory')
    if not source.is_dir() or any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in source.iterdir()):raise ValueError('source must contain ordinary local files')
    if any(p.is_dir() for p in source.iterdir()):raise ValueError('expected a flat vehicle asset directory')
    quality=None
    if preset:
        from master_rallye.addon_sdk.texture_quality import plan_textures
        quality=plan_textures(source,preset=preset,profile=profile)
    decisions={x['file']:x for x in quality['textures']} if quality else {}
    before=texture_working_set(source);output.mkdir(parents=True);records=[]
    for path in sorted(source.iterdir()):
        raw=path.read_bytes();result=raw;entry={'file':path.name,'source_sha256':hashlib.sha256(raw).hexdigest(),'changed':False}
        if path.suffix.lower()=='.dxt':
            tex=parse_dxt_bytes(raw);w,h=tex.width,tex.height;factor=1
            if quality:factor=decisions[path.name]['factor']
            else:
                while max(w//factor,h//factor)>max_edge:factor*=2
            if factor>1:
                if w%factor or h%factor or min(w//factor,h//factor)<1:raise ValueError('texture aspect cannot preserve integer reduction')
                tw,th=w//factor,h//factor;pixels=box_resize(tex.bgra,w,h,tw,th)
                result=struct.pack('<5I',0xfeed,1,zlib.crc32(pixels)&0xffffffff,tw,th)+pixels;parse_dxt_bytes(result)
                entry.update(changed=True,source_size=[w,h],output_size=[tw,th],filter='deterministic integer BGRA area average; alpha averaged')
        (output/path.name).write_bytes(result);entry['output_sha256']=hashlib.sha256(result).hexdigest();records.append(entry)
    after=texture_working_set(output)
    report={'status':'PASS_BYTE_PRESERVING_SOURCE_FIDELITY' if preset=='source-fidelity' else 'PASS_OPTIONAL_LOSSY_TEXTURE_NORMALIZATION','max_edge':max_edge,'quality_policy':quality,'source':str(source.resolve()),'output':str(output.resolve()),'before':before,'after':after,'files':records,
        'boundary':'Only image resolution changes. DX bytes/material references/UVs unchanged. Filtered alpha edges require human rendering review; no source parity claim.'}
    (output.parent/(output.name+'-normalization.json')).write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True);group.add_argument('--max-edge',type=int);group.add_argument('--preset',choices=['source-fidelity','balanced','performance'])
    p.add_argument('--quality-profile',type=Path);a=p.parse_args()
    if a.quality_profile and not a.preset:p.error('--quality-profile requires --preset')
    r=normalize(a.source,a.output,a.max_edge,preset=a.preset,profile=json.loads(a.quality_profile.read_text()) if a.quality_profile else None)
    print(json.dumps({'before_bytes':r['before']['cache_bytes'],'after_bytes':r['after']['cache_bytes'],'changed_textures':sum(x['changed'] for x in r['files'])}))
