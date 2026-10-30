"""Exact-build Xbox vertex fragments and isolated original linker execution.

Only original CPU code in a bounded emulator is run. No game/GPU/OS process is
started. Explicit context probes are not captured original runtime state.
"""
import struct
import math
from .dakar2 import PINS
from .dakar2_disc import FileReader,xdvdfs
from .. import universal_vehicle_scene as u
from .nv2a_vertex import decode_program,MAX_INSTRUCTIONS

BASE_PROGRAMS=(0x192588,0x192850)


def read_executable(image):
    reader=FileReader(image)
    row=next(r for r in xdvdfs(reader,0x18300000)if r['path'].lower()=='default.xbe')
    data=reader.read(row['offset'],row['bytes'])
    if u.sha(data)!=PINS['default.xbe']:raise ValueError('Unqualified original Dakar2 XBE')
    return data


def sections(data):
    if u.sha(data)!=PINS['default.xbe']:raise ValueError('Unqualified original Dakar2 XBE')
    base=struct.unpack_from('<I',data,0x104)[0]
    count,table=struct.unpack_from('<II',data,0x11c)
    if not 1<=count<=32:raise ValueError('XBE section budget')
    return [struct.unpack_from('<5I',data,table-base+i*56)for i in range(count)]


def original(data,va,size):
    if type(size)is not int or not 0<=size<=4096:raise ValueError('Native evidence byte budget')
    matches=[s for s in sections(data)if s[1]<=va and va+size<=s[1]+s[4]]
    if len(matches)!=1:raise ValueError('Native address outside unique stored section')
    s=matches[0];offset=s[3]+va-s[1]
    return data[offset:offset+size]


def program(data,va):
    header=original(data,va,4);kind,count=struct.unpack('<HH',header)
    if kind!=0x2078 or not 1<=count<=MAX_INSTRUCTIONS:raise ValueError('Unqualified original vertex fragment header')
    raw=original(data,va,4+count*16)
    decode_program(raw)
    return raw


def link_fragments(fragments):
    """Independent original f85bb non-optimizing concatenate rule."""
    if not isinstance(fragments,list)or not 1<=len(fragments)<=20:raise ValueError('Vertex fragment count budget')
    tokens=[]
    for blob in fragments:
        decoded=decode_program(blob)
        for i in range(decoded['count']):
            token=list(struct.unpack_from('<4I',blob,4+i*16));token[3]&=~1;tokens.append(token)
    if not 1<=len(tokens)<=MAX_INSTRUCTIONS:raise ValueError('Linked vertex instruction budget')
    tokens[-1][3]|=1
    return struct.pack('<HH',0x2078,len(tokens))+b''.join(struct.pack('<4I',*t)for t in tokens)


def compose_original(data,base_va,context):
    """Probe8d800→f85bb with explicit lighting/fog/texture-transform state.

    Driver/GPU bind functions are intercepted after reading their actual input.
    The original linker and fragment selectors execute, including their ABI.
    """
    if base_va not in BASE_PROGRAMS:raise ValueError('Qualified vehicle base program required')
    if not isinstance(context,dict)or set(context)!={'lighting','lights','fog','texture_transforms'}:
        raise ValueError('Explicit complete vertex context required')
    if type(context['lighting'])is not bool or type(context['fog'])is not bool:
        raise ValueError('Boolean lighting/fog state required')
    if not isinstance(context['lights'],list)or len(context['lights'])!=8 or any(x is not None and (type(x)is not int or x not in(0,1))for x in context['lights']):
        raise ValueError('Eight explicit light slots required')
    if not isinstance(context['texture_transforms'],list)or len(context['texture_transforms'])!=4 or any(type(x)is not bool for x in context['texture_transforms']):
        raise ValueError('Four texture transform states required')
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
    sec=sections(data);emu=Uc(UC_ARCH_X86,UC_MODE_32);emu.mem_map(0x10000,0x270000)
    for flags,va,virtual,offset,stored in sec:
        if va<0x10000 or va+max(virtual,stored)>0x280000:raise ValueError('XBE emulation mapping budget')
        if stored:emu.mem_write(va,data[offset:offset+stored])
    emu.mem_map(0x400000,0x10000);emu.mem_map(0x500000,0x10000)
    def put(va,value):emu.mem_write(va,struct.pack('<I',value))
    put(0x231180,0x400000)
    emu.mem_write(0x231089,bytes([context['lighting']]))
    emu.mem_write(0x230ebc,bytes([context['fog']]))
    put(0x230eb8,1)
    for i,kind in enumerate(context['lights']):
        put(0x230cf0+i*60,kind or 0);emu.mem_write(0x230cf4+i*60,bytes([kind is not None]))
    for i,enabled in enumerate(context['texture_transforms']):emu.mem_write(0x230b98+i*96,bytes([enabled]))
    observations={'fragments':[],'bound_program':None,'instructions':0,'last_pc':0}
    def hook(cpu,address,size,user):
        observations['instructions']+=1
        observations['last_pc']=address
        stack=cpu.reg_read(UC_X86_REG_ESP)
        if address==0xf85bb:
            args=struct.unpack('<6I',bytes(cpu.mem_read(stack+4,24)))
            if args[5]!=0 or not 1<=args[4]<=20:raise ValueError('Unqualified optimizing linker/context')
            addresses=struct.unpack('<%dI'%args[4],bytes(cpu.mem_read(args[3],args[4]*4)))
            blobs=[program(data,a)for a in addresses]
            link_fragments(blobs) # Reject allocation excess before native copy.
            observations['fragments']=[{'va':a,'sha256':u.sha(b),'count':decode_program(b)['count']}for a,b in zip(addresses,blobs)]
        if address in(0xe1170,0xe0f10):
            ret=struct.unpack('<I',bytes(cpu.mem_read(stack,4)))[0]
            if address==0xe1170:
                ptr=struct.unpack('<I',bytes(cpu.mem_read(stack+4,4)))[0]
                header=bytes(cpu.mem_read(ptr,4));count=struct.unpack('<HH',header)[1]
                if not 1<=count<=MAX_INSTRUCTIONS:raise ValueError('Native linked program budget')
                observations['bound_program']=bytes(cpu.mem_read(ptr,4+count*16))
            cpu.reg_write(UC_X86_REG_EAX,0);cpu.reg_write(UC_X86_REG_ESP,stack+12);cpu.reg_write(UC_X86_REG_EIP,ret)
    emu.hook_add(UC_HOOK_CODE,hook)
    stop=0x50f000;stack=0x508000
    attributes=0x193bb8 if base_va==BASE_PROGRAMS[0]else 0x193cb8
    emu.mem_write(stack,struct.pack('<4I',stop,0x1b,attributes,base_va));emu.reg_write(UC_X86_REG_ESP,stack)
    try:emu.emu_start(0x8d800,stop,timeout=5_000_000,count=200000)
    except Exception as error:
        raise ValueError('Native composition failed at '+hex(observations['last_pc'])+', EIP='+hex(emu.reg_read(UC_X86_REG_EIP)))from error
    if emu.reg_read(UC_X86_REG_EIP)!=stop or observations['bound_program']is None:
        raise ValueError('Native vertex composition instruction/time/bind gate')
    expected=link_fragments([program(data,r['va'])for r in observations['fragments']])
    if expected!=observations['bound_program']:raise ValueError('Native/Python vertex linking mismatch')
    return {'program':expected,'context':context,'fragments':observations['fragments'],
            'program_sha256':u.sha(expected),'instructions':observations['instructions'],
            'native_linker_matches':True,'original_runtime_state':'NOT CAPTURED'}


def replay_constants(data, *, world, view, projection):
    """Original initializer slices and8cda0 with explicit synthetic matrices.

    Matrix arithmetic/copy/transposition execute unchanged. Only GPU uploads
    and the final deferred render-state setter are intercepted. This identifies
    register ownership, not the matrices of an original running vehicle draw.
    """
    def matrix(values):
        if not isinstance(values,(list,tuple))or len(values)!=16 or any(type(x)not in(int,float)or not math.isfinite(x)or abs(x)>1e6 for x in values):
            raise ValueError('Sixteen bounded explicit matrix values required')
        return struct.pack('<16f',*values)
    matrices=[matrix(x)for x in(world,view,projection)]
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX,UC_X86_REG_EDX
    cpu=Uc(UC_ARCH_X86,UC_MODE_32);cpu.mem_map(0x10000,0x270000);cpu.mem_map(0x500000,0x10000)
    for _,va,virtual,offset,stored in sections(data):
        if va<0x10000 or va+max(virtual,stored)>0x280000:raise ValueError('XBE emulation mapping budget')
        if stored:cpu.mem_write(va,data[offset:offset+stored])
    rows=[];steps=[0]
    def read(at):return struct.unpack('<I',cpu.mem_read(at,4))[0]
    def hook(cpu,address,size,unused):
        steps[0]+=1
        if address in(0xe0f50,0xe0fa0,0x87470):
            stack=cpu.reg_read(UC_X86_REG_ESP);count=4 if address==0xe0f50 else read(stack+4)if address==0xe0fa0 else 0
            if count:
                if not 4<=count<=16 or count%4:raise ValueError('Vertex constant upload budget')
                hardware=cpu.reg_read(UC_X86_REG_ECX);pointer=cpu.reg_read(UC_X86_REG_EDX)
                rows.append({'hardware_index':hardware,'constant_index':hardware-96,
                             'values':list(struct.unpack('<'+str(count)+'f',cpu.mem_read(pointer,count*4)))})
            cpu.reg_write(UC_X86_REG_EIP,read(stack));cpu.reg_write(UC_X86_REG_ESP,stack+(8 if address==0xe0fa0 else 4))
    cpu.hook_add(UC_HOOK_CODE,hook)
    start_stack=0x508000;cpu.reg_write(UC_X86_REG_ESP,start_stack)
    # Execute original stack stores, stopping before the unrelated log call.
    cpu.emu_start(0x86ba0,0x86bcc,count=100)
    if cpu.reg_read(UC_X86_REG_EIP)!=0x86bcc:raise ValueError('Constant initializer slice did not stop')
    # Same locals after original logging arguments have been popped.
    cpu.reg_write(UC_X86_REG_ESP,start_stack-0x20)
    cpu.emu_start(0x86f3a,0x86f60,count=100)
    if cpu.reg_read(UC_X86_REG_EIP)!=0x86f60 or len(rows)!=1 or rows[0]['constant_index']!=65:
        raise ValueError('Original c65 upload slice mismatch')
    initial=rows.pop()
    for ptr,value in zip((0x19d400,0x19dc00,0x19e400),matrices):cpu.mem_write(ptr,value)
    for at in(0x1a0c00,0x1a0c04,0x1a0c08):cpu.mem_write(at,struct.pack('<I',0))
    for at in(0x231084,0x231085,0x231086,0x23108a,0x230ebd):cpu.mem_write(at,b'\0')
    cpu.mem_write(0x231088,b'\1')
    stop=0x50f000;cpu.mem_write(start_stack,struct.pack('<II',stop,0x1b));cpu.reg_write(UC_X86_REG_ESP,start_stack)
    cpu.emu_start(0x8cda0,stop,timeout=5_000_000,count=50000)
    if cpu.reg_read(UC_X86_REG_EIP)!=stop:raise ValueError('Original matrix upload did not return within budget')
    return {'initial_constant65':initial,'matrix_uploads':rows,'instructions':steps[0],
            'input_world':list(world),'input_view':list(view),'input_projection':list(projection),
            'runtime_state':'NOT CAPTURED; explicit controlled matrices',
            'intercepted_gpu_functions':[0xe0f50,0xe0fa0,0x87470]}
