"""Read bounded F10 sidecars only; never reads or writes game memory."""
from pathlib import Path
import argparse,json,hashlib
HERE=Path(__file__).resolve().parent
LOGS=Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')
ALLOWED={'cf49fd6ab8a8fa82867dd66632ba7f188cff6a9125de8b596dd0e4e9096a5872','638645b7ddc60aaa50651d35ff2436de1d9ba87f770b69bd1bed12ac4ca14dd9','1f17cc50a6a0b1f9dd815f20b636236707c0912fc74273956597c53229d1aadb'}
def passed(event):return event.get('draw_hresult')==0 and event.get('restore_hresult')==0
def summarize(rows,profile):
 name=profile['family'];events=[r for r in rows if r.get('family')==name or (name=='KiaSportage' and r.get('type')=='kia_brake_continuity')]
 submissions=[r for r in events if r['type']=='fleet_car_private_submission' and r.get('asset_sha256')==profile['CAR']['sha256'] and passed(r)]
 complete=[r for r in events if r['type']=='fleet_car_suppression_complete' and r.get('source_records')==profile['CAR']['source_records'] and r.get('native_suppressed_mask')==(1<<profile['CAR']['source_records'])-1]
 body=[r for r in submissions if any(r.get('instance')==c.get('instance') for c in complete)]
 wheels=[r for r in events if r['type']=='fleet_wheel_submission' and passed(r)]
 suppressed=[r for r in events if r['type']=='fleet_wheel_suppression_complete' and r.get('native_suppressed_mask')==(1<<r.get('source_records',0))-1]
 wheelowners={r['instance'] for r in wheels if any(r['instance']==c.get('instance') for c in suppressed)}
 lamps=[r for r in events if r['type'] in ('fleet_lamp_continuity','kia_brake_continuity') and r.get('owner_verified') and r.get('override_applied') and r.get('apply_hresult')==0 and passed(r)]
 return {'family':name,'native_damage_reflection_records':[r.get('source_index') for r in events if r.get('type')=='fleet_native_damage_reflection' and passed(r)],'private_ps2_off_seen':any(r.get('type')=='fleet_private_off_submission' and passed(r) for r in events),'body_draw_seen':bool(submissions),'whole_native_body_suppression_seen':bool(body),'healthy_body_confirmed':any(not r.get('private_damage_tree') for r in body),'damaged_body_confirmed':any(r.get('private_damage_tree') for r in body),'complete_ps2_wheel_owners_observed':len(wheelowners),'wheel_owner_count_expected':None,'lamp_layers':sorted({r['layer'] for r in lamps}),'damaged_lamp_layers':sorted({r['layer'] for r in lamps if r.get('damaged_branch_matched')}),'rejections':[{'type':r['type'],'reason':r.get('reason','unspecified')} for r in events if r['type'].endswith(('rejected','failure')) or r.get('override_applied') is False]}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);parser.add_argument('--logs',type=Path,default=LOGS);args=parser.parse_args();coverage=json.loads((HERE/'coverage.json').read_text());out=[]
 files=sorted(args.logs.glob(f'race-fleet-{args.pid}-d*-f*.jsonl'))
 if len(files)>128:raise ValueError('PID exceeds bounded128 capture budget')
 for f in files:
  if f.stat().st_size>128*1024:raise ValueError('Sidecar exceeds bounded size')
  frame=json.loads(f.read_text().splitlines()[0])['frame'];device=f.name.split('-d')[1].split('-')[0];f10=args.logs/f'frame-{args.pid}-d{device}-{frame:08d}.jsonl'
  with f10.open() as stream:meta=json.loads(stream.readline())
  if meta.get('type')!='frame_begin' or meta.get('proxy_sha256') not in ALLOWED:continue
  rows=[json.loads(line) for line in f.read_text().splitlines()];summaries=[summarize(rows,p) for p in coverage['vehicles']];summaries=[s for s in summaries if s['body_draw_seen'] or s['lamp_layers'] or s['rejections']]
  out.append({'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'proxy_sha256':meta['proxy_sha256'],'frame':frame,'reset':meta['quality']['successful_reset_epoch'],'msaa_samples':meta['quality']['aa_effective_samples'],'families':summaries})
 result={'schema':1,'pid':args.pid,'captures':out,'visual_acceptance':'USER_REPORT_REQUIRED','not_a_renderer_admission_certificate':True};target=HERE/f'runtime-qualification-{args.pid}.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'captures':len(out),'families':sorted({s['family'] for r in out for s in r['families']}),'output':str(target)},indent=2))
if __name__=='__main__':main()

