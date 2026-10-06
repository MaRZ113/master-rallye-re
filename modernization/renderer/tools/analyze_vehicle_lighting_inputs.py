"""Read-only vehicle DX lighting statistics, using the unchanged validated parser."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
from master_rallye.dx import parse_dx
from master_rallye.material_semantics import MaterialSemantics

def pearson(a,b):
    if len(a)<3 or len(a)!=len(b):return None
    ma,mb=statistics.mean(a),statistics.mean(b)
    va=sum((x-ma)**2 for x in a);vb=sum((y-mb)**2 for y in b)
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(va*vb) if va>1e-16 and vb>1e-16 else None

def directional_fit(normals,luma):
    if len(luma)<4:return None
    means=[statistics.mean(n[i] for n in normals) for i in range(3)];mean=statistics.mean(luma)
    x=[[n[i]-means[i] for i in range(3)] for n in normals];y=[v-mean for v in luma]
    rows=[[sum(n[i]*n[j] for n in x) for j in range(3)]+[sum(n[i]*v for n,v in zip(x,y))] for i in range(3)]
    for i in range(3):
        pivot=max(range(i,3),key=lambda k:abs(rows[k][i]))
        if abs(rows[pivot][i])<1e-10:return None
        rows[i],rows[pivot]=rows[pivot],rows[i];v=rows[i][i];rows[i]=[t/v for t in rows[i]]
        for j in range(3):
            if j!=i:
                v=rows[j][i];rows[j]=[a-v*b for a,b in zip(rows[j],rows[i])]
    vector=[rows[i][3] for i in range(3)];total=sum(v*v for v in y)
    if total<1e-16:return None
    residual=sum((sum(n[i]*vector[i] for i in range(3))-v)**2 for n,v in zip(x,y))
    return {'coefficients':vector,'r_squared':1-residual/total,'model':'luma = intercept + beta dot serialized_normal; heuristic only'}

def vertex_stats(positions,normals,colors):
    if not positions or len(normals)!=len(positions) or len(colors)!=len(positions)*4:raise ValueError('Mismatched vertex arrays')
    if not all(math.isfinite(x) for n in positions+normals for x in n):raise ValueError('Non-finite vertex data')
    rgba=[(colors[i+2],colors[i+1],colors[i],colors[i+3]) for i in range(0,len(colors),4)]
    luma=[(.2126*r+.7152*g+.0722*b)/255 for r,g,b,a in rgba]
    valid=[i for i,n in enumerate(normals) if sum(x*x for x in n)>1e-10]
    ns=[normals[i] for i in valid];ls=[luma[i] for i in valid]
    rgb_count=len({v[:3] for v in rgba})
    return {'vertices':len(positions),'unique_rgba':len(set(rgba)),'unique_rgb':rgb_count,
            'luma':{'min':min(luma),'max':max(luma),'mean':statistics.mean(luma),'stddev':statistics.pstdev(luma)},
            'alpha_histogram':dict(sorted(Counter(v[3] for v in rgba).items())),
            'valid_nonzero_normals':len(valid),'normal_length_range':[min(math.sqrt(sum(x*x for x in n)) for n in ns),max(math.sqrt(sum(x*x for x in n)) for n in ns)] if ns else None,
            'normal_luma_pearson':[pearson([n[i] for n in ns],ls) for i in range(3)],
            'height_luma_pearson':pearson([p[1] for p in positions],luma),
            'best_fit_direction':directional_fit(ns,ls),
            'semantic_verdict':'CONSTANT_RGB_OR_TINT_CANDIDATE' if rgb_count==1 else 'VARIABLE_VERTEX_COLOR_DOUBLE_LIGHT_RISK'}

def analyze(path,relative):
    model=parse_dx(path)
    if not model.diagnostics.validated:raise ValueError('Unvalidated DX '+relative)
    draws=[]
    for draw in model.physical_draws:
        ids=sorted(set(model.draw_global_indices(draw)))
        if not ids:continue
        semantics=MaterialSemantics.from_draw(draw)
        colors=b''.join(model.vertices.colors[i*4:i*4+4] for i in ids)
        stats=vertex_stats([model.vertices.positions[i] for i in ids],[model.vertices.normals[i] for i in ids],colors)
        draws.append({'draw_index':draw.draw_index,'triangles':draw.triangle_count,'material_family':semantics.runtime_shader_family,'diffuse_consumed':semantics.vertex_diffuse_enabled,'alpha_mode':semantics.alpha_mode,'slots':draw.texture_tuple,'flags':draw.flags_0x20.hex(),**stats})
    return {'asset':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'color_format':'D3DCOLOR AARRGGBB / little-endian BGRA','evidence_grade':'CONFIRMED_BY_ASSET_PARSER','uv_arrays':len(model.uv_sets),'triangles':model.triangle_count,'draws':draws}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('vehicle_root',type=Path);ap.add_argument('--vehicles',nargs='+',default=['Tata','Astero','KiaSportage','Pajero','Forester','Kamaz']);args=ap.parse_args()
    result={'scope':'serialized vehicle colors; not post-damage runtime VB content','assets':[]}
    for name in args.vehicles:
        if Path(name).name!=name:raise ValueError('Vehicle must be a directory name')
        for part in ('car.dx','wheel.dx'):
            p=args.vehicle_root/name/part
            if p.exists():result['assets'].append(analyze(p,f'{name}/{part}'))
    if not result['assets']:raise ValueError('No representative assets found')
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':main()
