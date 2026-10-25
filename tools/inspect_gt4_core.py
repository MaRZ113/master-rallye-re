"""Private GT4 CORE reconstruction for static analysis, never distribution.

Container/key recipe follows the user-local PDTools GT4ElfBuilderTool loader.
Crypto.Cipher.Salsa20 is an optional research dependency, not an SDK runtime
dependency. Original bytes remain immutable; output requires a new directory.
"""
import argparse,hashlib,json,struct,zlib
from pathlib import Path


def reconstruct(path,output):
    if output.exists():raise ValueError('output exists')
    data=path.read_bytes()
    if not 6<=len(data)<=64*1024*1024:raise ValueError('CORE input size budget')
    encrypted=data[0]!=1 and data[1]!=1
    crc=None
    if encrypted:
        table=[]
        for byte in range(256):
            word=byte<<24
            for _ in range(8):word=((word<<1)^ (0x1edc6f41 if word&0x80000000 else 0))&0xffffffff
            table.append(word)
        crc=0xffffffff
        for byte in data[:-4]:crc=((crc<<8)^table[(crc>>24)^byte])&0xffffffff
        crc=(~crc)&0xffffffff
        if crc!=struct.unpack_from('<I',data,len(data)-4)[0]:raise ValueError('encrypted CORE CRC mismatch')
        from Crypto.Cipher import Salsa20
        body=Salsa20.new(key=b'PolyphonyDigital',nonce=data[:8]).decrypt(data[8:-4])
    else:body=data
    flags,size=struct.unpack_from('<HI',body)
    if size>64*1024*1024:raise ValueError('CORE size budget exceeded')
    # Do not flush after the bounded call: malformed compressed data could
    # otherwise expand its unconsumed tail beyond the advertised size budget.
    inflater=zlib.decompressobj(-15);raw=inflater.decompress(body[6:],size+1)
    if len(raw)!=size or not inflater.eof:raise ValueError('CORE decompression size/end mismatch')
    pos=0
    def read(fmt):
        nonlocal pos
        result=struct.unpack_from('<'+fmt,raw,pos);pos+=struct.calcsize('<'+fmt);return result
    size1,=read('H');modulus=raw[pos:pos+size1];pos+=size1
    size2,=read('H');signature=raw[pos:pos+size2];pos+=size2
    hash_start=pos;count,entry=read('II');segments=[]
    if not 1<=count<=32:raise ValueError('invalid CORE segment count')
    for i in range(count):
        address,length=read('II')
        if pos+length>len(raw) or address+length>0x2000000:raise ValueError('CORE segment bounds')
        content=raw[pos:pos+length];pos+=length
        segments.append((address,content))
    if pos!=len(raw):raise ValueError('unparsed CORE body tail')
    digest=hashlib.sha512(raw[hash_start:]).digest();auth=[]
    # PDTools records 81001 as GT4 Online US. Verify ordinary RSA both byte
    # orders and retain the observation; decryption alone is not authentication.
    for endian in ['big','little']:
        n=int.from_bytes(modulus,endian);s=int.from_bytes(signature,endian)
        for exponent in [81001,82101,82201,83201]:
            result=pow(s,exponent,n).to_bytes(len(modulus),'big')
            if digest in result or digest[::-1] in result:auth.append({'exponent':exponent,'byte_order':endian})
    headers=52+32*count;start=(headers+4095)&~4095
    elf=bytearray(start);elf[:52]=struct.pack('<16sHHIIIIIHHHHHH',b'\x7fELF\x01\x01\x01'+bytes(9),2,8,1,entry,52,0,0x20924001,52,32,count,0,0,0)
    for i,(address,content) in enumerate(segments):
        offset=len(elf);elf.extend(content)
        struct.pack_into('<8I',elf,52+32*i,0x70000006 if len(content)==24 else 1,offset,address,address,len(content),len(content),4 if len(content)==24 else 7,1)
    output.mkdir(parents=True);(output/'core.elf').write_bytes(elf)
    report={'source_sha256':hashlib.sha256(data).hexdigest(),'encrypted_crc':crc,'load_source_flags':flags,'inflated_bytes':size,'entry':hex(entry),'elf_sha256':hashlib.sha256(elf).hexdigest(),'authentication':auth,
            'segments':[{'address':hex(a),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for a,b in segments],
            'layout':'minimal ELF program headers preserve original segment addresses/data; no heuristic source symbols or section split',
            'source_unchanged':path.read_bytes()==data}
    (output/'core-report.json').write_text(json.dumps(report,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(reconstruct(a.source,a.output),indent=2))
