"""Bounded read-only join of supplied Kia F10s; no live pointer use."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
LOGS=Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 result={'schema':1,'pid':23360,'classification':'CURRENT_LAYOUT_GATE_CONFIRMED; EXACT_UPLOAD_HASH_NOT_CAPTURED','frames':[]}
 for frame in (7771,8691,14443):
  p=LOGS/f'frame-23360-d1-{frame:08}.jsonl';row={'frame':frame,'file':p.name,'sha256':sha(p),'glow_shape_candidates':[],'on_shape_candidates':[]};result['frames'].append(row)
  for line in p.open():
   d=json.loads(line)
   if d.get('type')=='frame_begin':row['proxy_sha256']=d['proxy_sha256'];row['exe_sha256']=d['exe_sha256']
   if d.get('type')!='draw':continue
   args=d['arguments'];state=d['state']
   # Count/range only selects report candidates, never runtime material admission.
   glow=args[2]==32 and args[4]==32
   on=args[2]==16 and args[4]==12 and state['vertex_shader']==0x102
   if not(glow or on):continue
   states=state['render_states']
   out={'sequence_diagnostic_only':d['sequence'],'arguments':args[:5],'native_result':d['result'],'caller_rva':d['caller']['return_rva'],'fvf':state['vertex_shader'],'stride':state['streams'][0]['stride'],'texture':state['textures'][0],'vb':state['streams'][0],'ib':state['indices'],'world':state['matrices'].get('256'),'states':{k:states.get(str(v)) for k,v in {'ZENABLE':7,'ZWRITEENABLE':14,'ALPHATESTENABLE':15,'ALPHABLENDENABLE':27,'SRCBLEND':19,'DESTBLEND':20}.items()},'forwarded':d['forwarded'],'exact_source_hash_verified':False}
   row['glow_shape_candidates' if glow else 'on_shape_candidates'].append(out)
 session=LOGS/'session-20261015-233918-23360.jsonl';events=[]
 for line in session.open(encoding='utf-8',errors='replace'):
  if '"type":"ps2_brake_glow"' not in line:continue
  try:events.append(json.loads(line))
  except ValueError:pass
 result['session']={'file':session.name,'bytes':session.stat().st_size,'sha256':sha(session),'glow_events':events,'note':'Final file is8MiB, not16MiB. No positive or negative glow event recorded.'}
 result['installed_glow_asset']={'path':'D:/Game/Master Rallye Pristine/PS2Grass/PS2BrakeGlow.gxi','sha256':sha(Path('D:/Game/Master Rallye Pristine/PS2Grass/PS2BrakeGlow.gxi'))}
 (HERE/'kia-runtime-23360.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Kia runtime report:',[(r['frame'],len(r['glow_shape_candidates']),len(r['on_shape_candidates'])) for r in result['frames']])
if __name__=='__main__':main()
