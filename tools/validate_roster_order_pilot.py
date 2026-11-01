"""Offline V-DEF3 proof: real x86 helpers, private resources and immutable IDs.

Native Broker/string calls are mocked. This is not D3D8 or save lifecycle proof.
"""
from pathlib import Path
import argparse,json,struct,sys,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools'),str(ROOT/'.research-output/vehicles/v-def1/python-deps')]
from build_sdk_roster import derive
from validate_sdk_roster import validate as validate_resources,SHARED
from validate_sdk_capacity_emulation import validate as validate_helpers
import prepare_sdk_capacity_probe as probe
from master_rallye.addon_sdk.ui_assets import BANKS,parse_bank
from master_rallye.addon_sdk.demo_identity import localized_tables,localized_value


def frontend_machine(image,source):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as EAX,UC_X86_REG_ECX as ECX,UC_X86_REG_ESP as ESP,UC_X86_REG_EIP as EIP
    from j2_frontend_reentry import addon_runtime
    _,sections=addon_runtime._pe_sections(image)
    def machine():
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
        for s in sections:u.mem_write(0x400000+s['rva'],image[s['raw_offset']:s['raw_offset']+s['raw_size']])
        u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x20000)
        u.reg_write(ESP,0x100fff0);u.mem_write(0x100fff0,struct.pack('<II',0x1001000,0));u.reg_write(ECX,0x2000000)
        return u
    def ret(u,args=0,result=0):
        sp=u.reg_read(ESP);pc=struct.unpack('<I',u.mem_read(sp,4))[0]
        u.reg_write(ESP,sp+4+args);u.reg_write(EAX,result);u.reg_write(EIP,pc)
    def run(u,at):
        u.emu_start(at,0x1001000,count=20000)
        if u.reg_read(EIP)!=0x1001000:raise ValueError('native helper failed to return')
    u=machine();keys=[]
    def publish(uc,at,size,data):
        if at==0x5c20ba:
            sp=uc.reg_read(ESP);buffer,fmt,index=struct.unpack('<III',uc.mem_read(sp+4,12))
            pattern=bytes(uc.mem_read(fmt,128)).split(b'\0',1)[0].decode('ascii');text=(pattern%index).encode()+b'\0'
            if len(text)>64:raise ValueError('Publisher stack buffer overflow')
            keys.append(text[:-1].decode());uc.mem_write(buffer,text);ret(uc)
        elif at==0x4d0580:ret(uc,4)
        elif at==0x4d8ec0:ret(uc,8,0x2001000)
        elif at==0x4d8000:ret(uc)
    u.hook_add(UC_HOOK_CODE,publish);run(u,0x481950)
    if keys!=[f'Frontend/VehicleSelect/Button{i}XPos'for i in range(13)]:raise ValueError('13th position is not published')
    nav=[]
    for cls,count in enumerate((8,12,13)):
        for before in range(count):
            u=machine();u.mem_write(0x2000010,struct.pack('<I',cls));u.mem_write(0x2000014+4*cls,struct.pack('<I',before));u.mem_write(0x2000020+4*cls,struct.pack('<I',count))
            def navigate(uc,at,size,data):
                if at in (0x4ae700,0x4adc30,0x481950,0x4819b0,0x481df0):ret(uc)
            u.hook_add(UC_HOOK_CODE,navigate);run(u,0x481f50)
            after=struct.unpack('<I',u.mem_read(0x2000014+4*cls,4))[0]
            if after!=min(before+1,count-1):raise ValueError('Native navigation/count boundary failed')
            nav.append([cls,before,after])
    # Verify original constructor's count consumers and the parent G.1 cave
    # writes (actual bytes), not only values injected by the navigation harness.
    import sdk_capacity_native as native
    pe=native.registry.parse_pe(source)
    counts={}
    for cls,va in [('T1',0x68e638),('T2',0x68e63f),('T3',0x480a65)]:
        off=native.registry.va_to_file_offset(pe,va,1);counts[cls]=image[off]
    if list(counts.values())!=[8,12,13]:raise ValueError('Native count preimages mismatch')
    return {'published_keys':keys,'right_navigation':nav,'native_class_counts':counts,
            'boundary':'Original x86 with mocked Broker; no real frontend/game execution'}


def validate(candidate,baseline,protected):
    config=json.loads((candidate/'roster-config.json').read_text());ctx=derive(config)
    source=Path(config.get('retail_exe',ROOT.parent/'MRallye.exe')).read_bytes()
    result=validate_resources(config,candidate)
    result['helpers']=validate_helpers(source,ctx['image'],ctx['capacity'],ctx['rows'],
        shared_payload=(0x10000000,ctx['files']['native-extension.bin']))
    result['frontend']=frontend_machine(ctx['image'],source)
    root=candidate/'runtime/resource-root';old=baseline/'runtime/resource-root'
    preserved=[];old_manifest=json.loads((baseline/'runtime/resource-manifest.json').read_text())
    for record in old_manifest['resources']:
        path=record['path']
        if path in SHARED:continue
        if (root/path).read_bytes()!=(old/path).read_bytes():raise ValueError('Accepted resource changed: '+path)
        preserved.append(path)
    for path in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
        values=lambda b:{v.get('Name'):dict(v.attrib)for v in ET.fromstring(b).iter('Value')}
        a,b=values((old/path).read_bytes()),values((root/path).read_bytes())
        if any(b.get(k)!=v for k,v in a.items()):raise ValueError('Accepted physics changed')
    for prefix,_,_,_ in BANKS.values():
        a,b=parse_bank((old/(prefix+'.dxb')).read_bytes()),parse_bank((root/(prefix+'.dxb')).read_bytes())
        if a['records']!=b['records'][:a['count']]:raise ValueError('Accepted artwork frame changed')
    # Each physical widget owns its original image, visibility and unlock rules.
    scene='DataScene/FrontendScreens/VehicleSelect.xml'
    before=ET.fromstring((old/scene).read_bytes());after=ET.fromstring((root/scene).read_bytes())
    egg=lambda tree,name:next(e for e in tree.iter('Egg')if e.get('Name')==name)
    from master_rallye.addon_sdk.roster_layout import resolve_layout,BASE
    old_rows=derive(json.loads((baseline/'roster-config.json').read_text()))['rows']
    old_layout=resolve_layout(old_rows)['canonical'];new_layout=ctx['capacity']['selection_layout']
    widgets=[]
    for cls,ids in old_layout.items():
        for n,physical in enumerate(ids):
            mapping=new_layout['physical_id_to_class_local'][str(physical)]
            new=egg(after,f'{cls}_Car{mapping["class_local_index"]+1}')
            if physical==25: # archived widget missing in the old loose overlay
                from master_rallye.addon_sdk.project import read_sma_member
                parent=ET.fromstring(read_sma_member(old/'Data.sma',scene));original=egg(parent,'T3_Car12')
            else:original=egg(before,f'{cls}_Car{n+1}')
            def signature(element,root=True):
                attrs=dict(element.attrib)
                if root:attrs.pop('Name',None)
                if element.tag=='Value' and attrs.get('Name') in ('X ID','XPos*'):attrs.pop('Value',None)
                return (element.tag,sorted(attrs.items()),[signature(child,False)for child in element])
            if signature(original)!=signature(new):raise ValueError('Stock widget art/unlock/state altered: '+str(physical))
            widgets.append(physical)
    changed=[]
    for path,pin in json.loads(protected.read_text()).items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=pin:changed.append(path)
    if changed:raise ValueError('Protected input changed: '+str(changed))
    demo=ROOT.parent/'corpora/demo-8.4.1/MRallye.exe';raw=demo.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a':raise ValueError('Original Demo841 changed')
    tables=localized_tables(raw)
    from audit_demo_identity import pc_records
    corpus=json.loads((ROOT/'research/vehicles/sdk/restorations/demo-identity-corpus.json').read_text())['sources']['pc841']
    original_rows=pc_records(demo,raw,corpus['registration'],Path('C:/msys64/ucrt64/bin/objdump.exe'))
    historical_record=next(r for r in original_rows if r['id']==15)
    if historical_record['family'].casefold()!='wildcat':raise ValueError('Demo841 ID15 ownership changed')
    result.update(status='PASS_OFFLINE_ROSTER_ORDER_PILOT',accepted_resources_unchanged=len(preserved),
        existing_widget_ownership_unchanged=widgets,protected_inputs_unchanged=len(json.loads(protected.read_text())),
        historical_name={str(c):localized_value(tables,c,15)for c in (52,53)},
        historical_registration=historical_record,
        trial_save_policy=json.loads((candidate/'validation.json').read_text()).get('trial_save_policy'),
        owner_gameplay='PENDING',save_lifecycle='NOT TESTED; disposable new championships only')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','baseline','protected','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Fresh evidence output required')
    result=validate(a.candidate,a.baseline,a.protected)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
