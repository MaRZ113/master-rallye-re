"""Read-only compact quality/session audit. Counts never imply a human visual PASS."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

def audit(path):
    data=path.read_bytes()
    if len(data)>64*1024*1024:raise ValueError('Capture exceeds bounded audit size')
    rows=[json.loads(line) for line in data.decode('utf-8-sig').splitlines() if line.strip()]
    if not rows or rows[0].get('type') not in ('session','frame_begin'):raise ValueError('Not a renderer capture/session')
    h=rows[0];report=dict(name=path.name,sha256=hashlib.sha256(data).hexdigest(),proxy_version=h.get('proxy_version'),
                        exe_sha256=h.get('exe_sha256'),proxy_sha256=h.get('proxy_sha256'),last_record=rows[-1].get('type'),
                        evidence_grade='OBSERVED_IN_CAPTURE_NOT_VISUAL_VERDICT')
    report['frame_summaries']=sum(r.get('type')=='frame_summary' for r in rows)
    report['creates']=[dict(hresult=r.get('hresult'),effective=r.get('parameters_after')) for r in rows if r.get('type')=='create_device']
    report['successful_resets']=sum(r.get('type')=='reset' and r.get('hresult')==0 for r in rows)
    pp=[r.get('descriptor',{}).get('effective') for r in rows if r.get('type')=='quality_pipeline']
    report['effective_sizes']=sorted({(p['width'],p['height']) for p in pp if p})
    report['effective_samples']=sorted({p['multisample'] for p in pp if p})
    report['freeze']=[r for r in rows if r.get('type')=='menu_freeze_fix']
    report['requested_config']=next((r.get('requested',{}) for r in rows if r.get('type')=='renderer_config'),{})
    projections=[]
    for r in rows:
        if r.get('method')!='SetTransform' or r.get('arguments',[0])[0]!=3:continue
        bits=r.get('payload_bits',[])
        if len(bits)!=16:continue
        values=struct.unpack('<16f',struct.pack('<16I',*bits))
        if abs(values[0]-2/640)>1e-8 or abs(values[5]-2/480)>1e-8:continue
        projections.append(dict(return_rva=r.get('caller',{}).get('return_rva'),feature_mask=r.get('feature_mask'),
                                requested_equals_effective=bits==r.get('effective_payload_bits'),
                                widescreen_applied=r.get('widescreen_applied',False)))
    report['ui_projection_observations']=projections
    report['last_breadcrumb']=next((r.get('step') for r in reversed(rows) if r.get('type')=='display_breadcrumb'),None)
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('files',type=Path,nargs='+');a=ap.parse_args()
    print(json.dumps([audit(p) for p in a.files],indent=2))

if __name__=='__main__':main()
