"""Total Drivin' / Grand Tour Racing '98 (PS1, Eutechnyx) .COM / LEVELS.DAT decompressor.

Reimplements SLES_003.07 func 0x800168D0 (mode 1). Stream header: u32 packed size,
u32 unpacked size, i32 literal bits (8); then an LSB-first bit stream read as LE words.
Symbols: flag bit 1 -> dictionary code (code_bits wide, value + 256), flag 0 -> literal
(literal_bits wide). 256 = reset, 257 = end, dictionary starts at 0x102, max 0x1000,
code width grows when next_code - 257 == mask (classic LZW, KwKwK handled)."""
import struct,sys
class Bits:
    def __init__(s,b,o):s.b=b;s.o=o*8
    def peek(s,n):
        v=int.from_bytes(s.b[s.o//8:s.o//8+8].ljust(8,b'\0'),'little')>>(s.o%8)
        return v&((1<<n)-1)
    def skip(s,n):s.o+=n
def decode(buf,off=0):
    plen,ulen,lbits=struct.unpack_from('<IIi',buf,off)
    bs=Bits(buf,off+12);out=bytearray()
    lit_mask=(1<<lbits)-1 if lbits>=0 else 0
    def widths(base):
        t4=0x102;t3=0;t6=1
        while t4-base-t6>=0:t6<<=1;t3+=1
        return t3,t6-1
    base=1<<lbits if lbits>=0 else 0   # lbits < 0: plain LZW, no literal flag
    def sym(cb,cm):
        b=bs.peek(32)
        if lbits<0: bs.skip(cb);return b&cm
        if b&1: bs.skip(cb+1);return ((b>>1)&cm)+base
        bs.skip(lbits+1);return (b>>1)&lit_mask
    D={}
    cb,cm=widths(base);nxt=0x102
    v=sym(cb,cm);out.append(v);prev=first=v
    while True:
        v=sym(cb,cm)
        if v==0x100:
            nxt=0x102;cb,cm=widths(base);D={}
            v=sym(cb,cm);out.append(v);prev=first=v;continue
        if v==0x101 or len(out)>=ulen:break
        cur=v;stack=[]
        if v>=nxt: stack.append(first);v=prev
        while v>=0x100:
            e=D[v];stack.append(e&0xff);v=e>>16
        first=v;out.append(v);out.extend(reversed(stack))
        if nxt<0x1000:
            D[nxt]=(prev<<16)|first;nxt+=1
            if nxt<0x1000 and nxt-(base-1)-2==cm: cb+=1;cm=cm*2+1
        prev=cur
    return bytes(out),ulen,plen
def chunks(buf):
    """Split a .COM file: chunks of (u32 packed, u32 unpacked, i32 literal bits, data),
    next chunk at offset + 4 + packed, zero words skipped."""
    o=0;out=[]
    while o+12<=len(buf):
        p=struct.unpack_from('<I',buf,o)[0]
        if p==0:o+=4;continue
        d,u,_=decode(buf,o);out.append((o,d));o+=4+p
    return out
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read();o=int(sys.argv[3],0) if len(sys.argv)>3 else 0
    d,u,p=decode(b,o);print(len(d),u,p);open(sys.argv[2],'wb').write(d)
