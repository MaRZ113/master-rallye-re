"""Exact-retail QPC counters around qualified synchronous loading call sites.

No cache policy, texture quality, resource lifetime or original file changes.
Caller supplies unused RW/NX telemetry space in its sealed private allocation.
"""
import hashlib,struct
import patch_vehicle_registry_id26 as registry

RETAIL_SHA256='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
QPC_IAT=0x68f228
STAGES=(
    ('dx_cached_read_parse',0x53c719,0x551430,1,None),
    ('gxi_fallback_load',0x53d3e6,0x53dcc0,1,None),
    ('dxt_cached_load_inclusive',0x53d3fc,0x53df60,2,None),
    ('gpu_create_texture',0x5589cd,None,8,bytes.fromhex('ff525085c0')),
    ('surface_convert_upload',0x558a3f,0x5d8982,10,None),
    ('mipmap_generation',0x558a71,0x5d9281,4,None),
    ('texture_lru_eviction_release',0x53d53b,0x558740,0,None),
    ('texture_manager_clear_entry',0x53cffc,0x53e7c0,1,None),
    ('model_lru_eviction_release',0x53c09c,0x54c780,0,None),
)
COUNTER_STRIDE=32
STATE_BYTES=len(STAGES)*COUNTER_STRIDE


def wrapper(base_va,target,argc,counter_va,*,gpu=False):
    c=registry._CodeImage(base_va)
    def emit(h):c.emit(bytes.fromhex(h))
    emit('55 8bec 83ec10 9c60 8d45f8 50 ff1528f26800 619d')
    for i in reversed(range(argc)):emit('ff75'+f'{8+i*4:02x}')
    if gpu:emit('ff5250')
    else:c.call(target)
    # Preserve the original result, flags and volatile registers while timing.
    emit('9c60 8d45f0 50 ff1528f26800 8b45f0 8b55f4 2b45f8 1b55fc b9');c.emit(struct.pack('<I',counter_va))
    # No native calls occur under this short per-stage lock. Nested measured
    # calls have distinct counters; readers may retry a busy row.
    c.label('lock');emit('bb01000000 8719 85db');c.jne('lock')
    emit('ff4104 014108 11510c 894118 89511c 3b5114');c.ja('maximum');c.emit(bytes.fromhex('0f82'));c.rel32.append((len(c.code),len(c.code)+4,'unlock'));c.emit(b'\0'*4)
    emit('3b4110 0f86');c.rel32.append((len(c.code),len(c.code)+4,'unlock'));c.emit(b'\0'*4)
    c.label('maximum');emit('894110 895114')
    c.label('unlock');emit('c70100000000 619d 8be55d')
    if gpu:emit('85c0') # replay TEST displaced alongside 3-byte indirect CALL
    emit('c2');c.emit(struct.pack('<H',argc*4))
    return c.build()


def append_frontend_perf(source,image,blob,payload_va,allocation_size,*,state_va,state_size,audio_state=None):
    if hashlib.sha256(source).hexdigest()!=RETAIL_SHA256 or len(source)!=len(image):raise ValueError('unqualified frontend performance target')
    if type(state_va) is not int or state_va%16 or state_size<STATE_BYTES or not payload_va<=state_va or state_va+state_size>payload_va+allocation_size:raise ValueError('invalid telemetry storage')
    if audio_state:
        stride=audio_state['voice_slot_stride'];capacity=audio_state['map_capacity']
        start=audio_state['entries']['cursor'];used=4+capacity*8+capacity*stride
        if stride not in (40,44) or not 1<=capacity<=64 or state_va<start+used or state_va+state_size>start+4096:raise ValueError('telemetry overlaps supplemental audio state')
    # State must be reserved zero bytes already inside the emitted allocation.
    state_offset=state_va-payload_va
    if state_offset+state_size>len(blob) or any(blob[state_offset:state_offset+state_size]):raise ValueError('telemetry overlaps nonzero or unreserved data')
    pe=registry.parse_pe(source);result=bytearray(image);combined=blob;rows=[];operations=[]
    for index,(name,site,target,argc,original) in enumerate(STAGES):
        expected=original or b'\xe8'+struct.pack('<i',target-site-5)
        off=registry.va_to_file_offset(pe,site,len(expected))
        if source[off:off+len(expected)]!=expected or image[off:off+len(expected)]!=expected:raise ValueError('frontend perf preimage changed: '+name)
        combined+=b'\x90'*(-len(combined)%16);entry=payload_va+len(combined)
        combined+=wrapper(entry,target,argc,state_va+index*COUNTER_STRIDE,gpu=original is not None)
        replacement=b'\xe8'+struct.pack('<i',entry-site-5);result[off:off+5]=replacement
        operations.append({'name':'frontend_perf_'+name,'file_offset':off,'original_bytes':expected.hex(),'replacement_bytes':replacement.hex()})
        rows.append({'name':name,'call_va':site,'original_target':target,'argc':argc,'entry_va':entry,'counter_va':state_va+index*COUNTER_STRIDE})
    if len(combined)>allocation_size:raise ValueError('frontend profiler exceeds sealed allocation')
    return bytes(result),combined,{'operations':operations,'stages':rows,'state_va':state_va,'state_bytes':STATE_BYTES,'counter_stride':COUNTER_STRIDE,
        'layout':{'lock':0,'calls':4,'total_qpc_u64':8,'maximum_qpc_u64':16,'last_qpc_u64':24},'prefix_size':len(blob),'prefix_sha256':hashlib.sha256(blob).hexdigest(),
        'clock_iat':QPC_IAT,'boundary':'inclusive synchronous CPU wall time, including nested calls and driver blocking; GPU completion and fileIO/decoder subcosts are not independently timed','runtime_qualified':False}
