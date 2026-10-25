"""Inspect exported external meshes without model-number/material-role guesses.

Writes source-only diffuse diagnostics, never a deployable MR vehicle. Input
meshes and accompanying textures remain private caller-owned resources.
"""
import argparse,dataclasses,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.external_source import inspect_obj,digest
import vmesh_raster as raster
from generate_vehicle_ui_previews import frame_camera

def inspect(root,out,body):
    if out.exists():raise ValueError('output exists')
    out.mkdir(parents=True);models={p.name:inspect_obj(p) for p in sorted(root.glob('*.obj'))}
    (out/'source-report.json').write_text(json.dumps({'models':models,'source_yaml_sha256':digest(root/'model_set.yaml'),'runtime_material_passes':'UNQUALIFIED; source YAML commands retained at input, no numeric-prefix routing'},indent=2))
    items=raster.load_gt_obj(root/body,lambda p:(p[0],p[1],-p[2]));opaque=[]
    for item in items:
        texture=item.texture
        if texture:
            w,h,p=texture;p=bytearray(p);p[3::4]=bytes([255])*(w*h);texture=(w,h,bytes(p))
        opaque.append(dataclasses.replace(item,texture=texture,blend=False,alpha_test=False))
    points=[p for i in opaque for t in i.tris for p in t[:3]];centre=tuple((min(p[k] for p in points)+max(p[k] for p in points))/2 for k in range(3))
    for name,az,el in [('front',180,5),('rear',0,5),('side',-90,0),('three-quarter',138,10)]:
        camera=raster.Camera(az,el,1,centre,7 if name=='three-quarter' else None);frame_camera(points,camera,640,400,20)
        rgb=raster.render(opaque,camera,640,400);(out/(name+'.png')).write_bytes(raster.png_rgb(640,400,rgb))
    (out/'index.html').write_text('<h1>Source-only diffuse diagnostics</h1><p>Texture RGB with forced opaque preview alpha. No GT4 render-state emulation, assembled wheels, MR DX conversion or runtime qualification is claimed.</p>'+''.join(f'<h2>{name}</h2><img src="{name}.png">' for name in ('front','rear','side','three-quarter')))
    return {'status':'SOURCE_INSPECTED_NOT_RUNTIME_CANDIDATE','models':{k:{'triangles':v['triangles'],'materials':len(v['materials'])} for k,v in models.items()}}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--body',default='model0.obj');p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(inspect(a.source_root,a.output,a.body),indent=2))
