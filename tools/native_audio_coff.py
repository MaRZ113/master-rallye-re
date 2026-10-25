"""Bounded i386 COFF link of our source-only supplemental audio helper."""
from pathlib import Path
import hashlib,os,struct,subprocess,tempfile

SOURCE=Path(__file__).with_name('native_audio')/'layers.c'
DEFAULT_CL=Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x86/cl.exe')
def compile_object():
    compiler=Path(os.environ.get('MR_SDK_X86_CL',str(DEFAULT_CL)))
    if not compiler.is_file():raise ValueError('MSVC x86 cl.exe required; set MR_SDK_X86_CL')
    scratch=Path(__file__).resolve().parents[1]/'.research-output/vehicles/vaudio2-fix2/native-build';scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as tmp:
        out=Path(tmp)/'layers.obj'
        args=[str(compiler),'/nologo','/TP','/c','/O1','/GS-','/Zl','/Oi','/arch:IA32','/fp:strict','/Fo'+str(out),str(SOURCE)]
        r=subprocess.run(args,capture_output=True,text=True)
        if r.returncode:raise ValueError('native audio C compile failed: '+r.stdout+r.stderr)
        raw=out.read_bytes()
    return raw,{'compiler_sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'options':['/TP','/c','/O1','/GS-','/Zl','/Oi','/arch:IA32','/fp:strict']}

def link_object(raw,base):
    machine,n,_,symoff,nsym,optional,_=struct.unpack_from('<HHIIIHH',raw)
    if machine!=0x14c or n>32 or optional:raise ValueError('unsupported audio COFF')
    sections=[];blob=bytearray()
    for i in range(n):
        at=20+40*i;name=raw[at:at+8].rstrip(b'\0').decode();_,_,size,start,rel,_,count,_,flags=struct.unpack_from('<IIIIIIHHI',raw,at+8)
        admitted=name.startswith(('.text','.rdata'))
        if name.startswith(('.data','.bss')) and size:raise ValueError('mutable native globals forbidden')
        offset=None
        if admitted:
            blob+=b'\x90'*((-len(blob))%16);offset=len(blob);blob+=raw[start:start+size]
        sections.append((offset,start,size,rel,count))
    stringbase=symoff+nsym*18;symbols={};names={};i=0
    while i<nsym:
        at=symoff+i*18;name=raw[at:at+8]
        if name[:4]==b'\0'*4:
            k=stringbase+struct.unpack_from('<I',name,4)[0];name=raw[k:raw.index(0,k)]
        name=name.rstrip(b'\0').decode();value,section,typ,storage,aux=struct.unpack_from('<IhHBB',raw,at+8)
        if section>0 and sections[section-1][0] is not None:
            symbols[i]=base+sections[section-1][0]+value;names[name]=symbols[i]
        i+=1+aux
    for offset,start,size,rel,count in sections:
        if offset is None:continue
        for i in range(count):
            at,symbol,kind=struct.unpack_from('<IIH',raw,rel+10*i)
            if symbol not in symbols:raise ValueError('unresolved native helper symbol '+str(symbol))
            target=offset+at;value=struct.unpack_from('<I',blob,target)[0]
            if kind==6:value+=symbols[symbol]
            elif kind==20:value+=symbols[symbol]-(base+target+4)
            else:raise ValueError('unsupported native COFF relocation '+str(kind))
            struct.pack_into('<I',blob,target,value&0xffffffff)
    return bytes(blob),names
