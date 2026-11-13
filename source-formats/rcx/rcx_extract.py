"""Read RCX v4 index and boundedly decode the native LZ stream; research only."""
import argparse, hashlib, json, struct
from pathlib import Path

def unpack(src, expected):
    out=bytearray(); p=0
    def literal(n):
        nonlocal p
        if p+n>len(src) or len(out)+n>expected: raise ValueError('literal outside bounds')
        out.extend(src[p:p+n]); p+=n
    def back(dist,n):
        if dist>len(out) or len(out)+n>expected: raise ValueError('backreference outside bounds')
        for _ in range(n): out.append(out[-dist])
    while True:
        if p>=len(src): raise ValueError('missing terminator')
        c=src[p]; p+=1
        if c<0x80:
            if p>=len(src): raise ValueError('short command')
            b=src[p];p+=1;literal(c&3);back(((c>>5)<<8)+b+1,((c>>2)&7)+3)
        elif c<0xc0:
            if p+2>len(src): raise ValueError('short command')
            a,b=src[p:p+2];p+=2;literal(a>>6);back(((a&63)<<8)+b+1,(c&63)+4)
        elif c<0xe0:
            if p+3>len(src): raise ValueError('short command')
            a,b,d=src[p:p+3];p+=3;literal(c&3);back(((c&16)<<12)+(a<<8)+b+1,((c&12)<<6)+d+5)
        elif c<0xfc: literal(((c&31)+1)*4)
        else:
            literal(c&3)
            if len(out)!=expected: raise ValueError(f'decoded {len(out)} expected {expected}')
            if p!=len(src): raise ValueError(f'trailing {len(src)-p} bytes')
            return bytes(out)

def read(path):
    b=path.read_bytes()
    if len(b)<0x110 or len(b)>256*1024*1024 or b[:8]!=bytes.fromhex('c65e0bb004000000'): raise ValueError('unknown header')
    count=struct.unpack_from('<I',b,8)[0]
    table_end=0x110+(count-1)*0x128+36
    if not 2<=count<=10000 or table_end>len(b): raise ValueError('invalid table')
    rows=[];seen=set()
    for i in range(1,count):
        h=0x110+i*0x128; name=b[h-0x104:h-4].split(b'\0',1)[0].decode('ascii')
        typ,expanded,stored,off,idx,*rest=struct.unpack_from('<9I',b,h)
        if idx!=i or typ not in (5,6) or off+stored>len(b) or expanded>64*1024*1024 or (typ==6 and off<table_end): raise ValueError(f'bad entry {i}')
        if typ==6:
            if not name or any(c in name for c in '/\\:') or name in ('.','..') or name.rstrip(' .')!=name or name.lower() in seen:raise ValueError(f'unsafe or duplicate name {i}')
            seen.add(name.lower())
        rows.append(dict(index=i,name=name,type=typ,expanded=expanded,stored=stored,offset=off,unknown=rest))
    return b,rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    root=Path(__file__).resolve().parent; output=a.output.resolve()
    if output==root or not output.is_relative_to(root): raise ValueError('output must be a new subdirectory of exclusive_research')
    if output.exists(): raise ValueError('fresh output directory required')
    b,rows=read(a.source);output.mkdir(parents=True)
    a.output=output
    for r in rows:
        if r['type']!=6: continue
        raw=b[r['offset']:r['offset']+r['stored']]
        data=unpack(raw,r['expanded']) if r['expanded'] else raw
        r['decoded_sha256']=hashlib.sha256(data).hexdigest(); r['decoded_size']=len(data)
        name=r['name']
        if Path(name).name!=name or name in ('.','..'): raise ValueError('unsafe name')
        target=a.output/name
        if target.exists(): raise ValueError(f'duplicate {name}')
        target.write_bytes(data)
    (a.output/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
    print(f'{a.source.name}: {len(rows)} entries, {sum(r["type"]==6 for r in rows)} decoded')
if __name__=='__main__':main()
