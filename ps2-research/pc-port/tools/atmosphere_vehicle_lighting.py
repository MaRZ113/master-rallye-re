"""Vehicle Lighting SDK: source-material contracts, never per-mesh authorization."""
from pathlib import Path
import argparse,collections,hashlib,html,importlib.util,json,re,struct,sys
for root in Path(__file__).resolve().parents:
    if (root/'src/master_rallye').is_dir():sys.path.insert(0,str(root/'src'));break
spec=importlib.util.spec_from_file_location('body_policy',Path(__file__).with_name('atmosphere_body_metadata.py'));policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
ZERO='0'*64
ROLES={1:'paint',2:'opaque_trim',3:'opaque_panel',4:'opaque_cover',5:'opaque_helmet',6:'opaque_flat',7:'interior',8:'pilot',9:'wheel_rubber',10:'wheel_metal',11:'opaque_glazing'}
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(s):
    s=s.lower().replace('\\','/').split('/')[-1]
    if s.endswith(('.dxt','.gxi')):s=s[:-4]
    if s.endswith('.tga'):s=s[:-4]+'-tga'
    return re.sub(r'^mr-ref-[0-9a-f]+-','',s)
def role_for(primary,secondary,part,opaque=True):
    if not opaque:return 0,'Native transparency / glass'
    if any(t in primary for t in ('light','lamp','glow','brake')) or any(t in secondary for t in ('light','lamp','glow')):return 0,'Native emissive / lamp policy (phase 3.0)'
    if secondary=='glass-tga':
        return (11,'Opaque glazing RGB only; native reflection/alpha retained') if policy.safe(primary,secondary,11) else (0,'Native protected glass / lamp')
    if any(t in primary for t in ('glass','window','windscreen')):return 0,'Native glass / damage transparency'
    if part=='wheel':role=9 if secondary=='rubber-tga' else 10 if secondary=='chrome-tga' else 0
    elif secondary=='rubber-tga':role=9
    elif secondary=='chrome-tga':role=10
    elif 'wheelcover' in primary and secondary=='perspex-tga':role=4
    elif 'sticker' in primary and secondary in ('whitepaint-tga','silverpaint-tga','perspex-tga'):role=3
    elif 'helmet' in primary:role=5 if secondary in ('whitepaint-tga','silverpaint-tga') else 8
    elif any(t in primary for t in ('driver','pilot')):role=8
    elif secondary in ('whitepaint-tga','silverpaint-tga'):role=3 if 'sticker' in primary else 1
    elif any(t in primary for t in ('chair','seat','interior','dash','cockpit','steer')):role=7
    elif secondary=='perspex-tga':role=2
    elif secondary=='null':role=6
    else:role=0
    return (role,'Eligible; runtime owner/pass still required') if role and policy.safe(primary,secondary,role) else (0,'Unclassified / protected material contract')

def encode(rows):
    if len(rows)>2048:raise ValueError('native metadata record limit')
    def fixed(s,n):return policy.fixed(s,n)
    payload=b''.join(fixed(f,32)+fixed(part,32)+fixed(p,96)+fixed(s,96)+fixed(a,65)+fixed(b,65)+struct.pack('<I',role) for f,part,p,s,a,b,role in sorted(rows))
    return struct.pack('<4sII',b'BLM3',3,len(rows))+digest(payload).encode()+payload

def old_roles(path):
    if path is None:return {}
    data=path.read_bytes();magic,version,count=struct.unpack_from('<4sII',data)
    if magic!=b'BLM2' or version!=2 or len(data)!=76+293*count or digest(data[76:]).encode()!=data[12:76]:raise ValueError('baseline BLM2 integrity')
    rows={}
    for i in range(count):
        row=data[76+i*293:76+(i+1)*293];f=row[:32].split(b'\0')[0].decode();p=row[32:128].split(b'\0')[0].decode();s=row[128:224].split(b'\0')[0].decode();role=struct.unpack_from('<I',row,289)[0]
        if not policy.safe(p,s,role):raise ValueError('unsafe baseline role')
        key=(f,'car',p,s)
        if key in rows and rows[key]!=role:raise ValueError('baseline role ambiguity')
        rows[key]=role
    return rows

def ps2_bindings(path):
    data=path.read_bytes()
    if len(data)<64 or len(data)>32*1024*1024 or data[:8]!=b'PS2MDL02':raise ValueError('PS2 asset format / size')
    version,meta,meshes,vertices,indices,textures=struct.unpack_from('<6I',data,8)
    if version!=2 or meta>4*1024*1024 or meshes>512 or textures>512 or vertices>1000000 or indices>3000000:raise ValueError('PS2 counts')
    source=json.loads(data[64:64+meta]);at=64+meta+28*meshes+36*vertices+4*indices
    if at>len(data) or len(source['meshes'])!=meshes:raise ValueError('PS2 source bounds')
    hashes=[]
    for _ in range(textures):
        if at+12>len(data):raise ValueError('PS2 texture header')
        w,h,size=struct.unpack_from('<3I',data,at);at+=12
        if not w or not h or w>1024 or h>1024 or size!=w*h*4 or at+size>len(data):raise ValueError('PS2 texture bounds')
        hashes.append(digest(data[at:at+size]));at+=size
    if at!=len(data):raise ValueError('PS2 trailing bytes')
    result=[]
    for i,m in enumerate(source['meshes']):
        binary=struct.unpack_from('<7I',data,64+meta+28*i)
        if binary[1]!=m['mode'] or list(binary[2:5])!=m['texture_indices'] or binary[5]>indices or binary[6]>indices-binary[5] or binary[6]%3:raise ValueError('PS2 source/binary disagreement')
        source_slots=m.get('source_texture_slots',m.get('textures'))
        if source_slots is None:raise ValueError('PS2 source material provenance absent')
        slots={t['slot']:canonical(t['name']) for t in source_slots};mode=m['mode'];first=m['texture_indices'][0]
        if first>=len(hashes):raise ValueError('PS2 primary index')
        second=m['texture_indices'][1];secondary=hashes[second] if mode==3 and second<len(hashes) else ZERO
        result.append(dict(primary=slots.get(0,'null'),secondary=slots.get(1,'null'),primary_sha=hashes[first],secondary_sha=secondary,mode=mode,mesh=i))
    family=source.get('family')
    if not family:
        resource=source.get('source_resource','').replace('\\','/').split('/')
        if len(resource)<2:raise ValueError('PS2 source family provenance absent')
        family=resource[-2]
    return canonical(family),result,digest(data)

def export(sources,assets,output,base=None,aliases=None):
    if output.exists():raise ValueError('fresh output required')
    if not assets.is_dir():raise ValueError('PS2 source assets directory missing')
    from master_rallye.dx import parse_dx
    from master_rallye.material_semantics import MaterialSemantics
    authored=old_roles(base);records={(f,part,p,s,ZERO,ZERO,r) for (f,part,p,s),r in authored.items()};reports=[]
    def add(row,family,part,p,s,a=ZERO,b=ZERO,opaque=True):
        role,reason=role_for(p,s,part,opaque)
        if opaque and (family,part,p,s) in authored:role=authored[family,part,p,s];reason='Eligible accepted baseline material role; current source/pass proof required'
        try:policy.fixed(p,96);policy.fixed(s,96)
        except ValueError:role=0;reason='Unsupported binding identifier; native retained'
        if role:role=authored.get((family,part,p,s),role)
        row.update(primary=p,secondary=s,role=ROLES.get(role,'native'),status=reason,runtime='NOT_OBSERVED')
        if role:records.add((family,part,p,s,a,b,role))
    for root in sources:
        if not root.is_dir():raise ValueError('source missing: '+str(root))
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():continue
            for part in ('car','wheel'):
                path=folder/(part+'.dx')
                if not path.is_file():continue
                report=dict(source=str(path),family=folder.name.lower(),resource=part,source_sha256=digest(path.read_bytes()),route='NATIVE_DX',materials=[],runtime='NOT_TESTED')
                reports.append(report)
                try:
                    policy.fixed(folder.name.lower(),32);model=parse_dx(path)
                    if not model.diagnostics.validated:raise ValueError('source draw reconstruction unvalidated')
                    report['source_validated']=True
                    for draw in model.physical_draws:
                        semantics=MaterialSemantics.from_draw(draw);p,s,t=map(canonical,draw.texture_tuple);row=dict(draw=draw.record_path,alpha=semantics.alpha_mode,shader=semantics.runtime_shader_family);report['materials'].append(row)
                        supported=semantics.runtime_shader_family is not None and t=='null'
                        add(row,report['family'],part,p,s,opaque=supported and semantics.alpha_mode=='OPAQUE')
                except Exception as e:report['error']=f'{type(e).__name__}: {e}'
    aliases=aliases or {}
    for path in sorted(assets.glob('*.ps2model')):
        name=path.name.upper();part='wheel' if 'WHEEL' in name else 'car' if '-CAR' in name else None
        if part is None:continue
        report=dict(source=str(path),route='CERTIFIED_PS2_PRIVATE_ONLY',resource=part,materials=[],runtime='NOT_TESTED');reports.append(report)
        try:
            family,rows,h=ps2_bindings(path);family=aliases.get(family,family);policy.fixed(family,32);report.update(family=family,source_sha256=h,source_validated=True)
            for binding in rows:
                row=dict(binding);report['materials'].append(row);eligible=binding['mode'] in (1,3) and (binding['mode']!=3 or binding['secondary_sha']!=ZERO)
                add(row,family,part,binding['primary'],binding['secondary'],binding['primary_sha'],binding['secondary_sha'],eligible)
        except Exception as e:report['error']=f'{type(e).__name__}: {e}'
    # Never let conflicting source roles become first-match authorization.
    keys=collections.defaultdict(set)
    for f,part,p,s,a,b,r in records:keys[f,part,p,s].add(r)
    if any(len(v)!=1 for v in keys.values()):raise ValueError('native role conflict')
    data=encode(records);output.mkdir(parents=True);(output/'body.blm').write_bytes(data)
    result=dict(schema=1,format='BLM3',status='OFFLINE_SOURCE_QUALIFIED_GAMEPLAY_PENDING',records=len(records),sha256=digest(data),source_models=len(reports),families=sorted({r['family'] for r in reports if 'family'in r}),native_baseline_keys_preserved=len(authored),no_geometry_hash_allowlist=True,ps2_identity='PRIMARY_PLUS_SECONDARY_PIXELS_AND_OWNER_RESOURCE_MODE',models=reports,errors=[{k:r.get(k) for k in ('source','error')} for r in reports if 'error'in r])
    result['qualified_source_models']=sum('error' not in r for r in reports)
    result['qualified_families']=sorted({r['family'] for r in reports if 'error'not in r})
    if result['errors']:result['status']='PARTIAL_SOURCE_QUALIFICATION_GAMEPLAY_PENDING'
    (output/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rows=''.join('<tr><td>'+html.escape(r.get('family','?'))+'</td><td>'+html.escape(r['resource'])+'</td><td>'+html.escape(r['source'])+'</td><td>'+html.escape(r.get('error','OFFLINE source qualified; GAME NOT TESTED'))+'</td></tr>' for r in reports)
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Vehicle lighting SDK</title><h1>ATMOSPHERE2.9 source inventory</h1><p>Opaque candidate coverage is not runtime Lit. Transparent glass/emissive remain native; opaque glazing has a separate RGB-only role. Full per-material decisions in report.json.</p><table>'+rows+'</table>',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,action='append',required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--base',type=Path);p.add_argument('--family-aliases',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=export(a.source,a.assets,a.output,a.base,json.loads(a.family_aliases.read_text()) if a.family_aliases else None);print(json.dumps({k:r[k] for k in ('records','source_models','native_baseline_keys_preserved','errors')}))
