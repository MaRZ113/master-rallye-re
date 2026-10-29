"""Build private derived Dakar2 rendering projects from immutable L1 scenes."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_adapters.dakar2 import create_scene
from master_rallye.source_adapters.dakar2_fidelity import executable_evidence,derive_scene,variant_inventory
from master_rallye.source_scene_preview import stage_source_scene,capture_views


def run(image,source,output,viewer,*,nissan=False):
    image=Path(image).absolute();source=Path(source).absolute()
    output=u.output_directory(Path(output).absolute(),[image.parent,source.parent])
    if output.exists():raise ValueError('Fresh renderer output required')
    evidence=executable_evidence(image)
    # Original L1 scene remains unchanged; a new source snapshot is generated
    # only for Nissan's now evidenced row-vector basis interpretation.
    if nissan:
        source=output/'nissan-original/scene.json'
        create_scene(image,source.parent,'NISSAN',qualified_rotations=True)
    result=derive_scene(source,output/'scene',evidence)
    scene=u.load_scene(output/'scene/scene.json')
    stage_source_scene(scene,output/'preview.mrpv',scene_root=output/'scene')
    if viewer:
        for mode in ('source','cw','ccw','none'):
            capture_views(Path(viewer).absolute(),output/'preview.mrpv',output/('views-'+mode),cull=mode,
                provenance='Dakar2 static source state research; full shader/runtime parity unresolved')
    (output/'variant-inventory.json').write_bytes(u.canonical(variant_inventory(image)))
    (output/'result.json').write_bytes(u.canonical(result));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('xbox','source','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--viewer',type=Path);p.add_argument('--nissan',action='store_true')
    a=p.parse_args();print(run(a.xbox,a.source,a.output,a.viewer,nissan=a.nissan))
