"""Static frontend complexity and texture quality evidence, NOT game timings."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.addon_sdk.texture_quality import plan_textures
from master_rallye.addon_sdk.texture_budget import texture_working_set


def diagnose(root, *, reference=None, quality_profile=None):
    quality=plan_textures(root,profile=quality_profile)
    models={}
    for name in ('car.dx','complete.dx','wheel.dx'):
        raw=(root/name).read_bytes();m=parse_dx_bytes(raw)
        models[name]={'sha256':hashlib.sha256(raw).hexdigest(),'file_bytes':len(raw),
            'vertices':m.vertex_count,'triangles':m.triangle_count,'physical_draws':len(m.physical_draws),
            'texture_bindings':sum(t!='Null' for d in m.physical_draws for t in d.texture_tuple),
            'bounds':{'min':[min(p[k] for p in m.vertices.positions) for k in range(3)],'max':[max(p[k] for p in m.vertices.positions) for k in range(3)]}}
    for row in quality['textures']:
        if reference:
            path=reference/row['file']
            if path.exists():
                source=parse_dxt_bytes(path.read_bytes());current=parse_dxt_bytes((root/row['file']).read_bytes())
                # Compare at corresponding nearest source pixels. This exposes
                # resolution loss; it is not a perceptual score or GT parity.
                errors=[]
                for y in range(current.height):
                    for x in range(current.width):
                        a=(y*current.width+x)*4
                        b=((y*source.height//current.height)*source.width+x*source.width//current.width)*4
                        errors.extend(abs(current.bgra[a+c]-source.bgra[b+c]) for c in range(4))
                row['reference_comparison']={'reference_size':[source.width,source.height],
                    'linear_resolution_ratio':[current.width/source.width,current.height/source.height],
                    'corresponding_sample_mae_bgra':sum(errors)/max(len(errors),1),
                    'byte_identical':(root/row['file']).read_bytes()==path.read_bytes(),
                    'boundary':'nearest corresponding pixels; reduction averaging differs intentionally, not a fidelity acceptance score'}
            else:row['reference_comparison']={'status':'NO_MATCHING_REFERENCE_FILE'}
    return {'status':'STATIC_RESOURCE_DIAGNOSTICS','models':models,'residency':texture_working_set(root),'texture_quality':quality,
        'game_timing':{'measured':False,'cold':None,'warm':None,'reentry':None},
        'boundary':'structural/image evidence only. File sizes, parser costs and cache estimates do not measure native decoding, GPU creation, synchronization or menu latency.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('assets',type=Path);p.add_argument('--reference',type=Path);p.add_argument('--quality-profile',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=diagnose(a.assets,reference=a.reference,quality_profile=json.loads(a.quality_profile.read_text()) if a.quality_profile else None)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(a.output)
