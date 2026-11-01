"""V-DEF4.1 exact resource/physics/registration proof, not a game test."""
from pathlib import Path
import argparse,hashlib,json,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools'),str(ROOT/'.research-output/vehicles/v-def1/python-deps')]
from build_sdk_roster import derive
from validate_sdk_roster import validate
from validate_sdk_capacity_emulation import validate as emulate
from master_rallye.addon_sdk.demo_restoration import verify_retail_clone
from master_rallye.addon_sdk.physics_profile import MEMBERS
from master_rallye.addon_sdk.project import read_sma_member
from master_rallye.dx import parse_dx_bytes
from master_rallye.preview_scene import presentation_wheels


def sha(b):return hashlib.sha256(b).hexdigest()
def rows(raw):return {n.get('Name'):dict(n.attrib)for n in ET.fromstring(raw).iter('Value')}


def marker_replay(source,records):
    """Original record-vector copies; only native registry/Broker calls mocked."""
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESI as SI,UC_X86_REG_EBP as BP,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP
    import j2_frontend_reentry as j2
    _,sections=j2.addon_runtime._pe_sections(source);result=[]
    for row in records:
        for label,start,stop,slotreg in [('ordinary',0x44a681,0x44a6ba,BP),('competition',0x44a85a,0x44a893,SI)]:
            u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000);u.mem_map(0x2000000,0x20000);u.mem_map(0x3000000,0x20000)
            for s in sections:u.mem_write(0x400000+s['rva'],source[s['raw_offset']:s['raw_offset']+s['raw_size']])
            bits=bytes.fromhex(row['race_colour_rgba_f32le_hex']);u.mem_write(0x2000000+4+row['physical_id']*52+0x24,bits)
            u.reg_write(AX,row['physical_id']);u.reg_write(slotreg,2);u.reg_write(SP,0x3010000);published=[]
            def hook(uc,at,size,user):
                if at in(0x45a3c0,0x4ada50,0x4acdd0):
                    sp=uc.reg_read(SP);ret=int.from_bytes(uc.mem_read(sp,4),'little');cleanup=0
                    if at==0x4acdd0:
                        published.append({'slot':int.from_bytes(uc.mem_read(sp+4,4),'little'),'rgba_f32le_hex':bytes(uc.mem_read(sp+8,16)).hex()});cleanup=20
                    else:uc.reg_write(AX,0x2000000)
                    uc.reg_write(CX,0xbad1);uc.reg_write(DX,0xbad2);uc.reg_write(SP,sp+4+cleanup);uc.reg_write(IP,ret)
            u.hook_add(UC_HOOK_CODE,hook);u.emu_start(start,stop,count=400)
            if published!=[{'slot':2,'rgba_f32le_hex':bits.hex()}]or u.reg_read(SP)!=0x3010000:raise ValueError('Native marker publication mismatch')
            result.append({'physical_id':row['physical_id'],'path':label,**published[0]})
    return {'status':'PASS_ORIGINAL_X86_RECORD_VECTOR_PUBLICATION','cases':result,'boundary':'Registry/Broker calls mocked; existing HUD reader unchanged. Actual new per-vehicle marker rendering requires owner test.'}


def run(candidate,previous,sma):
    config=json.loads((candidate/'roster-config.json').read_text());ctx=derive(config);report=validate(config,candidate)
    old=previous/'runtime';new=candidate/'runtime';a=old/'resource-root';b=new/'resource-root'
    old_manifest=json.loads((old/'resource-manifest.json').read_text());new_manifest=json.loads((new/'resource-manifest.json').read_text())
    old_names={r['path']for r in old_manifest['resources']};new_names={r['path']for r in new_manifest['resources']}
    if old_names!=new_names:raise ValueError('Unexpected resource set change')
    diffs=[];unchanged=[]
    for name in sorted(old_names):
        before=(a/name).read_bytes();after=(b/name).read_bytes()
        if before!=after:diffs.append({'path':name,'before_sha256':sha(before),'after_sha256':sha(after)})
        else:unchanged.append(name)
    if {d['path']for d in diffs}!={'DataGame/vehicles.xml','DataGx/Frontend/RaceResults/smallcarsheet_035_000.dxt'}:raise ValueError('Unexpected resource differences')
    changes={}
    for name in MEMBERS:
        before=rows((a/name).read_bytes());after=rows((b/name).read_bytes());different=[{'name':k,'before':v,'after':after.get(k)}for k,v in before.items()if after.get(k)!=v]
        if any(not d['name'].startswith('Vehicles/DefTomcat/')for d in different)or before.keys()!=after.keys():raise ValueError('Unrelated physics/setup changed')
        changes[name]=different
    clone=verify_retail_clone({n:read_sma_member(sma,n)for n in MEMBERS},{n:(b/n).read_bytes()for n in MEMBERS},donor_family='Wildcat',runtime_family='DefTomcat')
    models=[parse_dx_bytes((b/'DataGx/Vehicles/DefTomcat'/name).read_bytes())for name in('car.dx','complete.dx','wheel.dx')];wheels=presentation_wheels(*models,diagnostics=True)
    wheel_vertices=models[2].vertices.positions;radius=max((p[1]*p[1]+p[2]*p[2])**.5 for p in wheel_vertices)
    selected=[r for r in ctx['rows']if r['physical_id']in(30,31,32)]
    source=Path(config.get('retail_exe',ROOT.parent/'MRallye.exe')).read_bytes()
    native=emulate(source,ctx['image'],ctx['capacity'],ctx['rows'],shared_payload=(0x10000000,(new/'native-extension.bin').read_bytes()))
    active=rows((b/MEMBERS[0]).read_bytes());dimensions={k.rsplit('/',1)[1]:v['Value']for k,v in active.items()if k.startswith('Vehicles/DefTomcat/Dimensions/')}
    return {'status':'PASS_OFFLINE_OWNER_GAMEPLAY_PENDING','roster':report,'resource_differences':diffs,'identical_resources':len(unchanged),'physics_differences':changes,'retail_clone':clone,'source_wheels':wheels,'visual_wheel_max_radius_m':radius,'retail_dimensions':dimensions,
            'native_emulation':native,'marker_publication':marker_replay(source,selected),'selection_layout':ctx['capacity']['selection_layout'],'owner_confirmation':'PENDING_NEW_CANDIDATE'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in('candidate','previous','retail-sma','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists()or not a.output.resolve().is_relative_to(ROOT/'.research-output'):raise ValueError('Fresh private evidence path required')
    report=run(a.candidate,a.previous,a.retail_sma);a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
