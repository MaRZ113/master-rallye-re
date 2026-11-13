"""Read-only bounded Xbox XDVDFS and GameCube RVZ/FST inspection.

Independent implementation from published filesystem/RVZ specifications. Not a
general disc repair/converter. RVZ support is deliberately GC/Zstandard only.
"""
from pathlib import Path
import hashlib
import struct
from functools import lru_cache

MAX_READ=256*1024*1024
MAX_ENTRIES=50000

def span(offset,size,total):
    if type(offset)is not int or type(size)is not int or offset<0 or size<0 or size>MAX_READ or offset+size>total:
        raise ValueError('disc span/budget')

class FileReader:
    def __init__(self,path):
        self.path=Path(path);self.size=self.path.stat().st_size
    def read(self,offset,size):
        span(offset,size,self.size)
        with self.path.open('rb')as f:f.seek(offset);data=f.read(size)
        if len(data)!=size:raise ValueError('short disc read')
        return data

def xdvdfs(reader,partition):
    magic=b'MICROSOFT*XBOX*MEDIA';head=reader.read(partition+0x10000,2048)
    if head[:20]!=magic or head[-20:]!=magic:raise ValueError('XDVDFS volume signature')
    sector,size=struct.unpack_from('<II',head,20);rows=[];directories=set();names=set();directory_bytes=0
    def directory(sec,size,parent,depth):
        nonlocal directory_bytes
        if depth>32 or size>4*1024*1024 or(sec,size)in directories:raise ValueError('directory cycle/budget')
        directory_bytes+=size
        if directory_bytes>64*1024*1024:raise ValueError('aggregate directory budget')
        directories.add((sec,size));data=reader.read(partition+sec*2048,size);seen=set()
        def entry(off,level):
            if level>256 or off in seen or off+14>len(data):raise ValueError('XDVDFS entry cycle/span')
            seen.add(off);left,right,s,n,flags,length=struct.unpack_from('<HHIIBB',data,off)
            if not length or off+14+length>len(data):raise ValueError('XDVDFS name span')
            name=data[off+14:off+14+length].decode('ascii')
            if name in('.','..')or any(c in name for c in '/\\:\0'):raise ValueError('unsafe disc name')
            path=parent+name
            if path.casefold()in names:raise ValueError('duplicate disc path')
            names.add(path.casefold())
            if len(names)>MAX_ENTRIES:raise ValueError('disc entry budget')
            if left:entry(left*4,level+1)
            if flags&16:directory(s,n,path+'/',depth+1)
            else:
                span(partition+s*2048,n,reader.size)
                rows.append({'path':path,'offset':partition+s*2048,'bytes':n,'attributes':flags})
            if right:entry(right*4,level+1)
        if size:entry(0,0)
    directory(sector,size,'',0)
    return sorted(rows,key=lambda r:r['path'])

def _zstd(data,limit):
    from compression import zstd
    decoder=zstd.ZstdDecompressor(options={zstd.DecompressionParameter.window_log_max:23});out=decoder.decompress(data,max_length=limit+1)
    if len(out)>limit or not decoder.eof or decoder.unused_data:raise ValueError('RVZ zstd budget/frame')
    return out

def _padding(seed,size,offset):
    state=list(struct.unpack('>17I',seed))+[0]*504
    for i in range(17,521):state[i]=((state[i-17]<<23)^(state[i-16]>>9)^state[i-1])&0xffffffff
    def advance():
        for i in range(521):state[i]^=state[i+489]if i<32 else state[i-32]
    for _ in range(4):advance()
    skip=offset%32768;out=bytearray()
    while len(out)<size+skip:
        for v in state:out.extend((v>>24,(v>>18)&255,(v>>8)&255,v&255))
        advance()
    return bytes(out[skip:skip+size])

def unpack_rvz(data,expected,disc_offset):
    if expected>4*1024*1024:raise ValueError('RVZ chunk budget')
    out=bytearray();cursor=0
    while cursor<len(data):
        if cursor+4>len(data):raise ValueError('RVZ packed length')
        word=struct.unpack_from('>I',data,cursor)[0];cursor+=4;size=word&0x7fffffff
        if not size or len(out)+size>expected:raise ValueError('RVZ packed output budget')
        stored=68 if word&0x80000000 else size
        if cursor+stored>len(data):raise ValueError('RVZ packed span')
        value=data[cursor:cursor+stored];cursor+=stored
        out.extend(_padding(value,size,disc_offset+len(out))if word&0x80000000 else value)
    if len(out)!=expected:raise ValueError('RVZ unpacked size')
    return bytes(out)

class RVZReader:
    def __init__(self,path):
        self.file=FileReader(path);header=self.file.read(0,0x48)
        if header[:4]!=b'RVZ\1' or hashlib.sha1(header[:52]).digest()!=header[52:72]:raise ValueError('RVZ header/hash')
        version,compatible,ds=struct.unpack_from('>III',header,4)
        if compatible>0x1000000 or ds!=0xdc:raise ValueError('unsupported RVZ header')
        self.size,stored=struct.unpack_from('>QQ',header,36)
        if stored!=self.file.size or not 0<self.size<=2*1024*1024*1024:raise ValueError('RVZ file/logical size')
        d=self.file.read(0x48,ds)
        if hashlib.sha1(d).digest()!=header[16:36]:raise ValueError('RVZ disc header hash')
        kind,compression,level,self.chunk=struct.unpack_from('>4I',d)
        if kind!=1 or compression!=5 or not 32768<=self.chunk<=4*1024*1024 or self.chunk&(self.chunk-1):raise ValueError('RVZ supports GC Zstandard power-of-two chunks only')
        if struct.unpack_from('>I',d,0x90)[0]:raise ValueError('Wii partition unsupported')
        self.dhead=d[16:144]
        nr,ro,rs,ng,go,gs=struct.unpack_from('>IQIIQI',d,0xb4)
        if not 1<=nr<=128 or not 1<=ng<=100000:raise ValueError('RVZ table budget')
        raw=_zstd(self.file.read(ro,rs),nr*24);groups=_zstd(self.file.read(go,gs),ng*12)
        if len(raw)!=nr*24 or len(groups)!=ng*12:raise ValueError('RVZ table size')
        self.groups=[struct.unpack_from('>III',groups,i*12)for i in range(ng)];self.ranges=[]
        for i in range(nr):
            off,size,index,count=struct.unpack_from('>QQII',raw,i*24)
            end=off+size;off=off//32768*32768;size=end-off
            if end>self.size or index+count>ng or count!=(size+self.chunk-1)//self.chunk:raise ValueError('RVZ raw range')
            self.ranges.append((off,size,index,count))
        ordered=sorted(self.ranges)
        if any(a[0]+a[1]>b[0]for a,b in zip(ordered,ordered[1:])):raise ValueError('overlapping RVZ raw ranges')
    @lru_cache(maxsize=4)
    def block(self,index,expected,disc_offset):
        offset,size,packed=self.groups[index];compressed=bool(size&0x80000000);size&=0x7fffffff
        if not size:return bytes(expected)
        if size>8*1024*1024 or packed>8*1024*1024:raise ValueError('RVZ block budget')
        data=self.file.read(offset*4,size)
        if compressed:data=_zstd(data,packed or expected)
        if packed:
            if len(data)!=packed:raise ValueError('RVZ packed size')
            data=unpack_rvz(data,expected,disc_offset)
        if len(data)!=expected:raise ValueError('RVZ block size')
        return data
    def read(self,offset,size):
        span(offset,size,self.size);out=bytearray()
        while len(out)<size:
            pos=offset+len(out);found=next((r for r in self.ranges if r[0]<=pos<r[0]+r[1]),None)
            if found is None:raise ValueError('RVZ unmapped read')
            start,length,index,count=found;relative=pos-start;n=relative//self.chunk
            expected=min(self.chunk,length-n*self.chunk);data=self.block(index+n,expected,start+n*self.chunk)
            within=relative%self.chunk;take=min(size-len(out),len(data)-within);out.extend(data[within:within+take])
        if offset<128:
            take=min(size,128-offset);out[:take]=self.dhead[offset:offset+take]
        return bytes(out)

def gamecube_fst(reader):
    header=reader.read(0,0x440)
    if header[0x1c:0x20]!=bytes.fromhex('c2339f3d'):raise ValueError('GameCube magic')
    dol,fst,size=struct.unpack_from('>III',header,0x420)
    if size>8*1024*1024:raise ValueError('FST budget')
    data=reader.read(fst,size);kind,_,count=struct.unpack_from('>III',data)
    if kind>>24!=1 or not 1<=count<=MAX_ENTRIES or count*12>size:raise ValueError('FST root')
    stack=[('',count)];rows=[];names=set()
    for i in range(1,count):
        while i>=stack[-1][1]:stack.pop()
        word,offset,length=struct.unpack_from('>III',data,i*12);at=count*12+(word&0xffffff);end=data.find(b'\0',at)
        if not count*12<=at<end<size:raise ValueError('FST string')
        name=data[at:end].decode('ascii')
        if name in('.','..')or any(c in name for c in '/\\:\0'):raise ValueError('unsafe FST name')
        path=stack[-1][0]+name
        if path.casefold()in names:raise ValueError('duplicate FST name')
        names.add(path.casefold())
        if word>>24:
            if word>>24!=1 or not i<length<=stack[-1][1]or len(stack)>32:raise ValueError('FST directory')
            stack.append((path+'/',length))
        else:span(offset,length,reader.size);rows.append({'path':path,'offset':offset,'bytes':length})
    return {'disc_id':header[:6].decode('ascii'),'revision':header[7],'dol_offset':dol,'fst_offset':fst,'files':rows}
