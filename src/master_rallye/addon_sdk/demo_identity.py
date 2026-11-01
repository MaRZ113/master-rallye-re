"""Read-only historical table evidence. Never equate IDs across game builds."""
import math
import struct


def load_segments(raw):
    if not 64<=len(raw)<=32*1024*1024:raise ValueError('Executable inspection size budget')
    rows=[]
    if raw[:4]==b'\x7fELF' and raw[4:6]==b'\x01\x01':
        offset=struct.unpack_from('<I',raw,28)[0];size,count=struct.unpack_from('<2H',raw,42)
        if size!=32 or not 1<=count<=128:raise ValueError('Unsupported ELF program table')
        for i in range(count):
            typ,fo,va,_,length,_,_,_=struct.unpack_from('<8I',raw,offset+i*size)
            if typ==1:rows.append((fo,length,va))
    elif raw[:2]==b'MZ':
        pe=struct.unpack_from('<I',raw,60)[0]
        if raw[pe:pe+4]!=b'PE\0\0':raise ValueError('Invalid PE signature')
        count=struct.unpack_from('<H',raw,pe+6)[0];size=struct.unpack_from('<H',raw,pe+20)[0]
        if not 1<=count<=96 or struct.unpack_from('<H',raw,pe+24)[0]!=0x10b:raise ValueError('Unsupported PE32 table')
        base=struct.unpack_from('<I',raw,pe+52)[0]
        for i in range(count):
            _,va,length,fo=struct.unpack_from('<4I',raw,pe+24+size+40*i+8);rows.append((fo,length,base+va))
    else:raise ValueError('Only PE32 / ELF32 little-endian are supported')
    if any(fo+length>len(raw) or va+length>0x100000000 for fo,length,va in rows):raise ValueError('Loaded range outside original file')
    return rows


def file_offset(segments,va,size=1):
    hits=[fo+va-base for fo,length,base in segments if base<=va and va+size<=base+length]
    if len(hits)!=1:raise ValueError('Address has no unique file-backed mapping')
    return hits[0]


def cstring(raw,segments,va):
    try:offset=file_offset(segments,va)
    except ValueError:return None
    end=raw.find(b'\0',offset,min(offset+128,len(raw)))
    if end<0:return None
    text=raw[offset:end]
    return text.decode('ascii') if text and all(32<=c<=126 for c in text) else None


def localized_tables(raw):
    """Retain exact triples and table runs, including pointers inside strings."""
    segments=load_segments(raw);rows=[]
    for offset in range(0,len(raw)-11,4):
        category,index,pointer=struct.unpack_from('<3I',raw,offset)
        if category not in (51,52,53,57)or index>=64:continue
        text=cstring(raw,segments,pointer)
        if text:rows.append({'file_offset':offset,'category':category,'index':index,'pointer':pointer,'text':text})
    # A standalone numerical coincidence is evidence to inspect, not a table.
    offsets={r['file_offset'] for r in rows}
    return [r for r in rows if r['file_offset']-12 in offsets or r['file_offset']+12 in offsets]


def localized_value(rows,category,index):
    selected=[r for r in rows if (r['category'],r['index'])==(category,index)]
    values=sorted({r['text']for r in selected})
    return {'status':'PROVEN'if len(values)==1 else'UNKNOWN','value':values[0]if len(values)==1 else None,'alternatives':values,'records':selected}


def selected_identity(identity,default_marker):
    """Original recovery wins over fallback without deleting either history."""
    original=identity['driver'];fallback=identity.get('driver_assignment')
    if original['value'] and original.get('status')not in('PROVEN','OWNER_CONFIRMED_IN_RACE'):
        raise ValueError('Unproven original driver cannot become an ORIGINAL assignment')
    if fallback is not None:
        value=fallback.get('value')
        if fallback.get('kind')!='REAL_FALLBACK' or not isinstance(value,str)or not value.strip()or len(value)>64 or any(not 32<=ord(c)<=126 for c in value)or not fallback.get('sources')or not fallback.get('credentials'):
            raise ValueError('Real driver fallback needs historical credentials and sources')
    value=original['value'] or (fallback['value']if fallback else identity['frontend']['combined'])
    marker=identity.get('race_marker',{'value':list(default_marker),'status':'UNKNOWN','kind':'SDK_FALLBACK','evidence':'Existing SDK class default; not recovered original RGB'})
    rgba=marker['value']
    if not isinstance(rgba,list)or len(rgba)!=4 or any(type(v)not in(int,float)or not math.isfinite(v)or not 0<=v<=1 for v in rgba):raise ValueError('Invalid historical race marker')
    if marker['status']not in('PROVEN','INFERRED','UNKNOWN'):raise ValueError('Invalid historical confidence')
    return {'driver':{'value':value,'kind':'ORIGINAL'if original['value']else'REAL_FALLBACK'if fallback else'VEHICLE_LABEL_FALLBACK','original':original,'fallback':fallback},'race_marker':marker}


def ps2_registration(raw,begin,end,*,string_call,record_call):
    """Bounded static evaluation of the verified straight-line R5900 initializer.

    Only observed integer moves, FP bit moves and stack stores are admitted.
    Calls are explicitly mocked: this proves initialization data, not runtime.
    """
    if end<=begin or end-begin>16384 or begin%4 or end%4:raise ValueError('Registration instruction budget')
    segments=load_segments(raw);registers={0:0,4:0x100000,29:0x800000};fp={};memory={};records=[];name=None;pending=None
    for pc in range(begin,end,4):
        word=struct.unpack_from('<I',raw,file_offset(segments,pc,4))[0]
        op=word>>26;rs=(word>>21)&31;rt=(word>>16)&31;rd=(word>>11)&31;imm=word&65535;signed=imm if imm<32768 else imm-65536
        get=lambda r:registers[r]if r in registers else None
        if word==0:pass
        elif op==15:registers[rt]=imm<<16
        elif op in(9,25):registers[rt]=None if get(rs)is None else(get(rs)+signed)&0xffffffff
        elif op==13:registers[rt]=None if get(rs)is None else get(rs)|imm
        elif op==0 and word&63 in(33,37,45):
            a,b=get(rs),get(rt);registers[rd]=None if a is None or b is None else(a|b if word&63==37 else(a+b)&0xffffffff)
        elif op==17 and rs==4:fp[rd]=get(rt)
        elif op in(43,57):
            if get(rs)is None:raise ValueError('Unknown registration store address')
            memory[get(rs)+signed]=(fp.get(rt)if op==57 else get(rt))
        elif op in(49,):fp[rt]=memory.get((get(rs)or 0)+signed)
        elif op in(30,31):pass # callee-saved 128-bit stack save/restore, not input data
        elif op==3:
            if pending is not None:raise ValueError('Call in delay slot')
            pending=(pc,((pc+4)&0xf0000000)|((word&0x3ffffff)<<2))
        elif op==0 and word&63==8:
            if rs!=31:raise ValueError('Unexpected indirect registration branch')
        else:raise ValueError('Unsupported R5900 initializer instruction at '+hex(pc)+': '+hex(word))
        registers[0]=0
        if pending and pending[0]+4==pc:
            call,target=pending;pending=None
            if target==string_call:
                name=cstring(raw,segments,get(5))
                if name is None:raise ValueError('Unresolved original resource string')
            elif target==record_call:
                ptr=memory.get(registers[29]+8)
                bits=[memory.get((ptr or 0)+4*i)for i in range(4)]
                if name is None or any(v is None for v in bits):raise ValueError('Unknown original marker input')
                rgba=list(struct.unpack('<4f',struct.pack('<4I',*bits)))
                if any(not math.isfinite(v)or not 0<=v<=1 for v in rgba):raise ValueError('Invalid original marker')
                records.append({'id':get(5),'family':name,'call_va':call,'class':get(6),'stats':[get(r)for r in(7,8,9,10)],'smallcarsheet':get(11),'rgba':rgba,'rgba_bits':[f'{b:08x}'for b in bits]});name=None
            else:raise ValueError('Unqualified call in registration initializer')
            # Preserve only observed callee-saved values, invalidate volatile inputs.
            for r in range(2,16):registers[r]=None
            for r in range(20):fp[r]=None
    ids=[r['id']for r in records]
    if pending or not records or ids!=list(range(len(records))):raise ValueError('Incomplete or reordered registration')
    return records
