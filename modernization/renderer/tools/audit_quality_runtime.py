"""Read-only compact quality/session audit. Counts never imply a human visual PASS."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

def display_lifecycle(rows):
    """Pair readiness with completed native attempts; never infer a visual fix."""
    pending={};lost=[];admissions=[];messages=[]
    for r in rows:
        kind=r.get('type');device=r.get('device_lifetime_id')
        if kind=='windowed_resize_admission':
            admissions.append({k:r.get(k) for k in ('event_sequence','device_lifetime_id','requested','normalized_logical',
                'actual_client_width','actual_client_height','decision','initial_window_commit_complete','accepted_target_source',
                'effective_backbuffer_width','effective_backbuffer_height')})
        elif kind=='display_window_message':
            messages.append({k:r.get(k) for k in ('event_sequence','device_lifetime_id','phase','message','style_old','style_new','window_context')})
        elif kind=='display_reset_readiness' and device is not None:pending[device]=r
        elif kind=='display_native_attempt' and r.get('operation')=='Reset' and device is not None:
            ready=pending.pop(device,None)
            if ready and ready.get('cooperative_hresult')==0x88760868:
                lost.append(dict(device_lifetime_id=device,readiness_sequence=ready.get('event_sequence'),
                    reset_sequence=r.get('event_sequence'),native_hresult=r.get('hresult'),
                    requested=r.get('requested'),sent=r.get('sent'),window_context=ready.get('window_context'),
                    evidence_grade='CONFIRMED_BY_TRACE'))
        elif kind=='display_native_begin' and r.get('operation')=='Reset':
            # A new attempt with no subsequent readiness cannot inherit an old probe.
            pending.pop(device,None)
    sequences=[r['event_sequence'] for r in rows if isinstance(r.get('event_sequence'),int)]
    # R-OBS1 records callback sequence at observation, then writes at Present.
    # Only those explicit message records may arrive after a later native event.
    immediate=[];deferred={}
    for r in rows:
        seq=r.get('event_sequence')
        if not isinstance(seq,int):continue
        if r.get('type')=='display_window_message' and r.get('telemetry_deferred') is True:
            deferred.setdefault(r.get('device_lifetime_id'),[]).append(seq)
        else:immediate.append(seq)
    increasing=lambda values:all(a<b for a,b in zip(values,values[1:]))
    valid=len(set(sequences))==len(sequences) and increasing(immediate) and all(increasing(v) for v in deferred.values())
    return dict(windowed_resize_decisions=admissions,window_message_count=len(messages),window_message_tail=messages[-24:],
                observed_reset_while_device_lost=lost,event_sequence_order_valid=valid if sequences else None,
                physical_write_order_valid=increasing(sequences) if sequences else None,
                runtime_fix_verdict='UNKNOWN_HUMAN_REQUIRED')

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
    report['display_lifecycle']=display_lifecycle(rows)
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('files',type=Path,nargs='+');a=ap.parse_args()
    print(json.dumps([audit(p) for p in a.files],indent=2))

if __name__=='__main__':main()
