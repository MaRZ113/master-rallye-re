"""Source-qualified batched BGRA reads for canonical native loose DXT streams."""
import hashlib,os,struct,subprocess,tempfile
from pathlib import Path
import patch_vehicle_registry_id26 as registry
from native_audio_coff import DEFAULT_CL,link_object
RETAIL_SHA256='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
SITE=0x558cba
ORIGINAL=0x581120
SOURCE=Path(__file__).with_name('native_frontend')/'dxt_bulk.c'


def compile_helper():
    compiler=Path(os.environ.get('MR_SDK_X86_CL',str(DEFAULT_CL)))
    if not compiler.is_file():raise ValueError('MSVC x86 compiler required')
    scratch=Path(__file__).resolve().parents[1]/'.research-output/vehicles/vsdk1-perf2/native-build';scratch.mkdir(parents=True,exist_ok=True)
    options=['/nologo','/TP','/c','/O1','/GS-','/Zl','/Oi','/arch:IA32','/fp:strict']
    with tempfile.TemporaryDirectory(dir=scratch) as temporary:
        output=Path(temporary)/'dxt-bulk.obj';run=subprocess.run([str(compiler),*options,'/Fo'+str(output),str(SOURCE)],capture_output=True,text=True)
        if run.returncode:raise ValueError('DXT bulk helper build failed: '+run.stdout+run.stderr)
        raw=output.read_bytes()
    return raw,{'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'compiler_sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'options':options}


def append_dxt_bulk(source,image,blob,payload_va,allocation_size):
    if hashlib.sha256(source).hexdigest()!=RETAIL_SHA256 or len(source)!=len(image):raise ValueError('unqualified DXT bulk target')
    pe=registry.parse_pe(source);offset=registry.va_to_file_offset(pe,SITE,5);before=b'\xe8'+struct.pack('<i',ORIGINAL-SITE-5)
    if source[offset:offset+5]!=before or image[offset:offset+5]!=before:raise ValueError('native DXT decoder call preimage changed')
    prefix=blob+b'\x90'*(-len(blob)%16);object_data,compiler=compile_helper();helper,entries=link_object(object_data,payload_va+len(prefix));entry=entries['_dxt_bulk@4'];combined=prefix+helper
    if len(combined)>allocation_size:raise ValueError('DXT bulk adapter exceeds sealed allocation')
    after=b'\xe8'+struct.pack('<i',entry-SITE-5);out=bytearray(image);out[offset:offset+5]=after
    return bytes(out),combined,{'operations':[{'name':'canonical_loose_dxt_batched_pixel_read','file_offset':offset,'original_bytes':before.hex(),'replacement_bytes':after.hex()}],
        'entry_va':entry,'size':len(helper),'prefix_size':len(blob),'prefix_sha256':hashlib.sha256(blob).hexdigest(),'compiler':compiler,
        'scope':'canonical native vtable0069CE44 loose files only; position12; exact20+width*height*4 file length; dimensions1..4096; archive/unknown/noncanonical fallback',
        'boundary':'pixel IO batching only; original native image constructor/destructor and subsequent GPU material/mipmap path unchanged; live speedup pending A/B','runtime_qualified':False}
