"""Owner-local TC -> Universal Vehicle Scene -> neutral D3D9; no MR build."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye.source_adapters.paris_dakar import QUALIFIED, create_scene
from master_rallye.universal_vehicle_scene import load_scene
from master_rallye.source_scene_preview import stage_source_scene, capture_views, preview_cull


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--catalog',choices=tuple(QUALIFIED),default='PajeroRED.tc')
    p.add_argument('--output',type=Path,required=True,help='Fresh private output; never include it in source archives')
    p.add_argument('--viewer',type=Path,help='Existing D3D9 previewer; enables six fixed captures')
    a=p.parse_args()
    result=create_scene(a.source_root,a.output,a.catalog)
    root=a.output.absolute();scene=load_scene(root/'scene.json')
    for basis in ('source','normalized'):
        path=root/'preview'/(basis+'.mrpv')
        stage_source_scene(scene,path,scene_root=root,basis=basis)
        if a.viewer:
            capture_views(a.viewer.absolute(),path,root/('captures-'+basis),basis=basis,cull=preview_cull(scene),
                          provenance=a.catalog+' | source reconstruction | static attach datum | neutral D3D9')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
