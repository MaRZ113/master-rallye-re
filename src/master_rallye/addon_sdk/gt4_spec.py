"""Bounded read-only GT4 GTDB row recovery for source rig provenance.

Little-endian GT4 DBT rows, prefix Huffman and template-byte differences.
No SQLite export or column-name interpretation is required to recover bytes.
"""
from __future__ import annotations
import hashlib,struct
from .gt4_source import Reader

class DatabaseTable:
    def __init__(self,data):
        self.data=data;self.r=Reader(data);r=self.r
        if not 16<=len(data)<=64*1024*1024 or data[:4]!=b'GTDB':raise ValueError('invalid GTDB')
        self.flags,alignment,self.count,self.row_size=r.get('HHII',4)
        if self.flags&~1 or not 0<self.count<=1000000 or not 0<self.row_size<=4096:raise ValueError('unsupported GTDB layout/budget')
        self.rows=dict(r.get('II',16+i*8) for i in range(self.count))
        if len(self.rows)!=self.count:raise ValueError('duplicate GTDB row IDs')
        self.code_at=16+self.count*8;self.data_at=self.code_at
        if self.flags&1:
            relative,ncodes=r.get('II',self.code_at)
            if not 0<ncodes<=512:raise ValueError('Huffman code count budget')
            self.prefix=[r.get('BB',self.code_at+8+i*2) for i in range(256)]
            self.codes={}
            for i in range(ncodes):
                length,symbol,unused,code=r.get('BBHI',self.code_at+0x208+i*8)
                if not 1<=length<=31 or code>=(1<<length) or (length,code) in self.codes:raise ValueError('invalid Huffman dictionary')
                self.codes[length,code]=symbol
            template_at=self.code_at+relative;relative,self.template_count=r.get('II',template_at)
            if not 0<self.template_count<=64:raise ValueError('template count budget')
            self.templates=template_at+8;self.data_at=template_at+relative
            r.get(f'{self.template_count*self.row_size}s',self.templates)
        if not 0<=self.data_at<=len(data):raise ValueError('GTDB data origin out of bounds')

    def row(self,row_id):
        if row_id not in self.rows:raise ValueError(f'GTDB row ID absent: {row_id}')
        at=self.data_at+self.rows[row_id];r=self.r
        if not self.flags&1:return r.get(f'{self.row_size}s',at)[0]
        count=r.get('B',at)[0]
        if not 1<=count<=1+self.row_size+(self.row_size+7)//8:raise ValueError('row decode budget')
        decoded=bytearray();bit=0
        for _ in range(count):
            pos=at+1+bit//8;available=self.data[pos:pos+5];word=int.from_bytes(available,'little')>>(bit%8)
            symbol,length=self.prefix[word&255]
            if not length:
                found=[(self.codes[length,word&((1<<length)-1)],length) for length in range(9,32) if (length,word&((1<<length)-1)) in self.codes]
                if len(found)!=1:raise ValueError('unresolved Huffman code')
                symbol,length=found[0]
            if bit+length>max(0,len(self.data)-at-1)*8:raise ValueError('truncated Huffman row')
            decoded.append(symbol);bit+=length
        kind,index=decoded[0]>>6,decoded[0]&63
        if kind in (0,2):
            if index>=self.template_count:raise ValueError('template index outside source table')
            out=bytearray(r.get(f'{self.row_size}s',self.templates+index*self.row_size)[0])
        if kind==0:
            if count!=1:raise ValueError('unexpected template-only bytes')
        elif kind==1:
            if count!=self.row_size+1:raise ValueError('incomplete raw row')
            out=decoded[1:]
        elif kind==2:
            mask_size=(self.row_size+7)//8;cursor=1+mask_size
            if cursor>count:raise ValueError('truncated row mask')
            for i in range(self.row_size):
                if decoded[1+i//8]>>(i%8)&1:
                    if cursor>=count:raise ValueError('truncated row replacement')
                    out[i]=decoded[cursor];cursor+=1
            if cursor!=count:raise ValueError('unexplained row tail')
        else:raise ValueError('unsupported row compression type')
        return bytes(out)

    def evidence(self,row_id):
        raw=self.row(row_id)
        return {'table_sha256':hashlib.sha256(self.data).hexdigest(),'row_id':row_id,'row_size':self.row_size,
                'row_sha256':hashlib.sha256(raw).hexdigest(),'raw_hex':raw.hex()}


def label_id(data,label):
    r=Reader(data)
    if data[:4]!=b'GTID':raise ValueError('expected GTID')
    count=r.get('I',4)[0]
    if count>1000000 or len(data)>64*1024*1024:raise ValueError('GTID budget')
    base=16+count*8;matches=[]
    for i in range(count):
        relative,row=r.get('II',16+i*8);at=base+relative;n=r.get('H',at)[0]
        if not 1<=n<=4096:raise ValueError('GTID label length')
        raw=r.get(f'{n}s',at+2)[0]
        if raw[-1]!=0:raise ValueError('unterminated GTID label')
        if raw[:-1].decode('ascii')==label:matches.append(row)
    if len(matches)!=1:raise ValueError(f'GTID label not unique/present: {label}')
    return matches[0]
