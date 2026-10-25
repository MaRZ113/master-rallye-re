"""Inspect actual converted DX reflection boundaries; optional source-informed draw selection."""
import argparse,json,sys,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.addon_sdk.reflection_continuity import audit
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx


def coverage_family(data,report,output):
    if output.exists():raise ValueError('coverage output exists')
    output.mkdir(parents=True);model=parse_dx_bytes(data);geometries=source_geometry(model);eligible=set(report['eligible_draws']);parts=[]
    colours={'reflection-green-tga':(50,210,50,255),'plain-red-tga':(40,40,230,255),'other-blue-tga':(190,70,35,255)}
    for stem,pixel in colours.items():
        raw=bytes(pixel);(output/(stem+'.dxt')).write_bytes(struct.pack('<5I',0xfeed,1,zlib.crc32(raw)&0xffffffff,1,1)+raw)
    for d in model.physical_draws:
        stem='other-blue-tga' if d.draw_index not in eligible else 'reflection-green-tga' if d.unknown_0x24&4 else 'plain-red-tga'
        parts.append(ScenePart(geometries[d.draw_index],(stem,'Null','Null')))
    (output/'car.dx').write_bytes(write_scene_dx(data,parts));(output/'complete.dx').write_bytes((output/'car.dx').read_bytes())
    (output/'legend.json').write_text(json.dumps({'green':'reflection helper enabled','red':'eligible without helper','blue':'outside selection','boundary':'Opaque diagnostic colours deliberately replace source appearance/alpha; not a fidelity render.'},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--eligible-draws',type=Path,help='optional JSON list of explicitly qualified exterior paint draw indices');p.add_argument('--coverage-dir',type=Path,help='optional NEW opaque diagnostic family; source appearance intentionally replaced');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    data=a.source.read_bytes();r=audit(data,eligible_draws=json.loads(a.eligible_draws.read_text()) if a.eligible_draws else None)
    if a.coverage_dir:coverage_family(data,r,a.coverage_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'warnings':len(r['warnings']),'reflected_area_m2':r['reflected_area_m2']}))
