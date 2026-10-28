"""Bounded read-only GT3 CarModel1 / ModelSet1 structural source adapter.

Layout evidence: local PDTools CarModel1, ModelSet1, PGLUshape, TextureSet1.
This inventories original structures; it does not equate shape counts with
selected-LOD rendered complexity or infer material semantics from Mat numbers.
"""
import hashlib,struct

MAX_BYTES=16*1024*1024
def sha(b):return hashlib.sha256(b).hexdigest()

def read_source(path):
    """Read an original raw/gzip member without unbounded decompression."""
    import gzip
    from pathlib import Path
    path=Path(path)
    if path.stat().st_size>MAX_BYTES:raise ValueError('GT3 stored source size budget')
    with path.open('rb')as stream:
        compressed=stream.read(2)==b'\x1f\x8b';stream.seek(0)
        try:
            if compressed:
                with gzip.GzipFile(fileobj=stream)as decoded:raw=decoded.read(MAX_BYTES+1)
            else:raw=stream.read(MAX_BYTES+1)
        except (OSError,EOFError)as exc:raise ValueError('Invalid GT3 gzip source')from exc
    if len(raw)>MAX_BYTES:raise ValueError('GT3 decoded source size budget')
    return raw

class Reader:
    def __init__(self,data,lower=0,upper=None):
        if not 32<=len(data)<=MAX_BYTES:raise ValueError('GT3 source size budget')
        self.data=data;self.lower=lower;self.upper=len(data)if upper is None else upper
        if not 0<=self.lower<=self.upper<=len(data):raise ValueError('GT3 component bounds')
    def span(self,off,size):
        if type(off)is not int or type(size)is not int or off<self.lower or size<0 or off+size>self.upper:raise ValueError('GT3 source span outside member/component')
        return self.data[off:off+size]
    def unpack(self,fmt,off):return struct.unpack(fmt,self.span(off,struct.calcsize(fmt)))
    def u32(self,off):return self.unpack('<I',off)[0]
    def pointers(self,base,table,count):
        if not 0<=count<=4096:raise ValueError('GT3 table count budget')
        return [base+n for n in self.unpack('<'+'I'*count,base+table)]

def texture_set(r,off):
    if r.span(off,4)!=b'Tex1':raise ValueError('GT3 texture set magic')
    size=r.u32(off+12);raw=r.span(off,size)
    if size<48:raise ValueError('GT3 texture set too short')
    count,transfers=r.unpack('<HH',off+20);texture_table,transfer_table,patches=r.unpack('<III',off+24)
    if count>1024 or transfers>4096:raise ValueError('GT3 texture table budget')
    def local(at,n):
        if not off<=at<=at+n<=off+size:raise ValueError('GT3 texture table outside Tex1')
        return r.span(at,n)
    local(off+texture_table,count*40);local(off+transfer_table,transfers*0x0c)
    # CLUT variants are source palette patches, not RGB tint presets.
    variants=[]
    if patches:
        n=r.u32(off+patches)
        if n>256:raise ValueError('GT3 CLUT variant budget')
        pointers=r.pointers(off,patches+4,n)
        for i,p in enumerate(pointers):
            if not off<=p<off+size:raise ValueError('GT3 CLUT patch outside texture set')
            entries=struct.unpack('<I',local(p,4))[0]
            if entries>1024:raise ValueError('GT3 CLUT patch budget')
            patch=local(p,4+entries*4)
            words=struct.unpack('<'+'I'*entries,patch[4:])
            if any(w>>23>=count for w in words):raise ValueError('GT3 CLUT texture index outside table')
            variants.append({'index':i,'offset':p,'patch_count':entries,'span_sha256':sha(patch),
                'patches':[{'texture_index':w>>23,'csa':w&31,'cbp':(w>>5)&16383,'psm':(w>>19)&15}for w in words]})
    return {'offset':off,'size':size,'sha256':sha(raw),'textures':count,'transfers':transfers,'source_clut_variants':variants,'colourways':max(1,len(variants))}

def modelset(r,base):
    if r.span(base,4)!=b'GTM1':raise ValueError('Unsupported GT3 ModelSet signature')
    counts=r.unpack('<6H',base+16);models,shapes,materials,textures,variant_tex,variant_mat=counts
    if not 0<models<=64 or not 0<shapes<=4096 or materials>4096 or textures>64 or variant_tex>256 or variant_mat>256:raise ValueError('GT3 ModelSet count budget')
    mt,st,mat,tt,bt,vt,vm=r.unpack('<7I',base+32)
    model_ptrs=r.pointers(base,mt,models);shape_ptrs=r.pointers(base,st,shapes);tex_ptrs=r.pointers(base,tt,textures)
    r.span(base+mat,materials*80);r.span(base+bt,models*16)
    records=[];packet_total=0
    for index,off in enumerate(shape_ptrs):
        flags,other,packets,verts,tris=r.unpack('<BBHHH',off+8)
        packet_total+=packets
        if packets>4096 or packet_total>16384:raise ValueError('GT3 shape packet budget')
        bindings=[]
        for j in range(packets):
            relative,qwords,packed=r.unpack('<IHH',off+16+j*8);r.span(off+relative,qwords*16)
            bindings.append({'material_index':packed>>9,'texture_selector':packed&511})
        records.append({'index':index,'offset':off,'triangles_header':tris,'strip_vertices_header':verts,'packets':packets,'shape_mode':flags&31,'flags':flags>>5,'bindings':bindings})
    tex=[texture_set(r,p)for p in tex_ptrs if p!=base]
    variations=[]
    for p in r.pointers(base,vm,variant_mat):variations.append({'offset':p,'sha256':sha(r.span(p,materials*80))})
    for p in r.pointers(base,vt,variant_tex):
        if p!=base:r.span(p,textures*4)
    return {'offset':base,'models':models,'model_command_offsets':model_ptrs,'shapes':records,'material_count':materials,'material_table_sha256':sha(r.span(base+mat,materials*80)),'texture_sets':tex,'material_variants':variations,'variation_tex_tables':variant_tex,'source_colourway_count':tex[0]['colourways']if tex else 1,'shape_triangle_sum_not_a_lod':sum(p['triangles_header']for p in records),'selected_lod_geometry_status':'NOT TESTED','material_roles_status':'NOT TESTED: source command interpretation required; numeric material IDs are not roles'}

def inspect_car(raw):
    r=Reader(raw);reloc,info,body,tyre,wheel,dummy=r.unpack('<6I',0)
    if reloc!=0 or not 32<=info<body<tyre<wheel<=len(raw):raise ValueError('Unsupported GT3 CarModel component layout')
    if r.span(info,4)!=b'GTCI' or r.span(tyre,4)!=b'GTTR' or r.span(wheel,4)!=b'GTTW':raise ValueError('GT3 component signatures unsupported')
    r.span(info,r.u32(info+12));tyre_end=tyre+r.u32(tyre+12);wheel_end=wheel+r.u32(wheel+12)
    if not tyre<tyre_end<=wheel or not wheel<wheel_end<=len(raw):raise ValueError('GT3 component declared size')
    bodyset=modelset(Reader(raw,body,tyre),body)
    wheelset=modelset(Reader(raw,wheel,wheel_end),wheel+r.u32(wheel+28))
    tiretex=texture_set(Reader(raw,tyre,tyre_end),tyre+r.u32(tyre+28))
    return {'status':'PASS','schema':'gt3-source-structure/1','sha256':sha(raw),'bytes':len(raw),'body':bodyset,'wheel':wheelset,'tyre':tiretex,'component_offsets':{'car_info':info,'body':body,'tyre':tyre,'wheel':wheel,'dummy':dummy},'boundary':'Original component/table/packet spans verified. Inventory is not conversion, selected LOD, material or gameplay qualification.'}
