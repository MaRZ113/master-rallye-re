"""Optional local GT3 RoFS2.2 → named IMGS/Tex1 → PNG research workflow.

Uses a user-supplied GTPS2ModelTool for Tex1 decoding. No game assets are bundled.
Structure follows the locally inspected pez2k GT3VOLExtractor/GT3IMGRipper and
PDTools TextureSet1 readers; unknown layouts fail closed instead of string carving.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,subprocess,zlib
from pathlib import Path,PurePosixPath

def sha(b):return hashlib.sha256(b).hexdigest()

def inventory(path):
    with path.open('rb') as f:
        head=f.read(20)
        if len(head)!=20:raise ValueError('short VOL')
        magic,version,size,names,_=struct.unpack('<5I',head)
        if magic not in (0x53466f52,0xacb990ad) or version!=0x20002 or not 20<names<size<=16*1024*1024:
            raise ValueError('only GT3 RoFS2.2 supported')
        f.seek(0);b=f.read(size)
    if len(b)!=size:raise ValueError('truncated VOL header')
    strings=b[names:];strings=bytes(x^255 for x in strings) if magic==0xacb990ad else strings
    rows=[];visited=set();file_size=path.stat().st_size
    def walk(pos,parent,depth):
        if depth>32 or pos in visited or pos<20 or pos+8>names:raise ValueError('invalid VOL directory graph')
        visited.add(pos);word,value=struct.unpack_from('<2I',b,pos);flag=word&0x3000000;pointer=(word&0xffffff)-names
        if not 0<=pointer<len(strings):raise ValueError('VOL filename outside table')
        end=strings.find(b'\0',pointer)
        if end<0:raise ValueError('unterminated VOL filename')
        name=strings[pointer:end].decode('ascii')
        if name not in ('.','..') and (not name or '/' in name or '\\' in name or ':' in name):raise ValueError('unsafe VOL filename')
        full=parent/name if name!='.' else parent
        if flag==0x1000000:
            if value>100_000 or pos+8+4*value>names:raise ValueError('VOL directory outside header')
            for i in range(value):
                pointer=struct.unpack_from('<I',b,pos+8+4*i)[0]
                if pointer>=pos+12+4*i:walk(pointer,full,depth+1)  # original parent-directory sentinel
        elif flag in (0,0x2000000):
            length=struct.unpack_from('<I',b,pos+(12 if flag else 8))[0]
            expected=struct.unpack_from('<I',b,pos+8)[0]
            if value*2048+length>file_size:raise ValueError('VOL member outside file')
            rows.append({'path':full.as_posix(),'offset':value*2048,'size':length,'uncompressed_size':expected,'compressed':bool(flag)})
        else:raise ValueError('unknown VOL entry flag')
    walk(20,PurePosixPath(),0)
    if len({r['path'] for r in rows})!=len(rows):raise ValueError('duplicate VOL member names')
    return rows

def read_member(path,member):
    rows=inventory(path);matches=[r for r in rows if r['path']==member]
    if len(matches)!=1:raise ValueError('GT3 member absent or ambiguous')
    row=matches[0]
    if row['size']>64*1024*1024 or row['uncompressed_size']>64*1024*1024:raise ValueError('UI member too large')
    with path.open('rb') as f:f.seek(row['offset']);raw=f.read(row['size'])
    if row['compressed']:
        if raw[:2]==b'\x1f\x8b':decoder=zlib.decompressobj(31);payload=raw
        elif raw[:4]==bytes.fromhex('c5eef7ff'):decoder=zlib.decompressobj(-15);payload=raw[8:]
        else:raise ValueError('unknown GT3 compression wrapper')
        data=decoder.decompress(payload,row['uncompressed_size']+1)
        if not decoder.eof or len(data)!=row['uncompressed_size']:raise ValueError('GT3 member decoded size mismatch')
    else:data=raw
    return data,{**row,'stored_sha256':sha(raw),'decoded_sha256':sha(data),'inventory_count':len(rows)}

def named_texture(data,name):
    if data[:8]!=b'IMGS\0\0\0\0' or len(data)<16:raise ValueError('not an admitted GT3 IMGS bank')
    count,start=struct.unpack_from('<2I',data,8)
    if not 0<count<=4096 or start!=16+count*64 or start>=len(data):raise ValueError('unsupported IMGS table')
    names={}
    for i in range(count):
        record=data[16+i*64:16+(i+1)*64];label=record[:60].split(b'\0')[0].decode('ascii');index=struct.unpack_from('<I',record,60)[0]
        if label in names or index>=count:raise ValueError('ambiguous IMGS index')
        names[label]=index
    textures=[];pos=start
    for i in range(count):
        if pos+16>len(data) or data[pos:pos+4]!=b'Tex1':raise ValueError('IMGS texture span is not Tex1')
        size=struct.unpack_from('<I',data,pos+12)[0]
        if size<48 or pos+size>len(data):raise ValueError('Tex1 outside IMGS')
        textures.append((pos,data[pos:pos+size]));pos=(pos+size+15)&~15
    if pos!=len(data):raise ValueError('unparsed IMGS trailing data')
    if name not in names:raise ValueError('image key not present in IMGS')
    index=names[name];offset,texture=textures[index]
    aliases=[label for label,idx in names.items() if textures[idx][1]==texture]
    return texture,{'name':name,'texture_index':index,'offset':offset,'sha256':sha(texture),
        'identical_named_images':aliases,'status':'SHARED_TEXTURE_REVIEW_REQUIRED' if len(aliases)>1 else 'EXTRACTED_VISUAL_REVIEW_REQUIRED'}

def pmb_texture(data,index):
    """Select a bounded Tex1 entry using pez2k GT3PMBDumper's offset table.

    An explicit index is required: menu display-list names are not treated as a
    universal vehicle-ID mapping. Compressed entries are size checked.
    """
    if len(data)<16:raise ValueError('short PMB')
    kind,head,count,start=struct.unpack_from('<4I',data)
    if kind not in (14,15) or head!=16 or not 0<count<=4096 or start<16 or start+8*count>len(data):raise ValueError('unsupported PMB table')
    if type(index) is not int or not 0<=index<count:raise ValueError('PMB texture index out of bounds')
    rows=[struct.unpack_from('<2I',data,start+8*i) for i in range(count)]
    offsets=[r[1] for r in rows]+[len(data)]
    if offsets[0]<start+8*count or any(a>=b for a,b in zip(offsets,offsets[1:])):raise ValueError('invalid PMB entry spans')
    size,off=rows[index];end=offsets[index+1];raw=data[off:end]
    if not 16<=size<=16*1024*1024:raise ValueError('PMB entry size invalid')
    if raw.startswith(b'\x1f\x8b'):
        dec=zlib.decompressobj(31);chunk=dec.decompress(raw,size+1)
        if not dec.eof or len(chunk)!=size or any(dec.unused_data):raise ValueError('PMB gzip size/padding mismatch')
    else:chunk=raw
    if chunk[:4]!=b'Tex1' or len(chunk)<16:raise ValueError('PMB entry is not Tex1')
    length=struct.unpack_from('<I',chunk,12)[0]
    if not 16<=length<=len(chunk) or any(chunk[length:]):raise ValueError('PMB Tex1 length/padding mismatch')
    texture=chunk[:length]
    return texture,{'texture_index':index,'offset':off,'stored_size':end-off,'decoded_size':len(chunk),'sha256':sha(texture),'status':'INDEXED_TEXTURE_VISUAL_REVIEW_REQUIRED','mapping_policy':'explicit caller index; no inferred vehicle identity'}

def key_border_background(image,rgb):
    """Optional explicit colour key, limited to exact border-connected pixels.

    This is an authoring conversion, not a claim about GT3 native alpha.
    Interior pixels of the same colour are retained unless connected to border.
    """
    w,h,source=image
    if len(rgb)!=3 or any(type(c) is not int or not 0<=c<=255 for c in rgb):raise ValueError('background key requires three byte values')
    out=bytearray(source);key=bytes(rgb);seen=set();stack=[(x,y) for y in (0,h-1) for x in range(w)]+[(x,y) for x in (0,w-1) for y in range(h)];removed=0
    while stack:
        x,y=stack.pop()
        if not 0<=x<w or not 0<=y<h or (x,y) in seen:continue
        seen.add((x,y));i=4*(y*w+x)
        if source[i:i+3]!=key:continue
        out[i+3]=0;removed+=1;stack.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
    if removed==0:raise ValueError('background key has no border-connected pixels')
    return (w,h,bytes(out)),{'method':'explicit exact border-connected colour key; not source alpha','rgb':list(rgb),'pixels_cleared':removed}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vol',type=Path,required=True);p.add_argument('--bank-member',required=True);selector=p.add_mutually_exclusive_group(required=True);selector.add_argument('--image-name');selector.add_argument('--pmb-index',type=int);p.add_argument('--decoder',type=Path,required=True);p.add_argument('--background-key',help='optional explicit R,G,B key; border-connected exact pixels only');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('output exists; refusing overwrite')
    bank,source=read_member(a.vol,a.bank_member)
    texture,report=pmb_texture(bank,a.pmb_index) if a.pmb_index is not None else named_texture(bank,a.image_name)
    a.output.mkdir(parents=True);img=a.output/'icon.img';img.write_bytes(texture)
    proc=subprocess.run([str(a.decoder.resolve()),str(img.resolve())],capture_output=True,text=True)
    (a.output/'decoder.log').write_text(proc.stdout+proc.stderr,encoding='utf-8')
    if proc.returncode or not img.with_suffix('.png').is_file():raise ValueError('Tex1 decoder failed or emitted multiple textures; inspect decoder.log')
    if a.background_key:
        from master_rallye.texture_authoring import decode_rgba_png
        from gtmat import png_from_rgba
        decoded=img.with_suffix('.png').read_bytes();(a.output/'decoder.png').write_bytes(decoded)
        image,key_report=key_border_background(decode_rgba_png(decoded),tuple(int(x) for x in a.background_key.split(',')))
        img.with_suffix('.png').write_bytes(png_from_rgba(*image));report['background_conversion']=key_report;report['decoder_png_sha256']=sha(decoded)
    report.update(source=source,decoder_sha256=sha(a.decoder.read_bytes()),png_sha256=sha(img.with_suffix('.png').read_bytes()))
    (a.output/'extraction.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
