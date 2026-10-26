"""Optional Unicorn/Capstone checks of emitted x86 helpers, never gameplay proof.

Dependencies can be installed into a caller-owned ignored directory. Nothing
is injected into a game. Native Broker/string/allocator calls are isolated.
"""
import argparse,json,struct,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import sdk_capacity_native as native
import j2_frontend_reentry as j2


def validate(source,image,report,rows,*,shared_payload=None):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_ECX as ECX, UC_X86_REG_EDX as EDX, UC_X86_REG_ESI as ESI, UC_X86_REG_ESP as ESP, UC_X86_REG_EIP as EIP, UC_X86_REG_EDI as EDI, UC_X86_REG_EBP as EBP, UC_X86_REG_EBX as EBX
    from capstone import Cs,CS_ARCH_X86,CS_MODE_32
    pe,sections=j2.addon_runtime._pe_sections(image)
    def machine():
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
        for s in sections:u.mem_write(0x400000+s['rva'],image[s['raw_offset']:s['raw_offset']+s['raw_size']])
        if shared_payload is not None:
            base,raw=shared_payload
            u.mem_map(base,(len(raw)+4095)//4096*4096);u.mem_write(base,raw)
        elif report.get('private_payload_hex'):
            u.mem_map(report['payload_va'],65536);u.mem_write(report['payload_va'],bytes.fromhex(report['private_payload_hex']))
        u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x20000)
        u.mem_write(0x100fff0,struct.pack('<I',0x1001000));u.reg_write(ESP,0x100fff0)
        u.reg_write(ECX,0x2000000)
        return u
    def run(u,start,stop=0x1001000):
        u.emu_start(start,stop,count=20000)
        if u.reg_read(EIP)!=stop:raise ValueError('helper did not reach its expected return/continuation')
    mapping=[]
    for c,ids in enumerate([list(range(7))+[26]+[r['physical_id'] for r in rows if r['vehicle_class']=='T1'],list(range(7,14))+[27]+[r['physical_id'] for r in rows if r['vehicle_class']=='T2'],list(range(14,26))]):
        for local,id_ in enumerate(ids):
            u=machine();u.mem_write(0x2000010,struct.pack('<I',c));u.mem_write(0x2000014+4*c,struct.pack('<I',local))
            run(u,0x481e20)
            if u.reg_read(EAX)!=id_ or u.reg_read(ESP)!=0x100fff4:raise ValueError('forward map/stack failure')
            v=machine();v.mem_write(0x100fff4,struct.pack('<I',id_));run(v,0x481e50,0x481e89)
            restored_c=struct.unpack('<I',v.mem_read(0x2000010,4))[0]
            restored_local=struct.unpack('<I',v.mem_read(0x2000014+4*c,4))[0]
            if (restored_c,restored_local)!=(c,local) or v.reg_read(ESP)!=0x100ffec:raise ValueError('reverse map/stack failure')
            mapping.append([id_,c,local])
    # Prove each generated T2 loop chains the baseline ID27 and new IDs once.
    pools={}
    for mode,hook,reentry,exit_ in [('quick_race',native.i0.QUICKRACE_T2_HOOK_VA,native.i0.QUICKRACE_T2_REENTRY_VA,native.i0.QUICKRACE_T2_EXIT_VA),('rallye_cup',native.i0.CUP_T2_HOOK_VA,native.i0.CUP_T2_REENTRY_VA,native.i0.CUP_T2_EXIT_VA),('master_rallye',native.i0.MASTER_T2_HOOK_VA,native.i0.MASTER_T2_REENTRY_VA,native.i0.MASTER_T2_EXIT_VA)]:
        u=machine();seen=[]
        def pool_hook(uc,at,size,user):
            if at==reentry:
                seen.append(uc.reg_read(ESI));uc.reg_write(ESI,seen[-1]+1);uc.reg_write(EIP,hook)
            elif at==exit_:uc.emu_stop()
        u.hook_add(UC_HOOK_CODE,pool_hook);u.reg_write(ESI,14);u.emu_start(hook,0,count=3000)
        expected=[27]+[r['physical_id'] for r in rows if r['vehicle_class']=='T2' and r['ai_eligibility'][mode]['enabled']]
        if seen!=expected or u.reg_read(ESI)!=14:raise ValueError('AI append chain failed: '+mode)
        pools[mode]=seen
    # Full emitted initializer with native call ABI mocks: preserve old record
    # region, verify new record destination/stack arguments, return pointer.
    u=machine();pe=native.registry.parse_pe(source)
    # The generated initializer's first CALL is its verified parent helper.
    def read_at(a,size):
        if shared_payload is not None and shared_payload[0]<=a<a+size<=shared_payload[0]+len(shared_payload[1]):
            return shared_payload[1][a-shared_payload[0]:a-shared_payload[0]+size]
        if report.get('private_payload_hex') and report['payload_va']<=a<report['payload_va']+report['payload_size']:
            raw=bytes.fromhex(report['private_payload_hex']);return raw[a-report['payload_va']:a-report['payload_va']+size]
        off=native.registry.va_to_file_offset(pe,a,size);return image[off:off+size]
    start=report['entries']['init'];parent=start+10+struct.unpack('<i',read_at(start+6,4))[0]
    initialized=[]
    def return_call(uc,cleanup):
        sp=uc.reg_read(ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0];uc.reg_write(ESP,sp+4+cleanup);uc.reg_write(EIP,ret)
    def init_hook(uc,at,size,user):
        if at==parent:return_call(uc,0)
        elif at==native.registry.STRING_CONSTRUCTOR_VA:return_call(uc,4)
        elif at==native.registry.VEHICLE_INITIALIZER_VA:
            sp=uc.reg_read(ESP);args=struct.unpack('<12I',uc.mem_read(sp+4,48));initialized.append({'destination':uc.reg_read(ECX),'arguments':list(args)});return_call(uc,48)
    u.hook_add(UC_HOOK_CODE,init_hook);run(u,start)
    if u.reg_read(ESP)!=0x100fff4 or u.reg_read(EAX)!=0x2000000:raise ValueError('initializer stack/return ABI failed')
    if len(initialized)!=len(rows):raise ValueError('initializer missed a row')
    for got,row in zip(initialized,rows):
        if got['destination']!=0x2000000+4+row['physical_id']*52 or got['arguments'][0]!=row['physical_id']:raise ValueError('initializer record destination/ID mismatch')
        colour=struct.pack('<4I',*got['arguments'][-4:]).hex()
        if colour!=row['race_colour_rgba_f32le_hex']:raise ValueError('initializer per-CarID race marker RGBA mismatch')
        got['race_colour_rgba_f32le_hex']=colour
    # Check all literal display paths and their unchanged fallback targets.
    bridges=[(0x481a0e,EDI,'manufacturer',0x481a18),(0x481a4b,EDI,'model',0x481a55),
        *[(v,EAX,'combined',v+8) for v in native.registry.QUICKRACE_LOCALIZATION_CALLS],
        *[(v,ESI,'manufacturer' if group==0x33 else 'model',resume)
          for v,group,label,string,resume in native.registry.RACE_OPTIONS_LOCALIZATION_CALLS],
        *[(hook,EAX,'combined',resume) for hook,slot,label,group,call,resume in native.registry.RACE_DETAILS_LOCALIZATION_CALLS],
        (0x44fa29,EDI,'combined',0x44fa33)]
    def cstring(u,at):return bytes(u.mem_read(at,512)).split(b'\0',1)[0].decode('ascii')
    display_checks=0
    for j,(hook,reg,field,resume) in enumerate(bridges):
        for row in rows:
            u=machine();u.reg_write(reg,row['physical_id']);run(u,hook,resume)
            if cstring(u,u.reg_read(EAX))!=row['frontend'][field] or u.reg_read(ESP)!=0x100fff0:
                raise ValueError('display literal/stack mismatch')
            display_checks+=1
        u=machine();u.reg_write(reg,0)
        # Resolve the last JMP in this bridge, before the following label.
        begin=report['entries'][f'display{j}'];end=report['entries'].get(f'display{j+1}',report['entries']['results'])
        last=end-5;old=last+5+struct.unpack('<i',read_at(last+1,4))[0]
        run(u,hook,old)
        if u.reg_read(ESP)!=0x100fff0:raise ValueError('display fallback changed stack')
    state_checks=[]
    for row in rows:
        u=machine();u.reg_write(EAX,0x2001000);u.reg_write(ESI,0x2000100);u.reg_write(EBP,0)
        u.mem_write(0x2001000,struct.pack('<I',0x2000400));u.mem_write(0x2000100,struct.pack('<I',0x2000200));u.mem_write(0x2000208,struct.pack('<I',row['physical_id']))
        run(u,report['entries']['results'],native.i0.natural.RESULTS_AFTER_LOOKUP_VA)
        if cstring(u,u.reg_read(EAX))!=row['results']['display_name'] or u.reg_read(ESP)!=0x100fff0:
            raise ValueError('Results literal/stack mismatch')
        u=machine();u.mem_write(0x2000004,struct.pack('<I',row['physical_id']));seen_unlock=[]
        def unlock_hook(uc,at,size,user):
            if at==0x45a150:
                seen_unlock.append(struct.unpack('<2I',uc.mem_read(uc.reg_read(ECX),8)))
                uc.reg_write(EAX,1);return_call(uc,0)
        u.hook_add(UC_HOOK_CODE,unlock_hook);run(u,report['entries']['unlock'])
        if seen_unlock!=[(0,10)] or u.reg_read(ESP)!=0x100fff4 or u.reg_read(ECX)!=0x2000000:
            raise ValueError('unlock mirror/stack mismatch')
        u=machine();u.reg_write(EAX,row['physical_id']-3);run(u,report['entries']['locked'],0x481b49)
        if u.reg_read(EBX)!=12 or u.reg_read(ESP)!=0x100fff0:raise ValueError('locked-reason ABI mismatch')
        state_checks.append(row['physical_id'])
    # Exercise stock fallbacks as well as added rows, using the real emitted
    # parent helper. Native getter mocks must honour *volatile* register ABI:
    # preserving ECX hid SCALE1's double-getter crash in the original tests.
    audio_checks=[]
    for physical in range(28+len(rows)):
        for participant in (0,2,5):
            u=machine();u.mem_write(0x100fff4,struct.pack('<I',participant));getter_args=[]
            def audio_hook(uc,at,size,user):
                if at==native.i0.audio.RACE_CAR_ID_GETTER_VA:
                    this=uc.reg_read(ECX)
                    if this!=0x2000000:raise ValueError(f'audio getter destroyed this pointer: {this:#x}')
                    getter_args.append(struct.unpack('<I',uc.mem_read(uc.reg_read(ESP)+4,4))[0])
                    uc.reg_write(EAX,physical);uc.reg_write(ECX,2);uc.reg_write(EDX,0xdeadbeef)
                    return_call(uc,4)
            u.hook_add(UC_HOOK_CODE,audio_hook);run(u,report['entries']['audio'])
            expected=next((r['audio']['stock_audio_profile_id'] for r in rows if r['physical_id']==physical),native.i0.audio_profile_for(physical))
            if getter_args!=[participant] or u.reg_read(EAX)!=expected or u.reg_read(ESP)!=0x100fff8:
                raise ValueError('audio single-lookup/profile/argument cleanup mismatch')
            audio_checks.append({'physical_id':physical,'participant':participant,'getter_calls':len(getter_args),'profile':expected})
    # Decode only emitted instruction ranges; literal strings are excluded.
    code_end=min(v for k,v in report['entries'].items() if k.startswith('name'))
    code=read_at(report['payload_va'],code_end-report['payload_va']);ins=list(Cs(CS_ARCH_X86,CS_MODE_32).disasm(code,report['payload_va']))
    if sum(i.size for i in ins)!=len(code):raise ValueError('generated payload has undecodable instructions')
    return {'status':'PASS_EMITTED_HELPERS_WITH_NATIVE_CALL_MOCKS','mapping':mapping,'pools':pools,'initializers':initialized,
            'instructions_decoded':len(ins),'display_literal_checks':display_checks,'results_unlock_audio_abi_ids':state_checks,'audio_single_lookup_checks':audio_checks,'runtime_qualified':False,'limitations':['Unicorn CPU helpers, not the native game lifecycle','Broker, allocator, string, audio getter, unlock oracle and native loop append body are mocked; getter clobbers ECX/EDX','No GPU, collision, gameplay, campaign save or Results lifecycle proof']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--row',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source=(ROOT.parent/'MRallye.exe').read_bytes();_,base,_=j2._parse_and_reconstruct(source,(a.base/'native-patch-ops.rvp').read_bytes());rows=[json.loads(a.row.read_text())]
    image,report=native.extend_image(source,base,rows);result=validate(source,image,report,rows);a.output.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['mapping','initializers']},indent=2))
