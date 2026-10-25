"""Exact-build source-bound alpha ownership bridge for external SDK runtimes.

No EXE or graphics DLL is written. Generated code calls native damage once,
then restores only coverage alpha when full original position and UV buffers
match the supplied model. Unknown models and unsuccessful native calls pass
through unchanged. A bounded 64/128-KiB process extension is used separately
from capacity experiments; occupied addresses fail closed in the launcher.
"""
import hashlib,struct
from master_rallye.dx import parse_dx_bytes
from master_rallye.addon_sdk.damage_policy import alpha_ownership
import patch_vehicle_registry_id26 as registry

RETAIL_SHA256='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
DAMAGE_CALL_VA=0x0056bd1d
DAMAGE_NATIVE_VA=0x005892e0
PAYLOAD_VA=0x10000000


def payload(model_data):
    policy=alpha_ownership(model_data);m=parse_dx_bytes(model_data);n=m.vertex_count
    code=registry._CodeImage(PAYLOAD_VA)
    def emit(s):code.emit(bytes.fromhex(s))
    def length_check(count):emit('81fa');code.emit(struct.pack('<I',count));code.jne('return')
    def compare(label,count):
        code.mov_eax_literal(label);emit('97 b9');code.emit(struct.pack('<I',count));emit('fc f3a7');code.jne('return')
    code.label('entry');emit('55 8bec 53 56 57 8bd9')
    # Copy original four stack arguments, preserve original this in EBX.
    emit('ff7514 ff7510 ff750c ff7508 8bcb');code.call(DAMAGE_NATIVE_VA)
    emit('50 9c 84c0');code.je('return')
    # Original CPU model: vector<XYZ> at +0, vector<UV-set> at +30h.
    emit('8b4508 8b7004 8b5008 2bd6');length_check(n*12)
    compare('positions',n*3)
    emit('8b4508 8b7034 85f6');code.je('return')
    emit('8b5038 2bd6');length_check(16)
    emit('8b5608 8b7604 2bd6');length_check(n*8)
    compare('uvs',n*2)
    # Source/current colour vector lengths must agree before byte restoration.
    emit('8b4508 8b7024 8b5028 2bd6');length_check(n*4)
    emit('8b7b0c 85ff');code.je('return')
    emit('8b5708 8b7f04 2bd7');length_check(n*4)
    code.mov_eax_literal('mask');emit('ba');code.emit(struct.pack('<I',n))
    code.label('alpha');emit('803801');code.jne('next')
    emit('8a4e03 884f03')
    code.label('next');emit('83c604 83c704 40 4a');code.jne('alpha')
    code.label('return');emit('9d 58 5f 5e 5b 5d c21000')
    code.align();code.label('positions')
    code.emit(b''.join(struct.pack('<3f',*p) for p in m.vertices.positions))
    code.label('uvs');code.emit(b''.join(struct.pack('<2f',*uv) for uv in m.uv_sets[0].values))
    code.label('mask');code.emit(bytes.fromhex(policy['mask_hex']))
    result=code.build()
    if len(result)>131072:raise ValueError('full damage identity and policy exceed the bounded 128-KiB extension budget')
    return result,{**policy,'payload_va':PAYLOAD_VA,'payload_size':len(result),
        **({'allocation_size':131072} if len(result)>65536 else {}),
        'code_size':code.labels['positions'],'entries':{k:PAYLOAD_VA+v for k,v in code.labels.items()},
        'identity':'full source XYZ and UV byte equality plus vector lengths; resource metadata separately sealed by launcher',
        'runtime_qualified':False}


def extend_image(source,base_image,model_data):
    if hashlib.sha256(source).hexdigest()!=RETAIL_SHA256 or len(source)!=len(base_image):raise ValueError('unqualified retail source')
    pe=registry.parse_pe(source);off=registry.va_to_file_offset(pe,DAMAGE_CALL_VA,5)
    expected=b'\xe8'+struct.pack('<i',DAMAGE_NATIVE_VA-DAMAGE_CALL_VA-5)
    if source[off:off+5]!=expected or base_image[off:off+5]!=expected:raise ValueError('native damage call preimage changed')
    blob,report=payload(model_data);image=bytearray(base_image)
    after=b'\xe8'+struct.pack('<i',PAYLOAD_VA-DAMAGE_CALL_VA-5);image[off:off+5]=after
    report['operations']=[{'name':'coverage_alpha_after_native_damage','file_offset':off,
        'original_bytes':expected.hex(),'replacement_bytes':after.hex()}]
    report['private_payload_hex']=blob.hex()
    return bytes(image),report


def payload_models(models, *, payload_va=PAYLOAD_VA):
    """One deformation call, then full source identities for independent models.

    A singleton at the historic address retains the exact legacy byte stream.
    The 256-KiB limit is an explicit SDK storage budget, not an engine limit.
    """
    models=list(models)
    if not 1<=len(models)<=16:raise ValueError('damage model count outside bounded profile')
    if len({hashlib.sha256(data).digest() for data in models})!=len(models):
        raise ValueError('duplicate damage model')
    if len(models)==1 and payload_va==PAYLOAD_VA:return payload(models[0])
    qualified=[];identities=set()
    for data in models:
        policy=alpha_ownership(data);m=parse_dx_bytes(data)
        xyz=b''.join(struct.pack('<3f',*p) for p in m.vertices.positions)
        uv=b''.join(struct.pack('<2f',*p) for p in m.uv_sets[0].values)
        identity=(m.vertex_count,xyz,uv)
        if identity in identities:raise ValueError('ambiguous damage model source identity')
        identities.add(identity);qualified.append((m,policy,xyz,uv))
    code=registry._CodeImage(payload_va)
    def emit(value):code.emit(bytes.fromhex(value))
    code.label('entry');emit('55 8bec 53 56 57 8bd9')
    emit('ff7514 ff7510 ff750c ff7508 8bcb');code.call(DAMAGE_NATIVE_VA)
    emit('50 9c 84c0');code.je('return')
    for i,(m,policy,xyz,uv) in enumerate(qualified):
        n=m.vertex_count;next_label='model'+str(i+1)
        code.label('model'+str(i))
        def length(count):
            emit('81fa');code.emit(struct.pack('<I',count));code.jne(next_label)
        def compare(label,count):
            code.mov_eax_literal(label+str(i));emit('97 b9');code.emit(struct.pack('<I',count));emit('fc f3a7');code.jne(next_label)
        emit('8b4508 8b7004 8b5008 2bd6');length(n*12);compare('positions',n*3)
        emit('8b4508 8b7034 85f6');code.je(next_label)
        emit('8b5038 2bd6');length(16)
        emit('8b5608 8b7604 2bd6');length(n*8);compare('uvs',n*2)
        emit('8b4508 8b7024 8b5028 2bd6');length(n*4)
        emit('8b7b0c 85ff');code.je(next_label)
        emit('8b5708 8b7f04 2bd7');length(n*4)
        code.mov_eax_literal('mask'+str(i));emit('ba');code.emit(struct.pack('<I',n))
        code.label('alpha'+str(i));emit('803801');code.jne('next'+str(i))
        emit('8a4e03 884f03');code.label('next'+str(i));emit('83c604 83c704 40 4a');code.jne('alpha'+str(i))
        code.jump('return')
    code.label('model'+str(len(qualified)))
    code.label('return');emit('9d 58 5f 5e 5b 5d c21000')
    code.align();code_size=len(code.code)
    for i,(m,policy,xyz,uv) in enumerate(qualified):
        code.label('positions'+str(i));code.emit(xyz)
        code.label('uvs'+str(i));code.emit(uv)
        code.label('mask'+str(i));code.emit(bytes.fromhex(policy['mask_hex']));code.align(4)
    result=code.build()
    if len(result)>262144:raise ValueError('multi-model damage identity exceeds bounded 256-KiB extension budget')
    allocation=65536 if len(result)<=65536 else 131072 if len(result)<=131072 else 262144
    return result,{'schema_version':1,'payload_va':payload_va,'payload_size':len(result),'allocation_size':allocation,
        'code_size':code_size,'models':[policy for _,policy,_,_ in qualified],
        'entries':{'entry':payload_va},'identity':'full source XYZ and UV byte equality plus vector lengths; first unique match only',
        'native_deformation_calls_per_dispatch':1,'runtime_qualified':False}


def extend_models(source,base_image,models, *, payload_va=PAYLOAD_VA):
    """Compose once against the original damage call; never chain deformers."""
    if hashlib.sha256(source).hexdigest()!=RETAIL_SHA256 or len(source)!=len(base_image):raise ValueError('unqualified retail source')
    pe=registry.parse_pe(source);off=registry.va_to_file_offset(pe,DAMAGE_CALL_VA,5)
    expected=b'\xe8'+struct.pack('<i',DAMAGE_NATIVE_VA-DAMAGE_CALL_VA-5)
    if source[off:off+5]!=expected or base_image[off:off+5]!=expected:raise ValueError('native damage call preimage changed')
    blob,report=payload_models(models,payload_va=payload_va);image=bytearray(base_image)
    after=b'\xe8'+struct.pack('<i',payload_va-DAMAGE_CALL_VA-5);image[off:off+5]=after
    report['operations']=[{'name':'coverage_alpha_after_native_damage','file_offset':off,'original_bytes':expected.hex(),'replacement_bytes':after.hex()}]
    report['private_payload_hex']=blob.hex()
    return bytes(image),report
