"""Read-only bounded ModelSet2/VIF evidence and conservative pass translation.

Layouts follow the user-supplied PDTools ModelSet2/PGLUshape/VIF readers.
Unqualified GS effects remain explicit, never inferred from MatN labels.
"""
import struct,math,hashlib,re

class Reader:
    def __init__(self,data):self.data=data
    def get(self,fmt,offset):
        size=struct.calcsize('<'+fmt)
        if offset<0 or offset+size>len(self.data):raise ValueError('GT4 span out of bounds')
        return struct.unpack_from('<'+fmt,self.data,offset)

def modelset(data):
    if len(data)>64*1024*1024:raise ValueError('source budget exceeded')
    r=Reader(data);base=r.get('I',24)[0] if data[:4]==b'CAR4' else 0
    if data[base:base+4]!=b'MDLS':raise ValueError('expected CAR4/MDLS ModelSet2')
    count=r.get('H',base+24)[0];table=r.get('I',base+60)[0];shapes=[]
    if not 0<count<=4096:raise ValueError('shape budget exceeded')
    for i in range(count):
        off=base+r.get('I',base+table+4*i)[0];bits,unk3,n,verts,tris=r.get('BBHHH',off+8);packets=[]
        if n>4096:raise ValueError('packet budget exceeded')
        for j in range(n):
            relative,qwords,flags=r.get('IHH',off+16+j*8);start=off+relative;end=start+16*qwords;r.get(f'{16*qwords}s',start)
            packets.append({'offset':start,'end':end,'material':flags>>9,'texture':flags&511,'commands':vif(data,start,end)})
        shapes.append({'index':i,'offset':off,'flags':[bits&31,bits>>5,unk3],'header_vertices':verts,'header_triangles':tris,'packets':packets})
    texture_sets=[];texture_lods=r.get('H',base+28)[0];colors=r.get('H',base+30)[0];sets_offset=r.get('I',base+68)[0]
    if colors:
        listing=r.get('I',base+sets_offset)[0]
        for lod in range(texture_lods):
            t=base+r.get('I',base+listing+4*lod)[0]
            if data[t:t+4]!=b'Tex1':raise ValueError('bad texture set')
            count_t=r.get('H',t+20)[0];mapping=r.get('I',t+24)[0];records=[]
            for k in range(count_t):
                tex0=r.get('Q',t+mapping+40*k)[0];clamp=r.get('Q',t+mapping+40*k+32)[0]
                records.append({'index':k,'tcc':(tex0>>34)&1,'tfx':(tex0>>35)&3,'wrap_s':clamp&3,'wrap_t':(clamp>>2)&3,'min_u':(clamp>>4)&1023,'max_u':(clamp>>14)&1023,'min_v':(clamp>>24)&1023,'max_v':(clamp>>34)&1023,'raw_tex0':hex(tex0),'raw_clamp':hex(clamp)})
            texture_sets.append(records)
    models_offset=r.get('I',base+56)[0];models_count=r.get('H',base+22)[0]
    models=[{'index':i,'origin':r.get('fff',base+models_offset+40*i+12),'commands_offset':base+r.get('I',base+models_offset+40*i+24)[0]} for i in range(models_count)]
    materials=[]
    material_count=r.get('H',base+26)[0];material_offset=r.get('I',base+64)[0]
    if material_count>4096:raise ValueError('material budget exceeded')
    for i in range(material_count):
        at=base+material_offset+i*80;values=r.get('16f',at)
        if not all(math.isfinite(v) for v in values):raise ValueError('nonfinite material colour')
        materials.append({'index':i+1,'ambient':values[:4],'diffuse':values[4:8],
                          'specular':values[8:12],'unknown_colour':values[12:16],
                          'unknown_tail_words':r.get('4I',at+64)})
    return {'base':base,'sha256':hashlib.sha256(data).hexdigest(),'shapes':shapes,'texture_sets':texture_sets,'models':models,'materials':materials}

def vif(data,start,end):
    r=Reader(data);pos=start;out=[];cycle=(1,1)
    while pos<end:
        at=pos;addr,num,op=r.get('HBB',pos);pos+=4;code=op&127;entry={'offset':at,'address':addr,'opcode':code,'count':num,'values':[]}
        if addr==0xc0c0:
            loops,pad,bits,regs=r.get('HHII',pos);pos+=12
            prim=(bits>>15)&0x7ff
            entry['gif']={'loops':loops&0x7fff,'eop':bool(loops&0x8000),
                          'prim':prim,'primitive':prim&7,'textured':bool(prim&16),
                          'blend':bool(prim&64),'gouraud':bool(prim&8),
                          'fog':bool(prim&32),'pre':bool(bits&0x4000),'registers':regs}
        elif code in (0x30,0x31):entry['register_words']=list(r.get('4I',pos));pos+=16
        elif code==0x20:entry['register_words']=list(r.get('I',pos));pos+=4
        elif code==1:cycle=(addr&255,(addr>>8)&255)
        elif code&0x60==0x60:
            if cycle[0]!=cycle[1]:raise ValueError('non-contiguous VIF cycle unsupported')
            kind=code&3;dims=((code>>2)&3)+1;count=num or 256
            if kind==3:raise ValueError('V4-5 unpack unsupported')
            fmt=('i','h','B')[kind];length=(4,2,1)[kind]*dims
            entry['format']=[kind,dims]
            for _ in range(count):entry['values'].append(list(r.get(fmt*dims,pos)));pos+=length
        elif code in (0x4a,0x50,0x51):raise ValueError('unsupported VIF upload/direct command')
        elif code not in (0,1,2,3,4,5,6,7,0x10,0x11,0x13,0x14,0x15,0x17):raise ValueError(f'unknown VIF opcode {code:#x} at {at:#x}')
        pos=(pos+3)&~3
        if pos>end:raise ValueError('VIF packet overflow')
        out.append(entry)
    return out

def shape_geometry(shape,*,uv_mask=None):
    """Recover packet-local strips; never join attribute arrays across packets."""
    vertices=[];triangles=[];packets=[]
    for packet in shape['packets']:
        cmds=packet['commands'];p=next((c for c in cmds if c['address'] in (0xc000,0x8000) and c.get('format',[0,0])[1]>=3),None)
        if p is None:raise ValueError('missing position unpack')
        uv_commands=[c for c in cmds if 0x40<=c['address']&0x3ff<0x40+len(p['values']) and c.get('format',[0,0])[1]==2]
        uv=uv_commands[0] if uv_commands else None
        normals=next((c for c in cmds if (c['address'] in (0xc040,0xc080) and c.get('format')==[0,3]) or
                      (c['address'] in (0x8040,0x8080) and c.get('format')==[2,3])),None)
        reset=next((c for c in cmds if c['address']==0xc040 and c.get('format',[0])[0]==2),None)
        if reset is None:raise ValueError('strip reset encoding unresolved')
        def floats(c):
            if c['format'][0]==0:return [tuple(struct.unpack('<f',struct.pack('<i',v))[0] for v in row) for row in c['values']]
            if c['format'][0]==1:return [tuple(v/4096 for v in row) for row in c['values']]
            raise ValueError('position/UV format unsupported')
        positions=floats(p);tex=unpack_uv(cmds,len(positions),initial_mask=uv_mask) if uv else [];ns=unpack_normals(cmds,normals) if normals else []
        if any(not all(math.isfinite(v) for v in normal) for normal in ns):raise ValueError('nonfinite source normal')
        if tex and len(tex)!=len(positions):raise ValueError('packet UV cardinality mismatch')
        if ns and len(ns)!=len(positions):raise ValueError('packet normal cardinality mismatch')
        colours=next((c['values'] for c in cmds if c['address']==0xc080 and c.get('format')==[2,4]),None)
        if colours is not None and len(colours)!=len(positions):raise ValueError('packet colour cardinality mismatch')
        targets={name:next((c for c in cmds if c['address']==address and c.get('format')==fmt),None)
                 for name,address,fmt in [('position',0xc020,[0,3]),('normal',0xc0a0,[0,3]),('uv',0xc060,[0,2])]}
        morph={name:floats(c) for name,c in targets.items() if c is not None}
        if morph and (set(morph)!={'position','normal','uv'} or any(len(values)!=len(positions) for values in morph.values())):
            raise ValueError('incomplete source morph target channels')
        if any(not all(math.isfinite(v) for v in row) for values in morph.values() for row in values):raise ValueError('nonfinite source morph target')
        offset=len(vertices)
        for k,point in enumerate(positions):
            if not all(math.isfinite(v) for v in point):raise ValueError('nonfinite position')
            vertices.append({'position':point[:3],'uv':tex[k] if tex else None,'normal':ns[k] if ns else None,'packet_offset':packet['offset'],
                             'rgba_ps2':tuple(colours[k]) if colours is not None else None,
                             'normal_encoding':'signed-byte unit direction' if normals and normals['format']==[2,3] else 'float32' if normals else None,
                             'morph_target':{name:values[k] for name,values in morph.items()} if morph else None})
        lengths=[(row[0]+6)//3 for row in reset['values'][1:]];cursor=0;before=len(triangles)
        for length in lengths:
            if length<3 or cursor+length>len(positions):raise ValueError('strip reset exceeds packet vertices')
            for k in range(length-2):
                ids=(cursor+k,cursor+k+1,cursor+k+2)
                if k&1:ids=ids[::-1]
                triangles.append(tuple(offset+i for i in ids))
            cursor+=length
        if cursor!=len(positions):raise ValueError('strip vertices unaccounted')
        raw_other=[c for c in cmds if c not in (p,normals,reset,*targets.values()) and c not in uv_commands and c.get('values')]
        gif=next((c['gif'] for c in cmds if 'gif' in c),None)
        if gif and gif['primitive']!=4:raise ValueError('non-strip GIF primitive requires separate decoding')
        packets.append({'material':packet['material'],'texture':packet['texture'],'first_triangle':before,'triangle_count':len(triangles)-before,'untranslated_attributes':raw_other,'gif':gif})
    if len(triangles)!=shape['header_triangles']:raise ValueError('triangle count disagrees with shape header')
    if 'header_vertices' in shape and len(vertices)!=shape['header_vertices']:raise ValueError('vertex count disagrees with shape header')
    return {'vertices':vertices,'triangles':triangles,'packets':packets}


def unpack_normals(commands,normal):
    """Preserve float normals; recover signed V3-8 *directions*, not VU gain.

    The signedness is the VIF USN bit. Race packets put V3-8 at the same
    normal-vector channel as menu V3-32, with STMOD=0. Integer vectors have
    length about 127. Normalization preserves direction independently of the
    still-unreconstructed VU lighting program's scalar conversion factor.
    Raw integer uploads remain in modelset() for provenance/diagnostics.
    """
    if normal['format']==[0,3]:
        return [tuple(struct.unpack('<f',struct.pack('<i',v))[0] for v in row) for row in normal['values']]
    mode=0
    for command in commands:
        if command['opcode']==5:mode=command['address']&3
        if command is normal:break
    if normal['format']!=[2,3] or normal['address']&0x4000 or mode or normal['opcode']&0x10:
        raise ValueError('unqualified packed normal arithmetic')
    result=[]
    for row in normal['values']:
        signed=tuple(v-256 if v&128 else v for v in row)
        length=math.sqrt(sum(v*v for v in signed))
        if not 120<=length<=133:raise ValueError('packed normal is not a qualified unit direction')
        result.append(tuple(v/length for v in signed))
    return result


def unpack_uv(commands, vertex_count,*,initial_mask=None):
    """Decode packet-local UV uploads, including signed delta V2-8/V2-16.

    STMOD(1/2) adds ROW; mode 2 also writes the sum back to ROW. USN is
    immediate bit 14. Split uploads address consecutive VU vectors, so a later
    V2-16 upload can continue a preceding V2-8 stream. Masked/fill-cycle cases
    are rejected instead of guessed. VIF arithmetic is verified against the
    PCSX2 Vif_Unpack implementation; 12-bit UV scaling is the existing GT
    packet convention. This does not decode the VU normal-lighting program.
    """
    mode=0;row=None;result=[None]*vertex_count;cycle=(1,1);mask=initial_mask
    for c in commands:
        op=c['opcode'];address=c['address']
        if op==1:cycle=(address&255,(address>>8)&255)
        elif op==5:mode=address&3
        elif op==0x30:row=list(c['register_words'])
        elif op==0x20:mask=c['register_words'][0]
        elif 0x40<=address&0x3ff<0x40+vertex_count and c.get('format',[0,0])[1]==2:
            if cycle[0]!=cycle[1]:raise ValueError('non-contiguous UV cycle unsupported')
            if op&0x10 and (mask is None or any((mask>>(8*r+2*a))&3 for r in range(4)for a in (0,1))):raise ValueError('masked UV XY replacement or unknown initial mask unsupported')
            kind=c['format'][0];start=(address&0x3ff)-0x40
            if start+len(c['values'])>vertex_count:raise ValueError('UV upload exceeds vertex array')
            if kind==0 and mode:raise ValueError('float UV with ROW arithmetic unsupported')
            if mode not in (0,1,2):raise ValueError('UV unpack mode unsupported')
            if mode and row is None:raise ValueError('delta UV has no packet-local ROW initializer')
            bits={0:32,1:16,2:8}[kind]
            for index,values in enumerate(c['values']):
                decoded=[]
                for axis,raw in enumerate(values):
                    if kind==0:v=struct.unpack('<f',struct.pack('<I',raw&0xffffffff))[0]
                    else:
                        raw &= (1<<bits)-1
                        if not address&0x4000 and raw&(1<<(bits-1)):raw-=1<<bits
                        if mode:raw=(raw+row[axis])&0xffffffff
                        if mode==2:row[axis]=raw
                        raw &= 0xffffffff
                        if raw&0x80000000:raw-=1<<32
                        v=raw/4096
                    if not math.isfinite(v):raise ValueError('nonfinite UV')
                    decoded.append(v)
                if result[start+index] is not None:raise ValueError('overlapping UV uploads unsupported')
                result[start+index]=tuple(decoded)
    if any(x is None for x in result):raise ValueError('UV upload leaves holes')
    return result

def translate_pass(commands,*,shadow=False,external_texture=False,tail_branch=None):
    state={'alpha_test':True,'alpha_func':'GREATER','alpha_ref':32,'blend':[0,1,0,1,1],'write_mask':0xffffffff,'depth_write':True,'destination_alpha_test':False};unknown=[]
    for command in commands:
        if command=='DisableAlphaTest':state['alpha_test']=False
        elif command=='EnableAlphaTest':state['alpha_test']=True
        elif command=='DisableDepthMask':state['depth_write']=False
        elif command=='EnableDepthMask':state['depth_write']=True
        elif command=='EnableDestinationAlphaTest':state['destination_alpha_test']=True
        elif command=='DisableDestinationAlphaTest':state['destination_alpha_test']=False
        elif command.startswith('AlphaFunction('):
            fn,ref=command[14:-1].split(',');state.update(alpha_func=fn.strip(),alpha_ref=int(ref))
        elif command.startswith('BlendFunction('):state['blend']=[int(x) for x in command[14:-1].split(',')]
        elif command.startswith('ColorMask('):state['write_mask']=int(command[10:-1],0)
        elif command.startswith(('DestinationAlphaFunc(','FogColor(','ExternalTextureIndex(')):state.setdefault('special_commands',[]).append(command)
        else:unknown.append(command)
    if shadow:route='unsupported_shadow'
    elif external_texture:route='unsupported_environment'
    elif not state['write_mask']&0xffffff:route='alpha_only_effect'
    elif state['destination_alpha_test'] or not state['depth_write'] or unknown or any(c.startswith(('FogColor(','ExternalTextureIndex(')) for c in state.get('special_commands',[])):route='unsupported_special'
    elif state['alpha_test'] and state['alpha_func']!='GREATER':route='unsupported_alpha_function'
    elif state['blend'][:4]==[0,1,0,1]:route='source_alpha' if not state['alpha_test'] else 'alpha_test'
    else:route='unsupported_blend'
    return {'route':route,'state':state,'unknown_commands':unknown,'tail_branch':tail_branch,'approximation':'MR source-alpha / alpha-test only; destination-alpha/masks/effects retained as unsupported records'}
