"""Small private spare-node probe; deliberately stops before wheel-back authoring."""
from pathlib import Path
from copy import deepcopy
import argparse
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.pajero_spare_probe import inspect, overlay
from master_rallye.pajero_livery_forensics import SOURCE_SCENE_SHA
from master_rallye.source_scene_preview import stage_source_scene,capture_views


def run(source,output,viewer):
    source=Path(source).absolute();raw=u.read_bounded(source,u.MAX_JSON_BYTES)
    if u.sha(raw)!=SOURCE_SCENE_SHA:raise ValueError('Qualified original Xbox scene required')
    s=u.load_scene(source);output=u.output_directory(output,[source.parent,*map(Path,s['source'].get('protected_roots',[]))])
    output.mkdir(parents=True)
    assets={name:u.read_bounded(source.parent/name,u.MAX_OUTPUT_BYTES)for name in json.loads((source.parent/'manifest.json').read_text())['files']if name!='scene.json'}
    report=inspect(s);report['source_scene_sha256']=u.sha(raw)
    derived=overlay(s,True)
    assert overlay(s,False)==s and derived['meshes']==s['meshes'] and derived['materials']==s['materials'] and derived['textures']==s['textures']
    for label,scene in [('A',s),('B-derived-spare',derived)]:
        result=u.save_scene(scene,output/label/'scene',assets,protected_roots=[source.parent])
        p=Path(result['scene']);preview=p.parent.parent/'preview.mrpv'
        stage_source_scene(u.load_scene(p),preview,scene_root=p.parent)
        capture_views(viewer,preview,p.parent.parent/'views',provenance='Original Xbox / optional authored rear spare; L2 WARN')
    close=deepcopy(s)
    for n in close['nodes']:
        # Retain visible ancestor frames; isolate by explicit draw membership.
        n['visible']=True
        if n['name']!='PAJ_FL_WHEEL':n['mesh_ids']=[]
    stage_source_scene(close,output/'wheel-closeup.mrpv',scene_root=source.parent)
    capture_views(viewer,output/'wheel-closeup.mrpv',output/'wheel-closeup',provenance='Original wheel component; no backing cap, renderer WARN')
    report['reversible']=True;report['geometry_material_texture_arrays_unchanged']=True
    report['derived_node']=derived['nodes'][-1]
    (output/'probe.json').write_bytes(u.canonical(report))
    if u.sha(u.read_bounded(source,u.MAX_JSON_BYTES))!=SOURCE_SCENE_SHA:raise ValueError('Original changed')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True)
    a=p.parse_args();run(a.source,a.output,a.viewer)
