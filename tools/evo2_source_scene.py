"""Inspect, reconstruct or preview the qualified Evo2 source scene; no MR build."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from master_rallye.source_adapters.evo2 import create_scene,inspect_source
from master_rallye.universal_vehicle_scene import load_scene,validate_scene,output_directory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    inspect=commands.add_parser('inspect');inspect.add_argument('--source-root',type=Path,required=True)
    create=commands.add_parser('create');create.add_argument('--source-root',type=Path,required=True)
    create.add_argument('--output',type=Path,required=True);create.add_argument('--wheel-detail',choices=('08','12','16'),default='16')
    create.add_argument('--config',type=Path)
    reopen=commands.add_parser('validate');reopen.add_argument('--scene',type=Path,required=True)
    preview=commands.add_parser('preview');preview.add_argument('--scene',type=Path,required=True)
    preview.add_argument('--output',type=Path,required=True)
    preview.add_argument('--viewer',type=Path,default=ROOT/'.research-output/vehicles/previewer/build/Release/mr-vehicle-previewer.exe')
    preview.add_argument('--basis',choices=('source','normalized'),default='normalized')
    preview.add_argument('--material-mode',choices=('original','interpreted','material_ids'),default='original')
    preview.add_argument('--all-source-objects',action='store_true');preview.add_argument('--capture-views',action='store_true')
    args=parser.parse_args()
    if args.command=='inspect':result=inspect_source(args.source_root)
    elif args.command=='create':result=create_scene(args.source_root,args.output,wheel_detail=args.wheel_detail,config_path=args.config)
    elif args.command=='validate':result={'status':'PASS','counts':validate_scene(load_scene(args.scene))}
    else:
        from master_rallye.source_scene_preview import stage_source_scene,capture_views,viewer_command
        from master_rallye.source_adapters.evo2 import _protected
        scene=load_scene(args.scene)
        output_directory(args.output,_protected(scene['source']['root']))
        args.output.mkdir(parents=True,exist_ok=False)
        staged=args.output/'scene.mrpv'
        result=stage_source_scene(scene,staged,scene_root=args.scene.parent,basis=args.basis,
                                  material_mode=args.material_mode,visibility='source'if args.all_source_objects else'selected')
        if args.capture_views:result['captures']=capture_views(args.viewer,staged,args.output/'views',basis=args.basis)
        else:subprocess.Popen(viewer_command(args.viewer,staged,basis=args.basis),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
