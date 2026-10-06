"""Exact retail six/seven/eight research scaffolding; no randomizer or UI changes."""
from __future__ import annotations
import argparse,json,math,struct
from pathlib import Path
import r_ai2_capacity as five
from r_ai1_mixed_class import (RETAIL_SHA256,RETAIL_SIZE,REPOSITORY,TEXT_SIZE_OFFSET,
    ORIGINAL_TEXT_SIZE,apply_ranges,ignored_output,sha256,stock_map,verify_capture)
from r_ai1_hardening import hardening_ranges,compose_ranges
from r_ai1_2_randomizer import Asm
from patch_vehicle_slot25 import parse_pe,va_to_file_offset

COMMON_BASE='8a17f2ddf59d81dd8f4f75e8c7601d61becc4c10'
TOTALS=(6,7,8)
ROSTER=(0,1,7,14,2,8,15,17)
CAVE=0x68E300
ROSTER_CAVE=0x68E400
CHOOSER_SITE=0x47B96E
PROFILE_SHA256={6:'c3280283f6f27f7a5744e9a42b2f1df244e55ac8d326f02a84808b4fba867de2',7:'484ac9da4e2fbd31660dd5e5ecbaddd6a342e71231c582ae365897ba49cacc09',8:'a2b188b23eab9bee87aa3c97c718a72b9d427967f435c53aed351c04377074d1'}

def require_total(total):
    if type(total)!=int or total not in TOTALS:raise ValueError('Only exact totals 6,7,8')

def profile(total):
    require_total(total);return f'retail-r-ai2-1-{total}-car-hardened'

def effective_opponents(total,**state):
    require_total(total)
    return total-1 if five.effective_opponents(**state)==4 else state['opponents']

def count_code(total):
    require_total(total)
    old=bytes.fromhex('c744241c04000000')
    code=five.shim()
    if code.count(old)!=1:raise ValueError('Unexpected closed five-car shim')
    return code.replace(old,bytes.fromhex('c744241c')+struct.pack('<I',total-1))

def roster_code(total):
    require_total(total);a=Asm(ROSTER_CAVE);a.emit('9c60')
    # PUSHFD/PUSHAD shifts the original five thiscall arguments by36 bytes.
    for offset,value in ((40,1),(44,total-1),(48,0),(52,0),(56,-1)):
        a.emit(bytes((0x83,0x7c,0x24,offset,value&255)));a.branch('0f85','stock')
    a.call(0x4AE700);a.emit('8bc8');a.call(CAVE)
    a.emit(bytes((0x83,0xf8,total-1)));a.branch('0f85','stock')
    a.call(0x4ADA50);a.emit('8bc8');a.call(0x4AC040)
    a.emit(bytes((0x83,0xf8,total)));a.branch('0f85','stock')
    for slot,id in enumerate(ROSTER[1:total],1):
        a.emit(bytes((0x6a,id,0x6a,slot)));a.call(0x4ADA50);a.emit('8bc8');a.call(0x4ACAF0)
        a.call(0x45A3C0);a.emit(b'\xff\xb0'+struct.pack('<I',id*0x34+0xC))
        a.emit(bytes((0x6a,slot)));a.call(0x4ADA50);a.emit('8bc8');a.call(0x4ACC10)
        a.emit(bytes((0x6a,slot-1,0x6a,slot)));a.call(0x4ADA50);a.emit('8bc8');a.call(0x4ACCD0)
    a.emit('619dc21400')
    a.label('stock');a.emit('619d');a.branch('e9',0x458090)
    return a.finish()[0]

def ranges(total):
    require_total(total)
    def call(site,target):return b'\xe8'+struct.pack('<i',target-site-5)
    rows=[]
    def row(va,old,new,purpose):rows.append(dict(va=va,offset=va-0x400000,original=old,replacement=new,purpose=purpose))
    for site in five.SITES:row(site,call(site,0x4AE150),call(site,CAVE),'Guarded visible Three -> effective research AI count')
    row(CAVE,bytes(len(count_code(total))),count_code(total),'Original getter and exact closed R-AI2 context guards; effective total-specific count')
    row(CHOOSER_SITE,call(CHOOSER_SITE,0x458090),call(CHOOSER_SITE,ROSTER_CAVE),'One-human Quick Race caller only: deterministic stock mixed roster avoids T1 pool exhaustion')
    code=roster_code(total)
    row(ROSTER_CAVE,bytes(len(code)),code,'Exact count/context/arguments; native CarID, registry CarClass and unique valid DriverID setters')
    end=ROSTER_CAVE+len(code)
    if end>=0x68F000:raise ValueError('Cave exceeds existing zero text padding')
    rows.append(dict(va=None,offset=TEXT_SIZE_OFFSET,original=struct.pack('<I',ORIGINAL_TEXT_SIZE),replacement=struct.pack('<I',end-0x401000),purpose='Declare bounded research text padding'))
    return compose_ranges(hardening_ranges(),rows)

def manifest(total,digest):
    return dict(phase='R-AI2.1',common_base=COMMON_BASE,profile=profile(total),source_sha256=RETAIL_SHA256,
        output_sha256=digest,size=RETAIL_SIZE,status='PREPARED_RUNTIME_UNTESTED',broker_dump_variant='native_hardened',
        num_cars=total,num_players=1,frontend_opponent_choice=3,effective_opponents=total-1,
        roster=[dict(slot=n,CarID=id,CarClass=0 if id<7 else 1 if id<14 else 2,DriverID=30 if n==0 else n-1) for n,id in enumerate(ROSTER[:total])],
        randomizer_dependency=False,ui_changes=False,physical_arrays_expanded=False,participant_loops_widened=False,
        guard=dict(mode=2,split_screen=False,ghost=0,player_id=0,track=10),
        ranges=[{**{k:v for k,v in r.items() if k not in ('original','replacement')},'length':len(r['original']),'original_hex':r['original'].hex(),'replacement_hex':r['replacement'].hex()} for r in ranges(total)])

def build(source,total):
    require_total(total)
    if len(source)!=RETAIL_SIZE or sha256(source)!=RETAIL_SHA256:raise ValueError('Require exact pristine retail hash and size')
    pe=parse_pe(source)
    for r in ranges(total):
        if r['va'] is not None and va_to_file_offset(pe,r['va'])!=r['offset']:raise ValueError('Target layout mismatch')
    binary=apply_ranges(source,ranges(total),RETAIL_SHA256);digest=sha256(binary)
    if digest!=PROFILE_SHA256[total]:raise ValueError('Pinned output mismatch')
    return binary,manifest(total,digest)

def verify(binary,total):
    require_total(total)
    if len(binary)!=RETAIL_SIZE or sha256(binary)!=PROFILE_SHA256[total]:raise ValueError('Unknown capacity candidate')
    restored=bytearray(binary)
    for r in ranges(total):
        start=r['offset'];end=start+len(r['replacement'])
        if binary[start:end]!=r['replacement']:raise ValueError('Replacement mismatch')
        restored[start:end]=r['original']
    rebuilt,result=build(bytes(restored),total)
    if rebuilt!=binary:raise ValueError('Inverse/reproduction mismatch')
    return result

def check_snapshot(snapshot,total,results=False):
    require_total(total);s=snapshot.get('source',{})
    label={6:'six',7:'seven',8:'eight'}[total]+('-results' if results else '-race')
    if snapshot.get('kind')!='master-rallye-broker-dump-snapshot' or snapshot.get('schema_version')!=1 or s.get('image_sha256')!=PROFILE_SHA256[total] or s.get('build_profile')!=profile(total) or s.get('broker_dump_variant')!='native_hardened' or s.get('label')!=label or s.get('freshness')!='post_baseline_complete_dump_proven':raise ValueError('Need fresh exact-profile lifecycle capture')
    entries=snapshot['entries']
    def get(path):
        rows=[r for r in entries if r['path']==path]
        if len(rows)!=1:raise ValueError('Missing/ambiguous '+path)
        return rows[0]['value']
    for path,value in {'Race/NumCars':total,'Race/NumPlayers':1,'Race/NumNetworkPlayers':0,'Race/Type':2,'Race/FinishingType':0,'Race/AttractMode':False,'Race/NetworkSyncActive':False,'Race/GhostPlayback':False,'Frontend/QuickRace/Track':10,'Frontend/QuickRace/Ghost':0}.items():
        actual=get(path)
        if type(actual)!=type(value) or actual!=value:raise ValueError('Wrong '+path)
    vehicles=stock_map();participants=[];paths={}
    canaries=json.loads((REPOSITORY/'research/r-ai1-1/vehicle-physics-canaries.json').read_text())['vehicles']
    for n,id in enumerate(ROSTER[:total]):
        p={key:get(f'Race/Car{n}/{key}') for key in ('CarID','CarClass','DriverID','PlayerType','CarType','WheelType')}
        expected=dict(CarID=id,CarClass=vehicles[id]['class'],DriverID=30 if n==0 else n-1,PlayerType=1 if n==0 else 2)
        for key,value in expected.items():
            if type(p[key])!=int or p[key]!=value:raise ValueError(f'Car{n} {key} mismatch')
        for key in ('CarType','WheelType'):
            if not isinstance(p[key],str) or p[key].casefold()!=vehicles[id]['family'].casefold():raise ValueError('Wrong family')
        for prefix in ('Vehicles','Physics','Controller','Network'):
            count=sum(r['path'].startswith(f'{prefix}/Car{n}/') for r in entries);paths[f'{prefix}/Car{n}']=count
            if prefix in ('Vehicles','Physics','Network') and not count:raise ValueError('Missing participant subsystem state')
        for suffix,value in next(r['values'] for r in canaries if r['id']==id).items():
            actual=get(f'Vehicles/Car{n}/'+suffix)
            if type(actual) not in (int,float) or not math.isclose(actual,value,rel_tol=0,abs_tol=.0001):raise ValueError('Named physical identity mismatch')
        participants.append(p)
    report=dict(status='BROKER_RESULTS_MATCH_ONLY' if results else 'BROKER_STATE_MATCH_ONLY',runtime_full_pass=False,expected_cars=total,participants=participants,subsystem_paths_not_actor_proof=paths)
    if results:
        lists={}
        for suffix in ('PositionList','NameList','TimeList'):
            path='Frontend/RaceResults/'+suffix;v=get(path)
            if not isinstance(v,list) or len(v)!=total or any(not isinstance(x,str) for x in v) or next(r for r in entries if r['path']==path)['type']!='StringList':raise ValueError('Wrong result list count')
            lists[suffix]=v
        if lists['PositionList']!=[f'"{n}"' for n in range(1,total+1)]:raise ValueError('Wrong result ranking')
        registry=json.loads((REPOSITORY/'research/r5v_a/final-vehicle-registry.json').read_text())
        image={r['index']:r['raw_numeric_arguments_push_order'][0] for r in registry['executable_registry']['records']}
        icons=[get(f'Frontend/RaceResults/Car{n}') for n in range(8)]
        if any(type(v)!=int for v in icons) or sorted(icons[:total])!=sorted(image[id] for id in ROSTER[:total]) or icons[total:]!=[12]*(8-total):raise ValueError('Wrong result images/blank padding')
        competitor={f'RaceData/Competitor{n}':{r['path']:r['value'] for r in entries if r['path'].startswith(f'RaceData/Competitor{n}/')} for n in range(total)}
        positions=[]
        for n,record in enumerate(competitor.values()):
            pos=record.get(f'RaceData/Competitor{n}/RacePosition');time=record.get(f'RaceData/Competitor{n}/RaceTime')
            if type(pos)!=int or not 1<=pos<=total or type(time) not in (int,float) or not math.isfinite(time) or time<0:raise ValueError('Missing/invalid competitor position/time')
            positions.append(pos)
        if sorted(positions)!=list(range(1,total+1)):raise ValueError('Aliased competitor ranking')
        report.update(result_lists=lists,result_image_ids=icons,race_data_competitors=competitor)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for command in ('build','verify','check-race','check-results'):
        q=sub.add_parser(command);q.add_argument('candidate',type=Path);q.add_argument('--expected-cars',type=int,choices=TOTALS,required=True)
        if command=='build':q.add_argument('--output',type=Path,required=True)
        if command.startswith('check-'):q.add_argument('snapshot',type=Path);q.add_argument('--observatory',type=Path,required=True)
    a=p.parse_args()
    if a.command=='build':
        b,report=build(a.candidate.read_bytes(),a.expected_cars);out=ignored_output(a.output);out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists():raise ValueError('Refuse candidate overwrite')
        out.write_bytes(b);out.with_suffix('.manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    else:
        report=verify(a.candidate.read_bytes(),a.expected_cars)
        if a.command.startswith('check-'):
            from r_ai1_observe import load_profile
            adapter=load_profile(a.observatory,a.candidate);snapshot=json.loads(a.snapshot.read_text(encoding='utf-8'));name=snapshot['source']['raw_sidecar']
            if Path(name).name!=name:raise ValueError('Invalid raw sidecar name')
            verify_capture(snapshot,a.snapshot.with_name(name).read_bytes(),adapter.core.parse_dump_bytes)
            report=check_snapshot(snapshot,a.expected_cars,a.command=='check-results')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
