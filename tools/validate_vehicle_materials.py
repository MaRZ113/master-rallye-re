"""Compare a private material revision against its qualified geometry baseline.

This audits actual DX/DXT resources, not screenshot similarity. No retail or
GT fixtures are distributed. Native brake semantics are validated separately
from the legacy physical-record parser.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.addon_sdk.native_brakes import validate_brake_scene


def sha(data):return hashlib.sha256(data).hexdigest()


def triangles(model,draws=None):
    result=Counter()
    for draw in model.physical_draws if draws is None else draws:
        ids=model.draw_global_indices(draw)
        for at in range(0,len(ids),3):
            corners=[]
            for i in ids[at:at+3]:
                corners.append((model.vertices.positions[i],model.vertices.normals[i],
                    model.vertices.colors[i*4:i*4+4],tuple(uv.values[i] for uv in model.uv_sets)))
            result[min(tuple(corners[n:]+corners[:n]) for n in range(3))]+=1
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','candidate','baseline-project','candidate-project','donor','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();checks={};report=json.loads((a.candidate/'conversion-report.json').read_text())
    old=json.loads((a.baseline/'conversion-report.json').read_text())
    for name in ('complete.dx','car.dx','wheel.dx'):
        before=(a.baseline/'assets'/name).read_bytes();after=(a.candidate/'assets'/name).read_bytes()
        x=parse_dx_bytes(before);y=parse_dx_bytes(after);cx=triangles(x);cy=triangles(y)
        missing=sum((cx-cy).values());added=sum((cy-cx).values())
        crew_added=sum(r.get('triangles',0) for r in report['conversion'][name] if r.get('component')=='crew')-sum(r.get('triangles',0) for r in old['conversion'][name] if r.get('component')=='crew')
        brake_added=(report.get('native_brakes',{}).get('lit_triangles',0)+report.get('native_brakes',{}).get('glow_triangles',0)) if name=='car.dx' and not old.get('native_brakes') else 0
        if missing or added!=crew_added+brake_added:raise ValueError('geometry/normal/UV/colour regression: '+name)
        if name=='wheel.dx' and before!=after:raise ValueError('wheel bytes changed')
        if before[x.collision.offset:x.collision.end_offset]!=after[y.collision.offset:y.collision.end_offset]:raise ValueError('collision changed')
        checks[name]={'missing_baseline_triangles':missing,'added_triangles':added,'sha256':sha(after),
            'unchanged_collision':True,'identical_bytes':before==after}
    if (a.baseline/'preview-profile.json').read_bytes()!=(a.candidate/'preview-profile.json').read_bytes():raise ValueError('wheel instances changed')
    immutable={}
    for folder in ('physics','ui','artwork'):
        xs={p.relative_to(a.baseline_project).as_posix():sha(p.read_bytes()) for p in (a.baseline_project/folder).rglob('*') if p.is_file() and (folder!='ui' or p.suffix=='.png')}
        ys={p.relative_to(a.candidate_project).as_posix():sha(p.read_bytes()) for p in (a.candidate_project/folder).rglob('*') if p.is_file() and (folder!='ui' or p.suffix=='.png')}
        if xs!=ys:raise ValueError('unchanged project resources changed: '+folder)
        immutable[folder]=xs
    native=validate_brake_scene((a.donor/'car.dx').read_bytes(),(a.candidate/'assets/car.dx').read_bytes())
    m=parse_dx_bytes((a.candidate/'assets/car.dx').read_bytes());lit=[m.physical_draws[i] for i in native['case2_draws'][:-1]]
    glow=m.physical_draws[native['glow_draw']];gv=[m.vertices.positions[i] for i in m.draw_global_indices(glow)]
    gn=[m.vertices.normals[i] for i in m.draw_global_indices(glow)]
    lv=[m.vertices.positions[i] for d in lit for i in m.draw_global_indices(d)]
    offset=report['native_brakes']['halo_offset_m']
    if len(gv)!=len(lv) or any(math.dist(g,tuple(v[k]+n[k]*offset for k in range(3)))>1e-6 for g,n,v in zip(gv,gn,lv)):raise ValueError('halo geometry expanded beyond source lens offset')
    gt=parse_dxt_bytes((a.candidate/'assets'/(glow.texture_tuple[0]+'.dxt')).read_bytes());xoff=0;outside=0
    for draw in lit:
        t=parse_dxt_bytes((a.candidate/'assets'/(draw.texture_tuple[0]+'.dxt')).read_bytes())
        for y in range(t.height):
            for x in range(t.width):
                if not t.bgra[(y*t.width+x)*4+3] and gt.bgra[(y*gt.width+xoff+x)*4+3]:outside+=1
        xoff+=t.width
    if outside:raise ValueError('halo alpha outside source lens mask')
    env={}
    for name in ('complete.dx','car.dx'):
        records=list(report['conversion'][name]);previous=old['conversion'][name]
        if name=='car.dx':records+=report['native_brakes']['off_conversion']
        count=lambda rs:sum(bool(r.get('environment')) and r.get('component')=='body' for r in rs)
        proofs=Counter(r['environment'].get('coverage','legacy_exact_pair') for r in records if r.get('environment') and r.get('component')=='body')
        decals=[r for r in records if r.get('depth_safe_window_decal')]
        if not decals or any(r['route']!='MR cutout' for r in decals):raise ValueError('depth-safe window decal policy absent')
        env[name]={'baseline_body_draws':count(previous),'candidate_body_draws':count(records),'source_coverage_proofs':dict(proofs),
            'depth_safe_window_decals':[r['shape'] for r in decals],
            'blended_body_shapes':sorted({r['shape'] for r in records if r['route']=='MR source-alpha' and r.get('component')=='body'})}
        if count(records)<=count(previous):raise ValueError('no source-qualified body reflection improvement')
    nonpaint={}
    for name in ('complete.dx','car.dx'):
        x=parse_dx_bytes((a.baseline/'assets'/name).read_bytes());y=parse_dx_bytes((a.candidate/'assets'/name).read_bytes())
        rs=[r for r in report['conversion'][name] if r['route'].startswith('MR ')];paint=set();crew=set()
        for i,r in enumerate(rs):
            if (r.get('environment') or {}).get('paint_role'):paint.update(triangles(y,[y.physical_draws[i]]))
            if r.get('component')=='crew':crew.add(i)
        if not paint:continue
        def states(m,skip):
            result=Counter()
            for d in m.physical_draws:
                if d.draw_index in skip:continue
                ts=triangles(m,[d]);hits=sum(k in paint for k in ts)
                if hits==len(ts):continue
                if hits:raise ValueError('ambiguous mixed paint/nonpaint draw')
                result[(tuple(sorted(ts.items())),d.flags_0x20,d.unknown_0x24,d.texture_tuple)]+=1
            return result
        before=states(x,set());after=states(y,crew)
        if before!=after:raise ValueError('non-paint material or geometry regression: '+name)
        nonpaint[name]={'unchanged_draws':sum(before.values()),'glass_decals_lights_and_other_nonpaint_materials_identical':True}
    result={'status':'PASS_MATERIAL_REVISION_WITH_DOCUMENTED_APPROXIMATIONS','geometry':checks,'wheel_instances_unchanged':True,
        'immutable_project_resources':immutable,'native_brakes':native,'halo_alpha_outside_source_mask':outside,
        'halo_source_offset_m':offset,'reflection_coverage':env,'nonpaint_regression':nonpaint,'runtime_qualified':False,
        'limitations':['depth-safe sticker cutouts quantize soft edges','MR environment helper approximates GT4 texgen/lighting',
            'reflective cutout coverage and reflection alpha share one MR channel; damage fading is approximate there']}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('immutable_project_resources','native_brakes')},indent=2))


if __name__=='__main__':main()
