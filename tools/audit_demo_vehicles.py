"""Bounded read-only Demo/retail/accepted vehicle census and decoded comparison.

Inputs come from a private JSON config; no original cooker, game or mod runs.
All output is private metadata and diagnostic images below .research-output.
"""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import math
import os
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye import demo_vehicle_audit as audit
from master_rallye.addon_sdk import heritage_source as heritage
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.gxi import parse_gxi_bytes,encode_gxi_as_observed_dxt
from master_rallye.vehicle_packaging import _open_sma_archive
from master_rallye.universal_vehicle_scene import output_directory
import addon_runtime

MAX_BYTES=64*1024*1024


def filehash(path):
    h=hashlib.sha256()
    with path.open('rb')as stream:
        for b in iter(lambda:stream.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def local_files(root):
    root=heritage._absolute_without_links(Path(root),'audit tree')
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in sorted(dirs):
            path=Path(directory)/name
            if path.is_symlink()or getattr(path,'is_junction',lambda:False)():raise ValueError('Linked audit directory')
        for name in sorted(files):
            path=Path(directory)/name
            if path.is_symlink():raise ValueError('Linked audit file')
            yield path


def read_resource(path):
    if path.stat().st_size>MAX_BYTES:raise ValueError('Audit file budget exceeded')
    with path.open('rb')as stream:data=stream.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:raise ValueError('Audit read budget exceeded')
    return data


def role(name):
    stem=Path(name).stem.casefold()
    return {'car':'car','complete':'complete','comlplete':'complete','wheel':'wheel'}.get(stem, 'extra:'+stem)


def texture_stem(reference):
    name=reference.replace('\\','/').split('/')[-1]
    if name.casefold().endswith('.tga'):name=name[:-4]+'-tga'
    elif name.casefold().endswith(('.gxi','.dxt')):name=name[:-4]
    return name.casefold()


def texture_inventory(files,models):
    references=set()
    for m in models.values():
        references.update(m.get('texture_references',[]))
        for material in m.get('source_materials',[]):references.update(t['reference']for t in material['textures']if t['reference'].casefold()!='null')
    referenced={texture_stem(n)for n in references}
    references.update(Path(name).stem for name in files if name.endswith(('.dxt','.gxi')))
    result={};groups={}
    for reference in references:groups.setdefault(texture_stem(reference),[]).append(reference)
    for stem,names in sorted(groups.items()):
        candidates=[s for s in (stem+'.dxt',stem+'.gxi')if s in files]
        values=[]
        for candidate in candidates:
            try:
                raw=files[candidate][1];t=parse_dxt_bytes(raw)if candidate.endswith('.dxt')else parse_dxt_bytes(encode_gxi_as_observed_dxt(parse_gxi_bytes(raw)))
                values.append({'file':files[candidate][0],'sha256':audit.sha(raw),'width':t.width,'height':t.height,
                               'decoded_bgra_sha256':audit.sha(t.bgra),'alpha_range':[min(t.bgra[3::4]),max(t.bgra[3::4])]})
            except Exception as e:values.append({'file':candidate,'status':'FAIL','error':str(e)})
        result[stem]={'status':'PASS_LOCAL'if any('decoded_bgra_sha256'in v for v in values)else'MISSING_INPUT'if not values else'FAIL',
                      'original_references':sorted(names),
                      'referenced_by_decoded_models':stem in referenced,
                      'decoded_pair_equal':len({(v['width'],v['height'],v['decoded_bgra_sha256'])for v in values if 'decoded_bgra_sha256'in v})==1 if len(values)>1 else None,
                      'candidates':values,'binding_boundary':'DX slot or GXM filename reference, not proof of runtime texture dispatch'}
    return result


def read_family(identifier,label,folder,files,cache,kind='source'):
    models={};source_mesh_names={}
    for lower,(name,raw)in sorted(files.items()):
        if lower.endswith('.txt'):
            import re
            names=re.findall(r'moMesh\(Name\s+\[([^\]]+)\]',raw.decode('utf-8',errors='replace'))
            if names:source_mesh_names[name]=names
        if not lower.endswith(('.dx','.gxm')):continue
        digest=audit.sha(raw)
        if digest not in cache:
            try:cache[digest]=audit.dx_evidence(raw,name)if lower.endswith('.dx')else audit.gxm_evidence(raw,name)
            except Exception as e:cache[digest]={'status':'UNSUPPORTED','error':str(e),'_positions':[],'_triangles':[]}
        models[name]={'sha256':digest,'bytes':len(raw),'role':role(name),'format':Path(name).suffix[1:].upper(),**audit.public(cache[digest])}
    textures=texture_inventory(files,models)
    return {'id':identifier,'label':label,'family':Path(folder).name,'relative_folder':str(folder),'kind':kind,
            'files':{name:{'bytes':len(raw),'sha256':audit.sha(raw)}for name,raw in files.values()},'models':models,
            'textures':textures,'source_mesh_names':source_mesh_names,
            'features':{'glass_name_candidates':[s for names in source_mesh_names.values()for s in names if any(w in s.lower()for w in ('glass','screen','window'))],
                        'lamp_name_candidates':[s for names in source_mesh_names.values()for s in names if any(w in s.lower()for w in ('light','blight'))],
                        'damage':'DX controller/group and collision metadata; no new gameplay qualification'},
            'native_roles':sorted({m['role']for m in models.values()if m['format']=='DX'and m['role'] in ('car','complete','wheel')and m['status']=='PASS_DRAW_SURFACES'}),
            'missing_texture_count':sum(t['status']!='PASS_LOCAL'and t['referenced_by_decoded_models']for t in textures.values())}


def physics_references(game,family):
    result={}
    for name in ('vehicles.xml','Modifications.xml'):
        path=game/'DataGame'/name
        if not path.is_file():continue
        try:
            raw=heritage.read(path);tree=ET.fromstring(raw);prefix='vehicles/'+family.casefold()+'/'
            rows=[dict(x.attrib)for x in tree.iter('Value')if x.get('Name','').casefold().startswith(prefix)]
            if rows:result[name]={'sha256':audit.sha(raw),'values':rows,'boundary':'Named reference only; no inferred CarID/audio/driver binding'}
        except Exception as e:result[name]={'status':'WARN','error':str(e)}
    return result


def compare_families(row,references,cache,memo=None):
    memo={}if memo is None else memo
    output=[]
    for name,m in row['models'].items():
        a=cache[m.get('_comparison_key',m['sha256'])]
        if 'surface_sha256'not in a:continue
        candidates=[]
        for ref in references:
            if ref['id']==row['id']:continue
            for rn,rm in ref['models'].items():
                if rm['role']!=m['role']:continue
                if rm['format']!=m['format']and not (m.get('_comparison_key')or rm.get('_comparison_key')):continue
                b=cache[rm.get('_comparison_key',rm['sha256'])]
                if 'surface_sha256'not in b:continue
                pair=(m.get('_comparison_key',m['sha256']),rm.get('_comparison_key',rm['sha256']))
                if pair not in memo:memo[pair]=audit.comparison(a,b)
                c=memo[pair]
                candidates.append({'family':ref['id'],'model':rn,'source_sha_equal':m['sha256']==rm['sha256'],
                                   'position_only_cross_format':rm['format']!=m['format'],**c})
        candidates.sort(key=lambda x:(-x['overlap'],x.get('sampled_unscaled_rms',0.0 if x['overlap']==1 else float('inf')),not x['source_sha_equal'],x['family'],x['model']))
        output.append({'model':name,'role':m['role'],'format':m['format'],'best':candidates[:5],
                       'all_exact':[x for x in candidates if x['kind']=='EXACT_DECODED_SURFACE']})
    return output


def align_source_frames(rows,cache):
    votes={};local={}
    for row in rows:
        for name,m in row['models'].items():
            if m['format']!='GXM'or m['role']not in('car','complete','wheel'):continue
            source=cache[m['sha256']]
            targets=[n for n in row['models'].values()if n['format']=='DX'and n['role']==m['role']and 'surface_sha256'in cache[n['sha256']]]
            if not targets or 'surface_sha256'not in source:continue
            target=cache[targets[0]['sha256']];alignment=audit.signed_axis_alignment(source,target)
            if alignment:
                local[(row['id'],name)]=alignment
                if m['role']=='car':votes.setdefault(row['label'],[]).append({'witness':row['id']+'/'+name,**alignment})
    consensus={}
    for label,items in votes.items():
        frames={(tuple(x['permutation']),tuple(x['signs']))for x in items}
        if len(frames)==1 and len(items)>=2:consensus[label]={'permutation':items[0]['permutation'],'signs':items[0]['signs'],'witnesses':[x['witness']for x in items]}
    for row in rows:
        for name,m in row['models'].items():
            if m['format']!='GXM'or 'surface_sha256'not in cache[m['sha256']]:continue
            alignment=local.get((row['id'],name))or consensus.get(row['label'])
            if alignment is None:continue
            key=m['sha256']+repr((alignment['permutation'],alignment['signs']))
            if key not in cache:cache[key]=audit.transform_surface(cache[m['sha256']],alignment)
            m['_comparison_key']=key
            m['position_comparison_frame']={'alignment':alignment,'evidence':'local position sample'if (row['id'],name)in local else'consistent same-source-root car witnesses; inference for this model',
                                            'boundary':'Position-only diagnostic normalization, not original hierarchy/UV/winding/units qualification'}
    return {'local_matches':len(local),'source_root_consensus':consensus}


def contact_sheet(rows,cache,path):
    from PIL import Image,ImageDraw
    w,h=300,245;cols=5;image=Image.new('RGB',(cols*w,math.ceil(len(rows)/cols)*h),'#1c232b');d=ImageDraw.Draw(image)
    for i,row in enumerate(rows):
        x=(i%cols)*w;y=(i//cols)*h
        chosen=next((m for m in row['models'].values()if m['role']=='car'and m['format']=='DX'and cache[m['sha256']].get('_triangles')),None)
        if chosen is None:chosen=next((m for m in row['models'].values()if m['role']=='car'and cache[m['sha256']].get('_triangles')),None)
        d.text((x+7,y+5),row['id'][:47],fill='white')
        d.text((x+7,y+20),'Diagnostic source-frame wire; no scale matching',fill='#b5bdc7')
        if chosen:
            model=cache[chosen['sha256']];points=model['_positions'];triangles=model['_triangles']
            projected=[(.72*p[0]-.69*p[2],.30*p[0]-.85*p[1]+.32*p[2])for p in points]
            bounds=[min(p[k]for p in projected)for k in (0,1)]+[max(p[k]for p in projected)for k in (0,1)]
            scale=min((w-25)/max(bounds[2]-bounds[0],.001),(h-75)/max(bounds[3]-bounds[1],.001))
            screen=[(x+12+(p[0]-bounds[0])*scale,y+38+(p[1]-bounds[1])*scale)for p in projected]
            for t in triangles[:15000]:d.line([screen[v]for v in (*t,t[0])],fill='#7ea2b4',width=1)
            d.text((x+7,y+h-29),chosen['format']+' / '+str(chosen['triangles'])+' triangles',fill='#f1c37b')
        else:d.text((x+20,y+100),'No qualified geometry array',fill='#ed9b9b')
        d.text((x+7,y+h-15),'native roles: '+','.join(row['native_roles'])+' / missing tex '+str(row['missing_texture_count']),fill='#b5bdc7')
    image.save(path)


def comparison_matrix(result,output):
    matrix=[]
    for row in result['families']:
        if row['kind']in('retail','accepted_reference'):continue
        models=[(name,m)for name,m in row['models'].items()if m['role']=='car'and 'surface_sha256'in m]
        models.sort(key=lambda item:(item[1]['format']!='DX',item[0]))
        selected=models[0]if models else None
        matches=[];accepted=[];source=[]
        if selected:
            name,m=selected
            for key,dest in [('retail',matches),('accepted',accepted),('sources',source)]:
                group=next((g for g in row['comparisons'][key]if g['model']==name),None)
                if group:dest.extend(group['best'])
        best=matches[0]if matches else None
        if not selected:uniqueness='UNRESOLVED_GEOMETRY'
        elif not best:uniqueness='NO_COMPARABLE_RETAIL_SURFACE'
        elif best['kind']in('EXACT_DECODED_SURFACE','SAME_SURFACE_WINDING_DIFFERS'):uniqueness='RETAIL_POSITIONAL_SURFACE_MATCH'
        elif best['overlap']>=.5:uniqueness='PARTIAL_RETAIL_SURFACE_VARIANT'
        else:uniqueness='NO_EXACT_RETAIL_SURFACE_MATCH'
        readiness=('COMPLETE_NATIVE_INPUTS'if len(row['native_roles'])==3 and not row['missing_texture_count']else
                   'NATIVE_TEXTURE_GAPS'if len(row['native_roles'])==3 else'PARTIAL_OR_SOURCE_ONLY')
        entry={'family':row['id'],'uniqueness':uniqueness,'readiness':readiness,'native_roles':row['native_roles'],
               'missing_referenced_textures':row['missing_texture_count'],'compared_car':selected[0]if selected else None,
               'retail':best,'accepted':accepted[0]if accepted else None,
               'source_matches':[m for m in source if m['kind']=='EXACT_DECODED_SURFACE'],
               'boundary':'Ranking columns describe source distinction and input completeness; they are not gameplay qualification.'}
        matrix.append(entry)
    (output/'matrix.json').write_text(json.dumps(matrix,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    lines=['# Complete Demo vehicle comparison matrix','',
           'Exact paths, resource hashes, decoded fingerprints, texture dimensions/alpha and comparison evidence are in private catalog.json. Native completeness does not imply playable integration. Source/GXM-only normalized comparisons are positional diagnostics; material/UV/hierarchy limitations remain explicit.','',
           '| Source / family | Source distinction | Input completeness | Native roles | Missing texture refs | Closest retail car (overlap / sampled RMS) | Accepted reference |',
           '|---|---|---|---|---:|---|---|']
    for e in matrix:
        def match(x):return (x['family']+' / '+str(x['overlap'])+' / '+str(x.get('sampled_unscaled_rms',0 if x['overlap']==1 else'?')))if x else'UNRESOLVED'
        lines.append('| '+e['family']+' | '+e['uniqueness']+' | '+e['readiness']+' | '+','.join(e['native_roles'])+' | '+str(e['missing_referenced_textures'])+' | '+match(e['retail'])+' | '+match(e['accepted'])+' |')
    (output/'matrix.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    primary=[e for e in matrix if e['family'].startswith(('pcg-rebaked/','nov-local/'))]
    novelty={'NO_EXACT_RETAIL_SURFACE_MATCH':0,'PARTIAL_RETAIL_SURFACE_VARIANT':1,'RETAIL_POSITIONAL_SURFACE_MATCH':2,'NO_COMPARABLE_RETAIL_SURFACE':3,'UNRESOLVED_GEOMETRY':4}
    primary.sort(key=lambda e:(novelty[e['uniqueness']],e['readiness']!='COMPLETE_NATIVE_INPUTS',e['missing_referenced_textures'],e['family']))
    (output/'shortlist-inputs.json').write_text(json.dumps(primary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def run(config,output):
    config_path=Path(config);cfg=json.loads(config_path.read_text(encoding='utf-8'))
    protected=[]
    for item in cfg['sources']:
        root=Path(item['root']);protected.append(root/'DataGx/Vehicles')
        protected.extend(p for p in (root/'MRallye.exe',root/'DataGame/vehicles.xml',root/'DataGame/Modifications.xml')if p.is_file())
    for item in cfg['accepted']:protected.append(Path(item['folder']))
    retail_exe=Path(addon_runtime.DEFAULT_RETAIL_EXE);retail_game=retail_exe.parent
    retail=retail_game/'Data.sma_unpacked';sma=retail_game/'Data.sma'
    capabilities=Path(addon_runtime.DEFAULT_CAPABILITIES);cap=json.loads(capabilities.read_text())
    if filehash(sma)!=cap['retail_data_sma_sha256']:raise ValueError('Configured retail archive does not match SDK resource profile')
    protected.extend([retail/'DataGx/Vehicles',retail/'DataGame/vehicles.xml',retail/'DataGame/Modifications.xml',sma,retail_exe,config_path])
    output=output_directory(Path(output),protected)
    if not output.is_relative_to((ROOT/'.research-output').absolute()):raise ValueError('Audit output must remain private below .research-output')
    tracked={}
    for folder in protected:
        paths=local_files(folder)if folder.is_dir()else [folder]
        for path in paths:
            tracked[str(path.absolute())]={'bytes':path.stat().st_size,'sha256':filehash(path)}
            if len(tracked)%500==0:print('Source preservation snapshot',len(tracked),flush=True)
    output.mkdir(parents=True)
    (output/'preservation-before.json').write_text(json.dumps(tracked,indent=2))
    rows=[];cache={};archives=[]
    for item in cfg['sources']+[{'label':'retail','root':str(retail),'kind':'retail'}]:
        root=Path(item['root']);vehicles=root/'DataGx/Vehicles';label=item['label']
        for folder in heritage.family_folders(vehicles):
            files={}
            for f in sorted(folder.iterdir()):
                if f.is_file()and f.suffix.casefold()in ('.dx','.gxm','.gxi','.dxt','.txt'):
                    lower=f.name.casefold()
                    if lower in files:raise ValueError('Case-colliding family file')
                    files[lower]=(f.name,read_resource(f))
            relative=folder.relative_to(vehicles).as_posix()
            row=read_family(label+'/'+relative,label,relative,files,cache,item.get('kind','source'))
            row['folder']=str(folder.absolute());row['source_claim']=item.get('provenance','Configured clean retail archive/unpacked pair')
            row['physics_references']=physics_references(root,row['family']);rows.append(row)
        for archive in vehicles.rglob('*.zip'):
            with zipfile.ZipFile(archive)as z:
                if len(z.infolist())>2000 or sum(i.file_size for i in z.infolist())>128*1024*1024:raise ValueError('Archive inspection budget')
                groups={};index=[]
                for info in z.infolist():
                    pure=Path(info.filename.replace('\\','/'))
                    if pure.is_absolute()or '..'in pure.parts or ':'in str(pure):raise ValueError('Unsafe vehicle archive member')
                    if info.is_dir():continue
                    if info.file_size>MAX_BYTES:raise ValueError('Archive member budget')
                    raw=z.read(info);index.append({'name':info.filename,'bytes':len(raw),'sha256':audit.sha(raw)})
                    if pure.suffix.casefold()in ('.dx','.gxm','.gxi','.dxt','.txt'):
                        group=groups.setdefault(pure.parent.as_posix(),{})
                        if pure.name.casefold()in group:raise ValueError('Archive member case collision')
                        group[pure.name.casefold()]=(pure.name,raw)
                for group,files in groups.items():
                    row=read_family(label+'@'+archive.name+'/'+group,label+'@archive',group,files,cache,'archive_snapshot')
                    row['archive']=str(archive);row['physics_references']={};rows.append(row)
                archives.append({'path':str(archive),'sha256':filehash(archive),'members':index})
        print('Inventoried',label,'families',sum(r['label']==label for r in rows),flush=True)
    for item in cfg['accepted']:
        folder=Path(item['folder']);files={f.name.casefold():(f.name,read_resource(f))for f in folder.iterdir()if f.is_file()and f.suffix.casefold()in('.dx','.dxt','.gxi','.gxm','.txt')}
        row=read_family('accepted/'+item['label'],'accepted',item['label'],files,cache,'accepted_reference');row['folder']=str(folder);row['physics_references']={};rows.append(row)
    # Verify that every retail resource used is genuinely in the configured archive.
    retail_errors=[]
    with _open_sma_archive(sma)as z:
        names={n.casefold():n for n in z.namelist()}
        for row in (r for r in rows if r['kind']=='retail'):
            for name,info in row['files'].items():
                key=('DataGx/Vehicles/'+row['relative_folder']+'/'+name).casefold()
                if key not in names or audit.sha(z.read(names[key]))!=info['sha256']:retail_errors.append(row['id']+'/'+name)
    if retail_errors:raise ValueError('Retail unpacked resources not authenticated by clean archive: '+repr(retail_errors[:10]))
    pools={'retail':[r for r in rows if r['kind']=='retail'],'accepted':[r for r in rows if r['kind']=='accepted_reference'],
           'sources':[r for r in rows if r['kind']not in('retail','accepted_reference')]}
    frames=align_source_frames(rows,cache)
    memo={}
    for row in rows:
        if row['kind']in('retail','accepted_reference'):continue
        row['comparisons']={key:compare_families(row,refs,cache,memo)for key,refs in pools.items()}
    for row in rows:
        for m in row['models'].values():m.pop('_comparison_key',None)
    result={'schema':'complete-demo-vehicle-audit/1','config':cfg,'coordinate_comparisons':frames,'retail_reference':{'capabilities':str(capabilities),'archive':str(sma),'sha256':cap['retail_data_sma_sha256'],'unpacked':str(retail),'resource_mismatches':retail_errors},
            'families':rows,'archives':archives,'boundaries':['No game, cooker, new CarID or native adaptation executed.','Exact surface comparisons ignore vertex ordering but preserve multiplicity and winding.','Approximate positional overlap uses 1e-5 units, not source identity.','GXM hierarchy and runtime texture dispatch remain separate from recovered triangle arrays.']}
    (output/'catalog.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    comparison_matrix(result,output)
    contact_sheet(pools['sources'],cache,output/'source-contact.png')
    # Prove the complete examined source and accepted trees were untouched.
    changed=[]
    for name,pin in tracked.items():
        p=Path(name)
        if not p.is_file()or p.stat().st_size!=pin['bytes']or filehash(p)!=pin['sha256']:changed.append(name)
    preservation={'files':len(tracked),'bytes':sum(p['bytes']for p in tracked.values()),'changed_or_missing':changed,'status':'PASS'if not changed else'FAIL'}
    (output/'preservation.json').write_text(json.dumps(preservation,indent=2))
    if changed:raise ValueError('Source or accepted file changed during read-only audit')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();result=run(a.config,a.output);print('Families',len(result['families']))
