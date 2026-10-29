"""Read-only original MR texture ownership and reversible UVS livery probes.

No CarID, DX authoring or native candidate. An experimental atlas patch is
explicitly separate from verified direct texture correspondence.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import re
from . import universal_vehicle_scene as u
from .dx import parse_dx
from .dxt import parse_dxt_bytes,decode_rgba_pixels,PNG_ROWS_PRESERVE_STORED
from .vehicle_packaging import _open_sma_archive

VERSION='lost-pajero-textures/1'
RETAIL_SHA='03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f'
SOURCE_SCENE_SHA='fb9a91ee48b1fa762115945085e1804dd2cdb791dde08c61bb018b45cecbd8ad'
BADGE_SHA='e56a2a39e1f799ec86bb78cb3f701b4910bc06f0d1c211cf209b25aa20dfac45'


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def txt_materials(text):
    result=[];material=None
    for line in text.splitlines():
        m=re.search(r'Material number \[\s*(\d+)\] has name \[([^]]+)\]',line)
        if m:material={'id':int(m[1]),'name':m[2]}
        m=re.search(r'Texture \[\s*(\d+)\].*Name\[([^]]+)\]',line)
        if m and material:
            path=m[2];stem=path.replace('\\','/').split('/')[-1].rsplit('.',1)[0].lower()+'-tga'
            result.append({**material,'slot':int(m[1]),'original_reference':path,'texture_stem':stem})
    return result


def inventory(corpus):
    corpus=Path(corpus).absolute();u.unlinked(corpus)
    archive=corpus/'retail/Data.sma';family=corpus/'retail/Data.sma_unpacked/DataGx/Vehicles/Pajero'
    if file_hash(archive)!=RETAIL_SHA:raise ValueError('Unqualified retail SMA')
    bindings=[];files=[];models=[]
    for p in sorted(family.glob('*.dx')):
        model=parse_dx(p)
        models.append({'path':str(p),'sha256':file_hash(p),'bytes':p.stat().st_size,
                       'vertices':len(model.vertices.positions),'triangles':sum(d.triangle_count for d in model.physical_draws),
                       'uv_sets':len(model.uv_sets),'warnings':model.diagnostics.warnings})
        for d in model.physical_draws:
            ids=model.draw_global_indices(d)
            uv=[model.uv_sets[0].values[k]for k in ids]if model.uv_sets else[]
            for slot in d.texture_slots:
                if slot.value.casefold()=='null':continue
                bindings.append({'model':p.name,'draw':d.draw_index,'group':d.group_label,'slot':slot.slot,
                    'texture_stem':slot.value.lower(),'triangles':d.triangle_count,'flags':list(d.flags_0x20),
                    'shader_bits':d.unknown_0x24,'uv_bounds':[[min(v[k]for v in uv),max(v[k]for v in uv)]for k in range(2)]if uv else None,
                    'uv_indexed_sha256':u.sha(u.canonical(uv))})
    text_refs={p.name:txt_materials(p.read_text(errors='strict'))for p in sorted(family.glob('*.txt'))}
    family_files=[]
    with _open_sma_archive(archive)as packed:
        lookup={n.replace('\\','/').lower():n for n in packed.namelist()}
        for p in sorted(family.iterdir()):
            if not p.is_file():continue
            u.unlinked(p);raw=u.read_bounded(p,16*1024*1024)
            member=p.relative_to(corpus/'retail/Data.sma_unpacked').as_posix();key=lookup.get(member.lower())
            if key is None or packed.read(key)!=raw:raise ValueError('Family extraction differs from original retail SMA')
            family_files.append({'path':str(p),'archive_member':key,'bytes':len(raw),'sha256':u.sha(raw),'archive_exact':True})
        for p in sorted(family.glob('*.dxt')):
            u.unlinked(p);raw=u.read_bounded(p,16*1024*1024);t=parse_dxt_bytes(raw)
            member=p.relative_to(corpus/'retail/Data.sma_unpacked').as_posix();key=lookup.get(member.lower())
            if key is None or packed.read(key)!=raw:raise ValueError('Extracted texture differs from clean SMA')
            stem=p.stem.lower();direct=[b for b in bindings if b['texture_stem']==stem]
            txt=[{'file':f,**row}for f,rows in text_refs.items()for row in rows if row['texture_stem']==stem]
            files.append({'path':str(p),'archive_member':key,'sha256':u.sha(raw),'bytes':len(raw),'width':t.width,'height':t.height,
                'header_words':[t.word_0x04,t.word_0x08],'alpha_range':[min(t.bgra[3::4]),max(t.bgra[3::4])],
                'native_bindings':direct,'txt_bindings':txt,
                'ownership':'DX_REFERENCED'if direct else'TXT_ONLY'if txt else'UNREFERENCED_WITHIN_PAJERO_DX_TXT',
                'archive_exact':True})
    demos=[]
    for demo in sorted(corpus.glob('demo-*')):
        root=demo/'DataGx/Vehicles';family_paths=[p for p in root.rglob('*')if p.is_file()and ('pajero' in p.as_posix().lower()or p.name.lower().startswith(('pdoor128','pajeror128','pfrontgb')))]
        demos.append({'root':str(demo),'executable_sha256':file_hash(demo/'MRallye.exe')if(demo/'MRallye.exe').is_file()else None,'pajero_related_files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':file_hash(p)}for p in family_paths],
            'status':'FOUND'if family_paths else'NO_PAJERO_FAMILY_IN_AVAILABLE_EXTRACTION','boundary':'No missing disc contents invented'})
    artwork=[]
    for relative in ('retail/Data.sma_unpacked','demo-8.4.1','demo-9.3.1','demo-9.10.0'):
        for name in ('carsheet_010_000.dxt','carsheet_022_000.dxt'):
            p=corpus/relative/'DataGx/Frontend/VehicleSelect'/name
            if p.is_file():
                t=parse_dxt_bytes(u.read_bounded(p,1024*1024));artwork.append({'path':str(p),'sha256':file_hash(p),'bytes':p.stat().st_size,'width':t.width,'height':t.height,'role':'FRONTEND_ARTWORK_NOT_MODEL_TEXTURE'})
    return {'schema':VERSION,'retail_archive':{'path':str(archive),'sha256':RETAIL_SHA},'family_files':family_files,'textures':files,'models':models,'frontend_artwork':artwork,
            'native_bindings':bindings,'txt_materials':text_refs,'demos':demos,
            'runtime':'DX reference is structural ownership, not proof a runtime switch selected that draw'}


def direct_compatible(source_uv,target_uv,*,source_layout_hash,target_layout_hash):
    """An equal numeric UV range alone cannot authorize cross-atlas rebinding."""
    return (bool(source_layout_hash)and source_layout_hash==target_layout_hash and source_uv==target_uv)


class OverlayHistory:
    def __init__(self,states=None,cursor=0):
        self.states=deepcopy(states or [{'enabled':False}]);self.cursor=cursor
        if (type(cursor)is not int or not isinstance(self.states,list)or not 1<=len(self.states)<=1024 or
            any(not isinstance(s,dict)or set(s)!={'enabled'}or type(s['enabled'])is not bool for s in self.states)or
            not 0<=cursor<len(self.states)):raise ValueError('Invalid history cursor/states')
    def apply(self,enabled):
        if type(enabled)is not bool:raise ValueError('Explicit boolean overlay required')
        self.states=self.states[:self.cursor+1]+[{'enabled':enabled}];self.cursor+=1
    def undo(self):self.cursor=max(0,self.cursor-1)
    def redo(self):self.cursor=min(len(self.states)-1,self.cursor+1)
    def restore(self):self.apply(False)
    def save(self,path):Path(path).write_bytes(u.canonical({'schema':VERSION,'states':self.states,'cursor':self.cursor}))
    @classmethod
    def load(cls,path):
        d=json.loads(u.read_bounded(Path(path),65536))
        if d.get('schema')!=VERSION:raise ValueError('Unknown overlay history schema')
        return cls(d['states'],d['cursor'])
    @property
    def enabled(self):return self.states[self.cursor]['enabled']


def patch_badge(base_rgba,width,height,badge_rgba,badge_width,badge_height,rectangles,*,mirror_x=()):
    """Explicit reviewed atlas rectangles, uniform resize, no invented artwork."""
    from PIL import Image
    if max(width,height,badge_width,badge_height)>2048 or min(width,height,badge_width,badge_height)<1:raise ValueError('Texture budget')
    if len(base_rgba)!=width*height*4 or len(badge_rgba)!=badge_width*badge_height*4:raise ValueError('Texture sample size')
    if not 1<=len(rectangles)<=8:raise ValueError('Rectangle budget')
    if any(type(i)is not int or not 0<=i<len(rectangles)for i in mirror_x):raise ValueError('Unknown mirrored island')
    base=Image.frombytes('RGBA',(width,height),base_rgba);badge=Image.frombytes('RGBA',(badge_width,badge_height),badge_rgba)
    changed=set()
    for ordinal,rect in enumerate(rectangles):
        if len(rect)!=4 or any(type(v)is not int for v in rect):raise ValueError('Integer rectangle required')
        x,y,right,bottom=rect
        if not 0<=x<right<=width or not 0<=y<bottom<=height or right-x!=bottom-y:raise ValueError('Square contained badge region required')
        # Source Xbox placards are inverted in stored texture rows. The derived
        # MR badge uses an explicit upright-to-stored-row vertical flip, not source UV edits.
        sample=badge.transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((right-x,bottom-y),Image.Resampling.NEAREST)
        if ordinal in mirror_x:sample=sample.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        base.paste(sample,(x,y))
        changed.update((yy*width+xx)for yy in range(y,bottom)for xx in range(x,right))
    raw=bytearray(base.tobytes())
    # Coverage is owned by the original Xbox material, never by the MR badge.
    raw[3::4]=base_rgba[3::4]
    if any(raw[i*4:i*4+4]!=base_rgba[i*4:i*4+4]for i in range(width*height)if i not in changed):raise ValueError('Patch escaped reviewed regions')
    return bytes(raw),sorted(changed)


def badge_experiment(source,output,mr_family,history):
    source=Path(source).absolute();root=source.parent;mr_family=Path(mr_family).absolute()
    if file_hash(source)!=SOURCE_SCENE_SHA:raise ValueError('Qualified immutable Xbox Pajero scene required')
    scene=u.load_scene(source);original=deepcopy(scene);assets={}
    for name in json.loads((root/'manifest.json').read_text())['files']:
        if name!='scene.json':assets[name]=(root/name).read_bytes()
    selected='node-000-sub-01';mesh=next(m for m in scene['meshes']if m['id']==selected)
    mat=next(m for m in scene['materials']if m['id']==mesh['material_id'])
    if mat['diffuse_texture_id']!='xtx-046' or mat['flags']['transparent_raw']!='0':raise ValueError('Unexpected opaque body ownership')
    tex=next(t for t in scene['textures']if t['id']=='xtx-046');base=assets[tex['rgba_path']]
    badge_path=mr_family/'mastersticker-tga.dxt';raw=u.read_bounded(badge_path,65536);badge=parse_dxt_bytes(raw)
    if u.sha(raw)!=BADGE_SHA:raise ValueError('Unqualified original MR badge')
    # Upright original MR graphic; never repaint its number or logo.
    rgba=decode_rgba_pixels(badge,'flip-vertical');rects=[[88,82,118,112],[88,178,118,208]]
    patched,pixels=patch_badge(base,tex['width'],tex['height'],rgba,badge.width,badge.height,rects,mirror_x=(1,))
    if history.enabled:
        key='derived-mr203-badge';path='derived/'+key+'.rgba';assets[path]=patched
        derived=deepcopy(tex);derived.update(id=key,rgba_path=path,rgba_sha256=u.sha(patched))
        derived['source_channels']={'mode':'DERIVED_RGB_ONLY','alpha':'unchanged original Xbox samples'}
        derived.pop('source',None)
        derived['derived_from']={'mr_badge':str(badge_path),'sha256':u.sha(raw),'xbox_texture':'xtx-046','original_rgba_sha256':tex['rgba_sha256'],'original_xbox_resource':tex['source']}
        scene['textures'].append(derived);mat['diffuse_texture_id']=key
    assets['original-mr/mastersticker-tga.dxt']=raw
    scene['source']['resources'].append({'member':'mr/Pajero/mastersticker-tga.dxt','snapshot_path':'original-mr/mastersticker-tga.dxt','bytes':len(raw),'sha256':u.sha(raw)})
    scene['metadata']['livery_experiment']={'schema':VERSION,'variant':'C_PARTIAL_BADGE_ONLY'if history.enabled else'A_ORIGINAL',
        'source_scene_sha256':SOURCE_SCENE_SHA,'enabled':history.enabled,'selected_mesh':selected,'atlas_rectangles':rects,
        'orientation':['upright MR to stored rows: flipV','opposed side island: flipV+flipU'],
        'mr_badge_sha256':u.sha(raw),'changed_pixel_budget':len(pixels),'qualification':'Authored atlas correspondence experiment, NOT verified direct UV compatibility or restored full MR livery',
        'limitations':['Original Xbox red/yellow paint and sponsors remain','Roof/hood number and other panels remain original',
            'Right-side badge legibility remains WARN in neutral captures; this is not a qualified two-sided transfer',
            'No new geometry or UV changes','L2 WARN source shader/runtime parity']}
    if history.enabled:scene['metadata']['display_name']='Dakar 2 Xbox Pajero — C partial MR203 badge — WARN'
    for before,after in zip(original['meshes'],scene['meshes']):
        if before!=after:raise ValueError('Source geometry/UV/stream changed')
    assets['inspection/livery-overlay.json']=u.canonical(scene['metadata']['livery_experiment'])
    return u.save_scene(scene,Path(output),assets,protected_roots=[root,mr_family,*map(Path,scene['source'].get('protected_roots',[]))])
