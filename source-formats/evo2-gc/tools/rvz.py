"""Minimal RVZ (Dolphin WIA/RVZ) reader for GameCube discs + GC FST extraction.
Junk (RVZ 'packed' LFG data) is returned as zeros: file data is exact, padding is not.
Requires Python 3.14+ (compression.zstd). usage: rvz.py <in.rvz> <outdir> [--list]"""
import struct,sys,os
from compression import zstd
class RVZ:
    def __init__(s,path):
        s.f=open(path,'rb');h1=s.f.read(0x48)
        assert h1[:4]==b'RVZ\x01',h1[:4]
        s.h2size=struct.unpack_from('>I',h1,0xC)[0];s.iso_size=struct.unpack_from('>Q',h1,0x24)[0]
        h2=s.f.read(s.h2size)
        s.disc_type,s.comp,s.level,s.chunk=struct.unpack_from('>IIiI',h2,0)
        s.disc_header=h2[0x10:0x90]
        o=0x90;npart,psz=struct.unpack_from('>II',h2,o);o+=8;poff=struct.unpack_from('>Q',h2,o)[0];o+=8+20
        nraw=struct.unpack_from('>I',h2,o)[0];rawoff=struct.unpack_from('>Q',h2,o+4)[0];rawsz=struct.unpack_from('>I',h2,o+12)[0];o+=16
        ngrp=struct.unpack_from('>I',h2,o)[0];grpoff=struct.unpack_from('>Q',h2,o+4)[0];grpsz=struct.unpack_from('>I',h2,o+12)[0]
        assert s.disc_type==1 and s.comp==5,(s.disc_type,s.comp)
        raw=s._z(rawoff,rawsz,nraw*24);grp=s._z(grpoff,grpsz,ngrp*12)
        s.raws=[struct.unpack_from('>QQII',raw,24*i) for i in range(nraw)]
        s.groups=[struct.unpack_from('>III',grp,12*i) for i in range(ngrp)]
        s.cache={}
    def _z(s,off,size,expect):
        s.f.seek(off);b=s.f.read(size);d=zstd.decompress(b) if size!=expect else b
        return d
    def _group(s,gi,length):
        if gi in s.cache:return s.cache[gi]
        off4,size,packed=s.groups[gi];comp=size>>31;size&=0x7fffffff
        if size==0:d=bytes(length)
        else:
            s.f.seek(off4<<2);d=s.f.read(size)
            if comp:d=zstd.decompress(d)
            if packed:
                out=bytearray();o=0
                while o<len(d) and len(out)<length:
                    n=struct.unpack_from('>I',d,o)[0];o+=4
                    if n&0x80000000:n&=0x7fffffff;o+=68;out+=bytes(n)
                    else:out+=d[o:o+n];o+=n
                d=bytes(out)
        d=d[:length].ljust(length,b'\0')
        if len(s.cache)>64:s.cache.clear()
        s.cache[gi]=d;return d
    def read(s,off,n):
        out=bytearray()
        while n>0:
            if off<0x80:
                k=min(n,0x80-off);out+=s.disc_header[off:off+k];off+=k;n-=k;continue
            for doff,dsz,gidx,ng in s.raws:
                skip=doff%0x8000;start=doff-skip;end=doff+dsz
                if start<=off<end:
                    rel=off-start;gi=rel//s.chunk;go=rel%s.chunk
                    glen=min(s.chunk,end-start-gi*s.chunk)
                    g=s._group(gidx+gi,glen);k=min(n,glen-go);out+=g[go:go+k];off+=k;n-=k;break
            else:
                k=min(n,0x8000-(off%0x8000));out+=bytes(k);off+=k;n-=k
        return bytes(out)
def fst(r):
    h=r.read(0,0x440);fo,fs=struct.unpack_from('>II',h,0x424);F=r.read(fo,fs)
    n=struct.unpack_from('>I',F,8)[0];names=F[n*12:]
    def name(o):return names[o:names.index(b'\0',o)].decode('latin1')
    out=[];stack=[(n,'')]
    for i in range(1,n):
        while stack and i>=stack[-1][0]:stack.pop()
        t,a,b=struct.unpack_from('>III',F,i*12);isdir=t>>24;nm=name(t&0xffffff)
        path=(stack[-1][1] if stack else '')+nm
        if isdir:stack.append((b,path+'/'))
        else:out.append((path,a,b))
    return out
if __name__=='__main__':
    r=RVZ(sys.argv[1]);files=fst(r)
    print(r.disc_header[:6],r.disc_header[0x20:0x60].split(b'\0')[0],len(files),'files')
    if '--list' in sys.argv:
        for p,a,b in files:print(p,a,b)
    else:
        for p,a,b in files:
            q=os.path.join(sys.argv[2],p);os.makedirs(os.path.dirname(q) or '.',exist_ok=True);open(q,'wb').write(r.read(a,b))
