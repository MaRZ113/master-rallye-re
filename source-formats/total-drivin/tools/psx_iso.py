"""Extract ISO9660 files from a MODE2/2352 PS1 track (Form1 user data at +24)."""
import struct,sys,os
src,out=sys.argv[1],sys.argv[2]
f=open(src,'rb')
def sec(n):
    f.seek(n*2352+24);return f.read(2048)
def read(lba,size):
    b=bytearray()
    for k in range((size+2047)//2048): b+=sec(lba+k)
    return bytes(b[:size])
pvd=sec(16);root=pvd[156:190];rl=struct.unpack_from('<I',root,2)[0];rs=struct.unpack_from('<I',root,10)[0]
def walk(lba,size,path):
    d=read(lba,size);o=0
    while o<len(d):
        l=d[o]
        if l==0:o=(o//2048+1)*2048;continue
        el=struct.unpack_from('<I',d,o+2)[0];es=struct.unpack_from('<I',d,o+10)[0];fl=d[o+25];nl=d[o+32];nm=d[o+33:o+33+nl].decode('latin1').split(';')[0]
        if nm not in('\x00','\x01'):
            p=os.path.join(path,nm)
            if fl&2: os.makedirs(p,exist_ok=True);walk(el,es,p)
            else: open(p,'wb').write(read(el,es));print(p[len(out)+1:],el,es)
        o+=l
os.makedirs(out,exist_ok=True);walk(rl,rs,out)
