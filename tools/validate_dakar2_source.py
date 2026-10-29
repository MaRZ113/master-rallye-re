"""Owner-local deterministic Dakar2 recovery, channels and neutral diagnostics.

Two source scenes only. No native integration or source-game execution. Images
are diagnostic and L2 stays WARN until original culling behavior is qualified.
"""
from pathlib import Path
import argparse
import json
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as uvs
from master_rallye.source_adapters.dakar2 import create_scene
from master_rallye.source_scene_preview import stage_source_scene,capture_views

def validate(image,output,viewer):
    image=Path(image).absolute();output=uvs.output_directory(Path(output).absolute(),[image.parent,image.parent.parent]);viewer=Path(viewer).absolute()
    if output.exists():raise ValueError('Fresh validation output required')
    reports={}
    for vehicle in('PAJERO','HINO'):
        root=output/vehicle;report=create_scene(image,root/'scene',vehicle);scene=uvs.load_scene(root/'scene/scene.json')
        repeated=create_scene(image,output/'repeat'/vehicle,vehicle)
        if (report['scene_sha256'],report['manifest_sha256'])!=(repeated['scene_sha256'],repeated['manifest_sha256']):raise ValueError('nondeterministic scene')
        manifest=json.loads((root/'scene/manifest.json').read_text())
        for name,row in manifest['files'].items():
            if (root/'scene'/name).read_bytes()!=(output/'repeat'/vehicle/name).read_bytes():raise ValueError('sidecar regeneration differs')
        # Check original bytes for every retained source stream, including packed
        # normals, vertex colors and UV1 which the neutral renderer does not apply.
        original={r['member']:(root/'scene'/r['snapshot_path']).read_bytes()for r in scene['source']['resources']}
        stream_count=0
        for mesh in scene['meshes']:
            source=mesh['source'];resource=original[source['member']]
            for row in source['streams'].values():
                raw=(root/'scene'/row['path']).read_bytes()
                if raw!=resource[row['offset']:row['offset']+len(raw)]or uvs.sha(raw)!=row['sha256']:raise ValueError('source stream changed')
                stream_count+=1
        stage_source_scene(scene,root/'normalized.mrpv',scene_root=root/'scene')
        captures={}
        for cull in('cw','ccw','none'):
            captures[cull]=capture_views(viewer,root/'normalized.mrpv',root/('views-'+cull),cull=cull,
                provenance='Original Dakar2 rest assembly; '+cull+' DIAGNOSTIC; runtime culling unresolved')
        report.update(deterministic_repeat=True,source_streams_exact=stream_count,captures=captures,
                      l0='PASS',l1='PASS_STRUCTURAL_RECOVERY',l2='WARN_MIXED_FACING_SOURCE_CULLING_UNRESOLVED',gameplay='NOT TESTED')
        reports[vehicle]=report;print(vehicle,report['counts'],flush=True)
    (output/'validation.json').write_bytes(uvs.canonical(reports));return reports

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('xbox','output','viewer'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();validate(args.xbox,args.output,args.viewer)
