"""Private source scenes and D3D9 evidence; source inputs always read-only."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_adapters import michelin
from master_rallye.source_scene_preview import stage_source_scene, capture_views


def run(root,output,viewer):
    output = u.output_directory(output,[root]);output.mkdir(parents=True)
    rows = []
    for archive in michelin.QUALIFIED:
        name = archive[:-4]; folder = output/name;folder.mkdir()
        assembled = michelin.assemble(root,archive,folder/'assembly/scene',tyre_choice=0)
        results = [('assembly',assembled)]
        for variant in range(4):
            results.append(('LOD%d'%variant,michelin.recover(root,archive,variant,folder/('LOD%d'%variant)/'scene')))
        for label,result in results:
            p = Path(result['scene']); scene = u.load_scene(p)
            preview = p.parent.parent/'preview.mrpv'; stage_source_scene(scene,preview,scene_root=p.parent)
            views = capture_views(viewer,preview,p.parent.parent/'views',provenance='Michelin source geometry; static neutral assembly; L2 WARN')
            rows.append({'archive':archive,'selection':label,'scene':result,'views':views})
    (output/'results.json').write_bytes(u.canonical(rows))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True)
    a=p.parse_args();run(a.source_root,a.output,a.viewer)
