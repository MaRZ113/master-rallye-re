"""Verify historical source hashes, accepted scene claims and sealed native inputs.

Mutable owner runtime saves/options/logs are not promoted into sealed resources.
"""
from pathlib import Path
import argparse,hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye import universal_vehicle_scene as u


def digest(path):
    u.unlinked(path);h=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def run(manifest,scenes,runtimes,index_hashes,output):
    if len(runtimes)!=len(index_hashes):raise ValueError('Each sealed runtime needs its known index SHA256')
    entries=u.load_json(u.read_bounded(manifest,16*1024*1024));protected=[manifest,*scenes,*runtimes]
    for root in scenes:
        for item in sorted(root.rglob('manifest.json')):
            doc=u.load_json(u.read_bounded(item,2*1024*1024))
            if doc.get('schema')!='universal-vehicle-scene-manifest/1':continue
            for name,row in doc['files'].items():
                entries[str((item.parent/u.relative_name(name)).absolute())]={'sha256':row['sha256'],'bytes':row['bytes']}
    runtime_files=0
    for runtime,expected in zip(runtimes,index_hashes):
        index=runtime/'resource-index.tsv'
        if digest(index)!=expected:raise ValueError('Sealed runtime index identity changed')
        for line in index.read_text().splitlines():
            sha,size,name=line.split('\t');u._hash(sha);u._size(int(size),1024*1024*1024)
            path=runtime/'resource-root'/u.relative_name(name)
            entries[str(path.absolute())]={'sha256':sha,'bytes':int(size)};runtime_files+=1
    output=u.output_directory(output,[*protected,*map(Path,entries)])
    changed=[];missing=[];total=0
    for i,(name,expected)in enumerate(entries.items()):
        path=Path(name)
        if not path.is_file():missing.append(name);continue
        size=path.stat().st_size;total+=size
        if size!=expected['bytes']or digest(path)!=expected['sha256']:changed.append(name)
        if (i+1)%2000==0:print('Hashed',i+1,'protected files',flush=True)
    result={'schema':'source-garage-preservation/1','status':'PASS'if not changed and not missing else'FAIL',
        'files':len(entries),'bytes_hashed':total,'sealed_runtime_resources':runtime_files,'changed':changed,'missing':missing,
        'mutable_owner_runtime_state':'Outside sealed index; owner gameplay saves/options are not reset or overwritten'}
    output.mkdir(parents=True);(output/'validation.json').write_bytes(u.canonical(result));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--legacy-manifest',type=Path,required=True)
    p.add_argument('--scene-root',type=Path,action='append',default=[]);p.add_argument('--runtime',type=Path,action='append',default=[])
    p.add_argument('--runtime-index-sha256',action='append',default=[]);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.legacy_manifest,a.scene_root,a.runtime,a.runtime_index_sha256,a.output);print(r)
    if r['status']!='PASS':sys.exit(1)
