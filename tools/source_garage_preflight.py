"""Read-only UVS/native boundary report with explicit authoring-policy selection."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_qualification import preflight

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--profile',type=Path);p.add_argument('--semantics',type=Path)
    a=p.parse_args();s=u.load_scene(a.scene)
    protected=[a.scene.parent,Path(s['source']['root']),*map(Path,s['source'].get('protected_roots',[]))]
    protected.extend(path for path in (a.profile,a.semantics)if path is not None)
    out=u.output_directory(a.output,protected)
    profile=u.load_json(u.read_bounded(a.profile,u.MAX_JSON_BYTES))if a.profile else None
    semantics=u.load_json(u.read_bounded(a.semantics,u.MAX_JSON_BYTES))if a.semantics else None
    report=preflight(a.scene,profile=profile,semantics=semantics)
    out.mkdir(parents=True);(out/'preflight.json').write_bytes(u.canonical(report))
    print(report['levels']);print(out/'preflight.json')
