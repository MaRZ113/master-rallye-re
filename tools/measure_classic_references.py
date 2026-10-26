"""Read-only, class-specific stock MR measurements; no universal polygon cap."""
import argparse,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes
from master_rallye.assets import AssetResolver
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.vehicle_physics_binding import RETAIL_FAMILY_CATALOG


def measure(folder):
    models={};textures={};resolver=AssetResolver(folder)
    for role in ('car.dx','complete.dx','wheel.dx'):
        raw=(folder/role).read_bytes();m=parse_dx_bytes(raw)
        if not m.diagnostics.validated:raise ValueError('Unqualified DX: '+str(folder/role))
        states={}
        for d in m.physical_draws:
            key='blend+test'if all(d.flags_0x20[:2])else'blend'if d.flags_0x20[0]else'cutout'if d.flags_0x20[1]else'opaque-env'if d.unknown_0x24&4 else'opaque-diffuse'
            states[key]=states.get(key,0)+1
            for stem in d.texture_tuple:
                if stem=='Null':continue
                path=resolver.resolve_texture(stem)
                if path is None:raise ValueError('Missing reference texture '+stem)
                if path.name not in textures:
                    t=parse_dxt_bytes(path.read_bytes());textures[path.name]={'size':[t.width,t.height],'cache_bytes':t.width*t.height*4,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        models[role]={'sha256':hashlib.sha256(raw).hexdigest(),'vertices':m.vertex_count,'triangles':m.triangle_count,'draws':len(m.physical_draws),'states':states}
    return {'models':models,'texture_count':len(textures),'texture_cache_bytes':sum(t['cache_bytes']for t in textures.values()),'textures':textures}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retail-root',type=Path,required=True);p.add_argument('--subaru',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report={'class_evidence':'existing retail initializer catalog / stock-ai-pools.json: ordinary T1 IDs0..6, T2 IDs7..13, T3 IDs14..20','vehicles':{},'ranges':{},'unavailable':[]}
    for entry in RETAIL_FAMILY_CATALOG:
        if entry.type_id>20:continue
        cls='T1'if entry.type_id<7 else'T2'if entry.type_id<14 else'T3'
        folder=a.retail_root/'DataGx/Vehicles'/entry.family
        try:report['vehicles'][entry.family]={'class':cls,**measure(folder)}
        except (ValueError,FileNotFoundError)as e:report['unavailable'].append({'family':entry.family,'error':str(e)})
    for cls in ('T1','T2','T3'):
        rows=[v for v in report['vehicles'].values()if v['class']==cls];summary={'sample_count':len(rows)}
        for role in ('car.dx','complete.dx','wheel.dx'):
            summary[role]={}
            for key in ('triangles','draws','vertices'):
                values=[r['models'][role][key]for r in rows];summary[role][key]={'min':min(values),'median':statistics.median(values),'max':max(values)}
        for key in ('texture_count','texture_cache_bytes'):
            values=[r[key]for r in rows];summary[key]={'min':min(values),'median':statistics.median(values),'max':max(values)}
        report['ranges'][cls]=summary
    report['subaru_frozen']=measure(a.subaru);report['policy']='Observed distributions, not limits. State roles derive from native flags; semantic paint classification needs separate source evidence. Cache charge width*height*4, not measured FPS.'
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['ranges'],indent=2))


if __name__=='__main__':main()
