"""Bounded Tex1 GS-memory reconstruction from immutable user-supplied bytes.

Implements actual transfer/destination address maps, not PNG numbering guesses.
PSMCT32/24 transfers, PSMT4/8 and CT32/24 sampling are admitted; other formats
fail explicitly. Raw PS2 alpha is retained (unity=128), separate from PNG alpha.
Address layouts are checked against the local PDTools GS readers and synthetic
round trips. No GT textures, palettes or external game libraries are bundled.
"""
from __future__ import annotations
import hashlib
from .gt4_source import Reader


def address32(bp,bw,x,y):
    bx,by=(x&63)>>3,(y&31)>>3
    block=(bx&1)|((by&1)<<1)|((bx&2)<<1)|((by&2)<<2)|((bx&4)<<2)
    word=(x&1)|((y&1)<<1)|((x&6)<<1)
    return bp*256+((x>>6)+(y>>5)*bw)*8192+block*256+((y&7)>>1)*64+word*4


def address_indexed(bp,bw,x,y,bits):
    if bits not in (4,8):raise ValueError('indexed format')
    if bits==8:
        bx,by=(x&127)>>4,(y&63)>>4
        block=(bx&1)|((by&1)<<1)|((bx&2)<<1)|((by&2)<<2)|((bx&4)<<2)
        page=(x>>7)+(y>>6)*(bw>>1)
    else:
        bx,by=(x&127)>>5,(y&127)>>4
        block=((bx&1)<<1)|(by&1)|((bx&2)<<2)|((by&2)<<1)|((by&4)<<2)
        page=(x>>7)+(y>>7)*(bw>>1)
    column=(y&15)>>2
    word=((x&1)|((x&6)<<1)|((y&1)<<1)) ^ ((((y>>1)^(y>>2))&1)<<3)
    part=((x&((16 if bits==4 else 8)*2-1))>>3)*2+((y>>1)&1)
    base=bp*256+page*8192+block*256+column*64+word*4
    return (base+part,0) if bits==8 else (base+(part>>1),(part&1)*4)


class TextureSet:
    def __init__(self,data,offset):
        r=Reader(data);self.source_offset=offset
        if r.get('4s',offset)[0]!=b'Tex1':raise ValueError('expected Tex1')
        size=r.get('I',offset+12)[0]
        if size==0:
            # Race-wheel LODs contain an explicit empty bank: Tex1 followed by
            # an all-zero header. Preserve its index; do not alias another LOD.
            header=r.get('48s',offset)[0]
            if any(header[4:]):raise ValueError('nonempty zero-size Tex1 header')
            self.data=header;self.registers=[];self.transfers=[];self.cache={};self.memory=self.written=bytearray();return
        if not 48<=size<=16*1024*1024:raise ValueError('Tex1 size budget')
        self.data=r.get(f'{size}s',offset)[0];r=Reader(self.data)
        n,nt,map_at,transfers_at,patches_at=r.get('HHIII',20)
        if n>4096 or nt>4096:raise ValueError('Tex1 table budget')
        if patches_at and r.get('I',patches_at)[0]:raise ValueError('Tex1 CLUT variation patches not yet admitted')
        self.registers=[];self.transfers=[];self.memory=bytearray(4*1024*1024);self.written=bytearray(len(self.memory));self.cache={}
        for i in range(n):
            tex0,tex1,mip1,mip2,clamp=r.get('5Q',map_at+40*i)
            self.registers.append({'tex0':tex0,'tex1':tex1,'clamp':clamp,
                'bp':tex0&0x3fff,'bw':tex0>>14&63,'psm':tex0>>20&63,
                'width':1<<(tex0>>26&15),'height':1<<(tex0>>30&15),
                'tcc':tex0>>34&1,'tfx':tex0>>35&3,'cbp':tex0>>37&0x3fff,
                'cpsm':tex0>>51&15,'csm':tex0>>55&1,'csa':tex0>>56&31,
                'wrap_s':clamp&3,'wrap_t':clamp>>2&3,'min_u':clamp>>4&1023,
                'max_u':clamp>>14&1023,'min_v':clamp>>24&1023,'max_v':clamp>>34&1023})
        for i in range(nt):
            off,bp,bw,fmt,w,h=r.get('IHBBHH',transfers_at+12*i)
            if fmt not in (0,1):raise ValueError(f'unsupported GS transfer PSM {fmt}')
            if not 0<w<=4096 or not 0<h<=4096 or w*h>4*1024*1024:raise ValueError('GS transfer dimensions')
            # For these GT texture sets PSMCT24 transfer units remain four bytes,
            # matching PGLU transfer storage; 24-bit sampling ignores stored alpha.
            pixels=r.get(f'{w*h*4}s',off)[0]
            for y in range(h):
                for x in range(w):
                    a=address32(bp,bw,x,y);s=(y*w+x)*4
                    self._range(a,4);self.memory[a:a+4]=pixels[s:s+4];self.written[a:a+4]=b'\1'*4
            self.transfers.append({'offset':off,'bp':bp,'bw':bw,'psm':fmt,'width':w,'height':h,'sha256':hashlib.sha256(pixels).hexdigest()})

    def _range(self,at,n):
        if not 0<=at<=len(self.memory)-n:raise ValueError('GS memory range exceeds 4 MiB')

    def _read(self,at,n):
        self._range(at,n)
        if not all(self.written[at:at+n]):raise ValueError('texture or palette references uninitialised GS bytes')
        return self.memory[at:at+n]

    def texture(self,index):
        if not 0<=index<len(self.registers):raise ValueError('texture index out of bounds')
        if index in self.cache:return self.cache[index]
        t=self.registers[index];w,h=t['width'],t['height'];psm=t['psm'];palette=None
        if w*h>4*1024*1024:raise ValueError('texture dimensions budget')
        if psm in (19,20):
            if t['cpsm']!=0 or t['csm']!=0:raise ValueError('unqualified CLUT format/storage mode')
            count=16 if psm==20 else 256;pw=8 if psm==20 else 16
            palette=[self._read(address32(t['cbp'],1,i%pw,i//pw)+t['csa']*32,4) for i in range(count)]
            if psm==19:palette=[palette[(i&~24)|((i&8)<<1)|((i&16)>>1)] for i in range(count)]
        elif psm not in (0,1):raise ValueError(f'unsupported GS texture PSM {psm}')
        rgba=bytearray(w*h*4)
        for y in range(h):
            for x in range(w):
                if palette is not None:
                    at,shift=address_indexed(t['bp'],t['bw'],x,y,4 if psm==20 else 8)
                    palette_index=(self._read(at,1)[0]>>shift)&(15 if psm==20 else 255);v=palette[palette_index]
                else:v=self._read(address32(t['bp'],t['bw'],x,y),4)
                at=(y*w+x)*4;rgba[at:at+4]=v
                if psm==1:rgba[at+3]=128
        result={'width':w,'height':h,'rgba_ps2':bytes(rgba),'registers':t}
        self.cache[index]=result;return result


def display_rgba(texture):
    result=bytearray(texture['rgba_ps2'])
    for i in range(3,len(result),4):result[i]=min(255,(result[i]*255)//128)
    return bytes(result)


def model_texture_sets(data,base=0,colour=0):
    r=Reader(data);lods,cols=r.get('HH',base+28)
    if not 0<=colour<cols:raise ValueError('ModelSet colour out of bounds')
    table=r.get('I',base+68)[0];listing=r.get('I',base+table+4*colour)[0]
    return [TextureSet(data,base+r.get('I',base+listing+4*i)[0]) for i in range(lods)]
