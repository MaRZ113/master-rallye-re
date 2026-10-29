"""Read-only Dakar2 platform audit and bounded Xbox neutral recovery."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as uvs
from master_rallye.source_adapters.dakar2_disc import FileReader,RVZReader,xdvdfs,gamecube_fst
from master_rallye.source_adapters.dakar2_formats import RBB,sbb_entries,digest

def file_hash(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
    return h.hexdigest()

def inventory(reader,rows):
    result=[]
    for row in rows:
        h=hashlib.sha256();off=row['offset'];size=row['bytes']
        for i in range(0,size,8*1024*1024):h.update(reader.read(off+i,min(8*1024*1024,size-i)))
        result.append({**row,'sha256':h.hexdigest(),'signature':reader.read(off,min(size,32)).hex()})
    return result

def audit(xbox,gamecube,ps2,output):
    inputs=[Path(p).absolute()for p in(xbox,gamecube,ps2)];output=uvs.output_directory(Path(output).absolute(),[p if p.is_dir()else p.parent for p in inputs])
    if output.exists():raise ValueError('Fresh audit output required')
    # Validation precedes writes; originals are always opened read-only.
    for p in inputs:uvs.unlinked(p)
    xr=FileReader(inputs[0]);xt=xdvdfs(xr,0x18300000);gr=RVZReader(inputs[1]);gt=gamecube_fst(gr)
    output.mkdir(parents=True);report={'schema':'dakar2-platform-corpus/1','platforms':{},'gameplay':'NOT TESTED','master_rallye_integration':'OUT OF SCOPE'}
    for name,path,reader,tree,endian in [('Xbox',inputs[0],xr,xt,'<'),('GameCube',inputs[1],gr,gt['files'],'>')]:
        rows=inventory(reader,tree);platform={'source':str(path),'bytes':path.stat().st_size,'sha256':file_hash(path),'files':rows,'file_count':len(rows)}
        if name=='GameCube':
            platform['disc_header']={k:v for k,v in gt.items()if k!='files'}
            header=reader.read(gt['dol_offset'],256);offsets=struct.unpack_from('>18I',header);addresses=struct.unpack_from('>18I',header,72);sizes=struct.unpack_from('>18I',header,144)
            length=max(o+n for o,n in zip(offsets,sizes)if n)
            if length>32*1024*1024:raise ValueError('DOL executable budget')
            dol=reader.read(gt['dol_offset'],length)
            platform['dol']={'bytes':length,'sha256':digest(dol),'entry_va':struct.unpack_from('>I',header,224)[0],
                'sections':[{'file_offset':o,'va':a,'bytes':n}for o,a,n in zip(offsets,addresses,sizes)if n]}
        else:platform['partition_offset']=0x18300000
        folder=output/name;folder.mkdir();selected={}
        if name=='GameCube':(folder/'main.dol').write_bytes(dol)
        for row in rows:
            if row['path'].lower().endswith(('all.vsr/rbb/xbox/all.rbb','all.vsr/rbb/xbox/all.sbb','all.vsr/rbb/gamecube/all.rbb','all.vsr/rbb/gamecube/all.sbb','default.xbe')):
                data=reader.read(row['offset'],row['bytes']);(folder/Path(row['path']).name).write_bytes(data);selected[Path(row['path']).name.upper()]=data
        rbb=RBB(selected['ALL.RBB'],endian);platform['container_resources']=rbb.resources
        platform['vehicle_stream_members']=sbb_entries(selected['ALL.SBB'],endian)
        if name=='Xbox':
            b=selected['DEFAULT.XBE'];base=struct.unpack_from('<I',b,0x104)[0];cert=struct.unpack_from('<I',b,0x118)[0]-base
            platform['xbe']={'magic':b[:4].decode(),'image_base':base,'entry_va':struct.unpack_from('<I',b,0x128)[0]^0xa8fc57ab,
                'title_id':struct.unpack_from('<I',b,cert+8)[0],'title':b[cert+12:cert+92].decode('utf-16le').rstrip('\0'),
                'region_mask':struct.unpack_from('<I',b,cert+0xa0)[0],'version':struct.unpack_from('<I',b,cert+0xac)[0]}
            count,address=struct.unpack_from('<II',b,0x160)
            if count>64 or address<base or address-base+count*16>len(b):raise ValueError('XBE library table')
            platform['xbe']['libraries']=[{'name':b[address-base+i*16:address-base+i*16+8].rstrip(b'\0').decode('ascii'),
                'version':list(struct.unpack_from('<4H',b,address-base+i*16+8))}for i in range(count)]
        report['platforms'][name]=platform
        print(name,len(rows),'files',flush=True)
    rows=[]
    for p in sorted(inputs[2].rglob('*')):
        if p.is_file():
            uvs.unlinked(p)
            with p.open('rb')as f:signature=f.read(32).hex()
            rows.append({'path':p.relative_to(inputs[2]).as_posix(),'bytes':p.stat().st_size,'sha256':file_hash(p),'signature':signature})
    folder=output/'PS2';folder.mkdir();main=next(inputs[2].glob('SLES*'));elf=uvs.read_bounded(main,16*1024*1024);(folder/main.name).write_bytes(elf)
    config=(inputs[2]/'SYSTEM.CNF').read_text();rbb=RBB((inputs[2]/'RES/ALL.VSR/RBB/PS2/ALL.RBB').read_bytes())
    report['platforms']['PS2']={'source':str(inputs[2]),'media':'owner-local extraction; original ISO unavailable','file_count':len(rows),'files':rows,
        'system_cnf':config,'elf':{'magic':elf[:4].hex(),'machine':struct.unpack_from('<H',elf,18)[0],'entry':struct.unpack_from('<I',elf,24)[0]},
        'container_resources':rbb.resources,'vehicle_stream_members':sbb_entries((inputs[2]/'RES/ALL.VSR/RBB/PS2/ALL.SBB').read_bytes())}
    (output/'corpus-manifest.json').write_bytes(uvs.canonical(report));return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    a=commands.add_parser('audit')
    for name in('xbox','gamecube','ps2','output'):a.add_argument('--'+name,type=Path,required=True)
    a=commands.add_parser('recover');a.add_argument('--xbox',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    a.add_argument('--vehicle',choices=['PAJERO','NISSAN','HINO'],default='PAJERO');a.add_argument('--viewer',type=Path)
    a.add_argument('--diagnostic-two-sided',action='store_true',help='Additional no-cull inspection; never source renderer qualification')
    args=parser.parse_args()
    if args.command=='audit':
        result=audit(args.xbox,args.gamecube,args.ps2,args.output);print(json.dumps({k:v['file_count']for k,v in result['platforms'].items()}))
    else:
        from master_rallye.source_adapters.dakar2 import create_scene
        result=create_scene(args.xbox,args.output,args.vehicle)
        if args.viewer:
            from master_rallye.source_scene_preview import stage_source_scene,capture_views
            scene=uvs.load_scene(args.output/'scene.json');stage_source_scene(scene,args.output/'preview.mrpv',scene_root=args.output)
            result['captures']=capture_views(args.viewer.absolute(),(args.output/'preview.mrpv').absolute(),args.output/'views',cull='cw',
                provenance='Original source rest assembly; CW inspection, source culling unresolved')
            if args.diagnostic_two_sided:
                result['diagnostic_captures']=capture_views(args.viewer.absolute(),(args.output/'preview.mrpv').absolute(),args.output/'two-sided-diagnostic',cull='none',
                    provenance='Two-sided DIAGNOSTIC ONLY; mixed facing unresolved, no source renderer fidelity claim')
        print(json.dumps(result,indent=2))

if __name__=='__main__':main()
