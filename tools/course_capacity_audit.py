"""Extract native race registrations and build an offline configurable catalog.

Uses existing Capstone/Unicorn installations. Never writes a game EXE, DLL,
original resource, or save; use an isolated output under this worktree.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from master_rallye.course_registry import validate_manifest,storage_layout,build_initializer,identity_contract


def pe_image(raw):
    at=struct.unpack_from('<I',raw,0x3c)[0]
    if raw[at:at+4]!=b'PE\0\0' or struct.unpack_from('<H',raw,at+4)[0]!=0x14c:raise ValueError('Need x86 PE')
    opt=at+24
    if struct.unpack_from('<H',raw,opt)[0]!=0x10b or struct.unpack_from('<I',raw,opt+28)[0]!=0x400000:raise ValueError('Incompatible PE32 layout')
    table=opt+struct.unpack_from('<H',raw,at+20)[0];sections=[]
    for i in range(struct.unpack_from('<H',raw,at+6)[0]):
        s=table+i*40;vsize,rva,size,offset=struct.unpack_from('<4I',raw,s+8)
        if offset+size>len(raw):raise ValueError('Truncated section')
        sections.append((rva,offset,size,vsize))
    def offset(va,size=1):
        for r,o,n,v in sections:
            if r<=va-0x400000 and va-0x400000+size<=r+n:return o+va-0x400000-r
        raise ValueError('Address not file backed: '+hex(va))
    return sections,offset


def extract(raw):
    from capstone import Cs,CS_ARCH_X86,CS_MODE_32
    from capstone.x86_const import X86_OP_IMM,X86_OP_MEM
    sections,offset=pe_image(raw);decoder=Cs(CS_ARCH_X86,CS_MODE_32);decoder.detail=True
    start=offset(0x4598d0);instructions=list(decoder.disasm(raw[start:offset(0x459fdc)],0x4598d0))
    rows=[];last_string=None;pushes=[];record_lea=None;sites=[]
    for i in instructions:
        if i.mnemonic=='push' and i.operands[0].type==X86_OP_IMM:pushes.append(i.operands[0].imm&0xffffffff)
        if i.mnemonic=='lea' and i.operands[-1].type==X86_OP_MEM:record_lea=i
        if i.mnemonic=='call' and i.operands[0].type==X86_OP_IMM:
            if i.operands[0].imm==0x4d11d0:
                last_string=pushes[-1];pushes=[]
            if i.operands[0].imm==0x45a330:
                if len(pushes)!=7 or last_string is None:raise ValueError('Unexpected race initializer shape')
                args=list(reversed(pushes));index=len(rows)
                if args[0]!=index or record_lea.operands[-1].mem.disp!=0x54c+44*index:raise ValueError('Race record address/identity differs')
                s=offset(last_string);end=raw.index(b'\0',s,s+256);scene=raw[s:end].decode('ascii')
                rows.append({'id':index,'scene':'DataScene/'+scene+'.xml','native_fields':args+[0xffffffff,0xffffffff]})
                sites.append({'address':hex(record_lea.address),'bytes':record_lea.bytes.hex(),'displacement':record_lea.operands[-1].mem.disp})
                pushes=[]
    if len(rows)!=39:raise ValueError('Original race registration inventory differs')
    return rows,sites


def catalog_from_resources(rows,data_root):
    index={p.relative_to(data_root).as_posix().lower():p for p in data_root.rglob('*') if p.is_file()}
    courses={};races=[];missing=[]
    for row in rows:
        scene=index.get(row['scene'].lower())
        if scene is None:raise ValueError('Missing scene: '+row['scene'])
        tree=ET.parse(scene).getroot()
        landscapes=[v.get('Value') for egg in tree.iter('Egg') if egg.get('Name','').lower()=='landscape' for v in egg.iter('Value') if v.get('Name')=='en3d Model Name']
        datasets=[v.get('Value') for v in tree.iter('Value') if v.get('Name')=='AI DataSet Name']
        if len(landscapes)!=1 or len(datasets)!=1:raise ValueError('Ambiguous scene resource binding: '+str(scene))
        model='DataGx/'+landscapes[0].replace('\\','/')+'.dx'
        dataset='DataScene/'+datasets[0].replace('\\','/')+'.sfl'
        folder=model.rsplit('/',1)[0];key='stock:'+folder.lower()
        courses[key]={'key':key,'folder':folder,'model':model}
        races.append({**row,'course':key,'icont':dataset})
        for resource in (model,dataset):
            if resource.lower() not in index:missing.append(resource)
    return {'schema':'mr-course-registry/1','vehicle_count':35,'courses':list(courses.values()),'races':races,'competitions':[]},missing


def cpu_probe(raw,catalog):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX
    sections,_=pe_image(raw);u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0,4096);u.mem_map(0x400000,0x400000)
    for r,o,n,v in sections:u.mem_write(0x400000+r,raw[o:o+n])
    blob,strings,records=build_initializer(catalog)
    for address,size in ((0x71000000,len(blob)),(0x2000000,catalog['layout']['allocation_size']+4096),(0x3000000,len(strings)),(0x1000000,65536)):
        u.mem_map(address,(size+4095)//4096*4096)
    u.mem_write(0x71000000,blob);u.mem_write(0x3000000,strings);sp=0x1008000
    u.mem_write(sp,struct.pack('<I',0x71000000+len(blob)));u.reg_write(UC_X86_REG_ESP,sp)
    copies=[];frees=[]
    def hook(uc,at,size,user):
        if at not in (0x4d1990,0x5b4c00):return
        stack=uc.reg_read(UC_X86_REG_ESP);ret,arg=struct.unpack('<2I',uc.mem_read(stack,8))
        if at==0x4d1990:uc.mem_write(uc.reg_read(UC_X86_REG_ECX),struct.pack('<I',arg));copies.append(arg)
        else:frees.append(arg)
        uc.reg_write(UC_X86_REG_ESP,stack+(8 if at==0x4d1990 else 4));uc.reg_write(UC_X86_REG_EIP,ret)
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x71000000,0x71000000+len(blob),count=5000000)
    for r in records:
        fields=struct.unpack('<11I',u.mem_read(r['address'],44))
        if fields[1:7]!=tuple(r['fields'][:5]+[r['fields'][6]]) or fields[7]!=r['string'] or fields[8:]!=tuple([r['fields'][5]]+r['fields'][7:]):raise ValueError('Actual native record field writes differ')
    if u.reg_read(UC_X86_REG_ESP)!=sp+4 or len(copies)!=len(records) or copies!=frees:raise ValueError('Initializer stack/string ownership call mismatch')
    return {'status':'PASS_NATIVE_RECORD_INITIALIZER','records':len(records),'original_function':'0x0045A330','string_assign_calls':len(copies),'temporary_release_calls':len(frees),'runtime_qualified':False,'boundary':'Original x86 field initializer executed; string assignment/free mocked; no native allocator, menu, save, game process or independent external courses qualified'}


def check_resources(catalog,data_root):
    index={p.relative_to(data_root).as_posix().lower():p for p in data_root.rglob('*') if p.is_file()}
    courses={c['key']:c for c in catalog['courses']};missing=[]
    for race in catalog['races']:
        model=courses[race['course']]['model']
        for path in (race['scene'],race['icont'],model,race['scene'].rsplit('.',1)[0]+'.hnt'):
            if path.lower() not in index:missing.append(path)
        if race['scene'].lower() in index:
            root=ET.parse(index[race['scene'].lower()]).getroot()
            models=['DataGx/'+v.get('Value').replace('\\','/')+'.dx' for e in root.iter('Egg') if e.get('Name','').lower()=='landscape' for v in e.iter('Value') if v.get('Name')=='en3d Model Name']
            if len(models)!=1 or models[0].lower()!=model.lower():raise ValueError('Scene/model catalog binding mismatch: '+race['scene'])
            datasets=['DataScene/'+v.get('Value').replace('\\','/')+'.sfl' for v in root.iter('Value') if v.get('Name')=='AI DataSet Name']
            if len(datasets)!=1 or datasets[0].lower()!=race['icont'].lower():raise ValueError('Scene/AI catalog binding mismatch: '+race['scene'])
    if missing:raise ValueError('Missing catalog resources: '+str(sorted(set(missing))))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--manifest',type=Path)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.research-output') or out.exists():raise ValueError('Use a fresh worktree-local research output')
    out.mkdir(parents=True);raw=a.exe.read_bytes();rows,sites=extract(raw);stock,missing=catalog_from_resources(rows,a.data_root)
    if missing:raise ValueError('Missing original dependencies: '+str(missing))
    doc=json.loads(a.manifest.read_text()) if a.manifest else copy.deepcopy(stock)
    if not a.manifest:
        for i,source in ((39,24),(40,9)):
            row=copy.deepcopy(doc['races'][source]);row['id']=i;row['native_fields'][0]=i
            row['purpose']='existing-scene addressing fixture, not a new independent course';doc['races'].append(row)
    catalog=validate_manifest(doc,rows)
    check_resources(catalog,a.data_root)
    def write(name,v):(out/name).write_text(json.dumps(v,indent=2)+'\n')
    write('stock-registrations.json',rows);write('stock-catalog.json',stock);write('registry-manifest.json',doc);write('compiled-catalog.json',catalog)
    write('native-initializer-probe.json',cpu_probe(raw,catalog))
    write('capacity-report.json',{'schema':'mr-course-capacity-audit/1','source_exe_sha256':hashlib.sha256(raw).hexdigest(),'original_races':39,'resource_folders':len(stock['courses']),'stock_layout':storage_layout(26,39),'accepted_vehicle_layout':storage_layout(35,39),'candidate_layout':catalog['layout'],'identity_contract':identity_contract(catalog),'initializer_sites':sites,'addressing_only_profiles':[storage_layout(35,n) for n in (127,128,254,255,256,257,513)],'runtime_installer_emitted':False,'global_limit':'unknown','unresolved_owners':['menu mode mapping','BestTime/Won key tables','championship stage ranges','native lifecycle widening','network qualification','shared Vehicle/Course registry installation']})
    print('COURSE_CAP1_OFFLINE_PASS',len(catalog['races']),'records;',len(stock['courses']),'folders; no runtime installation')


if __name__=='__main__':main()
