"""Coverage heatmaps and seated-crew fitting views from real converted resources.

These are explicitly diagnostic resources. They are not substituted into the
runtime package. Source-role annotations come from a qualified build report.
"""
import argparse,json,struct,sys,hashlib
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.topology_writer import source_geometry,DrawGeometry
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.preview_scene import logical_cases


def plane_hit(point,tri,axis):
    other=[i for i in range(3) if i!=axis];u,v=other;x,y=point[u],point[v];a,b,c=tri
    den=(b[v]-c[v])*(a[u]-c[u])+(c[u]-b[u])*(a[v]-c[v])
    if abs(den)<1e-10:return None
    s=((b[v]-c[v])*(x-c[u])+(c[u]-b[u])*(y-c[v]))/den
    t=((c[v]-a[v])*(x-c[u])+(a[u]-c[u])*(y-c[v]))/den
    if min(s,t,1-s-t)<-1e-7:return None
    return s*a[axis]+t*b[axis]+(1-s-t)*c[axis]


def diagnose(build,output):
    output.mkdir(parents=True,exist_ok=True);report=json.loads((build/'conversion-report.json').read_text());results={}
    for name in ('car.dx','complete.dx'):
        raw=(build/'assets'/name).read_bytes();m=parse_dx_bytes(raw);gs=source_geometry(m);cases,_=logical_cases(m)
        records=[r for r in report['conversion'][name] if r['route'].startswith('MR ')]
        if name=='car.dx':records += [r for r in report['native_brakes']['off_conversion'] if r['route'].startswith('MR ')]
        record_map={i:r for i,r in enumerate(records)}
        if len(records)!=len([d for d in m.physical_draws if cases.get(d.draw_index,(0,1))[1]!=2]):raise ValueError('build record/draw mapping mismatch')
        # Case2 has no ordinary records in this map, and lies after case1.
        coverage=[];weights=[];cutaway=[];paint=[];outer=[];helmets=[];person_points={};rows=[]
        for d in m.physical_draws:
            if cases.get(d.draw_index,(0,1))[1]==2:continue
            r=record_map[d.draw_index];g=gs[d.draw_index];reflect=bool(d.unknown_0x24&4);is_paint=bool((r.get('environment') or {}).get('paint_role'));crew=r.get('component')=='crew'
            tint=(20,220,230) if is_paint else (230,180,30) if reflect else (230,100,40) if crew else (70,75,80)
            tex=parse_dxt_bytes((build/'assets'/(d.texture_tuple[0]+'.dxt')).read_bytes());pixels=bytearray(tex.bgra)
            for at in range(0,len(pixels),4):pixels[at:at+3]=bytes(reversed(tint))
            stem='debug-'+hashlib.sha256(pixels).hexdigest()[:20]+'-tga';(output/(stem+'.dxt')).write_bytes(struct.pack('<5I',0xfeed,1,0,tex.width,tex.height)+pixels)
            neutral=replace(g,vertices=tuple(replace(v,color=b'\xff'*4) for v in g.vertices))
            coverage.append(ScenePart(neutral,(stem,'Null','Null'),bool(d.flags_0x20[0]),bool(d.flags_0x20[1])))
            pixels=bytearray(tex.bgra)
            for at in range(0,len(pixels),4):pixels[at:at+3]=bytes([pixels[at+3] if reflect else 0])*3
            stem='weight-'+hashlib.sha256(pixels).hexdigest()[:20]+'-tga';(output/(stem+'.dxt')).write_bytes(struct.pack('<5I',0xfeed,1,0,tex.width,tex.height)+pixels)
            weight_g=replace(g,vertices=tuple(replace(v,color=bytes([v.color[3]])*4) for v in g.vertices))
            weights.append(ScenePart(weight_g,(stem,'Null','Null'),bool(d.flags_0x20[0]),bool(d.flags_0x20[1])))
            triangles=[[g.vertices[i].position for i in t] for t in g.triangles]
            if is_paint:paint.extend(triangles)
            if is_paint or (r['route']=='MR source-alpha' and r.get('shape') in report['profile'].get('diagnostics',{}).get('glass_shapes',[])):outer.extend(triangles)
            if crew:
                cutaway.append(ScenePart(g,d.texture_tuple,environment=reflect));person_points.setdefault(r['person'],[]).extend(v.position for v in g.vertices)
                if r['role']=='helmets':helmets.extend(v.position for v in g.vertices)
            elif r.get('shape') in report['profile'].get('diagnostics',{}).get('cockpit_shapes',[]):
                box=report['profile']['diagnostics']['cockpit_bounds'];ts=[t for t in g.triangles if all(all(box[0][k]<=g.vertices[i].position[k]<=box[1][k] for k in range(3)) for i in t)]
                if ts:
                    used=sorted({i for t in ts for i in t});remap={i:j for j,i in enumerate(used)}
                    cutaway.append(ScenePart(DrawGeometry(tuple(g.vertices[i] for i in used),tuple(tuple(remap[i] for i in t) for t in ts)),d.texture_tuple,bool(d.flags_0x20[0]),bool(d.flags_0x20[1]),reflect))
            rows.append({'draw':d.draw_index,'shape':r.get('shape'),'source_packet':r.get('source_packet'),'triangles':len(g.triangles),'reflective':reflect,'paint':is_paint,'crew':crew,
                         'coverage':(r.get('environment') or {}).get('coverage'),'texture':d.texture_tuple[0]})
        label='race' if name=='car.dx' else 'frontend'
        (output/(label+'-coverage.dx')).write_bytes(write_scene_dx(raw,coverage))
        (output/(label+'-reflection-weight.dx')).write_bytes(write_scene_dx(raw,weights))
        if cutaway:
            (output/(label+'-crew-cutaway.dx')).write_bytes(write_scene_dx(raw,cutaway))
        # Preserve all stock textures for the cutaway only, never publish them.
        for part in cutaway:
            for value in part.textures:
                if value!='Null':(output/(value+'.dxt')).write_bytes((build/'assets'/(value+'.dxt')).read_bytes())
        roof=[t for t in paint if min(p[1] for p in t)>1.1];headroom=[]
        for p in helmets:
            hits=[h for t in roof if (h:=plane_hit(p,t,1)) is not None]
            if hits:headroom.append(min(hits)-p[1])
        if headroom and min(headroom)<.015:raise ValueError('helmet/roof clearance below 15 mm')
        side={}
        for who,points in person_points.items():
            ds=[]
            for p in points:
                hits=[h for t in outer if (h:=plane_hit(p,t,0)) is not None and abs(h)>.5 and h*p[0]>0]
                if hits:ds.append(max(abs(h) for h in hits)-abs(p[0]))
            if ds and min(ds)<-.001:raise ValueError('crew exceeds source door/window envelope')
            side[who]={'tested_vertices':len(ds),'minimum_lateral_clearance_m':min(ds) if ds else None,'unsupported_vertices':len(points)-len(ds)}
        results[name]={'rows':rows,'paint_draws':sum(r['paint'] for r in rows),'paint_source_packets':len({(r['shape'],r['source_packet']) for r in rows if r['paint']}),
            'paint_triangles':sum(r['triangles'] for r in rows if r['paint']),'paint_cutout_triangles':sum(r['triangles'] for r in rows if r['paint'] and r['coverage']=='paint_cutout_floor'),
            'crew_triangles':sum(r['triangles'] for r in rows if r['crew']),'helmet_roof_min_clearance_m':min(headroom) if headroom else None,'helmet_vertices_tested':len(headroom),'lateral_envelope':side}
    result={'status':'PASS_OFFLINE_COVERAGE_AND_CREW_ENVELOPES','scenes':results,'runtime_qualified':False,
        'legend':'cyan: qualified exterior paint; amber: other existing reflective materials; orange: crew; grey: non-reflective',
        'boundary':'projected roof/side-envelope checks plus cutaways; not a full body/seat/dashboard intersection solver or gameplay evidence'}
    (output/'diagnostics.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=diagnose(a.build,a.output);print(json.dumps({k:{x:y for x,y in v.items() if x!='rows'} for k,v in result['scenes'].items()},indent=2))
