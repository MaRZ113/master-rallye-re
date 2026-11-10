"""Generate optional exact-source lamp attachments; never edit installed assets.

Only missing ordinary rig lens anchors are considered. Passive main geometry
must duplicate an evidenced blight switch lens triangle; nearby body panels and
glow billboards never qualify. All barycentric authoring and motion checks run
the current C++ renderer implementation, not a Python geometry approximation.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, re, struct, subprocess, sys
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]

def sha(data): return hashlib.sha256(data).hexdigest()

def uv_bytes(values):
    out=bytearray()
    for uv in values:
        for value in uv:
            if not math.isfinite(value): raise ValueError('nonfinite UV')
            out.extend(struct.pack('<f',0.0 if value==0 else value))
    return bytes(out)

def triangle_key(points):
    return tuple(sorted(tuple(round(v,5) for v in p) for p in points))

def texture_identities(raw):
    if not raw or len(raw)%4:raise ValueError('invalid BGRA data')
    opaque=bytearray(raw);opaque[3::4]=b'\xff'*(len(opaque)//4)
    return sorted({sha(raw),sha(opaque)})

def parse_rigs(data):
    rigs={};current=None
    for line in data.decode('ascii').splitlines():
        p=line.split()
        if not p or p[0].startswith('#'):continue
        if p[0]=='car':
            if len(p)!=2 or not re.fullmatch(r'[A-Za-z0-9_-]{1,63}',p[1]) or p[1] in rigs:raise ValueError('invalid/duplicate car')
            current=rigs.setdefault(p[1],dict(textures=set(),points=[]))
        elif p[0]=='draw':
            if current is None:raise ValueError('draw before car')
            current['textures'].add(p[1].lower())
        elif p[0]=='point':
            if current is None or len(p)!=8:raise ValueError('invalid point')
            position=tuple(map(float,p[2:5]));kind=int(p[1])
            if kind not in range(5) or not all(math.isfinite(v) for v in position):raise ValueError('invalid point values')
            current['points'].append(dict(kind=kind,position=position))
    return rigs

def switch_role(draw, roots):
    path=str(draw.record_path);texture=draw.texture_tuple[0].lower()
    if 'glow' in texture:return None
    if any(path==root or path.startswith(root+'.') for root in roots):
        return 'on' if 'lightson' in texture else 'off'
    return 'main'

def select_modes(candidates,tolerance=.0004):
    """Require a real candidate in each visibility state; keep near-best ones."""
    selected={}
    for mode in ('off','on'):
        eligible=[c for c in candidates if c['role'] in ('main',mode)]
        if not eligible:raise ValueError('no certified '+mode+' attachment')
        best=min(c['anchor']['distance'] for c in eligible)
        for c in eligible:
            if c['anchor']['distance']<=best+tolerance:
                key=c['record'];selected.setdefault(key,dict(c,modes=[]))['modes'].append(mode)
    return list(selected.values())

def compile_probe(output,vcvars):
    helper=PORT/'tools/atmosphere_lamp_attachments_probe.cpp';exe=output/'attachments_probe.exe'
    command='call "'+str(vcvars)+'" x64_x86\ncl /nologo /std:c++17 /EHsc /O2 /MT /fp:strict /I "'+str(PORT/'renderer')+'" "'+str(helper)+'" /Fe:"'+str(exe)+'" /Fo:"'+str(output/'attachments_probe.obj')+'"\n'
    script=output/'compile.cmd';script.write_text(command)
    subprocess.run(['cmd','/d','/c',str(script)],check=True,capture_output=True,text=True)
    return exe

def run_probe(exe,cases,fixture):
    with fixture.open('w') as f:
        f.write(str(len(cases))+'\n')
        for case in cases:
            f.write(' '.join(map(str,(len(case['positions']),int(case['point']['kind'] in (0,4)),*case['point']['position'])))+'\n')
            for p in case['positions']:f.write(' '.join(map(str,p))+'\n')
    with fixture.open() as f:result=subprocess.run([str(exe)],stdin=f,capture_output=True,text=True,check=True)
    lines=result.stdout.splitlines()
    if len(lines)!=len(cases):raise ValueError('oracle result count')
    results=[]
    for line in lines:
        p=line.split()
        if p==['0']:results.append(None);continue
        if len(p)!=12 or p[0]!='1':raise ValueError('oracle format')
        anchor=dict(triangle=int(p[1]),weights=list(map(float,p[2:5])),offset=float(p[5]),sign=float(p[6]),distance=float(p[7]),translation_error=float(p[8]),rotation_error=float(p[9]),damage_error=float(p[10]),collapsed_rejected=p[11]=='1')
        if max(anchor[k] for k in ('translation_error','rotation_error','damage_error'))>1e-5 or not anchor['collapsed_rejected']:raise ValueError('oracle motion check failed')
        results.append(anchor)
    fixture.with_suffix('.results.txt').write_text(result.stdout)
    return results

def encode_rows(rig_data,rows):
    for row in rows:
        if len(row)!=12:raise ValueError('invalid attachment row size')
        car,point,texture,uv,vertices,triangle,*numbers=row
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,63}',car) or point<0 or not all(re.fullmatch('[0-9a-f]{64}',x) for x in (texture,uv)):raise ValueError('invalid attachment identity')
        if vertices<=0 or vertices%3 or triangle<0 or triangle>=vertices//3 or not all(math.isfinite(v) for v in numbers):raise ValueError('invalid attachment geometry')
        weights=numbers[:3];offset,sign,distance=numbers[3:]
        if min(weights)<-1e-6 or abs(sum(weights)-1)>1e-5 or not 0<=offset<=.060001 or sign not in (-1,1) or not 0<=distance<.0625:raise ValueError('invalid attachment anchor')
    payload=(''.join(' '.join(map(str,row))+'\n' for row in sorted(set(rows)))).encode('ascii')
    return ('LPA1 '+sha(rig_data)+' '+sha(payload)+'\n').encode('ascii')+payload

def generate(source,rig_path,output,parser_root,vcvars):
    sys.path.insert(0,str(parser_root))
    from master_rallye.dx import parse_dx
    from master_rallye.dxt import parse_dxt
    output.mkdir(parents=True,exist_ok=True);rig_data=rig_path.read_bytes();rigs=parse_rigs(rig_data);exe=compile_probe(output,vcvars)
    models={};missing_sources=[];ordinary=[];sources={}
    for car,rig in rigs.items():
        path=source/car/'car.dx'
        if not path.is_file():missing_sources.append(car);continue
        model=parse_dx(path);sources[car]=dict(path=str(path),sha256=sha(path.read_bytes()));draws=[]
        for draw in model.physical_draws:
            ix=model.draw_global_indices(draw)
            if ix:draws.append(dict(draw=draw,positions=[model.vertices.positions[i] for i in ix],indices=ix))
        models[car]=(model,draws)
        for point_index,point in enumerate(rig['points']):
            for d in draws:
                if d['draw'].texture_tuple[0].lower() in rig['textures']:
                    ordinary.append(dict(car=car,point_index=point_index,point=point,**d))
    ordinary_results=run_probe(exe,ordinary,output/'ordinary-fixture.txt')
    bound={(c['car'],c['point_index']) for c,a in zip(ordinary,ordinary_results) if a}
    missing=[(car,i,point) for car,rig in rigs.items() if car in models for i,point in enumerate(rig['points']) if (car,i) not in bound]
    cases=[]
    for car,i,point in missing:
        model,draws=models[car];roots=[str(d.group_label and d.record_path) for d in model.physical_draws if d.group_label=='blight']
        reference=set()
        for d in draws:
            if switch_role(d['draw'],roots) in ('on','off'):
                reference.update(triangle_key(d['positions'][j:j+3]) for j in range(0,len(d['positions']),3))
        for d in draws:
            role=switch_role(d['draw'],roots)
            if role is None:continue
            if role=='main' and not any(triangle_key(d['positions'][j:j+3]) in reference for j in range(0,len(d['positions']),3)):continue
            cases.append(dict(car=car,point_index=i,point=point,role=role,reference=reference,**d))
    anchors=run_probe(exe,cases,output/'attachments-fixture.txt');by_point=collections.defaultdict(list)
    for case,anchor in zip(cases,anchors):
        if not anchor:continue
        at=anchor['triangle']*3
        if triangle_key(case['positions'][at:at+3]) not in case['reference']:continue
        by_point[case['car'],case['point_index']].append(dict(case,record=str(case['draw'].record_path),anchor=anchor))
    rows=[];selected=[];texture_sources={}
    for car,i,point in missing:
        for candidate in select_modes(by_point[car,i]):
            model,_=models[car];draw=candidate['draw'];texture=draw.texture_tuple[0].lower();texture_path=source/car/(texture+'.dxt')
            decoded=parse_dxt(texture_path)
            texture_sources[str(texture_path)]=sha(texture_path.read_bytes());identities=texture_identities(decoded.bgra)
            uv=sha(uv_bytes(model.uv_sets[0].values[j] for j in candidate['indices']));a=candidate['anchor']
            for texture_sha in identities:rows.append((car,i,texture_sha,uv,len(candidate['positions']),a['triangle'],*a['weights'],a['offset'],a['sign'],a['distance']))
            selected.append(dict(car=car,point=i,kind=point['kind'],record=candidate['record'],texture=texture,texture_identities=identities,uv_sha256=uv,expanded_vertices=len(candidate['positions']),role=candidate['role'],modes=candidate['modes'],anchor=a,semantic_proof='EXACT_SWITCH_LENS_TRIANGLE_DUPLICATE' if candidate['role']=='main' else 'NATIVE_BLIGHT_SWITCH_LENS'))
    data=encode_rows(rig_data,rows);(output/'lamp_attachments.lpa').write_bytes(data)
    report=dict(schema=1,status='OFFLINE_ORIGINAL_GEOMETRY_VALIDATED_NOT_GAMEPLAY',rig_path=str(rig_path),rig_sha256=sha(rig_data),header_sha256=sha((PORT/'renderer/atmosphere_lamp_surface.hpp').read_bytes()),helper_sha256=sha((PORT/'tools/atmosphere_lamp_attachments_probe.cpp').read_bytes()),sidecar_sha256=sha(data),source_root=str(source),parser_root=str(parser_root),parser_sha256=sha((parser_root/'master_rallye/dx.py').read_bytes()),original_models_available=len(list(source.glob('*/car.dx'))),models_validated=len(models),missing_sources=missing_sources,ordinary_points_bound=len(bound),attachment_points=len(missing),rows=len(set(rows)),off_points=sum(any(c['car']==car and c['point']==i and 'off' in c['modes'] for c in selected) for car,i,_ in missing),on_points=sum(any(c['car']==car and c['point']==i and 'on' in c['modes'] for c in selected) for car,i,_ in missing),selected=selected,sources=sources,texture_sources=texture_sources)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--rig',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--parser-root',type=Path,required=True);p.add_argument('--vcvars',type=Path,default=Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'));a=p.parse_args()
    report=generate(a.source,a.rig,a.output,a.parser_root,a.vcvars);print(json.dumps({k:v for k,v in report.items() if k not in ('selected','sources','texture_sources')},indent=2))
