"""Bounded original PC/PS2 registration/localization/scene audit; no game writes."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.demo_identity import load_segments,cstring,localized_tables,localized_value,ps2_registration
from scanner.r5v_a_exe_registry import LINE,PUSH,LEA,CALL


def pc_records(path,raw,profile,objdump):
    start,stop,ctor,stride,count=profile;segments=load_segments(raw)
    assembly=subprocess.run([str(objdump),'-D','-Mintel',f'--start-address={start}',f'--stop-address={stop}',str(path)],check=True,capture_output=True,text=True).stdout
    rows=[];name=None;pointer=None;args=[];offset=None;colours={}
    for line in assembly.splitlines():
        m=LINE.match(line)
        if not m:continue
        va=int(m[1],16);text=m[2].strip();push=PUSH.match(text);lea=LEA.match(text);call=CALL.match(text)
        colour=re.fullmatch(r'mov\s+DWORD PTR \[esp\+0x(18|1c|20|24)\],0x([0-9a-f]+)',text)
        if colour:colours[int(colour[1],16)]=int(colour[2],16)
        if push:
            value=int(push[1],16)
            if value>=0x400000:pointer=value;name=cstring(raw,segments,value);args=[]
            elif pointer is not None:args.append(value)
        elif lea:offset=int(lea[1],16)
        elif call and int(call[1],16)==ctor:
            if pointer is None or offset is None or len(args)!=7 or (offset-4)%stride:raise ValueError('Unqualified registration arguments')
            row={'id':args[-1],'family':name,'class':args[-2],'stats':list(reversed(args[1:5])),'smallcarsheet':args[0],'record_index':(offset-4)//stride,'call_va':va}
            if stride==0x34 and set(colours)=={0x18,0x1c,0x20,0x24}:
                import struct,math
                bits=[colours[k]for k in sorted(colours)];rgba=list(struct.unpack('<4f',struct.pack('<4I',*bits)))
                if all(math.isfinite(v)and 0<=v<=1 for v in rgba):row.update(rgba=rgba,rgba_bits=[f'{b:08x}'for b in bits])
            rows.append(row);name=pointer=offset=None;args=[];colours={}
    if len(rows)!=count or sorted(r['record_index']for r in rows)!=list(range(count)):raise ValueError('Incomplete original registration table: '+str([r['record_index']for r in rows]))
    return rows


def scene_bindings(root):
    records=[];pins={};issues=[];paths=sorted((root/'DataScene').rglob('*.xml'))
    if len(paths)>4096:raise ValueError('Scene audit file budget')
    for p in paths:
        raw=p.read_bytes()
        if len(raw)>8*1024*1024:raise ValueError('Scene XML size budget')
        pins[p.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
        try:tree=ET.fromstring(raw)
        except ET.ParseError as exc:
            issues.append({'path':p.relative_to(root).as_posix(),'error':str(exc)});continue
        for egg in tree.iter():
            values={n.get('Name'):n.get('Value')for n in egg if n.tag=='Value'}
            if 'Car Name'in values and 'AI DriverID'in values:
                records.append({'path':p.relative_to(root).as_posix(),'tag':egg.tag,'family':values['Car Name'],'driver_id':values['AI DriverID'],'status':'PROVEN_SCENE_DEFAULT_NOT_CANONICAL_DRIVER'})
    return {'xml_pins':pins,'bindings':records,'unparsed_original_xml':issues}


def run(config,objdump):
    report={'schema':'demo-historical-identity/1','sources':{}}
    for label,source in config['sources'].items():
        path=Path(source['path']);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=source['sha256']:raise ValueError('Historical executable changed: '+label)
        localized=localized_tables(raw)
        records=ps2_registration(raw,**source['registration'])if label=='ps2'else pc_records(path,raw,source['registration'],objdump)
        for row in records:
            row['localized']={str(category):localized_value(localized,category,row['id'])for category in(52,53,57)}
            row['marker_status']='PROVEN'if 'rgba'in row else'UNKNOWN'
        scene=scene_bindings(Path(source['scene_root']))if 'scene_root'in source else None
        report['sources'][label]={'sha256':digest,'size':len(raw),'registration':records,'localized_records':localized,'scene_evidence':scene,
            'boundary':'Original table data only. PC Demo category57 is a separate 12-driver list, not a vehicle-indexed identity. PS2/retail IDs differ. Cross-build assignments require explicit correspondence.'}
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--objdump',type=Path,default=Path('C:/msys64/ucrt64/bin/objdump.exe'));a=p.parse_args()
    if a.output.exists():raise ValueError('Choose a fresh evidence output')
    config=json.loads(a.config.read_text());target=a.output.resolve()
    protected=[Path(v.get('scene_root',Path(v['path']).parent)).resolve()for v in config['sources'].values()]
    if not target.is_relative_to((ROOT/'.research-output').resolve())or any(target.is_relative_to(root)for root in protected):raise ValueError('Audit output must be private and outside original inputs')
    result=run(config,a.objdump);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print({k:len(v['registration'])for k,v in result['sources'].items()})
