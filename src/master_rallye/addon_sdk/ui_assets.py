"""Optional, bounded UI bank extension. No GT data or third-party decoder required."""
from __future__ import annotations
import hashlib,json,struct,zlib
from pathlib import Path,PurePosixPath
from ..dxt import parse_dxt_bytes,encode_dxt_pixels,decode_rgba_pixels
from ..texture_authoring import decode_rgba_png
from ..vehicle_packaging import _open_sma_archive
from .manifest import AddonValidationError

BANKS={
 'vehicle_select_art':('DataGx/Frontend/VehicleSelect/carsheet',32,23,(128,128)),
 'smallcarsheet':('DataGx/Frontend/RaceResults/smallcarsheet',30,13,(32,16)),
}

def sha(data):return hashlib.sha256(data).hexdigest()

def parse_bank(data:bytes):
    """Admit the observed v125 bank: identity pairs and two sprite parts/frame.

    Each part has 12 opaque scalar words followed by a counted ASCII texture
    name. Scalar words are retained, not assigned invented native meanings.
    """
    if len(data)<16:raise AddonValidationError('short DXB bank')
    magic,version,count=struct.unpack_from('<3I',data)
    if (magic,version)!=(0xf001,125) or not 1<=count<=128:raise AddonValidationError('unsupported DXB profile')
    pos=12
    for i in range(count):
        if pos+8>len(data) or struct.unpack_from('<2I',data,pos)!=(i,i):raise AddonValidationError('nonidentity bank mapping')
        pos+=8
    if pos+4>len(data) or struct.unpack_from('<I',data,pos)[0]!=count:raise AddonValidationError('bank frame counts disagree')
    pos+=4;records=[];names=[]
    for i in range(count):
        start=pos
        if pos+4>len(data) or struct.unpack_from('<I',data,pos)[0]!=2:raise AddonValidationError('unsupported sprite part count')
        pos+=4;current=[]
        for _ in range(2):
            if pos+52>len(data):raise AddonValidationError('truncated sprite part')
            length=struct.unpack_from('<I',data,pos+48)[0]
            if not 1<=length<=128 or pos+52+length>len(data):raise AddonValidationError('invalid sprite name length')
            try:name=data[pos+52:pos+52+length].decode('ascii')
            except UnicodeDecodeError as exc:raise AddonValidationError('non ASCII sprite name') from exc
            if not name.replace('_','').isalnum():raise AddonValidationError('unsafe sprite name')
            current.append(name);pos+=52+length
        if current[0]!=current[1]:raise AddonValidationError('two sprite parts use different textures')
        records.append(data[start:pos]);names.append(current[0])
    if pos!=len(data):raise AddonValidationError('unparsed bank tail')
    return {'count':count,'records':records,'names':names}

def append_frame(data,template_frame):
    bank=parse_bank(data);count=bank['count']
    if count>=128 or not 0<=template_frame<count:raise AddonValidationError('bank frame range exceeded')
    old=bank['names'][template_frame];prefix,frame,suffix=old.rsplit('_',2)
    if frame!=f'{template_frame:03d}' or suffix!='000':raise AddonValidationError('unsupported frame name convention')
    name=f'{prefix}_{count:03d}_000'
    record=bank['records'][template_frame].replace(old.encode(),name.encode())
    result=struct.pack('<3I',0xf001,125,count+1)+b''.join(struct.pack('<2I',i,i) for i in range(count+1))
    result+=struct.pack('<I',count+1)+b''.join(bank['records'])+record
    after=parse_bank(result)
    if after['records'][:-1]!=bank['records']:raise AddonValidationError('stock bank records changed')
    return result,name

def alpha_bounds(image,threshold=20):
    w,h,px=image;points=((i%w,i//w) for i,a in enumerate(px[3::4]) if a>threshold)
    x0,y0,x1,y1=w,h,0,0
    for x,y in points:x0=min(x0,x);y0=min(y0,y);x1=max(x1,x+1);y1=max(y1,y+1)
    if x1==0:raise AddonValidationError('reference icon has no visible alpha bounds')
    return (x0,y0,x1,y1)

def fit_rgba(image,width,height,padding=1,*,target_bounds=None):
    """Crop visible bounds and contain, area-filtering premultiplied RGBA."""
    sw,sh,px=image
    if sw*sh>16_777_216 or len(px)!=sw*sh*4:raise AddonValidationError('invalid/oversized icon')
    x0,y0,x1,y1=sw,sh,0,0
    for i,a in enumerate(px[3::4]):
        if a:
            x,y=i%sw,i//sw;x0=min(x0,x);y0=min(y0,y);x1=max(x1,x+1);y1=max(y1,y+1)
    if x1==0:raise AddonValidationError('icon is fully transparent')
    tx0,ty0,tx1,ty1=target_bounds or (0,0,width,height)
    if not 0<=tx0<tx1<=width or not 0<=ty0<ty1<=height or min(tx1-tx0,ty1-ty0)<=2*padding:
        raise AddonValidationError('invalid icon target bounds')
    cw,ch=x1-x0,y1-y0;scale=min((tx1-tx0-2*padding)/cw,(ty1-ty0-2*padding)/ch)
    dw,dh=max(1,round(cw*scale)),max(1,round(ch*scale));ox,oy=tx0+(tx1-tx0-dw)//2,ty0+(ty1-ty0-dh)//2
    out=bytearray(width*height*4)
    for y in range(dh):
        ya,yb=y0+y*ch/dh,y0+(y+1)*ch/dh
        for x in range(dw):
            xa,xb=x0+x*cw/dw,x0+(x+1)*cw/dw;tot=alpha=0.;rgb=[0.,0.,0.]
            for yy in range(int(ya),min(sh,int(yb)+1)):
                for xx in range(int(xa),min(sw,int(xb)+1)):
                    weight=max(0,min(xb,xx+1)-max(xa,xx))*max(0,min(yb,yy+1)-max(ya,yy));i=4*(yy*sw+xx)
                    tot+=weight;alpha+=px[i+3]*weight
                    for k in range(3):rgb[k]+=px[i+k]*px[i+3]*weight
            i=4*((oy+y)*width+ox+x)
            out[i:i+4]=bytes([round(v/alpha) if alpha else 0 for v in rgb]+[round(alpha/tot) if tot else 0])
    return bytes(out)

def archive_member(archive,path):
    names=[n for n in archive.namelist() if n.casefold()==path.casefold()]
    if len(names)!=1:raise AddonValidationError('absent or ambiguous stock UI member: '+path)
    return archive.read(names[0])

def build_ui_assets(root,addon,data_sma):
    selected={key for key in BANKS if addon['frontend'][key]['policy']=='project_frame'}
    if not selected:return {},None
    config=json.loads((root/'ui-assets.json').read_text(encoding='utf-8'))
    if not isinstance(config,dict) or set(config)!= {'version','icons'} or config['version']!=1 or not isinstance(config['icons'],dict) or set(config['icons'])!=selected:
        raise AddonValidationError('UI sidecar must match exactly the project_frame roles')
    assets={};report={'version':1,'roles':{}}
    with _open_sma_archive(data_sma) as archive:
        for role in sorted(selected):
            prefix,count,template,size=BANKS[role];item=config['icons'][role]
            if not isinstance(item,dict) or not {'png','sha256'}<=set(item) or set(item)-{'png','sha256','presentation'} or not isinstance(item['png'],str) or not isinstance(item['sha256'],str):raise AddonValidationError('UI icon needs png and sha256')
            if item.get('presentation','legacy') not in ('legacy','mr-native-v1'):raise AddonValidationError('unsupported UI presentation profile')
            relative=PurePosixPath(item['png'])
            if relative.is_absolute() or any(part in ('.','..') or ':' in part or '\\' in part for part in relative.parts):
                raise AddonValidationError('UI PNG must be a safe path inside project')
            path=root.joinpath(*relative.parts)
            if root.resolve() not in path.resolve().parents:raise AddonValidationError('UI PNG must be inside project')
            # Reject links on every component, including Windows junctions.
            current=root
            for part in relative.parts:
                current=current/part
                if current.is_symlink() or getattr(current,'is_junction',lambda:False)():raise AddonValidationError('linked UI path')
            raw=path.read_bytes()
            if sha(raw)!=item['sha256']:raise AddonValidationError('UI PNG hash mismatch')
            original=archive_member(archive,prefix+'.dxb');bank=parse_bank(original)
            if bank['count']!=count or addon['frontend'][role]['frame']!=count:raise AddonValidationError('project_frame must append exactly one stock bank frame')
            newbank,name=append_frame(original,template)
            tex=parse_dxt_bytes(archive_member(archive,f'{prefix}_{template:03d}_000.dxt'))
            if (tex.width,tex.height)!=size:raise AddonValidationError('stock icon dimensions changed')
            image=decode_rgba_png(raw)
            # CarSheet art is authored in the lower portion of the texture.
            # Retain native DXB rects and align pixels to the donor artwork region.
            bounds=alpha_bounds((*size,decode_rgba_pixels(tex))) if role=='vehicle_select_art' else None
            style=None
            if item.get('presentation')=='mr-native-v1':
                from .ui_preview import compose_preview
                rgba,style=compose_preview(image,role)
            else:rgba=fit_rgba(image,*size,padding=1,target_bounds=bounds)
            frame_path=prefix.rsplit('/',1)[0]+'/'+name+'.dxt'
            pixels=bytearray(encode_dxt_pixels(tex,rgba,*size))
            # Observed across the stock UI corpus: word0x08 is CRC32 of stored BGRA.
            # A new frame must not retain the donor pixel identity/checksum.
            struct.pack_into('<I',pixels,8,zlib.crc32(pixels[20:])&0xffffffff)
            assets[prefix+'.dxb']=newbank;assets[frame_path]=bytes(pixels)
            report['roles'][role]={'frame':count,'template':template,'dimensions':list(size),'png_sha256':sha(raw),
                'stock_bank_sha256':sha(original),'bank_path':prefix+'.dxb','frame_path':frame_path,
                'bank_sha256':sha(newbank),'frame_sha256':sha(assets[frame_path]),'stock_records_byte_identical':True}
            if bounds:report['roles'][role]['alignment']={'method':'stock template alpha bounds','target_bounds':list(bounds),'output_bounds':list(alpha_bounds((*size,rgba)))}
            if style:
                report['roles'][role]['presentation']=style
                report['roles'][role]['alignment']={'method':'mr-native-v1 grounded role composition','output_bounds':style['bounds']}
    return assets,report

def verify_ui_resources(root,row,archive):
    """Runtime composition admits only append-only banks based on its stock SMA."""
    report=json.loads((root/'ui-assets.report.json').read_text());assets={}
    selected={key for key in BANKS if row['frontend'][key]['policy']=='project_frame'}
    if report.get('version')!=1 or set(report.get('roles',{}))!=selected:raise AddonValidationError('UI build report mismatch')
    for role in selected:
        prefix,count,template,size=BANKS[role];r=report['roles'][role]
        original=archive_member(archive,prefix+'.dxb');expected,name=append_frame(original,template)
        bankpath=prefix+'.dxb';texpath=prefix.rsplit('/',1)[0]+'/'+name+'.dxt'
        if r['bank_path']!=bankpath or r['frame_path']!=texpath or r['frame']!=count or row['frontend'][role]['frame']!=count:raise AddonValidationError('UI frame reference mismatch')
        bank=(root/bankpath).read_bytes();texture=(root/texpath).read_bytes();t=parse_dxt_bytes(texture)
        if bank!=expected or sha(bank)!=r['bank_sha256'] or sha(texture)!=r['frame_sha256'] or (t.width,t.height)!=size or t.word_0x08!=zlib.crc32(t.bgra)&0xffffffff:
            raise AddonValidationError('invalid appended UI resources')
        assets[bankpath]=bank;assets[texpath]=texture
    return assets
