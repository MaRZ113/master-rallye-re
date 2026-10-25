"""Fixed-camera culling/material comparisons using private user DX resources.

This exercises the real Windows Previewer, not Master Rallye gameplay.
"""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.preview_scene import stage_vehicle


def capture_matrix(before,after,profile,viewer,output):
    output.mkdir(parents=True,exist_ok=False);report={'boundary':'offline D3D9 diagnostic, not gameplay','captures':[]}
    for label,family in [('before',before),('after',after)]:
        scene=output/(label+'.mrpv');stage_vehicle(family/'car.dx',scene,profile=profile)
        for variant in ('race','frontend'):
            for view,azimuth in [('front-left',-40),('front-right',40),('rear-left',-140),('rear-right',140)]:
                for cull in ('cw','ccw','none'):
                    name=f'{label}-{variant}-{view}-{cull}.bmp';cmd=[str(viewer.resolve()),'--scene',str(scene.resolve()),'--model',variant,'--azimuth',str(azimuth),'--zoom','.7','--cull',cull,'--capture',str((output/name).resolve())]
                    subprocess.run(cmd,check=True,timeout=30);report['captures'].append(name)
            for mode in ('reflection-mask','composed'):
                for reflection in (True,False):
                    name=f'{label}-{variant}-{mode}-env{int(reflection)}.bmp';cmd=[str(viewer.resolve()),'--scene',str(scene.resolve()),'--model',variant,'--azimuth','40','--zoom','.7','--material-mode',mode,'--capture',str((output/name).resolve())]
                    if not reflection:cmd.append('--no-reflections')
                    subprocess.run(cmd,check=True,timeout=30);report['captures'].append(name)
    report['status']='PASS_WINDOWS_CAPTURE_MATRIX';(output/'validation.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('before','after','profile','viewer','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();r=capture_matrix(**vars(a));print(r['status'],len(r['captures']))
