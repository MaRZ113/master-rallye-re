"""Batch Course SDK lighting packages and offline material reports (never gameplay proof)."""
from pathlib import Path
import argparse,collections,dataclasses,hashlib,html,importlib.util,json,sys,struct,re,xml.etree.ElementTree as ET

for root in Path(__file__).resolve().parents:
    if (root/'src/master_rallye').is_dir():
        sys.path.insert(0,str(root/'src'));break
from master_rallye.course_lighting import export_lighting_metadata,decode_metadata,encode_metadata,course_model_paths
from master_rallye.dxt import parse_dxt,encode_png,PNG_ROWS_PRESERVE_STORED

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def discover(sources):
    found={}
    for root in sources:
        if not root.is_dir():raise ValueError(f'source missing: {root}')
        for folder in sorted(root.iterdir()):
            if folder.is_dir() and course_model_paths(folder):found.setdefault(folder.name.casefold(),folder.name)
    return sorted(found.values(),key=str.casefold)

def thumbnail(texture):
    scale=min(1,96/max(texture.width,texture.height));w=max(1,round(texture.width*scale));h=max(1,round(texture.height*scale))
    bgra=b''.join(texture.bgra[(at:=(min(texture.height-1,int(y/scale))*texture.width+min(texture.width-1,int(x/scale)))*4):at+4] for y in range(h) for x in range(w))
    preview=bytearray(bgra);preview[3::4]=b'\xff'*(len(preview)//4)
    return encode_png(dataclasses.replace(texture,width=w,height=h,bgra=bytes(preview)),PNG_ROWS_PRESERVE_STORED)

def offline_verdict(material):
    if material['category'] and not material['flags']&16:return 'Eligible (runtime admission required)'
    label=material['material'].lower()
    protected=('water','glass','window','glow','lamp','shadow','decal','wheel','tyre','tire','tred','reflection','chrome','perspex')
    if any(x in label for x in protected):return 'Excluded'
    if any(c[1]!='Null' or c[2] not in ('Null','noise-tga') for c in material['bindings']):return 'Unsupported'
    return 'Unclassified'

def scene_references(path,available,models=None):
    if path.stat().st_size>8*1024*1024:raise ValueError('scene XML size limit')
    tree=ET.parse(path);refs=[]
    identity=[1.,0,0,0,0,1.,0,0,0,0,1.,0,0,0,0,1.]
    for egg in tree.iter('Egg'):
        values={v.get('Name'):v for v in egg.findall('Value')}
        model=values.get('en3d Model Name')
        if model is None:continue
        text=model.get('Value','').replace('\\','/');parts=text.split('/')
        if len(parts)!=3 or parts[0].casefold()!='course':continue
        folder=available.get(parts[1].casefold())
        if not folder:raise ValueError('course folder reference unavailable: '+text)
        if not re.fullmatch(r'[A-Za-z0-9_ -]+(?:\.dx)?',parts[2],re.I):raise ValueError('invalid model reference: '+text)
        if models is not None and parts[2].casefold().removesuffix('.dx') not in models.get(folder,set()):raise ValueError('referenced course model not in validated sources: '+text)
        matrix=values.get('en3d Matrix');numbers=[]
        if matrix is not None:
            numbers=[float(v) for n in range(4) for v in matrix.get('Row'+str(n),'').split()]
        refs.append(dict(folder=folder,model=text,identity_matrix=numbers==identity))
    return refs

def export_scene_packages(output,scene_roots,runtime_name="runtime-courses"):
    """Bind certified RaceTest scene IDs to source folders through source XML.

    Each resulting LSM/LNH still contains ONLY that scene's safe ID. No native
    alias or per-object table is compiled into the Proxy.
    """
    asset_root=output/'courses';runtime=output/runtime_name;runtime.mkdir(exist_ok=False)
    available={p.name.casefold():p.name for p in asset_root.iterdir() if p.is_dir() and (p/'package.json').exists()}
    models={folder:{Path(s['source'].replace('\\','/')).stem.casefold() for s in json.loads((asset_root/folder/'provenance.json').read_text())['sources']} for folder in available.values()}
    bindings={};errors=[]
    if not any(root.is_dir() and any(root.glob('*.xml')) for root in scene_roots):
        for folder in available.values():bindings[folder.casefold()]=dict(scene=folder,folders=[folder],normal_policy='IDENTITY_SOURCE_FOLDER',scene_xml=None)
    for scene_root in scene_roots:
        if not scene_root.is_dir():continue
        for path in sorted(scene_root.glob('*.xml')):
            try:
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,63}',path.stem):raise ValueError('unsafe scene ID')
                refs=scene_references(path,available,models)
                if not refs:
                    errors.append(dict(scene=path.stem,source=str(path),status='NO_COURSE_MODEL_REFERENCE_NOT_A_GAME_LOAD_RESULT'));continue
                folders=sorted({r['folder'] for r in refs})
                policy='IDENTITY_SOURCE_FOLDER' if len(folders)==1 and all(r['identity_matrix'] for r in refs) else 'GEOMETRIC_FALLBACK_SCENE_PLACEMENTS_NOT_BAKED'
                bindings[path.stem.casefold()]=dict(scene=path.stem,folders=folders,normal_policy=policy,scene_xml=str(path),scene_xml_sha256=digest(path),model_references=refs)
            except (ValueError,ET.ParseError,OSError) as e:
                bindings.pop(path.stem.casefold(),None)
                errors.append(dict(scene=path.stem,source=str(path),status='SCENE_BINDING_FAILED',reason=str(e)))
    for binding in bindings.values():
        scene=binding['scene'];dest=runtime/scene;dest.mkdir();records={};normal_rows=set()
        for folder in binding['folders']:
            source=asset_root/folder
            for row in decode_metadata((source/'materials.lsm').read_bytes()):
                row=dict(row,course=scene);key=row['texture_sha256'];previous=records.get(key)
                if previous:
                    if previous['category']==row['category'] and previous['winding']==row['winding'] and not (previous['flags']|row['flags'])&16:row['flags']|=previous['flags']
                    elif any(previous[k]!=row[k] for k in ['category','flags','winding']):row.update(category=0,flags=16)
                records[key]=row
            if binding['normal_policy']=='IDENTITY_SOURCE_FOLDER':
                data=(source/'normals.lnh').read_bytes();count=struct.unpack_from('<I',data,8)[0]
                for i in range(count):normal_rows.add(scene.encode().ljust(64,b'\0')+data[76+i*153+64:76+(i+1)*153])
        (dest/'materials.lsm').write_bytes(encode_metadata(list(records.values())))
        payload=b''.join(sorted(normal_rows));(dest/'normals.lnh').write_bytes(struct.pack('<4sII',b'LNH1',1,len(normal_rows))+hashlib.sha256(payload).hexdigest().encode()+payload)
        binding['material_records']=len(records);binding['normal_records']=len(normal_rows);binding['runtime']='NOT_TESTED'
        (dest/'package.json').write_text(json.dumps(binding|{'schema':1,'files':{n:digest(dest/n) for n in ['materials.lsm','normals.lnh']}},indent=2)+'\n')
    result=dict(schema=1,runtime_package_dir=runtime_name,bindings=list(bindings.values()),unbound_scenes=errors)
    (output/'scene-bindings.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def export_batch(sources,output,roles=None,base=None,courses=None,scene_roots=None):
    if output.exists():raise ValueError('fresh output required')
    output.mkdir(parents=True);roles=roles or {}
    spec=importlib.util.spec_from_file_location('normal_hint_export',Path(__file__).with_name('atmosphere_normal_hints.py'))
    normals=importlib.util.module_from_spec(spec);spec.loader.exec_module(normals)
    prior=decode_metadata(base.read_bytes()) if base else []
    index={'schema':1,'status':'OFFLINE_ONLY_ALL_RUNTIME_NOT_TESTED','geometry_hash_allowlist':False,'courses':[]}
    for course in courses or discover(sources):
        dest=output/'courses'/course;report_dir=output/'reports'/course;report_dir.mkdir(parents=True)
        result={'course':course,'runtime':'NOT_TESTED','status':'FAILED','source_models':[],'materials':[]}
        try:
            retained_by_id={r['texture_sha256']:dict(r,course=course) for r in prior if r['course'].casefold()=='common'}
            retained_by_id.update({r['texture_sha256']:r for r in prior if r['course'].casefold()==course.casefold()})
            retained=list(retained_by_id.values())
            meta=export_lighting_metadata(sources,[course],dest,roles,encode_metadata(retained) if retained else None)
            normal_report=normals.export(sources,[course],dest/'materials.lsm',dest/'normal-export')
            (dest/'normal-export/normals.lnh').replace(dest/'normals.lnh')
            combined={}
            for source in meta['sources']:
                result['source_models'].append({'path':source['source'],'sha256':source['source_sha256'],'source_render_validated':True})
                for m in source['materials']:
                    name=m['material'];row=combined.setdefault(name,dict(m,offline_verdict=offline_verdict(m),runtime_verdict='NOT_OBSERVED',thumbnail=None,texture_identities=[]))
                    if row['offline_verdict']!=offline_verdict(m):row['offline_verdict']='Mixed source contracts (see provenance)'
            for r in prior:
                if r['course'].casefold()=='common':
                    combined.setdefault('Common/'+r['material'],dict(r,material=r['material'],common_material=True,offline_verdict='Eligible (retained Common capability; runtime admission required)',runtime_verdict='NOT_OBSERVED',thumbnail=None,texture_identities=[],bindings=[]))
            records=decode_metadata((dest/'materials.lsm').read_bytes())
            for name,row in combined.items():
                texture_name=row['material'];folders=[root.parent/'Misc/Checkpoints' if row.get('common_material') else root/course for root in sources]
                texture=next((folder/(texture_name+'.dxt') for folder in folders if (folder/(texture_name+'.dxt')).is_file()),None)
                if texture:
                    try:
                        decoded=parse_dxt(texture);opaque=bytearray(decoded.bgra);opaque[3::4]=b'\xff'*(len(opaque)//4)
                        row['texture_identities']=sorted({hashlib.sha256(decoded.bgra).hexdigest(),hashlib.sha256(opaque).hexdigest()})
                        row['runtime_capabilities']=[r for r in records if r['texture_sha256'] in row['texture_identities']]
                        name_png=digest(texture)[:24]+'.png';thumb=report_dir/'textures'/name_png;thumb.parent.mkdir(exist_ok=True);thumb.write_bytes(thumbnail(decoded));row['thumbnail']='textures/'+name_png
                        row['texture_source']=str(texture);row['texture_file_sha256']=digest(texture);row['source_alpha_range']=[min(decoded.bgra[3::4]),max(decoded.bgra[3::4])];row['thumbnail_mode']='RGB_PREVIEW_SOURCE_ALPHA_REPORTED_SEPARATELY'
                    except Exception as e:row['thumbnail_missing_reason']=str(e)
                else:row['thumbnail_missing_reason']='decoded source texture not available'
            result.update(status='OFFLINE_VALIDATED_GAMEPLAY_PENDING',materials=list(combined.values()),material_records=meta['records'],normal_records=normal_report['records'],normal_bytes=normal_report['bytes'])
            package={'schema':1,'course':course,'status':result['status'],'per_geometry_hashes':False,'files':{n:digest(dest/n) for n in ['materials.lsm','normals.lnh']}}
            (dest/'package.json').write_text(json.dumps(package,indent=2)+'\n')
        except Exception as e:
            result['error']=f'{type(e).__name__}: {e}'
            result['source_models']=[{'path':str(p),'sha256':digest(p),'validation':'FAILED_OR_NOT_COMPLETED'} for root in sources for p in course_model_paths(root/course)]
        result['counts']=dict(collections.Counter(m['offline_verdict'] for m in result['materials']))
        (report_dir/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        rows=''.join('<tr><td>'+('<img src="'+m['thumbnail']+'">' if m['thumbnail'] else 'MISSING')+'</td><td>'+html.escape(m['material'])+'</td><td>'+html.escape(m['offline_verdict'])+'</td><td>NOT OBSERVED</td></tr>' for m in result['materials'])
        (report_dir/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>'+html.escape(course)+'</title><style>body{font:16px system-ui;background:#151923;color:#ddd;margin:30px}td,th{padding:10px;text-align:left;border-bottom:1px solid #445}img{max-width:96px;image-rendering:auto}a{color:#8bd}</style><h1>'+html.escape(course)+'</h1><p>RGB texture previews; source alpha range is recorded in report.json. Offline source qualification. Lit is established only by runtime ledger. All courses: gameplay NOT TESTED.</p><p>'+html.escape(result.get('error',result['status']))+'</p><table><tr><th>Texture</th><th>Material</th><th>Offline contract</th><th>Runtime</th></tr>'+rows+'</table>',encoding='utf-8')
        index['courses'].append({k:result[k] for k in ['course','status','runtime','counts']}|{'report':'reports/'+course+'/index.html','error':result.get('error')})
        print(course,result['status'],result.get('material_records',0),result.get('normal_records',0),flush=True)
        (output/'courses.json').write_text(json.dumps(index,indent=2)+'\n')
    links=''.join('<li><a href="'+x['report']+'">'+html.escape(x['course'])+'</a> '+html.escape(x['status'])+'</li>' for x in index['courses'])
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Course Lighting SDK</title><h1>Course Lighting SDK</h1><p>Offline qualification only. Runtime: NOT TESTED. No per-object geometry SHA whitelist.</p><ul>'+links+'</ul>',encoding='utf-8')
    roots=scene_roots if scene_roots is not None else [r.parents[1]/'DataScene/RaceTest' for r in sources]
    scenes=export_scene_packages(output,roots);index['runtime_packages']=len(scenes['bindings']);index['scene_bindings']='scene-bindings.json'
    (output/'courses.json').write_text(json.dumps(index,indent=2)+'\n')
    return index

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,action='append',required=True);p.add_argument('--scenes',type=Path,action='append');p.add_argument('--course',action='append');p.add_argument('--output',type=Path,required=True);p.add_argument('--roles',type=Path);p.add_argument('--base',type=Path);a=p.parse_args()
    export_batch(a.source,a.output,json.loads(a.roles.read_text()) if a.roles else None,a.base,a.course,a.scenes)
