"""Dakar2 bounded RBB/SBB and qualified Xbox XMD/HIR/XTX structural reader.

Original x86 loader evidence: 82020 XOR,821e0/82040 relocations,8b4b0 XMD,
8ac20 XTX. Offsets are original file offsets, never mutated loaded pointers.
"""
import hashlib
import math
import struct
from .dakar2_disc import MAX_READ,span

def digest(data):return hashlib.sha256(data).hexdigest()

class RBB:
    def __init__(self,data,endian='<'):
        if endian not in('<','>'):raise ValueError('RBB endian')
        self.data=data;self.endian=endian
        if not 0x48<=len(data)<=MAX_READ or data[:4]!=b'\0RBB':raise ValueError('RBB signature/budget')
        if self.u(4)not in(len(data),len(data)+8)or self.u(8)!=(self.u(0)^self.u(4)):raise ValueError('RBB declared size/header XOR')
        if self.u(0x18)!=1:raise ValueError('RBB multiblock UNSUPPORTED')
        count=self.u(0x1c)
        if not 1<=count<=8192 or self.u(0x20)!=count:raise ValueError('RBB resource count')
        flags,off,size,rel,nres,external,other,internal,checksum=struct.unpack_from(endian+'9I',data,0x24)
        if nres!=count or off<0x48+count*12:raise ValueError('RBB descriptor/directory')
        self.slice(off,size)
        if self.xor(16,off-16)!=self.u(12)or self.xor(off,size)!=checksum:raise ValueError('RBB content XOR')
        if external+other+internal>1000000 or (external+other+internal)*4>rel or rel>size:raise ValueError('RBB relocation budget')
        self.external=set();self.relative=set();self.payload_start=off+rel;self.payload_end=off+size
        for i in range(external):self.external.add(self.payload_start+self.u(off+i*4))
        for i in range(internal):self.relative.add(self.payload_start+self.u(off+(external+other+i)*4))
        if len(self.relative)!=internal or len(self.external)!=external or self.relative&self.external:raise ValueError('duplicate RBB relocation')
        for field in self.relative|self.external:self.slice(field,4)
        self.resources=[]
        for i in range(count):
            at=0x48+i*12;tag=self.slice(at,4).rstrip(b'\0').decode('ascii');encoded=self.u(at+8)
            if not tag.isalnum():raise ValueError('RBB resource tag')
            target=encoded&~3
            if encoded&3!=1:raise ValueError('RBB original resource reference state')
            self.slice(target,4)
            if target<self.payload_start:raise ValueError('RBB resource points into metadata')
            self.resources.append({'id':i,'type':tag,'offset':target,'encoded_reference':encoded})
        self.warnings=['RBB declared size exceeds stored member by8']if self.u(4)!=len(data)else[]
    def slice(self,p,n):span(p,n,len(self.data));return self.data[p:p+n]
    def u(self,p):return struct.unpack(self.endian+'I',self.slice(p,4))[0]
    def floats(self,p,n):
        values=list(struct.unpack(self.endian+str(n)+'f',self.slice(p,n*4)))
        if any(not math.isfinite(v)or abs(v)>1e8 for v in values):raise ValueError('invalid source floats')
        return values
    def pointer(self,p):
        if p not in self.relative:raise ValueError('unqualified self-relative pointer field')
        target=p+struct.unpack(self.endian+'i',self.slice(p,4))[0]
        if not self.payload_start<=target<self.payload_end:raise ValueError('self-relative target outside source payload')
        self.slice(target,1);return target
    def reference(self,p):
        if p not in self.external:raise ValueError('unqualified resource-reference field')
        index=self.u(p)
        if index>=len(self.resources):raise ValueError('resource index')
        return self.resources[index]
    def xor(self,p,n):
        if n%4:raise ValueError('unaligned RBB XOR')
        value=0
        for (word,)in struct.iter_unpack(self.endian+'I',self.slice(p,n)):value^=word
        return value

def sbb_entries(data,endian='<'):
    if len(data)<16 or len(data)>MAX_READ:raise ValueError('SBB input budget')
    count=struct.unpack_from(endian+'I',data)[0]
    if not 1<=count<=8192 or 16+count*52>len(data):raise ValueError('SBB directory count')
    rows=[];names=set();previous=16+count*52
    for i in range(count):
        at=16+i*52;name=data[at:at+32].split(b'\0')[0].decode('ascii')
        if not name or name.casefold()in names or any(c in name for c in '/\\:\0')or name in('.','..'):raise ValueError('SBB unsafe/duplicate name')
        offset,allocated,key,declared=struct.unpack_from(endian+'4I',data,at+32)
        span(offset,allocated,len(data))
        if offset<previous or not allocated or declared>allocated+2048:raise ValueError('SBB overlap/size')
        previous=offset+allocated;names.add(name.casefold())
        stored=min(allocated,declared)
        rows.append({'id':i,'name':name,'offset':offset,'allocated_bytes':allocated,'declared_bytes':declared,
            'stored_bytes':stored,'key':key,'sha256':digest(data[offset:offset+stored]),
            'warnings':['declared size exceeds allocation by%d; no over-read'%(declared-allocated)]if declared>allocated else[]})
    return rows

def compact_transform(values):
    """Native46da0 copies basis9;88eb0 uploads it as D3D row vectors.

    UVS uses column vectors, hence transpose the basis, retain translation.
    Only rigid orthonormal bases are qualified; scale/shear stay unsupported.
    """
    if len(values)!=12 or any(not math.isfinite(v) for v in values):raise ValueError('HIR affine values')
    b=values[:9]
    for r in range(3):
        for c in range(3):
            if abs(sum(b[r*3+k]*b[c*3+k]for k in range(3))-(r==c))>1e-5:
                raise ValueError('HIR scale/shear basis UNSUPPORTED')
    return [b[0],b[3],b[6],values[9],b[1],b[4],b[7],values[10],b[2],b[5],b[8],values[11],0.,0.,0.,1.]


def hierarchy(rbb,index,*,qualified_rotations=False):
    row=rbb.resources[index]
    if row['type']!='HIR':raise ValueError('HIR resource required')
    root=row['offset'];count=rbb.u(root+4)
    if not 1<=count<=256:raise ValueError('HIR bone count')
    nodes=[]
    for i in range(count):
        at=root+0x20+i*0xd4;rbb.slice(at,0xd4);name_at=rbb.pointer(at+0x60)
        raw=rbb.slice(name_at,min(256,len(rbb.data)-name_at));end=raw.find(b'\0')
        if end<1:raise ValueError('HIR name termination')
        name=raw[:end].decode('ascii');matrix=rbb.floats(at+8,12)
        parent,sibling,child=struct.unpack('<iii',rbb.slice(at+0x38,12))
        if any(v< -1 or v>=count for v in(parent,sibling,child))or parent==i:raise ValueError('HIR linkage')
        # Source stores 3 basis vectors followed by translation. First qualified
        # vehicles use identity bases; any different basis needs a new review.
        if matrix[:9]!=[1.,0.,0.,0.,1.,0.,0.,0.,1.] and not qualified_rotations:raise ValueError('HIR rotated rest basis UNSUPPORTED')
        compact_transform(matrix)
        nodes.append({'id':i,'name':name,'offset':at,'parent':parent,'sibling':sibling,'first_child':child,
            'original_basis_translation':matrix,'raw_record_sha256':digest(rbb.slice(at,0xd4)),
            'flags':rbb.u(at+0x64),'translation':matrix[9:]})
    for node in nodes:
        seen=set();n=node['id']
        while n!=-1:
            if n in seen:raise ValueError('HIR parent cycle')
            seen.add(n);n=nodes[n]['parent']
    return nodes

def strip_triangles(indices,vertex_count):
    if not indices or len(indices)>3000000 or any(i>=vertex_count or i<0 for i in indices):raise ValueError('XMD index/budget')
    triangles=[]
    for i in range(2,len(indices)):
        a,b,c=indices[i-2:i+1]
        if len({a,b,c})==3:triangles.append([b,a,c]if i%2 else[a,b,c])
    return triangles

def packed_normal(value):
    result=[]
    for shift,bits in ((0,11),(11,11),(22,10)):
        v=(value>>shift)&((1<<bits)-1)
        if v&(1<<(bits-1)):v-=1<<bits
        result.append(max(-1.,v/((1<<(bits-1))-1)))
    return result

def xmd_meshes(rbb,index):
    row=rbb.resources[index];root=row['offset']
    if row['type']!='XMD'or rbb.endian!='<'or rbb.u(root)!=0x4001eb85:raise ValueError('Xbox XMD2.03 required')
    count=rbb.u(root+16)
    if not 1<=count<=128:raise ValueError('XMD submesh count')
    array=rbb.pointer(root+20);meshes=[];total_vertices=total_indices=0
    for i in range(count):
        at=rbb.pointer(array+i*4);nidx,nvert,primitive=struct.unpack('<III',rbb.slice(at,12))
        declaration=rbb.u(at+0x20)
        if not 1<=nvert<=65536 or primitive!=6 or declaration not in(0x51a08,0x51a13,8,0x13):raise ValueError('XMD vertex declaration/primitive UNSUPPORTED')
        total_vertices+=nvert;total_indices+=nidx
        if not 3<=nidx<=3000000 or total_indices>3000000 or total_vertices>1000000:raise ValueError('XMD aggregate allocation budget')
        streams={}
        for slot in range(16):
            field=at+0x28+slot*4
            if rbb.u(field):
                desc=rbb.pointer(field);stride=rbb.u(desc)
                if not 1<=stride<=64:raise ValueError('XMD stream stride')
                data_at=rbb.pointer(desc+4);raw=rbb.slice(data_at,nvert*stride)
                streams[slot]={'stride':stride,'offset':data_at,'raw':raw,'sha256':digest(raw)}
        expected={0:12,2:4,3:4,9:8}
        if declaration>0xffff:expected[10]=8
        if {k:v['stride']for k,v in streams.items()}!=expected:raise ValueError('XMD stream layout UNSUPPORTED')
        idx_at=rbb.pointer(at+0x24);raw_indices=rbb.slice(idx_at,nidx*2);indices=list(struct.unpack('<'+str(nidx)+'H',raw_indices))
        positions=[list(v)for v in struct.iter_unpack('<3f',streams[0]['raw'])];normals=[packed_normal(v[0])for v in struct.iter_unpack('<I',streams[2]['raw'])]
        uv=[list(v)for v in struct.iter_unpack('<2f',streams[9]['raw'])]
        if any(not math.isfinite(v)or abs(v)>1e8 for row in positions+uv for v in row):raise ValueError('XMD nonfinite coordinate')
        texture_refs=[]
        for j in range(4):
            field=at+0x10+j*4
            if field in rbb.external:texture_refs.append(rbb.reference(field))
            elif rbb.u(field)==0:texture_refs.append(None)
            else:raise ValueError('unqualified XMD texture binding')
        if texture_refs[0]is None or any(t is not None and t['type']!='XTX'for t in texture_refs):raise ValueError('XMD texture reference type')
        meshes.append({'submesh':i,'offset':at,'positions':positions,'normals':normals,'uvs':uv,
            'triangles':strip_triangles(indices,nvert),'original_indices':indices,'indices_offset':idx_at,
            'texture_resource_ids':[t['id']if t is not None else None for t in texture_refs],'streams':streams,
            'raw_flags':rbb.u(at+12),'model_flags':rbb.u(root+4),'declaration':declaration})
    if sum(len(m['triangles'])for m in meshes)!=rbb.u(root+8)or sum(len(m['positions'])for m in meshes)!=rbb.u(root+12):
        raise ValueError('XMD original declared triangle/vertex count mismatch')
    return meshes

def xtx_texture(rbb,index):
    from PIL import Image
    row=rbb.resources[index];root=row['offset']
    if row['type']!='XTX'or rbb.endian!='<':raise ValueError('Xbox XTX required')
    width,height,format_,levels=struct.unpack('<4I',rbb.slice(root,16))
    if any(not 4<=d<=2048 or d&(d-1)for d in(width,height))or format_ not in(12,15)or not 1<=levels<=12:raise ValueError('XTX format/dimensions UNSUPPORTED')
    data_at=rbb.pointer(root+44);mips=[];cursor=data_at;w,h=width,height
    for level in range(levels):
        size=((w+3)//4)*((h+3)//4)*(8 if format_==12 else 16)
        raw=rbb.slice(cursor,size);mips.append({'level':level,'width':w,'height':h,'offset':cursor,'bytes':size,'sha256':digest(raw)})
        cursor+=size;w=max(1,w//2);h=max(1,h//2)
    original=rbb.slice(data_at,cursor-data_at);top=original[:mips[0]['bytes']]
    image=Image.frombytes('RGBA',(width,height),top,'bcn',1 if format_==12 else 3)
    return {'width':width,'height':height,'format':format_,'mips':mips,'original':original,'rgba':image.tobytes(),'offset':root}
