import zlib, struct
def load(path):
    d=open(path,'rb').read(); assert d[:8]==b'\x89PNG\r\n\x1a\n'
    pos=8; idat=b''; 
    while pos<len(d):
        n,t=struct.unpack('>I4s',d[pos:pos+8]); c=d[pos+8:pos+8+n]; pos+=12+n
        if t==b'IHDR': w,h,bd,ct=struct.unpack('>IIBB',c[:10])
        elif t==b'IDAT': idat+=c
    bpp={2:3,6:4}[ct]; raw=zlib.decompress(idat); stride=w*bpp; rows=[]; prev=bytearray(stride); p=0
    for y in range(h):
        f=raw[p]; line=bytearray(raw[p+1:p+1+stride]); p+=1+stride
        for i in range(stride):
            a=line[i-bpp] if i>=bpp else 0; b=prev[i]; c=prev[i-bpp] if i>=bpp else 0
            if f==1: line[i]=(line[i]+a)&255
            elif f==2: line[i]=(line[i]+b)&255
            elif f==3: line[i]=(line[i]+(a+b)//2)&255
            elif f==4:
                pa=abs(b-c); pb=abs(a-c); pc=abs(a+b-2*c)
                pr=a if pa<=pb and pa<=pc else (b if pb<=pc else c); line[i]=(line[i]+pr)&255
        rows.append(line); prev=line
    return w,h,lambda x,y:tuple(rows[y][x*bpp:x*bpp+3])
