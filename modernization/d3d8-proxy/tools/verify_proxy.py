"""Standard-library PE32/DLL/export/import verifier. This is not runtime proof."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

REQUIRED = {'Direct3DCreate8':5, 'ValidateVertexShader':3, 'ValidatePixelShader':2}

class PE:
    def __init__(self, data):
        self.data = data
        if self.take(0,2) != b'MZ':raise ValueError('Missing DOS signature')
        pe = self.u32(0x3c)
        if self.take(pe,4) != b'PE\0\0':raise ValueError('Missing PE signature')
        self.machine, count = self.unpack('<HH',pe+4)
        self.timestamp = self.u32(pe+8)
        opt_size, self.flags = self.unpack('<HH',pe+20)
        opt = pe+24
        if opt_size<224 or self.u16(opt)!=0x10b:raise ValueError('Expected PE32 optional header')
        self.image_base=self.u32(opt+28);self.entry=self.u32(opt+16)
        self.headers=self.u32(opt+60)
        if self.u32(opt+92)<14:raise ValueError('Missing standard PE directories')
        self.directories=[self.unpack('<II',opt+96+8*i) for i in range(min(16,self.u32(opt+92)))]
        self.sections=[]
        if not 1<=count<=96:raise ValueError('Invalid section count')
        for i in range(count):
            at=opt+opt_size+40*i
            name=self.take(at,8).split(b'\0')[0].decode('ascii')
            size, va, raw_size, raw=self.unpack('<IIII',at+8)
            if raw_size:self.take(raw,raw_size)
            self.sections.append(dict(name=name,rva=va,virtual_size=size,raw_size=raw_size,raw_offset=raw))
    def take(self, at, n):
        if at<0 or n<0 or at+n>len(self.data):raise ValueError('PE range outside file')
        return self.data[at:at+n]
    def unpack(self, fmt, at):return struct.unpack(fmt,self.take(at,struct.calcsize(fmt)))
    def u16(self, at):return self.unpack('<H',at)[0]
    def u32(self, at):return self.unpack('<I',at)[0]
    def offset(self, rva, n=1):
        if rva<self.headers:
            if rva+n>self.headers:raise ValueError('Header RVA crosses mapping')
            self.take(rva,n);return rva
        for s in self.sections:
            d=rva-s['rva']
            if 0<=d and d+n<=s['raw_size']:
                at=s['raw_offset']+d;self.take(at,n);return at
        raise ValueError('RVA not backed by file')
    def string(self, rva):
        chars=[]
        for i in range(4096):
            b=self.take(self.offset(rva+i),1)
            if b==b'\0':return b''.join(chars).decode('ascii')
            chars.append(b)
        raise ValueError('Unterminated PE string')
    def exports(self):
        rva,size=self.directories[0]
        if not rva:return {}
        at=self.offset(rva,40);base=self.u32(at+16);functions=self.u32(at+20);names=self.u32(at+24)
        if functions>65536 or names>65536:raise ValueError('Unreasonable export count')
        funcs=self.offset(self.u32(at+28),4*functions)
        name_table=self.offset(self.u32(at+32),4*names)
        ords=self.offset(self.u32(at+36),2*names);result={}
        for i in range(names):
            index=self.u16(ords+i*2)
            if index>=functions:raise ValueError('Invalid export ordinal index')
            name=self.string(self.u32(name_table+4*i));target=self.u32(funcs+4*index)
            if not target:raise ValueError('Export has no address')
            if name in result:raise ValueError('Duplicate export name')
            forwarded=rva<=target<rva+size
            if not forwarded:self.offset(target)
            result[name]={'ordinal':base+index,'rva':target,'forwarder':self.string(target) if forwarded else None}
        return result
    def imports(self):
        rva,size=self.directories[1]
        if not rva:return []
        result=[]
        for i in range(min(4096,size//20)):
            row=self.unpack('<IIIII',self.offset(rva+20*i,20))
            if not any(row):return result
            result.append(self.string(row[3]))
        raise ValueError('Unterminated import table')

def verify(data):
    pe=PE(data);exports=pe.exports();imports=pe.imports();errors=[]
    if pe.machine!=0x14c:errors.append('Machine must be I386')
    if not pe.flags&0x2000:errors.append('DLL characteristic missing')
    if 'd3d8.dll' in (x.casefold() for x in imports):errors.append('Recursive d3d8 import')
    if pe.directories[13][0]:errors.append('Delay imports require manual audit; none expected')
    for name,ordinal in REQUIRED.items():
        if name not in exports:errors.append('Missing export '+name)
        elif exports[name]['ordinal']!=ordinal or exports[name]['forwarder']:errors.append('Incorrect direct export '+name)
    return {'valid':not errors,'errors':errors,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),
            'machine':pe.machine,'pe_type':'PE32','dll':bool(pe.flags&0x2000),'image_base':pe.image_base,
            'timestamp':pe.timestamp,'entry_rva':pe.entry,'exports':exports,'imported_dlls':imports,'sections':pe.sections,
            'evidence_grade':'BUILD_VERIFIED_NOT_RUNTIME'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('dll',type=Path);a=ap.parse_args()
    try:result=verify(a.dll.read_bytes())
    except (ValueError,UnicodeError,struct.error) as e:result={'valid':False,'errors':[str(e)]}
    print(json.dumps(result,indent=2));return 0 if result['valid'] else 1

if __name__=='__main__':raise SystemExit(main())
