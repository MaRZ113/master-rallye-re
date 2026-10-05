"""Exact-build Challenge preview bridge and evidence-limited pair oracle."""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path
import r_ai1_2_randomizer as base
from r_ai1_hardening import compose_ranges
from r_ai1_mixed_class import apply_ranges, sha256, RETAIL_SHA256, RETAIL_SIZE, TEXT_SIZE_OFFSET, ORIGINAL_TEXT_SIZE, ignored_output, REPOSITORY, stock_class_local
from patch_vehicle_slot25 import parse_pe, va_to_file_offset

PREVIEW=0x68EF00
RESET_ENTRY=0x68EF60
RESET_BACK=0x68EF90
AUTHORED=((6,2),(4,3),(2,6),(5,9),(9,10),(13,7),(12,17),(19,15),(13,14),(21,18),(18,23))
PROFILE_SHA256={False: '185900aa1cb0fd1ce4dbac4bfa48196fb0b3753b7dddcbb5418a965e812d9980', True: 'e5257d991e434b63466ac08373d63e9e320af9bc11825a16dc0f01ee41d94343'}

def preview_ranges():
    rows=[]
    def row(va,old,new,purpose):
        rows.append(dict(va=va,offset=va-0x400000,original=old,replacement=new,purpose=purpose))
    a=base.Asm(PREVIEW)
    a.emit("8bbc38740500009c60") # stock opponent EDI load always runs
    a.emit("57538b461083c064506a01") # authored opponent, human EBX, event+100, hint1
    a.call(base.LOADER)
    a.emit("83f818");a.branch("0f87","stock")
    a.emit("89442400") # saved EDI is the ONLY changed native register
    a.label("stock");a.emit("619d");a.branch("e9",0x45EC3C)
    code=a.finish()[0]
    assert len(code)<=RESET_ENTRY-PREVIEW
    row(0x45EC35,bytes.fromhex("8bbc3874050000"),b'\xe9'+struct.pack('<i',PREVIEW-0x45EC35-5)+b'\x90\x90',"One opponent ID feeds native localized name and 3D preview model")
    row(PREVIEW,bytes(len(code)),code,"Generate once or reuse cached Challenge identity; no native registry mutation")
    for site,cave,target,purpose in ((0x45E511,RESET_ENTRY,0x4E3DD0,"Challenge screen initialization invalidates transient selection"),
                                     (0x45EA9A,RESET_BACK,0x45D910,"Challenge Back invalidates; original frontend transition and arguments preserved")):
        a=base.Asm(cave);a.emit("9c606a006a006a9c6a01");a.call(base.LOADER)
        a.emit("619d");a.branch("e9",target);code=a.finish()[0]
        assert len(code)<=0x30
        row(site,b'\xe8'+struct.pack('<i',target-site-5),b'\xe8'+struct.pack('<i',cave-site-5),purpose)
        row(cave,bytes(len(code)),code,purpose+" / bounded bridge")
    end=max(r['va']+len(r['replacement']) for r in rows)
    assert end<0x68F000 # never enter .rdata/IAT
    rows.append(dict(va=None,offset=TEXT_SIZE_OFFSET,original=struct.pack('<I',ORIGINAL_TEXT_SIZE),replacement=struct.pack('<I',end-0x401000),purpose="Declare bounded preview bridge in existing .text padding"))
    return rows

def ranges(five=False):return compose_ranges(base.ranges(five),preview_ranges())

def build(source,five=False):
    if len(source)!=RETAIL_SIZE or sha256(source)!=RETAIL_SHA256:raise ValueError('Require exact pristine retail hash/size')
    pe=parse_pe(source);patch=ranges(five)
    for r in patch:
        if r['va'] is not None and va_to_file_offset(pe,r['va'])!=r['offset']:raise ValueError('Unexpected target layout')
    output=apply_ranges(source,patch,RETAIL_SHA256);digest=sha256(output)
    if digest!=PROFILE_SHA256[five]:raise ValueError('Pinned preview output mismatch')
    return output,dict(phase='R-AI1.2a',profile='retail-r-ai1-2a-'+('five' if five else 'four')+'-hardened',status='PREPARED_RUNTIME_UNTESTED',source_sha256=RETAIL_SHA256,output_sha256=digest,size=len(output),randomizer_changes_count=False,capacity_composed=five,max_supported_total=5,policy_version=1,broker_dump_variant='native_hardened',ranges=[{**{k:v for k,v in r.items() if k not in ('original','replacement')},'length':len(r['original']),'original_hex':r['original'].hex(),'replacement_hex':r['replacement'].hex()} for r in patch])

def verify(candidate,five=False):
    if len(candidate)!=RETAIL_SIZE or sha256(candidate)!=PROFILE_SHA256[five]:raise ValueError('Unknown preview candidate')
    restored=bytearray(candidate)
    for r in ranges(five):
        start=r['offset'];end=start+len(r['original'])
        if candidate[start:end]!=r['replacement']:raise ValueError('Replacement mismatch')
        restored[start:end]=r['original']
    output,report=build(bytes(restored),five)
    if output!=candidate:raise ValueError('Inverse/reproduction mismatch')
    return report

def verify_module(binary,manifest):
    pin=json.loads((REPOSITORY/'research/r-ai1-2a/build-summary.json').read_text())
    if sha256(binary)!=pin['module']['sha256'] or len(binary)!=pin['module']['size']:raise ValueError('Unknown preview module')
    if manifest['module_sha256']!=pin['module']['sha256'] or manifest['module_size']!=pin['module']['size']:raise ValueError('Module manifest mismatch')
    if manifest['source_hashes']!=pin['module']['source_hashes']:raise ValueError('Source pins mismatch')
    for name,digest in manifest['source_hashes'].items():
        if sha256((REPOSITORY/name).read_bytes())!=digest:raise ValueError('Current source differs')
    if len(manifest['supported_profiles'])!=2:raise ValueError('Require both exact supported profiles')
    for five,p in zip((False,True),manifest['supported_profiles']):
        if p['output_sha256']!=PROFILE_SHA256[five] or p['profile']!='retail-r-ai1-2a-'+('five' if five else 'four')+'-hardened':raise ValueError('Module supported profile mismatch')
    return dict(module_sha256=sha256(binary),module_size=len(binary),implementation_version=1)

def check_pair(preview,race,log,config_data,generation=None):
    """Caller first verifies candidate/module and both JSON/raw integrity pairs."""
    def values(snapshot):
        result={}
        for e in snapshot['entries']:
            if e['path'] in result and result[e['path']]!=e.get('value'):raise ValueError('Conflicting native path values')
            result[e['path']]=e.get('value')
        return result
    pv=values(preview);rv=values(race)
    race_id=rv.get('Race/RaceID')
    if type(race_id)!=int:raise ValueError('Missing exact RaceID')
    event=race_id-25
    id=pv.get('Frontend/Challenge/OpponentCar')
    if type(event)!=int or not 0<=event<=10 or type(id)!=int:raise ValueError('Missing exact frontend identity')
    cls=stock_class_local(id)[0]
    human=pv.get('Frontend/Challenge/PlayerCar')
    if type(human)!=int or human!=rv.get('Race/Car0/CarID'):raise ValueError('Human preview/race mismatch')
    policy_hint=base.config(config_data)['Challenge']
    if human!=AUTHORED[event][0] or (policy_hint=='Stock' and id!=AUTHORED[event][1]):raise ValueError('Authored Challenge context mismatch')
    if rv.get('Race/Car0/PlayerType')!=1 or rv.get('Race/Car0/DriverID')!=30 or rv.get('Race/Car0/CarClass')!=stock_class_local(human)[0] or rv.get('Race/NumNetworkPlayers')!=0:raise ValueError('Invalid one-human offline roster')
    if type(rv.get('Race/Car1/DriverID'))!=int or not 0<=rv['Race/Car1/DriverID']<=9:raise ValueError('Invalid native driver')
    if not isinstance(pv.get('Frontend/Challenge/Car2Text'),str) or not pv['Frontend/Challenge/Car2Text']:raise ValueError('Missing preview name source state')
    if rv.get('Race/RaceID')!=event+25 or rv.get('Race/Car1/CarID')!=id or rv.get('Race/Car1/CarClass')!=cls:raise ValueError('Preview/race identity mismatch')
    if rv.get('Race/NumCars')!=2 or rv.get('Race/NumPlayers')!=1 or rv.get('Race/Car1/PlayerType')!=2 or rv.get('Race/Type')!=7:raise ValueError('Wrong Challenge context')
    if rv.get('Race/AttractMode') is not False or rv.get('Race/PlaybackReplay') is not False:raise ValueError('Need active ordinary Challenge')
    if len(log)>131072:raise ValueError('Log cap exceeded')
    digest=sha256(config_data);policy=policy_hint
    process=preview['source'].get('process_id')
    if type(process)!=int or process!=race['source'].get('process_id'):raise ValueError('Pair must share one process')
    lines=log.decode('ascii').splitlines();begins=[];uses=[]
    for n,line in enumerate(lines):
        parts=line.split()
        if parts and parts[0]=='PreviewV1':
            if len(parts)!=9 or parts[1] not in ('Begin','Use'):raise ValueError('Malformed preview diagnostic')
            try:serial,e,chosen,c,pid=int(parts[2]),int(parts[3]),int(parts[5]),int(parts[6]),int(parts[8])
            except ValueError:raise ValueError('Malformed preview identity')
            row=(n,serial,e,parts[4],chosen,c,parts[7],pid)
            (begins if parts[1]=='Begin' else uses).append(row)
    matches=[r for r in begins if r[2:]==(event,policy,id,cls,digest,process) and (generation is None or r[1]==generation)]
    if len(matches)!=1:raise ValueError('Ambiguous/missing generation; preserve full log or select --generation')
    begin=matches[0];consumers=[u for u in uses if u[1:]==begin[1:] and u[0]>begin[0]]
    if not consumers:raise ValueError('No same-generation Start consumption')
    use=consumers[0]
    if any(b[0]>begin[0] and b[0]<use[0] for b in begins):raise ValueError('Roster invalidated before Start')
    previous=max((b[0] for b in begins if b[0]<begin[0]),default=-1)
    groups=[line.split() for line in lines[previous+1:use[0]] if line.startswith('Challenge ')]
    if len(groups)!=1 or groups[0]!=['Challenge',policy,'1','1','-' if policy=='Stock' else str(cls),digest]:raise ValueError('Need exactly one generation group; redraw/Start must not reroll')
    return dict(status='CHALLENGE_PREVIEW_STATE_MATCH_ONLY',runtime_full_pass=False,event=event,event_preview_source='PreviewV1 Begin diagnostic, not a native Broker event publication',frontend_selection_value=pv.get('Frontend/Challenge/Challenge'),race_id=event+25,CarID=id,CarClass=cls,DriverID=rv.get('Race/Car1/DriverID'),driver_preview_exposed=False,policy=policy,config_sha256=digest,generation=begin[1],generation_groups=1,process_id=process,preview_text=pv['Frontend/Challenge/Car2Text'],visible_model_or_text_equality_proven=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    for command in ('build','verify'):
        p=sub.add_parser(command);p.add_argument('input',type=Path);p.add_argument('--five',action='store_true')
        if command=='build':p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('verify-module');p.add_argument('module',type=Path);p.add_argument('manifest',type=Path)
    p=sub.add_parser('check-challenge-pair')
    p.add_argument('preview',type=Path);p.add_argument('race',type=Path)
    for field in ('preview-raw','race-raw','candidate','module','module-manifest','observatory','config','log'):
        p.add_argument('--'+field,required=True,type=Path)
    p.add_argument('--generation',type=int);p.add_argument('--five',action='store_true')
    args=parser.parse_args()
    if args.command=='build':
        output,report=build(args.input.read_bytes(),args.five);dest=ignored_output(args.output);dest.mkdir(parents=True,exist_ok=True)
        (dest/'MRallye.exe').write_bytes(output);(dest/'patch-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    elif args.command=='verify':report=verify(args.input.read_bytes(),args.five)
    elif args.command=='verify-module':report=verify_module(args.module.read_bytes(),json.loads(args.manifest.read_text()))
    else:
        manifest=verify(args.candidate.read_bytes(),args.five)
        verify_module(args.module.read_bytes(),json.loads(args.module_manifest.read_text()))
        from r_ai1_observe import load_profile
        from r_ai1_mixed_class import verify_capture
        observe=load_profile(args.observatory,args.candidate)
        captures=[]
        for snapshot,raw in ((args.preview,args.preview_raw),(args.race,args.race_raw)):
            d=json.loads(snapshot.read_text());verify_capture(d,raw.read_bytes(),observe.core.parse_dump_bytes)
            s=d['source']
            if s.get('image_sha256')!=manifest['output_sha256'] or s.get('build_profile')!=manifest['profile'] or s.get('freshness')!='post_baseline_complete_dump_proven':raise ValueError('Capture build/freshness mismatch')
            captures.append(d)
        report=check_pair(*captures,args.log.read_bytes(),args.config.read_bytes(),args.generation)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
