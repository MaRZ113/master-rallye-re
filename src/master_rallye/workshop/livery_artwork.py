"""Live-view artwork composition using the existing SDK UI presentation API."""
from pathlib import Path
import json
import struct
import zlib
from PIL import Image
from master_rallye.addon_sdk.ui_preview import compose_preview,PROFILES
from master_rallye.dxt import parse_dxt_bytes,encode_dxt_pixels,PNG_ROWS_FLIP_VERTICAL
from .texture_images import rgba_png,load_image
from .service import sha,write_json


def default_presets():
    return {role:{'azimuth':42. if role=='vehicle_select_art' else -90.,'elevation':10. if role=='vehicle_select_art' else 0.,'frame_scale':1.,'fov':24.,'preset_version':3,
        'pan_x':0.,'pan_y':0.,'key':p['key'],'ambient':p['ambient'],'orthographic':role=='smallcarsheet',
        'background':'transparent'} for role,p in PROFILES.items()}


def normalize_presets(presets):
    """Upgrade only old built-in defaults; retain intentional owner settings."""
    defaults=default_presets();result={}
    for role,default in defaults.items():
        old=presets.get(role,{})
        if not old:result[role]=default;continue
        if old.get('preset_version')==3:result[role]={**default,**old};continue
        if old.get('preset_version')==2:
            result[role]={**default,**old,'frame_scale':1/old.get('zoom',1.),'preset_version':3};result[role].pop('zoom',None);continue
        reference=PROFILES[role]
        built_in=(old.get('azimuth'),old.get('elevation'),old.get('zoom'),old.get('pan_x'),old.get('pan_y'))==(*reference['camera'],.7,0.,0.)
        result[role]=default if built_in else {**default,**old,'frame_scale':.7/old.get('zoom',.7),'preset_version':3}
        result[role].pop('zoom',None)
    return result


def recover_coverage(black,white):
    """Dual-background coverage from the same fixed-function render, not keying."""
    black=Image.open(black).convert('RGB');white=Image.open(white).convert('RGB')
    if black.size!=white.size:raise ValueError('Art render dimensions mismatch')
    b,w=black.tobytes(),white.tobytes();rgba=bytearray(black.width*black.height*4)
    for i in range(black.width*black.height):
        src=i*3;dest=i*4;alpha=255-round(sum(max(0,w[src+k]-b[src+k]) for k in range(3))/3)
        rgba[dest:dest+4]=bytes([min(255,round(b[src+k]*255/alpha)) if alpha else 0 for k in range(3)]+[alpha])
    return black.width,black.height,bytes(rgba)


def compose_live(session,role,black,white,preset,output,*,model_role='complete.dx'):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    image=recover_coverage(black,white)
    source=rgba_png(*image);(output/'source.png').write_bytes(source)
    # The stock corpus medians are p90 166.109 / 202.787, matching v1;
    # v2's 190/220 targets made the new live captures unnecessarily bright.
    rgba,report=compose_preview(image,role,style='mr-native-v1');w,h=PROFILES[role]['size']
    # SDK auto-framing deliberately normalizes source bounds. Apply explicit
    # owner scale/placement afterwards, so those controls survive composition.
    scale=preset['frame_scale']
    im=Image.frombytes('RGBA',(w,h),rgba).convert('RGBa')
    bounds=im.getchannel('a').point(lambda a:255 if a>20 else 0).getbbox()
    # Keep a native-pixel guard even for an enlarged or offset custom preset.
    scale=min(scale,(w-2)/(bounds[2]-bounds[0]),(h-2)/(bounds[3]-bounds[1]))
    im=im.resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.LANCZOS).convert('RGBA')
    canvas=Image.new('RGBA',(w,h),(0,0,0,0))
    b=im.getchannel('A').point(lambda a:255 if a>20 else 0).getbbox()
    # Resampling/rounding can grow threshold coverage by a pixel. Re-measure
    # actual coverage, rather than trusting the requested floating-point scale.
    while b[2]-b[0]>w-2 or b[3]-b[1]>h-2:
        fit=min((w-3)/(b[2]-b[0]),(h-3)/(b[3]-b[1]))
        im=im.convert('RGBa').resize((max(1,int(im.width*fit)),max(1,int(im.height*fit))),Image.Resampling.LANCZOS).convert('RGBA')
        b=im.getchannel('A').point(lambda a:255 if a>20 else 0).getbbox()
    offset=((w-im.width)//2+round(preset['pan_x']*w/2),(h-im.height)//2+round(preset['pan_y']*h/2))
    offset=(max(1-b[0],min(w-1-b[2],offset[0])),max(1-b[1],min(h-1-b[3],offset[1])))
    canvas.alpha_composite(im,offset);rgba=canvas.tobytes();report['owner_placement']={'scale':scale,'offset':offset,'clipping':'clamped to one native pixel guard'}
    if preset['background']!='transparent':
        im=Image.frombytes('RGBA',(w,h),rgba);bg=Image.new('RGBA',im.size,preset['background']);bg.alpha_composite(im);rgba=bg.tobytes()
    raw=rgba_png(w,h,rgba);(output/'image.png').write_bytes(raw)
    entry={'role':role,'origin':'Reconstruction','method':'Live D3D9 fitted camera + SDK stock-tone composition',
        'historical_original':False,'png':str(output/'image.png'),'sha256':sha(raw),'source_png':str(output/'source.png'),
        'source_sha256':sha(source),'dimensions':[w,h],'preset':preset,'composition':report,
        'livery_id':session.metadata['livery_id'],'physical_id':session.metadata['physical_id'],
        'model_variant':session.metadata['model_variant'],'source_model':model_role,'input_signature':session.signature()}
    write_json(output/'generation.json',entry)
    return entry


def import_manual(session,role,path,origin,output,*,scale_to_native=False):
    w,h,rgba,warnings=load_image(path)
    # Historical exact native pixels retain their authored placement and tone.
    size=PROFILES[role]['size']
    source=rgba_png(w,h,rgba);source_size=[w,h]
    if (w,h)!=size:
        if not scale_to_native:raise ValueError(f'Manual artwork must match native {size[0]} x {size[1]} pixels; explicit scaling is required')
        from PIL import ImageOps
        im=Image.frombytes('RGBA',(w,h),rgba)
        im=ImageOps.contain(im.convert('RGBa'),size,Image.Resampling.LANCZOS).convert('RGBA')
        canvas=Image.new('RGBA',size,(0,0,0,0));canvas.alpha_composite(im,((size[0]-im.width)//2,(size[1]-im.height)//2));w,h=size;rgba=canvas.tobytes()
        warnings.append('Explicit full-canvas scaling to native size; source pixels retained separately; no tone adjustment or atlas crop')
    output=Path(output);output.mkdir(parents=True,exist_ok=False);raw=rgba_png(w,h,rgba);(output/'image.png').write_bytes(raw);(output/'source.png').write_bytes(source)
    return {'role':role,'origin':origin,'historical_original':origin in ('Original','Historical'),
        'method':'Manual image; native pixel placement retained' if source_size==list(size) else 'Manual image; explicitly scaled full canvas, original retained',
        'png':str(output/'image.png'),'sha256':sha(raw),'source_png':str(output/'source.png'),'source_sha256':sha(source),'source_dimensions':source_size,
        'dimensions':[w,h],'source_name':Path(path).name,'livery_id':session.metadata['livery_id'],
        'physical_id':session.metadata['physical_id'],'model_variant':session.metadata['model_variant'],'warnings':warnings}


def export_resource(entry,template,output):
    """Caller supplies a qualified native frame; no bank or ID is allocated."""
    from master_rallye.texture_authoring import decode_rgba_png
    t=parse_dxt_bytes(Path(template).read_bytes());w,h,rgba=decode_rgba_png(Path(entry['png']).read_bytes())
    raw=bytearray(encode_dxt_pixels(t,rgba,w,h,row_policy=PNG_ROWS_FLIP_VERTICAL))
    struct.pack_into('<I',raw,8,zlib.crc32(raw[20:])&0xffffffff);Path(output).write_bytes(raw)
    return {'template_sha256':sha(Path(template).read_bytes()),'resource_sha256':sha(raw),'dimensions':[w,h],
        'placement':'Standalone frame only; existing append-only SDK bank compiler owns runtime integration'}
